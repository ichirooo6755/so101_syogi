#!/usr/bin/env python3
"""Measured GUI workflow: native validation, read-only snapshot, audited transfers.

Imports MuJoCo only for offline validation/planning. The hardware commands use
the LeRobot Python and execute saved samples without generating new trajectories.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
import numpy as np
from so101_calligraphy.hardware_desk import (
    JOINT_NAMES, ROBOT_ID, _tip_and_axis, desk_fingerprint, desk_gripper_map,
    env_config_from_desk, lerobot_to_qpos, load_desk, playback_offsets,
    require_joint_ranges, require_ready, solve_tip_ik, validate_measured_paper,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def validate(args):
    report = {"desk_sha256": sha(args.desk), "geometry_ok": False, "pressure_ok": False,
              "errors": [], "physical_writing_verified": False}
    try:
        desk = require_ready(load_desk(args.desk))
        require_joint_ranges(desk)
        report["paper"] = validate_measured_paper(desk)
        if not desk.get("follower_usb_serial") or not desk.get("motor_calibration_sha256"):
            raise ValueError("現在のサーボ較正とUSB識別の同期が必要です")
        report["geometry_ok"] = True
        from scripts.hardware_write import _grid_pressure_calibration
        cal = desk.get("pressure_calibration_v1")
        if isinstance(cal, dict) and cal.get("desk_fingerprint") == desk_fingerprint(desk):
            profile = _grid_pressure_calibration(desk, 2)
            for index in ("0", "1"):
                lift = float(profile["cells"][index]["fallback_lift_mm"])
                if not np.isfinite(lift) or not 0 <= lift <= 15:
                    raise ValueError("筆圧の実測高さが不正です")
            report["pressure_ok"] = True
        else:
            report["errors"].append("現在の筆・紙に対応する筆圧較正が必要です")
    except (SystemExit, ValueError, TypeError, KeyError) as exc:
        report["errors"].append(str(exc))
    write_json(args.out, report)
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0  # Report describes incomplete setup; transport itself succeeded.


def robot_config(port):
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
    return SO101Follower(SO101FollowerConfig(port=port, id=ROBOT_ID,
        max_relative_target=None, disable_torque_on_disconnect=False))


def snapshot(args):
    from scripts.hardware_write import _validate_follower_port
    desk = require_ready(load_desk(args.desk))
    require_joint_ranges(desk)
    _validate_follower_port(args.port, desk)
    robot = robot_config(args.port)
    # Opening the bus does not call robot.connect/configure, enable torque or
    # send a goal. Preserve the exact torque state while reading encoders.
    try:
        robot.bus.connect()
        joints = {k: float(v) for k, v in robot.bus.sync_read("Present_Position", num_retry=3).items()}
        q = lerobot_to_qpos(joints, tilt_sign=desk["tilt_sign"], offsets=playback_offsets(desk), gripper_map=desk_gripper_map(desk))
        if q.shape != (6,) or not np.isfinite(q).all():
            raise ValueError("アームの位置を読み取れません")
        write_json(args.out, {"qpos": q.tolist(), "joints": joints,
            "desk_sha256": sha(args.desk), "host_monotonic_s": time.monotonic(),
            "motor_commands_sent": False})
    finally:
        if robot.bus.is_connected:
            robot.bus.disconnect(disable_torque=False)
    print("現在位置を読み取りました。目標位置・トルク設定は変更していません。")


class Planner:
    def __init__(self, desk, seed):
        from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
        self.desk = desk
        self.env = CalligraphyEnv("line", config=env_config_from_desk(desk))
        self.env.reset(seed=0, options={"layout_index": 0})
        self.limits = np.asarray(require_joint_ranges(desk))
        self.q = np.asarray(seed, dtype=float)
        self.points = []
        self.phases = []
        self.worst_error_mm = 0.0
        self.check(self.q)

    def check(self, q, target=None):
        if q.shape != (6,) or not np.isfinite(q).all():
            raise ValueError("移動経路に不正な関節値があります")
        if np.any(q < self.limits[:, 0] + np.deg2rad(2)) or np.any(q > self.limits[:, 1] - np.deg2rad(2)):
            raise ValueError("移動経路が関節端の2°以内に入ります。アームを手で安全な姿勢に置き直してください")
        tip, axis = _tip_and_axis(self.env, q)
        if np.degrees(np.arccos(np.clip(-axis[2], -1, 1))) > 8:
            raise ValueError("移動経路で筆が8°より傾きます。手首を曲げて筆を垂直にしてから位置を読み直してください")
        if target is not None:
            error = float(np.linalg.norm(tip - target) * 1000)
            self.worst_error_mm = max(self.worst_error_mm, error)
            if error > 1:
                raise ValueError(f"移動経路が届きません（誤差{error:.1f} mm）。硯・紙・待機位置を近づけて教示し直してください")
        return tip.copy()

    @property
    def tip(self):
        return self.check(self.q)

    def append(self, q, phase, target=None):
        self.check(q, target)
        if self.points and np.max(np.abs(q - self.points[-1])) > np.deg2rad(1) + 1e-7:
            raise ValueError("移動経路の関節変化が大きすぎます")
        self.points.append(q.copy())
        self.phases.append(phase)
        self.q = q.copy()

    def line(self, goal, phase, speed_mm_s=10):
        start = self.tip
        goal = np.asarray(goal, dtype=float)
        segments = max(1, int(np.ceil(np.linalg.norm(goal - start) / .002)))
        for alpha in np.linspace(0, 1, segments + 1)[1:]:
            target = start + alpha * (goal - start)
            q = solve_tip_ik(self.env, target, self.q, self.limits,
                limit_margin_rad=np.deg2rad(2), max_step_rad=np.deg2rad(5), continuity_weight=.002)
            self.check(q, target)
            previous = self.q.copy()
            previous_tip = self.tip
            seconds = max(np.linalg.norm(target - previous_tip) * 1000 / speed_mm_s,
                          float(np.max(np.abs(q - previous))) / np.deg2rad(15), 1 / 30)
            n = max(1, int(np.ceil(seconds * 30)))
            for mix in np.linspace(0, 1, n + 1)[1:]:
                self.append(previous + mix * (q - previous), phase, previous_tip + mix * (target - previous_tip))

    def join(self, goal, phase, clearance_z):
        goal = np.asarray(goal, dtype=float)
        before = self.q.copy()
        n = max(30, int(np.ceil(float(np.max(np.abs(goal - before))) / np.deg2rad(.5))))
        for alpha in np.linspace(0, 1, n + 1)[1:]:
            q = before + alpha * (goal - before)
            if self.check(q)[2] < clearance_z - .001:
                raise ValueError("姿勢をつなぐ途中で移動高さを下回ります。待機姿勢を取り直してください")
            self.append(q, phase)

    def dwell(self, seconds, phase):
        for _ in range(max(0, int(seconds * 30))):
            self.append(self.q, phase)

    def ink(self, settings):
        if settings["ink_mode"] != "automatic":
            return
        poses = self.desk["poses"]
        if "suzuri_pull" not in poses:
            raise ValueError("硯の墨池と引く端の両方を記録してください。引く長さは推測しません")
        def point(name):
            q = lerobot_to_qpos(poses[name], tilt_sign=self.desk["tilt_sign"],
                offsets=playback_offsets(self.desk), gripper_map=desk_gripper_map(self.desk))
            return _tip_and_axis(self.env, q)[0].copy()
        pool, near = point("suzuri_pool"), point("suzuri_pull")
        distance = float(np.linalg.norm(pool[:2] - near[:2]) * 1000)
        if not 5 <= distance <= 120 or abs(pool[2] - near[2]) > .005:
            raise ValueError("硯の2点は5〜120 mm離し、高さの差は5 mm以内で記録してください")
        lift = settings["ink_lift_mm"] / 1000
        safe = max(self.desk["paper"]["surface_z"], pool[2], near[2]) + settings["travel_mm"] / 1000
        self.line(np.r_[self.tip[:2], safe], "上へ逃がす")
        self.line(np.r_[pool[:2], safe], "硯の上へ")
        self.line(pool, "墨池につける", 5)
        self.dwell(settings["ink_dwell_s"], "含墨を待つ")
        for i in range(settings["ink_trips"]):
            self.line(near, "墨を整える", settings["ink_speed_mm_s"])
            if i + 1 < settings["ink_trips"]:
                self.line(near + [0, 0, lift], "硯から少し上げる", 5)
                self.line(pool + [0, 0, lift], "墨池へ戻す", settings["ink_speed_mm_s"])
                self.line(pool, "墨池へ下ろす", 5)
        self.dwell(settings["ink_wait_s"], "硯の端で待つ")
        self.line(np.r_[near[:2], safe], "硯から上げる", 5)

    def close(self):
        self.env.close()


def plan(args):
    desk = require_ready(load_desk(args.desk))
    settings = json.loads(args.settings.read_text())
    snap = json.loads(args.snapshot.read_text())
    if snap["desk_sha256"] != sha(args.desk):
        raise ValueError("位置の読み取り後に較正が変わりました")
    seed = np.asarray(snap["qpos"], dtype=float)
    planner = Planner(desk, seed)
    try:
        paper_z = desk["paper"]["surface_z"]
        safe = paper_z + settings["travel_mm"] / 1000
        if planner.tip[2] < paper_z - .001:
            raise ValueError("現在の毛先が紙面より下です。腕を支え、手で紙から離してから確認してください")
        planner.line(np.r_[planner.tip[:2], max(safe, planner.tip[2])], "筆を上げる")
        if args.trace:
            from scripts.hardware_write import _validate_trace_data
            with np.load(args.trace, allow_pickle=False) as trace:
                _validate_trace_data(trace, desk, False)
                first = np.asarray(trace["qpos"][0])
                end = np.asarray(trace["qpos"][-1])
                standby = np.asarray(trace["standby_qpos"])
                trace_arrays = {k: trace[k].copy() for k in ("qpos", "air_qpos", "expected_tip_xyz", "pen_down", "cell_index", "target_pressure", "dt")}
            planner.ink(settings)
            first_tip = _tip_and_axis(planner.env, first)[0].copy()
            high = max(planner.tip[2], safe)
            planner.line(np.r_[first_tip[:2], high], "紙の上へ")
            planner.line(first_tip, "書き出し位置へ")
            planner.join(first, "書字の姿勢に合わせる", safe)
            before, before_phases = np.asarray(planner.points), np.asarray(planner.phases)
            write_q, write_down, write_cells, write_pressure = [], [], [], []
            qs, expected = trace_arrays["qpos"], trace_arrays["expected_tip_xyz"]
            n = max(1, int(np.ceil(float(trace_arrays["dt"]) / settings["speed"] * 30)), int(np.ceil(np.max(np.abs(np.diff(qs, axis=0))) / np.deg2rad(.9))))
            for i in range(len(qs)):
                previous = max(0, i - 1)
                for mix in np.linspace(0, 1, n + 1)[1:]:
                    q = qs[previous] + mix * (qs[i] - qs[previous])
                    planner.check(q, expected[previous] + mix * (expected[i] - expected[previous]))
                    write_q.append(q)
                    write_down.append(bool(trace_arrays["pen_down"][i] and (trace_arrays["pen_down"][previous] or mix == 1)))
                    write_cells.append(int(trace_arrays["cell_index"][i]))
                    write_pressure.append(float(trace_arrays["target_pressure"][i]))
            planner.points, planner.phases, planner.q = [], [], end
            last = planner.tip
            planner.line(np.r_[last[:2], safe], "書き終えて筆を上げる")
            standby_tip = _tip_and_axis(planner.env, standby)[0].copy()
            planner.line(standby_tip, "紙の上で待機")
            planner.join(standby, "待機姿勢", safe)
            # A distinct, ink-free rehearsal from the same measured start.
            dry = Planner(desk, seed)
            try:
                air_q = trace_arrays["air_qpos"]
                air_targets = expected.copy()
                air_targets[:, 2] = safe
                high = max(dry.tip[2], safe)
                dry.line(np.r_[dry.tip[:2], high], "筆を上げる")
                dry.line(np.r_[air_targets[0, :2], high], "紙の上へ")
                dry.line(air_targets[0], "空中の書き出し位置へ")
                dry.join(air_q[0], "空中の姿勢を合わせる", safe)
                dry_before, dry_before_phase = np.asarray(dry.points), np.asarray(dry.phases)
                dry.points, dry.phases = [], []
                for i in range(len(air_q)):
                    prev = max(0, i - 1)
                    for mix in np.linspace(0, 1, n + 1)[1:]:
                        q = air_q[prev] + mix * (air_q[i] - air_q[prev])
                        dry.append(q, "空中で試す", air_targets[prev] + mix * (air_targets[i] - air_targets[prev]))
                dry_write = np.asarray(dry.points)
                dry.points, dry.phases = [], []
                dry.line(standby_tip, "紙の上で待機")
                dry.join(standby, "待機姿勢", safe)
                dry_after, dry_after_phase = np.asarray(dry.points), np.asarray(dry.phases)
            finally:
                dry.close()
        else:
            write_q, write_down, write_cells, write_pressure = [], [], [], []
            dry_before = dry_write = dry_after = np.empty((0, 6))
            dry_before_phase = dry_after_phase = np.asarray([])
            planner.ink(settings)
            initial_tip = _tip_and_axis(planner.env, seed)[0].copy()
            high = max(safe, planner.tip[2], initial_tip[2])
            planner.line(np.r_[planner.tip[:2], high], "筆を上げる")
            planner.line(np.r_[initial_tip[:2], high], "元の位置の上へ戻る")
            before, before_phases = np.asarray(planner.points), np.asarray(planner.phases)
            planner.points, planner.phases = [], []
        args.out.parent.mkdir(parents=True, exist_ok=True)
        np.savez(args.out, before_qpos=before, before_phase=before_phases,
                 after_qpos=np.asarray(planner.points).reshape(-1, 6),
                 after_phase=np.asarray(planner.phases), start_qpos=seed,
                 write_qpos=np.asarray(write_q).reshape(-1, 6), write_down=np.asarray(write_down),
                 write_cells=np.asarray(write_cells), write_pressure=np.asarray(write_pressure),
                 dry_before_qpos=dry_before, dry_before_phase=dry_before_phase,
                 dry_write_qpos=dry_write, dry_after_qpos=dry_after, dry_after_phase=dry_after_phase,
                 desk_sha256=sha(args.desk), settings_sha256=sha(args.settings),
                 trace_sha256=sha(args.trace) if args.trace else "", trace_path=str(args.trace or ""),
                 dt=1 / 30, snapshot_time_s=float(snap["host_monotonic_s"]))
        report = {"passed": True, "fk_error_max_mm": planner.worst_error_mm,
                  "before_samples": len(before), "after_samples": len(planner.points),
                  "physical_writing_verified": False, "motion_sha256": sha(args.out)}
        write_json(args.out.with_suffix(".json"), report)
        print(f"移動・硯・復帰経路を検証: {report}", flush=True)
    finally:
        planner.close()


def pressure_transfer(args):
    desk = require_ready(load_desk(args.desk))
    snap = json.loads(args.snapshot.read_text())
    if snap["desk_sha256"] != sha(args.desk):
        raise ValueError("筆圧試験の位置読み取り後に較正が変わりました")
    with np.load(args.pressure_plan, allow_pickle=False) as data:
        if str(data["desk_fingerprint"].item()) != desk_fingerprint(desk):
            raise ValueError("筆圧の試験軌道が古い較正のものです")
        first = data["air_qpos"][0].copy()
        last_air = data["air_qpos"][-1].copy()
    seed = np.asarray(snap["qpos"], dtype=float)
    planner = Planner(desk, seed)
    try:
        goal = _tip_and_axis(planner.env, first)[0].copy()
        safe = max(goal[2], planner.tip[2])
        if planner.tip[2] < desk["paper"]["surface_z"] - .001:
            raise ValueError("筆を紙から離し、垂直にしてから試験してください")
        planner.line(np.r_[planner.tip[:2], safe], "筆を上げる")
        planner.line(np.r_[goal[:2], safe], "試験位置の上へ")
        planner.line(goal, "試験の開始位置へ")
        planner.join(first, "試験姿勢へ合わせる", goal[2])
        entrance = np.asarray(planner.points)
        planner.points, planner.phases, planner.q = [], [], last_air
        goal = _tip_and_axis(planner.env, first)[0].copy()
        planner.line(goal, "試験開始点へ戻る")
        planner.join(first, "試験の開始姿勢に戻る", goal[2])
        np.savez(args.out, qpos=entrance, rehearsal_return_qpos=np.asarray(planner.points), start_qpos=seed,
                 desk_sha256=sha(args.desk), pressure_plan_sha256=sha(args.pressure_plan))
        print(f"筆圧試験への移動を検証しました（{len(planner.points)}点）")
    finally:
        planner.close()


def play(args):
    from scripts.hardware_write import (_validate_follower_port, _validate_trace_data,
        _connect_hold_present, _disconnect_holding, _safe_send_qpos, _read_feedback,
        _write_feedback_csv, _write_motion_gains)
    from scripts.gui_camera_guard import CameraGuard
    desk = require_ready(load_desk(args.desk))
    limits = np.asarray(require_joint_ranges(desk))
    settings = json.loads(args.settings.read_text())
    _validate_follower_port(args.port, desk)
    data = np.load(args.motion, allow_pickle=False)
    if str(data["desk_sha256"].item()) != sha(args.desk) or str(data["settings_sha256"].item()) != sha(args.settings):
        raise ValueError("較正か動作設定が変わりました。経路を確認し直してください")
    trace_path = str(data["trace_path"].item())
    trace = None
    if trace_path:
        if sha(trace_path) != str(data["trace_sha256"].item()):
            raise ValueError("確認後に書字軌道が変更されました")
        trace = np.load(trace_path, allow_pickle=False)
        _validate_trace_data(trace, desk, False)
    prefix = "dry_" if args.air_only else ""
    arrays = [np.asarray(data[prefix + k], dtype=float) for k in ("before_qpos", "after_qpos", "write_qpos")]
    for array in arrays:
        if array.ndim != 2 or array.shape[1] != 6 or not np.isfinite(array).all():
            raise ValueError("移動データが不正です")
        if np.any(array < limits[:, 0] + np.deg2rad(2)) or np.any(array > limits[:, 1] - np.deg2rad(2)):
            raise ValueError("移動データが可動域外です")
        if len(array) > 1 and np.max(np.abs(np.diff(array, axis=0))) > np.deg2rad(1) + 1e-7:
            raise ValueError("移動データの関節変化が大きすぎます")
    robot = robot_config(args.port)
    rows = []
    camera = None
    if settings["camera_enabled"] and trace is not None:
        camera = CameraGuard(settings["camera_url"], args.log.parent)
        camera.start()
        if not camera.wait_ready(6):
            camera.stop()
            raise ValueError("カメラの画像が取得できないため開始しません")
    last = None
    try:
        present = _connect_hold_present(robot)
        current = lerobot_to_qpos(present, tilt_sign=desk["tilt_sign"], offsets=playback_offsets(desk), gripper_map=desk_gripper_map(desk))
        if np.max(np.abs(current - data["start_qpos"])) > np.deg2rad(.5):
            raise ValueError("経路確認後にアームの姿勢が変わりました。現在位置から経路を確認し直してください")
        _write_motion_gains(robot.bus)
        def send(array, phases, writing=False):
            nonlocal last
            for index, (q, phase) in enumerate(zip(array, phases)):
                started = time.monotonic()
                if camera is not None and camera.failure is not None:
                    raise ValueError("カメラ監視が異常を検出しました。現在位置で停止します")
                observed = {k: float(v) for k, v in robot.bus.sync_read("Present_Position", num_retry=3).items()}
                observed_q = lerobot_to_qpos(observed, tilt_sign=desk["tilt_sign"], offsets=playback_offsets(desk), gripper_map=desk_gripper_map(desk))
                if last is not None and np.max(np.abs(observed_q - last)) > np.deg2rad(15):
                    raise ValueError("アームの追従誤差が15°を超えました。現在位置で停止します")
                metrics = _read_feedback(robot)
                for key, threshold in (desk.get("pressure_calibration_v1") or {}).get("safety", {}).items():
                    if writing and key in metrics and metrics[key] > float(threshold):
                        raise ValueError("サーボ負荷が較正時の上限を超えました。現在位置で停止します")
                _safe_send_qpos(robot, desk, q)
                last = q.copy()
                row = {"phase": str(phase), "host_monotonic_s": time.monotonic(), "command_start_monotonic_s": started, "pen_down": False}
                if writing:
                    row.update(pen_down=bool(data["write_down"][index]), cell=int(data["write_cells"][index]), target_pressure=float(data["write_pressure"][index]))
                row.update({f"position_deg:{k}": float(np.degrees(v)) for k, v in zip(JOINT_NAMES, observed_q)})
                row.update({f"command_deg:{k}": float(np.degrees(v)) for k, v in zip(JOINT_NAMES, q)})
                row.update(metrics)
                rows.append(row)
                time.sleep(max(0, 1 / 30 - (time.monotonic() - started)))
        send(arrays[0], data[prefix + "before_phase"])
        if trace is not None:
            if camera and not args.air_only and not camera.arm():
                raise ValueError("カメラ監視を開始できません")
            send(arrays[2], ["air" if args.air_only else "write"] * len(arrays[2]), writing=not args.air_only)
            if camera:
                camera.disarm()
        send(arrays[1], data[prefix + "after_phase"])
    finally:
        try:
            args.log.parent.mkdir(parents=True, exist_ok=True)
            _write_feedback_csv(args.log, rows)
        finally:
            try:
                if camera:
                    camera.stop()
            finally:
                # Hold the last position without an unchecked jump to hover.
                _disconnect_holding(robot)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("validate", "snapshot", "plan", "play", "pressure-transfer"))
    p.add_argument("--desk", type=Path, required=True)
    p.add_argument("--out", type=Path)
    p.add_argument("--settings", type=Path)
    p.add_argument("--snapshot", type=Path)
    p.add_argument("--trace", type=Path)
    p.add_argument("--motion", type=Path)
    p.add_argument("--log", type=Path)
    p.add_argument("--port")
    p.add_argument("--pressure-plan", type=Path)
    p.add_argument("--air-only", action="store_true")
    args = p.parse_args()
    try:
        return globals()[args.command.replace("-", "_")](args) or 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
