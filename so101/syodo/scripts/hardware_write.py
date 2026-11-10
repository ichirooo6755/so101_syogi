#!/usr/bin/env python3
"""Dump expert joints from sim, or play a taught paper-edge stroke.

Sim dump needs a solved desk. Hardware playback and taught stroke
(手前左→手前右) additionally require sync-limits:
  ~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py stroke

硯は Leader で一度録り、play の書字前に毎回再生する:
  ~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py record-suzuri
本書きは硯2往復のあと、穂先を硯に残したまま ID5 を90°回して整える:
  ./scripts/hw-write 文字
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import replace
import csv
import hashlib
import json
import os
import select
import shutil
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from so101_calligraphy.hardware_desk import (
    DEFAULT_DESK_PATH,
    DEFAULT_LEADER_PORT,
    DEFAULT_PORT,
    LEADER_ID,
    ROBOT_ID,
    _tip_and_axis,
    env_config_from_desk,
    format_joints,
    glyph_cells,
    lerobot_to_qpos,
    load_desk,
    playback_tilt,
    desk_gripper_map,
    desk_lift_gain,
    desk_suzuri_pull,
    desk_fingerprint,
    desk_joint_ranges,
    hardware_height_metadata,
    playback_offsets,
    place_on_paper,
    write_z_along_depth,
    pose_deg,
    qpos_to_lerobot,
    require_ready,
    require_joint_ranges,
    save_desk,
    solve_tip_ik,
    taught_ichi_waypoints,
)

from so101_calligraphy.config import JOINT_NAMES
from so101_calligraphy.camera_watchdog import CameraWatchdog, CameraWatchdogConfig

ACCEL = 200
CRUISE_VELOCITY = 900
P_GAIN = 16
# ponytail: position-position bilateral. Lower P so paper contact is a spring, not a fight.
LEADER_BILATERAL_P = 8
SUZURI_TRIPS = 2
SUZURI_AIR_MM = 15.0
SUZURI_LIFT_MM = 3.0
SUZURI_GROOM_ROLL_DEG = 90.0
TRAVEL_S = 4.0
DEFAULT_SUZURI_PATH = Path("data/hardware/suzuri.npz")
DEFAULT_SUZURI_GROOM_PATH = Path("data/hardware/suzuri-groom.npz")
DEFAULT_LEADER_REFERENCE_PATH = Path("data/hardware/leader-reference.json")
RECORD_HZ = 30.0
COMMAND_HZ = 30.0
BILATERAL_HZ = 15.0
BILATERAL_STEP_DEG = 5.0
BILATERAL_STEP_GRIP = 5.0
TRACE_SCHEMA = 5
TAUGHT_SCHEMA = 2
TAUGHT_WORDS = ("文字", "学習", "菅原")
IK_LIMIT_MARGIN_RAD = np.deg2rad(2.0)
IK_MAX_STEP_RAD = np.deg2rad(5.0)
LEADER_ALIGN_RAD = np.deg2rad(5.0)
LEADER_STABILITY_RAD = np.deg2rad(2.0)
TAUGHT_PRESSURE_CORRECTION_RAD = np.deg2rad(0.5)
PRESSURE_NOMINAL = 0.72
PRESSURE_LIFTS_MM = (12.0, 10.0, 8.0, 6.0, 4.0)
PRESSURE_LINE_LENGTH_M = 0.050
MAX_TILT_DEG = 8.0
DEFAULT_AIR_HEIGHT_MM = 60.0
DEFAULT_STANDBY_HEIGHT_MM = 100.0
DEFAULT_WRITE_LIFT_MM = 8.0
# ponytail: 手前は肩の dz/deg が奥の半分で、同じzでは紙に押し込めない。teach-referenceの閉ループ筆圧が取れたら捨てる。
DEFAULT_LOWER_CELL_EXTRA_PRESS_MM = 20.0
# ponytail: 字の宀は下段の奥側でてこが強く太る。子の深さは保ち宀だけ戻す。
DEFAULT_U_KANMURI_LIFT_MM = 8.0
U_KANMURI_STROKES = {"字": 3}


def _camera_roi(value: str) -> tuple[float, float, float, float]:
    try:
        roi = tuple(float(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("camera ROIはx0,y0,x1,y1です") from exc
    if len(roi) != 4:
        raise argparse.ArgumentTypeError("camera ROIはx0,y0,x1,y1の4値です")
    try:
        CameraWatchdogConfig(roi=roi)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return roi


def _new_run_dir() -> Path:
    path = Path("runs") / "hardware-two-character" / time.strftime("%Y%m%d-%H%M%S")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _npz_kanji(path: Path) -> str | None:
    try:
        data = np.load(path, allow_pickle=True)
    except (OSError, ValueError):
        return None
    if "kanji" not in data:
        return None
    return str(np.asarray(data["kanji"]).item())


def _resolve_play_path(
    value: str,
    *,
    tmp_dir: Path | None = None,
    run_dir: Path | None = None,
) -> Path:
    path = Path(value)
    if path.exists():
        return path
    if len(value) not in (1, 2, 3, 4):
        raise SystemExit(f"軌道ファイルがありません: {value}")
    tmp_dir = tmp_dir or Path("/tmp")
    run_dir = run_dir or (ROOT / "runs" / "hardware-two-character")
    hits: list[tuple[float, Path]] = []
    candidates = [tmp_dir / f"{value}.npz"]
    if tmp_dir.is_dir():
        candidates.extend(tmp_dir.glob("*.npz"))
    if run_dir.is_dir():
        candidates.extend(run_dir.glob(f"*/trace-{value}.npz"))
        candidates.extend(run_dir.glob("*/trace.npz"))
    for candidate in candidates:
        if not candidate.is_file() or candidate.stat().st_size > 20_000_000:
            continue
        if _npz_kanji(candidate) == value:
            hits.append((candidate.stat().st_mtime, candidate))
    if not hits:
        raise SystemExit(f"{value}のtraceがありません。先に trace {value} を実行してください。")
    hits.sort()
    return hits[-1][1]


def _dump(args: argparse.Namespace) -> None:
    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
    from so101_calligraphy.trajectory.kanjivg import load_kanjivg_character

    config = env_config_from_desk(desk)
    trajectory = load_kanjivg_character(
        args.kanji, cache_dir=args.kanjivg_cache, paper=config.paper
    )
    env = CalligraphyEnv(trajectory=trajectory, config=config)
    try:
        env.reset(seed=0, options={"layout_index": 0})
        rows = []
        xyz = []
        info: dict = {}
        for _ in range(args.max_steps):
            q = env.data.qpos[env._qpos_indices].copy()
            rows.append(q)
            xyz.append(env.brush_position.copy())
            _, _, terminated, truncated, info = env.step(env.expert_action())
            if terminated or truncated:
                break
        qpos = np.asarray(rows, dtype=np.float64)
        tip = np.asarray(xyz, dtype=np.float64)
        dt = float(env.model.opt.timestep * env.config.frame_skip)
        np.savez(
            args.out,
            qpos=qpos,
            tip_xyz=tip,
            dt=np.asarray(dt),
            kanji=np.asarray(args.kanji),
            desk=np.asarray(str(args.desk)),
            termination=np.asarray(info.get("termination_reason", "")),
        )
        print(
            f"saved {args.out} steps={len(qpos)} dt={dt:.4f}s "
            f"tip_z=[{tip[:, 2].min():.3f},{tip[:, 2].max():.3f}] "
            f"end={info.get('termination_reason')}"
        )
    finally:
        env.close()


def _resample(a: np.ndarray, b: np.ndarray, step: float) -> np.ndarray:
    """a を含まず b で終わる等間隔の点列。区間をつないでも重複が出ない。"""
    n = max(1, int(np.ceil(float(np.linalg.norm(b - a)) / step)))
    return a + np.outer(np.arange(1, n + 1) / n, b - a)


def _resample_with_values(
    a: np.ndarray,
    b: np.ndarray,
    value_a: float,
    value_b: float,
    step: float,
) -> tuple[np.ndarray, np.ndarray]:
    n = max(1, int(np.ceil(float(np.linalg.norm(b - a)) / step)))
    alpha = np.arange(1, n + 1, dtype=np.float64) / n
    return a + alpha[:, None] * (b - a), value_a + alpha * (value_b - value_a)


def _apply_depth_profile(
    targets: np.ndarray,
    paper,
    far_z: float,
    near_z: float,
    *,
    air_z: float,
    pen_down: np.ndarray,
) -> np.ndarray:
    """Set the final tip targets before IK; preserve the 60 mm transfer plane."""
    depth = glyph_cells(paper, 2)
    dz = write_z_along_depth(
        targets[:, 0], depth[0].center_x, depth[1].center_x, far_z, near_z,
    ) - far_z
    # Full compensation on the paper (including deliberately raised roof
    # strokes), fading continuously to zero on ascent/descent. Horizontal air
    # travel must keep its original clearance even above the lower cell.
    highest_contact = float(np.max(targets[np.asarray(pen_down, dtype=bool), 2]))
    if air_z - highest_contact < 0.015:
        raise SystemExit("書字位置と画間高さには15 mm以上の差が必要です")
    blend = np.clip((air_z - targets[:, 2]) / (air_z - highest_contact), 0.0, 1.0)
    out = targets.copy()
    out[:, 2] += dz * blend
    return out


class HardwarePathError(SystemExit):
    """A candidate layout does not satisfy the existing motion constraints."""


def _solve_hardware_targets(
    desk: dict,
    config,
    targets: np.ndarray,
    tolerance_mm: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv

    env = CalligraphyEnv(task="line", config=config)
    try:
        env.reset(seed=0, options={"layout_index": 0})
        limits = env._joint_limits
        q = lerobot_to_qpos(
            desk["poses"]["paper_center_touch"],
            tilt_sign=1,
            offsets=playback_offsets(desk),
            gripper_map=desk_gripper_map(desk),
        )
        rows = []
        errors = []
        for index, target in enumerate(targets):
            q = solve_tip_ik(
                env,
                target,
                q,
                limits,
                limit_margin_rad=IK_LIMIT_MARGIN_RAD,
                max_step_rad=None if index == 0 else IK_MAX_STEP_RAD,
                continuity_weight=0.002,
            )
            rows.append(q.copy())
            tip, axis = _tip_and_axis(env, q)
            errors.append(np.linalg.norm(tip - target))
            tilt = float(np.degrees(np.arccos(np.clip(-axis[2], -1.0, 1.0))))
            if tilt > MAX_TILT_DEG:
                raise HardwarePathError(
                    f"筆軸が8°を超えました（{tilt:.2f}°）。紙面または教示姿勢を確認してください。"
                )
            if np.any(q < limits[:, 0] + IK_LIMIT_MARGIN_RAD) or np.any(
                q > limits[:, 1] - IK_LIMIT_MARGIN_RAD
            ):
                raise HardwarePathError("IK解が関節端2°以内に収まりません")
            if index and np.max(np.abs(q - rows[-2])) > IK_MAX_STEP_RAD + 1e-8:
                raise HardwarePathError("筆記中の隣接関節変化が5°を超えました")
        worst = float(np.max(errors)) * 1000.0
        if worst > tolerance_mm:
            raise HardwarePathError(
                f"逆解が届かない点があります（最大 {worst:.1f} mm）。"
                "字を小さくするか、紙の位置を教示し直してください。"
            )
        qpos = np.stack(rows, axis=0)
        dq_dz = []
        for target, row in zip(targets, qpos):
            raised = solve_tip_ik(
                env,
                target + np.array([0.0, 0.0, 0.001]),
                row,
                limits,
                limit_margin_rad=IK_LIMIT_MARGIN_RAD,
                max_step_rad=IK_MAX_STEP_RAD,
                continuity_weight=0.002,
            )
            dq_dz.append((raised - row) / 0.001)
        return qpos, np.asarray(dq_dz, dtype=np.float64), worst
    finally:
        env.close()


def _save_layout_preview(path: Path, paper, cells, word: str, targets, down, indices) -> None:
    """Save a reader-oriented plan in millimetres, including frame occupancy."""
    from html import escape

    left = paper.center_y - paper.height / 2
    top = paper.center_x + paper.width / 2
    def xy(point):
        return ((point[1] - left) * 1000, (top - point[0]) * 1000)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {paper.height*1000} {paper.width*1000}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<title>書字計画（指令軌道。実測筆跡ではありません）</title>']
    layout = []
    down = np.asarray(down, dtype=bool)
    indices = np.asarray(indices)
    for i, cell in enumerate(cells):
        x, y = xy([cell.center_x + cell.width / 2, cell.center_y - cell.height / 2])
        parts.append(f'<rect x="{x}" y="{y}" width="{cell.height*1000}" height="{cell.width*1000}" fill="none" stroke="#94a3b8" stroke-width="0.35"/>')
        parts.append(f'<text x="{x+1}" y="{y+4}" font-size="3" fill="#64748b">{i+1}: {escape(word[i])}</text>')
        points = targets[down & (indices == i), :2]
        span = np.ptp(points, axis=0) * 1000
        layout.append({"character": word[i], "cell": i, "center_xy_m": [cell.center_x, cell.center_y],
                       "frame_mm": cell.width * 1000, "stroke_span_xy_mm": span.tolist(),
                       "long_axis_fill_ratio": float(span.max() / (cell.width * 1000))})
    for i in range(1, len(targets)):
        if not down[i] or indices[i] != indices[i-1]:
            continue
        a, b = xy(targets[i-1]), xy(targets[i])
        parts.append(f'<path d="M{a[0]:.3f},{a[1]:.3f} L{b[0]:.3f},{b[1]:.3f}" stroke="#172554" stroke-width="0.7" fill="none"/>')
    parts.append('</svg>')
    path.with_suffix('.layout.svg').write_text('\n'.join(parts), encoding='utf-8')
    path.with_suffix('.layout.json').write_text(json.dumps({"word": word, "order": "top_to_bottom_right_to_left", "physical_writing_verified": False, "cells": layout}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _trace(args: argparse.Namespace) -> None:
    # Search largest first. Only geometric failures permit a smaller candidate;
    # calibration, font and data errors remain fatal. Never weaken motion gates.
    for percent in ([100] if getattr(args, "glyph_mm", None) else range(100, 79, -2)):
        try:
            _trace_candidate(args, percent / 100)
            return
        except HardwarePathError as exc:
            if percent == 80 or getattr(args, "glyph_mm", None):
                raise
            print(f"枡の{percent}%では可動域条件を満たしません: {exc} 次の寸法を検証します。")


def _trace_candidate(args: argparse.Namespace, glyph_scale: float) -> None:
    """お手本を実機の紙面へ写し、5軸IKと圧力メタデータを保存する。"""

    from so101_calligraphy.trajectory.kanjivg import fetch_kanjivg, load_kanjivg_character
    from so101_calligraphy.trajectory.professional import fit_trajectory_to_exemplar_shape
    from so101_calligraphy.trajectory.profile import build_stroke_profile

    if len(args.kanji) not in (1, 2, 3, 4):
        raise SystemExit("trace は1〜4文字に対応します（3〜4文字は縦書き2×2）")
    for character in args.kanji:
        try:
            fetch_kanjivg(character, cache_dir=args.kanjivg_cache)
        except (RuntimeError, ValueError) as exc:
            raise SystemExit(f"KanjiVGにありません: {character}") from exc
    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    if args.out is None:
        args.out = _new_run_dir() / f"trace-{args.kanji}.npz"
    config = env_config_from_desk(desk)
    cells = glyph_cells(config.paper, len(args.kanji))
    requested_mm = getattr(args, "glyph_mm", None)
    if requested_mm is not None:
        if not np.isfinite(requested_mm) or requested_mm < 30:
            raise SystemExit("文字の大きさは30 mm以上で指定してください")
        if requested_mm > min(c.width for c in cells) * 1000 + 1e-6:
            raise SystemExit(f"指定した{requested_mm:g} mm角の文字は入りません（最大{min(c.width for c in cells)*1000:.1f} mm角）。文字数を減らしてください。")
        cells = tuple(replace(c, width=requested_mm / 1000, height=requested_mm / 1000) for c in cells)
    measured_heights = bool(getattr(args, "calibrated_heights", False))
    reference = None
    pressure_fallback = None
    if len(args.kanji) >= 2 or measured_heights:
        reference_path = Path(
            getattr(args, "reference", DEFAULT_LEADER_REFERENCE_PATH)
        )
        if not measured_heights and len(args.kanji) == 2 and reference_path.exists():
            reference = _load_leader_reference(reference_path, desk)
        else:
            pressure_fallback = desk.get("pressure_calibration_v1")
            if not isinstance(pressure_fallback, dict) or pressure_fallback.get(
                "desk_fingerprint"
            ) != desk_fingerprint(desk):
                raise SystemExit(
                    "Leader基準がなく、現在のdesk用の筆圧フォールバックもありません。"
                    "teach-referenceを実行してください。"
                )
    air_mm = float(getattr(args, "air_mm", DEFAULT_AIR_HEIGHT_MM))
    standby_mm = float(getattr(args, "standby_mm", DEFAULT_STANDBY_HEIGHT_MM))
    if not np.isfinite([air_mm, standby_mm]).all() or not 15 <= air_mm <= standby_mm <= 150:
        raise SystemExit("移動高さは15〜150 mm、待機高さは移動高さ以上で指定してください")
    clear_mm = air_mm - float(args.lift_mm)
    if clear_mm < 15.0:
        raise SystemExit(
            f"書字高さが高すぎて画間 {DEFAULT_AIR_HEIGHT_MM:.0f} mm を取れません。"
        )
    height = hardware_height_metadata(
        desk, write_lift_mm=args.lift_mm, clear_mm=clear_mm
    )
    air_z = float(height["air_tip_z_m"])
    if reference is not None:
        write_z_by_cell = [
            float(reference["cells"][str(cell)]["write_tip_z_m"])
            for cell in range(2)
        ]
    elif pressure_fallback is not None:
        try:
            write_z_by_cell = [
                float(desk["paper"]["surface_z"])
                + float(pressure_fallback["cells"][str(cell % 2)]["fallback_lift_mm"])
                / 1000.0
                for cell in range(len(cells))
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(
                "上下段別の固定筆圧がありません。teach-referenceを実行してください。"
            ) from exc
    else:
        write_z_by_cell = [float(height["write_tip_z_m"])]
    if measured_heights:
        rows = glyph_cells(config.paper, 2)
        zfar = config.paper.surface_z + float(pressure_fallback["cells"]["0"]["fallback_lift_mm"]) / 1000
        znear = config.paper.surface_z + float(pressure_fallback["cells"]["1"]["fallback_lift_mm"]) / 1000
        write_z_by_cell = [float(write_z_along_depth(c.center_x, rows[0].center_x, rows[1].center_x, zfar, znear)) for c in cells]
    if not measured_heights and reference is None and len(write_z_by_cell) >= 2:
        extra = DEFAULT_LOWER_CELL_EXTRA_PRESS_MM / 1000.0
        for index in range(len(write_z_by_cell)):
            write_z_by_cell[index] = write_z_by_cell[0] - (index % 2) * extra
    if len(cells) >= 3:
        _grid_pressure_calibration(desk, len(cells))
    ik_z = float(write_z_by_cell[0])
    if any(air_z - write_z < 0.015 for write_z in write_z_by_cell):
        raise SystemExit("画間高さがセル別の良い筆圧位置から15 mm以上ありません。")
    points: list[np.ndarray] = []
    down: list[bool] = []
    cell_index: list[int] = []
    pressure: list[float] = []
    here = None

    def append(
        point: np.ndarray,
        is_down: bool,
        cell_no: int,
        target_pressure: float = 0.0,
    ) -> None:
        points.append(np.asarray(point, dtype=np.float64))
        down.append(bool(is_down))
        cell_index.append(int(cell_no))
        pressure.append(float(target_pressure) if is_down else 0.0)

    def append_leg(
        start: np.ndarray,
        end: np.ndarray,
        is_down: bool,
        cell_no: int,
        pressure_start: float = 0.0,
        pressure_end: float = 0.0,
    ) -> None:
        sampled, values = _resample_with_values(
            start,
            end,
            pressure_start,
            pressure_end,
            args.step_mm / 1000.0,
        )
        for point, value in zip(sampled, values):
            append(point, is_down, cell_no, float(value))

    for cell_no, (character, cell) in enumerate(zip(args.kanji, cells)):
        cell = replace(cell, width=cell.width * glyph_scale, height=cell.height * glyph_scale)
        write_z = write_z_by_cell[cell_no] if reference is not None else ik_z
        trajectory = fit_trajectory_to_exemplar_shape(
            load_kanjivg_character(
                character, cache_dir=args.kanjivg_cache, paper=cell
            ),
            cell,
            padding=0.002,
        )
        for stroke_i, stroke in enumerate(trajectory.strokes):
            profile = build_stroke_profile(stroke)
            xy = place_on_paper(stroke.points, cell)
            stroke_z = write_z
            if (
                not measured_heights and reference is None
                and stroke_i < U_KANMURI_STROKES.get(character, 0)
            ):
                stroke_z = write_z + DEFAULT_U_KANMURI_LIFT_MM / 1000.0
            over = np.r_[xy[0], air_z]
            if here is None:
                append(over, False, cell_no)
            else:
                append_leg(points[-1], np.r_[here[:2], air_z], False, -1)
                append_leg(points[-1], over, False, cell_no)
            append_leg(points[-1], np.r_[xy[0], stroke_z], False, cell_no)
            previous_pressure = float(profile.pressure[0])
            # The arrival at the stroke origin is already contact. Include it
            # in feedback, contact replay and the measured planned footprint.
            down[-1] = True
            pressure[-1] = previous_pressure
            for point, target_pressure in zip(xy[1:], profile.pressure[1:]):
                append_leg(
                    points[-1],
                    np.r_[point, stroke_z],
                    True,
                    cell_no,
                    previous_pressure,
                    float(target_pressure),
                )
                previous_pressure = float(target_pressure)
            here = points[-1]
    append_leg(points[-1], np.r_[here[:2], air_z], False, -1)
    targets = np.stack(points, axis=0)

    if measured_heights:
        # Apply the measured two-height profile at every contact point, also
        # for a single glyph. Do not substitute the old fixed -20 mm slope.
        measured_z = write_z_along_depth(targets[:, 0], rows[0].center_x, rows[1].center_x, zfar, znear)
        blend = np.clip((air_z - targets[:, 2]) / (air_z - ik_z), 0, 1)
        targets[:, 2] += blend * (measured_z - ik_z)
    elif reference is None:
        targets = _apply_depth_profile(
            targets, config.paper, ik_z,
            ik_z - DEFAULT_LOWER_CELL_EXTRA_PRESS_MM / 1000.0,
            air_z=air_z, pen_down=np.asarray(down, dtype=bool),
        )
    # Solve the actual commanded geometry once, carrying the preceding pose
    # forward and enforcing the 5-degree step bound. Never extrapolate a local
    # 1 mm derivative by 20 mm or silently clip a completed trajectory.
    qpos, dq_dz, worst = _solve_hardware_targets(
        desk, config, targets, args.tolerance_mm
    )
    air_targets = targets.copy()
    air_targets[:, 2] = air_z
    air_qpos, _, _ = _solve_hardware_targets(
        desk, config, air_targets, args.tolerance_mm
    )
    standby_target = np.asarray(
        [
            config.paper.center_x,
            config.paper.center_y,
            config.paper.surface_z + standby_mm / 1000.0,
        ],
        dtype=np.float64,
    )
    standby_qpos, _, standby_worst = _solve_hardware_targets(
        desk, config, standby_target[None, :], args.tolerance_mm
    )
    worst = max(worst, standby_worst)
    dt = (args.step_mm / 1000.0) / (args.speed_mm_s / 1000.0)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        args.out,
        qpos=qpos,
        air_qpos=air_qpos,
        dq_dz=dq_dz,
        pen_down=np.asarray(down, dtype=bool),
        cell_index=np.asarray(cell_index, dtype=np.int8),
        target_pressure=np.asarray(pressure, dtype=np.float64),
        expected_tip_xyz=targets,
        standby_qpos=standby_qpos[0],
        standby_tip_xyz=standby_target,
        standby_height_above_paper_mm=standby_mm,
        cell_write_tip_z_m=np.asarray(write_z_by_cell, dtype=np.float64),
        command_hz=COMMAND_HZ,
        dt=dt,
        kanji=args.kanji,
        desk=str(args.desk),
        desk_fingerprint=desk_fingerprint(desk),
        motor_calibration_sha256=str(desk.get("motor_calibration_sha256") or ""),
        nominal_lift_mm=float(args.lift_mm),
        paper_surface_z_m=float(height["paper_surface_z_m"]),
        write_height_above_paper_mm=float(height["write_height_above_paper_mm"]),
        write_tip_z_m=float(height["write_tip_z_m"]),
        air_clearance_mm=float(height["air_clearance_mm"]),
        air_height_above_paper_mm=float(height["air_height_above_paper_mm"]),
        air_tip_z_m=float(height["air_tip_z_m"]),
        safe_height_above_paper_mm=float(height["safe_height_above_paper_mm"]),
        safe_tip_z_m=float(height["safe_tip_z_m"]),
        brush_tuft_cm=float(height["brush_tuft_cm"]),
        brush_total_cm=float(height["brush_total_cm"]),
        brush_rigid_cm=float(height["brush_rigid_cm"]),
        brush_tip_length_scale=float(height["brush_tip_length_scale"]),
        lift_deg_per_mm=float(height["lift_deg_per_mm"]),
        height_metadata_json=json.dumps(height, sort_keys=True, ensure_ascii=False),
        reference_json=(
            "" if reference is None else json.dumps(reference, sort_keys=True, ensure_ascii=False)
        ),
        reference_sha256=("" if reference is None else str(reference["reference_sha256"])),
        pressure_calibration_sha256=_canonical_sha256(desk.get("pressure_calibration_v1") or {}),
        trace_schema=TRACE_SCHEMA,
        glyph_scale=glyph_scale,
        height_profile_kind="measured_pressure" if measured_heights else "legacy",
        requested_glyph_mm=requested_mm or 0.0,
    )
    _save_layout_preview(args.out, config.paper, cells, args.kanji, targets, down, cell_index)
    print(
        f"保存 {args.out} 点数={len(qpos)} 接地={sum(down)} "
        f"所要={len(qpos) * dt:.0f}s 逆解の最大誤差={worst:.2f} mm "
        f"紙面 z={height['paper_surface_z_mm']:+.1f} mm / "
        f"書字 z={height['write_tip_z_mm']:+.1f} mm "
        f"(セル別 {', '.join(f'{value*1000:+.1f}' for value in write_z_by_cell)} mm) / "
        f"移動 紙面+{height['air_height_above_paper_mm']:.0f} mm / "
        f"待機 紙面+{standby_mm:.0f} mm"
    )


def _pressure_plan(args: argparse.Namespace) -> None:
    """上下セルの5段階試験線を作り、実機較正用NPZへ保存する。"""

    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    if args.out is None:
        args.out = _new_run_dir() / "pressure-plan.npz"
    config = env_config_from_desk(desk)
    cells = glyph_cells(config.paper, 2)
    lifts_mm = getattr(args, "lifts_mm", PRESSURE_LIFTS_MM)
    if len(lifts_mm) != 5 or not np.isfinite(lifts_mm).all() or min(lifts_mm) < 0 or max(lifts_mm) > 15:
        raise SystemExit("筆圧試験は紙面から0〜15 mmの5段階で指定してください")
    height = hardware_height_metadata(desk, write_lift_mm=max(lifts_mm), clear_mm=args.clear_mm)
    points: list[np.ndarray] = []
    down: list[bool] = []
    cell_index: list[int] = []
    line_index: list[int] = []
    here: np.ndarray | None = None

    def append(point: np.ndarray, is_down: bool, cell_no: int, line_no: int) -> None:
        points.append(np.asarray(point, dtype=np.float64))
        down.append(bool(is_down))
        cell_index.append(int(cell_no))
        line_index.append(int(line_no))

    def leg(start: np.ndarray, end: np.ndarray, is_down: bool, cell_no: int, line_no: int) -> None:
        for point in _resample(start, end, args.step_mm / 1000.0):
            append(point, is_down, cell_no, line_no)

    air_z = float(height["air_tip_z_m"])
    y0 = config.paper.center_y - PRESSURE_LINE_LENGTH_M / 2.0
    y1 = config.paper.center_y + PRESSURE_LINE_LENGTH_M / 2.0
    for cell_no, cell in enumerate(cells):
        for line_no, lift_mm in enumerate(lifts_mm):
            write_z = config.paper.surface_z + lift_mm / 1000.0
            x = cell.center_x + np.linspace(-0.035, 0.035, len(PRESSURE_LIFTS_MM))[line_no]
            start_air = np.asarray([x, y0, air_z])
            start_write = np.asarray([x, y0, write_z])
            end_write = np.asarray([x, y1, write_z])
            if here is None:
                append(start_air, False, cell_no, line_no)
            else:
                leg(here, np.r_[here[:2], air_z], False, -1, -1)
                leg(points[-1], start_air, False, cell_no, line_no)
            leg(points[-1], start_write, False, cell_no, line_no)
            leg(points[-1], end_write, True, cell_no, line_no)
            here = points[-1]
    leg(points[-1], np.r_[here[:2], air_z], False, -1, -1)
    # End where the trial starts. After the air baseline, the same qpos path
    # begins again; previously this jumped from the last row to the first.
    leg(points[-1], points[0].copy(), False, -1, -1)
    targets = np.stack(points, axis=0)
    config = env_config_from_desk(desk)
    qpos, dq_dz, worst = _solve_hardware_targets(
        desk, config, targets, args.tolerance_mm
    )
    air_targets = targets.copy()
    air_targets[:, 2] = air_z
    air_qpos, _, _ = _solve_hardware_targets(
        desk, config, air_targets, args.tolerance_mm
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        args.out,
        qpos=qpos,
        air_qpos=air_qpos,
        dq_dz=dq_dz,
        expected_tip_xyz=targets,
        pen_down=np.asarray(down, dtype=bool),
        cell_index=np.asarray(cell_index, dtype=np.int8),
        line_index=np.asarray(line_index, dtype=np.int8),
        target_pressure=np.zeros(len(qpos), dtype=np.float64),
        kanji=np.asarray(""),
        lift_mm=np.asarray(lifts_mm, dtype=np.float64),
        dt=(args.step_mm / 1000.0) / (args.speed_mm_s / 1000.0),
        desk=str(args.desk),
        desk_fingerprint=desk_fingerprint(desk),
        motor_calibration_sha256=str(desk.get("motor_calibration_sha256") or ""),
        pressure_plan_schema=TRACE_SCHEMA,
        paper_surface_z_m=float(height["paper_surface_z_m"]),
        pressure_lifts_mm=np.asarray(lifts_mm, dtype=np.float64),
        write_height_above_paper_mm=float(height["write_height_above_paper_mm"]),
        write_tip_z_m=float(height["write_tip_z_m"]),
        air_clearance_mm=float(height["air_clearance_mm"]),
        air_height_above_paper_mm=float(height["air_height_above_paper_mm"]),
        air_tip_z_m=float(height["air_tip_z_m"]),
        safe_height_above_paper_mm=float(height["safe_height_above_paper_mm"]),
        safe_tip_z_m=float(height["safe_tip_z_m"]),
        brush_tuft_cm=float(height["brush_tuft_cm"]),
        brush_total_cm=float(height["brush_total_cm"]),
        brush_rigid_cm=float(height["brush_rigid_cm"]),
        brush_tip_length_scale=float(height["brush_tip_length_scale"]),
        lift_deg_per_mm=float(height["lift_deg_per_mm"]),
        height_metadata_json=json.dumps(height, sort_keys=True, ensure_ascii=False),
    )
    print(
        f"筆圧較正計画を保存 {args.out} 点数={len(qpos)} 試験線=10 "
        f"逆解の最大誤差={worst:.2f} mm"
    )


def _raise_qpos(q: np.ndarray, clear_rad: float) -> np.ndarray:
    out = np.asarray(q, dtype=np.float64).copy()
    out[1] += clear_rad
    return out


def _clamp_qpos(q: np.ndarray, desk: dict) -> np.ndarray:
    limits = desk_joint_ranges(desk)
    if limits is None:
        return np.asarray(q, dtype=np.float64)
    ranges = np.asarray(limits, dtype=np.float64)
    return np.clip(np.asarray(q, dtype=np.float64), ranges[:, 0], ranges[:, 1])


def _joints_qpos(desk: dict, joints: dict[str, float]) -> np.ndarray:
    sign, _ = playback_tilt(desk)
    return lerobot_to_qpos(
        joints,
        tilt_sign=sign,
        offsets=playback_offsets(desk),
        gripper_map=desk_gripper_map(desk),
    )


def _action_to_qpos(desk: dict, action: dict[str, float]) -> np.ndarray:
    joints = {key.removesuffix(".pos"): float(value) for key, value in action.items()}
    return _joints_qpos(desk, joints)


def _aligned_leader_qpos(
    desk: dict, action: dict[str, float], offset_qpos: np.ndarray
) -> np.ndarray:
    return _action_to_qpos(desk, action) + np.asarray(offset_qpos, dtype=np.float64)


def _leader_alignment_offset(
    follower_qpos: np.ndarray, leader_qpos: np.ndarray
) -> np.ndarray:
    follower = np.asarray(follower_qpos, dtype=np.float64)
    leader = np.asarray(leader_qpos, dtype=np.float64)
    if (
        follower.ndim != 2
        or follower.shape != leader.shape
        or follower.shape[1:] != (len(JOINT_NAMES),)
        or len(follower) < 5
        or not np.isfinite(follower).all()
        or not np.isfinite(leader).all()
    ):
        raise SystemExit("Leader/Follower初期姿勢のサンプルが不足または不正です。")
    if max(float(np.max(np.ptp(follower, axis=0))), float(np.max(np.ptp(leader, axis=0)))) > LEADER_STABILITY_RAD:
        raise SystemExit("Leader/Follower初期姿勢が動いています。止めてからEnterしてください。")
    return np.median(follower, axis=0) - np.median(leader, axis=0)


def _load_recorded_suzuri(path: Path, desk: dict) -> tuple[np.ndarray, float] | None:
    if not path.exists():
        return None
    data = np.load(path)
    qpos = np.asarray(data["qpos"], dtype=np.float64)
    dt = float(np.asarray(data["dt"]))
    if qpos.ndim != 2 or qpos.shape[1] != 6 or len(qpos) < 2:
        raise SystemExit(f"硯の録画が壊れています: {path}")
    if "desk_fingerprint" not in data:
        raise SystemExit("硯の録画にdesk fingerprintがありません。record-suzuriし直してください。")
    if str(np.asarray(data["desk_fingerprint"]).item()) != desk_fingerprint(desk):
        raise SystemExit("硯の録画が今の desk と合いません。record-suzuri し直してください。")
    return qpos, dt


def _disconnect_holding(robot) -> None:
    """Leave torque on so the last lifted pose does not fall onto the sheet."""
    print("筆を上げたまま切断します。トルクは入ったままです。")
    try:
        robot.disconnect()
    except Exception:
        pass


def _disconnect_limp(robot) -> None:
    """Disable torque after an aborted calibration; the operator must support the arm."""
    print("較正を中断したためトルクを切ります。腕を支えてください。")
    try:
        if robot.bus.is_connected:
            robot.bus.disable_torque(num_retry=3)
            robot.bus.disconnect(disable_torque=False)
    except Exception:
        pass


def _safe_send_qpos(
    robot,
    desk: dict,
    qpos: np.ndarray,
    safe_qpos: np.ndarray | None = None,
) -> None:
    qpos = np.asarray(qpos, dtype=np.float64).reshape(-1)
    limits = desk_joint_ranges(desk)
    def valid(target) -> bool:
        values = np.asarray(target, dtype=np.float64)
        if values.shape != (6,) or not np.isfinite(values).all():
            return False
        return limits is None or bool(np.all(values >= np.asarray(limits)[:, 0]) and np.all(values <= np.asarray(limits)[:, 1]))

    if not valid(qpos):
        if safe_qpos is not None and valid(safe_qpos):
            try:
                robot.send_action(_action(safe_qpos, desk))
            except Exception:
                pass
        raise SystemExit("指令が実機可動域外または非有限です。軌道を切り詰めず退避して停止しました")
    try:
        robot.send_action(_action(qpos, desk))
    except Exception:
        if safe_qpos is not None and valid(safe_qpos):
            try:
                robot.send_action(_action(safe_qpos, desk))
            except Exception:
                pass
        raise


def _send_qpos(
    robot,
    desk: dict,
    seq: np.ndarray,
    period: float,
    *,
    safe_qpos: np.ndarray | None = None,
) -> None:
    if safe_qpos is None:
        try:
            safe_qpos = _joints_qpos(desk, desk["poses"]["hover_center"])
        except (KeyError, SystemExit, ValueError):
            pass
    previous: np.ndarray | None = None
    for q in np.asarray(seq, dtype=np.float64):
        if previous is None:
            started = time.perf_counter()
            _safe_send_qpos(robot, desk, q, safe_qpos)
            remain = period - (time.perf_counter() - started)
            if remain > 0:
                time.sleep(remain)
        else:
            _send_smoothed_target(robot, desk, previous, q, period, safe_qpos)
        previous = q


def _interpolate_joint_target(
    start: np.ndarray,
    goal: np.ndarray,
    duration_s: float,
    hz: float = COMMAND_HZ,
) -> tuple[np.ndarray, float]:
    duration = max(float(duration_s), 0.0)
    count = max(1, int(np.ceil(duration * float(hz))))
    alpha = np.arange(1, count + 1, dtype=np.float64) / count
    sequence = np.asarray(start, dtype=np.float64) + alpha[:, None] * (
        np.asarray(goal, dtype=np.float64) - np.asarray(start, dtype=np.float64)
    )
    return sequence, duration / count if duration > 0.0 else 0.0


def _send_smoothed_target(
    robot,
    desk: dict,
    start: np.ndarray,
    goal: np.ndarray,
    duration_s: float,
    safe_qpos: np.ndarray | None,
) -> None:
    sequence, period = _interpolate_joint_target(start, goal, duration_s)
    for command in sequence:
        started = time.perf_counter()
        _safe_send_qpos(robot, desk, command, safe_qpos)
        remain = period - (time.perf_counter() - started)
        if remain > 0:
            time.sleep(remain)


def _feedback_magnitude(channel: str, value: float) -> float:
    value = float(value)
    if channel == "current" and value > 32767.0:
        value -= 65536.0
    return abs(value)


def _read_feedback(robot) -> dict[str, float]:
    loads = robot.bus.sync_read("Present_Load", normalize=False, num_retry=2)
    currents = robot.bus.sync_read("Present_Current", normalize=False, num_retry=2)
    return {
        **{f"load:{name}": _feedback_magnitude("load", loads[name]) for name in JOINT_NAMES},
        **{f"current:{name}": _feedback_magnitude("current", currents[name]) for name in JOINT_NAMES},
    }


def _validate_follower_port(port: str, desk: dict) -> None:
    expected_id = desk.get("follower_id")
    if expected_id and expected_id != ROBOT_ID:
        raise SystemExit(f"deskのFollower IDが不正です（{expected_id}）。sync-limitsをやり直してください。")
    expected_port = desk.get("follower_port")
    if expected_port and Path(port) != Path(expected_port):
        raise SystemExit(
            f"Followerポートが較正時と違います（{port}）。保存済み: {expected_port}。"
            " sync-limits を新しいポートでやり直してください。"
        )
    expected_serial = desk.get("follower_usb_serial")
    if not expected_serial:
        raise SystemExit(
            "Follower USB識別が未確定です。Follower接続後に "
            "hardware_calibrate.py sync-limits を再実行してください。"
        )
    try:
        from serial.tools import list_ports

        info = next((item for item in list_ports.comports() if item.device == port), None)
    except Exception as exc:
        raise SystemExit(f"USB識別を確認できません（{exc}）。Followerへ誤送信しないため停止します。") from exc
    if info is None or info.serial_number != expected_serial:
        actual = None if info is None else info.serial_number
        raise SystemExit(
            f"Follower USBシリアルが一致しません（期待 {expected_serial}, 実際 {actual}）。"
        )


def _port_serial(port: str, label: str) -> str:
    try:
        from serial.tools import list_ports

        info = next((item for item in list_ports.comports() if item.device == port), None)
    except Exception as exc:
        raise SystemExit(f"{label}のUSB識別を確認できません（{exc}）。") from exc
    if info is None or not info.serial_number:
        raise SystemExit(f"{label}のUSBシリアルを取得できません（{port}）。")
    return str(info.serial_number)


def _canonical_sha256(payload: dict) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _reference_pose(samples: list[dict[str, object]]) -> dict[str, object]:
    if len(samples) < 5:
        raise SystemExit("基準姿勢の安定サンプルが不足しています。姿勢を止めてからEnterしてください。")
    qpos = np.stack([np.asarray(row["qpos"], dtype=np.float64) for row in samples])
    spread = np.max(np.ptp(qpos, axis=0))
    if spread > np.deg2rad(2.0):
        raise SystemExit("基準姿勢が動いています。姿勢を止めて教示し直してください。")
    keys = sorted(
        key for key in samples[0] if key.startswith("load:") or key.startswith("current:")
    )
    medians = {
        key: float(np.median([float(row[key]) for row in samples])) for key in keys
    }
    mads = {
        key: _mad(np.asarray([float(row[key]) for row in samples], dtype=np.float64))
        for key in keys
    }
    return {
        "qpos": [float(value) for value in np.median(qpos, axis=0)],
        "feedback_median": medians,
        "feedback_mad": mads,
    }


def _select_taught_signal(poses: dict[str, dict[str, object]]) -> dict[str, object]:
    best: tuple[float, str, int, float, float, float] | None = None
    hover = poses["hover"]
    contact = poses["contact"]
    good = poses["good"]
    for key, air_value in hover["feedback_median"].items():
        pooled_mad = max(
            float(hover["feedback_mad"][key]),
            float(contact["feedback_mad"][key]),
            float(good["feedback_mad"][key]),
            1.0,
        )
        contact_delta = float(contact["feedback_median"][key]) - float(air_value)
        good_delta = float(good["feedback_median"][key]) - float(air_value)
        for sign in (1, -1):
            contact_excess = float(sign) * contact_delta
            good_excess = float(sign) * good_delta
            if good_excess < max(6.0 * pooled_mad, contact_excess + 3.0 * pooled_mad):
                continue
            score = good_excess / pooled_mad
            candidate = (
                score,
                key,
                sign,
                contact_excess,
                good_excess,
                pooled_mad,
            )
            if best is None or candidate[0] > best[0]:
                best = candidate
    if best is None:
        raise SystemExit(
            "空中→接触→良い圧を区別できる荷重・電流信号がありません。"
            "筆を止め、良い圧を少し明確にして教示し直してください。"
        )
    _, key, sign, contact_excess, good_excess, pooled_mad = best
    contact_qpos = np.asarray(contact["qpos"], dtype=np.float64)
    good_qpos = np.asarray(good["qpos"], dtype=np.float64)
    hover_qpos = np.asarray(hover["qpos"], dtype=np.float64)
    pressure_direction = good_qpos - contact_qpos
    if np.max(np.abs(pressure_direction)) > np.deg2rad(8.0):
        raise SystemExit("接触→良い圧の姿勢差が8°を超えています。筆圧だけを変えて教示してください。")
    return {
        "channel": key,
        "sign": int(sign),
        "air_median": float(hover["feedback_median"][key]),
        "pooled_mad": float(pooled_mad),
        "contact_excess": float(contact_excess),
        "good_excess": float(good_excess),
        "pen_down_excess": float(
            max(3.0 * pooled_mad, 0.2 * good_excess, 0.5 * max(contact_excess, 0.0))
        ),
        "safety_excess": float(max(good_excess, contact_excess) + 5.0 * pooled_mad),
        "pressure_direction_qpos": [float(value) for value in pressure_direction],
        "air_delta_qpos": [float(value) for value in (hover_qpos - good_qpos)],
    }


def _reference_excess(reference_cell: dict, feedback: dict[str, float]) -> float:
    key = str(reference_cell["channel"])
    return float(reference_cell["sign"]) * (
        float(feedback[key]) - float(reference_cell["air_median"])
    )


def _validate_taught_word(word: str) -> str:
    if word not in TAUGHT_WORDS:
        raise SystemExit("Leader教示は 文字・学習・菅原 の3語だけ対応します。")
    return word


def _validate_leader_reference(reference: dict, desk: dict) -> dict:
    if int(reference.get("schema", 0)) != TAUGHT_SCHEMA:
        raise SystemExit("Leader基準のschemaが不正です。teach-referenceをやり直してください。")
    if reference.get("desk_fingerprint") != desk_fingerprint(desk):
        raise SystemExit("Leader基準が現在のdeskと一致しません。teach-referenceをやり直してください。")
    if reference.get("motor_calibration_sha256") != desk.get("motor_calibration_sha256"):
        raise SystemExit("Leader基準が現在のFollower較正と一致しません。")
    if set(reference.get("cells", {})) != {"0", "1"}:
        raise SystemExit("Leader基準に上下段がありません。")
    offset = np.asarray(reference.get("leader_to_follower_offset_qpos"), dtype=np.float64)
    if offset.shape != (len(JOINT_NAMES),) or not np.isfinite(offset).all():
        raise SystemExit("Leader基準に初期姿勢オフセットがありません。teach-referenceをやり直してください。")
    for cell in ("0", "1"):
        item = reference["cells"][cell]
        try:
            write_z = float(item["write_tip_z_m"])
            contact_z = float(item["contact_tip_z_m"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit("Leader基準に上下別の穂先高さがありません。teach-referenceをやり直してください。") from exc
        if not np.isfinite((write_z, contact_z)).all():
            raise SystemExit("Leader基準の穂先高さが不正です。teach-referenceをやり直してください。")
    recorded_sha = str(reference.get("reference_sha256") or "")
    unsigned = dict(reference)
    unsigned.pop("reference_sha256", None)
    if not recorded_sha or recorded_sha != _canonical_sha256(unsigned):
        raise SystemExit("Leader基準のhashが一致しません。teach-referenceをやり直してください。")
    return reference


def _load_leader_reference(path: Path, desk: dict) -> dict:
    try:
        reference = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Leader基準を読めません（{path}: {exc}）。") from exc
    return _validate_leader_reference(reference, desk)


def _reference_from_trace(data, desk: dict) -> dict:
    try:
        reference = json.loads(str(np.asarray(data["reference_json"]).item()))
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit("軌道内のLeader基準が壊れています。traceを作り直してください。") from exc
    return _validate_leader_reference(reference, desk)


def _add_reference_tip_heights(desk: dict, cells: dict[str, dict]) -> None:
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv

    env = CalligraphyEnv(task="line", config=env_config_from_desk(desk))
    try:
        env.reset(seed=0, options={"layout_index": 0})
        for cell in ("0", "1"):
            poses = cells[cell]["poses"]
            for pose in poses.values():
                tip, _ = _tip_and_axis(env, np.asarray(pose["qpos"], dtype=np.float64))
                pose["tip_xyz_m"] = [float(value) for value in tip]
            cells[cell]["contact_tip_z_m"] = float(poses["contact"]["tip_xyz_m"][2])
            cells[cell]["write_tip_z_m"] = float(poses["good"]["tip_xyz_m"][2])
            if float(poses["hover"]["tip_xyz_m"][2]) - cells[cell]["write_tip_z_m"] < 0.015:
                raise SystemExit("Leader空中姿勢が良い筆圧位置から15 mm以上上がっていません。")
    finally:
        env.close()


def _validate_taught_data(data, desk: dict) -> dict:
    required = (
        "taught_schema",
        "qpos",
        "air_qpos",
        "pen_down",
        "cell_index",
        "target_excess",
        "dt",
        "kanji",
        "desk_fingerprint",
        "motor_calibration_sha256",
        "reference_json",
        "reference_sha256",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise SystemExit("Leader教示NPZの項目が不足しています: " + ", ".join(missing))
    if int(np.asarray(data["taught_schema"]).item()) != TAUGHT_SCHEMA:
        raise SystemExit("Leader教示NPZのschemaが不正です。")
    word = _validate_taught_word(str(np.asarray(data["kanji"]).item()))
    if str(np.asarray(data["desk_fingerprint"]).item()) != desk_fingerprint(desk):
        raise SystemExit("Leader教示NPZが現在のdeskと一致しません。")
    if str(np.asarray(data["motor_calibration_sha256"]).item()) != str(
        desk.get("motor_calibration_sha256") or ""
    ):
        raise SystemExit("Leader教示NPZが現在のFollower較正と一致しません。")
    try:
        reference = json.loads(str(np.asarray(data["reference_json"]).item()))
    except json.JSONDecodeError as exc:
        raise SystemExit("Leader教示NPZ内の基準JSONが壊れています。") from exc
    reference = _validate_leader_reference(reference, desk)
    recorded_sha = str(np.asarray(data["reference_sha256"]).item())
    if reference.get("reference_sha256") != recorded_sha:
        raise SystemExit("Leader教示NPZと基準JSONのhashが一致しません。")
    qpos = np.asarray(data["qpos"], dtype=np.float64)
    air_qpos = np.asarray(data["air_qpos"], dtype=np.float64)
    _validate_taught_motion(qpos, air_qpos, desk)
    for key in ("pen_down", "cell_index", "target_excess"):
        if len(np.asarray(data[key])) != len(qpos):
            raise SystemExit(f"Leader教示NPZの{key}の長さが不正です。")
    cells = np.asarray(data["cell_index"], dtype=np.int8)
    if not set(np.unique(cells)).issubset({0, 1}) or set(np.unique(cells)) != {0, 1}:
        raise SystemExit("Leader教示NPZに上下段の両方がありません。")
    dt = float(np.asarray(data["dt"]).item())
    if not np.isfinite(dt) or dt <= 0.0:
        raise SystemExit("Leader教示NPZのdtが不正です。")
    reference["word"] = word
    return reference


_HEIGHT_KEYS = (
    "paper_surface_z_m",
    "write_height_above_paper_mm",
    "write_tip_z_m",
    "air_clearance_mm",
    "air_height_above_paper_mm",
    "air_tip_z_m",
    "safe_height_above_paper_mm",
    "safe_tip_z_m",
    "brush_tuft_cm",
    "brush_total_cm",
    "brush_rigid_cm",
    "brush_tip_length_scale",
    "lift_deg_per_mm",
)


def _validate_height_artifact(data, desk: dict, *, write_lift_mm: float) -> dict:
    missing = [*(_HEIGHT_KEYS), "height_metadata_json"]
    missing = [name for name in missing if name not in data]
    if missing:
        raise SystemExit("軌道の高さメタデータが不足しています: " + ", ".join(missing))
    try:
        recorded = json.loads(str(np.asarray(data["height_metadata_json"]).item()))
        expected = hardware_height_metadata(
            desk,
            write_lift_mm=float(write_lift_mm),
            clear_mm=float(np.asarray(data["air_clearance_mm"]).item()),
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit("軌道の高さメタデータが壊れています。作り直してください。") from exc
    if recorded.get("height_reference") != "paper_table_fk_plane":
        raise SystemExit("軌道の高さ基準が実機 desk と一致しません。作り直してください。")
    for key in _HEIGHT_KEYS:
        try:
            actual = float(np.asarray(data[key]).item())
            saved = float(recorded[key])
            target = float(expected[key])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit("軌道の高さメタデータが壊れています。作り直してください。") from exc
        if not np.isfinite(actual) or not np.isclose(actual, saved, atol=1e-9, rtol=0.0) or not np.isclose(actual, target, atol=1e-9, rtol=0.0):
            raise SystemExit("軌道の高さが現在の実機 desk と一致しません。作り直してください。")
    return recorded


def _validate_trace_data(data, desk: dict, allow_legacy: bool) -> bool:
    if "trace_schema" not in data:
        if allow_legacy:
            return False
        raise SystemExit(
            "旧形式の軌道です。安全な2文字再生には新しくtraceしてください。"
            "互換再生は --allow-legacy-open-loop を明示してください。"
        )
    schema = int(np.asarray(data["trace_schema"]).item())
    if schema != TRACE_SCHEMA:
        raise SystemExit(f"未対応のtrace schema: {schema}。現在のplannerでtraceを作り直してください。")
    required = (
        "qpos",
        "air_qpos",
        "dq_dz",
        "pen_down",
        "cell_index",
        "target_pressure",
        "expected_tip_xyz",
        "standby_qpos",
        "standby_tip_xyz",
        "standby_height_above_paper_mm",
        "cell_write_tip_z_m",
        "command_hz",
        "dt",
        "kanji",
        "desk_fingerprint",
        "motor_calibration_sha256",
        "nominal_lift_mm",
        "paper_surface_z_m",
        "write_height_above_paper_mm",
        "write_tip_z_m",
        "air_clearance_mm",
        "air_height_above_paper_mm",
        "air_tip_z_m",
        "safe_height_above_paper_mm",
        "safe_tip_z_m",
        "brush_tuft_cm",
        "brush_total_cm",
        "brush_rigid_cm",
        "brush_tip_length_scale",
        "lift_deg_per_mm",
        "height_metadata_json",
        "reference_json",
        "reference_sha256",
    )
    missing = [name for name in required if name not in data]
    if missing:
        raise SystemExit("軌道メタデータが不足しています: " + ", ".join(missing))
    actual = str(np.asarray(data["desk_fingerprint"]).item())
    if actual != desk_fingerprint(desk):
        raise SystemExit("軌道とdesk較正が一致しません。traceを作り直してください。")
    expected_motor = str(desk.get("motor_calibration_sha256") or "")
    actual_motor = str(np.asarray(data["motor_calibration_sha256"]).item())
    if actual_motor != expected_motor:
        raise SystemExit("軌道とFollowerサーボ較正が一致しません。sync-limits後にtraceを作り直してください。")
    _validate_height_artifact(
        data, desk, write_lift_mm=float(np.asarray(data["nominal_lift_mm"]).item())
    )
    qpos = np.asarray(data["qpos"], dtype=np.float64)
    if qpos.ndim != 2 or qpos.shape[1] != len(JOINT_NAMES):
        raise SystemExit("qposの形状が不正です")
    if not np.isfinite(qpos).all():
        raise SystemExit("qposに有限でない値があります")
    expected = np.asarray(data["expected_tip_xyz"], dtype=np.float64)
    if expected.shape != (len(qpos), 3) or not np.isfinite(expected).all():
        raise SystemExit("expected_tip_xyzの形状または値が不正です")
    for name in ("air_qpos", "dq_dz", "pen_down", "cell_index", "target_pressure"):
        if len(np.asarray(data[name])) != len(qpos):
            raise SystemExit(f"{name}の長さがqposと一致しません")
    if np.asarray(data["air_qpos"]).shape != qpos.shape:
        raise SystemExit("air_qposの形状がqposと一致しません")
    if np.asarray(data["dq_dz"]).shape != qpos.shape:
        raise SystemExit("dq_dzの形状がqposと一致しません")
    for name in ("air_qpos", "dq_dz"):
        if not np.isfinite(np.asarray(data[name], dtype=np.float64)).all():
            raise SystemExit(f"{name}に有限でない値があります")
    for name in ("qpos", "air_qpos"):
        if len(qpos) > 1 and np.max(np.abs(np.diff(np.asarray(data[name]), axis=0))) > IK_MAX_STEP_RAD + 1e-8:
            raise SystemExit(f"{name}の隣接姿勢が5°を超えています。traceを作り直してください。")
    if not np.isfinite(np.asarray(data["target_pressure"], dtype=np.float64)).all():
        raise SystemExit("target_pressureに有限でない値があります")
    kanji = str(np.asarray(data["kanji"]).item())
    if len(kanji) not in (1, 2, 3, 4):
        raise SystemExit("軌道の文字数は1〜4文字にしてください")
    cell_heights = np.asarray(data["cell_write_tip_z_m"], dtype=np.float64)
    if cell_heights.shape != (len(kanji),) or not np.isfinite(cell_heights).all():
        raise SystemExit("セル別の書字高さが不正です。traceを作り直してください。")
    raw_cells = np.asarray(data["cell_index"])
    if raw_cells.shape != (len(qpos),) or not np.isin(raw_cells, [-1, *range(len(kanji))]).all():
        raise SystemExit("軌道のセル番号が文字数と一致しません")
    cells = raw_cells.astype(np.int8)
    down = np.asarray(data["pen_down"], dtype=bool)
    if not np.isin(cells, [-1, *range(len(kanji))]).all() or np.any(down & (cells < 0)):
        raise SystemExit("軌道のセル番号が文字数と一致しません")
    has_reference = bool(str(np.asarray(data["reference_json"]).item() or "").strip())
    measured_heights = str(np.asarray(data.get("height_profile_kind", "legacy")).item()) == "measured_pressure"
    if measured_heights:
        profile = desk.get("pressure_calibration_v1") or {}
        if profile.get("desk_fingerprint") != desk_fingerprint(desk):
            raise SystemExit("現在の筆圧較正が必要です")
        rows = glyph_cells(env_config_from_desk(desk).paper, 2)
        zfar = desk["paper"]["surface_z"] + float(profile["cells"]["0"]["fallback_lift_mm"]) / 1000
        znear = desk["paper"]["surface_z"] + float(profile["cells"]["1"]["fallback_lift_mm"]) / 1000
        measured_z = write_z_along_depth(expected[:, 0], rows[0].center_x, rows[1].center_x, zfar, znear)
        if not np.allclose(expected[down, 2], measured_z[down], atol=1e-8, rtol=0):
            raise SystemExit("書字高さが実測した筆圧と一致しません")
        centre_z = write_z_along_depth(np.asarray([c.center_x for c in glyph_cells(env_config_from_desk(desk).paper, len(kanji))]), rows[0].center_x, rows[1].center_x, zfar, znear)
        if not np.allclose(cell_heights, centre_z, atol=1e-8, rtol=0):
            raise SystemExit("文字中央の高さが筆圧較正と一致しません")
    if has_reference and len(kanji) != 2:
        raise SystemExit("2文字のLeader基準は別の配置には使用できません")
    ceiling = DEFAULT_U_KANMURI_LIFT_MM / 1000.0 if not has_reference else 0.0
    extra = 0.0 if has_reference else DEFAULT_LOWER_CELL_EXTRA_PRESS_MM / 1000.0
    far_z = float(cell_heights[0])
    frames = glyph_cells(env_config_from_desk(desk).paper, len(kanji))
    for cell, write_z in enumerate(cell_heights):
        mask = down & (cells == cell)
        if not np.any(mask):
            raise SystemExit("軌道点とセル別の書字高さが一致しません。traceを作り直してください。")
        z_vals = expected[mask, 2]
        frame = frames[cell]
        if np.any(np.abs(expected[mask, :2] - [frame.center_x, frame.center_y]) > frame.width / 2 + 1e-6):
            raise SystemExit("書字軌道が割り当てられた枡の外に出ています")
        lo = write_z if has_reference else far_z - extra
        hi = (write_z if has_reference else far_z) + ceiling
        if not measured_heights and (float(np.min(z_vals)) < lo - 1e-6 or float(np.max(z_vals)) > hi + 1e-6):
            raise SystemExit("軌道点とセル別の書字高さが一致しません。traceを作り直してください。")
    air_expected = float(np.asarray(data["air_height_above_paper_mm"]).item()) if measured_heights else DEFAULT_AIR_HEIGHT_MM
    standby_expected = float(np.asarray(data["standby_height_above_paper_mm"]).item()) if measured_heights else DEFAULT_STANDBY_HEIGHT_MM
    if not np.isfinite([air_expected, standby_expected]).all() or not 15 <= air_expected <= standby_expected <= 150:
        raise SystemExit("画間・待機高さが不正です")
    if np.any(air_expected / 1000 + desk["paper"]["surface_z"] - cell_heights < .015):
        raise SystemExit("筆圧位置から15 mm以上の画間余裕が必要です")
    if not np.isclose(
        float(np.asarray(data["air_height_above_paper_mm"]).item()),
        air_expected,
        atol=1e-9,
        rtol=0.0,
    ):
        raise SystemExit(
            f"画間高さが{DEFAULT_AIR_HEIGHT_MM:.0f} mmではありません。traceを作り直してください。"
        )
    standby_qpos = np.asarray(data["standby_qpos"], dtype=np.float64)
    standby_tip = np.asarray(data["standby_tip_xyz"], dtype=np.float64)
    if standby_qpos.shape != (len(JOINT_NAMES),) or standby_tip.shape != (3,):
        raise SystemExit("待機姿勢の形状が不正です。traceを作り直してください。")
    if not np.isclose(
        float(np.asarray(data["standby_height_above_paper_mm"]).item()),
        standby_expected,
        atol=1e-9,
        rtol=0.0,
    ) or not np.isclose(
        standby_tip[2] - float(desk["paper"]["surface_z"]),
        standby_expected / 1000.0,
        atol=1e-9,
        rtol=0.0,
    ):
        raise SystemExit(
            f"待機高さが{DEFAULT_STANDBY_HEIGHT_MM:.0f} mmではありません。traceを作り直してください。"
        )
    if not np.isclose(
        float(np.asarray(data["command_hz"]).item()), COMMAND_HZ, atol=1e-9, rtol=0.0
    ):
        raise SystemExit("実機送信周波数が30 Hzではありません。traceを作り直してください。")
    limits = np.asarray(require_joint_ranges(desk), dtype=np.float64)
    if np.any(qpos < limits[:, 0] + IK_LIMIT_MARGIN_RAD) or np.any(
        qpos > limits[:, 1] - IK_LIMIT_MARGIN_RAD
    ) or np.any(standby_qpos < limits[:, 0] + IK_LIMIT_MARGIN_RAD) or np.any(
        standby_qpos > limits[:, 1] - IK_LIMIT_MARGIN_RAD
    ):
        raise SystemExit("軌道が関節端2°以内に入ります。traceを作り直してください。")
    air_qpos = np.asarray(data["air_qpos"], dtype=np.float64)
    if np.any(air_qpos < limits[:, 0] + IK_LIMIT_MARGIN_RAD) or np.any(air_qpos > limits[:, 1] - IK_LIMIT_MARGIN_RAD):
        raise SystemExit("空中軌道が関節端2°以内に入ります。traceを作り直してください。")
    if len(kanji) == 2 and str(np.asarray(data["reference_json"]).item() or "").strip():
        reference = _reference_from_trace(data, desk)
        if str(np.asarray(data["reference_sha256"]).item()) != str(
            reference["reference_sha256"]
        ):
            raise SystemExit("軌道とLeader基準のhashが一致しません。traceを作り直してください。")
        saved_heights = np.asarray(
            [reference["cells"][str(cell)]["write_tip_z_m"] for cell in range(2)],
            dtype=np.float64,
        )
        if not np.allclose(cell_heights, saved_heights, atol=1e-9, rtol=0.0):
            raise SystemExit("軌道とLeader基準の書字高さが一致しません。traceを作り直してください。")
    else:
        calibration = desk.get("pressure_calibration_v1")
        if not isinstance(calibration, dict):
            raise SystemExit("筆圧較正が未完了です。先に pressure-calibrate を実行してください。")
        if calibration.get("desk_fingerprint") != desk_fingerprint(desk):
            raise SystemExit("筆圧較正が古いdesk用です。pressure-calibrateをやり直してください。")
        saved = str(np.asarray(data.get("pressure_calibration_sha256", "")).item())
        if saved != _canonical_sha256(calibration):
            raise SystemExit("軌道と筆圧較正が一致しません。現在の筆圧でtraceを作り直してください。")
        _grid_pressure_calibration(desk, len(kanji))
    return True


def _mad(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=np.float64)
    median = float(np.median(values))
    return float(np.median(np.abs(values - median)))


def _pressure_profile_from_samples(
    data,
    air_rows: list[dict[str, object]],
    line_rows: list[dict[str, object]],
    selected_lines: tuple[int, int],
) -> dict:
    lifts = np.asarray(data["lift_mm"], dtype=np.float64)
    if len(lifts) != len(PRESSURE_LIFTS_MM):
        raise SystemExit("筆圧較正の段数が5ではありません")
    if len(selected_lines) != 2 or any(
        int(value) < 0 or int(value) >= len(lifts) for value in selected_lines
    ):
        raise SystemExit("筆圧較正の選択線番号が不正です")
    channels = tuple(
        f"{kind}:{name}" for kind in ("load", "current") for name in JOINT_NAMES
    )
    pen_down = (
        np.asarray(data["pen_down"], dtype=bool) if "pen_down" in data else None
    )
    cells: dict[str, dict] = {}
    safety: dict[str, float] = {}
    for cell in range(2):
        cell_air = [row for row in air_rows if row["cell"] == cell]
        if not cell_air:
            raise SystemExit(f"筆圧較正の空中基準が不足しています: cell={cell}")
        air_medians = {
            key: float(np.median([row[key] for row in cell_air])) for key in channels
        }
        line_medians: dict[str, np.ndarray] = {}
        line_mads: dict[str, np.ndarray] = {}
        cell_safety: dict[str, float] = {}
        for key in channels:
            medians = []
            deviations = []
            for line in range(len(lifts)):
                values = np.asarray(
                    [
                        row[key]
                        for row in line_rows
                        if row["cell"] == cell
                        and row["line"] == line
                        and (
                            pen_down is None
                            or "index" not in row
                            or bool(pen_down[int(row["index"])])
                        )
                    ],
                    dtype=np.float64,
                )
                if len(values) == 0:
                    raise SystemExit(
                        f"筆圧較正の試験線が不足しています: cell={cell} line={line + 1}"
                    )
                medians.append(float(np.median(values)))
                deviations.append(_mad(values))
            line_medians[key] = np.asarray(medians)
            line_mads[key] = np.asarray(deviations)
            threshold = float(max(medians) + 5.0 * max(max(deviations), 1.0))
            cell_safety[key] = threshold
            safety[key] = max(safety.get(key, 0.0), threshold)

        best: tuple[float, str, int, np.ndarray, float] | None = None
        for key in channels:
            pooled = max(float(np.median(line_mads[key])), 1.0)
            raw = line_medians[key] - air_medians[key]
            for sign in (1, -1):
                oriented = float(sign) * raw
                gaps = np.diff(oriented)
                if len(gaps) and np.all(gaps >= 0.0) and float(np.min(gaps)) >= 3.0 * pooled:
                    score = float(np.min(gaps) / pooled)
                    candidate = (score, key, sign, oriented, pooled)
                    if best is None or score > best[0]:
                        best = candidate
        chosen = int(selected_lines[cell])
        if best is None:
            cells[str(cell)] = {
                "mode": "open_loop",
                "channel": None,
                "selected_line": chosen,
                "fallback_lift_mm": float(lifts[chosen]),
                "air_median": None,
                "line_medians": {},
                "line_mads": {},
                "safety": cell_safety,
            }
            continue
        _, key, sign, oriented, pooled = best
        depth_m = -lifts / 1000.0
        slope = float(np.polyfit(depth_m, oriented, 1)[0])
        cells[str(cell)] = {
            "mode": "closed_loop" if slope > 0.0 else "open_loop",
            "channel": key,
            "sign": int(sign),
            "selected_line": chosen,
            "fallback_lift_mm": float(lifts[chosen]),
            "air_median": float(air_medians[key]),
            "line_medians": [float(value) for value in line_medians[key]],
            "line_mads": [float(value) for value in line_mads[key]],
            "selected_excess": float(oriented[chosen]),
            "slope_per_m": slope,
            "pooled_mad": pooled,
            "safety": cell_safety,
        }
    return {
        "schema": 1,
        "desk_fingerprint": "",
        "motor_calibration_sha256": "",
        "lifts_mm": [float(value) for value in lifts],
        "cells": cells,
        "safety": safety,
    }


def _feedback_rows(
    robot,
    desk: dict,
    sequence: np.ndarray,
    indices: np.ndarray,
    period: float,
    data,
    phase: str,
    safe_sequence: np.ndarray | None = None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    line_values = (
        np.asarray(data["line_index"])
        if "line_index" in data
        else np.full(len(np.asarray(data["cell_index"])), -1, dtype=np.int8)
    )
    sequence = np.asarray(sequence, dtype=np.float64)
    previous = sequence[0] if len(sequence) else None
    for index, qpos in zip(indices, sequence):
        started = time.perf_counter()
        source_index = int(index)
        try:
            _send_smoothed_target(
                robot,
                desk,
                previous,
                qpos,
                max(period - (time.perf_counter() - started), 0.0),
                None if safe_sequence is None else safe_sequence[source_index],
            )
            values = _read_feedback(robot)
        except Exception:
            raise
        row: dict[str, object] = {
            "time_s": float(time.time()),
            "index": source_index,
            "phase": phase,
            "cell": int(np.asarray(data["cell_index"])[source_index]),
            "line": int(line_values[source_index]),
        }
        row.update(values)
        rows.append(row)
        remain = period - (time.perf_counter() - started)
        if remain > 0:
            time.sleep(remain)
        previous = qpos
    return rows


def _write_feedback_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = ["time_s", "index", "phase", "cell", "line"]
    keys.extend(sorted({key for row in rows for key in row if key not in keys}))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _prompt_line(label: str) -> int:
    while True:
        value = input(f"{label}の良い線番号 (1-5): ").strip()
        try:
            number = int(value)
        except ValueError:
            number = 0
        if 1 <= number <= len(PRESSURE_LIFTS_MM):
            return number - 1
        print("1から5で入力してください。")


def _pressure_calibrate(args: argparse.Namespace) -> None:
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    _validate_follower_port(args.port, desk)
    data = np.load(args.plan, allow_pickle=True)
    if "pressure_plan_schema" not in data or int(np.asarray(data["pressure_plan_schema"]).item()) != TRACE_SCHEMA:
        raise SystemExit("筆圧較正計画のschemaが不正です。pressure-planを作り直してください。")
    if str(np.asarray(data["desk_fingerprint"]).item()) != desk_fingerprint(desk):
        raise SystemExit("筆圧較正計画とdesk較正が一致しません。pressure-planを作り直してください。")
    if str(np.asarray(data["motor_calibration_sha256"]).item()) != str(desk.get("motor_calibration_sha256") or ""):
        raise SystemExit("筆圧較正計画とFollower較正が一致しません。sync-limits後に作り直してください。")
    lift_key = "pressure_lifts_mm" if "pressure_lifts_mm" in data else "lift_mm"
    lifts = np.asarray(data[lift_key], dtype=np.float64)
    if lifts.ndim != 1 or len(lifts) != len(PRESSURE_LIFTS_MM):
        raise SystemExit("筆圧較正計画の高さ段数が不正です。pressure-planを作り直してください。")
    height_metadata = _validate_height_artifact(
        data, desk, write_lift_mm=float(np.max(lifts))
    )

    qpos = np.asarray(data["qpos"], dtype=np.float64)
    air_qpos = np.asarray(data["air_qpos"], dtype=np.float64)
    stride = max(1, int(args.stride))
    period = float(np.asarray(data["dt"])) / max(args.speed, 1e-6) * stride
    transfer = None
    if getattr(args, "approach_plan", None):
        import hashlib
        transfer = np.load(args.approach_plan, allow_pickle=False)
        if str(transfer["desk_sha256"].item()) != hashlib.sha256(args.desk.read_bytes()).hexdigest():
            raise SystemExit("筆圧試験への移動経路と較正が一致しません")
        if str(transfer["pressure_plan_sha256"].item()) != hashlib.sha256(args.plan.read_bytes()).hexdigest():
            raise SystemExit("確認後に筆圧の試験軌道が変更されています")
        targets = np.asarray(transfer["qpos"], dtype=float)
        limits = np.asarray(require_joint_ranges(desk))
        if targets.ndim != 2 or targets.shape[1] != 6 or not len(targets) or not np.isfinite(targets).all() or np.any(targets < limits[:,0] + IK_LIMIT_MARGIN_RAD) or np.any(targets > limits[:,1] - IK_LIMIT_MARGIN_RAD) or (len(targets)>1 and np.max(np.abs(np.diff(targets,axis=0))) > np.deg2rad(1)+1e-7):
            raise SystemExit("筆圧試験への移動経路が不正です")
        if np.max(np.abs(targets[-1] - air_qpos[0])) > 1e-7:
            raise SystemExit("移動経路が筆圧試験の開始姿勢につながりません")
        returned = np.asarray(transfer["rehearsal_return_qpos"], dtype=float)
        if returned.ndim != 2 or returned.shape[1] != 6 or not len(returned) or not np.isfinite(returned).all() or np.any(returned < limits[:,0] + IK_LIMIT_MARGIN_RAD) or np.any(returned > limits[:,1] - IK_LIMIT_MARGIN_RAD) or (len(returned)>1 and np.max(np.abs(np.diff(returned,axis=0))) > np.deg2rad(1)+1e-7) or np.max(np.abs(returned[-1] - qpos[0])) > 1e-7:
            raise SystemExit("空中リハーサルから試験線へ戻る経路が不正です")
    robot = SO101Follower(
        SO101FollowerConfig(
            port=args.port,
            id=ROBOT_ID,
            max_relative_target=None,
            position_p_coefficient=P_GAIN,
            disable_torque_on_disconnect=False,
        )
    )
    motion_complete = False
    try:
        present = _connect_hold_present(robot)
        for name in robot.bus.motors:
            robot.bus.write("P_Coefficient", name, P_GAIN)
            robot.bus.write("Acceleration", name, ACCEL)
            robot.bus.write("Goal_Velocity", name, CRUISE_VELOCITY)
        start = lerobot_to_qpos(
            present,
            tilt_sign=desk["tilt_sign"],
            offsets=playback_offsets(desk),
            gripper_map=desk_gripper_map(desk),
        )
        first_air = air_qpos[0]
        hz = 1.0 / max(period, 1e-6)
        print("墨なしで空中リハーサルを行います。腕を支えてください。")
        if transfer is not None:
            if np.max(np.abs(start - transfer["start_qpos"])) > np.deg2rad(.5):
                raise SystemExit("筆圧試験の移動確認後にアームが動きました。現在位置から確認し直してください")
            _send_qpos(robot, desk, transfer["qpos"], 1 / 30)
        else:
            _send_qpos(robot, desk, _blend(start, first_air, max(args.approach_s, 6.0), hz), period)
        air_indices = np.arange(0, len(air_qpos), stride, dtype=int)
        air_rows = _feedback_rows(
            robot, desk, air_qpos[::stride], air_indices, period, data, "air", air_qpos
        )
        if transfer is not None:
            _send_qpos(robot, desk, transfer["rehearsal_return_qpos"], 1 / 30)
        print("空中基準を取得しました。別紙へ墨を付けてください。")
        input("準備できたらEnter: ")
        line_indices = np.arange(0, len(qpos), stride, dtype=int)
        line_rows = _feedback_rows(
            robot, desk, qpos[::stride], line_indices, period, data, "line", air_qpos
        )
        motion_complete = True
    except BaseException:
        raise
    finally:
        if motion_complete:
            _disconnect_holding(robot)
        else:
            _disconnect_limp(robot)

    selected = (_prompt_line("奥側（上段）"), _prompt_line("手前側（下段）"))
    profile = _pressure_profile_from_samples(data, air_rows, line_rows, selected)
    profile["desk_fingerprint"] = desk_fingerprint(desk)
    profile["motor_calibration_sha256"] = str(desk.get("motor_calibration_sha256") or "")
    profile["selected_lines_1based"] = [value + 1 for value in selected]
    profile["height"] = height_metadata
    desk["pressure_calibration_v1"] = profile
    save_desk(args.desk, desk)
    log_path = args.log or _new_run_dir() / "pressure.csv"
    plan_copy = log_path.parent / "pressure-plan.npz"
    if Path(args.plan).resolve() != plan_copy.resolve():
        shutil.copy2(args.plan, plan_copy)
    _write_feedback_csv(log_path, [*air_rows, *line_rows])
    _write_json(log_path.with_name("pressure.json"), profile)
    print(f"筆圧較正を保存: {args.desk}\nログ: {log_path}")


def _action(qpos_rad: np.ndarray, desk: dict) -> dict[str, float]:
    sign, limits = playback_tilt(desk)
    return {
        f"{name}.pos": value
        for name, value in qpos_to_lerobot(
            qpos_rad,
            tilt_sign=sign,
            tilt_range=limits,
            offsets=playback_offsets(desk),
            gripper_map=desk_gripper_map(desk),
        ).items()
    }


def _add_joint(q: np.ndarray, index: int, delta: float) -> np.ndarray:
    out = np.asarray(q, dtype=np.float64).copy()
    out[index] += delta
    return out


def _suzuri_contact_qpos(desk: dict) -> tuple[np.ndarray, np.ndarray]:
    contact = np.deg2rad(SUZURI_LIFT_MM * desk_lift_gain(desk))
    pool = _raise_qpos(_joints_qpos(desk, desk["poses"]["suzuri_pool"]), contact)
    near = _raise_qpos(_joints_qpos(desk, desk_suzuri_pull(desk)), contact)
    return pool, near


def _retarget_wrist_roll(env, qpos: np.ndarray, roll: float, limits: np.ndarray) -> np.ndarray:
    """ID5を回しても穂先XYZを変えない。固定すると左へ約13 cm飛ぶ。"""
    tip, _ = _tip_and_axis(env, qpos)
    seed = np.asarray(qpos, dtype=np.float64).copy()
    seed[JOINT_NAMES.index("wrist_roll")] += roll
    return solve_tip_ik(
        env,
        tip,
        seed,
        limits,
        limit_margin_rad=IK_LIMIT_MARGIN_RAD,
        max_step_rad=None,
        continuity_weight=0.002,
    )


def _write_suzuri_groom(desk: dict, path: Path, *, clear_mm: float) -> None:
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv

    pool, near = _suzuri_contact_qpos(desk)
    clear = np.deg2rad(float(clear_mm) * desk_lift_gain(desk))
    near_clear = _raise_qpos(near, clear)
    roll = np.deg2rad(SUZURI_GROOM_ROLL_DEG)
    env = CalligraphyEnv(task="line", config=env_config_from_desk(desk))
    try:
        env.reset(seed=0, options={"layout_index": 0})
        limits = env._joint_limits
        rolled_pool = _retarget_wrist_roll(env, pool, roll, limits)
        rolled_near = _retarget_wrist_roll(env, near, roll, limits)
        rolled_near_clear = _retarget_wrist_roll(env, near_clear, roll, limits)
    finally:
        env.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        rolled_pool=rolled_pool,
        rolled_near=rolled_near,
        rolled_near_clear=rolled_near_clear,
        clear_mm=np.asarray(float(clear_mm)),
        roll_deg=np.asarray(SUZURI_GROOM_ROLL_DEG),
        desk_fingerprint=desk_fingerprint(desk),
    )
    print(f"毛先整え姿勢を保存 {path}（ID5 {SUZURI_GROOM_ROLL_DEG:.0f}°、穂先は硯の位置のまま）")


def _load_suzuri_groom(path: Path, desk: dict, *, clear_mm: float) -> dict[str, np.ndarray]:
    if not path.is_file():
        raise SystemExit(f"毛先整え姿勢がありません: {path}。prepare-groom を先に実行してください。")
    data = np.load(path, allow_pickle=True)
    if str(np.asarray(data["desk_fingerprint"]).item()) != desk_fingerprint(desk):
        raise SystemExit("毛先整え姿勢が今の desk と合いません。prepare-groom し直してください。")
    saved_clear = float(np.asarray(data["clear_mm"]).item())
    if abs(saved_clear - float(clear_mm)) > 0.1:
        raise SystemExit(
            f"毛先整えの clear が {saved_clear:.0f} mm で、今の --clear-mm {clear_mm:.0f} と違います。"
            " prepare-groom し直してください。"
        )
    return {key: np.asarray(data[key], dtype=np.float64) for key in ("rolled_pool", "rolled_near", "rolled_near_clear")}


def _prepare_suzuri_groom(args: argparse.Namespace) -> None:
    desk = require_ready(load_desk(args.desk))
    _write_suzuri_groom(desk, args.out, clear_mm=args.clear_mm)


def _suzuri_dips(pool: np.ndarray, near: np.ndarray, air: float, seconds: float):
    """手前→奥は air だけ浮かす。開始は手前。"""
    for i in range(1, SUZURI_TRIPS + 1):
        yield f"浮かす {i}/{SUZURI_TRIPS}", near, _add_joint(near, 1, air), seconds
        yield f"奥へ {i}/{SUZURI_TRIPS}", _add_joint(near, 1, air), _add_joint(pool, 1, air), seconds
        yield f"下ろす {i}/{SUZURI_TRIPS}", _add_joint(pool, 1, air), pool, seconds
        yield f"手前へ引く {i}/{SUZURI_TRIPS}", pool, near, seconds


def _suzuri_groom(
    near: np.ndarray,
    near_clear: np.ndarray,
    rolled_pool: np.ndarray,
    rolled_near: np.ndarray,
    rolled_near_clear: np.ndarray,
    dip_air: float,
    seconds: float,
):
    """ID5を90°回した姿勢は、穂先が元の硯位置に来るようIK済み。"""
    r_near_dip = _add_joint(rolled_near, 1, dip_air)
    r_pool_dip = _add_joint(rolled_pool, 1, dip_air)
    yield "整える:高く上げる", near, near_clear, seconds
    yield "整える:ID5 90°", near_clear, rolled_near_clear, seconds
    yield "整える:同じ場所へ", rolled_near_clear, rolled_near, seconds
    yield "整える:浮かす", rolled_near, r_near_dip, seconds
    yield "整える:奥へ", r_near_dip, r_pool_dip, seconds
    yield "整える:下ろす", r_pool_dip, rolled_pool, seconds
    yield "整える:手前へ引く", rolled_pool, rolled_near, seconds
    yield "整える:上げて戻す", rolled_near, rolled_near_clear, seconds
    yield "整える:ID5戻す", rolled_near_clear, near_clear, seconds


def _blend(start: np.ndarray, goal: np.ndarray, seconds: float, hz: float) -> np.ndarray:
    n = max(2, int(seconds * hz))
    alphas = np.linspace(0.0, 1.0, n)
    return np.stack([(1.0 - a) * start + a * goal for a in alphas], axis=0)


def _present_qpos(robot, desk: dict) -> np.ndarray:
    present = {
        name: float(value)
        for name, value in robot.bus.sync_read(
            "Present_Position", num_retry=3
        ).items()
    }
    return lerobot_to_qpos(
        present,
        tilt_sign=desk["tilt_sign"],
        offsets=playback_offsets(desk),
        gripper_map=desk_gripper_map(desk),
    )


def _capture_leader_alignment(
    robot,
    leader,
    desk: dict,
    align_rad: float,
    saved_offset: np.ndarray | None,
) -> np.ndarray:
    if saved_offset is not None:
        offset = np.asarray(saved_offset, dtype=np.float64)
        print("保存済みLeader補正を使います。両機を基準教示時と同じ姿勢へ合わせてください。")
        last_print = 0.0
        while True:
            follower = _present_qpos(robot, desk)
            target = _aligned_leader_qpos(desk, leader.get_action(), offset)
            worst = float(np.max(np.abs(target - follower)))
            if worst <= align_rad:
                input(f"補正後の姿勢差 {np.degrees(worst):.1f}°。EnterでFollower追従を有効化: ")
                follower = _present_qpos(robot, desk)
                target = _aligned_leader_qpos(desk, leader.get_action(), offset)
                if np.max(np.abs(target - follower)) <= align_rad:
                    return offset
                print("Enter中に姿勢がずれました。もう一度合わせます。")
            now = time.monotonic()
            if now - last_print >= 1.0:
                print(f"補正後の最大姿勢差 {np.degrees(worst):.1f}°（許容 {np.degrees(align_rad):.1f}°）")
                last_print = now
            time.sleep(0.05)

    print("FollowerはトルクOFFです。腕を支え、LeaderをFollowerと物理的に同じ姿勢へ合わせてEnterしてください。")
    follower_samples: deque[np.ndarray] = deque(maxlen=max(8, int(RECORD_HZ * 0.75)))
    leader_samples: deque[np.ndarray] = deque(maxlen=follower_samples.maxlen)
    last_print = 0.0
    while True:
        follower_samples.append(_present_qpos(robot, desk))
        leader_samples.append(_action_to_qpos(desk, leader.get_action()))
        if select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()
            try:
                offset = _leader_alignment_offset(
                    np.stack(follower_samples), np.stack(leader_samples)
                )
            except SystemExit as exc:
                print(exc)
                follower_samples.clear()
                leader_samples.clear()
                continue
            follower = _present_qpos(robot, desk)
            target = _aligned_leader_qpos(desk, leader.get_action(), offset)
            worst = float(np.max(np.abs(target - follower)))
            if worst <= align_rad:
                print(
                    f"Leaderゼロ点補正を取得しました。補正後の最大姿勢差 {np.degrees(worst):.1f}°。"
                )
                return offset
            print("Enter中に姿勢がずれました。姿勢を止めてもう一度Enterしてください。")
            follower_samples.clear()
            leader_samples.clear()
        now = time.monotonic()
        if now - last_print >= 1.0 and follower_samples:
            raw = np.abs(leader_samples[-1] - follower_samples[-1])
            worst_joint = JOINT_NAMES[int(np.argmax(raw))]
            print(f"未補正の最大差 {np.degrees(np.max(raw)):.1f}° ({worst_joint})")
            last_print = now
        time.sleep(1.0 / RECORD_HZ)


def _open_taught_session(
    args: argparse.Namespace, desk: dict, reference: dict | None = None
):
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
    from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

    _validate_follower_port(args.port, desk)
    follower_serial = _port_serial(args.port, "Follower")
    leader_serial = _port_serial(args.leader_port, "Leader")
    if follower_serial == leader_serial:
        raise SystemExit("LeaderとFollowerが同じUSBシリアルです。誤送信を避けるため停止します。")
    robot = SO101Follower(
        SO101FollowerConfig(
            port=args.port,
            id=ROBOT_ID,
            max_relative_target=None,
            position_p_coefficient=P_GAIN,
            disable_torque_on_disconnect=False,
        )
    )
    leader = SO101Leader(SO101LeaderConfig(port=args.leader_port, id=LEADER_ID))
    try:
        robot.bus.connect()
        robot.bus.disable_torque(num_retry=3)
        if not robot.bus.is_calibrated:
            raise SystemExit("Followerのサーボ本体較正がキャッシュと一致しません。")
        leader.connect(calibrate=False)
        if not leader.is_calibrated:
            raise SystemExit("Leaderのサーボ本体較正がキャッシュと一致しません。")
        leader_calibration_sha256 = hashlib.sha256(
            leader.calibration_fpath.read_bytes()
        ).hexdigest()
        if reference is not None:
            if reference.get("leader_usb_serial") != leader_serial:
                raise SystemExit("Leader USBシリアルが基準教示時と一致しません。")
            if reference.get("leader_calibration_sha256") != leader_calibration_sha256:
                raise SystemExit("Leader較正が基準教示時と一致しません。")

        offset = _capture_leader_alignment(
            robot,
            leader,
            desk,
            float(args.align_rad),
            None
            if reference is None
            else np.asarray(reference["leader_to_follower_offset_qpos"], dtype=np.float64),
        )

        present = {
            name: float(value)
            for name, value in robot.bus.sync_read(
                "Present_Position", num_retry=3
            ).items()
        }
        robot.bus.sync_write("Goal_Position", present)
        robot.bus.enable_torque(num_retry=3)
        for name in robot.bus.motors:
            robot.bus.write("P_Coefficient", name, P_GAIN)
            robot.bus.write("Acceleration", name, ACCEL)
            robot.bus.write("Goal_Velocity", name, CRUISE_VELOCITY)
        return robot, leader, _present_qpos(robot, desk), offset, {
            "follower_usb_serial": follower_serial,
            "leader_usb_serial": leader_serial,
            "leader_calibration_sha256": leader_calibration_sha256,
            "leader_to_follower_offset_qpos": [float(value) for value in offset],
        }
    except BaseException:
        try:
            leader.disconnect()
        except Exception:
            pass
        _disconnect_limp(robot)
        raise


def _follow_phase(
    robot,
    leader,
    desk: dict,
    prompt: str,
    previous_target: np.ndarray,
    leader_offset_qpos: np.ndarray,
    *,
    keep_all: bool,
    reference_cell: dict | None = None,
) -> tuple[list[dict[str, object]], np.ndarray]:
    print(prompt)
    window: deque[dict[str, object]] = deque(maxlen=max(8, int(RECORD_HZ * 0.75)))
    captured: list[dict[str, object]] = []
    period = 1.0 / RECORD_HZ
    previous = np.asarray(previous_target, dtype=np.float64).copy()
    while True:
        started = time.perf_counter()
        target = _aligned_leader_qpos(desk, leader.get_action(), leader_offset_qpos)
        if np.max(np.abs(target - previous)) > IK_MAX_STEP_RAD:
            raise SystemExit("Leader指令の隣接変化が5°を超えたため停止します。ゆっくり動かしてください。")
        _safe_send_qpos(robot, desk, target, previous)
        actual = _present_qpos(robot, desk)
        feedback = _read_feedback(robot)
        row: dict[str, object] = {
            "time_s": float(time.time()),
            "qpos": actual,
            **feedback,
        }
        if reference_cell is not None:
            excess = _reference_excess(reference_cell, feedback)
            if excess > float(reference_cell["safety_excess"]):
                hover = np.asarray(reference_cell["poses"]["hover"]["qpos"], dtype=np.float64)
                _safe_send_qpos(robot, desk, hover, previous)
                raise SystemExit("教示中の荷重が基準上限を超えたため空中姿勢へ退避しました。")
        window.append(row)
        if keep_all:
            captured.append(row)
        previous = target
        if select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()
            if len(window) < 5:
                print("サンプルが短すぎます。姿勢を保ってもう一度Enterしてください。")
            else:
                break
        remain = period - (time.perf_counter() - started)
        if remain > 0:
            time.sleep(remain)
    return (captured if keep_all else list(window)), previous


def _make_taught_air_qpos(
    qpos: np.ndarray,
    cells: np.ndarray,
    excess: np.ndarray,
    reference: dict,
) -> np.ndarray:
    qpos = np.asarray(qpos, dtype=np.float64)
    cells = np.asarray(cells, dtype=np.int8)
    excess = np.asarray(excess, dtype=np.float64)
    factors = np.zeros(len(qpos), dtype=np.float64)
    deltas = np.zeros_like(qpos)
    for cell in (0, 1):
        item = reference["cells"][str(cell)]
        mask = cells == cell
        factors[mask] = np.clip(
            excess[mask] / max(float(item["pen_down_excess"]), 1e-9), 0.0, 1.0
        )
        deltas[mask] = np.asarray(item["air_delta_qpos"], dtype=np.float64)
    # Widen the lifted interval around contact transitions without scipy.
    for _ in range(3):
        factors[1:] = np.maximum(factors[1:], factors[:-1])
        factors[:-1] = np.maximum(factors[:-1], factors[1:])
    return qpos + factors[:, None] * deltas


def _validate_taught_motion(qpos: np.ndarray, air_qpos: np.ndarray, desk: dict) -> None:
    if qpos.ndim != 2 or qpos.shape[1] != len(JOINT_NAMES) or air_qpos.shape != qpos.shape:
        raise SystemExit("Leader教示軌道の形状が不正です。")
    if len(qpos) < 10 or not np.isfinite(qpos).all() or not np.isfinite(air_qpos).all():
        raise SystemExit("Leader教示軌道が短いか有限でない値を含みます。")
    limits = np.asarray(require_joint_ranges(desk), dtype=np.float64)
    safe = np.stack(
        (limits[:, 0] + IK_LIMIT_MARGIN_RAD, limits[:, 1] - IK_LIMIT_MARGIN_RAD), axis=1
    )
    for name, values in (("本書き", qpos), ("空中", air_qpos)):
        if np.any(values < safe[:, 0]) or np.any(values > safe[:, 1]):
            raise SystemExit(f"Leader教示の{name}軌道が関節端2°以内に入ります。")
        if len(values) > 1 and np.max(np.abs(np.diff(values, axis=0))) > IK_MAX_STEP_RAD + 1e-8:
            raise SystemExit(f"Leader教示の{name}軌道で隣接変化が5°を超えます。")


def _teach_reference(args: argparse.Namespace) -> None:
    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    robot = leader = None
    success = False
    try:
        robot, leader, previous, leader_offset, identity = _open_taught_session(args, desk)
        cells: dict[str, dict] = {}
        for cell, label in ((0, "上段"), (1, "下段")):
            poses: dict[str, dict[str, object]] = {}
            for name, instruction in (
                ("hover", "筆先を紙から十分上げた空中姿勢"),
                ("contact", "筆先が紙に触れた瞬間の姿勢"),
                ("good", "実際に書きたい良い筆圧の姿勢"),
            ):
                rows, previous = _follow_phase(
                    robot,
                    leader,
                    desk,
                    f"{label}: {instruction}で止め、Enterしてください。",
                    previous,
                    leader_offset,
                    keep_all=False,
                )
                poses[name] = _reference_pose(rows)
            cells[str(cell)] = {"poses": poses, **_select_taught_signal(poses)}
        _add_reference_tip_heights(desk, cells)
        _, previous = _follow_phase(
            robot,
            leader,
            desk,
            "最後に筆先を紙から3〜5 cm上げ、止めてEnterしてください。",
            previous,
            leader_offset,
            keep_all=False,
        )
        payload = {
            "schema": TAUGHT_SCHEMA,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "desk_fingerprint": desk_fingerprint(desk),
            "motor_calibration_sha256": str(desk.get("motor_calibration_sha256") or ""),
            **identity,
            "cells": cells,
        }
        payload["reference_sha256"] = _canonical_sha256(payload)
        _write_json(args.out, payload)
        success = True
        print(f"Leader基準を保存: {args.out}")
    finally:
        if leader is not None:
            try:
                leader.disconnect()
            except Exception:
                pass
        if robot is not None:
            (_disconnect_holding if success else _disconnect_limp)(robot)


def _record_word(args: argparse.Namespace) -> None:
    word = _validate_taught_word(args.word)
    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    reference = _load_leader_reference(args.reference, desk)
    robot = leader = None
    success = False
    phases: list[list[dict[str, object]]] = []
    try:
        robot, leader, previous, leader_offset, _ = _open_taught_session(
            args, desk, reference
        )
        for cell, character in enumerate(word):
            rows, previous = _follow_phase(
                robot,
                leader,
                desk,
                f"{('上段' if cell == 0 else '下段')}の『{character}』を書き、"
                "最後に筆を上げてEnterしてください。",
                previous,
                leader_offset,
                keep_all=True,
                reference_cell=reference["cells"][str(cell)],
            )
            phases.append(rows)
        samples = [row for phase in phases for row in phase]
        cells = np.concatenate(
            [np.full(len(phase), cell, dtype=np.int8) for cell, phase in enumerate(phases)]
        )
        qpos = np.stack([np.asarray(row["qpos"], dtype=np.float64) for row in samples])
        times = np.asarray([float(row["time_s"]) for row in samples], dtype=np.float64)
        excess = np.asarray(
            [
                _reference_excess(reference["cells"][str(int(cell))], row)
                for cell, row in zip(cells, samples)
            ],
            dtype=np.float64,
        )
        pen_down = np.asarray(
            [
                value >= float(reference["cells"][str(int(cell))]["pen_down_excess"])
                for cell, value in zip(cells, excess)
            ],
            dtype=bool,
        )
        for cell in (0, 1):
            mask = cells == cell
            if int(np.sum(pen_down[mask])) < 5:
                raise SystemExit(f"{('上段' if cell == 0 else '下段')}で接地を検出できません。教示し直してください。")
            tail = np.flatnonzero(mask)[-min(5, int(np.sum(mask))):]
            if np.any(pen_down[tail]):
                raise SystemExit("Enter前に筆が上がっていません。筆を上げて記録し直してください。")
        air_qpos = _make_taught_air_qpos(qpos, cells, excess, reference)
        _validate_taught_motion(qpos, air_qpos, desk)
        feedback_keys = sorted(
            key for key in samples[0] if key.startswith("load:") or key.startswith("current:")
        )
        feedback_values = np.asarray(
            [[float(row[key]) for key in feedback_keys] for row in samples], dtype=np.float64
        )
        dt = float(np.median(np.diff(times))) if len(times) > 1 else 1.0 / RECORD_HZ
        out = args.out or _new_run_dir() / f"taught-{word}.npz"
        out.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            out,
            taught_schema=TAUGHT_SCHEMA,
            qpos=qpos,
            air_qpos=air_qpos,
            pen_down=pen_down,
            cell_index=cells,
            target_excess=np.maximum(excess, 0.0),
            feedback_keys=np.asarray(feedback_keys),
            feedback_values=feedback_values,
            dt=dt,
            kanji=word,
            desk_fingerprint=desk_fingerprint(desk),
            motor_calibration_sha256=str(desk.get("motor_calibration_sha256") or ""),
            reference_json=json.dumps(reference, sort_keys=True, ensure_ascii=False),
            reference_sha256=str(reference["reference_sha256"]),
        )
        success = True
        print(f"Leader教示を保存: {out}  {len(qpos)}点 / 接地{int(np.sum(pen_down))}点")
    finally:
        if leader is not None:
            try:
                leader.disconnect()
            except Exception:
                pass
        if robot is not None:
            (_disconnect_holding if success else _disconnect_limp)(robot)


def _record_suzuri(args: argparse.Namespace) -> None:
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
    from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    _validate_follower_port(args.port, desk)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    robot = SO101Follower(
        SO101FollowerConfig(
            port=args.port,
            id=ROBOT_ID,
            max_relative_target=None,
            position_p_coefficient=P_GAIN,
            disable_torque_on_disconnect=False,
        )
    )
    leader = SO101Leader(SO101LeaderConfig(port=args.leader_port, id=LEADER_ID))
    frames: list[np.ndarray] = []
    dt = 1.0 / RECORD_HZ
    try:
        _connect_hold_present(robot)
        for name in robot.bus.motors:
            robot.bus.write("P_Coefficient", name, P_GAIN)
            robot.bus.write("Acceleration", name, ACCEL)
            robot.bus.write("Goal_Velocity", name, CRUISE_VELOCITY)
        leader.connect(calibrate=False)
        if not leader.is_calibrated:
            raise SystemExit("Leader の較正がキャッシュと一致しません")
        print("Leader を持って硯の動きを教えてください。Follower が追います。")
        input("Enter で録画開始。もう一度 Enter か Ctrl+C で終了。")
        try:
            while True:
                t0 = time.perf_counter()
                action = leader.get_action()
                robot.send_action(action)
                frames.append(_action_to_qpos(desk, action))
                if select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.readline()
                    break
                remain = dt - (time.perf_counter() - t0)
                if remain > 0:
                    time.sleep(remain)
        except KeyboardInterrupt:
            print("\n録画を止めます")
    finally:
        try:
            leader.disconnect()
        except Exception:
            pass
        _disconnect_holding(robot)
    if len(frames) < 2:
        raise SystemExit("録画が短すぎます。Enter で開始してから動かしてください。")
    qpos = np.stack(frames)
    np.savez(args.out, qpos=qpos, dt=dt, desk_fingerprint=desk_fingerprint(desk))
    print(f"保存 {args.out}  {len(qpos)} steps, {len(qpos) * dt:.1f}s")


def _write_motion_gains(bus, p: int = P_GAIN) -> None:
    for name in bus.motors:
        bus.write("P_Coefficient", name, p)
        bus.write("Acceleration", name, ACCEL)
        bus.write("Goal_Velocity", name, CRUISE_VELOCITY)


def _pos_action(device) -> dict[str, float]:
    pos = device.bus.sync_read("Present_Position", num_retry=5)
    return {f"{name}.pos": float(pos[name]) for name in JOINT_NAMES}


def _action_offset(target: dict[str, float], source: dict[str, float]) -> dict[str, float]:
    return {key: float(target[key]) - float(source[key]) for key in source}


def _add_action(action: dict[str, float], offset: dict[str, float]) -> dict[str, float]:
    return {key: float(action[key]) + float(offset[key]) for key in action}


def _without_joint(
    action: dict[str, float], joint: str = "wrist_roll"
) -> dict[str, float]:
    key = f"{joint}.pos"
    return {name: value for name, value in action.items() if name != key}


def _limit_step(
    goal: dict[str, float],
    present: dict[str, float],
    max_deg: float = BILATERAL_STEP_DEG,
    max_grip: float = BILATERAL_STEP_GRIP,
) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, value in goal.items():
        now = float(present[key])
        cap = max_grip if key.startswith("gripper") else max_deg
        delta = max(-cap, min(cap, float(value) - now))
        out[key] = now + delta
    return out


def _hold_leader_present(leader) -> dict[str, float]:
    start = leader.get_action()
    print("Leader  ", format_joints({key.removesuffix(".pos"): value for key, value in start.items()}))
    leader.bus.sync_write(
        "Goal_Position",
        {key.removesuffix(".pos"): float(value) for key, value in start.items()},
    )
    leader.enable_torque()
    _write_motion_gains(leader.bus)
    return start


def _align_leader_to_follower(leader, present: dict[str, float], seconds: float = 8.0) -> None:
    start = _hold_leader_present(leader)
    goal = {f"{name}.pos": float(present[name]) for name in JOINT_NAMES}
    print(f"LeaderをFollowerへ {seconds:.0f}s で合わせます。")
    steps = [*np.linspace(0.0, 1.0, max(2, int(seconds * RECORD_HZ))), *([1.0] * int(RECORD_HZ))]
    for alpha in steps:
        t0 = time.perf_counter()
        leader.send_feedback(
            {key: (1.0 - alpha) * start[key] + alpha * goal[key] for key in goal}
        )
        remain = (1.0 / RECORD_HZ) - (time.perf_counter() - t0)
        if remain > 0:
            time.sleep(remain)


def _open_pair(args: argparse.Namespace):
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
    from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    _validate_follower_port(args.port, desk)
    if _port_serial(args.port, "Follower") == _port_serial(args.leader_port, "Leader"):
        raise SystemExit("LeaderとFollowerが同じUSBシリアルです。")
    robot = SO101Follower(
        SO101FollowerConfig(
            port=args.port,
            id=ROBOT_ID,
            max_relative_target=None,
            position_p_coefficient=P_GAIN,
            disable_torque_on_disconnect=False,
        )
    )
    leader = SO101Leader(SO101LeaderConfig(port=args.leader_port, id=LEADER_ID))
    try:
        present = _connect_hold_present(robot)
    except RuntimeError as exc:
        text = str(exc)
        if "Missing motor IDs" in text:
            raise SystemExit(
                "サーボが応答しません（ID5が消えていることが多い）。"
                "12Vを切って10秒待ち、デイジーチェーンを確認して入れ直してください。"
            ) from exc
        raise
    _write_motion_gains(robot.bus)
    print("Follower", format_joints(present))
    leader.connect(calibrate=False)
    if not leader.is_calibrated:
        raise SystemExit("Leader の較正がキャッシュと一致しません")
    return desk, robot, leader, present


def _close_pair(
    robot, leader, *, leader_torque: bool, follower_hold: bool = True
) -> None:
    if leader is not None:
        try:
            leader.bus.disconnect(disable_torque=not leader_torque)
        except Exception:
            pass
    if robot is not None:
        if follower_hold:
            _disconnect_holding(robot)
        else:
            _disconnect_limp(robot)


def _match_leader(args: argparse.Namespace) -> None:
    robot = leader = None
    try:
        _, robot, leader, present = _open_pair(args)
        _align_leader_to_follower(leader, present)
        print("LeaderをFollowerと同じ姿勢に合わせました。両方ともトルクは入ったままです。")
    finally:
        _close_pair(robot, leader, leader_torque=True)


def _bilateral(args: argparse.Namespace) -> None:
    robot = leader = None
    hold_follower = True
    stop = Path("/tmp/syodo-bilateral-stop")
    stop.unlink(missing_ok=True)
    rows = []
    try:
        desk, robot, leader, _present = _open_pair(args)
        start = _hold_leader_present(leader)
        leader.bus.disable_torque("wrist_roll")
        _write_motion_gains(leader.bus, LEADER_BILATERAL_P)
        offset = _action_offset(
            _without_joint(_pos_action(robot)), _without_joint(start)
        )
        inverse = {key: -value for key, value in offset.items()}
        print(
            "起動時の姿勢が原点。ID5は指令しない（手で置いたまま）。"
            "Ctrl+Cで終了。"
        )
        period = 1.0 / BILATERAL_HZ
        while not stop.exists():
            t0 = time.perf_counter()
            leader_all = _pos_action(leader)
            follower_all = _pos_action(robot)
            leader_now = _without_joint(leader_all)
            follower_now = _without_joint(follower_all)
            command = _limit_step(_add_action(leader_now, offset), follower_now)
            robot.send_action(command)
            leader.send_feedback(
                _limit_step(_add_action(follower_now, inverse), leader_now)
            )
            if getattr(args, "log", None):
                observed_q = _action_to_qpos(desk, follower_all)
                target_action = {**follower_all, **command}
                requested_q = _action_to_qpos(desk, target_action)
                row = {"phase": "bilateral", "host_monotonic_s": time.monotonic(),
                       "command_start_monotonic_s": t0, "pen_down": False}
                row.update({f"position_deg:{name}": float(np.degrees(value)) for name, value in zip(JOINT_NAMES, observed_q)})
                row.update({f"command_deg:{name}": float(np.degrees(value)) for name, value in zip(JOINT_NAMES, requested_q)})
                row.update(_read_feedback(robot))
                rows.append(row)
            remain = period - (time.perf_counter() - t0)
            if remain > 0:
                time.sleep(remain)
        print("停止ファイルを受け取りました。")
    except KeyboardInterrupt:
        print("\nバイラテを止めます")
    except (ConnectionError, RuntimeError, OSError) as exc:
        hold_follower = False
        print("通信が切れました。トルクを切ります。")
        print(exc)
        print(
            "Follower ID5が消えたら 12V を切って10秒待ち、"
            "基板→1→…→5→6 の鎖を見て入れ直してください。"
        )
    finally:
        try:
            if getattr(args, "log", None) and rows:
                args.log.parent.mkdir(parents=True, exist_ok=True)
                _write_feedback_csv(args.log, rows)
        finally:
            _close_pair(
                robot, leader, leader_torque=False, follower_hold=hold_follower
            )


def _play_taught(args: argparse.Namespace, desk: dict, data) -> None:
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

    reference = _validate_taught_data(data, desk)
    qpos = np.asarray(data["qpos"], dtype=np.float64)
    air_qpos = np.asarray(data["air_qpos"], dtype=np.float64)
    pen_down = np.asarray(data["pen_down"], dtype=bool)
    cells = np.asarray(data["cell_index"], dtype=np.int8)
    targets = np.asarray(data["target_excess"], dtype=np.float64)
    raw_dt = float(np.asarray(data["dt"]).item())
    dt = raw_dt / max(float(args.speed), 1e-6)
    stride = max(1, int(args.stride))
    period = dt * stride
    hz = 1.0 / max(dt, 1e-6)
    approach_s = max(float(args.approach_s), 6.0)
    word = str(reference["word"])
    log_path = args.log or _new_run_dir() / "write.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    camera: CameraWatchdog | None = None
    if args.camera_url:
        camera = CameraWatchdog(
            args.camera_url,
            log_path.parent,
            config=CameraWatchdogConfig(
                interval_s=args.camera_interval_s,
                timeout_s=args.camera_timeout_s,
                bad_frames=args.camera_bad_frames,
                save_every=args.camera_save_every,
                roi=args.camera_roi,
                scene_delta_limit=args.camera_scene_delta,
                outside_delta_limit=args.camera_outside_delta,
                paper_brightness_delta_limit=args.camera_paper_delta,
            ),
        )
        camera.start()
        ready_timeout = max(5.0, args.camera_timeout_s * args.camera_bad_frames + 1.0)
        if not camera.wait_ready(ready_timeout):
            failure = camera.failure or {}
            camera.stop()
            raise SystemExit(
                "ESP32カメラの有効なフレームを取得できないため書字を開始しません: "
                + str(failure.get("detail", failure.get("reason", "unknown")))
            )

    robot = SO101Follower(
        SO101FollowerConfig(
            port=args.port,
            id=ROBOT_ID,
            max_relative_target=None,
            position_p_coefficient=P_GAIN,
            disable_torque_on_disconnect=False,
        )
    )
    rows: list[dict[str, object]] = []
    success = False
    try:
        present = _connect_hold_present(robot)
        for name in robot.bus.motors:
            robot.bus.write("P_Coefficient", name, P_GAIN)
            robot.bus.write("Acceleration", name, ACCEL)
            robot.bus.write("Goal_Velocity", name, CRUISE_VELOCITY)
        start = lerobot_to_qpos(
            present,
            tilt_sign=desk["tilt_sign"],
            offsets=playback_offsets(desk),
            gripper_map=desk_gripper_map(desk),
        )
        print(f"Leader教示『{word}』: 墨なし空中再生を行います。腕を支えてください。")
        time.sleep(max(float(args.hold_s), 0.0))
        _send_qpos(
            robot,
            desk,
            _blend(start, air_qpos[0], approach_s, hz)[::stride],
            period,
            safe_qpos=air_qpos[0],
        )
        _send_qpos(robot, desk, air_qpos[::stride], period, safe_qpos=air_qpos[0])
        _send_qpos(
            robot, desk, air_qpos[::-1][::stride], period, safe_qpos=air_qpos[0]
        )
        input("空中再生を確認し、墨を付けて紙を準備したらEnter。本書きを開始します: ")
        if camera is not None and not camera.arm():
            raise SystemExit("カメラ監視の基準画像を取得できません。")
        _send_qpos(
            robot,
            desk,
            _blend(air_qpos[0], qpos[0], approach_s, hz)[::stride],
            period,
            safe_qpos=air_qpos[0],
        )
        previous = np.asarray(qpos[0], dtype=np.float64)
        limits = np.asarray(require_joint_ranges(desk), dtype=np.float64)
        safe_limits = np.stack(
            (limits[:, 0] + IK_LIMIT_MARGIN_RAD, limits[:, 1] - IK_LIMIT_MARGIN_RAD),
            axis=1,
        )
        for index in range(0, len(qpos), stride):
            started = time.perf_counter()
            cell = int(cells[index])
            item = reference["cells"][str(cell)]
            if camera is not None and camera.failure is not None:
                _safe_send_qpos(robot, desk, air_qpos[index], previous)
                failure = camera.failure or {}
                raise SystemExit(
                    "カメラ監視が異常を検出したため空中姿勢へ退避しました: "
                    + str(failure.get("reason", "unknown"))
                )
            metrics = _read_feedback(robot)
            measured = _reference_excess(item, metrics)
            if measured > float(item["safety_excess"]):
                _safe_send_qpos(robot, desk, air_qpos[index], previous)
                raise SystemExit("荷重がLeader教示上限を超えたため空中姿勢へ退避しました。")
            command = np.asarray(qpos[index], dtype=np.float64).copy()
            correction_scale = 0.0
            if pen_down[index]:
                good = max(float(item["good_excess"]), 1e-9)
                target = float(np.clip(targets[index], 0.0, float(item["safety_excess"])))
                correction_scale = float(np.clip(0.1 * (target - measured) / good, -0.1, 0.1))
                correction = (
                    np.asarray(item["pressure_direction_qpos"], dtype=np.float64)
                    * correction_scale
                )
                peak = float(np.max(np.abs(correction)))
                if peak > TAUGHT_PRESSURE_CORRECTION_RAD:
                    correction *= TAUGHT_PRESSURE_CORRECTION_RAD / peak
                command += correction
            if np.any(command < safe_limits[:, 0]) or np.any(command > safe_limits[:, 1]):
                _safe_send_qpos(robot, desk, air_qpos[index], previous)
                raise SystemExit("Leader筆圧補正が関節端2°以内に入ったため退避しました。")
            if np.max(np.abs(command - previous)) > IK_MAX_STEP_RAD + 1e-8:
                _safe_send_qpos(robot, desk, air_qpos[index], previous)
                raise SystemExit("Leader教示再生の隣接変化が5°を超えたため退避しました。")
            _safe_send_qpos(robot, desk, command, air_qpos[index])
            previous = command
            row: dict[str, object] = {
                "time_s": float(time.time()),
                "index": int(index),
                "phase": "write",
                "cell": cell,
                "line": -1,
                "pen_down": bool(pen_down[index]),
                "target_excess": float(targets[index]),
                "measured_excess": float(measured),
                "correction_scale": float(correction_scale),
            }
            row.update(metrics)
            rows.append(row)
            remain = period - (time.perf_counter() - started)
            if remain > 0:
                time.sleep(remain)
        if camera is not None:
            camera.disarm()
        _send_qpos(
            robot,
            desk,
            _blend(previous, air_qpos[-1], approach_s, hz)[::stride],
            period,
            safe_qpos=air_qpos[-1],
        )
        success = True
        trace_copy = log_path.parent / "taught.npz"
        if Path(args.trajectory).resolve() != trace_copy.resolve():
            shutil.copy2(args.trajectory, trace_copy)
        _write_feedback_csv(log_path, rows)
        _write_json(
            log_path.with_name("write.json"),
            {
                "kanji": word,
                "taught_schema": TAUGHT_SCHEMA,
                "desk_fingerprint": desk_fingerprint(desk),
                "reference_sha256": str(reference["reference_sha256"]),
                "status": "pending_user_review",
                "steps": len(qpos),
                "pen_down_steps": int(np.sum(pen_down)),
                "camera": camera.summary() if camera is not None else {"enabled": False},
            },
        )
        print(f"Leader教示を書き終えました。ログ: {log_path}")
    except BaseException as exc:
        _write_feedback_csv(log_path, rows)
        _write_json(
            log_path.with_name("write.json"),
            {
                "kanji": word,
                "taught_schema": TAUGHT_SCHEMA,
                "desk_fingerprint": desk_fingerprint(desk),
                "status": "aborted",
                "error": f"{type(exc).__name__}: {exc}",
                "camera": camera.summary() if camera is not None else {"enabled": False},
            },
        )
        raise
    finally:
        if camera is not None:
            camera.stop()
        (_disconnect_holding if success else _disconnect_limp)(robot)


def _play(args: argparse.Namespace) -> None:
    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    args.trajectory = _resolve_play_path(str(args.trajectory))
    print(f"play {args.trajectory}")
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

    _validate_follower_port(args.port, desk)
    sign, _ = playback_tilt(desk)
    offsets = playback_offsets(desk)
    data = np.load(args.trajectory, allow_pickle=True)
    if "taught_schema" in data:
        _play_taught(args, desk, data)
        return
    modern = _validate_trace_data(data, desk, args.allow_legacy_open_loop)
    qpos = np.asarray(data["qpos"], dtype=np.float64)
    air_qpos = np.asarray(data["air_qpos"], dtype=np.float64) if modern else None
    dt = float(np.asarray(data["dt"])) / max(args.speed, 1e-6)
    hz = 1.0 / dt
    kanji = str(np.asarray(data["kanji"]).item()) if "kanji" in data else "legacy"
    height_metadata = (
        json.loads(str(np.asarray(data["height_metadata_json"]).item()))
        if modern
        else None
    )
    log_path = (args.log or _new_run_dir() / "write.csv") if modern else None
    camera: CameraWatchdog | None = None
    if args.camera_url:
        if not modern or log_path is None:
            raise SystemExit("カメラ監視は新形式traceのplayだけ対応します")
        try:
            camera_config = CameraWatchdogConfig(
                interval_s=args.camera_interval_s,
                timeout_s=args.camera_timeout_s,
                bad_frames=args.camera_bad_frames,
                save_every=args.camera_save_every,
                roi=args.camera_roi,
                scene_delta_limit=args.camera_scene_delta,
                outside_delta_limit=args.camera_outside_delta,
                paper_brightness_delta_limit=args.camera_paper_delta,
            )
        except ValueError as exc:
            raise SystemExit(f"カメラ監視設定が不正です: {exc}") from exc
        camera = CameraWatchdog(
            args.camera_url,
            log_path.parent,
            config=camera_config,
        )
        camera.start()
        ready_timeout = max(5.0, args.camera_timeout_s * args.camera_bad_frames + 1.0)
        if not camera.wait_ready(ready_timeout):
            failure = camera.failure or {}
            camera.stop()
            raise SystemExit(
                "ESP32カメラの有効なフレームを取得できないため書字を開始しません: "
                + str(failure.get("detail", failure.get("reason", "unknown")))
            )
    print(f"再生 {len(qpos)} steps, {len(qpos) * dt:.1f}s, kanji={kanji}  腕を支えてください")
    robot = SO101Follower(
        SO101FollowerConfig(
            port=args.port,
            id=ROBOT_ID,
            max_relative_target=None,
            position_p_coefficient=P_GAIN,
            disable_torque_on_disconnect=False,
        )
    )
    try:
        present = _connect_hold_present(robot)
        for name in robot.bus.motors:
            robot.bus.write("P_Coefficient", name, P_GAIN)
            robot.bus.write("Acceleration", name, ACCEL)
            robot.bus.write("Goal_Velocity", name, CRUISE_VELOCITY)
        start = lerobot_to_qpos(
            present, tilt_sign=sign, offsets=offsets, gripper_map=desk_gripper_map(desk)
        )
        print("いま", format_joints(present))
        if args.hold_s > 0:
            print(f"{args.hold_s:.0f} 秒後に硯へ行きます。腕を支えてください。")
            time.sleep(args.hold_s)
        clear = np.deg2rad(args.clear_mm * desk_lift_gain(desk))
        start = _clamp_qpos(start, desk)
        hover = (
            np.asarray(data["standby_qpos"], dtype=np.float64)
            if modern
            else _joints_qpos(desk, desk["poses"]["hover_center"])
        )
        # 硯の前に紙の待機へ寄ると、バイラテ後のレストから待機へ行って硯がずれる。
        raised = _clamp_qpos(_raise_qpos(start, clear), desk)
        stride = max(1, int(args.stride))
        period = dt * stride
        travel_s = min(float(args.approach_s), TRAVEL_S)
        approach_s = max(float(args.approach_s), 6.0)
        air_rows: list[dict] = []
        recorded = _load_recorded_suzuri(args.suzuri, desk)
        if args.groom:
            recorded = None
        if recorded is None:
            if args.groom:
                print("毛先整え: 自動2往復のあと、硯の真上まで上げてからID5を90°回します")
            else:
                print(
                    f"硯の録画がありません（{args.suzuri}）。自動の{SUZURI_TRIPS}往復を使います。"
                    " record-suzuri で録ってください。"
                )
            contact = np.deg2rad(SUZURI_LIFT_MM * desk_lift_gain(desk))
            suzuri = _raise_qpos(_joints_qpos(desk, desk["poses"]["suzuri_pool"]), contact)
            pulled = _raise_qpos(_joints_qpos(desk, desk_suzuri_pull(desk)), contact)
            suzuri_up = _raise_qpos(suzuri, clear)
            pulled_up = _raise_qpos(pulled, clear)
            # シミュの硯は腕の左、実物は右。平行移動では拭う縁が向こう側に回るので
            # エキスパートは使わず、教示した墨池の関節へ直行する。
            legs: list[tuple[str, np.ndarray, np.ndarray, float]] = [
                ("筆を上げる", start, raised, travel_s),
                ("硯の上へ", raised, suzuri_up, travel_s),
                ("手前へ", suzuri_up, pulled_up, travel_s),
                ("硯の高さへ", pulled_up, pulled, travel_s),
            ]
            for label, a, b, seconds in legs:
                print(f"{label} {seconds:.1f}s")
                _send_qpos(
                    robot,
                    desk,
                    _blend(a, b, seconds, hz)[::stride],
                    period,
                    safe_qpos=hover,
                )
            dip_air = np.deg2rad(SUZURI_AIR_MM * desk_lift_gain(desk))
            suzuri_legs = list(_suzuri_dips(suzuri, pulled, dip_air, args.suzuri_s))
            if args.groom:
                rolled = _load_suzuri_groom(
                    Path(args.groom_npz), desk, clear_mm=args.clear_mm
                )
                suzuri_legs.extend(
                    _suzuri_groom(
                        pulled,
                        pulled_up,
                        rolled["rolled_pool"],
                        rolled["rolled_near"],
                        rolled["rolled_near_clear"],
                        dip_air,
                        args.suzuri_s,
                    )
                )
            for label, a, b, seconds in suzuri_legs:
                print(f"{label} {seconds:.1f}s")
                _send_qpos(
                    robot,
                    desk,
                    _blend(a, b, seconds, hz)[::stride],
                    period,
                    safe_qpos=hover,
                )
            after = (
                ("紙の上へ", pulled_up, hover, travel_s),
                ("字の位置へ", hover, qpos[0], approach_s),
            )
            if not args.groom:
                after = (("硯から上げる", pulled, pulled_up, travel_s),) + after
        else:
            suzuri_qpos, suzuri_dt = recorded
            here = start
            print(f"硯の録画を再生 {len(suzuri_qpos)} steps, {len(suzuri_qpos) * suzuri_dt:.1f}s")
            _send_qpos(
                robot,
                desk,
                _blend(here, suzuri_qpos[0], travel_s, hz)[::stride],
                period,
                safe_qpos=hover,
            )
            _send_qpos(robot, desk, suzuri_qpos, suzuri_dt, safe_qpos=hover)
            after = (
                ("紙の上へ", suzuri_qpos[-1], hover, travel_s),
                ("字の位置へ", hover, qpos[0], approach_s),
            )
        for label, a, b, seconds in after:
            print(f"{label} {seconds:.1f}s")
            _send_qpos(
                robot,
                desk,
                _blend(a, b, seconds, hz)[::stride],
                period,
                safe_qpos=hover,
            )
        print("書字")
        if modern:
            assert log_path is not None
            trace_copy = log_path.parent / "trace.npz"
            if Path(args.trajectory).resolve() != trace_copy.resolve():
                shutil.copy2(args.trajectory, trace_copy)
            write_rows: list[dict[str, object]] = []
            try:
                if camera is not None and not camera.arm():
                    failure = camera.failure or {}
                    _safe_send_qpos(robot, desk, hover, air_qpos[0])
                    raise SystemExit(
                        "カメラ監視を開始できないためhoverへ退避しました: "
                        + str(failure.get("reason", "no_baseline"))
                    )
                write_rows = _send_writing(
                    robot,
                    desk,
                    data,
                    qpos,
                    period,
                    stride,
                    air_rows,
                    camera=camera,
                    hover_qpos=hover,
                    recorded_rows=write_rows,
                )
            except BaseException as exc:
                _write_feedback_csv(log_path, [*air_rows, *write_rows])
                _write_json(
                    log_path.with_name("write.json"),
                    {
                        "kanji": kanji,
                        "trace_schema": int(np.asarray(data["trace_schema"]).item()),
                        "desk_fingerprint": desk_fingerprint(desk),
                        "height": height_metadata,
                        "status": "aborted",
                        "steps_completed": len(write_rows),
                        "error": f"{type(exc).__name__}: {exc}",
                        "camera": (
                            camera.summary() if camera is not None else {"enabled": False}
                        ),
                    },
                )
                raise
            if camera is not None:
                camera.disarm()
            _write_feedback_csv(log_path, [*air_rows, *write_rows])
            _write_json(
                log_path.with_name("write.json"),
                {
                    "kanji": kanji,
                    "trace_schema": int(np.asarray(data["trace_schema"]).item()),
                    "desk_fingerprint": desk_fingerprint(desk),
                    "height": height_metadata,
                    "status": "pending_user_review",
                    "steps": len(qpos),
                    "pen_down_steps": int(np.asarray(data["pen_down"], dtype=bool).sum()),
                    "cell_write_tip_z_m": [
                        float(value) for value in np.asarray(data["cell_write_tip_z_m"])
                    ],
                    "air_height_above_paper_mm": float(
                        np.asarray(data["air_height_above_paper_mm"]).item()
                    ),
                    "standby_height_above_paper_mm": float(
                        np.asarray(data["standby_height_above_paper_mm"]).item()
                    ),
                    "command_hz": float(np.asarray(data["command_hz"]).item()),
                    "pressure_mode": (
                        "leader_reference"
                        if str(np.asarray(data["reference_json"]).item() or "").strip()
                        else {
                            str(cell): str(item.get("mode", "open_loop"))
                            for cell, item in desk["pressure_calibration_v1"]["cells"].items()
                        }
                    ),
                    "camera": (
                        camera.summary() if camera is not None else {"enabled": False}
                    ),
                },
            )
            print(f"荷重・電流ログ: {log_path}")
        else:
            _send_qpos(robot, desk, qpos[::stride], period, safe_qpos=hover)
        if camera is not None:
            camera.disarm()
        print(f"筆を上げる {min(args.approach_s, TRAVEL_S):.1f}s")
        _send_qpos(
            robot,
            desk,
            _blend(qpos[-1], hover, travel_s, hz)[::stride],
            period,
            safe_qpos=hover,
        )
    finally:
        _disconnect_holding(robot)
        if camera is not None:
            camera.stop()


def _deg_action(q_deg: np.ndarray) -> dict[str, float]:
    return {f"{name}.pos": float(q_deg[i]) for i, name in enumerate(JOINT_NAMES)}


def _send_deg(
    robot,
    seq: np.ndarray,
    dt: float,
    *,
    desk: dict | None = None,
    safe_deg: np.ndarray | None = None,
) -> None:
    for q in seq:
        t0 = time.perf_counter()
        if desk is None:
            robot.send_action(_deg_action(q))
        else:
            safe_qpos = (
                None
                if safe_deg is None
                else _action_to_qpos(desk, _deg_action(safe_deg))
            )
            _safe_send_qpos(
                robot,
                desk,
                _action_to_qpos(desk, _deg_action(q)),
                safe_qpos,
            )
        remain = dt - (time.perf_counter() - t0)
        if remain > 0:
            time.sleep(remain)


def _raise(q: np.ndarray, shoulder_deg: float) -> np.ndarray:
    """Lift the tip off the sheet without touching the fold, so the brush keeps its angle."""
    out = np.asarray(q, dtype=np.float64).copy()
    out[1] += shoulder_deg
    return out


def _lock_fold(q: np.ndarray, template: np.ndarray) -> np.ndarray:
    """Keep elbow + brush on the standing 手前左 pose. Interpolate pan and lift only."""
    out = np.asarray(q, dtype=np.float64).copy()
    out[2:] = np.asarray(template, dtype=np.float64)[2:]
    return out


def _connect_hold_present(robot) -> dict[str, float]:
    """Torque on at the limp pose. Do not track a stale Goal_Position from last play."""
    robot.bus.connect()
    try:
        robot.bus.disable_torque(num_retry=3)
        if not robot.bus.is_calibrated:
            raise RuntimeError("サーボ本体の較正がキャッシュと一致しません")
        present = {
            motor: float(value)
            for motor, value in robot.bus.sync_read("Present_Position", num_retry=3).items()
        }
        robot.bus.sync_write("Goal_Position", present)
        robot.bus.enable_torque(num_retry=3)
        return present
    except Exception:
        try:
            robot.bus.disable_torque(num_retry=1)
            robot.bus.disconnect(disable_torque=False)
        except Exception:
            pass
        raise


def _grid_pressure_calibration(desk: dict, count: int) -> dict:
    """Share depth-based open-loop settings across columns, never taught feedback."""
    calibration = desk["pressure_calibration_v1"]
    if count <= 2:
        return calibration
    cells = calibration.get("cells", {})
    if any(cells.get(str(row), {}).get("mode") != "open_loop" for row in range(2)):
        raise SystemExit("3〜4文字には奥・手前のopen_loop筆圧較正が必要です。2文字用の閉ループ基準は転用できません")
    return {**calibration, "cells": {str(i): dict(cells[str(i % 2)]) for i in range(count)}}


def _air_baselines(rows: list[dict[str, float]], calibration: dict) -> dict[tuple[int, str], float]:
    result: dict[tuple[int, str], float] = {}
    for cell, item in calibration.get("cells", {}).items():
        key = item.get("channel")
        if key is None:
            continue
        values = [row[key] for row in rows if row["cell"] == int(cell)]
        if values:
            result[(int(cell), key)] = float(np.median(values))
        elif item.get("air_median") is not None:
            result[(int(cell), key)] = float(item["air_median"])
    return result


def _send_writing(
    robot,
    desk: dict,
    data,
    qpos: np.ndarray,
    period: float,
    stride: int,
    air_rows: list[dict[str, object]],
    *,
    camera: CameraWatchdog | None = None,
    hover_qpos: np.ndarray | None = None,
    recorded_rows: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    reference = None
    if "reference_json" in data and str(np.asarray(data["reference_json"]).item()):
        reference = _reference_from_trace(data, desk)
    calibration = reference or _grid_pressure_calibration(
        desk, len(str(np.asarray(data.get("kanji", "字")).item()))
    )
    baselines = _air_baselines(air_rows, calibration)
    limits = np.asarray(desk_joint_ranges(desk), dtype=np.float64)
    safe_limits = np.stack(
        (limits[:, 0] + IK_LIMIT_MARGIN_RAD, limits[:, 1] - IK_LIMIT_MARGIN_RAD), axis=1
    )
    dq_dz = np.asarray(data["dq_dz"], dtype=np.float64)
    down = np.asarray(data["pen_down"], dtype=bool)
    cells = np.asarray(data["cell_index"], dtype=np.int8)
    pressures = np.asarray(data["target_pressure"], dtype=np.float64)
    air_qpos = np.asarray(data["air_qpos"], dtype=np.float64)
    safety = {key: float(value) for key, value in calibration.get("safety", {}).items()}
    rows: list[dict[str, object]] = recorded_rows if recorded_rows is not None else []
    previous = np.asarray(qpos[0], dtype=np.float64)
    for index in range(0, len(qpos), stride):
        started = time.perf_counter()
        command_start_monotonic = time.monotonic()
        if camera is not None and camera.failure is not None:
            failure = camera.failure or {}
            camera.disarm()
            retreat = air_qpos[index] if hover_qpos is None else hover_qpos
            _safe_send_qpos(robot, desk, retreat, air_qpos[index])
            reason = str(failure.get("reason", "camera_failure"))
            raise SystemExit(f"カメラ監視が{reason}を検出したためhoverへ退避しました")
        command = np.asarray(qpos[index], dtype=np.float64).copy()
        metrics: dict[str, float] = {}
        measured_excess: float | None = None
        target_excess: float | None = None
        delta_z = 0.0
        cell = int(cells[index])
        if down[index] and cell >= 0:
            item = calibration["cells"].get(str(cell))
            if not isinstance(item, dict):
                raise SystemExit(f"筆圧較正にcell={cell}がありません")
            try:
                metrics = _read_feedback(robot)
            except Exception:
                try:
                    _safe_send_qpos(robot, desk, air_qpos[index])
                finally:
                    raise
            key = item.get("channel")
            if reference is not None and key:
                baseline = baselines.get((cell, key), float(item["poses"]["hover"]["feedback_median"][key]))
                measured_excess = float(item.get("sign", 1)) * (metrics[key] - baseline)
                if measured_excess > float(item["safety_excess"]):
                    _safe_send_qpos(robot, desk, air_qpos[index])
                    raise SystemExit("荷重がLeader教示上限を超えたため空中姿勢へ退避しました。")
                target_excess = float(item["good_excess"]) * float(
                    np.clip(pressures[index] / PRESSURE_NOMINAL, 0.0, 1.35)
                )
                depth_m = float(item["contact_tip_z_m"]) - float(item["write_tip_z_m"])
                response = float(item["good_excess"]) - float(item["contact_excess"])
                slope = response / depth_m if depth_m > 1e-6 and response > 0.0 else 0.0
                if slope > 0.0:
                    delta_z = float(
                        np.clip(-(target_excess - measured_excess) / slope, -0.0002, 0.0002)
                    )
                    command += dq_dz[index] * delta_z
            else:
                thresholds = {
                    name: float(value)
                    for name, value in item.get("safety", safety).items()
                }
                exceeded = [
                    name for name, limit in thresholds.items() if metrics.get(name, 0.0) > limit
                ]
                if exceeded:
                    _safe_send_qpos(robot, desk, air_qpos[index])
                    raise SystemExit(
                        "サーボ荷重が較正最深線を超えたため退避しました: " + ", ".join(exceeded)
                    )
            if (
                reference is None
                and item.get("mode") == "closed_loop"
                and key
                and float(item.get("slope_per_m", 0.0)) > 0.0
            ):
                baseline = baselines.get((cell, key), float(item.get("air_median", 0.0)))
                measured_excess = float(item.get("sign", 1)) * (metrics[key] - baseline)
                target_excess = float(item.get("selected_excess", 0.0)) * float(
                    np.clip(pressures[index] / PRESSURE_NOMINAL, 0.0, 1.35)
                )
                delta_z = -(target_excess - measured_excess) / float(item["slope_per_m"])
                delta_z = float(np.clip(delta_z, -0.0002, 0.0002))
                command += dq_dz[index] * delta_z
            if np.any(command < safe_limits[:, 0]) or np.any(command > safe_limits[:, 1]):
                try:
                    _safe_send_qpos(robot, desk, air_qpos[index])
                finally:
                    raise SystemExit("筆圧補正が実機関節の安全範囲を超えたため退避しました")
        # The reading precedes the next waypoint: compare it with the last
        # sent command to separate servo lag from planned geometric error.
        try:
            observed = _present_qpos(robot, desk)
            if observed.shape != (6,) or not np.isfinite(observed).all():
                raise ValueError("Follower位置の読み戻しが不正です")
        except Exception:
            _safe_send_qpos(robot, desk, air_qpos[index])
            raise
        tracking = float(np.rad2deg(np.max(np.abs(observed - previous))))
        previous_command = previous.copy()
        _send_smoothed_target(
            robot,
            desk,
            previous,
            command,
            max(period - (time.perf_counter() - started), 0.0),
            air_qpos[index],
        )
        previous = command
        row: dict[str, object] = {
            "time_s": float(time.time()),
            "host_monotonic_s": time.monotonic(),
            "command_start_monotonic_s": command_start_monotonic,
            "force_plate_session": os.environ.get("SYODO_FORCE_PLATE_SESSION", ""),
            "index": int(index),
            "phase": "write",
            "cell": cell,
            "line": -1,
            "pen_down": bool(down[index]),
            "tracking_error_max_deg": tracking,
            "target_pressure": float(pressures[index]),
            "target_excess": target_excess,
            "measured_excess": measured_excess,
            "pressure_delta_z_mm": delta_z * 1000.0,
        }
        if "expected_tip_xyz" in data:
            for axis, value in zip("xyz", data["expected_tip_xyz"][index]):
                row[f"expected_tip_{axis}_m"] = float(value)
        row.update(metrics)
        for joint, measured, prior, requested in zip(JOINT_NAMES, observed, previous_command, command):
            row[f"position_deg:{joint}"] = float(np.rad2deg(measured))
            row[f"previous_command_deg:{joint}"] = float(np.rad2deg(prior))
            row[f"command_deg:{joint}"] = float(np.rad2deg(requested))
        rows.append(row)
    return rows


def _stroke(args: argparse.Namespace) -> None:
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    _validate_follower_port(args.port, desk)
    try:
        _, start, end, _ = (
            goal for _, goal in taught_ichi_waypoints(desk, lift_mm=args.lift_mm)
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    hz = 12.0
    dt = 1.0 / hz
    print(
        f"教示した手前左→手前右の横画。教示接地から {args.lift_mm:.1f} mm 上げます。"
        "折りと ID6 は下手左のまま。途中で机に食い込んだら支えて止めてください。"
    )
    robot = SO101Follower(
        SO101FollowerConfig(
            port=args.port,
            id=ROBOT_ID,
            max_relative_target=None,
            position_p_coefficient=P_GAIN,
            disable_torque_on_disconnect=False,
        )
    )
    try:
        present = _connect_hold_present(robot)
        for name in robot.bus.motors:
            robot.bus.write("P_Coefficient", name, P_GAIN)
            robot.bus.write("Acceleration", name, ACCEL)
            robot.bus.write("Goal_Velocity", name, CRUISE_VELOCITY)
        here = np.asarray([present[name] for name in JOINT_NAMES], dtype=np.float64)
        start[4:] = here[4:]
        end = _lock_fold(end, start)
        print("いま", format_joints(present))
        print(
            f"{args.hold_s:.0f} 秒後に硯へ行ってから下手左へ。腕を支えてください。"
        )
        time.sleep(max(args.hold_s, 0.0))
        # ponytail: 逃がし量は下手左で測った換算。here が大きく違う姿勢だと実際の
        # 逃がしは前後する。紙を擦らない側に振れるよう既定を厚めに取ってある。
        clear = args.clear_mm * desk_lift_gain(desk)
        contact = SUZURI_LIFT_MM * desk_lift_gain(desk)
        suzuri = _raise(pose_deg(desk, "suzuri_pool"), contact)
        pulled = _raise(
            np.asarray(
                [desk_suzuri_pull(desk)[name] for name in JOINT_NAMES], dtype=np.float64
            ),
            contact,
        )
        phases = (
            ("筆を上げる", here, _raise(here, clear), args.up_s, False),
            ("硯の上へ", _raise(here, clear), _raise(suzuri, clear), args.approach_s, False),
            ("手前へ", _raise(suzuri, clear), _raise(pulled, clear), args.up_s, False),
            ("硯の高さへ", _raise(pulled, clear), pulled, args.down_s, False),
        )
        for label, a, b, seconds, on_paper in phases:
            print(f"{label} {seconds:.1f}s")
            _send_deg(
                robot,
                _blend(a, b, seconds, hz),
                dt,
                desk=desk,
                safe_deg=pose_deg(desk, "hover_center"),
            )
        for label, a, b, seconds in _suzuri_dips(
            suzuri,
            pulled,
            SUZURI_AIR_MM * desk_lift_gain(desk),
            args.suzuri_s,
        ):
            print(f"{label} {seconds:.1f}s")
            _send_deg(
                robot,
                _blend(a, b, seconds, hz),
                dt,
                desk=desk,
                safe_deg=pose_deg(desk, "hover_center"),
            )
        phases = (
            ("硯から上げる", pulled, _raise(pulled, clear), args.up_s, False),
            ("下手左の上へ", _raise(pulled, clear), _raise(start, clear), args.approach_s, False),
            ("下ろす", _raise(start, clear), start, args.down_s, True),
            ("横画", start, end, args.stroke_s, True),
            ("筆を上げる", end, _raise(end, clear), args.up_s, False),
        )
        for label, a, b, seconds, on_paper in phases:
            print(f"{label} {seconds:.1f}s")
            _send_deg(
                robot,
                _blend(a, b, seconds, hz),
                dt,
                desk=desk,
                safe_deg=pose_deg(desk, "hover_center"),
            )
            if on_paper and args.mark_s > 0.0:
                # トルクは入ったままなので、この間サーボは端で静止する。
                print(f"  {args.mark_s:.0f} 秒静止。毛先の位置に印をつけてください。")
                time.sleep(args.mark_s)
    finally:
        _disconnect_holding(robot)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--desk", type=Path, default=DEFAULT_DESK_PATH)
    sub = parser.add_subparsers(dest="cmd", required=True)
    dump = sub.add_parser("dump", parents=[common])
    dump.add_argument("--out", type=Path, default=Path("/tmp/ichi.npz"))
    dump.add_argument("--kanji", default="一")
    dump.add_argument("--kanjivg-cache", type=Path, default=Path("data/kanjivg"))
    dump.add_argument("--max-steps", type=int, default=20_000)
    trace = sub.add_parser("trace", parents=[common])
    trace.add_argument("kanji")
    trace.add_argument("--out", type=Path, default=None)
    trace.add_argument("--kanjivg-cache", type=Path, default=Path("data/kanjivg"))
    trace.add_argument(
        "--reference",
        type=Path,
        default=DEFAULT_LEADER_REFERENCE_PATH,
        help="上下別の接触・良い筆圧を保存したLeader基準",
    )
    trace.add_argument(
        "--lift-mm",
        type=float,
        default=DEFAULT_WRITE_LIFT_MM,
        help="教示接地から上げる mm",
    )
    trace.add_argument("--clear-mm", type=float, default=32.0, help="互換用。画間は 60 mm 固定")
    trace.add_argument("--step-mm", type=float, default=3.0, help="点の間隔")
    trace.add_argument("--speed-mm-s", type=float, default=16.0)
    trace.add_argument("--tolerance-mm", type=float, default=1.0)
    trace.add_argument("--glyph-mm", type=float, default=None, help="文字の正方形の辺。指定時は勝手に縮小しない")
    trace.add_argument("--calibrated-heights", action="store_true", help="上下の実測筆圧を使い、固定20 mm補正を使わない")
    trace.add_argument("--air-mm", type=float, default=DEFAULT_AIR_HEIGHT_MM)
    trace.add_argument("--standby-mm", type=float, default=DEFAULT_STANDBY_HEIGHT_MM)
    pressure_plan = sub.add_parser("pressure-plan", parents=[common])
    pressure_plan.add_argument("--out", type=Path, default=None)
    pressure_plan.add_argument("--step-mm", type=float, default=3.0)
    pressure_plan.add_argument("--speed-mm-s", type=float, default=10.0)
    pressure_plan.add_argument("--clear-mm", type=float, default=20.0)
    pressure_plan.add_argument("--tolerance-mm", type=float, default=1.0)
    pressure_plan.add_argument("--lifts-mm", type=lambda text: tuple(float(v) for v in text.split(',')), default=PRESSURE_LIFTS_MM)
    pressure_calibrate = sub.add_parser("pressure-calibrate", parents=[common])
    pressure_calibrate.add_argument("plan", type=Path)
    pressure_calibrate.add_argument("--port", default=DEFAULT_PORT)
    pressure_calibrate.add_argument("--speed", type=float, default=0.25)
    pressure_calibrate.add_argument("--approach-s", type=float, default=6.0)
    pressure_calibrate.add_argument("--stride", type=int, default=1)
    pressure_calibrate.add_argument("--log", type=Path, default=None)
    pressure_calibrate.add_argument("--approach-plan", type=Path, default=None)
    teach_reference = sub.add_parser("teach-reference", parents=[common])
    teach_reference.add_argument("--port", default=DEFAULT_PORT)
    teach_reference.add_argument("--leader-port", default=DEFAULT_LEADER_PORT)
    teach_reference.add_argument("--out", type=Path, default=DEFAULT_LEADER_REFERENCE_PATH)
    teach_reference.add_argument(
        "--align-deg",
        dest="align_rad",
        type=lambda value: np.deg2rad(float(value)),
        default=LEADER_ALIGN_RAD,
        help="Follower追従を有効化できる初期最大関節差",
    )
    record_word = sub.add_parser("record-word", parents=[common])
    record_word.add_argument("word")
    record_word.add_argument("--port", default=DEFAULT_PORT)
    record_word.add_argument("--leader-port", default=DEFAULT_LEADER_PORT)
    record_word.add_argument("--reference", type=Path, default=DEFAULT_LEADER_REFERENCE_PATH)
    record_word.add_argument("--out", type=Path, default=None)
    record_word.add_argument(
        "--align-deg",
        dest="align_rad",
        type=lambda value: np.deg2rad(float(value)),
        default=LEADER_ALIGN_RAD,
        help="Follower追従を有効化できる初期最大関節差",
    )
    play = sub.add_parser("play", parents=[common])
    play.add_argument("trajectory", help="NPZパス、または trace 済みの1〜4文字")
    play.add_argument("--port", default=DEFAULT_PORT)
    play.add_argument("--speed", type=float, default=1.5, help="1.0 = sim time")
    play.add_argument("--approach-s", type=float, default=6.0)
    play.add_argument("--hold-s", type=float, default=0.0)
    play.add_argument("--clear-mm", type=float, default=45.0, help="硯の移動で肩を逃がす mm")
    play.add_argument("--suzuri-s", type=float, default=2.0, help="硯の一往路にかける秒数（録画が無いとき）")
    play.add_argument(
        "--suzuri",
        type=Path,
        default=DEFAULT_SUZURI_PATH,
        help="Leader で録った硯。あれば書字の前に再生する",
    )
    play.add_argument("--stride", type=int, default=1, help="Send every Nth sample")
    play.add_argument(
        "--groom",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="硯2往復のあと、ID5を90°回して毛先を整える（既定オン。穂先はIKで硯位置に保つ）",
    )
    play.add_argument(
        "--groom-npz",
        type=Path,
        default=DEFAULT_SUZURI_GROOM_PATH,
        help="prepare-groom が書いた毛先整え姿勢",
    )
    play.add_argument("--allow-legacy-open-loop", action="store_true")
    play.add_argument("--log", type=Path, default=None)
    play.add_argument(
        "--camera-url",
        default=None,
        help="ESP32 camera base URL。指定時は映像断・大きな画面異常でhover退避",
    )
    play.add_argument(
        "--camera-roi",
        type=_camera_roi,
        default=(0.08, 0.08, 0.92, 0.92),
        metavar="X0,Y0,X1,Y1",
        help="画像内の紙面・書字領域（0-1正規化）",
    )
    play.add_argument("--camera-interval-s", type=float, default=0.5)
    play.add_argument("--camera-timeout-s", type=float, default=1.5)
    play.add_argument("--camera-bad-frames", type=int, default=3)
    play.add_argument("--camera-save-every", type=int, default=1)
    play.add_argument("--camera-scene-delta", type=float, default=35.0)
    play.add_argument("--camera-outside-delta", type=float, default=18.0)
    play.add_argument("--camera-paper-delta", type=float, default=50.0)
    prepare_groom = sub.add_parser("prepare-groom", parents=[common])
    prepare_groom.add_argument("--out", type=Path, default=DEFAULT_SUZURI_GROOM_PATH)
    prepare_groom.add_argument("--clear-mm", type=float, default=45.0)
    record_suzuri = sub.add_parser("record-suzuri", parents=[common])
    record_suzuri.add_argument("--port", default=DEFAULT_PORT)
    record_suzuri.add_argument("--leader-port", default=DEFAULT_LEADER_PORT)
    record_suzuri.add_argument("--out", type=Path, default=DEFAULT_SUZURI_PATH)
    match_leader = sub.add_parser("match-leader", parents=[common])
    match_leader.add_argument("--port", default=DEFAULT_PORT)
    match_leader.add_argument("--leader-port", default=DEFAULT_LEADER_PORT)
    bilateral = sub.add_parser("bilateral", parents=[common])
    bilateral.add_argument("--port", default=DEFAULT_PORT)
    bilateral.add_argument("--leader-port", default=DEFAULT_LEADER_PORT)
    bilateral.add_argument("--log", type=Path, default=None)
    stroke = sub.add_parser("stroke", parents=[common])
    stroke.add_argument("--port", default=DEFAULT_PORT)
    stroke.add_argument("--hold-s", type=float, default=5.0)
    stroke.add_argument("--approach-s", type=float, default=12.0)
    stroke.add_argument("--down-s", type=float, default=14.0)
    stroke.add_argument("--stroke-s", type=float, default=16.0)
    stroke.add_argument("--up-s", type=float, default=12.0)
    stroke.add_argument("--mark-s", type=float, default=0.0, help="各端で静止して印をつける秒数")
    stroke.add_argument("--lift-mm", type=float, default=8.0, help="教示接地から毛先を上げる mm")
    stroke.add_argument("--clear-mm", type=float, default=25.0, help="移動中に紙から逃がす mm")
    stroke.add_argument("--suzuri-s", type=float, default=4.0, help="硯の一往路（手前 7 cm）にかける秒数")
    args = parser.parse_args()
    if args.cmd == "dump":
        _dump(args)
    elif args.cmd == "trace":
        _trace(args)
    elif args.cmd == "pressure-plan":
        _pressure_plan(args)
    elif args.cmd == "pressure-calibrate":
        _pressure_calibrate(args)
    elif args.cmd == "teach-reference":
        _teach_reference(args)
    elif args.cmd == "record-word":
        _record_word(args)
    elif args.cmd == "play":
        _play(args)
    elif args.cmd == "prepare-groom":
        _prepare_suzuri_groom(args)
    elif args.cmd == "record-suzuri":
        _record_suzuri(args)
    elif args.cmd == "match-leader":
        _match_leader(args)
    elif args.cmd == "bilateral":
        _bilateral(args)
    else:
        _stroke(args)


if __name__ == "__main__":
    main()
