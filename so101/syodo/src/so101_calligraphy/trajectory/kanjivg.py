"""Thin adapter for real stroke and radical data from KanjiVG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
import tarfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as etree

from so101_calligraphy.config import PaperConfig
from so101_calligraphy.trajectory.svg import load_svg_trajectory
from so101_calligraphy.trajectory.types import Stroke, Trajectory


KANJIVG_REVISION = "r20250816"
KANJIVG_URL = (
    "https://raw.githubusercontent.com/KanjiVG/kanjivg/"
    f"{KANJIVG_REVISION}/kanji"
)
KANJIVG_ARCHIVE_URL = (
    f"https://github.com/KanjiVG/kanjivg/archive/refs/tags/{KANJIVG_REVISION}.tar.gz"
)
KVG = "http://kanjivg.tagaini.net"
KVG_TYPE = f"{{{KVG}}}type"
KVG_RADICAL = f"{{{KVG}}}radical"


@dataclass(frozen=True)
class KanjiVGStage:
    slug: str
    label: str
    character: str
    stroke_number: int | None = None
    expected_type: str | None = None
    radical: bool = False


TECHNIQUE_STAGES = (
    KanjiVGStage("horizontal", "横画（㇐）", "一", 1, "㇐"),
    KanjiVGStage("vertical", "縦画（㇑）", "十", 2, "㇑"),
    KanjiVGStage("dot", "点（㇔）", "主", 1, "㇔"),
    KanjiVGStage("left-sweep", "左払い（㇒）", "人", 1, "㇒"),
    KanjiVGStage("right-sweep", "右払い（㇏）", "人", 2, "㇏"),
    KanjiVGStage("turn", "折れ（㇕）", "口", 2, "㇕"),
    KanjiVGStage("hook", "はね（㇚）", "小", 1, "㇚"),
)

RADICAL_STAGES = (
    KanjiVGStage("ninben", "にんべん（亻）", "休", radical=True),
    KanjiVGStage("sanzui", "さんずい（氵）", "海", radical=True),
    KanjiVGStage("risshinben", "りっしんべん（忄）", "情", radical=True),
    KanjiVGStage("tehen", "てへん（扌）", "持", radical=True),
    KanjiVGStage("kusakanmuri", "くさかんむり（艹）", "花", radical=True),
    KanjiVGStage("shinnyou", "しんにょう（⻌）", "道", radical=True),
    KanjiVGStage("gonben", "ごんべん（言）", "語", radical=True),
)


def _validate_character(character: str) -> None:
    if len(character) != 1:
        raise ValueError("KanjiVG input must be exactly one Unicode character.")


def _validate_svg(path: Path) -> None:
    try:
        root = etree.parse(path).getroot()
    except (OSError, etree.ParseError) as exc:
        raise ValueError(f"Invalid cached KanjiVG SVG {path}: {exc}") from exc
    if not any(element.tag.rsplit("}", 1)[-1] == "path" for element in root.iter()):
        raise ValueError(f"KanjiVG SVG has no stroke paths: {path}")


def fetch_kanjivg(character: str, cache_dir: str | Path = "data/kanjivg") -> Path:
    """Download one pinned KanjiVG SVG, or return its validated cache file."""

    _validate_character(character)
    cache_dir = Path(cache_dir).expanduser().resolve()
    target = cache_dir / f"{ord(character):05x}.svg"
    if target.exists():
        _validate_svg(target)
        return target

    cache_dir.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        f"{KANJIVG_URL}/{target.name}",
        headers={"User-Agent": "so101-calligraphy/0.1"},
    )
    temporary = target.with_suffix(".svg.tmp")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            temporary.write_bytes(response.read())
        _validate_svg(temporary)
        temporary.replace(target)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            f"Could not fetch KanjiVG {KANJIVG_REVISION} data for {character!r}: {exc}"
        ) from exc
    return target


def fetch_kanjivg_many(
    characters: tuple[str, ...] | list[str],
    cache_dir: str | Path = "data/kanjivg",
) -> tuple[Path, ...]:
    """Fetch many glyphs from one pinned archive instead of many HTTP requests."""

    if not characters:
        return ()
    for character in characters:
        _validate_character(character)
    cache_dir = Path(cache_dir).expanduser().resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    targets = tuple(cache_dir / f"{ord(character):05x}.svg" for character in characters)
    missing: dict[str, Path] = {}
    for target in targets:
        if target.exists():
            _validate_svg(target)
        else:
            missing[target.name] = target
    if not missing:
        return targets

    archive = cache_dir / f"kanjivg-{KANJIVG_REVISION}.tar.gz"
    temporary = archive.with_name(f"{archive.name}.tmp")
    if not archive.exists():
        request = urllib.request.Request(
            KANJIVG_ARCHIVE_URL,
            headers={"User-Agent": "so101-calligraphy/0.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                temporary.write_bytes(response.read())
            with tarfile.open(temporary, "r:gz"):
                pass
            temporary.replace(archive)
        except (OSError, tarfile.TarError, urllib.error.URLError) as exc:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"Could not fetch KanjiVG archive: {exc}") from exc

    try:
        with tarfile.open(archive, "r:gz") as bundle:
            for member in bundle:
                name = PurePosixPath(member.name)
                if (
                    member.isfile()
                    and len(name.parts) >= 2
                    and name.parts[-2] == "kanji"
                    and name.name in missing
                ):
                    source = bundle.extractfile(member)
                    if source is None:
                        continue
                    target = missing.pop(name.name)
                    target_tmp = target.with_suffix(".svg.tmp")
                    target_tmp.write_bytes(source.read())
                    _validate_svg(target_tmp)
                    target_tmp.replace(target)
    except (OSError, ValueError, tarfile.TarError) as exc:
        raise RuntimeError(f"Could not extract KanjiVG archive: {exc}") from exc
    if missing:
        raise RuntimeError(
            "KanjiVG archive is missing: " + ", ".join(sorted(missing))
        )
    return targets


def _stroke_number(element: etree.Element) -> int | None:
    suffix = element.get("id", "").rsplit("-s", 1)
    return int(suffix[1]) if len(suffix) == 2 and suffix[1].isdigit() else None


def load_kanjivg_stage(
    stage: KanjiVGStage,
    *,
    cache_dir: str | Path = "data/kanjivg",
    paper: PaperConfig | None = None,
    spacing: float = 0.008,
) -> Trajectory:
    """Load a curated stroke, a marked general radical, or a complete glyph."""

    source = fetch_kanjivg(stage.character, cache_dir)
    selected_types: list[str] = []

    def include(element: etree.Element, ancestors: tuple[etree.Element, ...]) -> bool:
        if stage.stroke_number is not None:
            selected = _stroke_number(element) == stage.stroke_number
        elif stage.radical:
            selected = any(group.get(KVG_RADICAL) == "general" for group in ancestors)
        else:
            selected = True
        if selected:
            selected_types.append(element.get(KVG_TYPE, ""))
        return selected

    try:
        trajectory = load_svg_trajectory(
            source,
            paper=paper,
            spacing=spacing,
            element_filter=include,
        )
    except ValueError as exc:
        raise ValueError(f"KanjiVG stage {stage.slug!r} selected no usable strokes.") from exc
    if stage.expected_type and not any(
        value.startswith(stage.expected_type) for value in selected_types
    ):
        raise ValueError(
            f"KanjiVG stage {stage.slug!r} expected {stage.expected_type!r}, "
            f"found {selected_types!r}."
        )

    strokes = tuple(
        Stroke(
            stroke.points,
            name=f"{stage.slug}-stroke-{index}",
            stroke_type=stroke.stroke_type,
            technique=stroke.technique,
        )
        for index, stroke in enumerate(trajectory.strokes, start=1)
    )
    return Trajectory(
        strokes=strokes,
        source=f"KanjiVG {KANJIVG_REVISION}: {stage.character} {stage.label}",
        character=stage.character,
    )


def load_kanjivg_character(
    character: str,
    *,
    cache_dir: str | Path = "data/kanjivg",
    paper: PaperConfig | None = None,
    spacing: float = 0.008,
) -> Trajectory:
    _validate_character(character)
    return load_kanjivg_stage(
        KanjiVGStage(f"kanji-{ord(character):05x}", character, character),
        cache_dir=cache_dir,
        paper=paper,
        spacing=spacing,
    )


def kanjivg_curriculum(name: str) -> tuple[KanjiVGStage, ...]:
    if name == "techniques":
        return TECHNIQUE_STAGES
    if name == "radicals":
        return RADICAL_STAGES
    if name == "foundations":
        return (*TECHNIQUE_STAGES, *RADICAL_STAGES)
    raise ValueError("KanjiVG curriculum must be techniques, radicals, or foundations.")


def kanjivg_stage(slug: str) -> KanjiVGStage:
    for stage in (*TECHNIQUE_STAGES, *RADICAL_STAGES):
        if stage.slug == slug:
            return stage
    raise ValueError(f"Unknown KanjiVG stage: {slug}")
