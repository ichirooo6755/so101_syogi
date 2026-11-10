"""画間クリアランス — くっつくべきでない画が癒着しないように筆圧を抑える。

楷書では、交差する画（十）や T 字に接する画（目の横画と縦画）は墨がつながる。
一方、三の三本の横画や、目の内側の二本の横画は、白（布白）で分かれていなければ
ならない。お手本フォントは画数の多い字ほど線を細くしてこれを成立させているが、
用筆プランナは一画ずつ独立に計画するため、隣の画の存在を知らない。

そこで全画を計画したあとに一度だけ、
    「接続しない相手の骨格までの距離」から許容される幅の上限
を求め、それを超える箇所の筆圧を下げる。書家が混み合った部分だけ筆を細める
のと同じで、字全体を一律に細くするわけではない。

接続の判定は幾何のみに基づく:
  * 骨格が交差する            → 接続（十、書の縦画と横画）
  * 端点が相手の本体に接する  → 接続（目の横画が縦画に取り付く T 字）
  * それ以外                  → 分離（三の横画同士、目の内側の横画同士）
"""

from __future__ import annotations

from dataclasses import replace
from typing import Mapping

import numpy as np

from so101_calligraphy.brushwork import (
    BrushworkProfile,
    _width_from_pressure,
    classify_stroke_family,
)
from so101_calligraphy.config import BrushConfig
from so101_calligraphy.trajectory.types import Stroke


# ``CalligraphyEnv._target_requires_contact`` treats values above this as
# writing pressure.  A clearance cap must not cross that boundary for a point
# which was originally meant to remain on paper: with a wide physical minimum
# tip, an impossible requested width otherwise inverts to exactly zero and an
# entire short stroke can be skipped in the air.
CONTACT_REQUIRED_PRESSURE = 0.015
CLEARANCE_CONTACT_PRESSURE_FLOOR = 0.020


def _point_to_polyline(points: np.ndarray, polyline: np.ndarray) -> np.ndarray:
    """points の各点から polyline までの距離。形状 (len(points),)。"""

    start = polyline[:-1]
    end = polyline[1:]
    segment = end - start
    length_sq = np.einsum("ij,ij->i", segment, segment)
    safe = np.maximum(length_sq, 1e-18)
    delta = points[:, None, :] - start[None, :, :]
    t = np.clip(np.einsum("ijk,jk->ij", delta, segment) / safe, 0.0, 1.0)
    t = np.where(length_sq[None, :] > 1e-18, t, 0.0)
    closest = start[None, :, :] + t[..., None] * segment[None, :, :]
    return np.linalg.norm(points[:, None, :] - closest, axis=2).min(axis=1)


def _segments_cross(first: np.ndarray, second: np.ndarray) -> bool:
    """2 本のポリラインが真に交差するか（端点接触は含めない）。"""

    p1, p2 = first[:-1], first[1:]
    q1, q2 = second[:-1], second[1:]

    def side(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
        return (c[..., 1] - a[..., 1]) * (b[..., 0] - a[..., 0]) - (
            b[..., 1] - a[..., 1]
        ) * (c[..., 0] - a[..., 0])

    # (i, j) 行列に展開してまとめて判定する。
    a = q1[None, :, :]
    b = q2[None, :, :]
    c = p1[:, None, :]
    d = p2[:, None, :]
    first_split = (side(a, b, c) > 0.0) != (side(a, b, d) > 0.0)
    second_split = (side(c, d, a) > 0.0) != (side(c, d, b) > 0.0)
    return bool(np.any(first_split & second_split))


def designed_contact(
    strokes: tuple[Stroke, ...] | list[Stroke],
    *,
    junction_tolerance: float,
) -> np.ndarray:
    """設計上つながる画の組を True にした対称行列を返す。"""

    count = len(strokes)
    contact = np.zeros((count, count), dtype=bool)
    for i in range(count):
        first = np.asarray(strokes[i].points, dtype=np.float64)
        ends_i = first[[0, -1]]
        for j in range(i + 1, count):
            second = np.asarray(strokes[j].points, dtype=np.float64)
            junction = min(
                float(_point_to_polyline(ends_i, second).min()),
                float(_point_to_polyline(second[[0, -1]], first).min()),
            )
            joined = junction <= junction_tolerance or _segments_cross(first, second)
            contact[i, j] = contact[j, i] = joined
    return contact


def exposed_horizontal_endpoints(
    strokes: tuple[Stroke, ...] | list[Stroke],
    *,
    junction_tolerance: float,
    angle_tolerance: float = np.deg2rad(35.0),
) -> np.ndarray:
    """Return ``(stroke, start/end)`` flags for visible horizontal ends.

    A crossing in the middle of 「十」 does not hide either end. Endpoint joins
    such as 「目」 do, so they keep their designed T connection instead of being
    sharpened into a detached triangle.
    """

    result = np.zeros((len(strokes), 2), dtype=bool)
    maximum_slope = float(np.tan(angle_tolerance))
    for index, stroke in enumerate(strokes):
        points = np.asarray(stroke.points, dtype=np.float64)
        if len(points) < 2 or classify_stroke_family(stroke) != "heng":
            continue
        for endpoint, (point, neighbour) in enumerate(
            ((points[0], points[1]), (points[-1], points[-2]))
        ):
            tangent = point - neighbour
            if abs(tangent[0]) <= 1e-12 or abs(tangent[1]) > maximum_slope * abs(tangent[0]):
                continue
            joined = any(
                other != index
                and float(
                    _point_to_polyline(
                        point.reshape(1, 2),
                        np.asarray(strokes[other].points, dtype=np.float64),
                    )[0]
                )
                <= junction_tolerance
                for other in range(len(strokes))
            )
            result[index, endpoint] = not joined
    return result


def _smooth(values: np.ndarray, window: int) -> np.ndarray:
    """幅の急な段差で穂先が痙攣しないよう移動平均で均す。"""

    if window <= 1 or len(values) <= 2:
        return values
    window = min(window, len(values))
    padded = np.pad(values, (window // 2, window // 2), mode="edge")
    kernel = np.ones(window, dtype=np.float64) / window
    return np.convolve(padded, kernel, mode="valid")[: len(values)]


def _pressure_for_width(
    width: np.ndarray,
    body_width: float,
    brush: BrushConfig,
    *,
    upper: np.ndarray,
) -> np.ndarray:
    """_width_from_pressure の単調性を使った二分法での逆算。"""

    low = np.zeros_like(width)
    high = np.array(upper, dtype=np.float64, copy=True)
    for _ in range(24):
        middle = 0.5 * (low + high)
        too_wide = _width_from_pressure(middle, body_width, brush) > width
        high = np.where(too_wide, middle, high)
        low = np.where(too_wide, low, middle)
    return 0.5 * (low + high)


def apply_clearance_caps(
    strokes: tuple[Stroke, ...] | list[Stroke],
    profiles: tuple[BrushworkProfile, ...],
    brush: BrushConfig,
    *,
    junction_tolerance: float = 0.009,
    minimum_gap: float = 0.0015,
    floor_ratio: float = 0.55,
    smoothing_window: int = 5,
    observed_width_p90_by_phase: Mapping[str, float] | None = None,
) -> tuple[BrushworkProfile, ...]:
    """接続しない画同士が触れないところまで筆圧と幅を下げたプロファイルを返す。

    ``minimum_gap <= 0`` なら何もしない（従来の挙動）。
    """

    if minimum_gap <= 0.0 or len(strokes) < 2:
        return profiles

    contact = designed_contact(strokes, junction_tolerance=junction_tolerance)
    points = [np.asarray(stroke.points, dtype=np.float64) for stroke in strokes]
    updated: list[BrushworkProfile] = []
    for index, profile in enumerate(profiles):
        planned = np.asarray(profile.width, dtype=np.float64)
        if len(planned) != len(points[index]):
            # プランナが点数を変えている場合は安全側に倒して手を触れない。
            updated.append(profile)
            continue
        cap = np.full(len(planned), np.inf)
        inflation = np.zeros(len(planned), dtype=np.float64)
        if observed_width_p90_by_phase:
            phases = np.asarray(profile.phases, dtype=object)
            for phase, observed_width in observed_width_p90_by_phase.items():
                selected = phases == phase
                if not np.any(selected):
                    continue
                planned_p90 = float(np.percentile(planned[selected], 90))
                inflation[selected] = max(float(observed_width) - planned_p90, 0.0)
        for other in range(len(strokes)):
            if other == index or contact[index, other]:
                continue
            distance = _point_to_polyline(points[index], points[other])
            # 双方が同じ幅まで細るとして、半幅の和 + 隙間 <= 距離。
            cap = np.minimum(cap, distance - minimum_gap - inflation)
        if not np.isfinite(cap).any():
            updated.append(profile)
            continue
        floor = floor_ratio * planned
        target = np.minimum(planned, np.maximum(cap, floor))
        target = _smooth(target, smoothing_window)
        target = np.minimum(target, planned)
        if np.allclose(target, planned, rtol=0.0, atol=1e-9):
            updated.append(profile)
            continue
        body_width = float(profile.body_width)
        if body_width <= 0.0:
            updated.append(profile)
            continue
        pressure = np.asarray(profile.pressure, dtype=np.float64)
        scaled = _pressure_for_width(target, body_width, brush, upper=pressure)
        scaled = np.minimum(scaled, pressure)
        phases = np.asarray(profile.phases, dtype=object)
        contact_required = pressure > CONTACT_REQUIRED_PRESSURE
        if profile.technique != "tome":
            contact_required &= phases != "finish"
        # If ``target`` is narrower than ``brush.minimum_width``, the inverse
        # correctly returns zero pressure but zero also means "do not require
        # paper contact" to the controller.  Keep the smallest practical
        # writing pressure instead.  This accepts the physical minimum width
        # when the requested clearance is impossible without deleting a画.
        contact_floor = np.minimum(pressure, CLEARANCE_CONTACT_PRESSURE_FLOOR)
        scaled = np.where(
            contact_required,
            np.maximum(scaled, contact_floor),
            scaled,
        )
        updated.append(
            replace(
                profile,
                pressure=scaled,
                width=_width_from_pressure(scaled, body_width, brush),
            )
        )
    return tuple(updated)
