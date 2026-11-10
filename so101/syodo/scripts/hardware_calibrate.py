#!/usr/bin/env python3
"""Torque-off desk calibration. Do this before any writing playback.

Teach (lerobot venv, arm supported by hand):
  ~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_calibrate.py peek
  ~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_calibrate.py teach

Solve FK (syodo venv):
  python scripts/hardware_calibrate.py solve
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from so101_calligraphy.hardware_desk import (  # noqa: E402
    DEFAULT_DESK_PATH,
    DEFAULT_PORT,
    MAX_TUFT_CM,
    MAX_TOTAL_BRUSH_CM,
    MIN_TOTAL_BRUSH_CM,
    MIN_TUFT_CM,
    ROBOT_ID,
    SIM_HOME_POSE,
    SNAP_POSES,
    TEACH_AXES,
    TEACH_PROMPTS,
    REQUIRED_POSES,
    GRIPPER_RAD,
    JOINT_NAMES,
    desk_gaps,
    desk_fingerprint,
    desk_joint_ranges,
    format_desk,
    format_joints,
    geometry_fingerprint,
    joint_offsets_from_sim_home,
    load_desk,
    save_desk,
    solve_desk,
    brush_geometry,
    require_ready,
)

DEFAULT_ROBOT_CALIBRATION = Path.home() / ".cache/huggingface/lerobot/calibration/robots/so_follower/syodo_follower.json"


def _ask(prompt: str) -> str:
    return input(prompt).strip()


def _open_limp(port: str):
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

    robot = SO101Follower(
        SO101FollowerConfig(
            port=port,
            id=ROBOT_ID,
            max_relative_target=None,
            disable_torque_on_disconnect=True,
        )
    )
    # connect() は configure() の最後にトルクを再ONする。教示ではバスだけ開く。
    robot.bus.connect()
    robot.bus.disable_torque()
    return robot


def _close_limp(robot) -> None:
    if robot is None or not robot.bus.is_connected:
        return
    print("切断します。腕を支えてください。")
    try:
        robot.bus.disable_torque()
    except Exception:
        pass
    robot.bus.disconnect(disable_torque=False)


def _read_joints(robot) -> dict[str, float]:
    return {
        motor: float(value)
        for motor, value in robot.bus.sync_read("Present_Position", num_retry=3).items()
    }


def _record_pose(desk: dict, name: str, joints: dict[str, float]) -> None:
    desk.setdefault("poses", {})[name] = joints
    if name in desk.get("stale_poses", ()):
        desk["stale_poses"] = [pose for pose in desk["stale_poses"] if pose != name]
    if name == "suzuri_pull":
        desk["suzuri_pull_deg"] = dict(joints)
    else:
        desk["ready"] = False
        desk["pressure_calibration_v1"] = None
    print(f"記録 {name}  {format_joints(joints)}")


def _set_brush(args: argparse.Namespace) -> None:
    desk = load_desk(args.desk)
    scale, rigid_m, _ = brush_geometry(args.total_cm, args.tuft_cm)
    # Legacy desk stored grip-to-tip length under brush_tuft_cm. If the total
    # reach is unchanged, all taught FK geometry remains valid: only its rigid
    # versus flexible composition was mislabeled. Preserve physical pressure
    # observations, but bind them to the corrected fingerprint.
    previous_scale = desk.get("brush_tip_length_scale")
    previous_fingerprint = desk_fingerprint(desk)
    legacy = desk.get("brush_total_cm") is None
    if legacy and desk.get("geometry_fingerprint") is not None:
        if desk["geometry_fingerprint"] != geometry_fingerprint(desk, include_brush_split=False):
            raise SystemExit("古いdeskの較正後に幾何が変更されています。長さ表記だけでは移行できません。")
    if not legacy and desk.get("ready") is True:
        # Never bless stale geometry simply by re-entering the brush length.
        require_ready(desk)
    same_tuft = legacy or desk.get("brush_tuft_cm") == float(args.tuft_cm)
    if legacy:
        # Schema-1 fingerprint before the total/rigid fields were introduced.
        payload = {key: desk.get(key) for key in (
            "paper", "brush_tuft_cm", "brush_tip_length_scale", "joint_offsets_deg",
            "joint_ranges_rad", "gripper_map_rad", "tilt_sign", "motor_calibration_sha256",
        )}
        legacy_fingerprint = hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8")).hexdigest()
    else:
        legacy_fingerprint = None
    same_reach = bool(
        desk.get("ready") is True
        and isinstance(previous_scale, (int, float))
        and np.isfinite(previous_scale)
        and np.isclose(float(previous_scale), scale, rtol=1e-9)
    )
    desk["brush_total_cm"] = float(args.total_cm)
    desk["brush_tuft_cm"] = float(args.tuft_cm)
    desk["brush_rigid_cm"] = rigid_m * 100.0
    desk["brush_tip_length_scale"] = scale
    if same_reach:
        desk["geometry_fingerprint"] = geometry_fingerprint(desk)
        calibration = desk.get("pressure_calibration_v1")
        if (same_tuft and isinstance(calibration, dict)
                and calibration.get("desk_fingerprint") is not None
                and calibration.get("desk_fingerprint") in
                {previous_fingerprint, legacy_fingerprint}):
            calibration = dict(calibration)
            calibration["desk_fingerprint"] = desk_fingerprint(desk)
            desk["pressure_calibration_v1"] = calibration
        else:
            desk["pressure_calibration_v1"] = None
        require_ready(desk)
    else:
        desk["ready"] = False
        desk["pressure_calibration_v1"] = None
    save_desk(args.desk, desk)
    print(
        f"把持→毛先 {desk['brush_total_cm']:g} cm = "
        f"筆軸 {desk['brush_rigid_cm']:g} cm + 穂 {desk['brush_tuft_cm']:g} cm → {args.desk}"
    )


def _sync_limits(args: argparse.Namespace) -> None:
    calibration_path = args.robot_calibration.expanduser().resolve()
    try:
        payload = calibration_path.read_bytes()
        calibration = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Follower較正JSONを読めません（{calibration_path}: {exc}）") from exc
    missing = [name for name in JOINT_NAMES if name not in calibration]
    if missing:
        raise SystemExit(f"Follower較正JSONに軸がありません: {', '.join(missing)}")

    desk = load_desk(args.desk)
    offsets = desk.get("joint_offsets_deg") or {}
    if any(name not in offsets for name in JOINT_NAMES[:-1]):
        raise SystemExit("先に preview → snap sim_home → solve で関節オフセットを作ってください")
    ranges: list[list[float]] = []
    for name in JOINT_NAMES[:-1]:
        item = calibration[name]
        try:
            if int(item["id"]) != JOINT_NAMES.index(name) + 1:
                raise ValueError("id")
            low = float(item["range_min"])
            high = float(item["range_max"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"{name} のidまたはrange_min/range_maxが不正です") from exc
        if not np.isfinite([low, high]).all() or high <= low:
            raise SystemExit(f"{name} の較正範囲が不正です")
        mid = (low + high) / 2.0
        degrees = sorted(((low - mid) * 360.0 / 4095.0, (high - mid) * 360.0 / 4095.0))
        offset = float(offsets[name])
        ranges.append([float(np.deg2rad(degrees[0] + offset)), float(np.deg2rad(degrees[1] + offset))])
    # Gripper is exposed as a 0–100% LeRobot signal.  Its qpos endpoints are
    # the calibrated desk map, while the JSON range is still parsed and
    # validated below so a stale/partial six-axis file cannot pass silently.
    try:
        gripper_item = calibration["gripper"]
        if int(gripper_item["id"]) != len(JOINT_NAMES):
            raise ValueError("id")
        gripper_low = float(gripper_item["range_min"])
        gripper_high = float(gripper_item["range_max"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit("gripper のidまたはrange_min/range_maxが不正です") from exc
    if not np.isfinite([gripper_low, gripper_high]).all() or gripper_high <= gripper_low:
        raise SystemExit("gripper の較正範囲が不正です")
    gripper = desk.get("gripper_map_rad") or GRIPPER_RAD
    ranges.append(sorted(float(value) for value in gripper))

    old_hash = desk.get("motor_calibration_sha256")
    digest = hashlib.sha256(payload).hexdigest()
    desk["joint_ranges_rad"] = ranges
    try:
        desk_joint_ranges(desk)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    desk["motor_calibration_sha256"] = digest
    usb_serial = args.usb_serial or desk.get("follower_usb_serial")
    if getattr(args, "verify_connected", False):
        from serial.tools import list_ports
        info = next((item for item in list_ports.comports() if item.device == args.port), None)
        if info is None or not info.serial_number:
            raise SystemExit("選んだFollowerのUSBが見つかりません。接続画面で実際のポートを選んでください。")
        usb_serial = info.serial_number
    if usb_serial is None:
        try:
            from serial.tools import list_ports

            info = next((item for item in list_ports.comports() if item.device == args.port), None)
            usb_serial = None if info is None else info.serial_number
        except Exception:
            usb_serial = None
    prepare_only = bool(getattr(args, "prepare_only", False))
    if not usb_serial and not prepare_only:
        raise SystemExit(
            "Follower USBシリアルを特定できません。Follower接続中に --usb-serial を指定してください。"
        )
    if usb_serial:
        desk["follower_usb_serial"] = str(usb_serial)
        desk["follower_port"] = args.port
    else:
        desk["follower_usb_serial"] = None
        desk["follower_port"] = None
    desk["follower_id"] = ROBOT_ID
    if old_hash != digest:
        desk["pressure_calibration_v1"] = None
        if old_hash is not None:
            # Encoder recalibration changes the meaning of every taught pose.
            desk["ready"] = False
            desk["stale_poses"] = list((*REQUIRED_POSES, SIM_HOME_POSE))
    save_desk(args.desk, desk)
    if desk.get("stale_poses"):
        print("サーボ較正が変わりました。ready=false。teach と snap sim_home を取り直してから solve してください。")
    binding = (
        f"USB={usb_serial} port={args.port}"
        if usb_serial
        else "USB binding=pending（Follower接続後にsync-limitsを再実行）"
    )
    print(
        f"実機関節範囲を保存: {args.desk}  sha256={digest[:12]}…\n"
        f"範囲(rad)={[[round(value, 4) for value in pair] for pair in ranges]}\n{binding}"
    )


def _snap(args: argparse.Namespace) -> None:
    name = args.pose
    if name not in SNAP_POSES:
        raise SystemExit("姿勢は: " + ", ".join(SNAP_POSES))
    path = args.desk
    desk = load_desk(path)
    if desk.get("brush_tuft_cm") is None:
        raise SystemExit("先に hardware_calibrate.py brush 12 4")
    if name == SIM_HOME_POSE and not desk.get("sim_home_qpos_deg"):
        raise SystemExit("先に .venv/bin/python scripts/hardware_calibrate.py preview")
    print(TEACH_PROMPTS[name])
    robot = None
    try:
        robot = _open_limp(args.port)
        joints = _read_joints(robot)
        print("いま", format_joints(joints))
        _record_pose(desk, name, joints)
        if name == SIM_HOME_POSE:
            desk["joint_offsets_deg"] = joint_offsets_from_sim_home(desk)
            print("offsets °", desk["joint_offsets_deg"])
        save_desk(path, desk)
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(
            f"サーボに繋がりません（{exc}）。12V を入れ直して腕を支えてください。"
        ) from exc
    finally:
        _close_limp(robot)
    if name == SIM_HOME_POSE:
        print(f"目視合わせを保存: {path}")
        return
    if name == "suzuri_pull":
        print(f"硯の手前端を保存: {path}。solve は不要。go で書けます。")
        return
    leftover = desk_gaps(desk)
    if leftover:
        print("次:", leftover[0], "—", TEACH_PROMPTS[leftover[0]])
    else:
        print("全部揃った。次: .venv/bin/python scripts/hardware_calibrate.py solve")


def _teach(args: argparse.Namespace) -> None:
    path = args.desk
    desk = load_desk(path)
    print(
        "定規で2つ測る: 把持位置から毛先までの全長と、毛の根元から毛先までの穂長。\n"
        f"全長 {MIN_TOTAL_BRUSH_CM:.0f}–{MAX_TOTAL_BRUSH_CM:.0f} cm、"
        f"穂 {MIN_TUFT_CM:.0f}–{MAX_TUFT_CM:.0f} cm。"
    )
    total_suggested = desk.get("brush_total_cm") or 12.0
    suggested = desk.get("brush_tuft_cm") if desk.get("brush_total_cm") else 4.0
    if suggested is None:
        suggested = 4.0
    while True:
        total_raw = _ask(f"把持位置から毛先まで cm [{total_suggested:g}]: ")
        raw = _ask(f"穂（毛だけ）の長さ cm [{suggested:g}]: ")
        try:
            total = float(total_raw) if total_raw else float(total_suggested)
            tuft = float(raw) if raw else float(suggested)
            scale, rigid_m, _ = brush_geometry(total, tuft)
            desk["brush_total_cm"] = total
            desk["brush_tuft_cm"] = tuft
            desk["brush_rigid_cm"] = rigid_m * 100.0
            desk["brush_tip_length_scale"] = scale
            break
        except ValueError as exc:
            print(exc)
    desk["ready"] = False
    save_desk(path, desk)

    print(TEACH_AXES)
    print("腕を手で支えてください。Enter で読み取り開始（トルクは入れません）。")
    _ask("")
    robot = None
    try:
        robot = _open_limp(args.port)
    except Exception as exc:
        raise SystemExit(
            f"サーボに繋がりません（{exc}）。\n"
            "12V を一度切って入れ直し、腕を支えてから同じコマンドを再実行してください。"
        ) from exc
    print("トルク OFF。手で動かして、各姿勢で Enter。q で中断。")
    prev: dict[str, float] | None = None
    try:
        for name in REQUIRED_POSES:
            while True:
                print(f"\n[{name}] {TEACH_PROMPTS[name]}")
                if name in desk.get("poses", {}):
                    print("  記録済み。Enter で上書き、s でスキップ。")
                key = _ask("> ")
                if key in {"q", "Q"}:
                    save_desk(path, desk)
                    return
                if key.lower() == "s" and name in desk.get("poses", {}):
                    break
                joints = {
                    motor: float(value)
                    for motor, value in robot.bus.sync_read(
                        "Present_Position", num_retry=3
                    ).items()
                }
                if prev is not None and max(
                    abs(joints[k] - prev[k]) for k in joints
                ) < 1.0:
                    print(
                        "  関節がほとんど動いていません。"
                        "一番先端（横軸）か腕を動かしてから Enter。この値でよければ s。"
                    )
                    again = _ask("  > ")
                    if again in {"q", "Q"}:
                        save_desk(path, desk)
                        return
                    if again.lower() != "s":
                        continue
                _record_pose(desk, name, joints)
                save_desk(path, desk)
                prev = joints
                break
    finally:
        _close_limp(robot)
    print(f"教示を保存: {path}")
    leftover = desk_gaps(desk)
    if leftover:
        print("まだ足りない:", ", ".join(leftover))
        print("solve は全部揃ってから。")
    else:
        print("次: 書道 venv で  python scripts/hardware_calibrate.py solve")


def _solve(args: argparse.Namespace) -> None:
    path = args.desk
    try:
        desk = solve_desk(load_desk(path))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    save_desk(path, desk)
    print(format_desk(desk))
    print(f"保存: {path}")


def _preview(args: argparse.Namespace) -> None:
    import imageio.v2 as imageio
    import mujoco
    import numpy as np
    from so101_calligraphy.config import EnvConfig, JOINT_NAMES
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
    from so101_calligraphy.hardware_desk import overlay_desk_hardware

    desk = load_desk(args.desk)
    if desk.get("brush_tuft_cm") is None:
        raise SystemExit("先に hardware_calibrate.py brush 12 4")
    env = CalligraphyEnv(
        task="line",
        render_mode="rgb_array",
        config=overlay_desk_hardware(
            EnvConfig(reset_noise=0.0, domain_randomization=False), desk
        ),
    )
    try:
        env.reset(seed=0)
        qdeg = np.rad2deg(env.data.qpos[env._qpos_indices])
        home = {
            name: float(qdeg[i]) for i, name in enumerate(JOINT_NAMES)
        }
        if home != desk.get("sim_home_qpos_deg"):
            desk["ready"] = False
            desk["pressure_calibration_v1"] = None
            desk["stale_poses"] = list(dict.fromkeys([*desk.get("stale_poses", ()), SIM_HOME_POSE]))
        desk["sim_home_qpos_deg"] = home
        save_desk(args.desk, desk)
        out_dir = args.desk.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        renderer = mujoco.Renderer(env.model, height=720, width=960)
        renderer.update_scene(env.data, camera="overview")
        overview = out_dir / "sim-home-overview.png"
        imageio.imwrite(overview, renderer.render())
        cam = mujoco.MjvCamera()
        mujoco.mjv_defaultFreeCamera(env.model, cam)
        look = env.data.site_xpos[env._brush_mount_site_id]
        cam.lookat[:] = look
        cam.distance = 0.65
        cam.azimuth = -90.0
        cam.elevation = -18.0
        renderer.update_scene(env.data, camera=cam)
        side = out_dir / "sim-home-side.png"
        imageio.imwrite(side, renderer.render())
        renderer.close()
    finally:
        env.close()
    print("シミュリセット °", {k: round(v, 1) for k, v in desk["sim_home_qpos_deg"].items()})
    print(overview)
    print(side)


def _peek(args: argparse.Namespace) -> None:
    robot = None
    try:
        robot = _open_limp(args.port)
        joints = _read_joints(robot)
        print(format_joints(joints))
        # 正規化値は較正レンジ外を 0/100% に丸める。生 tick なら端に張り付いても分かる。
        raw = robot.bus.sync_read("Present_Position", normalize=False, num_retry=3)
        print("生 tick ", {name: int(value) for name, value in raw.items()})
    except Exception as exc:
        raise SystemExit(
            f"サーボに繋がりません（{exc}）。12V を入れ直して腕を支えてください。"
        ) from exc
    finally:
        _close_limp(robot)


def _show(args: argparse.Namespace) -> None:
    print(format_desk(load_desk(args.desk)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--desk", type=Path, default=DEFAULT_DESK_PATH)
    common.add_argument("--port", default=DEFAULT_PORT)
    sub.add_parser("teach", parents=[common])
    sub.add_parser("solve", parents=[common])
    sub.add_parser("show", parents=[common])
    sub.add_parser("preview", parents=[common])
    sub.add_parser("peek", parents=[common])
    brush = sub.add_parser("brush", parents=[common])
    brush.add_argument("total_cm", type=float, help="把持位置から毛先まで")
    brush.add_argument("tuft_cm", type=float, help="毛の根元から毛先まで")
    sync = sub.add_parser("sync-limits", parents=[common])
    sync.add_argument("--robot-calibration", type=Path, default=DEFAULT_ROBOT_CALIBRATION)
    sync.add_argument("--usb-serial", default=None)
    sync.add_argument("--verify-connected", action="store_true")
    sync.add_argument(
        "--prepare-only",
        action="store_true",
        help="Follower未接続で可動域とhashだけ保存し、USB照合は接続後まで保留",
    )
    snap = sub.add_parser("snap", parents=[common])
    snap.add_argument("pose", choices=SNAP_POSES)
    args = parser.parse_args()
    if args.cmd == "teach":
        _teach(args)
    elif args.cmd == "solve":
        _solve(args)
    elif args.cmd == "show":
        _show(args)
    elif args.cmd == "preview":
        _preview(args)
    elif args.cmd == "peek":
        _peek(args)
    elif args.cmd == "brush":
        _set_brush(args)
    elif args.cmd == "sync-limits":
        _sync_limits(args)
    else:
        _snap(args)


if __name__ == "__main__":
    main()
