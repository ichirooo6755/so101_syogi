"""Convert ordered SVG geometry to equally spaced A4 trajectories."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import xml.etree.ElementTree as etree

import numpy as np
from svgpathtools.document import CONVERSIONS
from svgpathtools.parser import parse_path, parse_transform
from svgpathtools.path import transform as transform_path

from so101_calligraphy.config import PaperConfig
from so101_calligraphy.trajectory.types import Stroke, Trajectory


ElementFilter = Callable[[etree.Element, tuple[etree.Element, ...]], bool]
KVG_TYPE = "{http://kanjivg.tagaini.net}type"


def _nonempty_subpaths(svg_path: object) -> list[object]:
    subpaths = svg_path.continuous_subpaths()
    return [subpath for subpath in subpaths if subpath.length(error=1e-5) > 1e-9]


def _sample_path(svg_path: object, raw_spacing: float) -> np.ndarray:
    length = float(svg_path.length(error=1e-5))
    count = max(2, int(np.ceil(length / raw_spacing)) + 1)
    distances = np.linspace(0.0, length, count, dtype=np.float64)
    values = [svg_path.point(svg_path.ilength(float(distance))) for distance in distances]
    return np.asarray([(value.real, value.imag) for value in values], dtype=np.float64)


def _paths_in_document_order(
    filename: Path, element_filter: ElementFilter | None = None
) -> list[tuple[object, str, str]]:
    """Return supported visible elements in XML order with transforms applied."""

    root = etree.parse(filename).getroot()
    paths: list[tuple[object, str, str]] = []
    ignored_containers = {"defs", "clipPath", "mask", "metadata", "title", "desc"}

    def visit(
        element: etree.Element,
        parent_transform: np.ndarray,
        ancestors: tuple[etree.Element, ...],
    ) -> None:
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in ignored_containers:
            return
        style = element.get("style", "").replace(" ", "").lower()
        if element.get("display", "").lower() == "none" or "display:none" in style:
            return
        element_transform = parent_transform @ parse_transform(element.get("transform"))
        converter = CONVERSIONS.get(tag)
        if converter is not None and (
            element_filter is None or element_filter(element, ancestors)
        ):
            path_data = converter(element)
            if path_data:
                technique = element.get("data-technique", "auto")
                if technique == "auto":
                    for ancestor in reversed(ancestors):
                        if ancestor.get("data-technique"):
                            technique = ancestor.get("data-technique", "auto")
                            break
                paths.append(
                    (
                        transform_path(parse_path(path_data), element_transform),
                        element.get(KVG_TYPE, ""),
                        technique,
                    )
                )
        for child in element:
            visit(child, element_transform, (*ancestors, element))

    visit(root, np.identity(3), ())
    return paths


def load_svg_trajectory(
    filename: str | Path,
    *,
    paper: PaperConfig | None = None,
    spacing: float = 0.008,
    element_filter: ElementFilter | None = None,
) -> Trajectory:
    """Load SVG strokes in document order and fit them uniformly onto A4 paper.

    Each SVG element and each disconnected subpath becomes one pen-down stroke.
    The SVG Y axis is flipped to match a conventional paper/world coordinate
    frame. Group transforms are handled by ``svgpathtools``.
    """

    paper = paper or PaperConfig()
    filename = Path(filename).expanduser().resolve()
    if not filename.is_file():
        raise FileNotFoundError(f"SVG file does not exist: {filename}")
    if filename.suffix.lower() != ".svg":
        raise ValueError(f"Expected an .svg file, got: {filename.name}")
    if spacing <= 0:
        raise ValueError("spacing must be positive")

    try:
        svg_paths = _paths_in_document_order(filename, element_filter)
    except Exception as exc:
        raise ValueError(f"Could not parse SVG {filename}: {exc}") from exc

    ordered_paths = [
        (subpath, stroke_type, technique)
        for svg_path, stroke_type, technique in svg_paths
        for subpath in _nonempty_subpaths(svg_path)
    ]
    if not ordered_paths:
        raise ValueError(f"SVG contains no drawable, non-empty paths: {filename}")

    boxes = np.asarray(
        [subpath.bbox() for subpath, _, _ in ordered_paths], dtype=np.float64
    )
    # svgpathtools bbox order is xmin, xmax, ymin, ymax.
    xmin, xmax = float(boxes[:, 0].min()), float(boxes[:, 1].max())
    ymin, ymax = float(boxes[:, 2].min()), float(boxes[:, 3].max())
    span_x = max(xmax - xmin, 1e-9)
    span_y = max(ymax - ymin, 1e-9)
    usable_x = paper.width - 2.0 * paper.margin
    usable_y = paper.height - 2.0 * paper.margin
    if usable_x <= 0 or usable_y <= 0:
        raise ValueError("Paper margin leaves no writable area.")
    scale = min(usable_x / span_x, usable_y / span_y)

    raw_spacing = spacing / scale
    svg_center = np.asarray([(xmin + xmax) * 0.5, (ymin + ymax) * 0.5])
    world_center = np.asarray([paper.center_x, paper.center_y])
    strokes: list[Stroke] = []
    for index, (svg_path, stroke_type, technique) in enumerate(ordered_paths):
        points = _sample_path(svg_path, raw_spacing)
        points = (points - svg_center) * scale
        points[:, 1] *= -1.0
        points += world_center
        strokes.append(
            Stroke(
                points,
                name=f"svg-stroke-{index + 1}",
                stroke_type=stroke_type,
                technique=technique,
            )
        )

    return Trajectory(strokes=tuple(strokes), source=str(filename))
