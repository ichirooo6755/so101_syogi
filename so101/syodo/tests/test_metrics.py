from __future__ import annotations

import numpy as np

from so101_calligraphy.metrics import (
    aggregate_beauty_components,
    character_balance,
    discrete_frechet,
    glyph_mask_quality,
    smooth_motion_quality,
    stroke_quality,
    symmetric_chamfer,
)


def test_tome_finish_penalizes_terminal_width_bloat() -> None:
    progress = np.linspace(0.0, 1.0, 20)
    target_width = np.full(20, 0.006)
    clean_width = np.concatenate((target_width[:14], np.full(6, 0.0062)))
    bloated_width = np.concatenate((target_width[:14], np.full(6, 0.0095)))
    common = dict(
        actual_points=np.column_stack((np.linspace(0.0, 0.08, 20), np.zeros(20))),
        actual_progress=progress,
        actual_pressure=np.full(20, 0.42),
        actual_speed=np.full(20, 0.08),
        target_points=np.column_stack((np.linspace(0.0, 0.08, 20), np.zeros(20))),
        target_progress=progress,
        target_width=target_width,
        target_pressure=np.full(20, 0.42),
        target_speed=np.full(20, 0.08),
        target_tangent=np.asarray([1.0, 0.0]),
        technique="tome",
    )
    clean = stroke_quality(**common, actual_width=clean_width)
    bloated = stroke_quality(**common, actual_width=bloated_width)
    assert clean["finish"] > bloated["finish"]


def test_identical_paths_have_zero_shape_distance() -> None:
    points = np.asarray([[0.0, 0.0], [0.5, 0.1], [1.0, 0.0]])
    assert discrete_frechet(points, points) == 0.0
    assert symmetric_chamfer(points, points) == 0.0


def test_character_balance_prefers_matching_placement() -> None:
    target = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.5, 1.0], [0.5, 0.5]])
    matching = character_balance(target, target)
    shifted = character_balance(target + np.asarray([0.08, 0.0]), target)
    assert matching["score"] > shifted["score"]
    assert matching["score"] == 1.0


def test_professional_mask_and_motion_breakdown() -> None:
    target = np.zeros((32, 32))
    target[8:24, 13:19] = 1.0
    matching = glyph_mask_quality(target, target)
    distorted = target.copy()
    distorted[8:16, 5:27] = 1.0
    mismatch = glyph_mask_quality(distorted, target)
    assert matching["score"] > mismatch["score"]

    velocity = np.column_stack((np.linspace(0, 0.1, 20), np.zeros((20, 2))))
    acceleration = np.zeros((20, 6))
    motion = smooth_motion_quality(velocity, acceleration)
    components = {
        "glyph_shape": matching["score"],
        "stroke_placement": 1.0,
        "stroke_length": 1.0,
        "stroke_angle": 1.0,
        "line_width": 1.0,
        "trajectory": 1.0,
        "stroke_order": 1.0,
        "smoothness": motion["score"],
        "brushwork": 1.0,
        "ink_quality": 1.0,
        "ink_loading": 1.0,
        "drip_control": 1.0,
        "collision_safety": 1.0,
        "balance": 1.0,
    }
    score, breakdown = aggregate_beauty_components(components)
    assert 0.0 < score <= 100.0
    assert set(breakdown) == set(components)
