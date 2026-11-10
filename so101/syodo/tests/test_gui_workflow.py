"""Measured-paper checks and real MuJoCo paths, without a connected robot."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pytest

from scripts import gui_workflow as workflow
from scripts import hardware_write as hw
from so101_calligraphy.hardware_desk import (desk_fingerprint, geometry_fingerprint,
    glyph_cells, load_desk, require_ready, validate_measured_paper, write_z_along_depth)

ROOT = Path(__file__).resolve().parents[1]


def ruler_desk():
    return {"paper_measurement_v1": {"depth_mm": 200., "width_mm": 150.}, "tips_m": {
        "paper_near_left": [.1, -.075, .01], "paper_near_right": [.1, .075, .01],
        "paper_far_left": [.3, -.075, .01], "paper_far_right": [.3, .075, .01],
        "paper_center_touch": [.2, 0, .01],
    }}


def test_independent_ruler_measurement_accepts_rectangle():
    report = validate_measured_paper(ruler_desk())
    assert report["ruler_error_max_mm"] < 1e-10
    assert report["centre_error_mm"] < 1e-10


@pytest.mark.parametrize("kind", ["skew", "reversed", "bad_length", "centre"])
def test_paper_rejects_incorrect_order_dimensions_and_skew(kind):
    desk = ruler_desk()
    if kind == "skew":
        desk["tips_m"]["paper_far_left"][1] += .02
    elif kind == "reversed":
        desk["tips_m"]["paper_far_left"][0] = .05
    elif kind == "bad_length":
        desk["paper_measurement_v1"]["width_mm"] = 170
    else:
        desk["tips_m"]["paper_center_touch"][1] = .01
    with pytest.raises(ValueError):
        validate_measured_paper(desk)


def test_old_four_character_fixture_is_not_independently_verified_paper():
    desk = load_desk(ROOT / "tests/fixtures/hardware-desk.json")
    cells = glyph_cells(workflow.env_config_from_desk(desk).paper, 4)
    assert cells[0].width * 1000 == pytest.approx(61.952, abs=.01)
    desk["paper_measurement_v1"] = {"depth_mm": 267, "width_mm": 154}
    with pytest.raises(ValueError, match="揃っていません"):
        validate_measured_paper(desk)


@pytest.fixture(scope="module")
def measured_trace(tmp_path_factory):
    path = tmp_path_factory.mktemp("gui-native-kinematics")
    desk = load_desk(ROOT / "tests/fixtures/hardware-desk.json")
    desk["pressure_calibration_v1"] = {"desk_fingerprint": desk_fingerprint(desk),
        "source": "synthetic_for_offline_test", "mode": "open_loop", "cells": {
            str(i): {"mode": "open_loop", "channel": None, "fallback_lift_mm": lift, "safety": {}}
            for i, lift in enumerate((4., 1.))}, "safety": {}}
    (path / "desk.json").write_text(json.dumps(desk))
    args = argparse.Namespace(kanji="一", desk=path / "desk.json", out=path / "trace.npz",
        kanjivg_cache=ROOT / "data/kanjivg", reference=path / "absent-reference.json",
        glyph_mm=100., calibrated_heights=True, lift_mm=4., air_mm=30., standby_mm=30.,
        step_mm=3., speed_mm_s=16., tolerance_mm=1.)
    hw._trace(args)
    with np.load(args.out) as trace:
        seed = trace["qpos"][0].tolist()
    (path / "snapshot.json").write_text(json.dumps({"qpos": seed,
        "desk_sha256": workflow.sha(args.desk), "host_monotonic_s": time.monotonic(),
        "source": "synthetic_offline_snapshot"}))
    (path / "settings.json").write_text(json.dumps({"ink_mode": "manual", "travel_mm": 30., "speed": .8}))
    workflow.plan(argparse.Namespace(desk=args.desk, settings=path / "settings.json",
        snapshot=path / "snapshot.json", trace=args.out, out=path / "motion.npz"))
    return path, desk, args


def test_single_character_uses_measured_pressure_not_fixed_twenty_mm(measured_trace):
    path, desk, args = measured_trace
    with np.load(args.out) as data:
        assert hw._validate_trace_data(data, desk, False)
        down = data["pen_down"].astype(bool)
        points = data["expected_tip_xyz"][down]
        frames = glyph_cells(workflow.env_config_from_desk(desk).paper, 2)
        expected = write_z_along_depth(points[:,0], frames[0].center_x, frames[1].center_x,
            desk["paper"]["surface_z"] + .004, desk["paper"]["surface_z"] + .001)
        assert np.allclose(points[:,2], expected, atol=1e-10)
        assert np.min(points[:,2]) >= desk["paper"]["surface_z"] + .001 - 1e-8
        assert data["requested_glyph_mm"].item() == 100
        assert data["glyph_scale"].item() == 1


def test_native_fk_audit_and_all_transfers_pass_and_dry_path_is_separate(measured_trace):
    from scripts.audit_hardware_trace import audit_trace
    path, desk, args = measured_trace
    result, _ = audit_trace(args.out, desk)
    assert result["passed"]
    assert result["metrics"]["fk_error_max_mm"] < 1
    with np.load(path / "motion.npz") as motion:
        for name in ("before_qpos", "write_qpos", "after_qpos", "dry_before_qpos", "dry_write_qpos", "dry_after_qpos"):
            q = motion[name]
            assert len(q) > 0
            assert np.max(np.abs(np.diff(q, axis=0))) <= np.deg2rad(1) + 1e-7
        assert not np.array_equal(motion["write_qpos"], motion["dry_write_qpos"])
    report = json.loads((path / "motion.json").read_text())
    assert report["physical_writing_verified"] is False


def test_requested_size_is_rejected_instead_of_silently_shrunk(measured_trace):
    path, _, args = measured_trace
    args = deepcopy(args)
    args.kanji = "一一"
    args.glyph_mm = 140
    args.out = path / "must-not-be-created.npz"
    with pytest.raises(SystemExit, match="入りません"):
        hw._trace(args)
    assert not args.out.exists()


def test_native_validation_cannot_bless_ready_boolean_alone(tmp_path):
    desk = tmp_path / "desk.json"
    desk.write_text(json.dumps({"ready": True}))
    out = tmp_path / "validation.json"
    workflow.validate(argparse.Namespace(desk=desk, out=out))
    report = json.loads(out.read_text())
    assert not report["geometry_ok"]
    assert not report["pressure_ok"]
    assert report["errors"]


def test_snapshot_does_not_send_goals_or_toggle_torque(tmp_path, monkeypatch):
    desk = ROOT / "tests/fixtures/hardware-desk.json"
    positions = load_desk(desk)["poses"]["hover_center"]
    calls = []
    class Bus:
        is_connected = False
        def connect(self): self.is_connected = True; calls.append("connect")
        def sync_read(self, name, **kwargs): calls.append(name); return positions
        def disconnect(self, **kwargs): calls.append(kwargs); self.is_connected = False
    class Robot: bus = Bus()
    monkeypatch.setattr(workflow, "robot_config", lambda port: Robot())
    monkeypatch.setattr(hw, "_validate_follower_port", lambda *args: None)
    out = tmp_path / "snapshot.json"
    workflow.snapshot(argparse.Namespace(desk=desk, port="mock", out=out))
    assert calls == ["connect", "Present_Position", {"disable_torque": False}]
    assert json.loads(out.read_text())["motor_commands_sent"] is False
