#!/usr/bin/env python3
"""Audit final hardware commands by FK without connecting to the robot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.hardware_desk import (
    DEFAULT_DESK_PATH, _tip_and_axis, desk_fingerprint, env_config_from_desk,
    load_desk, require_joint_ranges, require_ready,
)


def _forward(env, qpos):
    positions, tilts = [], []
    for q in np.atleast_2d(qpos):
        tip, axis = _tip_and_axis(env, q)
        positions.append(tip.copy())
        tilts.append(float(np.rad2deg(np.arccos(np.clip(-axis[2], -1.0, 1.0)))))
    return np.asarray(positions), np.asarray(tilts)


def audit_trace(path: Path, desk: dict) -> tuple[dict, dict[str, np.ndarray]]:
    """Inspect the stored qpos, including any post-IK edits. Never fit a new path."""
    require_ready(desk)
    limits = np.asarray(require_joint_ranges(desk))
    with np.load(path, allow_pickle=False) as data:
        arrays = {name: np.asarray(data[name]) for name in (
            "qpos", "air_qpos", "expected_tip_xyz", "pen_down", "standby_qpos", "standby_tip_xyz",
        )}
        if str(data["desk_fingerprint"].item()) != desk_fingerprint(desk):
            raise ValueError("Trace and desk fingerprint differ")
        word = str(data["kanji"].item())
        schema = int(data["trace_schema"].item())
        air_mm = float(data["air_height_above_paper_mm"].item())
    count = len(arrays["qpos"])
    shapes = {
        "qpos": (count, 6), "air_qpos": (count, 6), "expected_tip_xyz": (count, 3),
        "pen_down": (count,), "standby_qpos": (6,), "standby_tip_xyz": (3,),
    }
    if count == 0 or any(value.shape != shapes[key] or not np.isfinite(value).all() for key, value in arrays.items()):
        raise ValueError("Trace has empty, malformed or non-finite arrays")
    env = CalligraphyEnv("line", config=env_config_from_desk(desk))
    try:
        env.reset(seed=0, options={"layout_index": 0})
        actual, tilt = _forward(env, arrays["qpos"])
        air_actual, air_tilt = _forward(env, arrays["air_qpos"])
        standby, standby_tilt = _forward(env, arrays["standby_qpos"])
    finally:
        env.close()
    target = arrays["expected_tip_xyz"]
    down = arrays["pen_down"].astype(bool)
    surface = float(desk["paper"]["surface_z"])
    expected_air = target.copy()
    expected_air[:, 2] = surface + air_mm / 1000
    errors = np.linalg.norm(actual - target, axis=1) * 1000
    air_error = np.linalg.norm(air_actual - expected_air, axis=1) * 1000
    xy_error = np.linalg.norm(actual[:, :2] - target[:, :2], axis=1) * 1000
    transfer = (~down) & np.r_[False, np.linalg.norm(np.diff(target[:, :2], axis=0), axis=1) > 1e-9]
    clearance = (actual[:, 2] - surface) * 1000
    all_q = np.vstack((arrays["qpos"], arrays["air_qpos"], arrays["standby_qpos"]))
    margin = float(np.rad2deg(np.min(np.minimum(all_q - limits[:, 0], limits[:, 1] - all_q))))
    step = max(float(np.rad2deg(np.abs(np.diff(arrays[name], axis=0))).max()) if count > 1 else 0.0 for name in ("qpos", "air_qpos"))
    metrics = {
        "fk_error_max_mm": float(errors.max()), "fk_error_p90_mm": float(np.percentile(errors, 90)),
        "write_fk_error_max_mm": float(errors[down].max()) if down.any() else None,
        "write_xy_error_max_mm": float(xy_error[down].max()) if down.any() else None,
        "tilt_max_deg": float(max(tilt.max(), air_tilt.max(), standby_tilt.max())),
        "joint_step_max_deg": step, "joint_margin_min_deg": margin,
        "air_fk_error_max_mm": float(air_error.max()),
        "transfer_clearance_min_mm": float(clearance[transfer].min()) if transfer.any() else None,
        "last_clearance_mm": float(clearance[-1]),
        "standby_error_mm": float(np.linalg.norm(standby[0] - arrays["standby_tip_xyz"]) * 1000),
    }
    gates = {
        "position_within_1mm": metrics["fk_error_max_mm"] <= 1.0,
        "upright_within_8deg": metrics["tilt_max_deg"] <= 8.0,
        "step_within_5deg": step <= 5.0 + 1e-6,
        "joint_margin_2deg": margin >= 2.0 - 1e-6,
        "air_position_within_1mm": metrics["air_fk_error_max_mm"] <= 1.0,
        "transfer_clearance_as_recorded": not transfer.any() or bool(np.all(np.abs(clearance[transfer] - air_mm) <= 1.0)),
        "final_lift_as_recorded": abs(metrics["last_clearance_mm"] - air_mm) <= 1.0,
        "standby_position_within_1mm": metrics["standby_error_mm"] <= 1.0,
    }
    result = {
        "word": word, "trace": str(path.resolve()), "trace_schema": schema,
        "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "desk_fingerprint": desk_fingerprint(desk), "count": count, "pen_down_count": int(down.sum()),
        "measurement_kind": "forward_kinematics_of_commanded_positions",
        "physical_writing_verified": False, "metrics": metrics, "gates": gates,
        "passed": all(gates.values()),
    }
    return result, {"expected": target, "actual": actual, "down": down, "error_mm": errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--desk", type=Path, default=DEFAULT_DESK_PATH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        desk = require_ready(load_desk(args.desk))
        results = [audit_trace(path, desk)[0] for path in args.traces]
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"results": results, "passed": all(r["passed"] for r in results)}, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for result in results:
        print(f"{result['word']}: {'PASS' if result['passed'] else 'FAIL'} {result['metrics']}")
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
