"""Conservative ESP32 camera watchdog for real-hardware writing."""

from __future__ import annotations

import io
import json
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image, UnidentifiedImageError


@dataclass(frozen=True)
class CameraWatchdogConfig:
    interval_s: float = 0.5
    timeout_s: float = 1.5
    bad_frames: int = 3
    save_every: int = 1
    roi: tuple[float, float, float, float] = (0.08, 0.08, 0.92, 0.92)
    image_width: int = 160
    image_height: int = 120
    changed_pixel_delta: float = 28.0
    scene_delta_limit: float = 35.0
    outside_delta_limit: float = 18.0
    outside_changed_fraction_limit: float = 0.20
    paper_brightness_delta_limit: float = 50.0
    paper_changed_fraction_limit: float = 0.45

    def __post_init__(self) -> None:
        x0, y0, x1, y1 = self.roi
        if not (0.0 <= x0 < x1 <= 1.0 and 0.0 <= y0 < y1 <= 1.0):
            raise ValueError("camera ROI must be normalized x0,y0,x1,y1")
        if self.interval_s <= 0.0 or self.timeout_s <= 0.0:
            raise ValueError("camera timing must be positive")
        if self.bad_frames < 1 or self.save_every < 1:
            raise ValueError("camera frame counts must be at least one")
        if self.image_width < 2 or self.image_height < 2:
            raise ValueError("camera image size is too small")
        thresholds = (
            self.changed_pixel_delta,
            self.scene_delta_limit,
            self.outside_delta_limit,
            self.outside_changed_fraction_limit,
            self.paper_brightness_delta_limit,
            self.paper_changed_fraction_limit,
        )
        if any(value < 0.0 for value in thresholds):
            raise ValueError("camera thresholds must be non-negative")


def decode_jpeg(data: bytes, config: CameraWatchdogConfig) -> np.ndarray:
    if len(data) < 100 or not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise ValueError("camera response is not a complete JPEG")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            gray = image.convert("L").resize(
                (config.image_width, config.image_height), Image.Resampling.BILINEAR
            )
            return np.asarray(gray, dtype=np.float32)
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"camera JPEG cannot be decoded: {exc}") from exc


def analyze_frame(
    current: np.ndarray,
    baseline: np.ndarray,
    config: CameraWatchdogConfig,
) -> dict[str, object]:
    current = np.asarray(current, dtype=np.float32)
    baseline = np.asarray(baseline, dtype=np.float32)
    if current.shape != baseline.shape or current.ndim != 2:
        raise ValueError("camera frames must be equal-sized grayscale images")

    height, width = current.shape
    x0, y0, x1, y1 = config.roi
    left = int(round(x0 * width))
    top = int(round(y0 * height))
    right = int(round(x1 * width))
    bottom = int(round(y1 * height))
    inside = np.zeros(current.shape, dtype=bool)
    inside[top:bottom, left:right] = True
    outside = ~inside
    if not np.any(inside) or not np.any(outside):
        raise ValueError("camera ROI must leave both paper and surrounding pixels")

    delta = np.abs(current - baseline)
    changed = delta >= config.changed_pixel_delta
    scene_delta = float(np.mean(delta))
    outside_delta = float(np.mean(delta[outside]))
    outside_changed = float(np.mean(changed[outside]))
    paper_brightness_delta = float(abs(np.mean(current[inside]) - np.mean(baseline[inside])))
    paper_changed = float(np.mean(changed[inside]))

    reasons: list[str] = []
    if scene_delta >= config.scene_delta_limit and outside_changed >= 0.25:
        reasons.append("scene_shift")
    if (
        outside_delta >= config.outside_delta_limit
        and outside_changed >= config.outside_changed_fraction_limit
    ):
        reasons.append("outside_motion")
    if (
        paper_brightness_delta >= config.paper_brightness_delta_limit
        and paper_changed >= config.paper_changed_fraction_limit
    ):
        reasons.append("paper_obscured")
    return {
        "anomaly": bool(reasons),
        "reasons": reasons,
        "scene_delta": scene_delta,
        "outside_delta": outside_delta,
        "outside_changed_fraction": outside_changed,
        "paper_brightness_delta": paper_brightness_delta,
        "paper_changed_fraction": paper_changed,
    }


def _capture_url(base_url: str) -> str:
    value = base_url.rstrip("/")
    return value if value.endswith("/capture") else value + "/capture"


class CameraWatchdog:
    """Poll bounded JPEG requests, save evidence, and expose fail-safe state."""

    def __init__(
        self,
        base_url: str,
        run_dir: Path,
        *,
        config: CameraWatchdogConfig | None = None,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.capture_url = _capture_url(base_url)
        self.config = config or CameraWatchdogConfig()
        self.camera_dir = Path(run_dir) / "camera"
        self.frames_dir = self.camera_dir / "frames"
        self.metrics_path = self.camera_dir / "metrics.jsonl"
        self.summary_path = self.camera_dir / "camera.json"
        self._opener = opener
        self._lock = threading.Lock()
        self._capture_lock = threading.Lock()
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._baseline: np.ndarray | None = None
        self._latest_gray: np.ndarray | None = None
        self._latest_jpeg: bytes | None = None
        self._armed = False
        self._failure: dict[str, object] | None = None
        self._bad_streak = 0
        self._sample_count = 0
        self._saved_count = 0
        self._last_frame_time: float | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.camera_dir.joinpath("config.json").write_text(
            json.dumps(asdict(self.config), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._thread = threading.Thread(target=self._run, name="camera-watchdog", daemon=True)
        self._thread.start()

    def wait_ready(self, timeout_s: float = 5.0) -> bool:
        if self._ready.wait(timeout_s):
            return True
        self._set_failure("camera_start_timeout", f"no valid frame within {timeout_s:.1f}s")
        return False

    def arm(self) -> bool:
        try:
            baseline_jpeg = self._fetch()
            baseline_gray = decode_jpeg(baseline_jpeg, self.config)
        except Exception as exc:
            self._set_failure("camera_baseline_failed", f"{type(exc).__name__}: {exc}")
            return False
        with self._lock:
            if self._failure is not None:
                return False
            self._baseline = baseline_gray.copy()
            self._latest_gray = baseline_gray
            self._latest_jpeg = baseline_jpeg
            self._last_frame_time = time.time()
            self._armed = True
            self._bad_streak = 0
        self.camera_dir.joinpath("baseline.jpg").write_bytes(baseline_jpeg)
        self._record(baseline_jpeg, {"state": "baseline", "anomaly": False})
        return True

    def disarm(self) -> None:
        with self._lock:
            self._armed = False

    @property
    def failure(self) -> dict[str, object] | None:
        with self._lock:
            return None if self._failure is None else dict(self._failure)

    def summary(self) -> dict[str, object]:
        with self._lock:
            failure = None if self._failure is None else dict(self._failure)
            return {
                "enabled": True,
                "url": self.base_url,
                "status": "failed" if failure else ("armed" if self._armed else "ok"),
                "failure": failure,
                "samples": self._sample_count,
                "saved_frames": self._saved_count,
                "last_frame_time_s": self._last_frame_time,
                "directory": str(self.camera_dir),
            }

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.config.timeout_s + 2.0)
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        self.summary_path.write_text(
            json.dumps(self.summary(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _fetch(self) -> bytes:
        request = Request(self.capture_url, headers={"User-Agent": "syodo-camera-watchdog/1"})
        with self._capture_lock:
            with self._opener(request, timeout=self.config.timeout_s) as response:
                return response.read()

    def _set_failure(self, reason: str, detail: str) -> None:
        with self._lock:
            if self._failure is None:
                self._failure = {
                    "reason": reason,
                    "detail": detail,
                    "time_s": time.time(),
                    "bad_streak": self._bad_streak,
                }

    def _bad(self, reason: str, detail: str) -> None:
        with self._lock:
            self._bad_streak += 1
            streak = self._bad_streak
        if streak >= self.config.bad_frames:
            self._set_failure(reason, detail)

    def _good(self) -> None:
        with self._lock:
            self._bad_streak = 0

    def _write_metric(self, payload: dict[str, object]) -> None:
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with self.metrics_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _record(self, jpeg: bytes, metrics: dict[str, object]) -> None:
        with self._lock:
            index = self._sample_count
            self._sample_count += 1
            should_save = index % self.config.save_every == 0 or bool(metrics.get("anomaly"))
        frame_path: Path | None = None
        if should_save:
            frame_path = self.frames_dir / f"frame-{index:06d}.jpg"
            frame_path.write_bytes(jpeg)
            with self._lock:
                self._saved_count += 1
        row = {"time_s": time.time(), "index": index, **metrics}
        if frame_path is not None:
            row["frame"] = str(frame_path)
        self._write_metric(row)

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                jpeg = self._fetch()
                gray = decode_jpeg(jpeg, self.config)
            except Exception as exc:
                detail = f"{type(exc).__name__}: {exc}"
                self._write_metric(
                    {"time_s": time.time(), "state": "capture_error", "detail": detail}
                )
                self._bad("camera_unavailable", detail)
            else:
                now = time.time()
                with self._lock:
                    self._latest_gray = gray
                    self._latest_jpeg = jpeg
                    self._last_frame_time = now
                    baseline = None if self._baseline is None else self._baseline.copy()
                    armed = self._armed
                self._ready.set()
                metrics: dict[str, object] = {"state": "armed" if armed else "observe"}
                if armed and baseline is not None:
                    metrics.update(analyze_frame(gray, baseline, self.config))
                    if metrics["anomaly"]:
                        reasons = ",".join(str(value) for value in metrics["reasons"])
                        self._bad("visual_anomaly", reasons)
                    else:
                        self._good()
                else:
                    metrics["anomaly"] = False
                    self._good()
                self._record(jpeg, metrics)
            elapsed = time.monotonic() - started
            self._stop.wait(max(0.0, self.config.interval_s - elapsed))
