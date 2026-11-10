"""Elementary and complete joyo kanji metadata and trajectory loading."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
import gzip
from pathlib import Path
import urllib.error
import urllib.request
import xml.etree.ElementTree as etree

from so101_calligraphy.config import PaperConfig
from so101_calligraphy.trajectory.kanjivg import (
    fetch_kanjivg_many,
    load_kanjivg_character,
)
from so101_calligraphy.trajectory.animcjk import enrich_many_with_animcjk_widths
from so101_calligraphy.trajectory.types import Trajectory


KANJIDIC2_URL = "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz"
EXPECTED_GRADE_COUNTS = {1: 80, 2: 160, 3: 200, 4: 202, 5: 193, 6: 191}
EXPECTED_JOYO_GRADE_COUNTS = EXPECTED_GRADE_COUNTS | {8: 1110}


@dataclass(frozen=True)
class EducationKanji:
    character: str
    grade: int
    stroke_count: int


class JoyoTrajectoryDataset(Sequence[Trajectory]):
    """Memory-bounded, random-access trajectories for all 2,136 joyo kanji."""

    def __init__(
        self,
        entries: Sequence[EducationKanji],
        *,
        kanjivg_cache: str | Path = "data/kanjivg",
        animcjk_cache: str | Path | None = "data/animcjk",
        cache_size: int = 48,
        use_animcjk_medians: bool = False,
        paper: PaperConfig | None = None,
        spacing: float = 0.008,
    ) -> None:
        if cache_size <= 0:
            raise ValueError("cache_size must be positive")
        if spacing <= 0.0:
            raise ValueError("spacing must be positive")
        self.entries = tuple(entries)
        self.kanjivg_cache = Path(kanjivg_cache)
        self.animcjk_cache = None if animcjk_cache is None else Path(animcjk_cache)
        self.cache_size = cache_size
        self.use_animcjk_medians = use_animcjk_medians
        self.paper = paper or PaperConfig()
        self.spacing = spacing
        self._cache: dict[int, Trajectory] = {}
        self._order: list[int] = []

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, index: int | slice) -> Trajectory | tuple[Trajectory, ...]:
        if isinstance(index, slice):
            return tuple(self[position] for position in range(*index.indices(len(self))))
        position = int(index)
        if position < 0:
            position += len(self)
        if not 0 <= position < len(self):
            raise IndexError(position)
        if position in self._cache:
            self._order.remove(position)
            self._order.append(position)
            return self._cache[position]
        entry = self.entries[position]
        trajectory = load_kanjivg_character(
            entry.character,
            cache_dir=self.kanjivg_cache,
            paper=self.paper,
            spacing=self.spacing,
        )
        if self.animcjk_cache is not None:
            trajectory = enrich_many_with_animcjk_widths(
                ((trajectory, entry.character, None),),
                cache_dir=self.animcjk_cache,
                paper=self.paper,
                use_medians=self.use_animcjk_medians,
                spacing=self.spacing,
            )[0]
        self._cache[position] = trajectory
        self._order.append(position)
        if len(self._order) > self.cache_size:
            del self._cache[self._order.pop(0)]
        return trajectory

    def __iter__(self) -> Iterator[Trajectory]:
        return (self[index] for index in range(len(self)))


def _read_kanji(
    path: Path,
    expected_counts: dict[int, int],
) -> tuple[EducationKanji, ...]:
    try:
        with gzip.open(path, "rb") as handle:
            root = etree.parse(handle).getroot()
    except (OSError, etree.ParseError) as exc:
        raise ValueError(f"Invalid KANJIDIC2 cache {path}: {exc}") from exc

    entries: list[EducationKanji] = []
    for element in root.findall("character"):
        grade_text = element.findtext("misc/grade")
        if grade_text is None or int(grade_text) not in expected_counts:
            continue
        character = element.findtext("literal")
        stroke_text = element.findtext("misc/stroke_count")
        if character is None or stroke_text is None:
            raise ValueError("KANJIDIC2 education-kanji entry is incomplete.")
        entries.append(EducationKanji(character, int(grade_text), int(stroke_text)))

    counts = Counter(entry.grade for entry in entries)
    if dict(sorted(counts.items())) != expected_counts:
        raise ValueError(
            f"KANJIDIC2 grade counts are {dict(sorted(counts.items()))}, "
            f"expected {expected_counts}."
        )
    return tuple(
        sorted(entries, key=lambda entry: (entry.grade, entry.stroke_count, entry.character))
    )


def _read_education_kanji(path: Path) -> tuple[EducationKanji, ...]:
    return _read_kanji(path, EXPECTED_GRADE_COUNTS)


def _read_joyo_kanji(path: Path) -> tuple[EducationKanji, ...]:
    return _read_kanji(path, EXPECTED_JOYO_GRADE_COUNTS)


def load_education_kanji(
    cache_dir: str | Path = "data/kanjidic2",
    *,
    refresh: bool = False,
) -> tuple[EducationKanji, ...]:
    """Fetch and validate the current KANJIDIC2 elementary grade list."""

    cache_dir = Path(cache_dir).expanduser().resolve()
    target = cache_dir / "kanjidic2.xml.gz"
    if refresh:
        target.unlink(missing_ok=True)
    if target.exists():
        return _read_education_kanji(target)

    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.tmp")
    request = urllib.request.Request(
        KANJIDIC2_URL,
        headers={"User-Agent": "so101-calligraphy/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            temporary.write_bytes(response.read())
        entries = _read_education_kanji(temporary)
        temporary.replace(target)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Could not fetch KANJIDIC2: {exc}") from exc
    return entries


def load_joyo_kanji(
    cache_dir: str | Path = "data/kanjidic2",
    *,
    refresh: bool = False,
) -> tuple[EducationKanji, ...]:
    """Fetch and validate all 2,136 grade 1–6 and grade-8 joyo kanji."""

    cache_dir = Path(cache_dir).expanduser().resolve()
    target = cache_dir / "kanjidic2.xml.gz"
    if refresh:
        target.unlink(missing_ok=True)
    if not target.exists():
        load_education_kanji(cache_dir, refresh=False)
    return _read_joyo_kanji(target)


def load_education_trajectories(
    entries: tuple[EducationKanji, ...],
    *,
    kanjivg_cache: str | Path = "data/kanjivg",
    animcjk_cache: str | Path | None = None,
    paper: PaperConfig | None = None,
    spacing: float = 0.008,
) -> tuple[Trajectory, ...]:
    """Load a validated trajectory for every supplied education kanji."""

    fetch_kanjivg_many([entry.character for entry in entries], kanjivg_cache)
    trajectories = tuple(
        load_kanjivg_character(
            entry.character,
            cache_dir=kanjivg_cache,
            paper=paper,
            spacing=spacing,
        )
        for entry in entries
    )
    if animcjk_cache is None:
        return trajectories
    return enrich_many_with_animcjk_widths(
        (
            (trajectory, entry.character, None)
            for trajectory, entry in zip(trajectories, entries, strict=True)
        ),
        cache_dir=animcjk_cache,
        paper=paper,
        spacing=spacing,
    )


def load_joyo_trajectories(
    entries: tuple[EducationKanji, ...],
    *,
    kanjivg_cache: str | Path = "data/kanjivg",
    animcjk_cache: str | Path | None = None,
    paper: PaperConfig | None = None,
    spacing: float = 0.008,
) -> tuple[Trajectory, ...]:
    """Load validated KanjiVG/AnimCJK trajectories for supplied joyo entries."""

    return load_education_trajectories(
        entries,
        kanjivg_cache=kanjivg_cache,
        animcjk_cache=animcjk_cache,
        paper=paper,
        spacing=spacing,
    )


def lazy_joyo_trajectories(
    entries: Sequence[EducationKanji],
    *,
    kanjivg_cache: str | Path = "data/kanjivg",
    animcjk_cache: str | Path | None = "data/animcjk",
    cache_size: int = 48,
    use_animcjk_medians: bool = False,
    paper: PaperConfig | None = None,
    spacing: float = 0.008,
) -> JoyoTrajectoryDataset:
    """Fetch source files and return an LRU-backed joyo trajectory sequence."""

    fetch_kanjivg_many([entry.character for entry in entries], kanjivg_cache)
    return JoyoTrajectoryDataset(
        entries,
        kanjivg_cache=kanjivg_cache,
        animcjk_cache=animcjk_cache,
        cache_size=cache_size,
        use_animcjk_medians=use_animcjk_medians,
        paper=paper,
        spacing=spacing,
    )
