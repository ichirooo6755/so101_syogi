from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from so101_calligraphy.training.hard_mining import (
    CoverageError,
    MiningThresholds,
    assess_characters,
    merge_shard_csvs,
    read_character_csv,
    validate_unicode_coverage,
)


def _row(character: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "character": character,
        "success": "1",
        "progress": "1.0",
        "beauty_score": "80",
        "line_width": "75",
        "brushwork": "70",
        "drip_count": "0",
        "collision": "",
        "unintended_ink_fraction": "0.01",
        "width_consistency": "0.9",
        "width_error": "0.1",
    }
    row.update(overrides)
    return row


def test_assessment_reports_all_gates_weakest_component_and_weights() -> None:
    rows = [
        _row("三", collision="self-collision", width_consistency="0.4"),
        _row("一"),
        _row("二", line_width="40"),
    ]
    thresholds = MiningThresholds(
        additional_width_minima=(("width_consistency", 0.8),),
        additional_width_maxima=(("width_error", 0.2),),
    )

    result = assess_characters(rows, "一二三", thresholds=thresholds)

    assert result.coverage.valid
    assert result.failed_indices == (1, 2)
    assert result.failed_characters == ("二", "三")
    assert result.assessments[0].passed
    assert result.assessments[0].checks == {
        "completion": True,
        "safety": True,
        "beauty": True,
        "line_width": True,
        "brushwork": True,
        "width:width_consistency": True,
        "width:width_error": True,
    }
    assert result.assessments[1].weakest_component == "line_width"
    assert result.assessments[2].weakest_component == "safety"
    assert result.assessments[2].checks["width:width_consistency"] is False
    np.testing.assert_allclose(result.sampling_weights.sum(), 1.0)
    assert result.sampling_weights[1] > result.sampling_weights[0]
    assert result.sampling_weights[2] > result.sampling_weights[0]
    assert not result.sampling_weights.flags.writeable
    assert tuple(item.index for item in result.assessments) == (0, 1, 2)


@pytest.mark.parametrize(
    ("overrides", "failed_gate"),
    [
        ({"success": "0"}, "completion"),
        ({"progress": "0.9"}, "completion"),
        ({"drip_count": "1"}, "safety"),
        ({"unintended_ink_fraction": "0.2"}, "safety"),
        ({"beauty_score": "59"}, "beauty"),
        ({"line_width": "64"}, "line_width"),
        ({"brushwork": "61"}, "brushwork"),
        ({"width_error": "0.3"}, "width:width_error"),
    ],
)
def test_each_acceptance_gate_can_fail(
    overrides: dict[str, object], failed_gate: str
) -> None:
    thresholds = MiningThresholds(
        additional_width_maxima=(("width_error", 0.2),)
    )
    result = assess_characters([_row("永", **overrides)], "永", thresholds=thresholds)

    assessment = result.assessments[0]
    assert not assessment.passed
    assert assessment.checks[failed_gate] is False
    assert result.failed_indices == (0,)


def test_beauty_80_threshold_adds_sub_80_glyph_to_hard_pool() -> None:
    result = assess_characters(
        [_row("一", beauty_score="79.99")],
        "一",
        thresholds=MiningThresholds(beauty=80.0),
    )

    assert result.failed_characters == ("一",)
    assert result.assessments[0].checks["beauty"] is False


def test_unicode_validation_detects_normalised_duplicate_and_missing() -> None:
    rows = [{"character": "が"}, {"character": "か\u3099"}]

    report = validate_unicode_coverage(rows, ("が", "木"))

    assert not report.valid
    assert report.duplicate_characters == ("が",)
    assert report.missing_characters == ("木",)
    with pytest.raises(CoverageError) as error:
        validate_unicode_coverage(rows, ("が", "木"), raise_on_error=True)
    assert error.value.report == report


def test_assessment_rejects_unexpected_and_non_finite_data() -> None:
    with pytest.raises(CoverageError):
        assess_characters([_row("一"), _row("外")], "一二")
    with pytest.raises(ValueError, match="must be finite"):
        assess_characters([_row("一", beauty_score="nan")], "一")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("character", "beauty_score"))
        writer.writeheader()
        writer.writerows(rows)


def test_merge_shards_validates_and_orders_by_expected_corpus(tmp_path: Path) -> None:
    shard_0 = tmp_path / "shard-0.csv"
    shard_1 = tmp_path / "shard-1.csv"
    merged_path = tmp_path / "nested" / "characters.csv"
    _write_csv(
        shard_0,
        [
            {"character": "三", "beauty_score": "63"},
            {"character": "一", "beauty_score": "81"},
        ],
    )
    _write_csv(shard_1, [{"character": "二", "beauty_score": "72"}])

    merged = merge_shard_csvs(
        [shard_0, shard_1], "一二三", output_path=merged_path
    )

    assert [row["character"] for row in merged] == ["一", "二", "三"]
    assert read_character_csv(merged_path) == merged


def test_merge_shards_rejects_duplicate_before_writing(tmp_path: Path) -> None:
    shard_0 = tmp_path / "shard-0.csv"
    shard_1 = tmp_path / "shard-1.csv"
    destination = tmp_path / "characters.csv"
    _write_csv(shard_0, [{"character": "一", "beauty_score": "81"}])
    _write_csv(shard_1, [{"character": "一", "beauty_score": "82"}])

    with pytest.raises(CoverageError) as error:
        merge_shard_csvs([shard_0, shard_1], "一二", output_path=destination)

    assert error.value.report.duplicate_characters == ("一",)
    assert error.value.report.missing_characters == ("二",)
    assert not destination.exists()


def test_weighted_sampling_uses_corpus_indices() -> None:
    result = assess_characters(
        [_row("二", line_width="20"), _row("一")],
        "一二",
    )

    sampled = result.sample_indices(12, rng=7)

    assert sampled.shape == (12,)
    assert set(sampled.tolist()) <= {0, 1}
    assert np.count_nonzero(sampled == 1) > np.count_nonzero(sampled == 0)
