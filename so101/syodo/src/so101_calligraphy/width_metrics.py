"""Explainable, scale-aware width metrics for kaisho stroke profiles.

The evaluator separates overall brush size from intra-stroke teian, terminal
release, corner control, and high-frequency instability.  It intentionally
uses only NumPy so it can run in training workers without optional packages.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


_GRID_SIZE = 65
_RELEASE_TECHNIQUES = frozenset({"harai", "hane", "pie", "na", "ti", "gou"})


def _score(error: float, tolerance: float) -> float:
    return float(np.clip(np.exp(-((error / tolerance) ** 2)), 0.0, 1.0))


def _as_vector(values: np.ndarray, name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float64)
    if vector.ndim != 1:
        raise ValueError(f"{name} must be a 1-D array.")
    if len(vector) < 4:
        raise ValueError(f"{name} must contain at least four samples.")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain only finite values.")
    return vector


def _prepare_profile(
    actual_width: np.ndarray,
    target_width: np.ndarray,
    progress: np.ndarray,
    curvature: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    actual = _as_vector(actual_width, "actual_width")
    target = _as_vector(target_width, "target_width")
    position = _as_vector(progress, "progress")
    if not (len(actual) == len(target) == len(position)):
        raise ValueError("actual_width, target_width, and progress must have equal lengths.")
    if np.any(actual <= 0.0) or np.any(target <= 0.0):
        raise ValueError("Width samples must be strictly positive.")

    bend = None
    if curvature is not None:
        bend = _as_vector(curvature, "curvature")
        if len(bend) != len(position):
            raise ValueError("curvature and progress must have equal lengths.")
        if np.any(bend < 0.0):
            raise ValueError("curvature must be non-negative.")

    order = np.argsort(position, kind="stable")
    position = position[order]
    actual = actual[order]
    target = target[order]
    if bend is not None:
        bend = bend[order]

    unique, inverse = np.unique(position, return_inverse=True)
    if len(unique) < 4 or unique[-1] <= unique[0]:
        raise ValueError("progress must contain at least four distinct values.")

    counts = np.bincount(inverse).astype(np.float64)

    def grouped(values: np.ndarray) -> np.ndarray:
        return np.bincount(inverse, weights=values) / counts

    actual = grouped(actual)
    target = grouped(target)
    if bend is not None:
        bend = grouped(bend)

    normalized_progress = (unique - unique[0]) / (unique[-1] - unique[0])
    grid = np.linspace(0.0, 1.0, _GRID_SIZE)
    actual = np.interp(grid, normalized_progress, actual)
    target = np.interp(grid, normalized_progress, target)
    if bend is not None:
        bend = np.interp(grid, normalized_progress, bend)
    return grid, actual, target, bend


def _profile_scales(actual: np.ndarray, target: np.ndarray) -> tuple[float, float]:
    return float(np.median(actual)), float(np.median(target))


def evaluate_width_profile(
    *,
    actual_width: np.ndarray,
    target_width: np.ndarray,
    progress: np.ndarray,
    technique: str,
    curvature: np.ndarray | None = None,
) -> dict[str, float]:
    """Evaluate one stroke's width behavior with scores in ``[0, 1]``.

    ``technique`` accepts finish labels such as ``tome``, ``harai``, and
    ``hane`` as well as release-oriented stroke-family labels.  Curvature is
    optional; without it, ``corner_width`` is neutral because no corner is
    observable.
    """

    if not isinstance(technique, str) or not technique.strip():
        raise ValueError("technique must be a non-empty string.")
    technique = technique.strip().lower()
    grid, actual, target, bend = _prepare_profile(
        actual_width, target_width, progress, curvature
    )
    actual_scale, target_scale = _profile_scales(actual, target)

    scale_error = abs(float(np.log(actual_scale / target_scale)))
    width_scale = _score(scale_error, 0.30)

    actual_shape = actual / actual_scale
    target_shape = target / target_scale
    contrast_error = float(np.sqrt(np.mean(np.square(actual_shape - target_shape))))
    width_contrast = _score(contrast_error, 0.20)

    body_mask = (grid >= 0.38) & (grid <= 0.62)
    prefinish_mask = (grid >= 0.62) & (grid <= 0.78)
    tail_mask = grid >= 0.88
    actual_body = float(np.median(actual[body_mask]))
    target_body = float(np.median(target[body_mask]))
    actual_tail = float(np.mean(actual[tail_mask]))
    target_tail = float(np.mean(target[tail_mask]))
    taper_error = abs(
        float(np.log((actual_tail / actual_body) / (target_tail / target_body)))
    )
    taper = _score(taper_error, 0.30)
    if technique in _RELEASE_TECHNIQUES:
        actual_prefinish = float(np.mean(actual[prefinish_mask]))
        target_prefinish = float(np.mean(target[prefinish_mask]))
        target_release = max(
            (target_prefinish - target_tail) / target_body,
            0.12,
        )
        actual_release = (actual_prefinish - actual_tail) / actual_body
        release_ratio = float(np.clip(actual_release / target_release, 0.0, 1.0))
        taper = float(np.sqrt(taper * release_ratio))

    corner_width = 1.0
    if bend is not None and float(np.max(bend)) >= 0.18:
        corner_threshold = max(0.18, 0.55 * float(np.max(bend)))
        corner_mask = bend >= corner_threshold
        corner_shape_error = float(
            np.sqrt(
                np.mean(
                    np.square(actual_shape[corner_mask] - target_shape[corner_mask])
                )
            )
        )
        actual_corner = float(np.mean(actual[corner_mask])) / actual_body
        target_corner = float(np.mean(target[corner_mask])) / target_body
        corner_ratio_error = abs(float(np.log(actual_corner / target_corner)))
        corner_width = float(
            np.sqrt(
                _score(corner_shape_error, 0.18)
                * _score(corner_ratio_error, 0.24)
            )
        )

    curvature_residual = np.diff(actual_shape - target_shape, n=2)
    smoothness_error = float(np.sqrt(np.mean(np.square(curvature_residual))))
    actual_variation = float(np.mean(np.abs(np.diff(actual_shape))))
    target_variation = float(np.mean(np.abs(np.diff(target_shape))))
    excess_variation = max(0.0, actual_variation - target_variation - 0.004)
    width_smoothness = float(
        np.sqrt(
            _score(smoothness_error, 0.035)
            * _score(excess_variation, 0.025)
        )
    )

    score = float(
        0.22 * width_scale
        + 0.25 * width_contrast
        + 0.18 * taper
        + 0.18 * corner_width
        + 0.17 * width_smoothness
    )
    return {
        "width_scale": width_scale,
        "width_contrast": width_contrast,
        "taper": taper,
        "corner_width": corner_width,
        "width_smoothness": width_smoothness,
        "score": float(np.clip(score, 0.0, 1.0)),
    }


def aggregate_width_hierarchy(
    *,
    actual_widths: Sequence[np.ndarray],
    target_widths: Sequence[np.ndarray],
    progresses: Sequence[np.ndarray],
    techniques: Sequence[str],
    curvatures: Sequence[np.ndarray | None] | None = None,
) -> dict[str, float]:
    """Aggregate profile scores and relative thick/thin hierarchy across strokes."""

    stroke_count = len(actual_widths)
    if stroke_count == 0:
        raise ValueError("At least one stroke is required.")
    if not (
        len(target_widths) == len(progresses) == len(techniques) == stroke_count
    ):
        raise ValueError("All stroke sequences must have equal lengths.")
    if curvatures is None:
        curvature_items: Sequence[np.ndarray | None] = [None] * stroke_count
    else:
        if len(curvatures) != stroke_count:
            raise ValueError("curvatures must match the number of strokes.")
        curvature_items = curvatures

    profiles: list[dict[str, float]] = []
    actual_scales: list[float] = []
    target_scales: list[float] = []
    for actual, target, position, technique, bend in zip(
        actual_widths,
        target_widths,
        progresses,
        techniques,
        curvature_items,
        strict=True,
    ):
        profiles.append(
            evaluate_width_profile(
                actual_width=actual,
                target_width=target,
                progress=position,
                technique=technique,
                curvature=bend,
            )
        )
        _, prepared_actual, prepared_target, _ = _prepare_profile(
            actual, target, position, bend
        )
        actual_scale, target_scale = _profile_scales(
            prepared_actual, prepared_target
        )
        actual_scales.append(actual_scale)
        target_scales.append(target_scale)

    log_scale_error = np.log(
        np.asarray(actual_scales, dtype=np.float64)
        / np.asarray(target_scales, dtype=np.float64)
    )
    relative_error = log_scale_error - float(np.mean(log_scale_error))
    hierarchy = _score(
        float(np.sqrt(np.mean(np.square(relative_error)))),
        0.22,
    )

    keys = (
        "width_scale",
        "width_contrast",
        "taper",
        "corner_width",
        "width_smoothness",
    )
    result = {
        key: float(np.mean([profile[key] for profile in profiles])) for key in keys
    }
    result["hierarchy"] = hierarchy
    result["score"] = float(
        np.clip(
            0.19 * result["width_scale"]
            + 0.22 * result["width_contrast"]
            + 0.15 * result["taper"]
            + 0.15 * result["corner_width"]
            + 0.14 * result["width_smoothness"]
            + 0.15 * hierarchy,
            0.0,
            1.0,
        )
    )
    return result
