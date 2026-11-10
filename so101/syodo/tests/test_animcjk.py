from __future__ import annotations

import json
import numpy as np

from so101_calligraphy.trajectory.animcjk import (
    ANIMCJK_REVISION,
    enrich_with_animcjk_widths,
)
from so101_calligraphy.trajectory.types import Stroke, Trajectory


def test_animcjk_outline_adds_width_profile(tmp_path) -> None:
    cache = tmp_path / f"graphicsJa-{ANIMCJK_REVISION[:12]}.txt"
    entry = {
        "character": "一",
        "strokes": ["M 0 40 L 100 40 L 100 60 L 0 60 Z"],
        "medians": [[[5, 50], [50, 50], [95, 50]]],
    }
    cache.write_text(json.dumps(entry) + "\n" + " " * 1_000_001, encoding="utf-8")
    points = np.asarray([[0.18, 0.0], [0.23, 0.0], [0.28, 0.0]])
    trajectory = Trajectory((Stroke(points, stroke_type="㇐"),), source="fixture")
    enriched = enrich_with_animcjk_widths(trajectory, "一", cache_dir=tmp_path)
    widths = enriched.strokes[0].widths
    assert widths is not None
    assert widths.shape == (3,)
    assert np.all(widths > 0)
    assert "AnimCJK" in enriched.source


def test_animcjk_can_replace_centerline_with_authored_japanese_median(tmp_path) -> None:
    cache = tmp_path / f"graphicsJa-{ANIMCJK_REVISION[:12]}.txt"
    entry = {
        "character": "一",
        "strokes": ["M 0 40 L 100 40 L 100 60 L 0 60 Z"],
        "medians": [[[5, 50], [50, 54], [95, 50]]],
    }
    cache.write_text(json.dumps(entry) + "\n" + " " * 1_000_001, encoding="utf-8")
    original = np.asarray([[0.18, 0.04], [0.23, 0.04], [0.28, 0.04]])
    trajectory = Trajectory((Stroke(original, stroke_type="㇐"),), source="fixture")

    enriched = enrich_with_animcjk_widths(
        trajectory,
        "一",
        cache_dir=tmp_path,
        use_medians=True,
        spacing=0.02,
    )

    points = enriched.strokes[0].points
    assert len(points) > len(original)
    assert abs(points[:, 1].mean()) < 0.01
    assert enriched.strokes[0].widths.shape == (len(points),)
    assert "Japanese medians/outlines" in enriched.source
