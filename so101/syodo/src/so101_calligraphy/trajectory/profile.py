"""Pressure, speed, and width exemplars for Japanese brush finishes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from so101_calligraphy.config import BrushConfig
from so101_calligraphy.trajectory.types import Stroke, TECHNIQUES


# KanjiVG uses the Unicode CJK Strokes characters. These compound strokes end
# in a hook even when KanjiVG appends a shape variant such as ``a`` or ``b``.
_HANE_STROKES = frozenset("㇂㇃㇄㇅㇆㇇㇈㇉㇊㇋㇌㇍㇎㇚㇟")
_HARAI_STROKES = frozenset("㇒㇏")


@dataclass(frozen=True)
class StrokeProfile:
    progress: np.ndarray
    tangents: np.ndarray
    pressure: np.ndarray
    speed: np.ndarray
    width: np.ndarray
    technique: str


def resolve_technique(stroke: Stroke) -> str:
    """Resolve explicit SVG metadata or infer the finish from KanjiVG type."""

    if stroke.technique != "auto":
        return stroke.technique
    symbols = set(stroke.stroke_type)
    if symbols & _HARAI_STROKES:
        return "harai"
    if symbols & _HANE_STROKES:
        return "hane"
    return "tome"


def technique_one_hot(technique: str) -> np.ndarray:
    values = np.zeros(len(TECHNIQUES), dtype=np.float64)
    values[TECHNIQUES.index(technique)] = 1.0
    return values


def _smoothstep(value: np.ndarray) -> np.ndarray:
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def _progress_and_tangents(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    segments = np.diff(points, axis=0)
    lengths = np.linalg.norm(segments, axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    progress = cumulative / max(float(cumulative[-1]), 1e-12)
    tangent = np.empty_like(points)
    tangent[0] = segments[0]
    tangent[-1] = segments[-1]
    if len(points) > 2:
        tangent[1:-1] = points[2:] - points[:-2]
    norm = np.linalg.norm(tangent, axis=1, keepdims=True)
    tangent /= np.maximum(norm, 1e-12)
    return progress, tangent


def build_stroke_profile(
    stroke: Stroke, brush: BrushConfig | None = None
) -> StrokeProfile:
    """Create a deterministic calligraphic exemplar for one sampled stroke."""

    brush = brush or BrushConfig()
    progress, tangents = _progress_and_tangents(stroke.points)
    technique = resolve_technique(stroke)

    pressure = np.full(len(progress), 0.72, dtype=np.float64)
    speed = np.full(len(progress), brush.nominal_speed, dtype=np.float64)

    # The first tenth is the visible onset: contact, brief settling, then send.
    onset = _smoothstep(progress / 0.12)
    pressure = 0.30 + (pressure - 0.30) * onset
    speed = brush.nominal_speed * (0.35 + 0.65 * onset)

    if technique == "tome":
        finish = _smoothstep((progress - 0.82) / 0.18)
        pressure = pressure * (1.0 - finish) + 0.90 * finish
        speed = speed * (1.0 - finish) + 0.025 * finish
    elif technique == "harai":
        finish = _smoothstep((progress - 0.65) / 0.35)
        pressure = pressure * (1.0 - finish) + 0.035 * finish
        speed = speed * (1.0 - finish) + brush.nominal_speed * 1.75 * finish
    else:  # hane
        finish = np.clip((progress - 0.72) / 0.28, 0.0, 1.0)
        turn = _smoothstep(np.minimum(finish / 0.45, 1.0))
        release = _smoothstep(np.maximum((finish - 0.35) / 0.65, 0.0))
        speed = speed * (1.0 - turn) + brush.nominal_speed * 0.32 * turn
        speed = speed * (1.0 - release) + brush.nominal_speed * 1.55 * release
        pressure = pressure * (1.0 - turn) + 0.86 * turn
        pressure = pressure * (1.0 - release) + 0.04 * release

    width_fraction = np.sqrt(np.clip(pressure, 0.0, 1.0))
    width = brush.minimum_width + (
        brush.maximum_width - brush.minimum_width
    ) * width_fraction
    if stroke.widths is not None:
        outline_width = np.asarray(stroke.widths, dtype=np.float64)
        if len(outline_width) >= 5:
            outline_width = np.convolve(
                np.pad(outline_width, (2, 2), mode="edge"),
                np.asarray([1.0, 2.0, 3.0, 2.0, 1.0]) / 9.0,
                mode="valid",
            )
        outline_width = np.clip(
            outline_width, brush.minimum_width, brush.maximum_width
        )
        width = 0.75 * outline_width + 0.25 * width
        inferred_pressure = np.square(
            np.clip(
                (width - brush.minimum_width)
                / (brush.maximum_width - brush.minimum_width),
                0.0,
                1.0,
            )
        )
        pressure = 0.65 * inferred_pressure + 0.35 * pressure
    return StrokeProfile(progress, tangents, pressure, speed, width, technique)
