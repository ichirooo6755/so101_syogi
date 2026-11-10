"""Validated trajectory data structures."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


TECHNIQUES = ("tome", "hane", "harai")


@dataclass(frozen=True)
class Stroke:
    """One ordered pen-down stroke in world XY coordinates."""

    points: np.ndarray
    name: str = "stroke"
    stroke_type: str = ""
    technique: str = "auto"
    widths: np.ndarray | None = None

    def __post_init__(self) -> None:
        points = np.asarray(self.points, dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError("Stroke points must have shape (N, 2).")
        if len(points) < 2:
            raise ValueError("A stroke must contain at least two points.")
        if not np.isfinite(points).all():
            raise ValueError("Stroke points must all be finite.")
        if self.technique not in ("auto", *TECHNIQUES):
            raise ValueError(
                f"Unknown stroke technique {self.technique!r}; "
                f"choose auto or one of {', '.join(TECHNIQUES)}."
            )
        if self.widths is not None:
            widths = np.asarray(self.widths, dtype=np.float64)
            if widths.shape != (len(points),):
                raise ValueError("Stroke widths must have shape (N,).")
            if not np.isfinite(widths).all() or np.any(widths <= 0):
                raise ValueError("Stroke widths must be positive and finite.")
            object.__setattr__(self, "widths", widths)
        object.__setattr__(self, "points", points)


@dataclass(frozen=True)
class Trajectory:
    """An ordered list of strokes."""

    strokes: tuple[Stroke, ...]
    source: str = "unknown"
    character: str | None = None

    def __post_init__(self) -> None:
        strokes = tuple(self.strokes)
        if not strokes:
            raise ValueError("A trajectory must contain at least one stroke.")
        if self.character is not None and len(self.character) != 1:
            raise ValueError("Trajectory character must be one Unicode character.")
        object.__setattr__(self, "strokes", strokes)

    @property
    def point_count(self) -> int:
        return sum(len(stroke.points) for stroke in self.strokes)
