from __future__ import annotations

import numpy as np
import pytest

from so101_calligraphy.width_metrics import (
    aggregate_width_hierarchy,
    evaluate_width_profile,
)


def _ends_heavy_profile(progress: np.ndarray) -> np.ndarray:
    return 0.72 + 0.24 * np.cos(2.0 * np.pi * progress)


def test_matching_profile_scores_one_and_stays_bounded() -> None:
    progress = np.linspace(0.0, 1.0, 81)
    target = _ends_heavy_profile(progress)
    result = evaluate_width_profile(
        actual_width=target,
        target_width=target,
        progress=progress,
        technique="tome",
    )
    assert set(result) == {
        "width_scale",
        "width_contrast",
        "taper",
        "corner_width",
        "width_smoothness",
        "score",
    }
    assert all(0.0 <= value <= 1.0 for value in result.values())
    assert all(value == pytest.approx(1.0) for value in result.values())


def test_same_mean_sausage_profile_loses_contrast() -> None:
    progress = np.linspace(0.0, 1.0, 81)
    target = _ends_heavy_profile(progress)
    sausage = 0.72 - 0.24 * np.cos(2.0 * np.pi * progress)
    sausage *= np.mean(target) / np.mean(sausage)

    matching = evaluate_width_profile(
        actual_width=target,
        target_width=target,
        progress=progress,
        technique="tome",
    )
    distorted = evaluate_width_profile(
        actual_width=sausage,
        target_width=target,
        progress=progress,
        technique="tome",
    )
    assert np.mean(sausage) == pytest.approx(np.mean(target))
    assert distorted["width_scale"] > 0.95
    assert distorted["width_contrast"] < 0.20
    assert distorted["score"] < matching["score"] - 0.30


def test_failed_harai_release_loses_taper_even_at_same_mean() -> None:
    progress = np.linspace(0.0, 1.0, 101)
    target = np.full_like(progress, 0.86)
    release = progress >= 0.58
    target[release] = np.interp(progress[release], [0.58, 1.0], [0.86, 0.12])
    failed = np.full_like(target, np.mean(target))

    matching = evaluate_width_profile(
        actual_width=target,
        target_width=target,
        progress=progress,
        technique="harai",
    )
    distorted = evaluate_width_profile(
        actual_width=failed,
        target_width=target,
        progress=progress,
        technique="harai",
    )
    assert np.mean(failed) == pytest.approx(np.mean(target))
    assert matching["taper"] == pytest.approx(1.0)
    assert distorted["taper"] == pytest.approx(0.0)
    assert distorted["score"] < matching["score"] - 0.25


def test_corner_blob_loses_corner_width_score() -> None:
    progress = np.linspace(0.0, 1.0, 101)
    curvature = 0.62 * np.exp(-((progress - 0.5) / 0.035) ** 2)
    target = 0.72 + 0.15 * np.exp(-((progress - 0.5) / 0.055) ** 2)
    blob = 0.72 + 0.75 * np.exp(-((progress - 0.5) / 0.095) ** 2)
    blob *= np.mean(target) / np.mean(blob)

    matching = evaluate_width_profile(
        actual_width=target,
        target_width=target,
        progress=progress,
        technique="tome",
        curvature=curvature,
    )
    distorted = evaluate_width_profile(
        actual_width=blob,
        target_width=target,
        progress=progress,
        technique="tome",
        curvature=curvature,
    )
    assert np.mean(blob) == pytest.approx(np.mean(target))
    assert matching["corner_width"] == pytest.approx(1.0)
    assert distorted["corner_width"] < 0.10
    assert distorted["score"] < matching["score"] - 0.25


def test_high_frequency_width_vibration_loses_smoothness() -> None:
    progress = np.linspace(0.0, 1.0, 129)
    target = 0.76 + 0.08 * np.cos(2.0 * np.pi * progress)
    vibrating = target * (1.0 + 0.16 * np.sin(24.0 * np.pi * progress))
    vibrating *= np.mean(target) / np.mean(vibrating)

    matching = evaluate_width_profile(
        actual_width=target,
        target_width=target,
        progress=progress,
        technique="tome",
    )
    distorted = evaluate_width_profile(
        actual_width=vibrating,
        target_width=target,
        progress=progress,
        technique="tome",
    )
    assert np.mean(vibrating) == pytest.approx(np.mean(target))
    assert distorted["width_scale"] > 0.95
    assert distorted["width_smoothness"] < 0.10
    assert distorted["score"] < matching["score"] - 0.15


def test_hierarchy_ignores_global_scale_but_rejects_flattened_strokes() -> None:
    progress = np.linspace(0.0, 1.0, 65)
    shape = 0.90 + 0.10 * np.cos(2.0 * np.pi * progress)
    target_widths = [shape * scale for scale in (0.65, 1.0, 1.55)]
    proportional = [width * 1.25 for width in target_widths]
    flattened = [shape * np.median(target_widths[1]) for _ in target_widths]
    progresses = [progress] * 3
    techniques = ["tome"] * 3

    good = aggregate_width_hierarchy(
        actual_widths=proportional,
        target_widths=target_widths,
        progresses=progresses,
        techniques=techniques,
    )
    bad = aggregate_width_hierarchy(
        actual_widths=flattened,
        target_widths=target_widths,
        progresses=progresses,
        techniques=techniques,
    )
    assert all(0.0 <= value <= 1.0 for value in good.values())
    assert good["hierarchy"] == pytest.approx(1.0)
    assert bad["hierarchy"] < 0.10
    assert good["score"] > bad["score"]


def test_invalid_profiles_are_rejected() -> None:
    progress = np.linspace(0.0, 1.0, 8)
    with pytest.raises(ValueError, match="strictly positive"):
        evaluate_width_profile(
            actual_width=np.zeros(8),
            target_width=np.ones(8),
            progress=progress,
            technique="tome",
        )
    with pytest.raises(ValueError, match="equal lengths"):
        aggregate_width_hierarchy(
            actual_widths=[np.ones(8)],
            target_widths=[np.ones(8), np.ones(8)],
            progresses=[progress],
            techniques=["tome"],
        )
