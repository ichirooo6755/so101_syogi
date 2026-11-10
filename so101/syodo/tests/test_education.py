from __future__ import annotations

import gzip
import io
from pathlib import Path
import tarfile

from so101_calligraphy.trajectory import education, kanjivg


def test_cached_kanjidic2_has_all_expected_grades(tmp_path: Path) -> None:
    cache = tmp_path / "kanjidic2"
    cache.mkdir()
    characters = iter(chr(code) for code in range(0x4E00, 0x9FFF))
    entries = []
    for grade, count in education.EXPECTED_GRADE_COUNTS.items():
        for _ in range(count):
            entries.append(
                f"<character><literal>{next(characters)}</literal>"
                f"<misc><grade>{grade}</grade><stroke_count>{grade}</stroke_count>"
                "</misc></character>"
            )
    with gzip.open(cache / "kanjidic2.xml.gz", "wt", encoding="utf-8") as handle:
        handle.write(f"<kanjidic2>{''.join(entries)}</kanjidic2>")

    result = education.load_education_kanji(cache)
    assert len(result) == 1026
    assert result[0].grade == 1
    assert result[-1].grade == 6


def test_cached_kanjidic2_validates_all_joyo_grades(tmp_path: Path) -> None:
    cache = tmp_path / "kanjidic2"
    cache.mkdir()
    characters = iter(chr(code) for code in range(0x3400, 0x9FFF))
    entries = []
    for grade, count in education.EXPECTED_JOYO_GRADE_COUNTS.items():
        for _ in range(count):
            entries.append(
                f"<character><literal>{next(characters)}</literal>"
                f"<misc><grade>{grade}</grade><stroke_count>{grade}</stroke_count>"
                "</misc></character>"
            )
    with gzip.open(cache / "kanjidic2.xml.gz", "wt", encoding="utf-8") as handle:
        handle.write(f"<kanjidic2>{''.join(entries)}</kanjidic2>")

    result = education.load_joyo_kanji(cache)
    assert len(result) == 2136
    assert sum(entry.grade == 8 for entry in result) == 1110


def test_bulk_kanjivg_fetch_extracts_only_requested_svg(
    tmp_path: Path, monkeypatch
) -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 1"/></svg>'
    archive = tmp_path / "source.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        info = tarfile.TarInfo("kanjivg-test/kanji/04e00.svg")
        info.size = len(svg)
        bundle.addfile(info, io.BytesIO(svg))
    monkeypatch.setattr(kanjivg, "KANJIVG_ARCHIVE_URL", archive.as_uri())

    cache = tmp_path / "kanjivg"
    result = kanjivg.fetch_kanjivg_many(["一"], cache)
    assert result == (cache / "04e00.svg",)
    assert result[0].read_bytes() == svg
