"""Optional Japanese kaisho stroke-outline widths from the AnimCJK project."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence
import urllib.error
import urllib.request

import numpy as np
from svgpathtools.parser import parse_path

from so101_calligraphy.config import PaperConfig
from so101_calligraphy.trajectory.types import Stroke, Trajectory


ANIMCJK_REVISION = "ec5e17cca76c87587790bcbce5ea0b4d4fb753d6"
ANIMCJK_URL = (
    "https://raw.githubusercontent.com/parsimonhi/animCJK/"
    f"{ANIMCJK_REVISION}/graphicsJa.txt"
)


def fetch_animcjk(cache_dir: str | Path = "data/animcjk") -> Path:
    """Fetch the pinned Japanese outline/median JSONL file once."""

    cache_dir = Path(cache_dir).expanduser().resolve()
    target = cache_dir / f"graphicsJa-{ANIMCJK_REVISION[:12]}.txt"
    if target.is_file() and target.stat().st_size > 1_000_000:
        return target
    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    request = urllib.request.Request(
        ANIMCJK_URL, headers={"User-Agent": "so101-calligraphy/0.2"}
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            temporary.write_bytes(response.read())
        if temporary.stat().st_size <= 1_000_000:
            raise ValueError("downloaded file is unexpectedly small")
        temporary.replace(target)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Could not fetch pinned AnimCJK graphicsJa data: {exc}") from exc
    return target


ANIMCJK_ALIASES = {"𠮟": "叱", "剝": "剥"}


@lru_cache(maxsize=4)
def _line_index(
    path_text: str,
    size: int,
    modified_ns: int,
) -> dict[str, int]:
    """Index the JSONL once without retaining its large outline payloads."""

    del size, modified_ns
    offsets: dict[str, int] = {}
    with Path(path_text).open("rb") as handle:
        while True:
            offset = handle.tell()
            line = handle.readline()
            if not line:
                break
            if not line.strip():
                continue
            entry = json.loads(line)
            character = entry.get("character")
            if isinstance(character, str):
                offsets[character] = offset
    return offsets


def _entries(path: Path, characters: set[str]) -> dict[str, dict[str, object]]:
    stat = path.stat()
    offsets = _line_index(str(path), stat.st_size, stat.st_mtime_ns)
    resolved = {
        character: ANIMCJK_ALIASES.get(character, character)
        for character in characters
    }
    missing = set(resolved.values()) - offsets.keys()
    if missing:
        raise ValueError("AnimCJK has no Japanese outline for: " + "".join(sorted(missing)))
    found: dict[str, dict[str, object]] = {}
    with path.open("rb") as handle:
        for requested, character in resolved.items():
            handle.seek(offsets[character])
            found[requested] = json.loads(handle.readline())
    return found


def animcjk_coverage(
    characters: Sequence[str],
    cache_dir: str | Path = "data/animcjk",
) -> tuple[str, ...]:
    """Return requested characters missing from the pinned Japanese dataset."""

    path = fetch_animcjk(cache_dir)
    stat = path.stat()
    offsets = _line_index(str(path), stat.st_size, stat.st_mtime_ns)
    return tuple(
        character
        for character in characters
        if ANIMCJK_ALIASES.get(character, character) not in offsets
    )


def _arc_progress(points: np.ndarray) -> np.ndarray:
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    return cumulative / max(float(cumulative[-1]), 1e-12)


def _outline_widths(entry: dict[str, object], paper: PaperConfig) -> tuple[np.ndarray, ...]:
    medians = tuple(np.asarray(points, dtype=np.float64) for points in entry["medians"])
    outlines = tuple(str(path) for path in entry["strokes"])
    if len(medians) != len(outlines) or not medians:
        raise ValueError("AnimCJK stroke outlines and medians do not match.")
    all_points = np.concatenate(medians, axis=0)
    span = np.maximum(np.ptp(all_points, axis=0), 1e-9)
    scale = min(
        (paper.width - 2.0 * paper.margin) / span[0],
        (paper.height - 2.0 * paper.margin) / span[1],
    )
    widths: list[np.ndarray] = []
    for median, path_data in zip(medians, outlines, strict=True):
        outline = parse_path(path_data)
        sample_count = max(160, min(640, int(outline.length(error=1e-4) / 3.0)))
        boundary = np.asarray(
            [
                (point.real, point.imag)
                for point in (
                    outline.point(value)
                    for value in np.linspace(0.0, 1.0, sample_count, endpoint=False)
                )
            ],
            dtype=np.float64,
        )
        distance = np.linalg.norm(median[:, None, :] - boundary[None, :, :], axis=2)
        raw_width = 2.0 * distance.min(axis=1)
        widths.append(np.clip(raw_width * scale, 0.0012, 0.020))
    return tuple(widths)


def _world_medians(
    entry: dict[str, object], paper: PaperConfig
) -> tuple[np.ndarray, ...]:
    """Fit AnimCJK's authored Japanese medians into the A4 writing box."""

    medians = tuple(np.asarray(points, dtype=np.float64) for points in entry["medians"])
    if not medians or any(points.ndim != 2 or points.shape[1] != 2 for points in medians):
        raise ValueError("AnimCJK medians are missing or malformed.")
    all_points = np.concatenate(medians, axis=0)
    lower = all_points.min(axis=0)
    upper = all_points.max(axis=0)
    span = np.maximum(upper - lower, 1e-9)
    scale = min(
        (paper.width - 2.0 * paper.margin) / span[0],
        (paper.height - 2.0 * paper.margin) / span[1],
    )
    center = 0.5 * (lower + upper)
    world_center = np.asarray([paper.center_x, paper.center_y], dtype=np.float64)
    return tuple((points - center) * scale + world_center for points in medians)


def _resample_polyline(points: np.ndarray, spacing: float) -> tuple[np.ndarray, np.ndarray]:
    progress = _arc_progress(points)
    length = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())
    count = max(2, int(np.ceil(length / spacing)) + 1)
    target_progress = np.linspace(0.0, 1.0, count)
    sampled = np.column_stack(
        (
            np.interp(target_progress, progress, points[:, 0]),
            np.interp(target_progress, progress, points[:, 1]),
        )
    )
    return sampled, target_progress


def enrich_with_animcjk_widths(
    trajectory: Trajectory,
    character: str,
    *,
    stroke_numbers: Sequence[int] | None = None,
    cache_dir: str | Path = "data/animcjk",
    paper: PaperConfig | None = None,
    use_medians: bool = False,
    spacing: float = 0.008,
) -> Trajectory:
    """Attach outline widths and optionally authored Japanese centre-lines."""

    if len(character) != 1:
        raise ValueError("AnimCJK input must be exactly one Unicode character.")
    paper = paper or PaperConfig()
    entry = _entries(fetch_animcjk(cache_dir), {character})[character]
    source_widths = _outline_widths(entry, paper)
    if stroke_numbers is None:
        stroke_numbers = tuple(range(1, len(trajectory.strokes) + 1))
    if len(stroke_numbers) != len(trajectory.strokes):
        raise ValueError("AnimCJK stroke-number mapping does not match trajectory.")

    return _attach_widths(
        trajectory,
        character,
        source_widths,
        stroke_numbers=stroke_numbers,
        source_medians=_world_medians(entry, paper) if use_medians else None,
        spacing=spacing,
    )


def _attach_widths(
    trajectory: Trajectory,
    character: str,
    source_widths: tuple[np.ndarray, ...],
    *,
    stroke_numbers: Sequence[int] | None,
    source_medians: tuple[np.ndarray, ...] | None = None,
    spacing: float = 0.008,
) -> Trajectory:
    if stroke_numbers is None:
        stroke_numbers = tuple(range(1, len(trajectory.strokes) + 1))
    if len(stroke_numbers) != len(trajectory.strokes):
        raise ValueError("AnimCJK stroke-number mapping does not match trajectory.")
    strokes: list[Stroke] = []
    for stroke, stroke_number in zip(trajectory.strokes, stroke_numbers, strict=True):
        if not 1 <= stroke_number <= len(source_widths):
            raise ValueError(
                f"AnimCJK has no stroke {stroke_number} for {character!r}."
            )
        widths = source_widths[stroke_number - 1]
        if source_medians is None:
            points = stroke.points
            source_progress = np.linspace(0.0, 1.0, len(widths))
            target_progress = _arc_progress(points)
        else:
            if not 0 < spacing:
                raise ValueError("AnimCJK median spacing must be positive.")
            authored = source_medians[stroke_number - 1]
            points, target_progress = _resample_polyline(authored, spacing)
            source_progress = _arc_progress(authored)
        strokes.append(
            Stroke(
                points,
                name=stroke.name,
                stroke_type=stroke.stroke_type,
                technique=stroke.technique,
                widths=np.interp(target_progress, source_progress, widths),
            )
        )
    return Trajectory(
        strokes=tuple(strokes),
        source=(
            f"{trajectory.source} + AnimCJK {ANIMCJK_REVISION[:12]} "
            + ("Japanese medians/outlines" if source_medians is not None else "outlines")
        ),
        character=trajectory.character or character,
    )


def enrich_many_with_animcjk_widths(
    items: Iterable[tuple[Trajectory, str, Sequence[int] | None]],
    *,
    cache_dir: str | Path = "data/animcjk",
    paper: PaperConfig | None = None,
    use_medians: bool = False,
    spacing: float = 0.008,
) -> tuple[Trajectory, ...]:
    """Batch-friendly convenience wrapper used by curriculum builders."""

    materialized = tuple(items)
    paper = paper or PaperConfig()
    entries = _entries(
        fetch_animcjk(cache_dir), {character for _, character, _ in materialized}
    )
    return tuple(
        _attach_widths(
            trajectory,
            character,
            _outline_widths(entries[character], paper),
            stroke_numbers=stroke_numbers,
            source_medians=(
                _world_medians(entries[character], paper) if use_medians else None
            ),
            spacing=spacing,
        )
        for trajectory, character, stroke_numbers in materialized
    )
