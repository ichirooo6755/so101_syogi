"""Offline checks for the physical two-character trajectory and pressure path."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil

import numpy as np
import pytest

from scripts.hardware_calibrate import _set_brush, _sync_limits, _record_pose
from scripts.hardware_write import (
    COMMAND_HZ,
    DEFAULT_AIR_HEIGHT_MM,
    DEFAULT_LOWER_CELL_EXTRA_PRESS_MM,
    DEFAULT_STANDBY_HEIGHT_MM,
    DEFAULT_U_KANMURI_LIFT_MM,
    TAUGHT_SCHEMA,
    TRACE_SCHEMA,
    _canonical_sha256,
    _clamp_qpos,
    _disconnect_limp,
    _dump,
    _play,
    _interpolate_joint_target,
    _add_action,
    _action_offset,
    _limit_step,
    _without_joint,
    _leader_alignment_offset,
    _load_recorded_suzuri,
    _make_taught_air_qpos,
    _pressure_profile_from_samples,
    _resolve_play_path,
    _safe_send_qpos,
    _select_taught_signal,
    _send_writing,
    _suzuri_contact_qpos,
    _suzuri_dips,
    _suzuri_groom,
    _retarget_wrist_roll,
    _write_suzuri_groom,
    _apply_depth_profile,
    _trace,
    _validate_follower_port,
    _validate_taught_data,
    _validate_taught_motion,
    _validate_taught_word,
    _validate_trace_data,
    PRESSURE_LIFTS_MM,
)
from so101_calligraphy.config import JOINT_NAMES, PaperConfig
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.hardware_desk import (
    SUZURI_PULL_M,
    _tip_and_axis,
    desk_fingerprint,
    desk_gripper_map,
    desk_joint_ranges,
    env_config_from_desk,
    fit_suzuri_pull,
    glyph_cells,
    hardware_height_metadata,
    lerobot_to_qpos,
    load_desk,
    playback_offsets,
    solve_desk,
    REQUIRED_POSES,
    SIM_HOME_POSE,
)


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "tests/fixtures/follower-calibration.json"


@pytest.mark.parametrize("command", [_dump, _play])
@pytest.mark.parametrize("data", [{}, {"schema": 1, "ready": True}, {"schema": 1, "ready": "true"}])
def test_uncalibrated_dump_and_play_stop_before_loading_trajectory_or_robot(
    tmp_path: Path, command, data,
) -> None:
    path = tmp_path / "desk.json"
    if data:
        path.write_text(json.dumps(data), encoding="utf-8")
    # No other arguments or LeRobot dependency are needed to reject this desk.
    with pytest.raises(SystemExit, match="デスク較正"):
        command(argparse.Namespace(desk=path))


@pytest.mark.parametrize("limits", [[0, float("nan")], [float("-inf"), 4095], [500, 100]])
def test_sync_limits_rejects_invalid_arm_range_without_saving(tmp_path: Path, limits) -> None:
    desk_path = _synced_desk(tmp_path)
    before = desk_path.read_bytes()
    calibration = json.loads(CALIBRATION.read_text())
    calibration["elbow_flex"].update(range_min=limits[0], range_max=limits[1])
    calibration_path = tmp_path / "invalid.json"
    calibration_path.write_text(json.dumps(calibration))
    with pytest.raises(SystemExit, match="elbow_flex の較正範囲"):
        _sync_limits(argparse.Namespace(
            desk=desk_path, robot_calibration=calibration_path,
            usb_serial="test-follower", port="/dev/test-follower",
        ))
    assert desk_path.read_bytes() == before


def _calibration_source(tmp_path: Path) -> Path:
    return CALIBRATION


def _synced_desk(tmp_path: Path) -> Path:
    path = tmp_path / "desk.json"
    shutil.copyfile(ROOT / "tests/fixtures/hardware-desk.json", path)
    _sync_limits(
        argparse.Namespace(
            desk=path,
            robot_calibration=_calibration_source(tmp_path),
            usb_serial="test-follower",
            port="/dev/test-follower",
        )
    )
    desk = load_desk(path)
    # Explicit offline pressure fixture; never read this Mac's live calibration.
    desk["pressure_calibration_v1"] = {
        "desk_fingerprint": desk_fingerprint(desk),
        "mode": "open_loop",
        "cells": {
            str(cell): {"mode": "open_loop", "channel": None, "fallback_lift_mm": lift, "safety": {}}
            for cell, lift in enumerate((4.0, -16.0))
        },
        "safety": {},
    }
    path.write_text(json.dumps(desk), encoding="utf-8")
    return path


def test_brush_geometry_migration_preserves_same_reach_calibration(tmp_path: Path) -> None:
    path = tmp_path / "legacy-desk.json"
    shutil.copyfile(ROOT / "tests/fixtures/hardware-desk.json", path)
    legacy = load_desk(path)
    legacy.pop("brush_total_cm")
    legacy.pop("brush_rigid_cm")
    legacy["brush_tuft_cm"] = 12.0  # legacy field actually held grip-to-tip reach
    legacy["pressure_calibration_v1"] = {
        "desk_fingerprint": desk_fingerprint(legacy),
        "mode": "open_loop",
        "cells": {},
        "safety": {},
    }
    before_paper = json.loads(json.dumps(legacy["paper"]))
    before_offsets = dict(legacy["joint_offsets_deg"])
    path.write_text(json.dumps(legacy), encoding="utf-8")

    _set_brush(argparse.Namespace(desk=path, total_cm=12.0, tuft_cm=4.0))
    migrated = load_desk(path)
    assert migrated["ready"] is True
    assert migrated["brush_total_cm"] == pytest.approx(12.0)
    assert migrated["brush_rigid_cm"] == pytest.approx(8.0)
    assert migrated["brush_tuft_cm"] == pytest.approx(4.0)
    assert migrated["paper"] == before_paper
    assert migrated["joint_offsets_deg"] == before_offsets
    assert migrated["pressure_calibration_v1"]["desk_fingerprint"] == desk_fingerprint(migrated)


def test_brush_geometry_change_invalidates_old_calibration(tmp_path: Path) -> None:
    path = tmp_path / "desk.json"
    shutil.copyfile(ROOT / "tests/fixtures/hardware-desk.json", path)
    desk = load_desk(path)
    desk["pressure_calibration_v1"] = {"desk_fingerprint": desk_fingerprint(desk)}
    path.write_text(json.dumps(desk), encoding="utf-8")

    _set_brush(argparse.Namespace(desk=path, total_cm=11.0, tuft_cm=4.0))
    changed = load_desk(path)
    assert changed["ready"] is False
    assert changed["pressure_calibration_v1"] is None


def test_brush_reentry_does_not_bless_stale_geometry_or_pressure(tmp_path: Path) -> None:
    from so101_calligraphy.hardware_desk import geometry_fingerprint
    path = tmp_path / "desk.json"
    shutil.copyfile(ROOT / "tests/fixtures/hardware-desk.json", path)
    desk = load_desk(path)
    desk["geometry_fingerprint"] = geometry_fingerprint(desk)
    desk["paper"]["surface_z"] += .01
    path.write_text(json.dumps(desk), encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(SystemExit, match="較正"):
        _set_brush(argparse.Namespace(desk=path, total_cm=12.0, tuft_cm=4.0))
    assert path.read_bytes() == before
    desk["geometry_fingerprint"] = geometry_fingerprint(desk)
    desk["pressure_calibration_v1"] = {"desk_fingerprint": "stale"}
    path.write_text(json.dumps(desk), encoding="utf-8")
    _set_brush(argparse.Namespace(desk=path, total_cm=12.0, tuft_cm=4.0))
    assert load_desk(path)["pressure_calibration_v1"] is None


def _leader_reference(tmp_path: Path, desk: dict) -> Path:
    surface = float(desk["paper"]["surface_z"])
    cells = {}
    for cell, write_lift_mm in ((0, 8.0), (1, 5.0)):
        key = "load:shoulder_lift"
        write_z = surface + write_lift_mm / 1000.0
        cells[str(cell)] = {
            "poses": {
                "hover": {"feedback_median": {key: 100.0}},
                "contact": {},
                "good": {},
            },
            "channel": key,
            "sign": 1,
            "contact_excess": 8.0,
            "good_excess": 25.0,
            "safety_excess": 30.0,
            "contact_tip_z_m": write_z + 0.002,
            "write_tip_z_m": write_z,
        }
    reference = {
        "schema": TAUGHT_SCHEMA,
        "desk_fingerprint": desk_fingerprint(desk),
        "motor_calibration_sha256": desk["motor_calibration_sha256"],
        "leader_to_follower_offset_qpos": [0.0, 0.0, 0.0, 0.0, np.deg2rad(100.0), 0.2],
        "cells": cells,
    }
    reference["reference_sha256"] = _canonical_sha256(reference)
    path = tmp_path / "leader-reference.json"
    path.write_text(json.dumps(reference, ensure_ascii=False), encoding="utf-8")
    return path


def test_pressure_profile_selects_monotonic_signal_and_falls_back() -> None:
    keys = [f"{kind}:{name}" for kind in ("load", "current") for name in JOINT_NAMES]
    data = {"lift_mm": np.asarray(PRESSURE_LIFTS_MM)}
    air = []
    lines = []
    for cell in range(2):
        air.extend({"cell": cell, **{key: 100.0 for key in keys}} for _ in range(3))
        for line in range(5):
            lines.extend(
                {
                    "cell": cell,
                    "line": line,
                    **{
                        key: 100.0 + (line + 1) * 10.0
                        if key == "load:shoulder_lift"
                        else 100.0
                        for key in keys
                    },
                }
                for _ in range(3)
            )
    profile = _pressure_profile_from_samples(data, air, lines, (1, 3))
    assert profile["cells"]["0"]["mode"] == "closed_loop"
    assert profile["cells"]["0"]["channel"] == "load:shoulder_lift"
    assert profile["cells"]["0"]["selected_line"] == 1

    flat = [{**row, **{key: 100.0 for key in keys}} for row in lines]
    fallback = _pressure_profile_from_samples(data, air, flat, (1, 3))
    assert fallback["cells"]["0"]["mode"] == "open_loop"
    assert fallback["cells"]["0"]["channel"] is None
    assert fallback["cells"]["0"]["fallback_lift_mm"] == PRESSURE_LIFTS_MM[1]


def test_clamp_qpos_keeps_commands_inside_follower_range(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    ranges = np.asarray(desk_joint_ranges(desk))
    qpos = ranges[:, 0] - 0.2
    clamped = _clamp_qpos(qpos, desk)
    assert np.all(clamped >= ranges[:, 0])
    assert np.all(clamped <= ranges[:, 1])


def test_bilateral_offset_keeps_the_startup_pair_stationary() -> None:
    leader = {f"{name}.pos": 3.0 for name in JOINT_NAMES}
    leader["wrist_roll.pos"] = 0.0
    follower = dict(leader)
    follower["wrist_roll.pos"] = -108.0
    offset = _action_offset(follower, leader)
    assert _add_action(leader, offset) == follower
    inverse = {key: -value for key, value in offset.items()}
    assert _add_action(follower, inverse) == leader
    moved = dict(leader)
    moved["wrist_roll.pos"] = 10.0
    assert _add_action(moved, offset)["wrist_roll.pos"] == pytest.approx(-98.0)
    dropped = _without_joint(leader)
    assert "wrist_roll.pos" not in dropped
    assert dropped["elbow_flex.pos"] == 3.0
    present = {"elbow_flex.pos": 10.0, "gripper.pos": 40.0}
    limited = _limit_step(
        {"elbow_flex.pos": 40.0, "gripper.pos": 90.0}, present
    )
    assert limited["elbow_flex.pos"] == pytest.approx(15.0)
    assert limited["gripper.pos"] == pytest.approx(45.0)


def test_leader_alignment_uses_stable_relative_zero_instead_of_raw_difference() -> None:
    follower = np.tile(np.asarray([0.1, -0.4, 0.6, 0.2, -1.8, -0.5]), (8, 1))
    raw_difference = np.asarray(
        [np.deg2rad(3.0), 0.0, 0.0, 0.0, np.deg2rad(100.0), 0.22]
    )
    leader = follower - raw_difference
    offset = _leader_alignment_offset(follower, leader)
    assert offset == pytest.approx(raw_difference)
    assert np.max(np.abs(leader[-1] + offset - follower[-1])) < np.deg2rad(0.01)

    moving = follower.copy()
    moving[-1, 0] += np.deg2rad(3.0)
    with pytest.raises(SystemExit, match="動いて"):
        _leader_alignment_offset(moving, leader)


def test_joint_interpolation_is_30hz_and_preserves_duration_and_endpoint() -> None:
    start = np.zeros(6)
    goal = np.full(6, np.deg2rad(5.0))
    sequence, period = _interpolate_joint_target(start, goal, 0.1875)
    assert len(sequence) == 6
    assert period == pytest.approx(0.03125)
    assert len(sequence) * period == pytest.approx(0.1875)
    assert sequence[-1] == pytest.approx(goal)
    assert np.max(np.abs(np.diff(np.vstack((start, sequence)), axis=0))) <= (
        np.deg2rad(5.0) / 6 + 1e-12
    )
    assert 1.0 / period >= COMMAND_HZ


def test_height_metadata_comes_from_measured_paper_plane(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    metadata = hardware_height_metadata(desk, write_lift_mm=8.0, clear_mm=20.0)
    surface_mm = float(desk["paper"]["surface_z"]) * 1000.0
    assert metadata["height_reference"] == "paper_table_fk_plane"
    assert metadata["paper_surface_z_mm"] == pytest.approx(surface_mm)
    assert metadata["write_height_above_paper_mm"] == pytest.approx(8.0)
    assert metadata["write_tip_z_mm"] == pytest.approx(surface_mm + 8.0)
    assert metadata["air_height_above_paper_mm"] == pytest.approx(28.0)
    assert metadata["air_tip_z_mm"] == pytest.approx(surface_mm + 28.0)
    assert metadata["safe_height_above_paper_mm"] == pytest.approx(30.8082697699)
    assert metadata["safe_tip_z_mm"] == pytest.approx(
        surface_mm + float(desk["safe_height_m"]) * 1000.0
    )
    assert metadata["brush_total_cm"] == pytest.approx(12.0)
    assert metadata["brush_rigid_cm"] == pytest.approx(8.0)
    assert metadata["brush_tuft_cm"] == pytest.approx(4.0)


def test_aborted_calibration_disconnects_with_torque_disabled() -> None:
    class Bus:
        is_connected = True

        def __init__(self) -> None:
            self.disabled = False
            self.disconnected = False

        def disable_torque(self, num_retry: int) -> None:
            assert num_retry == 3
            self.disabled = True

        def disconnect(self, disable_torque: bool) -> None:
            assert disable_torque is False
            self.disconnected = True

    class Robot:
        def __init__(self) -> None:
            self.bus = Bus()

    robot = Robot()
    _disconnect_limp(robot)
    assert robot.bus.disabled
    assert robot.bus.disconnected


def test_taught_reference_selects_monotonic_feedback_signal() -> None:
    def pose(qpos_deg: float, load: float, mad: float = 1.0) -> dict:
        return {
            "qpos": [np.deg2rad(qpos_deg), 0.0, 0.0, 0.0, 0.0, 0.0],
            "feedback_median": {"load:shoulder_lift": load},
            "feedback_mad": {"load:shoulder_lift": mad},
        }

    selected = _select_taught_signal(
        {"hover": pose(0.0, 100.0), "contact": pose(1.0, 108.0), "good": pose(2.0, 125.0)}
    )
    assert selected["channel"] == "load:shoulder_lift"
    assert selected["sign"] == 1
    assert selected["good_excess"] == pytest.approx(25.0)
    assert selected["safety_excess"] == pytest.approx(30.0)
    assert max(abs(v) for v in selected["pressure_direction_qpos"]) <= np.deg2rad(8.0)

    with pytest.raises(SystemExit, match="区別できる"):
        _select_taught_signal(
            {"hover": pose(0.0, 100.0), "contact": pose(1.0, 101.0), "good": pose(2.0, 102.0)}
        )


def test_taught_air_path_uses_cell_hover_delta_and_validates_motion(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    qpos = np.zeros((20, 6), dtype=np.float64)
    cells = np.r_[np.zeros(10, dtype=np.int8), np.ones(10, dtype=np.int8)]
    excess = np.zeros(20)
    excess[5] = 10.0
    excess[15] = 10.0
    reference = {
        "cells": {
            "0": {"pen_down_excess": 5.0, "air_delta_qpos": [0.01, 0, 0, 0, 0, 0]},
            "1": {"pen_down_excess": 5.0, "air_delta_qpos": [0.02, 0, 0, 0, 0, 0]},
        }
    }
    air = _make_taught_air_qpos(qpos, cells, excess, reference)
    assert air[5, 0] == pytest.approx(0.01)
    assert air[15, 0] == pytest.approx(0.02)
    _validate_taught_motion(qpos, air, desk)

    bad = qpos.copy()
    bad[1, 0] = np.deg2rad(6.0)
    with pytest.raises(SystemExit, match="5°"):
        _validate_taught_motion(bad, air, desk)


def test_taught_npz_accepts_only_three_words_and_matching_fingerprints(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    assert _validate_taught_word("文字") == "文字"
    with pytest.raises(SystemExit, match="3語"):
        _validate_taught_word("天地")

    reference_path = _leader_reference(tmp_path, desk)
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    path = tmp_path / "taught.npz"
    count = 10
    np.savez(
        path,
        taught_schema=TAUGHT_SCHEMA,
        qpos=np.zeros((count, 6)),
        air_qpos=np.zeros((count, 6)),
        pen_down=np.zeros(count, dtype=bool),
        cell_index=np.r_[np.zeros(5, dtype=np.int8), np.ones(5, dtype=np.int8)],
        target_excess=np.zeros(count),
        dt=1.0 / 30.0,
        kanji="文字",
        desk_fingerprint=desk_fingerprint(desk),
        motor_calibration_sha256=desk["motor_calibration_sha256"],
        reference_json=json.dumps(reference, ensure_ascii=False),
        reference_sha256=reference["reference_sha256"],
    )
    data = np.load(path, allow_pickle=True)
    assert _validate_taught_data(data, desk)["word"] == "文字"
    desk["paper"]["surface_z"] += 0.001
    with pytest.raises(SystemExit, match="desk"):
        _validate_taught_data(data, desk)


def test_sync_limits_requires_six_axes_and_invalidates_pressure(tmp_path: Path) -> None:
    desk_path = _synced_desk(tmp_path)
    desk = load_desk(desk_path)
    desk["pressure_calibration_v1"] = {"desk_fingerprint": desk_fingerprint(desk)}
    desk_path.write_text(json.dumps(desk), encoding="utf-8")

    calibration = json.loads(_calibration_source(tmp_path).read_text(encoding="utf-8"))
    calibration_path = tmp_path / "follower.json"
    calibration["gripper"]["range_max"] += 1
    calibration_path.write_text(json.dumps(calibration), encoding="utf-8")
    _sync_limits(
        argparse.Namespace(
            desk=desk_path,
            robot_calibration=calibration_path,
            usb_serial="test-follower",
            port="/dev/test-follower",
        )
    )
    assert load_desk(desk_path)["pressure_calibration_v1"] is None
    assert load_desk(desk_path)["ready"] is False
    stale = load_desk(desk_path)
    assert set(stale["stale_poses"]) == set((*REQUIRED_POSES, SIM_HOME_POSE))
    # Re-solving the old encoder readings must not silently re-enable motion.
    with pytest.raises(ValueError, match="再教示"):
        solve_desk(stale)
    _record_pose(stale, "upright", dict(stale["poses"]["upright"]))
    assert "upright" not in stale["stale_poses"]
    assert "paper_center_touch" in stale["stale_poses"]

    calibration.pop("gripper")
    calibration_path.write_text(json.dumps(calibration), encoding="utf-8")
    with pytest.raises(SystemExit, match="軸がありません"):
        _sync_limits(
            argparse.Namespace(
                desk=desk_path,
                robot_calibration=calibration_path,
                usb_serial="test-follower",
                port="/dev/test-follower",
            )
        )


def test_prepare_only_syncs_real_ranges_but_requires_usb_binding(tmp_path: Path) -> None:
    desk_path = tmp_path / "desk.json"
    shutil.copyfile(ROOT / "tests/fixtures/hardware-desk.json", desk_path)
    desk = load_desk(desk_path)
    desk["joint_ranges_rad"] = None
    desk["motor_calibration_sha256"] = None
    desk["follower_usb_serial"] = None
    desk["follower_port"] = None
    desk_path.write_text(json.dumps(desk), encoding="utf-8")
    _sync_limits(
        argparse.Namespace(
            desk=desk_path,
            robot_calibration=_calibration_source(tmp_path),
            usb_serial=None,
            port="/dev/not-connected",
            prepare_only=True,
        )
    )
    prepared = load_desk(desk_path)
    assert len(prepared["joint_ranges_rad"]) == 6
    assert prepared["motor_calibration_sha256"]
    assert prepared["follower_usb_serial"] is None
    with pytest.raises(SystemExit, match="USB識別が未確定"):
        _validate_follower_port("/dev/not-connected", prepared)


def test_recorded_suzuri_roundtrip_and_rejects_mismatch(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    path = tmp_path / "suzuri.npz"
    assert _load_recorded_suzuri(path, desk) is None
    qpos = np.linspace(0.0, 1.0, 12).reshape(2, 6)
    np.savez(path, qpos=qpos, dt=1.0 / 30.0, desk_fingerprint=desk_fingerprint(desk))
    loaded, dt = _load_recorded_suzuri(path, desk)
    assert loaded.shape == (2, 6)
    assert dt == pytest.approx(1.0 / 30.0)
    np.savez(path, qpos=np.zeros((1, 6)), dt=0.03, desk_fingerprint=desk_fingerprint(desk))
    with pytest.raises(SystemExit, match="壊れ"):
        _load_recorded_suzuri(path, desk)
    np.savez(path, qpos=qpos, dt=0.03, desk_fingerprint="other")
    with pytest.raises(SystemExit, match="desk"):
        _load_recorded_suzuri(path, desk)


def test_command_outside_follower_range_is_clipped(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))

    class Robot:
        def __init__(self) -> None:
            self.actions = []

        def send_action(self, action) -> None:
            self.actions.append(action)

    robot = Robot()
    safe = np.zeros(6)
    bad = safe.copy()
    bad[0] = desk["joint_ranges_rad"][0][1] + 0.1
    with pytest.raises(SystemExit, match="切り詰めず退避"):
        _safe_send_qpos(robot, desk, bad, safe)
    assert len(robot.actions) == 1


def test_camera_failure_retires_writing_to_hover(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    desk["pressure_calibration_v1"] = {"cells": {}, "safety": {}}

    class Robot:
        def __init__(self) -> None:
            self.actions = []

        def send_action(self, action) -> None:
            self.actions.append(action)

    class Camera:
        failure = {"reason": "visual_anomaly"}
        disarmed = False

        def disarm(self) -> None:
            self.disarmed = True

    robot = Robot()
    camera = Camera()
    qpos = np.zeros((1, 6), dtype=np.float64)
    data = {
        "dq_dz": np.zeros_like(qpos),
        "pen_down": np.zeros(1, dtype=bool),
        "cell_index": np.full(1, -1, dtype=np.int8),
        "target_pressure": np.zeros(1),
        "air_qpos": qpos.copy(),
        "nominal_lift_mm": np.asarray(8.0),
    }
    with pytest.raises(SystemExit, match="カメラ監視.*hover"):
        _send_writing(
            robot,
            desk,
            data,
            qpos,
            0.0,
            1,
            [],
            camera=camera,
            hover_qpos=np.zeros(6),
        )
    assert camera.disarmed
    assert len(robot.actions) == 1


def test_depth_profile_preserves_lower_cell_air_clearance_and_roof_lift() -> None:
    paper = PaperConfig(width=0.267, height=0.154, center_x=0.24, center_y=0.0, margin=0.015)
    far, near = glyph_cells(paper, 2)
    far_z, near_z = 0.008, -0.012
    targets = np.array([
        [far.center_x, 0.0, far_z],
        [near.center_x, 0.0, 0.060],
        [near.center_x, 0.0, 0.038],
        [near.center_x, 0.0, far_z + 0.008],
        [near.center_x, 0.0, far_z],
    ])
    out = _apply_depth_profile(
        targets, paper, far_z, near_z, air_z=0.060,
        pen_down=np.array([True, False, False, True, True]),
    )
    assert out[:, :2] == pytest.approx(targets[:, :2])
    assert out[:, 2] == pytest.approx([far_z, 0.060, 0.028, near_z + 0.008, near_z])
    assert targets[1, 2] == 0.060  # Input remains intact for auditing.


@pytest.mark.parametrize("word,cell", (("字", 0), ("春夏秋冬", 2), ("春夏秋冬", 3)))
def test_writing_logs_previous_command_tracking_and_keeps_rows_on_disconnect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, word: str, cell: int,
) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    qpos = np.array([np.zeros(6), np.full(6, 0.05), np.full(6, 0.06)])
    data = {
        "dq_dz": np.full_like(qpos, 100.0),
        "pen_down": np.ones(3, dtype=bool),
        "cell_index": np.full(3, cell, dtype=np.int8),
        "kanji": np.asarray(word),
        "target_pressure": np.full(3, 0.72),
        "air_qpos": np.zeros_like(qpos),
    }
    sent = []
    observations = iter([np.zeros(6), np.full(6, 0.01), OSError("disconnected")])

    def observe(*_args):
        value = next(observations)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr("scripts.hardware_write._present_qpos", observe)
    monkeypatch.setattr("scripts.hardware_write._read_feedback", lambda _robot: {})
    monkeypatch.setattr("scripts.hardware_write._send_smoothed_target", lambda _robot, _desk, _start, goal, *_args: sent.append(goal.copy()))

    class Robot:
        def send_action(self, _action):
            pass

    recorded = []
    with pytest.raises(OSError, match="disconnected"):
        _send_writing(Robot(), desk, data, qpos, 0.0, 1, [], recorded_rows=recorded)
    assert len(recorded) == 2
    # No large post-IK fallback correction, even with an exaggerated dq/dz.
    assert np.asarray(sent) == pytest.approx(qpos[:2])
    row = recorded[1]
    assert row["tracking_error_max_deg"] == pytest.approx(np.rad2deg(0.01))
    assert row["previous_command_deg:elbow_flex"] == 0.0
    assert row["command_deg:elbow_flex"] == pytest.approx(np.rad2deg(0.05))
    assert row["position_deg:elbow_flex"] == pytest.approx(np.rad2deg(0.01))


def test_trace_rejects_legacy_without_explicit_opt_in(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    path = tmp_path / "legacy.npz"
    np.savez(path, qpos=np.zeros((1, 6)), dt=0.1)
    data = np.load(path, allow_pickle=True)
    with pytest.raises(SystemExit, match="旧形式"):
        _validate_trace_data(data, desk, False)


def test_four_cell_pressure_mapping_keeps_thresholds_and_rejects_closed_loop(tmp_path: Path) -> None:
    from scripts.hardware_write import _grid_pressure_calibration
    desk = load_desk(_synced_desk(tmp_path))
    before = json.dumps(desk, sort_keys=True)
    calibration = _grid_pressure_calibration(desk, 4)
    assert calibration['cells']['2'] == desk['pressure_calibration_v1']['cells']['0']
    assert calibration['cells']['3'] == desk['pressure_calibration_v1']['cells']['1']
    assert json.dumps(desk, sort_keys=True) == before
    desk['pressure_calibration_v1']['cells']['0']['mode'] = 'closed_loop'
    with pytest.raises(SystemExit, match='閉ループ'):
        _grid_pressure_calibration(desk, 4)


def test_layout_search_does_not_retry_calibration_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    def fail(_args, scale):
        calls.append(scale)
        raise SystemExit('較正が古い')
    monkeypatch.setattr('scripts.hardware_write._trace_candidate', fail)
    with pytest.raises(SystemExit, match='較正が古い'):
        _trace(argparse.Namespace())
    assert calls == [1.0]


def test_modern_trace_requires_matching_pressure_fingerprint(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    path = tmp_path / "modern.npz"
    count = 2
    height = hardware_height_metadata(
        desk, write_lift_mm=8.0, clear_mm=DEFAULT_AIR_HEIGHT_MM - 8.0
    )
    write_z = float(desk["paper"]["surface_z"]) + 0.008
    standby_tip = np.asarray(
        [
            desk["paper"]["center_x"],
            desk["paper"]["center_y"],
            desk["paper"]["surface_z"] + DEFAULT_STANDBY_HEIGHT_MM / 1000.0,
        ]
    )
    np.savez(
        path,
        trace_schema=TRACE_SCHEMA,
        desk_fingerprint=desk_fingerprint(desk),
        motor_calibration_sha256=desk["motor_calibration_sha256"],
        qpos=np.zeros((count, 6)),
        air_qpos=np.zeros((count, 6)),
        dq_dz=np.zeros((count, 6)),
        pen_down=np.asarray([True, False]),
        cell_index=np.zeros(count, dtype=np.int8),
        target_pressure=np.zeros(count),
        expected_tip_xyz=np.asarray([[desk['paper']['center_x'], desk['paper']['center_y'], write_z], [desk['paper']['center_x'], desk['paper']['center_y'], height["air_tip_z_m"]]]),
        standby_qpos=np.zeros(6),
        standby_tip_xyz=standby_tip,
        standby_height_above_paper_mm=DEFAULT_STANDBY_HEIGHT_MM,
        cell_write_tip_z_m=np.asarray([write_z]),
        command_hz=COMMAND_HZ,
        dt=0.1,
        kanji="字",
        nominal_lift_mm=8.0,
        reference_json="",
        reference_sha256="",
        pressure_calibration_sha256=_canonical_sha256({"desk_fingerprint": desk_fingerprint(desk)}),
        **{key: value for key, value in height.items() if key != "height_reference"},
        height_metadata_json=json.dumps(height, ensure_ascii=False),
    )
    data = np.load(path, allow_pickle=True)
    desk["pressure_calibration_v1"] = {"desk_fingerprint": desk_fingerprint(desk)}
    assert _validate_trace_data(data, desk, False) is True
    desk["pressure_calibration_v1"]["extra_depth_mm"] = 1.0
    with pytest.raises(SystemExit, match="軌道と筆圧較正"):
        _validate_trace_data(data, desk, False)
    desk["paper"]["surface_z"] += 0.001
    with pytest.raises(SystemExit, match="desk較正"):
        _validate_trace_data(data, desk, False)


def test_trace_rejects_unregistered_kanji_before_ik(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(character: str, cache_dir="data/kanjivg"):
        raise RuntimeError("missing")

    monkeypatch.setattr(
        "so101_calligraphy.trajectory.kanjivg.fetch_kanjivg", boom
    )
    with pytest.raises(SystemExit, match="KanjiVGにありません"):
        _trace(
            argparse.Namespace(
                desk=tmp_path / "unused.json",
                kanji="字",
                out=tmp_path / "out.npz",
                reference=tmp_path / "missing.json",
                kanjivg_cache=tmp_path,
                lift_mm=8.0,
                clear_mm=32.0,
                step_mm=3.0,
                speed_mm_s=16.0,
                tolerance_mm=1.0,
            )
        )




@pytest.mark.parametrize("kanji", ("文字", "学習", "菅原", "春夏秋", "春夏秋冬", "永"))
def test_target_words_stay_inside_margin_and_reach_with_smooth_ik(
    tmp_path: Path, kanji: str
) -> None:
    desk_path = _synced_desk(tmp_path)
    desk = load_desk(desk_path)
    out = tmp_path / f"{kanji}.npz"
    _trace(
        argparse.Namespace(
            desk=desk_path,
            kanji=kanji,
            out=out,
            reference=tmp_path / "missing-reference.json",
            kanjivg_cache=ROOT / "data/kanjivg",
            lift_mm=8.0,
            clear_mm=32.0,
            step_mm=3.0,
            speed_mm_s=16.0,
            tolerance_mm=1.0,
        )
    )
    data = np.load(out, allow_pickle=True)
    assert _validate_trace_data(data, desk, False) is True
    assert int(data["trace_schema"]) == TRACE_SCHEMA
    if len(kanji) == 4:
        original = {key: np.asarray(data[key]).copy() for key in data.files}
        invalid = dict(original)
        invalid['cell_index'] = original['cell_index'].astype(np.int64)
        invalid['cell_index'][0] = 256
        with pytest.raises(SystemExit, match='セル番号'):
            _validate_trace_data(invalid, desk, False)
        invalid = dict(original)
        invalid['expected_tip_xyz'] = original['expected_tip_xyz'].copy()
        first = np.flatnonzero(original['pen_down'])[0]
        invalid['expected_tip_xyz'][first, 1] += 0.1
        with pytest.raises(SystemExit, match='枡の外'):
            _validate_trace_data(invalid, desk, False)
    assert data["qpos"].shape == data["air_qpos"].shape == data["dq_dz"].shape
    assert str(data["desk_fingerprint"].item()) == desk_fingerprint(desk)
    assert float(data["paper_surface_z_m"]) == pytest.approx(desk["paper"]["surface_z"])
    assert float(data["write_height_above_paper_mm"]) == pytest.approx(8.0)
    assert float(data["write_tip_z_m"]) == pytest.approx(desk["paper"]["surface_z"] + 0.008)
    cell_write = np.asarray(data["cell_write_tip_z_m"])
    assert len(cell_write) == len(kanji)
    if len(kanji) >= 2:
        assert cell_write[0] - cell_write[1] == pytest.approx(
            DEFAULT_LOWER_CELL_EXTRA_PRESS_MM / 1000.0
        )
    assert float(data["air_height_above_paper_mm"]) == pytest.approx(DEFAULT_AIR_HEIGHT_MM)
    assert float(data["standby_height_above_paper_mm"]) == pytest.approx(
        DEFAULT_STANDBY_HEIGHT_MM
    )
    assert float(data["command_hz"]) == pytest.approx(COMMAND_HZ)
    assert float(data["safe_height_above_paper_mm"]) == pytest.approx(desk["safe_height_m"] * 1000.0)
    brush = json.loads(str(data["height_metadata_json"].item()))
    assert brush["brush_total_cm"] == pytest.approx(12.0)
    assert brush["brush_rigid_cm"] == pytest.approx(8.0)
    assert brush["brush_tuft_cm"] == pytest.approx(4.0)
    paper = desk["paper"]
    down = np.asarray(data["pen_down"], dtype=bool)
    targets = np.asarray(data["expected_tip_xyz"])[down]
    down_cells = np.asarray(data["cell_index"])[down]
    far_z = float(np.asarray(data["cell_write_tip_z_m"])[0])
    extra = DEFAULT_LOWER_CELL_EXTRA_PRESS_MM / 1000.0
    ceiling = DEFAULT_U_KANMURI_LIFT_MM / 1000.0
    for cell in range(len(np.asarray(data["cell_write_tip_z_m"]))):
        cell_z = targets[down_cells == cell, 2]
        assert cell_z.min() >= far_z - extra - 1e-6
        assert cell_z.max() <= far_z + ceiling + 1e-6
    assert targets[:, 0].min() >= paper["center_x"] - paper["width"] / 2 + paper["margin"]
    assert targets[:, 0].max() <= paper["center_x"] + paper["width"] / 2 - paper["margin"]
    assert targets[:, 1].min() >= paper["center_y"] - paper["height"] / 2 + paper["margin"]
    assert targets[:, 1].max() <= paper["center_y"] + paper["height"] / 2 - paper["margin"]
    assert data["expected_tip_xyz"][-1, 2] == pytest.approx(
        paper["surface_z"] + DEFAULT_AIR_HEIGHT_MM / 1000.0
    )
    preview = json.loads(out.with_suffix('.layout.json').read_text())
    assert len(preview['cells']) == len(kanji)
    assert out.with_suffix('.layout.svg').is_file()
    for cell, box in enumerate(glyph_cells(env_config_from_desk(desk).paper, len(kanji))):
        cell_targets = targets[down_cells == cell, :2]
        centre = np.asarray([box.center_x, box.center_y])
        assert np.all(np.abs(cell_targets-centre) <= box.width / 2 + 1e-6)
        # Preserve natural aspect ratio while filling the long side, with 2 mm ink room.
        assert 0.8 <= float(data['glyph_scale']) <= 1.0
        assert np.max(np.ptp(cell_targets, axis=0)) >= box.width * float(data['glyph_scale']) - 0.0041

    env = CalligraphyEnv(task="line", config=env_config_from_desk(desk))
    try:
        env.reset(seed=0, options={"layout_index": 0})
        errors = []
        tilts = []
        for qpos, target in zip(data["qpos"], data["expected_tip_xyz"]):
            tip, axis = _tip_and_axis(env, qpos)
            errors.append(np.linalg.norm(tip - target))
            tilts.append(np.degrees(np.arccos(np.clip(-axis[2], -1.0, 1.0))))
        assert max(errors) <= 0.001
        assert max(tilts) <= 8.0
        assert np.degrees(np.max(np.abs(np.diff(data["qpos"], axis=0)))) <= 5.1
        limits = np.asarray(desk_joint_ranges(desk))
        assert np.all(data["qpos"] >= limits[:, 0] + np.deg2rad(2.0) - 1e-9)
        assert np.all(data["qpos"] <= limits[:, 1] - np.deg2rad(2.0) + 1e-9)
        standby_tip, standby_axis = _tip_and_axis(env, data["standby_qpos"])
        assert standby_tip == pytest.approx(data["standby_tip_xyz"], abs=0.001)
        assert np.degrees(np.arccos(np.clip(-standby_axis[2], -1.0, 1.0))) <= 8.0
    finally:
        env.close()

    from scripts.audit_hardware_trace import audit_trace

    audit, _ = audit_trace(out, desk)
    assert audit["passed"] is True
    assert audit["physical_writing_verified"] is False
    if kanji == "文字":
        # Simulate a post-IK joint edit with unchanged saved targets/errors.
        # The independent audit must recompute FK from the actual commands.
        corrupted = {key: np.asarray(data[key]).copy() for key in data.files}
        corrupted["qpos"][:, 0] += np.deg2rad(2.0)
        bad = tmp_path / "post-ik-edit.npz"
        np.savez_compressed(bad, **corrupted)
        rejected, _ = audit_trace(bad, desk)
        assert rejected["passed"] is False
        assert rejected["gates"]["position_within_1mm"] is False


def test_suzuri_dips_two_trips() -> None:
    pool = np.zeros(6)
    near = np.ones(6)
    legs = list(_suzuri_dips(pool, near, 0.1, 1.0))
    assert len(legs) == 8
    assert legs[0][0] == "浮かす 1/2"
    assert legs[-1][0] == "手前へ引く 2/2"


def test_suzuri_pull_distance_keeps_taught_id6(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    offsets = playback_offsets(desk)
    gripper_map = desk_gripper_map(desk)
    pool = desk["poses"]["suzuri_pool"]
    env = CalligraphyEnv(task="line", config=env_config_from_desk(desk))
    try:
        env.reset(seed=0, options={"layout_index": 0})
        pulled = fit_suzuri_pull(env, pool, offsets, gripper_map)
        assert pulled["gripper"] == pytest.approx(pool["gripper"])
        assert pulled["wrist_roll"] == pytest.approx(pool["wrist_roll"])
        start, _ = _tip_and_axis(
            env,
            lerobot_to_qpos(pool, tilt_sign=1, offsets=offsets, gripper_map=gripper_map),
        )
        end, _ = _tip_and_axis(
            env,
            lerobot_to_qpos(pulled, tilt_sign=1, offsets=offsets, gripper_map=gripper_map),
        )
        delta = end - start
        assert delta[0] == pytest.approx(-SUZURI_PULL_M, abs=0.005)
        assert abs(delta[2]) < 0.006
    finally:
        env.close()


def test_naive_id5_roll_leaves_suzuri_ik_holds_tip(tmp_path: Path) -> None:
    desk = load_desk(_synced_desk(tmp_path))
    _pool, near = _suzuri_contact_qpos(desk)
    env = CalligraphyEnv(task="line", config=env_config_from_desk(desk))
    try:
        env.reset(seed=0, options={"layout_index": 0})
        tip, _ = _tip_and_axis(env, near)
        naive = near.copy()
        naive[JOINT_NAMES.index("wrist_roll")] += np.deg2rad(90)
        naive_tip, _ = _tip_and_axis(env, naive)
        assert np.linalg.norm((naive_tip - tip)[:2]) > 0.10
        rolled = _retarget_wrist_roll(env, near, np.deg2rad(90), env._joint_limits)
        got, _ = _tip_and_axis(env, rolled)
        assert np.linalg.norm(got - tip) < 0.002
    finally:
        env.close()
    path = tmp_path / "groom.npz"
    _write_suzuri_groom(desk, path, clear_mm=45.0)
    data = np.load(path)
    drop = {
        label: b
        for label, a, b, _ in _suzuri_groom(
            near,
            near,
            data["rolled_pool"],
            data["rolled_near"],
            data["rolled_near_clear"],
            0.1,
            1.0,
        )
    }["整える:同じ場所へ"]
    assert drop == pytest.approx(data["rolled_near"])
    assert not np.allclose(drop, naive)


def test_resolve_play_path_uses_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "trace.npz"
    np.savez(path, kanji=np.asarray("学習"))
    assert _resolve_play_path(str(path), tmp_dir=tmp_path / "tmp", run_dir=tmp_path / "runs") == path


def test_resolve_play_path_picks_latest_matching_npz(tmp_path: Path) -> None:
    tmp = tmp_path / "tmp"
    runs = tmp_path / "runs"
    tmp.mkdir()
    stale = tmp / "stale.npz"
    latest = tmp / "moji.npz"
    other = tmp / "other.npz"
    np.savez(stale, kanji=np.asarray("文字"))
    np.savez(other, kanji=np.asarray("菅原"))
    np.savez(latest, kanji=np.asarray("文字"))
    os.utime(stale, (1_000_000, 1_000_000))
    os.utime(latest, (2_000_000, 2_000_000))
    assert _resolve_play_path("文字", tmp_dir=tmp, run_dir=runs) == latest


def test_resolve_play_path_from_run_dir(tmp_path: Path) -> None:
    tmp = tmp_path / "tmp"
    run = tmp_path / "runs" / "20260902-000000"
    tmp.mkdir()
    run.mkdir(parents=True)
    path = run / "trace-文字.npz"
    np.savez(path, kanji=np.asarray("文字"))
    assert _resolve_play_path("文字", tmp_dir=tmp, run_dir=tmp_path / "runs") == path


def test_resolve_play_path_missing(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="traceがありません"):
        _resolve_play_path("文字", tmp_dir=tmp_path, run_dir=tmp_path / "runs")
