from __future__ import annotations

import pytest

from so101_calligraphy.trajectory.kanjivg import (
    KanjiVGStage,
    fetch_kanjivg,
    kanjivg_curriculum,
    load_kanjivg_character,
    load_kanjivg_stage,
)
from so101_calligraphy.trajectory.profile import resolve_technique


def _write_fixture(cache, character: str, groups: str) -> None:
    (cache / f"{ord(character):05x}.svg").write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg"
        xmlns:kvg="http://kanjivg.tagaini.net" viewBox="0 0 109 109">
        <g kvg:element="{character}">{groups}</g>
        </svg>""",
        encoding="utf-8",
    )


def test_technique_selects_numbered_stroke_and_type(tmp_path) -> None:
    _write_fixture(
        tmp_path,
        "一",
        '<path id="kvg:04e00-s1" kvg:type="㇐" d="M10 50 L99 50"/>',
    )
    stage = KanjiVGStage("horizontal", "横画", "一", 1, "㇐")
    trajectory = load_kanjivg_stage(stage, cache_dir=tmp_path)
    assert len(trajectory.strokes) == 1
    assert "KanjiVG" in trajectory.source
    assert trajectory.strokes[0].stroke_type == "㇐"
    assert resolve_technique(trajectory.strokes[0]) == "tome"


def test_radical_selects_only_marked_group(tmp_path) -> None:
    _write_fixture(
        tmp_path,
        "休",
        """<g kvg:element="亻" kvg:radical="general">
          <path id="kvg:04f11-s1" kvg:type="㇒" d="M30 10 L10 70"/>
          <path id="kvg:04f11-s2" kvg:type="㇑" d="M30 30 L30 95"/>
        </g>
        <g kvg:element="木">
          <path id="kvg:04f11-s3" kvg:type="㇐" d="M45 45 L100 45"/>
        </g>""",
    )
    radical = load_kanjivg_stage(
        KanjiVGStage("ninben", "にんべん", "休", radical=True),
        cache_dir=tmp_path,
    )
    complete = load_kanjivg_character("休", cache_dir=tmp_path)
    assert len(radical.strokes) == 2
    assert len(complete.strokes) == 3


def test_cached_fetch_validates_without_network(tmp_path) -> None:
    _write_fixture(
        tmp_path,
        "一",
        '<path id="kvg:04e00-s1" kvg:type="㇐" d="M10 50 L99 50"/>',
    )
    assert fetch_kanjivg("一", tmp_path) == tmp_path / "04e00.svg"


def test_expected_stroke_type_is_checked(tmp_path) -> None:
    _write_fixture(
        tmp_path,
        "一",
        '<path id="kvg:04e00-s1" kvg:type="㇐" d="M10 50 L99 50"/>',
    )
    with pytest.raises(ValueError, match="expected"):
        load_kanjivg_stage(
            KanjiVGStage("wrong", "wrong", "一", 1, "㇑"), cache_dir=tmp_path
        )


def test_foundations_are_techniques_then_radicals() -> None:
    stages = kanjivg_curriculum("foundations")
    assert len(stages) == 14
    assert stages[0].slug == "horizontal"
    assert stages[-1].slug == "gonben"
