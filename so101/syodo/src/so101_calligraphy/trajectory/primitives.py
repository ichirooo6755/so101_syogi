"""Small geometry curriculum used before arbitrary SVG characters."""

from __future__ import annotations

import numpy as np

from so101_calligraphy.config import PaperConfig
from so101_calligraphy.trajectory.types import Stroke, Trajectory


PRIMITIVE_NAMES = ("line", "circle", "cross")


def _line_points(start: np.ndarray, end: np.ndarray, spacing: float) -> np.ndarray:
    distance = float(np.linalg.norm(end - start))
    count = max(2, int(np.ceil(distance / spacing)) + 1)
    return np.linspace(start, end, count, dtype=np.float64)


def primitive_trajectory(
    name: str,
    *,
    paper: PaperConfig | None = None,
    spacing: float = 0.008,
) -> Trajectory:
    """Return line, circle, or two-stroke cross in A4 world coordinates."""

    paper = paper or PaperConfig()
    if spacing <= 0:
        raise ValueError("spacing must be positive")

    center = np.asarray([paper.center_x, paper.center_y], dtype=np.float64)
    half_span = 0.45 * min(
        paper.width - 2.0 * paper.margin,
        paper.height - 2.0 * paper.margin,
    )
    if half_span <= 0.0:
        raise ValueError("paper margin leaves no writable area")
    if name == "line":
        start = center + np.asarray([0.0, half_span])
        end = center + np.asarray([0.0, -half_span])
        strokes = (Stroke(_line_points(start, end, spacing), "line"),)
    elif name == "circle":
        radius = half_span
        circumference = 2.0 * np.pi * radius
        count = max(12, int(np.ceil(circumference / spacing)) + 1)
        angles = np.linspace(0.0, 2.0 * np.pi, count, dtype=np.float64)
        points = center + np.column_stack((radius * np.cos(angles), radius * np.sin(angles)))
        strokes = (Stroke(points, "circle"),)
    elif name == "cross":
        horizontal = _line_points(
            center + np.asarray([-half_span, 0.0]),
            center + np.asarray([half_span, 0.0]),
            spacing,
        )
        vertical = _line_points(
            center + np.asarray([0.0, half_span]),
            center + np.asarray([0.0, -half_span]),
            spacing,
        )
        strokes = (Stroke(horizontal, "horizontal"), Stroke(vertical, "vertical"))
    else:
        choices = ", ".join(PRIMITIVE_NAMES)
        raise ValueError(f"Unknown primitive {name!r}; choose one of: {choices}.")

    return Trajectory(strokes=strokes, source=f"primitive:{name}")
