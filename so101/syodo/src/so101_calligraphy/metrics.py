"""Transparent geometry and line-quality metrics for calligraphy episodes."""

from __future__ import annotations

import numpy as np
from PIL import Image

from so101_calligraphy.width_metrics import evaluate_width_profile


BEAUTY_COMPONENT_WEIGHTS = {
    "glyph_shape": 0.17,
    "stroke_placement": 0.06,
    "stroke_length": 0.04,
    "stroke_angle": 0.05,
    "line_width": 0.14,
    "trajectory": 0.10,
    "stroke_order": 0.02,
    "smoothness": 0.02,
    "brushwork": 0.20,
    "ink_quality": 0.05,
    "ink_loading": 0.03,
    "drip_control": 0.02,
    "collision_safety": 0.05,
    "balance": 0.05,
}

# Previous aggregate weights kept for ablation / before-after rescoring.
LEGACY_BEAUTY_COMPONENT_WEIGHTS = {
    "glyph_shape": 0.14,
    "stroke_placement": 0.06,
    "stroke_length": 0.04,
    "stroke_angle": 0.04,
    "line_width": 0.14,
    "trajectory": 0.09,
    "stroke_order": 0.05,
    "smoothness": 0.06,
    "brushwork": 0.14,
    "ink_quality": 0.05,
    "ink_loading": 0.03,
    "drip_control": 0.06,
    "collision_safety": 0.05,
    "balance": 0.05,
}

# Exported on stroke/character evaluations; gated separately from beauty weights.
WIDTH_DETAIL_KEYS = (
    "width_scale",
    "width_contrast",
    "taper",
    "corner_width",
    "width_smoothness",
)


def endpoint_shape_quality(
    actual_patch: np.ndarray,
    target_patch: np.ndarray,
) -> dict[str, float]:
    """Compare one exposed stroke end with its tangent-aligned teacher patch."""

    actual = np.clip(np.asarray(actual_patch, dtype=np.float64), 0.0, 1.0)
    target = np.clip(np.asarray(target_patch, dtype=np.float64), 0.0, 1.0)
    if actual.shape != target.shape or actual.ndim != 2 or not actual.size:
        raise ValueError("endpoint patches must be equally sized non-empty 2-D arrays")
    union = float(np.maximum(actual, target).sum())
    iou = float(np.minimum(actual, target).sum() / max(union, 1e-9))
    actual_profile = actual.mean(axis=1)
    target_profile = target.mean(axis=1)
    scale = max(float(target_profile.max()), 0.05)
    envelope_error = float(np.mean(np.abs(actual_profile - target_profile)) / scale)
    envelope = float(np.exp(-((envelope_error / 0.50) ** 2)))
    tip_rows = max(1, len(actual_profile) // 4)
    actual_body_raw = float(actual_profile[-tip_rows:].mean())
    target_body_raw = float(target_profile[-tip_rows:].mean())
    actual_body = max(actual_body_raw, 0.05)
    target_body = max(target_body_raw, 0.05)
    actual_tip_ratio = float(actual_profile[:tip_rows].mean()) / actual_body
    target_tip_ratio = float(target_profile[:tip_rows].mean()) / target_body
    tip_error = abs(actual_tip_ratio - target_tip_ratio)
    tip = float(np.exp(-((tip_error / 0.50) ** 2)))
    # IoU remains the main contract; the two profiles distinguish a real wedge
    # from a rounded cap without letting a one-pixel apex dominate the score.
    score = 0.75 * iou + 0.20 * envelope + 0.05 * tip
    # A pointed exposed end has much less ink outside the authored endpoint
    # than in the inner body. This is deliberately teacher-independent: some
    # fonts draw a blunt stop even though the attachment is being calibrated
    # specifically for the triangular real-brush endpoint.
    body_presence = float(np.clip(actual_body_raw / max(target_body_raw, 0.05), 0.0, 1.0))
    wedge = float(np.exp(-actual_tip_ratio / 0.60) * body_presence)
    return {
        "score": score,
        "iou": iou,
        "envelope": envelope,
        "tip": tip,
        "wedge": wedge,
        "body_presence": body_presence,
        "actual_tip_ratio": actual_tip_ratio,
        "target_tip_ratio": target_tip_ratio,
    }


def symmetric_chamfer(first: np.ndarray, second: np.ndarray) -> float:
    if len(first) == 0 or len(second) == 0:
        return float("inf")
    distances = np.linalg.norm(first[:, None, :] - second[None, :, :], axis=2)
    return float(0.5 * (distances.min(axis=1).mean() + distances.min(axis=0).mean()))


def discrete_frechet(first: np.ndarray, second: np.ndarray) -> float:
    """Discrete Fréchet distance without a SciPy dependency."""

    if len(first) == 0 or len(second) == 0:
        return float("inf")
    previous = np.full(len(second), np.inf, dtype=np.float64)
    for row, point in enumerate(first):
        current = np.full(len(second), np.inf, dtype=np.float64)
        for column, other in enumerate(second):
            distance = float(np.linalg.norm(point - other))
            if row == 0 and column == 0:
                current[column] = distance
            elif row == 0:
                current[column] = max(current[column - 1], distance)
            elif column == 0:
                current[column] = max(previous[column], distance)
            else:
                current[column] = max(
                    min(previous[column], previous[column - 1], current[column - 1]),
                    distance,
                )
        previous = current
    return float(previous[-1])


def _resample_to(
    actual_progress: np.ndarray,
    actual: np.ndarray,
    target_progress: np.ndarray,
) -> np.ndarray:
    """実測を進捗軸で目標グリッドへ内挿する。

    実測は制御ステップ単位（1 画あたり 100-190 点）、目標はウェイポイント単位
    （同 20-28 点）で長さが構造的に一致しない。他の成分は `_profile_error` が
    内挿して吸収しているが、`evaluate_width_profile` は同長を要求するため
    毎回 ValueError で落ち、フォールバックが使われていた（幅の詳細評価が
    一度も動いていなかった）。
    """

    if len(actual) == 0:
        return np.zeros_like(target_progress)
    order = np.argsort(actual_progress)
    sorted_progress = actual_progress[order]
    sorted_actual = actual[order]
    unique_progress, inverse = np.unique(sorted_progress, return_inverse=True)
    totals = np.bincount(inverse, weights=sorted_actual)
    counts = np.bincount(inverse)
    unique_actual = totals / np.maximum(counts, 1)
    if len(unique_progress) == 1:
        return np.full_like(target_progress, unique_actual[0], dtype=np.float64)
    return np.interp(target_progress, unique_progress, unique_actual)


def _profile_error(
    actual_progress: np.ndarray,
    actual: np.ndarray,
    target_progress: np.ndarray,
    target: np.ndarray,
    scale: float,
) -> float:
    if len(actual) == 0:
        return 1.0
    order = np.argsort(actual_progress)
    sorted_progress = actual_progress[order]
    sorted_actual = actual[order]
    unique_progress = np.unique(sorted_progress)
    unique_actual = np.asarray(
        [sorted_actual[sorted_progress == value].mean() for value in unique_progress]
    )
    if len(unique_progress) == 1:
        interpolated = np.full_like(target, unique_actual[0])
    else:
        interpolated = np.interp(target_progress, unique_progress, unique_actual)
    return float(np.mean(np.abs(interpolated - target)) / max(scale, 1e-9))


def stroke_quality(
    *,
    actual_points: np.ndarray,
    actual_progress: np.ndarray,
    actual_width: np.ndarray,
    actual_pressure: np.ndarray,
    actual_speed: np.ndarray,
    target_points: np.ndarray,
    target_progress: np.ndarray,
    target_width: np.ndarray,
    target_pressure: np.ndarray,
    target_speed: np.ndarray,
    target_tangent: np.ndarray,
    technique: str,
    curvature: np.ndarray | None = None,
) -> dict[str, float]:
    """Score one finished stroke; all component scores are in [0, 1]."""

    if len(actual_points) < 2:
        return {
            "shape": 0.0,
            "frechet": 0.0,
            "placement": 0.0,
            "length": 0.0,
            "angle": 0.0,
            "width": 0.0,
            "pressure": 0.0,
            "speed": 0.0,
            "finish": 0.0,
            "score": 0.0,
            **{name: 0.0 for name in WIDTH_DETAIL_KEYS},
        }

    chamfer_distance = symmetric_chamfer(actual_points, target_points)
    frechet_distance = discrete_frechet(actual_points, target_points)
    shape = float(np.exp(-((chamfer_distance / 0.009) ** 2)))
    frechet = float(np.exp(-((frechet_distance / 0.016) ** 2)))
    placement_error = float(
        np.linalg.norm(actual_points.mean(axis=0) - target_points.mean(axis=0))
    )
    placement = float(np.exp(-((placement_error / 0.015) ** 2)))

    def arc_length(points: np.ndarray) -> float:
        return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())

    actual_length = max(arc_length(actual_points), 1e-9)
    target_length = max(arc_length(target_points), 1e-9)
    length = float(np.exp(-((np.log(actual_length / target_length) / 0.32) ** 2)))
    actual_direction = actual_points[-1] - actual_points[0]
    target_direction = target_points[-1] - target_points[0]
    if min(np.linalg.norm(actual_direction), np.linalg.norm(target_direction)) < 1e-8:
        angle = 0.0
    else:
        actual_direction /= np.linalg.norm(actual_direction)
        target_direction /= np.linalg.norm(target_direction)
        angle_error = float(
            np.arccos(np.clip(np.dot(actual_direction, target_direction), -1.0, 1.0))
        )
        angle = float(np.exp(-((angle_error / np.deg2rad(22.0)) ** 2)))
    width_error = _profile_error(
        actual_progress,
        actual_width,
        target_progress,
        target_width,
        max(float(np.max(target_width)), 1e-9),
    )
    pressure_error = _profile_error(
        actual_progress, actual_pressure, target_progress, target_pressure, 1.0
    )
    speed_error = _profile_error(
        actual_progress,
        actual_speed,
        target_progress,
        target_speed,
        max(float(np.max(target_speed)), 1e-9),
    )
    profile_width_score = float(np.exp(-((width_error / 0.28) ** 2)))
    pressure_score = float(np.exp(-((pressure_error / 0.30) ** 2)))
    speed_score = float(np.exp(-((speed_error / 0.55) ** 2)))
    try:
        # 実測を目標の進捗グリッドへ内挿してから渡す。curvature は目標側の
        # 系列なので、これで 3 つの長さが揃う。
        width_details = evaluate_width_profile(
            actual_width=_resample_to(actual_progress, actual_width, target_progress),
            target_width=target_width,
            progress=target_progress,
            technique=technique,
            curvature=curvature,
        )
    except ValueError:
        width_details = {
            "width_scale": profile_width_score,
            "width_contrast": profile_width_score,
            "taper": profile_width_score,
            "corner_width": 1.0,
            "width_smoothness": profile_width_score,
            "score": profile_width_score,
        }
    width_score = float(
        0.40 * profile_width_score + 0.60 * float(width_details["score"])
    )

    tail_count = max(1, min(3, len(actual_width)))
    tail_width = float(np.mean(actual_width[-tail_count:]))
    middle = actual_width[
        max(0, len(actual_width) // 3) : max(1, 2 * len(actual_width) // 3)
    ]
    body_width = max(float(np.median(middle)), 1e-6)
    tail_pressure = float(np.mean(actual_pressure[-tail_count:]))
    tail_speed = float(np.mean(actual_speed[-tail_count:]))
    target_tail_count = max(1, min(3, len(target_width)))
    target_tail_width = float(np.mean(target_width[-target_tail_count:]))
    target_tail_pressure = float(np.mean(target_pressure[-target_tail_count:]))
    target_tail_speed = float(np.mean(target_speed[-target_tail_count:]))
    terminal_width = float(
        np.exp(
            -(
                (tail_width - target_tail_width)
                / max(0.32 * body_width, 0.0012)
            )
            ** 2
        )
    )
    terminal_pressure = float(
        np.exp(-(((tail_pressure - target_tail_pressure) / 0.24) ** 2))
    )
    terminal_speed = float(
        np.exp(-(((tail_speed - target_tail_speed) / 0.065) ** 2))
    )
    movement = actual_points[-1] - actual_points[max(0, len(actual_points) - 3)]
    if np.linalg.norm(movement) > 1e-8:
        movement /= np.linalg.norm(movement)
    alignment = float(np.clip(np.dot(movement, target_tangent), -1.0, 1.0))

    if technique == "tome":
        width_bloat = tail_width / body_width
        stop_clean = float(
            np.exp(-((max(width_bloat - 1.08, 0.0) / 0.18) ** 2))
        )
        finish = float(
            0.32 * terminal_width
            + 0.22 * terminal_pressure
            + 0.18 * terminal_speed
            + 0.28 * stop_clean
        )
    else:
        outgoing = 0.5 + 0.5 * alignment
        finish = float(
            0.30 * terminal_width
            + 0.24 * terminal_pressure
            + 0.18 * terminal_speed
            + 0.28 * outgoing
        )

    score = float(
        0.17 * shape
        + 0.12 * frechet
        + 0.08 * placement
        + 0.06 * length
        + 0.06 * angle
        + 0.16 * width_score
        + 0.11 * pressure_score
        + 0.07 * speed_score
        + 0.17 * finish
    )
    return {
        "shape": shape,
        "frechet": frechet,
        "placement": placement,
        "length": length,
        "angle": angle,
        "width": width_score,
        "pressure": pressure_score,
        "speed": speed_score,
        "finish": finish,
        "score": score,
        **{name: float(width_details[name]) for name in WIDTH_DETAIL_KEYS},
    }


def character_balance(ink_points: np.ndarray, target_points: np.ndarray) -> dict[str, float]:
    if len(ink_points) < 3 or len(target_points) < 3:
        return {"centroid": 0.0, "scale": 0.0, "tilt": 0.0, "score": 0.0}
    ink_center = ink_points.mean(axis=0)
    target_center = target_points.mean(axis=0)
    centroid = float(np.exp(-((np.linalg.norm(ink_center - target_center) / 0.020) ** 2)))

    ink_extent = np.maximum(np.ptp(ink_points, axis=0), 1e-6)
    target_extent = np.maximum(np.ptp(target_points, axis=0), 1e-6)
    log_ratio = np.log(ink_extent / target_extent)
    scale = float(np.exp(-np.mean(np.square(log_ratio)) / 0.35**2))

    def covariance(points: np.ndarray) -> np.ndarray:
        centered = points - points.mean(axis=0)
        matrix = centered.T @ centered / max(len(points) - 1, 1)
        return matrix / max(float(np.trace(matrix)), 1e-12)

    covariance_error = np.linalg.norm(covariance(ink_points) - covariance(target_points))
    tilt = float(np.exp(-((covariance_error / 0.45) ** 2)))
    return {
        "centroid": centroid,
        "scale": scale,
        "tilt": tilt,
        "score": float(0.45 * centroid + 0.30 * scale + 0.25 * tilt),
    }


def _block_mean(mask: np.ndarray, block: int) -> np.ndarray:
    rows = mask.shape[0] // block * block
    columns = mask.shape[1] // block * block
    cropped = mask[:rows, :columns]
    return cropped.reshape(rows // block, block, columns // block, block).mean(
        axis=(1, 3)
    )


def normalize_glyph_mask(mask: np.ndarray, resolution: int = 192) -> np.ndarray:
    """Crop and scale a glyph to a common critic canvas, preserving aspect."""

    source = np.clip(np.asarray(mask, dtype=np.float64), 0.0, 1.0)
    if source.ndim != 2:
        raise ValueError("Glyph mask must be 2-D.")
    rows, columns = np.nonzero(source > 0.03)
    result = np.zeros((resolution, resolution), dtype=np.float64)
    if len(rows) == 0:
        return result
    cropped = source[rows.min() : rows.max() + 1, columns.min() : columns.max() + 1]
    available = max(2, resolution - 24)
    scale = min(available / cropped.shape[1], available / cropped.shape[0])
    width = max(1, int(round(cropped.shape[1] * scale)))
    height = max(1, int(round(cropped.shape[0] * scale)))
    resized = np.asarray(
        Image.fromarray(np.uint8(cropped * 255.0)).resize(
            (width, height), Image.Resampling.LANCZOS
        ),
        dtype=np.float64,
    ) / 255.0
    row = (resolution - height) // 2
    column = (resolution - width) // 2
    result[row : row + height, column : column + width] = resized
    return result


def glyph_mask_quality(actual: np.ndarray, target: np.ndarray) -> dict[str, float]:
    """Multiscale soft-mask and negative-space agreement in [0, 1]."""

    actual = np.clip(np.asarray(actual, dtype=np.float64), 0.0, 1.0)
    target = np.clip(np.asarray(target, dtype=np.float64), 0.0, 1.0)
    if actual.shape != target.shape or actual.ndim != 2:
        raise ValueError("Glyph masks must be same-shaped 2-D arrays.")
    if max(float(actual.max()), float(target.max())) <= 0.0:
        return {"iou": 0.0, "dice": 0.0, "negative_space": 0.0, "score": 0.0}

    actual = normalize_glyph_mask(actual)
    target = normalize_glyph_mask(target)
    scale_ious: list[float] = []
    for block in (1, 2, 4):
        first = _block_mean(actual, block)
        second = _block_mean(target, block)
        intersection = np.minimum(first, second).sum()
        union = np.maximum(first, second).sum()
        scale_ious.append(float(intersection / max(float(union), 1e-9)))
    intersection = np.minimum(actual, target).sum()
    dice = float(
        2.0 * intersection / max(float(actual.sum() + target.sum()), 1e-9)
    )
    first_blocks = _block_mean(actual, 16)
    second_blocks = _block_mean(target, 16)
    negative_space = float(
        np.exp(-np.mean(np.abs(first_blocks - second_blocks)) / 0.18)
    )
    iou = float(np.mean(scale_ious))
    return {
        "iou": iou,
        "dice": dice,
        "negative_space": negative_space,
        "score": float(0.52 * iou + 0.33 * dice + 0.15 * negative_space),
    }


def smooth_motion_quality(
    tip_velocity: np.ndarray,
    joint_acceleration: np.ndarray,
) -> dict[str, float]:
    """Score expert-like low jerk and stable vertical brush motion."""

    velocity = np.asarray(tip_velocity, dtype=np.float64).reshape(-1, 3)
    acceleration = np.asarray(joint_acceleration, dtype=np.float64)
    if len(velocity) < 4 or len(acceleration) < 3:
        return {"tip_jerk": 0.0, "joint_jerk": 0.0, "vertical": 0.0, "score": 0.0}
    tip_jerk_rms = float(np.sqrt(np.mean(np.square(np.diff(velocity, n=2, axis=0)))))
    joint_jerk_rms = float(
        np.sqrt(np.mean(np.square(np.diff(acceleration, axis=0))))
    )
    vertical_variation = float(np.std(velocity[:, 2]))
    tip_score = float(np.exp(-((tip_jerk_rms / 0.045) ** 2)))
    joint_score = float(np.exp(-((joint_jerk_rms / 35.0) ** 2)))
    vertical_score = float(np.exp(-((vertical_variation / 0.12) ** 2)))
    return {
        "tip_jerk": tip_score,
        "joint_jerk": joint_score,
        "vertical": vertical_score,
        "score": float(0.42 * tip_score + 0.36 * joint_score + 0.22 * vertical_score),
    }


def aggregate_beauty_components(
    components: dict[str, float],
    *,
    weights: dict[str, float] | None = None,
) -> tuple[float, dict[str, float]]:
    """Return fixed aggregate and visible 0–100 component scores."""

    weight_map = BEAUTY_COMPONENT_WEIGHTS if weights is None else weights
    missing = set(weight_map) - components.keys()
    if missing:
        raise ValueError("Missing beauty components: " + ", ".join(sorted(missing)))
    normalized = {
        name: float(np.clip(components[name], 0.0, 1.0))
        for name in weight_map
    }
    total = 100.0 * sum(
        weight_map[name] * normalized[name] for name in weight_map
    )
    return float(total), {name: 100.0 * value for name, value in normalized.items()}
