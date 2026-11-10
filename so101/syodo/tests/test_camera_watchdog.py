from __future__ import annotations

import io

import numpy as np
from PIL import Image

from so101_calligraphy.camera_watchdog import (
    CameraWatchdog,
    CameraWatchdogConfig,
    analyze_frame,
    decode_jpeg,
)


def _jpeg(value: int = 200) -> bytes:
    stream = io.BytesIO()
    Image.new("L", (32, 24), value).save(stream, format="JPEG")
    return stream.getvalue()


def test_camera_frame_analysis_is_quiet_for_stable_image_and_flags_gross_changes() -> None:
    config = CameraWatchdogConfig(roi=(0.2, 0.2, 0.8, 0.8))
    baseline = np.full((120, 160), 200.0, dtype=np.float32)
    assert analyze_frame(baseline.copy(), baseline, config)["anomaly"] is False

    outside = baseline.copy()
    outside[:24] = 0.0
    outside[-24:] = 0.0
    result = analyze_frame(outside, baseline, config)
    assert result["anomaly"] is True
    assert "outside_motion" in result["reasons"]

    covered = baseline.copy()
    covered[24:96, 32:128] = 0.0
    result = analyze_frame(covered, baseline, config)
    assert result["anomaly"] is True
    assert "paper_obscured" in result["reasons"]


def test_camera_watchdog_decodes_jpeg_and_fails_closed_on_bad_frames(tmp_path) -> None:
    config = CameraWatchdogConfig(interval_s=0.01, timeout_s=0.05, bad_frames=2)
    decoded = decode_jpeg(_jpeg(), config)
    assert decoded.shape == (120, 160)

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"not-a-jpeg"

    watchdog = CameraWatchdog(
        "http://camera.local",
        tmp_path,
        config=config,
        opener=lambda *_args, **_kwargs: Response(),
    )
    watchdog.start()
    assert not watchdog.wait_ready(0.2)
    watchdog.stop()
    assert watchdog.failure is not None
    assert watchdog.summary_path.is_file()
