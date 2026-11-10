"""Kaisho brush-motion laws behind an ablation-friendly planner interface.

AnimCJK / KanjiVG supply stroke order, centre-line shape, and a body-width
scale. Local pressure, tip path micro-motions, shaft roll, and speed come from
published kaisho yōhitsu (用筆): reverse entry, teian (提按), corners, and
finish return / release. Width is never copied sample-by-sample into Z.

Horizontal 「一」 follows classroom guidance (トン・スー・トン, ~45° entry,
tip riding the upper edge, light finish return without a bottom blob), e.g.
https://matsumotoshoeido-shodo.jp/blog/4571/ and basic line drills such as
https://www.kasumi-syodo.jp/activities/10642
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

import numpy as np

from so101_calligraphy.config import BrushConfig
from so101_calligraphy.ink import tip_width_from_pressure

if TYPE_CHECKING:
    from so101_calligraphy.trajectory.types import Stroke


BRUSHWORK_PHASES = ("entry", "send", "corner", "finish")

# Stable family labels applied to every joyo glyph via KanjiVG stroke types.
STROKE_FAMILIES = (
    "heng",  # 横画
    "shu",  # 縦画
    "pie",  # 撇 / 左払い
    "na",  # 捺 / 右払い
    "dian",  # 点
    "ti",  # 挑 / 提
    "zhe",  # 折 / 転折
    "gou",  # 鉤 / はね
)

_HENG = frozenset("㇐")
_SHU = frozenset("㇑")
_PIE = frozenset("㇒㇓")
_NA = frozenset("㇏")
_DIAN = frozenset("㇔")
_TI = frozenset("㇀")
_ZHE = frozenset("㇕㇖㇗㇘㇙㇛㇜㇝㇞㇟㇇㇋㇎")
_GOU = frozenset("㇚㇁㇂㇃㇄㇅㇆㇈㇉㇊㇌")


def _smoothstep(value: np.ndarray) -> np.ndarray:
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def _curvature(tangents: np.ndarray) -> np.ndarray:
    cosine = np.sum(tangents[1:] * tangents[:-1], axis=1)
    angles = np.arccos(np.clip(cosine, -1.0, 1.0))
    return np.concatenate(([0.0], angles))


def _stroke_symbols(stroke_type: str) -> set[str]:
    return {char for char in stroke_type if "\u31c0" <= char <= "\u31ef"}


def classify_stroke_family(stroke: Stroke) -> str:
    """Map a KanjiVG / CJK Strokes label onto a kaisho motion family."""

    symbols = _stroke_symbols(stroke.stroke_type)
    if not symbols:
        # Fall back on finish technique and geometry when metadata is absent.
        from so101_calligraphy.trajectory.profile import resolve_technique

        technique = resolve_technique(stroke)
        delta = stroke.points[-1] - stroke.points[0]
        if technique == "hane":
            return "gou"
        if technique == "harai":
            return "na" if abs(delta[0]) >= abs(delta[1]) * 0.55 else "pie"
        if abs(delta[0]) >= abs(delta[1]) * 1.15:
            return "heng"
        if abs(delta[1]) >= abs(delta[0]) * 1.15:
            return "shu"
        length = float(np.sum(np.linalg.norm(np.diff(stroke.points, axis=0), axis=1)))
        return "dian" if length < 0.018 else "heng"

    if symbols & _GOU:
        return "gou"
    if symbols & _ZHE:
        return "zhe"
    if symbols & _DIAN:
        return "dian"
    if symbols & _TI:
        return "ti"
    if symbols & _NA:
        return "na"
    if symbols & _PIE:
        return "pie"
    if symbols & _SHU:
        return "shu"
    if symbols & _HENG:
        return "heng"
    return "heng"


@dataclass(frozen=True)
class BrushworkProfile:
    progress: np.ndarray
    tangents: np.ndarray
    pressure: np.ndarray
    speed: np.ndarray
    width: np.ndarray
    roll: np.ndarray
    phases: tuple[str, ...]
    technique: str
    path_delta: np.ndarray
    stroke_family: str
    # AnimCJK 由来の胴体幅スケール。画間クリアランスで幅を細める後段
    # (trajectory.clearance) が、筆圧から幅を引き直すために必要。
    body_width: float = 0.0


class BrushworkPlanner(Protocol):
    def plan(self, stroke: Stroke, brush: BrushConfig) -> BrushworkProfile: ...


def _motion_phases(
    progress: np.ndarray, curvature: np.ndarray, family: str
) -> tuple[str, ...]:
    phases: list[str] = []
    finish_start = (
        0.72
        if family in {"pie", "na", "ti"}
        else 0.84
        if family in {"heng", "shu"}
        else 0.78
    )
    for value, bend in zip(progress, curvature, strict=True):
        if value <= 0.14:
            phases.append("entry")
        elif value >= finish_start:
            phases.append("finish")
        elif family == "zhe" and bend >= 0.18:
            phases.append("corner")
        elif bend >= 0.28:
            phases.append("corner")
        else:
            phases.append("send")
    return tuple(phases)


def _body_width_scale(stroke: Stroke, brush: BrushConfig) -> float:
    """One scalar from AnimCJK / authored widths; never a per-sample Z map."""

    if stroke.widths is None:
        return 0.55 * (brush.minimum_width + brush.maximum_width)
    widths = np.asarray(stroke.widths, dtype=np.float64)
    # Global scale only. Local thick/thin of the outline is discarded so that
    # kaisho teian can own the bone structure.
    scale = float(np.median(widths))
    return float(np.clip(scale, brush.minimum_width, brush.maximum_width))


def _width_from_pressure(
    pressure: np.ndarray, body_width: float, brush: BrushConfig
) -> np.ndarray:
    """Map calligraphy pressure to the ink-transfer footprint used at contact."""

    # ``body_width`` remains in the interface for historical profile objects;
    # both planning and deposited ink now use the same invertible tip curve.
    del body_width
    return np.asarray(tip_width_from_pressure(pressure, brush), dtype=np.float64)


def _tip_pressure_profile(pressure: np.ndarray, brush: BrushConfig) -> np.ndarray:
    return np.clip(
        pressure * brush.tip_pressure_scale,
        brush.tip_pressure_floor,
        brush.tip_pressure_ceiling,
    )


def _unit(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm < 1e-12:
        return np.asarray([1.0, 0.0], dtype=np.float64)
    return vector / norm


def _kaisho_pressure_speed(
    progress: np.ndarray,
    family: str,
    technique: str,
    curvature: np.ndarray,
    brush: BrushConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Entry press → send glide → finish press/release per stroke family.

    For heng/shu the classroom rhythm is light トン・スー・トン: seat the tip,
    glide without grinding, then a light stop — not a heavy sausage press.
    """

    # Entry window long enough to seat at ~45°, short enough to keep スー light.
    entry = _smoothstep(progress / 0.18)
    finish = _smoothstep(np.clip((progress - 0.78) / 0.22, 0.0, 1.0))
    corner = np.clip(curvature / 0.55, 0.0, 1.0)
    corner = np.convolve(
        np.pad(corner, (1, 1), mode="edge"),
        np.asarray([0.25, 0.50, 0.25]),
        mode="valid",
    )

    # Default horizontal bone: トン・スー・トン (light).
    press_entry = 0.74
    press_send = 0.40
    press_finish = 0.70
    speed_entry = 0.32
    speed_send = 1.05
    speed_finish = 0.12

    if family == "shu":
        press_entry, press_send, press_finish = 0.72, 0.44, 0.68
        if technique == "harai":
            # Suspended needle: finish releases.
            press_finish = 0.03
            speed_finish = 1.68
    elif family == "pie":
        # Left harai: firm-enough entry, hold body, then clear outgoing release.
        press_entry, press_send, press_finish = 0.78, 0.48, 0.02
        speed_finish = 1.95
        finish = _smoothstep(np.clip((progress - 0.58) / 0.42, 0.0, 1.0))
    elif family == "na":
        # Right harai: gradual press, pause, then release (波磔).
        press_entry, press_send, press_finish = 0.62, 0.72, 0.02
        speed_finish = 1.68
        finish = _smoothstep(np.clip((progress - 0.60) / 0.40, 0.0, 1.0))
        belly = np.sin(np.pi * np.clip(progress, 0.0, 1.0)) ** 2
        press_send = 0.58 + 0.22 * belly
    elif family == "dian":
        press_entry, press_send, press_finish = 0.88, 0.72, 0.50
        speed_entry, speed_send, speed_finish = 0.22, 0.55, 0.35
        finish = _smoothstep(np.clip((progress - 0.45) / 0.55, 0.0, 1.0))
    elif family == "ti":
        press_entry, press_send, press_finish = 0.76, 0.40, 0.05
        speed_finish = 1.65
        finish = _smoothstep(np.clip((progress - 0.55) / 0.45, 0.0, 1.0))
    elif family == "zhe":
        press_entry, press_send, press_finish = 0.76, 0.46, 0.72
    elif family == "gou":
        press_entry, press_send = 0.78, 0.50
        # Settle (蓄力) then release along the hook (趯).
        finish_g = np.clip((progress - 0.72) / 0.28, 0.0, 1.0)
        turn = _smoothstep(np.minimum(finish_g / 0.40, 1.0))
        release = _smoothstep(np.maximum((finish_g - 0.32) / 0.68, 0.0))
        press_finish = 0.78 * (1.0 - release) + 0.05 * release
        pressure = press_send + (press_entry - press_send) * (1.0 - entry)
        pressure = pressure * (1.0 - turn) + 0.82 * turn
        pressure = pressure * (1.0 - release) + 0.05 * release
        pressure = pressure + 0.12 * corner
        pressure = np.clip(pressure, 0.02, 1.0)
        speed = brush.nominal_speed * (speed_entry + (speed_send - speed_entry) * entry)
        speed = speed * (1.0 - turn) + brush.nominal_speed * 0.22 * turn
        speed = speed * (1.0 - release) + brush.nominal_speed * 1.55 * release
        speed = speed * (1.0 - 0.40 * corner)
        speed = np.clip(speed, brush.nominal_speed * 0.02, brush.nominal_speed * 2.0)
        return _tip_pressure_profile(pressure, brush), speed

    if technique == "tome" and family in {"heng", "shu", "zhe"}:
        pass  # keep default press_finish for トン・スー・トン width at stop
    pressure = press_send + (press_entry - press_send) * (1.0 - entry)
    pressure = pressure * (1.0 - finish) + press_finish * finish
    # Mild teian after the entry release — keep スー from going completely flat.
    send_end = 0.84 if family in {"heng", "shu"} else 0.78
    teian = 0.04 * np.sin(2.0 * np.pi * np.clip((progress - 0.22) / 0.58, 0.0, 1.0))
    teian *= (progress > 0.22) & (progress < send_end)
    if family in {"heng", "shu"} and technique in {"tome", "harai"}:
        teian *= 0.25
    pressure = pressure + teian * (family in {"heng", "shu", "zhe"})
    pressure = pressure + 0.14 * corner
    pressure = np.clip(pressure, 0.02, 1.0)

    speed = brush.nominal_speed * (
        speed_entry + (speed_send - speed_entry) * entry
    )
    speed = speed * (1.0 - finish) + brush.nominal_speed * speed_finish * finish
    speed = speed * (1.0 - 0.55 * corner)
    if family == "na":
        pause = np.sin(np.pi * np.clip((progress - 0.62) / 0.14, 0.0, 1.0)) ** 2
        speed = speed * (1.0 - 0.52 * pause)
    if family == "pie":
        settle = np.sin(np.pi * np.clip((progress - 0.55) / 0.12, 0.0, 1.0)) ** 2
        speed = speed * (1.0 - 0.35 * settle)
    speed = np.clip(speed, brush.nominal_speed * 0.02, brush.nominal_speed * 2.0)
    return _tip_pressure_profile(pressure, brush), speed


def _path_delta(
    progress: np.ndarray,
    tangents: np.ndarray,
    family: str,
    technique: str,
    curvature: np.ndarray,
) -> np.ndarray:
    """XY micro-motions: reverse entry, tip-upper bias, finish return, corners."""

    delta = np.zeros((len(progress), 2), dtype=np.float64)
    entry_tangent = _unit(tangents[0])
    finish_tangent = _unit(tangents[-1])
    entry_env = 1.0 - _smoothstep(progress / 0.18)
    finish_env = _smoothstep(np.clip((progress - 0.82) / 0.18, 0.0, 1.0))
    left_normal = np.stack((-tangents[:, 1], tangents[:, 0]), axis=1)
    left_normal = left_normal / np.maximum(
        np.linalg.norm(left_normal, axis=1, keepdims=True), 1e-9
    )

    # 欲右先左 / 欲下先上: enter against the stroke direction.
    gyakunyu = {
        "heng": 0.0030,
        "shu": 0.0026,
        "pie": 0.0024,
        "na": 0.0022,
        "dian": 0.0016,
        "ti": 0.0020,
        "zhe": 0.0026,
        "gou": 0.0024,
    }[family]
    delta -= entry_tangent * gyakunyu * entry_env[:, None]

    if family in {"heng", "shu", "zhe"}:
        # 穂先は線の上部を通る + 横画はわずかに右上がり。
        tip_upper = 0.0011 if family == "heng" else 0.0007
        delta += left_normal * tip_upper
        if family == "heng":
            bow = np.sin(np.pi * np.clip(progress, 0.0, 1.0))
            delta += left_normal * (0.00055 * bow)[:, None]

    # 回鋒: 左上（穂先方向）へ軽く突き返し。右下押し込みの下部コブを避ける。
    returning = family in {"heng", "shu", "dian", "zhe"} and technique == "tome"
    if family == "dian":
        returning = True
    if returning:
        return_len = (
            0.0010 if family == "heng" else 0.0016 if family != "dian" else 0.0012
        )
        tip_return = -finish_tangent + 0.55 * left_normal[-1]
        tip_return = tip_return / max(float(np.linalg.norm(tip_return)), 1e-9)
        delta += tip_return * return_len * finish_env[:, None]

    if family == "zhe" or np.any(curvature >= 0.22):
        normals = np.stack((-tangents[:, 1], tangents[:, 0]), axis=1)
        corner = np.clip(curvature / 0.55, 0.0, 1.0)
        delta += normals * (0.0007 * corner)[:, None]

    if family == "na" and technique == "harai":
        release = _smoothstep(np.clip((progress - 0.86) / 0.14, 0.0, 1.0))
        delta += finish_tangent * 0.0012 * release[:, None]

    return delta


def _shaft_roll(
    progress: np.ndarray,
    tangents: np.ndarray,
    family: str,
    technique: str,
    curvature: np.ndarray,
) -> np.ndarray:
    direction = np.unwrap(np.arctan2(tangents[:, 1], tangents[:, 0]))
    # Align the shaft; entry targets ~40–45° side contact (classroom 入筆).
    roll = 0.18 * np.sin(direction)
    entry = 1.0 - _smoothstep(progress / 0.18)
    entry_angle = 0.70 if family in {"heng", "shu", "zhe"} else 0.45
    sign = np.sign(np.cos(direction[0]) + 1e-9)
    roll += entry_angle * entry * sign
    finish = _smoothstep(np.clip((progress - 0.82) / 0.18, 0.0, 1.0))
    if family in {"heng", "shu"} and technique == "tome":
        roll = roll * (1.0 - 0.35 * finish) + entry_angle * 0.85 * finish * sign
    roll += 0.18 * np.clip(curvature / 0.55, 0.0, 1.0)
    if family == "gou" or technique == "hane":
        anchor = max(0, int(np.searchsorted(progress, 0.72)) - 1)
        roll = roll.copy()
        roll[progress >= 0.72] = roll[anchor]
    if family == "dian":
        roll *= 0.55
    return roll


class LegacyBrushworkPlanner:
    def plan(self, stroke: Stroke, brush: BrushConfig) -> BrushworkProfile:
        from so101_calligraphy.trajectory.profile import build_stroke_profile

        profile = build_stroke_profile(stroke, brush)
        curvature = _curvature(profile.tangents)
        family = classify_stroke_family(stroke)
        return BrushworkProfile(
            profile.progress,
            profile.tangents,
            profile.pressure,
            profile.speed,
            profile.width,
            np.zeros(len(profile.progress), dtype=np.float64),
            _motion_phases(profile.progress, curvature, family),
            profile.technique,
            np.zeros((len(profile.progress), 2), dtype=np.float64),
            family,
        )


class ProfessionalBrushworkPlanner:
    """Stroke-family kaisho laws with AnimCJK body-width scale only."""

    def plan(self, stroke: Stroke, brush: BrushConfig) -> BrushworkProfile:
        from so101_calligraphy.trajectory.profile import build_stroke_profile

        base = build_stroke_profile(stroke, brush)
        progress = base.progress
        tangents = base.tangents
        curvature = _curvature(tangents)
        family = classify_stroke_family(stroke)
        technique = base.technique

        pressure, speed = _kaisho_pressure_speed(
            progress, family, technique, curvature, brush
        )
        body_width = _body_width_scale(stroke, brush)
        width = _width_from_pressure(pressure, body_width, brush)
        path_delta = _path_delta(progress, tangents, family, technique, curvature)
        roll = _shaft_roll(progress, tangents, family, technique, curvature)
        return BrushworkProfile(
            progress,
            tangents,
            pressure,
            speed,
            width,
            roll,
            _motion_phases(progress, curvature, family),
            technique,
            path_delta,
            family,
            body_width,
        )


def make_brushwork_planner(mode: str) -> BrushworkPlanner:
    if mode == "legacy":
        return LegacyBrushworkPlanner()
    if mode == "professional":
        return ProfessionalBrushworkPlanner()
    raise ValueError(f"Unknown brushwork mode: {mode!r}")
