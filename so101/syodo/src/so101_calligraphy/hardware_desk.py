"""Desk calibration for real SO-101: paper, suzuri, tilt range, brush sign.

Taught with torque off. Sim writing is blocked until ``ready`` is true.
Hardware scene: hanshi portrait on the same table as the base (not the A4 150 mm riser).
# ponytail: paper is an axis-aligned box; rotate the sheet to the robot XY first.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from so101_calligraphy.config import (
    EnvConfig,
    HardwareCalibrationConfig,
    InkstoneConfig,
    JOINT_LIMITS,
    JOINT_NAMES,
    ModuleConfig,
    PaperConfig,
    WritingLayoutConfig,
)

SCHEMA = 1
DEFAULT_DESK_PATH = Path("data/hardware/desk.json")
DEFAULT_PORT = "/dev/cu.usbmodem5B7B0136431"
DEFAULT_LEADER_PORT = "/dev/cu.usbmodem5B7B0140931"
ROBOT_ID = "syodo_follower"
LEADER_ID = "syodo_leader"
GRIPPER_RAD = (float(JOINT_LIMITS[-1, 0]), float(JOINT_LIMITS[-1, 1]))
# Stock MJCF has no exposed rigid shaft: grip and hair root coincide.
STOCK_TUFT_M = 0.038
MIN_PAPER_M = 0.10
# 肩・肘のゼロ点を四隅から詰めるので、実測は 1.2 mm まで揃う。
# ここが緩いとゼロ点ずれを見逃す。紙寸法との突き合わせを外した分、この砦を締める。
MAX_CORNER_Z_SPAN_M = 0.010
MIN_TUFT_CM = 2.0
MAX_TUFT_CM = 8.0
MIN_TOTAL_BRUSH_CM = 4.0
MAX_TOTAL_BRUSH_CM = 30.0
# 本番: 半紙は縦置き。width=X=縦（下手→上手）、height=Y=横。本紙 24.2×33.3 cm。
HANSHI_VERTICAL_M = 0.333
HANSHI_HORIZONTAL_M = 0.242
# 土台と半紙は同じ机。学習用 A4 の 150 mm 台座は使わない。
TABLE_BASE_RISER_M = 0.0
REQUIRED_POSES = (
    "upright",
    "lean_toward_paper",
    "tilt_min",
    "tilt_max",
    "paper_near_right",
    "paper_near_left",
    "paper_far_left",
    "paper_far_right",
    "paper_center_touch",
    "hover_center",
    "suzuri_pool",
)
# Optional: visual match to sim reset. Not required for solve.
SIM_HOME_POSE = "sim_home"
SNAP_POSES = REQUIRED_POSES + (SIM_HOME_POSE, "suzuri_pull")
PAPER_CORNERS = (
    "paper_near_right",
    "paper_near_left",
    "paper_far_left",
    "paper_far_right",
)
# 穂が直立していないと教示にならない姿勢。lean_toward_paper は寝かせるので除く。
UPRIGHT_POSES = PAPER_CORNERS + ("paper_center_touch", "hover_center", "upright")
ICHI_POSES = ("paper_near_left", "paper_near_right")
# ID6 の 0-100% は MJCF 可動域（110°）ではなく実機の実可動を張る。
# 731-2541 tick を手で突き当てて実測（2026-09-01）。% が増えるほど筆は寝るので負。
# ゲインは tick 幅で決まる物理量なので固定し、ゼロ点だけ直立教示から当てる。
GRIPPER_DEG_PER_PCT = -159.1 / 100.0
GRIPPER_FIT_MAX_RESID_DEG = 15.0
# 硯は液面の教示から手前（下手、-x）へ 7 cm 引いて墨量を整える。
SUZURI_PULL_M = 0.070
ID6_BAND_PCT = 20.0
MIN_UPRIGHT_ID6_PCT = 10.0
# シミュの L 字（上腕垂直・前腕水平）。preview はこの姿勢を描いて保存する。
SIM_HOME_QPOS_DEG = {
    "shoulder_pan": 0.0,
    "shoulder_lift": -90.0,
    "elbow_flex": 90.0,
    "wrist_flex": 0.0,
    "wrist_roll": 0.0,
}
TEACH_AXES = """半紙は字の上下が「縦」、左右が「横」。手前が下手、奥が上手。

サーボ（筆から）:
  ID6 一番先端: 筆を立てる・寝かす。可動 159°。単独では直立まで届かない
  ID4 手首曲げ: 直立の主役。下に曲げると立つ
  ID5 その手前: 筆が立っているとき、毛先を左右へ。寝たまま回しても立たない
"""
TEACH_PROMPTS = {
    "upright": "ID6 で筆を立て、毛先は机。ID5 は触らない。",
    "lean_toward_paper": (
        "ID6 だけ回し、筆を起筆のように寝かせる。毛先が紙に近づく側。ID5 と腕は動かさない。"
    ),
    "tilt_min": (
        "ID6 を手で回し、これ以上寝かせたくない位置へ。書きで使う寝側の端をあなたが決める。"
        "突き当たりまで行かなくてよい。"
    ),
    "tilt_max": (
        "ID6 を手で回し、これ以上立てたくない位置へ。書きで使う立側の端をあなたが決める。"
    ),
    "paper_near_right": (
        "筆を直立させる（主役は手首曲げ ID4。ID6 は補助）。寝たまま ID5 は回さない。"
        "毛先を半紙の下手右（手前右）につける。肩・肘・手首曲げは使ってよい。"
    ),
    "paper_near_left": (
        "筆を直立させる（主役は手首曲げ ID4。ID6 は補助）。寝たまま ID5 は回さない。"
        "毛先を半紙の下手左（手前左）につける。肩・肘・手首曲げは使ってよい。"
    ),
    "paper_far_left": (
        "筆を直立させる（主役は手首曲げ ID4）。毛先を半紙の上手左（奥左）につける。"
    ),
    "paper_far_right": (
        "筆を直立させる（主役は手首曲げ ID4）。毛先を半紙の上手右（奥右）につける。"
    ),
    "paper_center_touch": (
        "筆を直立させる（主役は手首曲げ ID4）。毛先を半紙の中央につける。浮かせない。"
    ),
    "hover_center": (
        "筆の向きは紙に触れたときと同じ（直立のまま）。"
        "半紙中央の真上。毛先は紙から離す。"
    ),
    "suzuri_pool": "硯の墨池中心。穂先が液面（または空の硯底）に触れたところ。",
    "suzuri_pull": (
        "墨をかける手前側の端。毛先は硯の面に付けたまま、墨池から手前へ引いた位置。"
        "2 往復の引き側になる。"
    ),
    SIM_HOME_POSE: (
        "シミュの L 字（上腕垂直・前腕水平）に腕を合わせる。"
        "筆は直立のまま。毛先は紙に刺さなくてよい。"
    ),
}


def empty_desk() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "tilt_sign": None,
        "gripper_map_rad": None,
        "tip_points_down": None,
        "brush_tuft_cm": None,
        "brush_total_cm": None,
        "brush_rigid_cm": None,
        "brush_tip_length_scale": None,
        "poses": {},
        "paper": None,
        "inkstone_offset_m": None,
        "tilt_range": None,
        "safe_height_m": None,
        "lift_deg_per_mm": None,
        "suzuri_pull_deg": None,
        "wrist_roll_offset_deg": None,
        "sim_home_qpos_deg": None,
        "joint_offsets_deg": None,
        "joint_ranges_rad": None,
        "motor_calibration_sha256": None,
        "follower_usb_serial": None,
        "follower_port": None,
        "follower_id": None,
        "pressure_calibration_v1": None,
        "ready": False,
    }


def load_desk(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return empty_desk()
    data = json.loads(path.read_text(encoding="utf-8"))
    if int(data.get("schema", 0)) != SCHEMA:
        raise ValueError(f"unsupported desk schema: {data.get('schema')}")
    return data


def save_desk(path: Path, desk: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(desk, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def desk_fingerprint(desk: dict[str, Any]) -> str:
    """Hash the measured inputs that can invalidate a hardware path."""
    payload = {
        key: desk.get(key)
        for key in (
            "paper",
            "brush_tuft_cm",
            "brush_total_cm",
            "brush_rigid_cm",
            "brush_tip_length_scale",
            "joint_offsets_deg",
            "joint_ranges_rad",
            "gripper_map_rad",
            "tilt_sign",
            "motor_calibration_sha256",
        )
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def desk_joint_ranges(desk: dict[str, Any]) -> tuple[tuple[float, float], ...] | None:
    values = desk.get("joint_ranges_rad")
    if values is None:
        return None
    ranges = tuple(tuple(float(v) for v in pair) for pair in values)
    if len(ranges) != len(JOINT_NAMES) or any(len(pair) != 2 for pair in ranges):
        raise ValueError("desk joint_ranges_rad must have six [min, max] pairs")
    arrays = tuple(np.asarray(pair, dtype=np.float64) for pair in ranges)
    if any(not np.isfinite(pair).all() or pair[1] <= pair[0] for pair in arrays):
        raise ValueError("desk joint_ranges_rad must contain finite increasing ranges")
    return ranges


def require_joint_ranges(desk: dict[str, Any]) -> tuple[tuple[float, float], ...]:
    ranges = desk_joint_ranges(desk)
    if ranges is None:
        raise SystemExit(
            "実機関節範囲が未同期です。先に hardware_calibrate.py sync-limits を実行してください。"
        )
    return ranges


def _gripper_pct(q_rad: float, tilt_sign: int, gripper_map: tuple[float, float]) -> float:
    lo, hi = gripper_map
    pct = (float(q_rad) - lo) / (hi - lo) * 100.0
    if tilt_sign < 0:
        pct = 100.0 - pct
    return float(np.clip(pct, 0.0, 100.0))


def _gripper_rad(pct: float, tilt_sign: int, gripper_map: tuple[float, float]) -> float:
    lo, hi = gripper_map
    value = float(np.clip(pct, 0.0, 100.0))
    if tilt_sign < 0:
        value = 100.0 - value
    return lo + value / 100.0 * (hi - lo)


def _offsets(offsets: dict[str, float] | None) -> dict[str, float]:
    """sim_deg = lerobot_deg + offset. Gripper is percent; it has no offset."""
    given = offsets or {}
    return {name: float(given.get(name, 0.0)) for name in JOINT_NAMES[:-1]}


def qpos_to_lerobot(
    qpos_rad: np.ndarray,
    *,
    tilt_sign: int = 1,
    tilt_range: tuple[float, float] | None = None,
    offsets: dict[str, float] | None = None,
    gripper_map: tuple[float, float] | None = None,
) -> dict[str, float]:
    qpos_rad = np.asarray(qpos_rad, dtype=np.float64)
    off = _offsets(offsets)
    out = {
        name: float(np.rad2deg(qpos_rad[i]) - off[name])
        for i, name in enumerate(JOINT_NAMES[:-1])
    }
    gripper = _gripper_pct(qpos_rad[-1], tilt_sign, gripper_map or GRIPPER_RAD)
    if tilt_range is not None:
        gripper = float(np.clip(gripper, tilt_range[0], tilt_range[1]))
    out["gripper"] = gripper
    return out


def lerobot_to_qpos(
    joints: dict[str, float],
    *,
    tilt_sign: int = 1,
    offsets: dict[str, float] | None = None,
    gripper_map: tuple[float, float] | None = None,
) -> np.ndarray:
    q = np.zeros(6, dtype=np.float64)
    off = _offsets(offsets)
    for i, name in enumerate(JOINT_NAMES[:-1]):
        q[i] = np.deg2rad(float(joints[name]) + off[name])
    q[-1] = _gripper_rad(float(joints["gripper"]), tilt_sign, gripper_map or GRIPPER_RAD)
    return q


def joint_offsets_from_sim_home(desk: dict[str, Any]) -> dict[str, float]:
    """sim reset degrees minus taught LeRobot degrees. Gripper is percent; skip it."""
    target = desk.get("sim_home_qpos_deg")
    taught = (desk.get("poses") or {}).get(SIM_HOME_POSE)
    if not target or not taught:
        raise ValueError("先に preview と snap sim_home")
    stale = [
        name
        for name, value in SIM_HOME_QPOS_DEG.items()
        if abs(float(target[name]) - value) > 1e-6
    ]
    if stale:
        raise ValueError(
            f"保存された sim_home が L 字ではありません（{', '.join(stale)}）。"
            "preview を取り直してください。"
        )
    return {
        name: float(target[name] - taught[name])
        for name in JOINT_NAMES[:-1]
    }


def format_joints(joints: dict[str, float]) -> str:
    return (
        f"ID6（筆 立つ/寝る）{joints['gripper']:.1f}%  "
        f"ID5（毛先の左右）{joints['wrist_roll']:.1f}°  "
        f"肩 {joints['shoulder_lift']:.1f}°  "
        f"肘 {joints['elbow_flex']:.1f}°  "
        f"手首曲げ {joints['wrist_flex']:.1f}°  "
        f"土台 {joints['shoulder_pan']:.1f}°"
    )


def id6_band(desk: dict[str, Any]) -> tuple[float, float]:
    """ID6 の粗い許容幅。preview が入れた直立 % の周り。無ければ 0% 付近だけ弾く。"""
    center = desk.get("upright_id6_pct")
    if center is None:
        return (MIN_UPRIGHT_ID6_PCT, 100.0)
    return (max(0.0, float(center) - ID6_BAND_PCT), min(100.0, float(center) + ID6_BAND_PCT))


def check_upright_id6(desk: dict[str, Any], name: str, joints: dict[str, float]) -> None:
    if name not in UPRIGHT_POSES:
        return
    lo, hi = id6_band(desk)
    pct = float(joints["gripper"])
    if not lo <= pct <= hi:
        raise ValueError(
            f"{name} の ID6 が {pct:.1f}%。筆が直立した教示ではないので送らない。"
            f"直立は {lo:.0f}–{hi:.0f}% のあたり。先に peek で % を見てから snap。"
        )


def require_upright_id6(
    desk: dict[str, Any], names: tuple[str, ...] = UPRIGHT_POSES
) -> None:
    poses = desk.get("poses") or {}
    for name in names:
        joints = poses.get(name)
        if joints is None:
            raise ValueError(f"未記録: {name}")
        check_upright_id6(desk, name, joints)


def tilt_from_vertical_deg(axis: np.ndarray) -> float:
    return float(np.degrees(np.arccos(np.clip(-float(axis[2]), -1.0, 1.0))))


def pose_deg(desk: dict[str, Any], name: str) -> np.ndarray:
    poses = desk.get("poses") or {}
    joints = poses.get(name)
    if joints is None:
        raise ValueError(f"未記録: {name}")
    return np.asarray([float(joints[joint]) for joint in JOINT_NAMES], dtype=np.float64)


def taught_ichi_waypoints(
    desk: dict[str, Any], *, lift_mm: float = 0.0
) -> tuple[tuple[str, np.ndarray], ...]:
    """Hover is 手前左 with pan centered. Do not take lift from hover_center.

    Raising shoulder to hover_center while keeping the writing fold pitches the brush.
    横画 is pan only; ID6 stays on 手前左. lift_mm backs the tuft off the taught
    contact, which is recorded limp and so sits deeper than playback needs.
    """
    left = pose_deg(desk, "paper_near_left")
    right = pose_deg(desk, "paper_near_right")
    if lift_mm:
        shoulder_lift = lift_mm * desk_lift_gain(desk)
        left[1] += shoulder_lift
        right[1] += shoulder_lift
    up = left.copy()
    up[0] = 0.5 * (left[0] + right[0])
    end = left.copy()
    end[0] = right[0]
    return (
        ("hover", up),
        ("start", left),
        ("end", end),
        ("hover", up.copy()),
    )


def missing_poses(desk: dict[str, Any]) -> tuple[str, ...]:
    poses = desk.get("poses") or {}
    return tuple(name for name in REQUIRED_POSES if name not in poses)


def desk_gaps(desk: dict[str, Any]) -> tuple[str, ...]:
    gaps = list(missing_poses(desk))
    gaps.extend(f"{name}（サーボ再較正後の再教示）" for name in desk.get("stale_poses", ()))
    if desk.get("brush_tuft_cm") is None:
        gaps.append("brush_tuft_cm")
    if desk.get("brush_total_cm") is None:
        gaps.append("brush_total_cm")
    if desk.get("brush_rigid_cm") is None:
        gaps.append("brush_rigid_cm")
    if SIM_HOME_POSE not in (desk.get("poses") or {}):
        gaps.append(SIM_HOME_POSE)
    if not desk.get("joint_offsets_deg"):
        gaps.append("joint_offsets_deg")
    return tuple(gaps)


def tuft_scale(cm: float) -> float:
    measured = float(cm)
    if not MIN_TUFT_CM <= measured <= MAX_TUFT_CM:
        raise ValueError(
            f"穂の長さ {measured} cm は {MIN_TUFT_CM:.0f}–{MAX_TUFT_CM:.0f} cm で測ってください。"
            f"（シミュ基準 {STOCK_TUFT_M * 100:.1f} cm）"
        )
    return (measured / 100.0) / STOCK_TUFT_M


def brush_geometry(total_cm: float, tuft_cm: float) -> tuple[float, float, float]:
    """Return total scale, rigid metres and tuft metres after validation."""
    total = float(total_cm)
    tuft = float(tuft_cm)
    tuft_scale(tuft)
    if not MIN_TOTAL_BRUSH_CM <= total <= MAX_TOTAL_BRUSH_CM:
        raise ValueError(
            f"把持位置から毛先まで {total} cm は {MIN_TOTAL_BRUSH_CM:.0f}–{MAX_TOTAL_BRUSH_CM:.0f} cm で測ってください。"
        )
    if total < tuft:
        raise ValueError("把持位置から毛先までの長さは穂より短くできません")
    return (total / 100.0 / STOCK_TUFT_M, (total - tuft) / 100.0, tuft / 100.0)


def check_taught_plane(corners_xyz: np.ndarray) -> None:
    z = np.asarray(corners_xyz, dtype=np.float64)[:, 2]
    span = float(z.max() - z.min())
    if span > MAX_CORNER_Z_SPAN_M:
        raise ValueError(
            "教示した四隅がシミュでは同じ机の高さになりません"
            f"（z {z.min() * 1000:.0f}–{z.max() * 1000:.0f} mm）。"
            "半紙の取り直しではなく、肩・肘のゼロ点が LeRobot とシミュでずれています。"
            "書字再生はまだ危険です。"
        )


def fit_paper(corners_xyz: np.ndarray, touch_z: float) -> dict[str, float]:
    """教示した四隅を書字領域にする。半紙の実寸とは突き合わせない。

    四隅は紙の角ではなく内側に取ってよい。ゼロ点が合っているかは
    check_taught_plane（四隅が同じ机の高さに乗るか）で見る。
    """
    xy = np.asarray(corners_xyz, dtype=np.float64)[:, :2]
    width = float(xy[:, 0].max() - xy[:, 0].min())
    height = float(xy[:, 1].max() - xy[:, 1].min())
    if width < MIN_PAPER_M or height < MIN_PAPER_M:
        raise ValueError(
            f"書字領域が小さすぎます ({width * 1000:.0f}×{height * 1000:.0f} mm)。"
            "四隅をもっと広く取り直してください。"
        )
    return {
        "width": width,
        "height": height,
        "center_x": float((xy[:, 0].min() + xy[:, 0].max()) * 0.5),
        "center_y": float((xy[:, 1].min() + xy[:, 1].max()) * 0.5),
        "surface_z": float(touch_z),
        "margin": 0.015,
    }


def validate_measured_paper(desk: dict, tips: dict | None = None) -> dict:
    """Independent ruler check for the GUI's taught, axis-aligned rectangle.

    The old AABB can include points outside a skewed quadrilateral. Do not call
    that area measured paper. GUI teaches must match a marked rectangle within
    5 mm, including its centre and edge directions.
    """
    measurement = desk.get("paper_measurement_v1")
    if not isinstance(measurement, dict):
        raise ValueError("教示する長方形の奥行き・幅を定規で測り、保存してください")
    expected = np.asarray([measurement["depth_mm"], measurement["width_mm"]], dtype=float)
    if not np.isfinite(expected).all() or np.any(expected < 100) or np.any(expected > 450):
        raise ValueError("教示する長方形は奥行き・幅とも100〜450 mmで実測してください")
    xyz = tips or desk.get("tips_m", {})
    nl, nr, fl, fr, centre = [np.asarray(xyz[n], dtype=float) for n in (
        "paper_near_left", "paper_near_right", "paper_far_left", "paper_far_right", "paper_center_touch",
    )]
    if any(v.shape != (3,) or not np.isfinite(v).all() for v in (nl, nr, fl, fr, centre)):
        raise ValueError("紙の教示位置が不正です")
    edges = np.asarray([fl - nl, fr - nr, nr - nl, fr - fl]) * 1000
    lengths = np.linalg.norm(edges[:, :2], axis=1)
    if np.any(edges[:2, 0] <= 0) or np.any(edges[2:, 1] <= 0):
        raise ValueError("紙の手前・奥または左・右が逆です。図の向きで取り直してください")
    drift = float(max(np.abs(edges[:2, 1]).max(), np.abs(edges[2:, 0]).max()))
    if drift > 5:
        raise ValueError(f"教示した長方形がアームの前後・左右に揃っていません（横ずれ{drift:.1f} mm）。紙を図の向きに合わせてください")
    error = float(np.max(np.abs(lengths - expected[[0, 0, 1, 1]])))
    if error > 5:
        raise ValueError(f"定規の実測と毛先の計算位置が一致しません（最大{error:.1f} mm）。筆の取付長さ・四隅・基準姿勢を確認してください")
    middle_error = float(np.linalg.norm(centre - (nl + nr + fl + fr) / 4) * 1000)
    if middle_error > 5:
        raise ValueError(f"紙の中央が四隅の中央と合いません（{middle_error:.1f} mm）。中央の接触を取り直してください")
    return {"edge_lengths_mm": lengths.tolist(), "ruler_error_max_mm": error,
            "axis_drift_max_mm": drift, "centre_error_mm": middle_error}


def lean_metric(axis: np.ndarray) -> float:
    return float(1.0 - abs(axis[2]))


def infer_tilt_sign(upright_axis: np.ndarray, lean_axis: np.ndarray) -> int:
    if lean_metric(lean_axis) > lean_metric(upright_axis):
        return 1
    if lean_metric(lean_axis) < lean_metric(upright_axis):
        return -1
    raise ValueError("直立と起筆で筆軸の差が出ません。アタッチメントだけ倒して取り直してください。")


def require_ready(desk: dict[str, Any]) -> dict[str, Any]:
    if desk.get("ready") is not True:
        missing = ", ".join(desk_gaps(desk)) or "solve 未実行"
        raise SystemExit(
            f"デスク較正が未完了です（{missing}）。先に scripts/hardware_calibrate.py を実行してください。"
        )
    try:
        _validate_solved_desk(desk)
        fingerprint = desk.get("geometry_fingerprint")
        if fingerprint is not None and fingerprint != geometry_fingerprint(desk):
            raise ValueError("solve 後に教示値または幾何が変わっています")
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise SystemExit(
            f"デスク較正が不正です（{exc}）。実測値を確認して solve をやり直してください。"
        ) from exc
    return desk


def _validate_solved_desk(desk: dict[str, Any]) -> None:
    """Check measured and solved values, including legacy schema-1 desks."""
    gaps = desk_gaps(desk)
    if gaps:
        raise ValueError("未記録: " + ", ".join(gaps))
    if desk.get("schema") != SCHEMA or desk.get("tip_points_down") is not True:
        raise ValueError("schema または穂先の下向き確認が不正です")

    def finite(values: Any, size: int, name: str) -> np.ndarray:
        array = np.asarray(values, dtype=np.float64)
        if array.shape != (size,) or not np.isfinite(array).all():
            raise ValueError(f"{name} は有限の実測値 {size} 個が必要です")
        return array

    for name in (*REQUIRED_POSES, SIM_HOME_POSE):
        finite([desk["poses"][name][joint] for joint in JOINT_NAMES], 6, name)
    finite([desk["sim_home_qpos_deg"][joint] for joint in JOINT_NAMES], 6, "sim_home")
    finite([desk["joint_offsets_deg"][joint] for joint in JOINT_NAMES[:-1]], 5, "offsets")
    scale = finite([desk["brush_tip_length_scale"]], 1, "brush_tip_length_scale")[0]
    expected_scale, rigid_m, _ = brush_geometry(desk["brush_total_cm"], desk["brush_tuft_cm"])
    if not np.isclose(scale, expected_scale, rtol=1e-9, atol=0):
        raise ValueError("把持位置から毛先までの長さと brush_tip_length_scale が一致しません")
    if not np.isclose(float(desk["brush_rigid_cm"]), rigid_m * 100, atol=1e-9):
        raise ValueError("筆軸長は全長から穂長を引いた値にしてください")
    if isinstance(desk["tilt_sign"], bool) or desk["tilt_sign"] not in (-1, 1):
        raise ValueError("tilt_sign は -1 または 1 が必要です")
    tilt = finite(desk["tilt_range"], 2, "tilt_range")
    if not 0 <= tilt[0] < tilt[1] <= 100:
        raise ValueError("tilt_range は 0–100% 内の増加範囲が必要です")
    gripper = finite(desk["gripper_map_rad"], 2, "gripper_map_rad")
    if gripper[0] == gripper[1]:
        raise ValueError("gripper_map_rad の可動幅がありません")
    finite(desk["inkstone_offset_m"], 3, "inkstone_offset_m")
    height = finite([desk["safe_height_m"]], 1, "safe_height_m")[0]
    if height < 0.015:
        raise ValueError("hover は紙面から 15 mm 以上必要です")
    paper = desk["paper"]
    width, height, _, _, _, margin = finite(
        [paper[key] for key in ("width", "height", "center_x", "center_y", "surface_z", "margin")],
        6, "paper",
    )
    if min(width, height) < MIN_PAPER_M or not 0 <= 2 * margin < min(width, height):
        raise ValueError("紙の大きさまたは余白が不正です")
    desk_joint_ranges(desk)
    if desk.get("paper_measurement_v1") is not None:
        validate_measured_paper(desk)


def geometry_fingerprint(desk: dict[str, Any], *, include_brush_split: bool = True) -> str:
    """Bind a solve to its taught inputs and results, independent of USB binding."""
    payload = {key: desk.get(key) for key in (
        "schema", "brush_total_cm", "brush_rigid_cm", "brush_tuft_cm",
        "brush_tip_length_scale", "tip_points_down",
        "sim_home_qpos_deg", "joint_offsets_deg", "gripper_map_rad", "tilt_sign",
        "paper", "inkstone_offset_m", "tilt_range", "safe_height_m",
        "wrist_roll_offset_deg", "lift_deg_per_mm", "tips_m",
    )}
    payload["poses"] = {
        name: (desk.get("poses") or {}).get(name)
        for name in (*REQUIRED_POSES, SIM_HOME_POSE)
    }
    if desk.get("paper_measurement_v1") is not None:
        payload["paper_measurement_v1"] = desk["paper_measurement_v1"]
    if not include_brush_split:
        # Read-only validation of a pre-split calibration during migration.
        payload.pop("brush_total_cm")
        payload.pop("brush_rigid_cm")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def playback_tilt(desk: dict[str, Any]) -> tuple[int, tuple[float, float] | None]:
    require_ready(desk)
    lo, hi = (float(v) for v in desk["tilt_range"])
    return int(desk["tilt_sign"]), (lo, hi)


def playback_wrist_offset(desk: dict[str, Any]) -> float:
    require_ready(desk)
    return float(desk.get("wrist_roll_offset_deg") or 0.0)


def desk_offsets(desk: dict[str, Any]) -> dict[str, float]:
    offsets = desk.get("joint_offsets_deg")
    if not offsets:
        raise ValueError("関節オフセットが未計算です。先に preview → snap sim_home。")
    return {name: float(offsets[name]) for name in JOINT_NAMES[:-1]}


def playback_offsets(desk: dict[str, Any]) -> dict[str, float]:
    require_ready(desk)
    return desk_offsets(desk)


def desk_gripper_map(desk: dict[str, Any]) -> tuple[float, float]:
    """(0% の rad, 100% の rad)。solve 前は MJCF 可動域にしか頼れない。"""
    values = desk.get("gripper_map_rad")
    return (float(values[0]), float(values[1])) if values else GRIPPER_RAD


def taught_ik_seeds(
    desk: dict[str, Any],
) -> tuple[tuple[float, float, float, float, float], ...]:
    """紙に届くと分かっている折り。pan は目標から決まるので落とす。

    初期値を増やすだけの補助なので、教示やオフセットが無ければ黙って諦める。
    """
    poses = desk.get("poses") or {}
    if not desk.get("joint_offsets_deg"):
        return ()
    offsets = desk_offsets(desk)
    gripper_map = desk_gripper_map(desk)
    seeds = []
    for name in PAPER_CORNERS + ("paper_center_touch",):
        if name in poses:
            q = lerobot_to_qpos(
                poses[name], tilt_sign=1, offsets=offsets, gripper_map=gripper_map
            )
            seeds.append(tuple(float(v) for v in q[1:]))
    return tuple(seeds)


def desk_lift_gain(desk: dict[str, Any]) -> float:
    gain = desk.get("lift_deg_per_mm")
    if gain is None:
        raise SystemExit("持ち上げ量が未較正です。solve を掛け直してください。")
    return float(gain)


def hardware_height_metadata(
    desk: dict[str, Any], *, write_lift_mm: float, clear_mm: float
) -> dict[str, float | str]:
    """Return absolute and paper-relative tip heights from the real desk teach.

    ``paper.surface_z`` is the FK height of the taught paper/table plane.  It is
    a local robot-world reference, not a promise about the room floor.  Keeping
    both values in every hardware artifact prevents a later run from silently
    mixing the old simulator surface (12 mm) with the measured desk surface.
    """
    paper = desk.get("paper")
    if not isinstance(paper, dict) or paper.get("surface_z") is None:
        raise SystemExit("紙面 z が未較正です。先に hardware_calibrate.py solve を実行してください。")
    if desk.get("safe_height_m") is None:
        raise SystemExit("搬送高さが未較正です。先に hardware_calibrate.py solve を実行してください。")
    lift = float(write_lift_mm)
    clear = float(clear_mm)
    safe = float(desk["safe_height_m"]) * 1000.0
    if not np.isfinite([lift, clear, safe]).all() or lift < 0.0 or clear < 0.0 or safe <= 0.0:
        raise SystemExit("書字・画間・搬送の高さが不正です。desk較正を確認してください。")
    surface_z = float(paper["surface_z"])
    write_z = surface_z + lift / 1000.0
    air_height = lift + clear
    air_z = surface_z + air_height / 1000.0
    return {
        "height_reference": "paper_table_fk_plane",
        "paper_surface_z_m": surface_z,
        "paper_surface_z_mm": surface_z * 1000.0,
        "write_height_above_paper_mm": lift,
        "write_tip_z_m": write_z,
        "write_tip_z_mm": write_z * 1000.0,
        "air_clearance_mm": clear,
        "air_height_above_paper_mm": air_height,
        "air_tip_z_m": air_z,
        "air_tip_z_mm": air_z * 1000.0,
        "safe_height_above_paper_mm": safe,
        "safe_tip_z_m": surface_z + safe / 1000.0,
        "safe_tip_z_mm": surface_z * 1000.0 + safe,
        "brush_tuft_cm": float(desk["brush_tuft_cm"]),
        "brush_total_cm": float(desk["brush_total_cm"]),
        "brush_rigid_cm": float(desk["brush_rigid_cm"]),
        "brush_tip_length_scale": float(desk["brush_tip_length_scale"]),
        "lift_deg_per_mm": float(desk_lift_gain(desk)),
    }


def desk_suzuri_pull(desk: dict[str, Any]) -> dict[str, float]:
    joints = (desk.get("poses") or {}).get("suzuri_pull") or desk.get("suzuri_pull_deg")
    if not joints:
        raise SystemExit("硯の手前端が未記録です。snap suzuri_pull してください。")
    return {name: float(joints[name]) for name in JOINT_NAMES}


def format_desk(desk: dict[str, Any]) -> str:
    if not desk.get("ready"):
        gaps = ", ".join(desk_gaps(desk)) or "solve 未実行"
        return f"未完了: {gaps}"
    paper = desk["paper"]
    lo, hi = desk["tilt_range"]
    return (
        f"ready  半紙 {paper['width']*1000:.0f}×{paper['height']*1000:.0f} mm  "
        f"中心 ({paper['center_x']*1000:.0f},{paper['center_y']*1000:.0f}) mm  "
        f"紙面 z={paper['surface_z']*1000:.1f} mm\n"
        f"把持→毛先 {desk['brush_total_cm']:.1f} cm（筆軸 {desk['brush_rigid_cm']:.1f} + 穂 {desk['brush_tuft_cm']:.1f} cm）  "
        f"tilt_sign={desk['tilt_sign']}  wrist_roll_off={desk.get('wrist_roll_offset_deg')}°  "
        f"gripper {lo:.0f}–{hi:.0f}%  "
        f"搬送 紙面から+{desk['safe_height_m']*1000:.1f} mm "
        f"(z={(paper['surface_z'] + desk['safe_height_m'])*1000:+.1f} mm)"
    )


def env_config_from_desk(desk: dict[str, Any]) -> EnvConfig:
    require_ready(desk)
    paper = PaperConfig(
        width=float(desk["paper"]["width"]),
        height=float(desk["paper"]["height"]),
        center_x=float(desk["paper"]["center_x"]),
        center_y=float(desk["paper"]["center_y"]),
        surface_z=float(desk["paper"]["surface_z"]),
        margin=float(desk["paper"].get("margin", 0.015)),
    )
    offset = tuple(float(v) for v in desk["inkstone_offset_m"])
    inner = min(paper.width, paper.height) - 2.0 * paper.margin
    glyph = min(0.110, max(0.040, inner * 0.70))
    scale = float(desk["brush_tip_length_scale"])
    _, _, tuft_m = brush_geometry(desk["brush_total_cm"], desk["brush_tuft_cm"])
    joint_ranges = desk_joint_ranges(desk)
    # desk は紙面からの余裕を持つが、env の safe_height と搬送高さは世界座標の絶対 z。
    # 既定値は紙面 12 mm 前提なので、実測した紙面に載せ替える。段差は既定のまま保つ。
    stock = EnvConfig()
    safe_height = paper.surface_z + float(desk["safe_height_m"])
    transport_gap = stock.hardware.upright_transport_height_m - stock.safe_height
    return EnvConfig(
        paper=paper,
        writing_layout=WritingLayoutConfig(single_center_size=glyph),
        hardware=replace(
            HardwareCalibrationConfig(),
            brush_tip_length_scale=scale,
            brush_tuft_length_m=tuft_m,
            base_riser_height_m=TABLE_BASE_RISER_M,
            inkstone_offset_m=(offset[0], offset[1], offset[2]),
            upright_transport_height_m=safe_height + transport_gap,
            gripper_range_rad=desk_gripper_map(desk),
            joint_ranges_rad=joint_ranges,
            reset_ik_seed_folds_rad=taught_ik_seeds(desk),
        ),
        modules=ModuleConfig(
            brush_physics="professional",
            ink_model="professional",
            brushwork="professional",
            # 既定の硯は腕の左、実物は右。offset は平行移動なので拭う縁が硯の
            # 向こう側に回り、届かなくなる。左右反転を持たせるまで墨は手で含ませる。
            inkstone=False,
            professional_exemplar=False,
        ),
        safe_height=safe_height,
        reset_noise=0.0,
        domain_randomization=False,
    )


def hanshi_portrait_paper() -> PaperConfig:
    return PaperConfig(
        width=HANSHI_VERTICAL_M,
        height=HANSHI_HORIZONTAL_M,
        center_x=0.250,
        center_y=0.0,
        surface_z=0.012,
        margin=0.015,
    )


def overlay_desk_hardware(config: EnvConfig, desk: dict[str, Any]) -> EnvConfig:
    """Apply measured rigid-holder + tuft geometry before solving the desk."""
    if desk.get("brush_total_cm") is None or desk.get("brush_tuft_cm") is None:
        raise ValueError("筆の全長と穂長が未記録")
    scale, _, tuft_m = brush_geometry(desk["brush_total_cm"], desk["brush_tuft_cm"])
    return replace(
        config,
        paper=hanshi_portrait_paper(),
        writing_layout=WritingLayoutConfig(single_center_size=0.110),
        hardware=replace(
            config.hardware,
            brush_tip_length_scale=scale,
            brush_tuft_length_m=tuft_m,
            base_riser_height_m=TABLE_BASE_RISER_M,
            inkstone_offset_m=(0.030, 0.0, 0.0),
        ),
    )


def _tip_and_axis(env: Any, qpos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    import mujoco

    env.data.qpos[env._qpos_indices] = qpos
    env.data.qvel[:] = 0.0
    mujoco.mj_forward(env.model, env.data)
    # IK uses the unbent reference; the dynamic tip may lag under paper friction.
    mount = env.data.site_xpos[env._brush_mount_site_id]
    rest = env.data.site_xpos[env._brush_rest_tip_site_id].copy()
    axis = rest - mount
    axis = axis / max(float(np.linalg.norm(axis)), 1e-12)
    return rest, axis


def match_tip_z(env: Any, qpos: np.ndarray, target_z: float) -> np.ndarray:
    """肩だけ動かして穂先 z を target に合わせる。中央で測った mm/deg は奥と手前で効きが違う。"""
    q = np.asarray(qpos, dtype=np.float64).copy()
    z0 = _tip_and_axis(env, q)[0][2]
    probe = q.copy()
    probe[1] += np.deg2rad(1.0)
    dz = _tip_and_axis(env, probe)[0][2] - z0
    if abs(dz) < 1e-7:
        return q
    q[1] += (target_z - z0) / dz * np.deg2rad(1.0)
    return q


def _forward_poses(
    env: Any,
    poses: dict[str, dict[str, float]],
    tilt_sign: int,
    offsets: dict[str, float] | None = None,
    gripper_map: tuple[float, float] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    xyz: dict[str, np.ndarray] = {}
    axes: dict[str, np.ndarray] = {}
    for name, joints in poses.items():
        xyz[name], axes[name] = _tip_and_axis(
            env,
            lerobot_to_qpos(
                joints, tilt_sign=tilt_sign, offsets=offsets, gripper_map=gripper_map
            ),
        )
    return xyz, axes


def gripper_vertical_fit(
    env: Any,
    joints: dict[str, float],
    offsets: dict[str, float] | None = None,
    step: float = 0.5,
) -> tuple[float, float, np.ndarray]:
    """穂軸が最も下を向く MJCF gripper 角、そのときの傾き、穂先位置。

    ID6 の % を使わず関節角を直接振るので、この推定は ID6 の % 較正に依存しない。
    """
    q = lerobot_to_qpos(joints, tilt_sign=1, offsets=offsets)
    best: tuple[float, float, np.ndarray] | None = None
    for d in np.arange(-180.0, 180.0, step):
        xyz, axis = _tip_and_axis(env, np.r_[q[:5], np.deg2rad(float(d))])
        tilt = tilt_from_vertical_deg(axis)
        if best is None or tilt < best[1]:
            best = (float(d), tilt, xyz.copy())
    assert best is not None
    return best


def solve_tip_ik(
    env: Any,
    target: np.ndarray,
    seed: np.ndarray,
    limits: np.ndarray,
    *,
    tolerance: float = 1e-5,
    limit_margin_rad: float = 0.0,
    max_step_rad: float | None = None,
    axis_weight: float = 0.01,
    continuity_weight: float = 0.02,
    free: Sequence[int] | None = None,
) -> np.ndarray:
    """穂先を target へ。手首回転を固定し、既定は ID6 を含む5軸を解く。

    ``max_step_rad`` は連続する筆記点だけに使う。最初の点はhoverからの
    ゆっくりした補間で近づくため、呼び出し側が必要なときだけ指定する。

    ponytail: 残差は FK の差分。速さが要るなら mj_jacSite で解析ヤコビアンを渡す。
    """
    from scipy.optimize import least_squares

    free = list(free) if free is not None else [0, 1, 2, 3, 5]
    q = np.asarray(seed, dtype=np.float64).copy()
    target = np.asarray(target, dtype=np.float64)
    lower = np.asarray(limits, dtype=np.float64)[free, 0] + float(limit_margin_rad)
    upper = np.asarray(limits, dtype=np.float64)[free, 1] - float(limit_margin_rad)
    if max_step_rad is not None:
        step = abs(float(max_step_rad))
        lower = np.maximum(lower, q[free] - step)
        upper = np.minimum(upper, q[free] + step)
    if np.any(upper <= lower):
        raise ValueError("IK の実機安全範囲が狭すぎます")

    def residual(values: np.ndarray) -> np.ndarray:
        trial = q.copy()
        trial[free] = values
        tip, axis = _tip_and_axis(env, trial)
        # 穂軸を縦に保ち、ひとつ前の解へ引っ張る。
        return np.r_[tip - target, axis_weight * axis[:2], continuity_weight * (values - q[free])]

    fit = least_squares(
        residual,
        np.clip(q[free], lower + 1e-6, upper - 1e-6),
        bounds=(lower, upper),
        xtol=tolerance,
        ftol=tolerance,
    )
    q[free] = fit.x
    return q


def fit_suzuri_pull(
    env: Any,
    joints: dict[str, float],
    offsets: dict[str, float],
    gripper_map: tuple[float, float],
    *,
    pull_m: float = SUZURI_PULL_M,
) -> dict[str, float]:
    """墨池の教示から穂先を手前へ pull_m 引いた関節。高さは変えない。"""
    q = lerobot_to_qpos(
        joints, tilt_sign=1, offsets=offsets, gripper_map=gripper_map
    )
    tip, _ = _tip_and_axis(env, q)
    target = tip + np.array([-pull_m, 0.0, 0.0])
    pulled = solve_tip_ik(
        env, target, q, env._joint_limits, free=(0, 1, 2, 3)
    )
    got = _tip_and_axis(env, pulled)[0]
    if np.linalg.norm(got - target) > 0.005:
        raise ValueError(
            f"硯を手前へ {pull_m*100:.0f} cm 引けません（誤差 {np.linalg.norm(got-target)*1000:.0f} mm）。"
        )
    result = qpos_to_lerobot(
        pulled, tilt_sign=1, offsets=offsets, gripper_map=gripper_map
    )
    result["gripper"] = float(joints["gripper"])
    result["wrist_roll"] = float(joints["wrist_roll"])
    return result


def write_z_along_depth(
    x: float | np.ndarray,
    far_x: float,
    near_x: float,
    far_z: float,
    near_z: float,
) -> np.ndarray:
    """奥（+x）ほど高く、手前ほど低く。同じzだと奥がてこで太る。"""
    span = float(near_x) - float(far_x)
    x = np.asarray(x, dtype=np.float64)
    if abs(span) < 1e-9:
        return np.full(x.shape, far_z, dtype=np.float64)
    t = np.clip((x - float(far_x)) / span, 0.0, 1.0)
    return float(far_z) + t * (float(near_z) - float(far_z))


def glyph_cells(paper: PaperConfig, count: int) -> tuple[PaperConfig, ...]:
    """紙の余白内に最大の正方形を置く。3〜4字は縦書き2×2。

    書き手から見た紙の天は腕の奥、つまり +x。お手本は天を +y・右を +x として
    作られる。下手から見て左右がそのままになるのは (x, y) → (y, x)。
    時計回り 90° だと字の右が下手左へ行き、左右が反転する。
    """
    if count not in (1, 2, 3, 4):
        raise ValueError("文字数は1〜4文字にしてください")
    usable_width = paper.width - 2.0 * paper.margin
    usable_height = paper.height - 2.0 * paper.margin
    if min(usable_width, usable_height) <= 0:
        raise ValueError("紙の余白が書字領域を潰しています")
    rows = 1 if count == 1 else 2
    columns = 2 if count >= 3 else 1
    pitch = usable_width / rows
    column_pitch = usable_height / columns
    size = min(pitch, column_pitch)
    far = paper.center_x + 0.5 * usable_width
    return tuple(
        replace(
            paper,
            width=size,
            height=size,
            center_x=far - (i % rows + 0.5) * pitch,
            center_y=paper.center_y + usable_height / 2 - (i // rows + 0.5) * column_pitch,
            # Sheet margin is already applied; don't subtract it again per cell.
            margin=0.0,
        )
        for i in range(count)
    )


def upright_on_paper(points: np.ndarray, cell: PaperConfig) -> np.ndarray:
    """お手本の天（+y）を紙の奥（+x）へ。字の右（+x）は下手右（+y）へ。"""
    centre = np.asarray([cell.center_x, cell.center_y])
    delta = np.asarray(points, dtype=np.float64) - centre
    return centre + np.column_stack((delta[:, 1], delta[:, 0]))


def place_on_paper(points: np.ndarray, cell: PaperConfig) -> np.ndarray:
    """お手本を紙の向きへ転置する。拡大・移動はセル生成側で済ませる。"""
    return upright_on_paper(points, cell)


def refine_arm_offsets(
    env: Any, poses: dict[str, dict[str, float]], offsets: dict[str, float]
) -> dict[str, float]:
    """肩・肘のゼロ点を「机は平ら」から詰める。紙の寸法も ID6 の % 較正も使わない。

    sim_home の目視 L 字は肘で 20° 以上ずれうる。四隅と中央は同じ机に接地しているので、
    穂先 z が揃うという制約のほうがはるかに強い。
    """
    on_desk = PAPER_CORNERS + ("paper_center_touch",)

    def spread(d_lift: float, d_elbow: float) -> float:
        trial = {
            **offsets,
            "shoulder_lift": offsets["shoulder_lift"] + d_lift,
            "elbow_flex": offsets["elbow_flex"] + d_elbow,
        }
        # 探索は粗い刻みで足りる。最終的な穂先位置は 0.5° 刻みで出し直す。
        z = [gripper_vertical_fit(env, poses[name], trial, step=2.0)[2][2] for name in on_desk]
        return float(np.std(z))

    best = (spread(0.0, 0.0), 0.0, 0.0)
    for step, span in ((4.0, 40.0), (0.5, 4.0)):
        centre = best
        for d_lift in np.arange(centre[1] - span, centre[1] + span + step / 2, step):
            for d_elbow in np.arange(centre[2] - span, centre[2] + span + step / 2, step):
                score = spread(float(d_lift), float(d_elbow))
                if score < best[0]:
                    best = (score, float(d_lift), float(d_elbow))
    return {
        **offsets,
        "shoulder_lift": offsets["shoulder_lift"] + best[1],
        "elbow_flex": offsets["elbow_flex"] + best[2],
    }


def fit_lift_gain(
    env: Any,
    joints: dict[str, float],
    offsets: dict[str, float],
    gripper_map: tuple[float, float],
) -> float:
    """毛先を 1 mm 上げるのに要する shoulder_lift の度数。

    教示は腕を支えた脱力状態で取るので穂先は触れるだけだが、再生ではサーボが同じ
    角度まで押し込むので穂が潰れる。肩から先は一体で回るため、数 mm なら xy と
    傾きのずれは無視できる。線形性はここで検算する。
    """
    q = lerobot_to_qpos(joints, tilt_sign=1, offsets=offsets, gripper_map=gripper_map)

    def tip_z(d_deg: float) -> float:
        shifted = np.r_[q[0], q[1] + np.deg2rad(d_deg), q[2:]]
        return float(_tip_and_axis(env, shifted)[0][2])

    per_deg = (tip_z(1.0) - tip_z(-1.0)) / 2.0
    if abs(per_deg) < 1e-5:
        raise ValueError("肩を振っても毛先が上下しません。教示姿勢を確認してください。")
    gain = 0.001 / per_deg
    for want_mm in (2.0, 5.0):
        got_mm = 1000.0 * (tip_z(want_mm * gain) - tip_z(0.0))
        if abs(got_mm - want_mm) > 0.5:
            raise ValueError(
                f"肩だけでは持ち上げが線形になりません（{want_mm:.0f} mm 指示で {got_mm:.1f} mm）。"
            )
    return float(gain)


def fit_gripper_zero(pct: np.ndarray, deg: np.ndarray) -> tuple[float, np.ndarray]:
    """ゼロ点と残差。中央値なので、寝たまま取った教示が混ざっても引きずられない。"""
    zero = float(np.median(deg - GRIPPER_DEG_PER_PCT * pct))
    return zero, deg - (GRIPPER_DEG_PER_PCT * pct + zero)


def fit_gripper_map(
    env: Any, poses: dict[str, dict[str, float]], offsets: dict[str, float] | None = None
) -> tuple[float, float]:
    """直立教示から ID6 のゼロ点を当て、(0% の rad, 100% の rad) を返す。

    直立と申告された姿勢が本当に直立なら、必要な gripper 角は % の一次式に乗る。
    乗らない姿勢は寝たまま取った教示なので、そこで止める。
    """
    names = [name for name in UPRIGHT_POSES if name in poses]
    pct = np.array([float(poses[name]["gripper"]) for name in names])
    deg = np.array([gripper_vertical_fit(env, poses[name], offsets)[0] for name in names])
    zero, resid = fit_gripper_zero(pct, deg)
    bad = [
        (name, float(r), float((d - zero) / GRIPPER_DEG_PER_PCT))
        for name, r, d in zip(names, resid, deg)
        if abs(float(r)) > GRIPPER_FIT_MAX_RESID_DEG
    ]
    if bad:
        detail = "  ".join(
            f"{name} は {abs(r):.0f}° 外れ（ID6 {float(poses[name]['gripper']):.0f}% "
            f"→ 約 {want:.0f}% なら直立）"
            for name, r, want in bad
        )
        raise ValueError(
            "直立と申告された教示が ID6 の一次式に乗りません。寝たまま取った姿勢があります。\n"
            f"{detail}\n該当姿勢を snap し直してください。"
        )
    return (np.deg2rad(zero), np.deg2rad(zero + GRIPPER_DEG_PER_PCT * 100.0))


def id6_for_upright(
    env: Any,
    joints: dict[str, float],
    offsets: dict[str, float] | None = None,
    gripper_map: tuple[float, float] | None = None,
) -> float:
    """穂軸がいちばん下を向く ID6 %。教示のやり直しで狙う値。"""
    best_pct = 0.0
    best_z = 1.0
    for pct in np.arange(0.0, 100.5, 0.5):
        _, axis = _tip_and_axis(
            env,
            lerobot_to_qpos(
                {**joints, "gripper": float(pct)},
                tilt_sign=1,
                offsets=offsets,
                gripper_map=gripper_map,
            ),
        )
        if axis[2] < best_z:
            best_z = float(axis[2])
            best_pct = float(pct)
    return best_pct


def infer_wrist_roll_offset(env: Any, upright_joints: dict[str, float]) -> float:
    """sim_home 由来の roll と突き合わせるための独立推定。取り付け逆なら落とす。

    ID6 は各 roll で最も下を向く角を選ぶので、この推定は ID6 の % 較正に依存しない。
    """
    # ponytail: 5deg scan; finer fit if playback still rolls the tuft.
    tilt, best_off = min(
        (
            (gripper_vertical_fit(env, upright_joints, {"wrist_roll": float(off)})[1], float(off))
            for off in np.arange(-180.0, 180.0, 5.0)
        ),
        key=lambda pair: pair[0],
    )
    if tilt > 20.0:
        raise ValueError(
            "直立を机向きにできません。筆の取り付けと手首回転（縦軸）を確認してください。"
        )
    return best_off


def solve_desk(desk: dict[str, Any]) -> dict[str, Any]:
    gaps = desk_gaps(desk)
    if gaps:
        raise ValueError("未記録: " + ", ".join(gaps))

    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv

    scale, _, _ = brush_geometry(desk["brush_total_cm"], desk["brush_tuft_cm"])
    poses = desk["poses"]
    env = CalligraphyEnv(
        task="line",
        config=overlay_desk_hardware(
            EnvConfig(reset_noise=0.0, domain_randomization=False), desk
        ),
    )
    offsets = desk_offsets(desk)
    try:
        env.reset(seed=0)
        roll_scan = infer_wrist_roll_offset(env, poses["upright"])
        sim_home_offsets = offsets
        offsets = refine_arm_offsets(env, poses, offsets)
        gripper_map = fit_gripper_map(env, poses, offsets)
        xyz, axes = _forward_poses(
            env, poses, tilt_sign=1, offsets=offsets, gripper_map=gripper_map
        )
        # 較正済みの写像は向きも含む。ここで反転が要るなら較正と教示が矛盾している。
        tilt_sign = infer_tilt_sign(axes["upright"], axes["lean_toward_paper"])
        if tilt_sign < 0:
            raise ValueError(
                "起筆が直立より立って見えます。lean_toward_paper を寝る側で取り直してください。"
            )
        upright_pct = id6_for_upright(
            env, poses[SIM_HOME_POSE], offsets, gripper_map=gripper_map
        )
        lift_gain = fit_lift_gain(env, poses["paper_center_touch"], offsets, gripper_map)
        # GUI ink motion always uses two explicitly taught endpoints. Never
        # invent the historical 70 mm pull for an unknown inkstone.
        suzuri_pull = poses.get("suzuri_pull")
        if suzuri_pull is None and not desk.get("gui_profile_v2"):
            suzuri_pull = fit_suzuri_pull(env, poses["suzuri_pool"], offsets, gripper_map)
    finally:
        env.close()

    g_min = min(float(poses["tilt_min"]["gripper"]), float(poses["tilt_max"]["gripper"]))
    g_max = max(float(poses["tilt_min"]["gripper"]), float(poses["tilt_max"]["gripper"]))
    corners = np.stack([xyz[name] for name in PAPER_CORNERS], axis=0)
    check_taught_plane(corners)
    if desk.get("paper_measurement_v1") is not None:
        validate_measured_paper(desk, xyz)
    paper = fit_paper(corners, xyz["paper_center_touch"][2])
    hover_clearance = float(xyz["hover_center"][2] - paper["surface_z"])
    if hover_clearance < 0.015:
        raise ValueError("hover が紙面に近すぎます。もっと上げて取り直してください。")
    ink = InkstoneConfig()
    pool = xyz["suzuri_pool"]
    desk = dict(desk)
    # Motor limits are expressed in qpos using these mappings. A new mapping
    # requires sync-limits again; retaining the old ranges would move the stops.
    if desk.get("joint_offsets_deg") != offsets or desk.get("gripper_map_rad") != list(gripper_map):
        desk["joint_ranges_rad"] = None
    desk["pressure_calibration_v1"] = None
    desk["brush_tip_length_scale"] = scale
    desk["tilt_sign"] = int(tilt_sign)
    desk["gripper_map_rad"] = [float(gripper_map[0]), float(gripper_map[1])]
    desk["wrist_roll_offset_deg"] = offsets["wrist_roll"]
    desk["wrist_roll_offset_scan_deg"] = roll_scan
    desk["joint_offsets_deg"] = dict(offsets)
    desk["joint_offsets_sim_home_deg"] = dict(sim_home_offsets)
    desk["upright_id6_pct"] = upright_pct
    desk["lift_deg_per_mm"] = lift_gain
    desk["suzuri_pull_deg"] = suzuri_pull
    desk["tip_points_down"] = True
    desk["paper"] = paper
    desk["inkstone_offset_m"] = [
        float(pool[0] - ink.center_x),
        float(pool[1] - ink.center_y),
        float(pool[2] - ink.pool_surface_z),
    ]
    desk["tilt_range"] = [g_min, g_max]
    desk["safe_height_m"] = hover_clearance
    desk["ready"] = True
    desk["tips_m"] = {name: [float(v) for v in xyz[name]] for name in REQUIRED_POSES}
    _validate_solved_desk(desk)
    desk["geometry_fingerprint"] = geometry_fingerprint(desk)
    return desk
