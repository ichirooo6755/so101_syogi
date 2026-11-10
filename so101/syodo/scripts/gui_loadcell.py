"""One HX711 at the brush mount; standard-library HTTP acquisition and evidence.

This is separate from the old four-corner plate. The scalar is force along the
sensor axis, including gravity/inertia; it is not a measured 3-D tip position.
"""
from __future__ import annotations
from collections import deque
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import statistics
import threading
import time
from urllib.request import urlopen
import uuid


def binding(settings):
    keys = ("camera_url", "brush_length_mm", "tuft_mm", "reach_mm")
    return hashlib.sha256(json.dumps({k: settings[k] for k in keys}, sort_keys=True).encode()).hexdigest()


def decode_sample(payload, sent, received):
    if payload.get("sensor") != "hx711-single" or payload.get("schema") != 1:
        raise ValueError("このESPには1個用ロードセルのファームウェアが必要です")
    if payload.get("ready") is not True or payload.get("saturated") is not False:
        raise ValueError("HX711が未応答、または値が飽和しています")
    raw = payload.get("raw_counts")
    if isinstance(raw, bool) or not isinstance(raw, int) or not -8388608 < raw < 8388607:
        raise ValueError("ロードセルの生値が不正です")
    sequence = payload.get("sequence")
    acquired, served = payload.get("device_time_us"), payload.get("server_time_us")
    if not payload.get("boot_id") or isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise ValueError("取得番号か起動識別子がありません")
    if not all(not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v) for v in (acquired, served)) or not 0 <= acquired <= served or served - acquired > 500000:
        raise ValueError("ロードセルの取得時刻が古いか不正です")
    age = (served - acquired) / 1e6
    return {**payload, "host_receive_monotonic_s": received,
            "host_sample_monotonic_s": (sent + received) / 2 - age,
            "clock_uncertainty_s": (received - sent) / 2,
            "timestamp_method": "http_round_trip_midpoint_minus_sample_age"}


class LoadCell:
    def __init__(self, calibration_path, settings, on_fault=None):
        self.path = Path(calibration_path)
        self.settings = settings
        self.on_fault = on_fault
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.samples = deque(maxlen=400)
        self.latest = None
        self.error = None
        self.calibration = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.recording = None
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        last = None
        while not self.stop_event.is_set():
            settings = self.settings()
            if not settings.get("loadcell_enabled"):
                self.stop_event.wait(.2)
                continue
            try:
                sent = time.monotonic()
                with urlopen(settings["camera_url"].rstrip("/") + "/force", timeout=.4) as response:
                    payload = json.loads(response.read(16000))
                sample = decode_sample(payload, sent, time.monotonic())
                identity = (sample["boot_id"], sample["sequence"])
                if last and identity[0] == last[0] and identity[1] < last[1]:
                    raise ValueError("ロードセルの取得番号が逆戻りしました")
                with self.lock:
                    if identity != last:
                        self.samples.append(sample)
                        self.latest = sample
                        last = identity
                        if self.recording:
                            self.recording.write(json.dumps({**sample, "force_session": self.session, "binding": binding(settings)}, allow_nan=False) + "\n")
                            self.recording.flush()
                    self.error = None
                status = self.status()
                if self.recording and (not status["valid"] or abs(status["axis_force_n"]) > settings["force_limit_n"]):
                    if self.on_fault:
                        self.on_fault("ロードセルの欠測・較正不一致、または力の上限超過を検出しました")
            except Exception as exc:
                with self.lock:
                    self.error = str(exc)
                if self.recording and self.on_fault:
                    self.on_fault("ロードセルの受信が途切れたため停止します: " + str(exc))
            self.stop_event.wait(.06)

    def status(self):
        with self.lock:
            s = self.settings()
            row = self.latest
            fresh = bool(row and time.monotonic() - row["host_receive_monotonic_s"] < .5 and not self.error)
            cal = self.calibration
            bound = bool(row and cal.get("binding") == binding(s) and cal.get("tare_boot_id") == row["boot_id"])
            valid = bool(fresh and bound and cal.get("validated") is True)
            force = (row["raw_counts"] - cal["zero_counts"]) * cal["newtons_per_count"] if valid else None
            return {"enabled": s.get("loadcell_enabled", False), "connected": fresh,
                    "valid": valid, "raw_counts": row["raw_counts"] if fresh else None,
                    "axis_force_n": force, "mass_equivalent_g": force / 9.80665 * 1000 if force is not None else None,
                    "error": self.error, "calibration": deepcopy(cal),
                    "clock_uncertainty_s": row["clock_uncertainty_s"] if fresh else None,
                    "normal_force_measured": False, "recording": bool(self.recording)}

    def mean(self):
        with self.lock:
            now = time.monotonic()
            rows = [r for r in self.samples if now - r["host_receive_monotonic_s"] < 3]
            if len(rows) < 12 or self.error or not self.status()["connected"]:
                raise ValueError("同じ姿勢で静止し、12回以上の新しい計測を待ってください")
            rows = rows[-20:]
            if len({r["boot_id"] for r in rows}) != 1:
                raise ValueError("ESPが再起動しました。ゼロ点から取り直してください")
            raw = [r["raw_counts"] for r in rows]
            return statistics.mean(raw), statistics.pstdev(raw), rows[-1]

    def calibrate(self, action, mass_g=None):
        mean, deviation, row = self.mean()
        with self.lock:
            cal = dict(self.calibration)
            if action == "tare":
                cal = {"schema": 1, "binding": binding(self.settings()), "tare_boot_id": row["boot_id"],
                       "zero_counts": mean, "tare_std_counts": deviation, "validated": False,
                       "tare_sequence": row["sequence"], "source": "measured"}
            else:
                if cal.get("binding") != binding(self.settings()) or cal.get("tare_boot_id") != row["boot_id"]:
                    raise ValueError("まず筆を紙から離し、同じ姿勢でゼロ点を取ってください")
                mass_g = float(mass_g)
                if not math.isfinite(mass_g) or not 5 <= mass_g <= 500:
                    raise ValueError("既知の重りは5〜500 gで入力してください")
                if row["sequence"] <= cal.get("tare_sequence", 0) + 12:
                    raise ValueError("重りを載せ、値が落ち着いてから実行してください")
                if action == "gain":
                    delta = mean - cal["zero_counts"]
                    if abs(delta) < max(20, 10 * deviation, 10 * cal["tare_std_counts"]):
                        raise ValueError("荷重の変化が小さすぎるか、計測が安定していません")
                    cal.update(newtons_per_count=mass_g * .00980665 / delta, mass_g=mass_g,
                               gain_sequence=row["sequence"], gain_counts=mean, validated=False)
                elif action == "verify":
                    if "newtons_per_count" not in cal or mass_g == cal.get("mass_g") or row["sequence"] <= cal.get("gain_sequence", 0) + 12:
                        raise ValueError("換算に使った重りとは別の重りに替え、落ち着いてから確認してください")
                    measured = (mean - cal["zero_counts"]) * cal["newtons_per_count"]
                    expected = mass_g * .00980665
                    error = abs(measured - expected)
                    if error > max(.02, expected * .05):
                        raise ValueError(f"確認用の重りと一致しません（誤差{error:.3f} N）。較正を取り直してください")
                    cal.update(validated=True, validation_mass_g=mass_g, validation_error_n=error)
                else:
                    raise ValueError("較正の操作が不正です")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(cal, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
            temporary.replace(self.path)
            self.calibration = cal

    def begin_record(self, directory):
        if not self.status()["valid"]:
            raise ValueError("ロードセルを使うにはゼロ点・既知の重り・別の重りでの確認が必要です")
        with self.lock:
            path = Path(directory) / "loadcell.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            self.recording = path.open("x")
            self.session = uuid.uuid4().hex
            self.recording.write(json.dumps({"event": "session", "force_session": self.session,
                "calibration": self.calibration, "direction": "sensor_axis_including_gravity_and_inertia"}) + "\n")

    def end_record(self):
        with self.lock:
            if self.recording:
                self.recording.close()
                self.recording = None

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(2)
        self.end_record()
