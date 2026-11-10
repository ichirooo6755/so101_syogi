from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from PIL import Image

from scripts.prepare_visual_review import prepare_review, review_rows, sha256


def _evaluation(tmp_path: Path):
    directory = tmp_path / "evaluation"
    directory.mkdir()
    rows = []
    for character, glyph, iou in zip("一目旬", (90, 25, 90), (90, 80, 10)):
        row = {
            "character": character, "grade": "1", "beauty_score": "90",
            "line_width": "85", "brushwork": "80", "glyph_shape": str(glyph),
            "exemplar_mask_iou": str(iou), "success": "1", "progress": "1",
            "drip_count": "0", "collision": "", "hard_limit": "False",
        }
        rows.append(row)
        for kind in ("ink", "comparisons"):
            folder = directory / kind
            folder.mkdir(exist_ok=True)
            Image.new("RGB", (64, 64), "white").save(folder / f"{ord(character):05x}-{character}.png")
    _write_rows(directory, rows)
    summary = {
        "model": str(tmp_path / "model.zip"),
        "all_joyo_evaluated": True,
        "acceptance": {"all_complete": True},
        "evaluation": {
            "count": 3, "ablation": "all",
            "component_means": {"line_width": 85, "brushwork": 80, "glyph_shape": 68.333333},
            "technique_means": {"harai": {"count": 3, "finish": 75, "width": 80}},
        },
    }
    (directory / "summary.json").write_text(json.dumps(summary))
    model = tmp_path / "model.zip"
    model.write_bytes(b"offline model identity fixture")
    return directory, model, rows


def _write_rows(directory, rows):
    with (directory / "characters.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_review_preserves_metrics_hashes_and_requires_human_decision(tmp_path: Path):
    directory, model, rows = _evaluation(tmp_path)
    output = tmp_path / "review"
    result = prepare_review(directory, output, expected=tuple("一目旬"), model=model, weakest=1)
    assert result["visual_acceptance"] == "pending_human_review"
    assert result["historical_model_hash_verified"] is False
    assert result["count"] == 3
    assert result["model_sha256_at_review"] == sha256(model)
    assert result["visual_metrics"]["exemplar_mask_iou"]["mean"] == 60
    assert all(result["acceptance"].values())
    assert [row["character"] for row in result["selected"]] == ["一", "目", "旬"]
    with (output / "ranked-characters.csv").open() as handle:
        assert next(csv.DictReader(handle))["character"] == "目"
    with Image.open(output / "ink-contact-sheet.png") as image:
        image.verify()
    assert (output / "review.md").is_file()
    with pytest.raises(ValueError, match="already exists"):
        prepare_review(directory, output, expected=tuple("一目旬"), model=model)


@pytest.mark.parametrize("field,value", [
    ("progress", "0.9"), ("success", "0"), ("hard_limit", "True"),
    ("line_width", "10"), ("exemplar_mask_iou", "nan"),
])
def test_review_rejects_bad_rows_even_when_stored_acceptance_passes(tmp_path: Path, field, value):
    directory, model, rows = _evaluation(tmp_path)
    rows[0][field] = value
    _write_rows(directory, rows)
    with pytest.raises(ValueError):
        prepare_review(directory, tmp_path / "review", expected=tuple("一目旬"), model=model)
    assert not (tmp_path / "review").exists()


def test_review_rejects_missing_corpus_character_and_missing_weak_image(tmp_path: Path):
    directory, model, _ = _evaluation(tmp_path)
    with pytest.raises(ValueError, match="coverage"):
        prepare_review(directory, tmp_path / "review", expected=tuple("一目旬二"), model=model)
    (directory / "ink" / "076ee-目.png").unlink()
    with pytest.raises(ValueError, match="目"):
        prepare_review(directory, tmp_path / "review", expected=tuple("一目旬"), model=model)
    assert not (tmp_path / "review").exists()


def test_grade_sampling_and_visual_selection_ignore_csv_order(tmp_path: Path):
    _, _, rows = _evaluation(tmp_path)
    assert review_rows(rows, seed=17, weakest=1) == review_rows(list(reversed(rows)), seed=17, weakest=1)


@pytest.mark.parametrize("change", ["ablation", "model", "model_sha256", "acceptance"])
def test_review_rejects_incomplete_or_mismatched_evaluation_provenance(tmp_path: Path, change):
    directory, model, _ = _evaluation(tmp_path)
    path = directory / "summary.json"
    summary = json.loads(path.read_text())
    if change == "ablation":
        summary["evaluation"]["ablation"] = "no_brushwork"
    elif change == "model":
        del summary["model"]
    elif change == "model_sha256":
        summary["model_sha256"] = "0" * 64
    else:
        summary["acceptance"]["all_complete"] = False
    path.write_text(json.dumps(summary))
    with pytest.raises(ValueError):
        prepare_review(directory, tmp_path / "review", expected=tuple("一目旬"), model=model)
    assert not (tmp_path / "review").exists()
