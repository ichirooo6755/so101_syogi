#!/usr/bin/env python3
"""Local SO-101 console. The UI server itself needs only Python's standard library.

Motor commands run only after an explicit action in the UI. Existing CLI checks
remain authoritative; the GUI uses its own desk and never edits desk.json.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
from datetime import datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import threading
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import webbrowser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).with_name("gui")
sys.path.insert(0, str(Path(__file__).parent))
from gui_loadcell import LoadCell
POSES = (
    ("upright", "筆を垂直に", "手首を曲げて筆を立て、毛先を机につけます。"),
    ("lean_toward_paper", "筆を傾ける", "腕と筆元の回転部分はそのまま。図の「筆を傾ける部分」だけを動かし、毛先が紙に近づく側へ傾けます。"),
    ("tilt_min", "寝かせる側の限界", "図の「筆を傾ける部分」を、使いたい寝側の端へ。突き当たりまで回す必要はありません。"),
    ("tilt_max", "立てる側の限界", "図の「筆を傾ける部分」を、使いたい立側の端へ。"),
    ("paper_near_right", "紙の手前・右", "筆を垂直にして、毛先を紙の手前右につけます。"),
    ("paper_near_left", "紙の手前・左", "筆を垂直にして、毛先を紙の手前左につけます。"),
    ("paper_far_left", "紙の奥・左", "筆を垂直にして、毛先を紙の奥左につけます。"),
    ("paper_far_right", "紙の奥・右", "筆を垂直にして、毛先を紙の奥右につけます。"),
    ("paper_center_touch", "紙の中央", "筆を垂直にして、毛先を紙の中央につけます。"),
    ("hover_center", "紙の中央の上", "筆を垂直にしたまま、紙面から15 mm以上離します。"),
    ("suzuri_pool", "硯の墨池", "毛先を墨池の中心の液面につけます。"),
    ("sim_home", "腕の基準姿勢", "基準画像に合わせ、上腕を垂直・前腕を水平のL字にします。筆は垂直です。"),
    ("suzuri_pull", "硯の手前の端", "毛先を硯につけたまま、墨池から手前へ引いた端に置きます。"),
)
REQUIRED = [p[0] for p in POSES if p[0] != "suzuri_pull"]


class UserError(Exception):
    pass


def read_json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else deepcopy(default)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def finite(value, label, lo, hi):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise UserError(f"{label}を入力してください。") from None
    if not math.isfinite(result) or not lo <= result <= hi:
        raise UserError(f"{label}は{lo:g}〜{hi:g}で入力してください。")
    return result


def camera_url(value):
    value = str(value).strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise UserError("カメラのURLは http://192.168.4.1 の形式で入力してください。")
    try:
        parsed.port
    except ValueError:
        raise UserError("カメラのポート番号が不正です。") from None
    return value


class Jobs:
    """One worker, one process group; cancellation also covers between-step gaps."""

    def __init__(self, root):
        self.root = root
        self.lock = threading.RLock()
        self.lines = deque(maxlen=300)
        self.sequence = 0
        self.active = False
        self.process = None
        self.cancel = threading.Event()
        self.prompt = None
        self.info = {"label": "待機中", "state": "idle", "action": None, "returncode": None}

    def log(self, message):
        with self.lock:
            self.sequence += 1
            self.lines.append({"id": self.sequence, "text": message})

    def snapshot(self):
        with self.lock:
            return {**self.info, "active": self.active, "lines": list(self.lines), "prompt": self.prompt}

    def start(self, label, action, commands, *, env=None, success=None, interactive=False, finish=None):
        with self.lock:
            if self.active:
                raise UserError("実行中の操作が終わるか、停止してから操作してください。")
            self.active = True
            self.cancel.clear()
            self.lines.clear()
            self.prompt = None
            self.info = {"label": label, "state": "running", "action": action, "returncode": None}
            self.thread = threading.Thread(target=self._run, args=(commands, env, success, interactive, finish), daemon=True)
            self.thread.start()

    def _run(self, commands, env, success, interactive, finish):
        code = 0
        try:
            for description, command in commands:
                with self.lock:
                    if self.cancel.is_set():
                        break
                    self.log(description)
                    self.process = subprocess.Popen(
                        command, cwd=self.root, env=env, stdin=subprocess.PIPE if interactive else subprocess.DEVNULL,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding="utf-8", errors="replace", bufsize=1,
                        start_new_session=True,
                    )
                    process = self.process
                for line in process.stdout:
                    if line.startswith("SYODO_GUI_PROMPT:"):
                        prompt = json.loads(line.split(":", 1)[1])
                        with self.lock:
                            self.prompt = {**prompt, "id": secrets.token_hex(12)}
                        self.log(prompt["text"])
                    else:
                        self.log(line.rstrip())
                code = process.wait()
                process.stdout.close()
                if process.stdin:
                    process.stdin.close()
                with self.lock:
                    self.process = None
                if code or self.cancel.is_set():
                    break
            with self.lock:
                if not code and not self.cancel.is_set() and success:
                    success()
        except Exception as exc:
            code = 1
            self.log(str(exc))
        finally:
            with self.lock:
                if finish:
                    try:
                        finish(code, self.cancel.is_set())
                    except Exception as exc:
                        code = 1
                        self.log(str(exc))
                stopped = self.cancel.is_set()
                self.info.update(state="stopped" if stopped else "error" if code else "done", returncode=code)
                self.log("停止しました。" if stopped else "操作に失敗しました。ログを確認してください。" if code else "完了しました。")
                self.active = False
                self.process = None
                self.prompt = None

    def respond(self, prompt_id, value):
        with self.lock:
            if not self.active or self.cancel.is_set() or not self.prompt or self.prompt["id"] != prompt_id or self.process is None:
                raise UserError("この入力待ちは終了しています。画面を確認してください。")
            value = str(value)
            if self.prompt["kind"] == "line" and value not in ("1", "2", "3", "4", "5", "none"):
                raise UserError("1〜5から試験線を選んでください。")
            if self.prompt["kind"] == "continue" and value != "":
                raise UserError("「準備できたので続ける」を押してください。")
            self.process.stdin.write(value + "\n")
            self.process.stdin.flush()
            self.prompt = None

    def stop(self):
        with self.lock:
            if not self.active:
                return
            self.cancel.set()
            self.info["state"] = "stopping"
            self.log("停止を要求しました。現在の処理が終了するまでお待ちください。")
            if self.process is not None and self.process.poll() is None:
                try:
                    os.killpg(self.process.pid, signal.SIGINT)
                except ProcessLookupError:
                    pass


class Console:
    def __init__(self, root=ROOT, data=None):
        self.root = Path(root).resolve()
        self.data = Path(data) if data else self.root / "data/hardware/gui"
        self.desk_path = self.data / "desk.json"
        self.settings_path = self.data / "settings.json"
        self.jobs = Jobs(self.root)
        self.prepared = None
        self.pressure_plan = None
        self.ink_prepared = None
        self.last_run = None
        self.air_verified_key = None
        self.ink_verified_key = None
        self.token = secrets.token_urlsafe(32)
        if not self.desk_path.exists():
            desk = read_json(self.root / "data/hardware/desk.json", {"schema": 1, "poses": {}})
            desk.update(ready=False, pressure_calibration_v1=None, stale_poses=REQUIRED, suzuri_pull_deg=None)
            desk.setdefault("poses", {}).pop("suzuri_pull", None)
            desk["gui_profile_v2"] = True
            write_json(self.desk_path, desk)
        current_desk = read_json(self.desk_path)
        if not current_desk.get("gui_profile_v2"):
            write_json(self.data / "desk-before-v2.json", current_desk)
            current_desk.update(gui_profile_v2=True, ready=False, pressure_calibration_v1=None, suzuri_pull_deg=None)
            current_desk.setdefault("poses", {}).pop("suzuri_pull", None)
            write_json(self.desk_path, current_desk)
        defaults = {
            "brush_length_mm": 240.0, "tuft_mm": 42.0, "reach_mm": None,
            "word": "一", "speed": 0.8, "glyph_mm": 100.0, "travel_mm": 30.0,
            "paper_depth_mm": None, "paper_width_mm": None,
            "ink_mode": "manual", "ink_trips": 1, "ink_dwell_s": 2.0,
            "ink_wait_s": 3.0, "ink_lift_mm": 5.0, "ink_speed_mm_s": 10.0,
            "loadcell_enabled": False, "force_limit_n": 2.0,
            "camera_enabled": False, "camera_url": "http://192.168.4.1",
            "camera_roi": [0.08, 0.08, 0.92, 0.92],
            "follower_port": "/dev/cu.usbmodem5B7B0136431",
            "leader_port": "/dev/cu.usbmodem5B7B0140931",
            "sim_python": os.environ.get("SYODO_PYTHON", str(self.root / ".venv/bin/python")),
            "hw_python": os.environ.get("LEROBOT_HW_PYTHON", str(Path.home() / "Documents/lerobot-hw/.venv/bin/python")),
        }
        stored = read_json(self.settings_path, {})
        if stored and "glyph_mm" not in stored:
            write_json(self.data / "settings-before-v2.json", stored)
            stored["word"] = "一"
        self.settings = {**defaults, **stored}
        if not self.settings_path.exists() or self.settings != stored:
            write_json(self.settings_path, self.settings)
        self.loadcell = LoadCell(self.data / "loadcell.json", lambda: self.settings, self.sensor_fault)

    def sensor_fault(self, reason):
        if self.jobs.active and not self.jobs.cancel.is_set():
            self.jobs.log(reason)
            self.jobs.stop()

    def validation_command(self):
        return ("実測値・較正・筆圧の整合性を検証", self.command("gui_workflow.py", ["validate", "--desk", self.desk_path, "--out", self.data / "validation.json"]))

    def key(self):
        return hashlib.sha256(self.desk_path.read_bytes() + json.dumps(self.settings, sort_keys=True).encode()).hexdigest()

    def status(self):
        with self.jobs.lock:
            desk = read_json(self.desk_path, {})
            stale = desk.get("stale_poses", [])
            poses = desk.get("poses", {})
            missing = [name for name in REQUIRED if name not in poses or name in stale]
            brush_matches = self.settings.get("reach_mm") is not None and math.isclose(
                desk.get("brush_total_cm", 0) or 0, self.settings["reach_mm"] / 10,
            ) and math.isclose(desk.get("brush_tuft_cm", 0) or 0, self.settings["tuft_mm"] / 10)
            # These labels summarize stored state. CLI require_ready, USB binding,
            # fingerprints and range validation run again before any movement.
            proof = read_json(self.data / "validation.json", {})
            proof_matches = proof.get("desk_sha256") == hashlib.sha256(self.desk_path.read_bytes()).hexdigest()
            ready = bool(desk.get("ready") is True and not missing and brush_matches and proof_matches and proof.get("geometry_ok") is True)
            pressure_ready = bool(ready and proof.get("pressure_ok") is True)
            depth = (desk.get("paper") or {}).get("width", 0) * 1000 if ready else self.settings.get("paper_depth_mm") or 0
            width = (desk.get("paper") or {}).get("height", 0) * 1000 if ready else self.settings.get("paper_width_mm") or 0
            maximum = max(0, min(width - 30, (depth - 30) / len(self.settings["word"])))
            return {
                "settings": self.settings, "job": self.jobs.snapshot(), "ready": ready,
                "pressure_ready": pressure_ready,
                "pressure_plan_ready": bool(self.pressure_plan and self.pressure_plan["key"] == self.key()),
                "prepared": bool(self.prepared and self.prepared["key"] == self.key()),
                "prepared_path": str(self.prepared["directory"]) if self.prepared else None,
                "ink_prepared": bool(self.ink_prepared and self.ink_prepared["key"] == self.key()),
                "validation_errors": proof.get("errors", []) if proof_matches else ["実測する長方形を設定し、位置の較正・検証を完了してください"],
                "layout": {"depth_mm": depth, "width_mm": width, "maximum_glyph_mm": maximum,
                    "fits": bool(maximum >= self.settings["glyph_mm"]), "glyph_mm": self.settings["glyph_mm"]},
                "ports": sorted(str(p) for p in Path("/dev").glob("cu.usb*")),
                "follower_present": Path(self.settings["follower_port"]).exists(),
                "loadcell": self.loadcell.status(),
                "last_run": str(self.last_run) if self.last_run else None,
                "last_run_action": read_json(self.last_run / "session.json", {}).get("action") if self.last_run else None,
                "camera_calibrated": (self.data / "camera-calibration.json").is_file(),
                "camera_proposal": read_json(self.data / "camera-proposal.json", None),
                "air_verified": self.air_verified_key == self.key(),
                "ink_verified": self.ink_verified_key == self.key(),
                "poses": [{"name": n, "label": label, "hint": hint, "recorded": n in poses and n not in stale} for n, label, hint in POSES],
                "desk": {"paper": desk.get("paper"), "inkstone_offset_m": desk.get("inkstone_offset_m"), "safe_height_m": desk.get("safe_height_m")},
                "desk_path": str(self.desk_path),
            }

    def save(self, changes):
        with self.jobs.lock:
            if self.jobs.active:
                raise UserError("実行中は設定を変更できません。停止後に保存してください。")
            if not isinstance(changes, dict) or set(changes) - set(self.settings):
                raise UserError("設定項目が不正です。")
            s = {**self.settings, **changes}
            s["brush_length_mm"] = finite(s["brush_length_mm"], "筆の全長 mm", 40, 300)
            s["tuft_mm"] = finite(s["tuft_mm"], "穂の長さ mm", 20, 80)
            if s["tuft_mm"] >= s["brush_length_mm"]:
                raise UserError("穂の長さは筆の全長より短くしてください。")
            if s["reach_mm"] in (None, ""):
                s["reach_mm"] = None
            else:
                s["reach_mm"] = finite(s["reach_mm"], "取り付け位置から毛先まで mm", 40, s["brush_length_mm"])
                if s["reach_mm"] <= s["tuft_mm"]:
                    raise UserError("取り付け位置から毛先までは、穂の長さより長くしてください。")
            s["word"] = str(s["word"]).strip()
            if not 1 <= len(s["word"]) <= 2 or any(c.isspace() or ord(c) < 32 for c in s["word"]):
                raise UserError("この筆のGUIは大きな1〜2文字用です。4文字を小さく詰める操作はできません。")
            s["speed"] = finite(s["speed"], "速さ", 0.1, 1.5)
            s["glyph_mm"] = finite(s["glyph_mm"], "文字の大きさ mm", 60, 180)
            s["travel_mm"] = finite(s["travel_mm"], "移動高さ mm", 20, 80)
            for key in ("paper_depth_mm", "paper_width_mm"):
                s[key] = None if s[key] in (None, "") else finite(s[key], "定規で測る書字領域 mm", 100, 450)
            if (s["paper_depth_mm"] is None) != (s["paper_width_mm"] is None):
                raise UserError("長方形の奥行きと幅は両方入力してください")
            if s["ink_mode"] not in ("manual", "automatic"):
                raise UserError("墨を付ける方法が不正です")
            trips = finite(s["ink_trips"], "硯で引く回数", 1, 3)
            if not trips.is_integer():
                raise UserError("硯で引く回数は整数です")
            s["ink_trips"] = int(trips)
            for key, hi in (("ink_dwell_s", 10), ("ink_wait_s", 10), ("ink_lift_mm", 15), ("ink_speed_mm_s", 20)):
                s[key] = finite(s[key], "硯の動き", 0 if key.endswith("_s") and "speed" not in key else 1, hi)
            if not isinstance(s["loadcell_enabled"], bool):
                raise UserError("ロードセルの使用設定が不正です")
            s["force_limit_n"] = finite(s["force_limit_n"], "計測方向の力の上限 N", .1, 5)
            if not isinstance(s["camera_enabled"], bool):
                raise UserError("カメラの設定が不正です。")
            s["camera_url"] = camera_url(s["camera_url"])
            if not isinstance(s["camera_roi"], list) or len(s["camera_roi"]) != 4:
                raise UserError("カメラの紙面範囲は4つの数値で設定してください。")
            roi = [finite(v, "紙面範囲", 0, 1) for v in s["camera_roi"]]
            if roi[0] >= roi[2] or roi[1] >= roi[3]:
                raise UserError("紙面範囲は左上から右下の順で指定してください。")
            s["camera_roi"] = roi
            for key in ("sim_python", "hw_python", "follower_port", "leader_port"):
                s[key] = str(s[key]).strip()
                if not s[key] or any(ord(c) < 32 for c in s[key]):
                    raise UserError("接続設定を入力してください。")
            if s["follower_port"] == s["leader_port"]:
                raise UserError("FollowerとLeaderには別々のUSBポートを指定してください")
            brush_changed = any(s[k] != self.settings[k] for k in ("brush_length_mm", "tuft_mm", "reach_mm"))
            binding_changed = s["follower_port"] != self.settings["follower_port"]
            paper_changed = any(s[k] != self.settings[k] for k in ("paper_depth_mm", "paper_width_mm"))
            if brush_changed or binding_changed or paper_changed:
                desk = read_json(self.desk_path)
                desk.update(ready=False, pressure_calibration_v1=None, gui_profile_v2=True)
                if brush_changed:
                    desk["stale_poses"] = REQUIRED
                    desk["suzuri_pull_deg"] = None
                    desk.setdefault("poses", {}).pop("suzuri_pull", None)
                    desk["brush_total_cm"] = s["reach_mm"] / 10 if s["reach_mm"] else None
                    desk["brush_tuft_cm"] = s["tuft_mm"] / 10
                    desk["brush_rigid_cm"] = (s["reach_mm"] - s["tuft_mm"]) / 10 if s["reach_mm"] else None
                    desk["brush_tip_length_scale"] = s["reach_mm"] / 38 if s["reach_mm"] else None
                if binding_changed:
                    desk["follower_usb_serial"] = None
                    desk["follower_port"] = None
                if paper_changed:
                    desk["paper_measurement_v1"] = ({"depth_mm": s["paper_depth_mm"], "width_mm": s["paper_width_mm"]} if s["paper_depth_mm"] else None)
                    desk["stale_poses"] = list(dict.fromkeys([*desk.get("stale_poses", []), "paper_near_left", "paper_near_right", "paper_far_left", "paper_far_right", "paper_center_touch", "hover_center"]))
                write_json(self.desk_path, desk)
            if s != self.settings:
                self.prepared = None
                self.pressure_plan = None
                self.ink_prepared = None
            write_json(self.settings_path, s)
            self.settings = s

    def command(self, script, args, *, hardware=False):
        python = Path(self.settings["hw_python" if hardware else "sim_python"]).expanduser()
        if not python.is_file() or not os.access(python, os.X_OK):
            raise UserError(f"Pythonが見つかりません。「接続」で設定してください: {python}")
        return [str(python), "-u", str(self.root / "scripts" / script), *map(str, args)]

    def action(self, name, payload):
        with self.jobs.lock:
            if self.jobs.active:
                raise UserError("実行中の操作を停止してから切り替えてください。")
            s = self.settings
            desk = ["--desk", str(self.desk_path)]
            follower = ["--port", s["follower_port"]]
            pair = [*follower, "--leader-port", s["leader_port"]]
            commands = []
            success = None
            interactive = False
            record_directory = None
            if name in ("snap", "sync-limits", "limp", "write", "air-test", "ink-test", "bilateral", "pressure-calibrate", "camera-calibrate", "camera-detect") and not Path(s["follower_port"]).exists():
                raise UserError("FollowerのUSBが見つかりません。「接続」で実際のポートを選んでください。")
            if name in ("snap", "preview", "solve", "sync-limits", "prepare", "write", "bilateral") and s["reach_mm"] is None:
                raise UserError("「準備」で取り付け位置から毛先までの長さを測り、保存してください。")
            if name in ("preview", "solve", "sync-limits", "snap"):
                self.prepared = None
                self.pressure_plan = None
                self.ink_prepared = None
                args = [name]
                hardware = name in ("snap", "sync-limits")
                if name == "snap":
                    pose = payload.get("pose")
                    if pose not in [p[0] for p in POSES]:
                        raise UserError("記録する位置が不正です。")
                    args.append(pose)
                args += desk
                if hardware:
                    args += follower
                if name == "sync-limits":
                    args += ["--verify-connected"]
                commands.append(("較正を実行します", self.command("hardware_calibrate.py", args, hardware=hardware)))
                if name in ("solve", "sync-limits"):
                    commands.append(self.validation_command())
                label = {"preview": "基準画像を作成", "solve": "紙・硯の位置を計算", "snap": "現在の位置を記録", "sync-limits": "サーボの較正を同期"}[name]
            elif name == "limp":
                label = "トルクをOFFにします"
                commands.append(("腕を手で支えてください。現在位置を読み取り、トルクをOFFにします。", self.command("hardware_calibrate.py", ["peek", *desk, *follower], hardware=True)))
            elif name == "pressure-plan":
                if not self.status()["ready"]:
                    raise UserError("先に位置の較正とサーボの同期を完了してください。")
                directory = self.root / "runs/gui" / datetime.now().strftime("pressure-%Y%m%d-%H%M%S-%f")
                plan = directory / "pressure-plan.npz"
                self.pressure_plan = None
                commands.append(("筆圧の試験軌道を作成します（アームは動きません）", self.command("hardware_write.py", ["pressure-plan", *desk, "--out", plan, "--lifts-mm", "4,3,2,1,0", "--clear-mm", s["travel_mm"] - 4])))
                key = self.key()
                def success():
                    self.pressure_plan = {"key": key, "directory": directory}
                label = "筆圧の試験軌道を確認"
            elif name == "pressure-calibrate":
                if not self.pressure_plan or self.pressure_plan["key"] != self.key():
                    raise UserError("先に「筆圧の試験軌道を確認」を実行してください。")
                directory = self.pressure_plan["directory"]
                commands.append(("現在位置を読み取ります", self.command("gui_workflow.py", ["snapshot", *desk, *follower, "--out", directory / "start.json"], hardware=True)))
                commands.append(("筆圧試験に入るまでの移動を検証", self.command("gui_workflow.py", ["pressure-transfer", *desk, "--snapshot", directory / "start.json", "--pressure-plan", directory / "pressure-plan.npz", "--out", directory / "transfer.npz"])))
                command = self.command("gui_task.py", ["pressure-calibrate", directory / "pressure-plan.npz", *desk, *follower, "--approach-plan", directory / "transfer.npz", "--log", directory / "pressure.csv"], hardware=True)
                commands.append(("最初に墨なしの空中リハーサルを行います。腕を支えてください。", command))
                commands.append(self.validation_command())
                self.prepared = self.pressure_plan = None
                interactive = True
                record_directory = directory
                label = "筆圧を較正中"
            elif name in ("prepare", "ink-prepare"):
                if not self.status()["ready"]:
                    raise UserError("先に「準備」で較正とサーボの同期を完了してください。")
                if name == "prepare" and not self.status()["pressure_ready"]:
                    raise UserError("先に「準備」の「筆圧を合わせる」を完了してください。")
                if not Path(s["follower_port"]).exists():
                    raise UserError("現在位置を読むためFollowerをUSB接続してください。経路確認ではアームを動かしません。")
                if name == "prepare" and not self.status()["layout"]["fits"]:
                    raise UserError(f"{s['glyph_mm']:g} mm角の文字は入りません。文字数を減らすか、書字領域を取り直してください。")
                if name == "ink-prepare" and s["ink_mode"] != "automatic":
                    raise UserError("硯の動作確認は「硯で付ける」に切り替えてから実行してください。")
                word = s["word"]
                for char in word:
                    if not (self.root / "data/kanjivg" / f"{ord(char):05x}.svg").is_file():
                        raise UserError(f"「{char}」の筆順データがありません。別の文字を選ぶか、KanjiVGデータを追加してください。")
                directory = self.root / "runs/gui" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                trace = directory / "trace.npz"
                self.prepared = None
                self.ink_prepared = None
                commands = [
                    ("現在位置を読み取り（アームは動かしません）", self.command("gui_workflow.py", ["snapshot", *desk, *follower, "--out", directory / "start.json"], hardware=True)),
                ]
                if name == "prepare":
                    commands += [
                        ("指定した実寸で文字の軌道を作成", self.command("hardware_write.py", ["trace", word, *desk, "--reference", self.data / "leader-reference.json", "--glyph-mm", s["glyph_mm"], "--calibrated-heights", "--lift-mm", "4", "--air-mm", s["travel_mm"], "--standby-mm", s["travel_mm"], "--out", trace])),
                        ("書字軌道のFK・可動域を監査", self.command("audit_hardware_trace.py", [trace, *desk, "--output", directory / "preflight.json"])),
                    ]
                args = ["plan", *desk, "--settings", self.settings_path, "--snapshot", directory / "start.json", "--out", directory / "motion.npz"]
                if name == "prepare":
                    args += ["--trace", trace]
                commands.append(("現在位置から硯・紙・復帰まで全移動を検証", self.command("gui_workflow.py", args)))
                key = self.key()
                def success():
                    files = ["motion.npz", "start.json"] + (["trace.npz", "preflight.json"] if name == "prepare" else [])
                    hashes = {f: hashlib.sha256((directory / f).read_bytes()).hexdigest() for f in files}
                    if name == "prepare":
                        if read_json(directory / "preflight.json").get("passed") is not True:
                            raise UserError("軌道監査に合格していません")
                        self.prepared = {"key": key, "directory": directory, "hashes": hashes}
                    else:
                        self.ink_prepared = {"key": key, "directory": directory, "hashes": hashes}
                label = "軌道を確認中"
            elif name in ("write", "air-test", "ink-test"):
                prepared = self.prepared if name in ("write", "air-test") else self.ink_prepared
                if not prepared or prepared["key"] != self.key():
                    raise UserError("現在の設定で「軌道を確認」を実行してください。")
                directory = prepared["directory"]
                if name == "write" and self.air_verified_key != self.key():
                    raise UserError("先に空中で試し、接触せず動いたことを結果欄で記録してください。動作後は現在位置から経路を確認し直します。")
                if name == "write" and s["ink_mode"] == "automatic" and self.ink_verified_key != self.key():
                    raise UserError("先に硯の動きだけ試し、実物の動きを結果欄で確認してください。")
                for filename, digest in prepared["hashes"].items():
                    if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != digest:
                        raise UserError("確認後に経路ファイルが変更されています。確認し直してください。")
                args = ["play", *desk, *follower, "--settings", self.settings_path, "--motion", directory / "motion.npz", "--log", directory / "write.csv"]
                if name == "air-test":
                    args += ["--air-only"]
                commands.append(("検証した経路を実行します", self.command("gui_workflow.py", args, hardware=True)))
                # A prepared path is single-use, including after interruption.
                self.prepared = None
                self.ink_prepared = None
                record_directory = directory
                label = f"「{s['word']}」を書いています" if name == "write" else "空中で経路を試しています" if name == "air-test" else "硯の動作を試しています"
            elif name == "bilateral":
                if not self.status()["ready"]:
                    raise UserError("先に「準備」で較正を完了してください。")
                if not Path(s["leader_port"]).exists():
                    raise UserError("LeaderのUSBが見つかりません。両方のアームを接続してください。")
                directory = self.root / "runs/gui" / datetime.now().strftime("bilateral-%Y%m%d-%H%M%S-%f")
                record_directory = directory
                commands = [
                    ("LeaderをFollowerに合わせます", self.command("hardware_write.py", ["match-leader", *desk, *pair], hardware=True)),
                    ("バイラテラルを開始します", self.command("hardware_write.py", ["bilateral", *desk, *pair, "--log", directory / "write.csv"], hardware=True)),
                ]
                self.prepared = None
                label = "バイラテラルモード"
            elif name in ("camera-calibrate", "camera-detect"):
                if not s["camera_enabled"] or not self.status()["ready"]:
                    raise UserError("カメラを使用する設定にし、先に机の較正とサーボの同期を完了してください")
                if name == "camera-detect" and not (self.data / "camera-calibration.json").is_file():
                    raise UserError("先にカメラの基準を記録してください")
                # A failed new observation must never leave an older proposal actionable.
                (self.data / "camera-proposal.json").unlink(missing_ok=True)
                if name == "camera-calibrate":
                    (self.data / "camera-calibration.json").unlink(missing_ok=True)
                before, after = self.data / "camera-before.json", self.data / "camera-after.json"
                frame, overlay = self.data / "camera-frame.jpg", self.data / "camera-overlay.jpg"
                common = ["--desk", self.desk_path, "--before", before, "--after", after, "--image", frame, "--url", s["camera_url"],
                          "--calibration", self.data / "camera-calibration.json", "--proposal", self.data / "camera-proposal.json", "--overlay", overlay]
                commands = [
                    ("撮影前の腕の姿勢を読み取ります", self.command("gui_workflow.py", ["snapshot", *desk, *follower, "--out", before], hardware=True)),
                    ("カメラで撮影します", self.command("gui_camera.py", ["capture", "--url", s["camera_url"], "--image", frame])),
                    ("撮影後の腕の姿勢を読み取ります", self.command("gui_workflow.py", ["snapshot", *desk, *follower, "--out", after], hardware=True)),
                    ("目印と座標を検証します", self.command("gui_camera.py", ["calibrate" if name == "camera-calibrate" else "detect", *common])),
                ]
                label = "カメラの基準を記録" if name == "camera-calibrate" else "紙と硯を検出"
            elif name == "camera-apply":
                proposal = read_json(self.data / "camera-proposal.json", {})
                if proposal.get("desk_sha256") != hashlib.sha256(self.desk_path.read_bytes()).hexdigest():
                    raise UserError("先に現在の較正で紙と硯を検出してください")
                self.prepared = self.pressure_plan = self.ink_prepared = None
                commands = [("検出位置の逆運動学と机の較正を検証", self.command("gui_camera.py", ["apply", *desk, "--proposal", self.data / "camera-proposal.json"])), self.validation_command()]
                label = "検出位置を計算して反映"
            elif name == "camera-test":
                commands.append(("ESP32カメラの接続を確認", self.command("esp32_camera.py", ["health", s["camera_url"], "--timeout", "3"])))
                label = "カメラの接続確認"
            elif name == "esp-flash":
                port = str(payload.get("port", "")).strip()
                if port not in [str(p) for p in Path("/dev").glob("cu.usb*")]:
                    raise UserError("接続中のXIAO ESP32S3 SenseのUSBポートを指定してください")
                if port in (s["follower_port"], s["leader_port"]):
                    raise UserError("アームのUSBポートは指定できません。XIAOのポートを選んでください")
                cli = shutil.which("arduino-cli")
                if not cli:
                    raise UserError("arduino-cliが見つかりません。ArduinoのESP32開発環境が必要です")
                commands.append(("XIAO向けにビルドして書き込みます", [cli, "compile", "--fqbn", "esp32:esp32:XIAO_ESP32S3:PSRAM=opi", "--upload", "--port", port, str(self.root / "firmware/esp32-sense-mjpeg")]))
                label = "ESP32-S3に書き込み"
            elif name == "validate":
                commands.append(self.validation_command())
                label = "較正を検証中"
            elif name == "export-learning":
                if not self.last_run:
                    raise UserError("先にアームとロードセルのデータを記録してください")
                commands.append(("時刻と実物の評価を確認して学習用データを書き出す", self.command("export_gui_learning.py", [self.last_run, "--out", self.last_run / "learning"])))
                label = "学習用データを書き出し中"
            else:
                raise UserError("この操作はありません。")
            env = {**os.environ, "PYTHONPATH": str(self.root / "src") + os.pathsep + str(self.root), "PYTHONUNBUFFERED": "1"}
            if record_directory and s["loadcell_enabled"]:
                self.loadcell.begin_record(record_directory)
            if record_directory:
                self.last_run = record_directory
                write_json(record_directory / "session.json", {"action": name, "settings": s, "key": self.key(), "desk_sha256": hashlib.sha256(self.desk_path.read_bytes()).hexdigest(), "physical_result_reviewed": False})
            try:
                def finish(code, stopped):
                    self.loadcell.end_record()
                    if record_directory:
                        path = record_directory / "session.json"
                        session = read_json(path, {})
                        session["state"] = "done" if not code and not stopped else "aborted"
                        write_json(path, session)
                self.jobs.start(label, name, commands, env=env, success=success, interactive=interactive, finish=finish)
            except Exception:
                self.loadcell.end_record()
                raise

    def glyphs(self, word):
        if not 1 <= len(word) <= 2:
            raise UserError("1〜2文字を入力してください。")
        result = []
        for char in word:
            path = self.root / "data/kanjivg" / f"{ord(char):05x}.svg"
            paths = []
            if path.is_file():
                tree = ET.fromstring(path.read_text(encoding="utf-8"))
                paths = [p.attrib["d"] for p in tree.iter("{http://www.w3.org/2000/svg}path") if "d" in p.attrib]
            result.append({"char": char, "paths": paths})
        return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    @property
    def app(self):
        return self.server.console

    def send(self, data, content_type="application/json; charset=utf-8", status=200):
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def valid_host(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def do_GET(self):
        if not self.valid_host():
            return self.send({"error": "Invalid Host"}, status=403)
        path = urlsplit(self.path).path
        try:
            if path == "/api/state":
                return self.send({**self.app.status(), "token": self.app.token})
            if path == "/api/layout-preview":
                prepared = self.app.prepared
                if not prepared or prepared["key"] != self.app.key():
                    raise UserError("現在の軌道が未確認です")
                return self.send((prepared["directory"] / "trace.layout.svg").read_bytes(), "image/svg+xml")
            if path == "/api/camera":
                if not self.app.settings["camera_enabled"]:
                    raise UserError("カメラは使用しない設定です。")
                url = camera_url(self.app.settings["camera_url"]) + "/capture"
                with urlopen(Request(url, headers={"User-Agent": "syodo-gui/1"}), timeout=3) as response:
                    frame = response.read(4_000_001)
                if len(frame) > 4_000_000 or not frame.startswith(b"\xff\xd8") or not frame.endswith(b"\xff\xd9"):
                    raise UserError("カメラからJPEG画像を受信できません。")
                return self.send(frame, "image/jpeg")
            if path == "/api/camera-overlay":
                return self.send((self.app.data / "camera-overlay.jpg").read_bytes(), "image/jpeg")
            if path in ("/api/reference-side", "/api/reference-overview"):
                name = "sim-home-side.png" if path.endswith("side") else "sim-home-overview.png"
                image = self.app.data / name
                if not image.is_file():
                    raise UserError("先に基準画像を作成してください。")
                return self.send(image.read_bytes(), "image/png")
            files = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8"), "/arm-guide.svg": ("arm-guide.svg", "image/svg+xml"), "/brush-guide.svg": ("brush-guide.svg", "image/svg+xml"), "/camera-markers.svg": ("camera-markers.svg", "image/svg+xml"), "/camera-guide.svg": ("camera-guide.svg", "image/svg+xml")}
            if path in files:
                name, mime = files[path]
                return self.send((STATIC / name).read_bytes(), mime)
            self.send({"error": "Not found"}, status=404)
        except (UserError, OSError, ValueError) as exc:
            self.send({"error": str(exc)}, status=400)

    def do_POST(self):
        origin = self.headers.get("Origin")
        expected = f"http://127.0.0.1:{self.server.server_port}"
        if not self.valid_host() or (origin is not None and origin != expected) or not secrets.compare_digest(self.headers.get("X-Syodo-Token", ""), self.app.token):
            return self.send({"error": "Invalid request"}, status=403)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16000:
                raise UserError("リクエストが不正です。")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise UserError("リクエストが不正です。")
            path = urlsplit(self.path).path
            if path == "/api/settings":
                self.app.save(payload)
            elif path == "/api/action":
                self.app.action(payload.get("action"), payload)
            elif path == "/api/stop":
                self.app.jobs.stop()
            elif path == "/api/respond":
                self.app.jobs.respond(payload.get("id"), payload.get("value"))
            elif path == "/api/loadcell-calibrate":
                if self.app.jobs.active:
                    raise UserError("アームの動作中はロードセルの較正を変更できません")
                self.app.loadcell.calibrate(payload.get("action"), payload.get("mass_g"))
            elif path == "/api/review":
                if self.app.jobs.active or not self.app.last_run:
                    raise UserError("動作が終わってから結果を記録してください")
                if payload.get("result") not in ("good", "bad"):
                    raise UserError("良い・やり直しのどちらかを選んでください")
                write_json(self.app.last_run / "review.json", {"result": payload["result"], "source": "human", "physical_result_reviewed": True})
                session = read_json(self.app.last_run / "session.json", {})
                if session.get("key") == self.app.key() and session.get("state") == "done":
                    if session["action"] == "air-test":
                        self.app.air_verified_key = session["key"] if payload["result"] == "good" else None
                    if session["action"] == "ink-test":
                        self.app.ink_verified_key = session["key"] if payload["result"] == "good" else None
            elif path == "/api/glyphs":
                return self.send(self.app.glyphs(str(payload.get("word", ""))))
            else:
                return self.send({"error": "Not found"}, status=404)
            self.send(self.app.status())
        except (UserError, ValueError, TypeError, OSError) as exc:
            self.send({"error": str(exc)}, status=400)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    # Two windows may control one server; two servers must not own the same arm.
    import fcntl
    data = ROOT / "data/hardware/gui"
    data.mkdir(parents=True, exist_ok=True)
    lock_file = (data / "console.lock").open("a")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        running = read_json(data / "server.json", {})
        url = running.get("url", "http://127.0.0.1:8765")
        print(f"書道GUIは起動済みです: {url}")
        if not args.no_browser:
            webbrowser.open(url)
        return
    app = Console(data=data)
    app.loadcell.start()
    # Other desktop software can already use 8765. Keep the single-instance
    # lock, but select another local port instead of failing at startup.
    import errno
    server = None
    for port in (range(8765, 8796) if args.port == 8765 else [args.port]):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
    if server is None:
        app.loadcell.close()
        raise SystemExit("GUIの接続先ポートが見つかりません")
    server.console = app
    url = f"http://127.0.0.1:{server.server_port}"
    write_json(data / "server.json", {"url": url, "pid": os.getpid()})
    print(f"書道GUI: {url}\n終了: Ctrl+C", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        app.jobs.stop()
        if app.jobs.active:
            print("実行中の操作を停止しています…", flush=True)
            app.jobs.thread.join()
        app.loadcell.close()
        server.server_close()
        lock_file.close()


if __name__ == "__main__":
    main()
