"""Hiragana and katakana trajectories from KanjiVG (no AnimCJK dependency)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from so101_calligraphy.config import PaperConfig
from so101_calligraphy.trajectory.kanjivg import fetch_kanjivg_many, load_kanjivg_character
from so101_calligraphy.trajectory.types import Trajectory

# Basic gojuon + small kana + prolonged sound for brush drills.
HIRAGANA = (
    "あいうえおかきくけこさしすせそたちつてとなにぬねの"
    "はひふへほまみむめもやゆよらりるれろわをん"
    "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
    "ぁぃぅぇぉっゃゅょー"
)
KATAKANA = (
    "アイウエオカキクケコサシスセソタチツテトナニヌネノ"
    "ハヒフヘホマミムメモヤユヨラリルレロワヲン"
    "ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ"
    "ァィゥェォッャュョー"
)


def kana_characters(*, include_voiced: bool = True) -> tuple[str, ...]:
    if include_voiced:
        return tuple(dict.fromkeys(HIRAGANA + KATAKANA))
    plain_hira = HIRAGANA[:84]
    plain_kata = KATAKANA[:84]
    return tuple(dict.fromkeys(plain_hira + plain_kata))


def load_kana_trajectories(
    characters: Sequence[str] | None = None,
    *,
    kanjivg_cache: str | Path = "data/kanjivg",
    spacing: float = 0.008,
    paper: PaperConfig | None = None,
) -> tuple[Trajectory, ...]:
    """Load kana centre-lines; widths come later from kaisho brushwork laws."""

    glyphs = tuple(characters) if characters is not None else kana_characters()
    if not glyphs:
        raise ValueError("No kana characters requested.")
    fetch_kanjivg_many(glyphs, cache_dir=kanjivg_cache)
    trajectories: list[Trajectory] = []
    for character in glyphs:
        trajectory = load_kanjivg_character(
            character, cache_dir=kanjivg_cache, spacing=spacing, paper=paper
        )
        trajectories.append(
            Trajectory(
                strokes=trajectory.strokes,
                source=f"{trajectory.source}; kana brushwork widths",
                character=character,
            )
        )
    return tuple(trajectories)
