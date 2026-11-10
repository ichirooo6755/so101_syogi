"""Kaisho stroke-family motion laws for joyo-wide brushwork."""

from __future__ import annotations

import numpy as np

from so101_calligraphy.brushwork import (
    ProfessionalBrushworkPlanner,
    classify_stroke_family,
)
from so101_calligraphy.config import BrushConfig
from so101_calligraphy.trajectory.types import Stroke


def _stroke(points: np.ndarray, stroke_type: str, technique: str = "auto") -> Stroke:
    return Stroke(points, stroke_type=stroke_type, technique=technique)


def test_classify_common_cjk_stroke_symbols() -> None:
    line = np.column_stack((np.linspace(0.0, 0.05, 8), np.zeros(8)))
    assert classify_stroke_family(_stroke(line, "㇐")) == "heng"
    assert classify_stroke_family(_stroke(line, "㇑a")) == "shu"
    assert classify_stroke_family(_stroke(line, "㇒")) == "pie"
    assert classify_stroke_family(_stroke(line, "㇏a")) == "na"
    assert classify_stroke_family(_stroke(line, "㇔")) == "dian"
    assert classify_stroke_family(_stroke(line, "㇀")) == "ti"
    assert classify_stroke_family(_stroke(line, "㇕a")) == "zhe"
    assert classify_stroke_family(_stroke(line, "㇆/㇚")) == "gou"


def test_families_expose_entry_send_finish_contrast() -> None:
    brush = BrushConfig()
    planner = ProfessionalBrushworkPlanner()
    samples = {
        "heng": (_stroke(np.column_stack((np.linspace(0, 0.08, 20), np.zeros(20))), "㇐", "tome"), "ends"),
        "shu": (
            _stroke(np.column_stack((np.zeros(20), np.linspace(0.04, -0.04, 20))), "㇑", "tome"),
            "ends",
        ),
        "pie": (
            _stroke(
                np.column_stack((np.linspace(0.04, -0.02, 20), np.linspace(0.03, -0.03, 20))),
                "㇒",
                "harai",
            ),
            "release",
        ),
        "na": (
            _stroke(
                np.column_stack((np.linspace(-0.02, 0.05, 20), np.linspace(0.03, -0.03, 20))),
                "㇏",
                "harai",
            ),
            "release",
        ),
        "dian": (
            _stroke(
                np.column_stack((np.linspace(0.0, 0.008, 8), np.linspace(0.0, -0.006, 8))),
                "㇔",
                "tome",
            ),
            "entry",
        ),
        "gou": (
            _stroke(
                np.column_stack((np.zeros(20), np.linspace(0.04, -0.02, 20))),
                "㇚",
                "hane",
            ),
            "release",
        ),
    }
    for family, (stroke, pattern) in samples.items():
        profile = planner.plan(stroke, brush)
        assert profile.stroke_family == family
        entry = float(np.mean(profile.pressure[profile.progress <= 0.12]))
        mid = float(
            np.mean(profile.pressure[(profile.progress >= 0.35) & (profile.progress <= 0.60)])
        )
        finish = float(np.mean(profile.pressure[profile.progress >= 0.88]))
        assert entry > 0.30, family
        if pattern == "ends":
            assert entry > mid * 0.95, family
            assert finish > mid, family
        elif pattern == "entry":
            assert entry >= mid, family
            assert np.ptp(profile.pressure) > 0.15, family
        else:
            assert finish < mid * 0.85, family
        assert np.linalg.norm(profile.path_delta[0]) > 0.0008, family
