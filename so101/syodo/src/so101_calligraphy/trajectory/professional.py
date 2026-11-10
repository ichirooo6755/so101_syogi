"""Verified professional final-image exemplars for calligraphy learning."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import os
from dataclasses import replace
from pathlib import Path
import urllib.error
import urllib.request
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from svgpathtools.parser import parse_path

from so101_calligraphy.config import InkConfig, PaperConfig
from so101_calligraphy.trajectory.animcjk import _entries, fetch_animcjk
from so101_calligraphy.trajectory.types import Stroke, Trajectory


MOTOYA_SOURCE = "S Motoya Seikaisho 5 ProN"
MOTOYA_PRODUCT_URL = "https://www.motoyafont.jp/font-list/seikai.html"
KOUZAN_SOURCE = "Aoyagi Kouzan / Musashi System Kouzan Mouhitu Font"
KOUZAN_FONT_URL = "https://opentype.jp/bin/KouzanMouhituFont.zip"
KOUZAN_ZIP_SHA256 = "453a35f6ca1bd5863aa06827ebbd2c41d8676fc1d9d705e5a0eb027ce3907f9a"
KOUZAN_TTF_SHA256 = "582f269574e71336f1ee8318664ff6cfafd84293b3267ddf39410015713c951e"

# Compatibility forms for which the ProN cmap may expose only the unified joyo
# glyph. Stroke order and trajectory continue to use the original character.
PROFESSIONAL_GLYPH_ALIASES = {"𠮟": "叱", "剝": "剥"}


class MotoyaFontError(RuntimeError):
    """Raised when the exact licensed final-image teacher is unavailable."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch_kouzan_font(cache_dir: str | Path = "data/professional") -> Path:
    """Fetch and verify the freely distributable Aoyagi Kouzan exemplar."""

    cache = Path(cache_dir).expanduser().resolve()
    target = cache / "KouzanMouhituFont.ttf"
    if target.is_file() and _sha256(target.read_bytes()) == KOUZAN_TTF_SHA256:
        return target
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / "KouzanMouhituFont.zip"
    if not archive.is_file() or _sha256(archive.read_bytes()) != KOUZAN_ZIP_SHA256:
        temporary = archive.with_suffix(".zip.tmp")
        request = urllib.request.Request(
            KOUZAN_FONT_URL,
            headers={"User-Agent": "so101-calligraphy/0.5"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = response.read()
            if _sha256(payload) != KOUZAN_ZIP_SHA256:
                raise ValueError("Aoyagi Kouzan archive checksum mismatch")
            temporary.write_bytes(payload)
            temporary.replace(archive)
        except (OSError, ValueError, urllib.error.URLError) as exc:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"Could not fetch Aoyagi Kouzan font: {exc}") from exc
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = [member for member in bundle.infolist() if not member.is_dir()]
            if len(members) != 1:
                raise ValueError("Aoyagi Kouzan archive must contain one font")
            payload = bundle.read(members[0])
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise RuntimeError(f"Could not extract Aoyagi Kouzan font: {exc}") from exc
    if _sha256(payload) != KOUZAN_TTF_SHA256:
        raise RuntimeError("Aoyagi Kouzan font checksum mismatch")
    target.write_bytes(payload)
    return target


def _candidate_paths(explicit: str | Path | None) -> tuple[Path, ...]:
    configured = explicit or os.environ.get("SO101_MOTOYA_FONT")
    if configured:
        return (Path(configured).expanduser(),)
    roots = (
        Path.home() / "Library/Fonts",
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
    )
    candidates: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for pattern in ("*Motoya*", "*motoya*", "*モトヤ*"):
            candidates.extend(path for path in root.glob(pattern) if path.is_file())
    return tuple(dict.fromkeys(candidates))


def _font_name_text(path: Path) -> str:
    try:
        font = TTFont(path, lazy=True)
        try:
            values: list[str] = []
            for record in font["name"].names:
                if record.nameID not in (1, 2, 4, 6, 16, 17):
                    continue
                try:
                    values.append(record.toUnicode())
                except UnicodeDecodeError:
                    continue
            return " ".join(values)
        finally:
            font.close()
    except Exception as exc:
        raise MotoyaFontError(f"Could not inspect font {path}: {exc}") from exc


def _adobe_japan_supplement(path: Path) -> int | None:
    """Return the CFF Adobe-Japan collection supplement when available."""

    try:
        font = TTFont(path, lazy=True)
        try:
            if "CFF " not in font:
                return None
            registry, ordering, supplement = font["CFF "].cff.topDictIndex[0].ROS
            registry_text = registry.decode() if isinstance(registry, bytes) else str(registry)
            ordering_text = ordering.decode() if isinstance(ordering, bytes) else str(ordering)
            if registry_text == "Adobe" and ordering_text == "Japan1":
                return int(supplement)
        finally:
            font.close()
    except Exception:
        return None
    return None


def verify_motoya_font(path: str | Path) -> Path:
    """Verify that *path* identifies S Motoya Seikaisho 5 ProN."""

    candidate = Path(path).expanduser().resolve()
    if not candidate.is_file():
        raise MotoyaFontError(f"Motoya font file does not exist: {candidate}")
    names = _font_name_text(candidate)
    folded = names.casefold().replace(" ", "")
    path_name = candidate.name.casefold().replace(" ", "")
    pro_n = "pron" in folded or "pron" in path_name
    supplement = _adobe_japan_supplement(candidate)
    pro_n = pro_n or (supplement is not None and supplement >= 5)
    checks = (
        ("Motoya", "motoya" in folded or "モトヤ" in folded),
        ("Seikaisho", "seikai" in folded or "正楷" in folded),
        ("weight 5", "5" in folded),
        ("ProN character collection", pro_n),
    )
    missing = [label for label, present in checks if not present]
    if missing:
        raise MotoyaFontError(
            f"{candidate} is not {MOTOYA_SOURCE}; missing name markers: "
            + ", ".join(missing)
        )
    return candidate


def resolve_motoya_font(path: str | Path | None = None) -> Path:
    """Resolve and verify the licensed teacher without downloading anything."""

    candidates = _candidate_paths(path)
    errors: list[str] = []
    for candidate in candidates:
        try:
            return verify_motoya_font(candidate)
        except MotoyaFontError as exc:
            errors.append(str(exc))
    hint = (
        "Install the licensed S Motoya Seikaisho 5 ProN font and set "
        "SO101_MOTOYA_FONT=/absolute/path/to/font.otf (or pass --motoya-font). "
        f"The project does not download or substitute this commercial asset. {MOTOYA_PRODUCT_URL}"
    )
    if errors:
        hint += " Checked: " + " | ".join(errors)
    raise MotoyaFontError(hint)


def verify_licensed_exemplar_font(
    path: str | Path,
    *,
    sample_characters: tuple[str, ...] = ("一", "永", "鬱"),
) -> Path:
    """Accept a locally licensed teacher font after coverage and render checks."""

    candidate = Path(path).expanduser().resolve()
    if not candidate.is_file():
        raise MotoyaFontError(f"Exemplar font file does not exist: {candidate}")
    missing = font_coverage(sample_characters, candidate)
    if missing:
        raise MotoyaFontError(
            f"{candidate} is missing teacher glyphs: {''.join(missing)}"
        )
    try:
        _raw_glyph_mask("一", candidate)
    except MotoyaFontError as exc:
        raise MotoyaFontError(f"{candidate} could not render a teacher glyph") from exc
    return candidate


def _licensed_exemplar_source(path: Path) -> str:
    try:
        return _font_name_text(path).strip() or path.name
    except MotoyaFontError:
        return path.name


def resolve_exemplar_font(
    path: str | Path | None = None,
    *,
    motoya_path: str | Path | None = None,
    cache_dir: str | Path = "data/professional",
) -> tuple[Path, str]:
    """Resolve teacher font: exemplar → Motoya → verified Aoyagi."""

    exemplar_configured = path or os.environ.get("SO101_EXEMPLAR_FONT")
    motoya_configured = motoya_path or os.environ.get("SO101_MOTOYA_FONT")
    if exemplar_configured is not None:
        candidate = Path(exemplar_configured).expanduser().resolve()
        if candidate.is_file() and _sha256(candidate.read_bytes()) == KOUZAN_TTF_SHA256:
            return candidate, KOUZAN_SOURCE
        resolved = verify_licensed_exemplar_font(candidate)
        return resolved, _licensed_exemplar_source(resolved)
    if motoya_configured is not None:
        candidate = Path(motoya_configured).expanduser().resolve()
        if candidate.is_file() and _sha256(candidate.read_bytes()) == KOUZAN_TTF_SHA256:
            return candidate, KOUZAN_SOURCE
        return resolve_motoya_font(candidate), MOTOYA_SOURCE
    return fetch_kouzan_font(cache_dir), KOUZAN_SOURCE


def font_coverage(
    characters: tuple[str, ...] | list[str],
    font_path: str | Path,
) -> tuple[str, ...]:
    """Return teacher glyphs missing from a resolved professional font."""

    font = TTFont(Path(font_path), lazy=True)
    try:
        covered = {
            chr(codepoint)
            for table in font["cmap"].tables
            if table.isUnicode()
            for codepoint in table.cmap
        }
    finally:
        font.close()
    return tuple(
        character
        for character in characters
        if PROFESSIONAL_GLYPH_ALIASES.get(character, character) not in covered
    )


@lru_cache(maxsize=256)
def _raw_glyph_mask(character: str, font_path: Path, resolution: int = 1024) -> np.ndarray:
    glyph = PROFESSIONAL_GLYPH_ALIASES.get(character, character)
    font = ImageFont.truetype(str(font_path), int(resolution * 0.78))
    canvas = Image.new("L", (resolution, resolution), 0)
    draw = ImageDraw.Draw(canvas)
    box = draw.textbbox((0, 0), glyph, font=font)
    width, height = box[2] - box[0], box[3] - box[1]
    draw.text(
        ((resolution - width) * 0.5 - box[0], (resolution - height) * 0.5 - box[1]),
        glyph,
        font=font,
        fill=255,
    )
    crop = canvas.getbbox()
    if crop is None:
        raise MotoyaFontError(f"The exemplar font rendered no glyph for {character!r}.")
    return np.asarray(canvas.crop(crop), dtype=np.float32) / 255.0


@lru_cache(maxsize=8)
def _animcjk_fallback_mask(
    character: str,
    cache_text: str,
    resolution: int = 1024,
) -> np.ndarray:
    """Rasterize pinned Japanese stroke outlines for a blank font glyph."""

    entry = _entries(fetch_animcjk(cache_text), {character})[character]
    polygons: list[np.ndarray] = []
    for path_data in entry["strokes"]:
        outline = parse_path(str(path_data))
        sample_count = max(192, min(768, int(outline.length(error=1e-4) / 2.0)))
        polygons.append(
            np.asarray(
                [
                    (point.real, point.imag)
                    for point in (
                        outline.point(value)
                        for value in np.linspace(0.0, 1.0, sample_count, endpoint=False)
                    )
                ],
                dtype=np.float64,
            )
        )
    points = np.concatenate(polygons, axis=0)
    lower = points.min(axis=0)
    span = np.maximum(np.ptp(points, axis=0), 1e-9)
    scale = (resolution - 32.0) / max(float(span.max()), 1e-9)
    offset = 16.0 + 0.5 * ((resolution - 32.0) - span * scale)
    canvas = Image.new("L", (resolution, resolution), 0)
    draw = ImageDraw.Draw(canvas)
    for polygon in polygons:
        mapped = (polygon - lower) * scale + offset
        draw.polygon([tuple(point) for point in mapped], fill=255)
    crop = canvas.getbbox()
    if crop is None:
        raise ValueError(f"AnimCJK rendered no fallback glyph for {character!r}.")
    return np.asarray(canvas.crop(crop), dtype=np.float32) / 255.0


def align_glyph_mask(
    source_mask: np.ndarray,
    target_points: np.ndarray,
    paper: PaperConfig,
    ink: InkConfig,
    *,
    padding: float = 0.007,
) -> np.ndarray:
    """Place an exemplar in the writing box for image scoring only."""

    source = np.asarray(source_mask, dtype=np.float32)
    points = np.asarray(target_points, dtype=np.float64)
    if source.ndim != 2 or source.size == 0:
        raise ValueError("source_mask must be a non-empty 2-D array")
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 2:
        raise ValueError("target_points must have shape (N, 2)")
    rows = int(np.ceil(paper.height / ink.pixel_size))
    columns = int(np.ceil(paper.width / ink.pixel_size))
    result = np.zeros((rows, columns), dtype=np.float32)
    xmin = paper.center_x - paper.width * 0.5
    ymax = paper.center_y + paper.height * 0.5
    lower = points.min(axis=0) - padding
    upper = points.max(axis=0) + padding
    desired_width = max((upper[0] - lower[0]) / ink.pixel_size, 2.0)
    desired_height = max((upper[1] - lower[1]) / ink.pixel_size, 2.0)
    scale = min(desired_width / source.shape[1], desired_height / source.shape[0])
    width = max(1, int(round(source.shape[1] * scale)))
    height = max(1, int(round(source.shape[0] * scale)))
    resized = np.asarray(
        Image.fromarray(np.uint8(np.clip(source, 0.0, 1.0) * 255)).resize(
            (width, height), Image.Resampling.LANCZOS
        ),
        dtype=np.float32,
    ) / 255.0
    center = 0.5 * (lower + upper)
    center_column = int(round((center[0] - xmin) / ink.pixel_size))
    center_row = int(round((ymax - center[1]) / ink.pixel_size))
    c0, r0 = center_column - width // 2, center_row - height // 2
    c1, r1 = c0 + width, r0 + height
    src_c0, src_r0 = max(0, -c0), max(0, -r0)
    src_c1 = width - max(0, c1 - columns)
    src_r1 = height - max(0, r1 - rows)
    c0, r0, c1, r1 = max(0, c0), max(0, r0), min(columns, c1), min(rows, r1)
    if c0 < c1 and r0 < r1:
        result[r0:r1, c0:c1] = resized[src_r0:src_r1, src_c0:src_c1]
    return result


def render_professional_mask(
    character: str,
    target_points: np.ndarray,
    paper: PaperConfig,
    ink: InkConfig,
    font_path: str | Path | None = None,
    animcjk_cache: str | Path = "data/animcjk",
) -> np.ndarray:
    """Render the selected verified final-image teacher."""

    resolved, _ = resolve_exemplar_font(font_path)
    try:
        source = _raw_glyph_mask(character, resolved)
    except MotoyaFontError:
        source = _animcjk_fallback_mask(
            character,
            str(Path(animcjk_cache).expanduser().resolve()),
        )
    return align_glyph_mask(
        source,
        target_points,
        paper,
        ink,
    )


def exemplar_thumbnail(mask: np.ndarray, size: int = 16) -> np.ndarray:
    """Crop ink-bearing pixels and return a fixed image observation."""

    source = np.asarray(mask, dtype=np.float32)
    rows, columns = np.nonzero(source > 0.01)
    if len(rows) == 0:
        return np.zeros((size, size), dtype=np.float32)
    padding = 3
    row0, row1 = max(0, rows.min() - padding), min(source.shape[0], rows.max() + padding + 1)
    column0 = max(0, columns.min() - padding)
    column1 = min(source.shape[1], columns.max() + padding + 1)
    cropped = source[row0:row1, column0:column1]
    return np.asarray(
        Image.fromarray(np.uint8(np.clip(cropped, 0.0, 1.0) * 255.0)).resize(
            (size, size), Image.Resampling.LANCZOS
        ),
        dtype=np.float32,
    ) / 255.0


def sample_paper_mask(
    mask: np.ndarray,
    points: np.ndarray,
    paper: PaperConfig,
    ink: InkConfig,
) -> np.ndarray:
    """Bilinearly sample a paper raster at world-space XY points."""

    points = np.asarray(points, dtype=np.float64)
    xmin = paper.center_x - paper.width * 0.5
    ymax = paper.center_y + paper.height * 0.5
    columns = (points[:, 0] - xmin) / ink.pixel_size - 0.5
    rows = (ymax - points[:, 1]) / ink.pixel_size - 0.5
    column0 = np.floor(columns).astype(np.int64)
    row0 = np.floor(rows).astype(np.int64)
    column_weight = columns - column0
    row_weight = rows - row0
    values = np.zeros(len(points), dtype=np.float64)
    valid = (
        (column0 >= 0)
        & (row0 >= 0)
        & (column0 + 1 < mask.shape[1])
        & (row0 + 1 < mask.shape[0])
    )
    selected = np.flatnonzero(valid)
    if len(selected) == 0:
        return values
    columns0 = column0[selected]
    rows0 = row0[selected]
    x_weight = column_weight[selected]
    y_weight = row_weight[selected]
    values[selected] = (
        mask[rows0, columns0] * (1.0 - x_weight) * (1.0 - y_weight)
        + mask[rows0, columns0 + 1] * x_weight * (1.0 - y_weight)
        + mask[rows0 + 1, columns0] * (1.0 - x_weight) * y_weight
        + mask[rows0 + 1, columns0 + 1] * x_weight * y_weight
    )
    return values


def fit_trajectory_to_exemplar_shape(
    trajectory: Trajectory,
    paper: PaperConfig,
    *,
    font_path: str | Path | None = None,
    animcjk_cache: str | Path = "data/animcjk",
    strength: float = 1.0,
    padding: float = 0.007,
) -> Trajectory:
    """字の外形比をお手本字形に合わせる（大域アフィン）。

    軌道は KanjiVG/AnimCJK の骨格 bbox を書き枠に目一杯フィットさせ、お手本は
    フォント字形の比率を保って配置される。両者の比率は一致しないため、平たい字
    (二・三・工) は横に 27-39% 広がり、縦長の字 (日・目・自) は縦に 32-65% 伸びる。
    IoU が画数の少ない字ほど悪いのはこれが原因（0-4画 49.6 対 20-24画 60.1）。

    ``refine_trajectory_to_exemplar`` は各画を法線方向へ ±8mm しか動かせないので、
    数十 mm の寸法差は直せない。先にここで外形を合わせてから局所リファインする。

    ``strength`` は 0 で無効、1 で完全にお手本の比率へ。
    ``padding`` は ``align_glyph_mask`` と同じ値にすること（お手本が軌道 bbox に
    padding つきで収められるため、外形の定義を揃えないとズレが残る）。
    """

    if strength <= 0.0 or trajectory.character is None:
        return trajectory
    try:
        resolved, _ = resolve_exemplar_font(font_path)
    except (MotoyaFontError, RuntimeError):
        # お手本フォントが無ければ外形を合わせる基準が無い。本番では直後の
        # render_professional_mask が同じ理由で失敗するので、ここでは黙って
        # 素通りしてよい（マスクを差し替えるテストのためでもある）。
        return trajectory
    try:
        source = _raw_glyph_mask(trajectory.character, resolved)
    except MotoyaFontError:
        source = _animcjk_fallback_mask(
            trajectory.character,
            str(Path(animcjk_cache).expanduser().resolve()),
        )
    if source.shape[0] < 2 or source.shape[1] < 2:
        return trajectory
    aspect = float(source.shape[1]) / float(source.shape[0])

    points = np.concatenate([stroke.points for stroke in trajectory.strokes], axis=0)
    lower, upper = points.min(axis=0), points.max(axis=0)
    span = np.maximum(upper - lower, 1e-9)
    usable_x = paper.width - 2.0 * paper.margin
    usable_y = paper.height - 2.0 * paper.margin
    if usable_x <= 0.0 or usable_y <= 0.0:
        raise ValueError("Paper margin leaves no writable area.")
    # 外形（padding 込み）をお手本の比率のまま書き枠いっぱいに取る。
    outer_height = min(usable_y, usable_x / aspect)
    outer_width = outer_height * aspect
    target = np.asarray(
        [
            max(outer_width - 2.0 * padding, 1e-4),
            max(outer_height - 2.0 * padding, 1e-4),
        ]
    )
    scale = np.clip(target / span, 0.2, 5.0)
    scale = 1.0 + strength * (scale - 1.0)
    center = 0.5 * (lower + upper)
    world_center = np.asarray([paper.center_x, paper.center_y])
    # 線幅は面積が破綻しないよう相乗平均で追従させる。
    width_scale = float(np.sqrt(scale[0] * scale[1]))
    refit = tuple(
        replace(
            stroke,
            points=(stroke.points - center) * scale + world_center,
            widths=None if stroke.widths is None else stroke.widths * width_scale,
        )
        for stroke in trajectory.strokes
    )
    return replace(trajectory, strokes=refit)


def refine_trajectory_to_exemplar(
    trajectory: Trajectory,
    mask: np.ndarray,
    paper: PaperConfig,
    ink: InkConfig,
    *,
    strength: float = 0.72,
    maximum_offset: float = 0.008,
) -> Trajectory:
    """Gently fit ordered medians to nearby exemplar ink.

    Each stroke can only move along its own normal. A cubic fit suppresses
    point-wise snapping at crossings, while tight displacement and width-ratio
    bounds preserve KanjiVG/AnimCJK topology and stroke order.
    """

    if strength <= 0.0:
        return trajectory
    refined: list[Stroke] = []
    offsets = np.linspace(-maximum_offset, maximum_offset, 41)
    width_offsets = np.linspace(-0.009, 0.009, 55)
    for stroke in trajectory.strokes:
        points = stroke.points
        derivatives = np.gradient(points, axis=0)
        norms = np.linalg.norm(derivatives, axis=1, keepdims=True)
        tangents = derivatives / np.maximum(norms, 1e-12)
        normals = np.column_stack((-tangents[:, 1], tangents[:, 0]))
        candidates = points[:, None, :] + normals[:, None, :] * offsets[None, :, None]
        values = sample_paper_mask(
            mask,
            candidates.reshape(-1, 2),
            paper,
            ink,
        ).reshape(len(points), len(offsets))
        proximity = np.exp(-0.5 * np.square(offsets / 0.0045))[None, :]
        weights = np.square(values) * proximity
        totals = weights.sum(axis=1)
        raw_offsets = np.divide(
            (weights * offsets).sum(axis=1),
            totals,
            out=np.zeros(len(points), dtype=np.float64),
            where=totals > 0.35,
        )
        progress = np.linspace(-1.0, 1.0, len(points))
        valid = totals > 0.35
        if np.count_nonzero(valid) >= 3:
            degree = min(3, np.count_nonzero(valid) - 1)
            coefficients = np.polyfit(
                progress[valid],
                raw_offsets[valid],
                degree,
                w=np.sqrt(totals[valid]),
            )
            smooth_offsets = np.polyval(coefficients, progress)
        else:
            smooth_offsets = raw_offsets
        smooth_offsets = np.clip(smooth_offsets, -maximum_offset, maximum_offset)
        new_points = points + strength * smooth_offsets[:, None] * normals

        original_widths = (
            np.asarray(stroke.widths, dtype=np.float64)
            if stroke.widths is not None
            else np.full(len(points), 0.006, dtype=np.float64)
        )
        # Normal-only fitting cannot close a horizontal median that ends well
        # before a font junction (the inner bars of 目 are 14-16 mm short in
        # AnimCJK). Extend/retract each endpoint only through the contiguous
        # exemplar-ink run that already contains it; this cannot jump a white
        # gap to an unrelated stroke.
        endpoint_offsets = np.linspace(-0.020, 0.020, 81)
        endpoint_normal_offsets = np.linspace(-maximum_offset, maximum_offset, 33)
        endpoint_progress = np.linspace(0.0, 1.0, len(new_points))
        for endpoint, outward, normal, envelope in (
            (0, -tangents[0], normals[0], np.square(1.0 - endpoint_progress)),
            (-1, tangents[-1], normals[-1], np.square(endpoint_progress)),
        ):
            endpoint_candidates = (
                new_points[endpoint][None, None, :]
                + endpoint_offsets[:, None, None] * outward[None, None, :]
                + endpoint_normal_offsets[None, :, None] * normal[None, None, :]
            )
            values = sample_paper_mask(
                mask, endpoint_candidates.reshape(-1, 2), paper, ink
            ).reshape(len(endpoint_offsets), len(endpoint_normal_offsets))
            valid = np.max(values, axis=1) >= 0.35
            zero = int(np.argmin(np.abs(endpoint_offsets)))
            if not valid[zero]:
                valid_indices = np.flatnonzero(valid)
                if not len(valid_indices):
                    continue
                anchor = int(valid_indices[np.argmin(np.abs(valid_indices - zero))])
                if abs(endpoint_offsets[anchor]) > 0.004:
                    continue
            else:
                anchor = zero
            last = anchor
            gaps = 0
            for candidate_index in range(anchor + 1, len(valid)):
                if valid[candidate_index]:
                    last = candidate_index
                    gaps = 0
                else:
                    gaps += 1
                    if gaps > 1:
                        break
            half_width = 0.5 * float(
                np.clip(original_widths[endpoint], 0.002, 0.012)
            )
            endpoint_shift = float(
                np.clip(endpoint_offsets[last] - half_width, -0.020, 0.020)
            )
            center_index = int(np.argmin(np.abs(endpoint_offsets - endpoint_shift)))
            cross_weights = np.square(values[center_index])
            normal_shift = float(
                np.divide(
                    cross_weights @ endpoint_normal_offsets,
                    cross_weights.sum(),
                    out=np.asarray(0.0),
                    where=cross_weights.sum() > 0.35,
                )
            )
            endpoint_delta = endpoint_shift * outward + normal_shift * normal
            new_points += (
                strength * envelope[:, None] * endpoint_delta[None, :]
            )

        width_candidates = (
            new_points[:, None, :]
            + normals[:, None, :] * width_offsets[None, :, None]
        )
        width_values = sample_paper_mask(
            mask,
            width_candidates.reshape(-1, 2),
            paper,
            ink,
        ).reshape(len(points), len(width_offsets))
        width_totals = width_values.sum(axis=1)
        means = np.divide(
            (width_values * width_offsets).sum(axis=1),
            width_totals,
            out=np.zeros(len(points), dtype=np.float64),
            where=width_totals > 1.0,
        )
        variances = np.divide(
            (
                width_values
                * np.square(width_offsets[None, :] - means[:, None])
            ).sum(axis=1),
            width_totals,
            out=np.zeros(len(points), dtype=np.float64),
            where=width_totals > 1.0,
        )
        exemplar_widths = np.sqrt(12.0 * np.maximum(variances, 0.0))
        exemplar_widths = np.clip(
            exemplar_widths,
            0.70 * original_widths,
            1.30 * original_widths,
        )
        # ponytail: Morisawa print glyphs are thinner than brush ink; blending
        # exemplar width into the trajectory is the lw-regression path seen in
        # harai-focus/mining/guarded/stage3. Keep AnimCJK/brushwork widths.
        # Upgrade: optional width_blend CLI if a teacher is actually brush-wide.
        width_blend = 0.0
        new_widths = np.where(
            width_totals > 1.0,
            (1.0 - width_blend) * original_widths + width_blend * exemplar_widths,
            original_widths,
        )
        refined.append(
            Stroke(
                new_points,
                name=stroke.name,
                stroke_type=stroke.stroke_type,
                technique=stroke.technique,
                widths=new_widths,
            )
        )
    return Trajectory(
        tuple(refined),
        source=f"{trajectory.source} + image-exemplar low-order fit",
        character=trajectory.character,
    )
