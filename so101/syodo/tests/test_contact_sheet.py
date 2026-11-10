from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest
from PIL import Image


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "render_ppo_contact_sheet.py"
SPEC = importlib.util.spec_from_file_location("render_ppo_contact_sheet", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
contact_sheet = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contact_sheet)


def _row(
    character: str,
    grade: str,
    beauty: float,
    line_width: float,
    brushwork: float,
) -> dict[str, str]:
    return {
        "character": character,
        "grade": grade,
        "beauty_score": str(beauty),
        "line_width": str(line_width),
        "brushwork": str(brushwork),
    }


def _write_csv(directory: Path, rows: list[dict[str, str]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "characters.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def _write_image(path: Path, color: str = "white") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (80, 60), color).save(path)


def test_selection_is_ordered_union_and_does_not_consult_images() -> None:
    rows = [
        _row("甲", "1", 10, 90, 90),
        _row("乙", "1", 20, 10, 80),
        _row("丙", "2", 30, 80, 5),
        _row("丁", "2", 40, 70, 70),
        _row("戊", "3", 50, 60, 60),
    ]

    selected = contact_sheet.select_rows(
        rows,
        representatives=("丁", "甲"),
        grade_per_stratum=1,
        beauty_quantiles=(0.0, 0.5, 1.0),
        weakest_count=1,
    )

    assert [row["character"] for row in selected] == ["丁", "甲", "乙", "戊", "丙"]
    assert len({row["character"] for row in selected}) == len(selected)


def test_selection_supports_multiple_samples_per_grade() -> None:
    rows = [
        _row("一", "1", 10, 50, 50),
        _row("二", "1", 20, 50, 50),
        _row("三", "1", 30, 50, 50),
        _row("四", "1", 40, 50, 50),
    ]

    selected = contact_sheet.select_rows(
        rows,
        representatives=(),
        grade_per_stratum=2,
        beauty_quantiles=(),
        weakest_count=0,
    )

    assert [row["character"] for row in selected] == ["二", "三"]


def test_visual_weakness_selection_uses_glyph_and_iou_independent_of_beauty() -> None:
    rows = [_row("一", "1", 90, 80, 80), _row("目", "1", 95, 80, 80), _row("旬", "1", 96, 80, 80)]
    for row, glyph, iou in zip(rows, (80, 20, 30), (80, 40, 10)):
        row.update(glyph_shape=str(glyph), exemplar_mask_iou=str(iou))
    selected = contact_sheet.select_rows(
        rows, representatives=(), grade_per_stratum=0, beauty_quantiles=(),
        weakest_count=1, weakest_metrics=("glyph_shape", "exemplar_mask_iou"),
    )
    assert [row["character"] for row in selected] == ["目", "旬"]
    rows[-1]["exemplar_mask_iou"] = "nan"
    with pytest.raises(contact_sheet.ContactSheetError, match="有限値"):
        contact_sheet.select_rows(rows, weakest_metrics=("exemplar_mask_iou",))


def test_load_rows_reports_missing_metric_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "characters.csv"
    csv_path.write_text(
        "character,grade,beauty_score,line_width\n一,1,80,70\n",
        encoding="utf-8",
    )

    with pytest.raises(contact_sheet.ContactSheetError, match="brushwork"):
        contact_sheet.load_character_rows(csv_path)


def test_resolve_images_reports_every_missing_character(tmp_path: Path) -> None:
    rows = [
        _row("一", "1", 80, 70, 60),
        _row("十", "1", 70, 60, 50),
        _row("水", "1", 60, 50, 40),
    ]
    _write_image(tmp_path / "ink" / "04e00-一.png")

    with pytest.raises(contact_sheet.ContactSheetError) as error:
        contact_sheet.resolve_images(rows, tmp_path)

    message = str(error.value)
    assert "十" in message and "水" in message
    assert "ink" in message


def test_auto_source_falls_back_to_comparisons_and_renders_grid(
    tmp_path: Path,
) -> None:
    rows = [
        _row("一", "1", 80, 70, 60),
        _row("十", "1", 70, 60, 50),
        _row("水", "1", 60, 50, 40),
    ]
    _write_csv(tmp_path, rows)
    for row in rows:
        character = row["character"]
        _write_image(
            tmp_path / "comparisons" / f"{ord(character):05x}-{character}.png"
        )

    output = tmp_path / "result.png"
    result = contact_sheet.main(
        [
            str(tmp_path),
            "--output",
            str(output),
            "--columns",
            "2",
            "--cell-width",
            "180",
            "--cell-height",
            "180",
        ]
    )

    assert result == 0
    with Image.open(output) as image:
        assert image.size == (360, 360)
        assert image.format == "PNG"
