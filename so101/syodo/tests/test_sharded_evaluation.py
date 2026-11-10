from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "evaluate_joyo_shards.py"
SPEC = importlib.util.spec_from_file_location("evaluate_joyo_shards", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
evaluate_joyo_shards = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluate_joyo_shards)


def _row(
    character: str,
    beauty: float,
    *,
    success: int = 1,
    drips: int = 0,
    collision: str = "",
) -> dict[str, str]:
    return {
        "character": character,
        "success": str(success),
        "beauty_score": str(beauty),
        "drip_count": str(drips),
        "collision": collision,
        "shape": str(beauty + 1.0),
    }


def _summary(
    count: int,
    *,
    technique_count: int,
    finish: float,
    width: float,
) -> dict[str, object]:
    return {
        "evaluation": {
            "ablation": "all",
            "count": count,
            "component_means": {"shape": 0.0},
            "technique_means": {
                "tome": {
                    "count": technique_count,
                    "finish": finish,
                    "width": width,
                }
            },
        }
    }


def _layout_rows(characters: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for character in characters:
        for layout in range(6):
            row = _row(character, 70.0 + layout)
            row.update(
                layout_index=str(layout),
                writing_frame_size_m="0.085",
                pressure_calibration_sample_count="10",
                pressure_calibration_clipped_count=str(layout),
                pressure_calibration_fallback_count=str(layout % 2),
            )
            rows.append(row)
    return rows


def test_merge_shards_validates_and_recomputes_combined_results() -> None:
    rows, result = evaluate_joyo_shards.merge_shards(
        [
            [_row("一", 80.0), _row("三", 60.0, success=0, collision="table")],
            [_row("二", 70.0, drips=2), _row("四", 90.0)],
        ],
        [
            _summary(2, technique_count=1, finish=10.0, width=20.0),
            _summary(2, technique_count=3, finish=30.0, width=40.0),
        ],
        ("一", "二", "三", "四"),
    )

    assert [row["character"] for row in rows] == ["一", "二", "三", "四"]
    assert result["count"] == 4
    assert result["success_rate"] == 0.75
    assert result["mean_beauty_score"] == 75.0
    assert result["p10_beauty_score"] == pytest.approx(
        np.percentile([80.0, 70.0, 60.0, 90.0], 10)
    )
    assert result["minimum_beauty_score"] == 60.0
    assert result["total_drips"] == 2
    assert result["collision_count"] == 1
    assert result["component_means"] == {"shape": 76.0}
    assert result["component_minimums"] == {"shape": 61.0}
    assert result["technique_means"]["tome"] == {
        "count": 4,
        "finish": 25.0,
        "width": 35.0,
    }


def test_merge_shards_rejects_unicode_duplicates_and_missing_characters() -> None:
    with pytest.raises(
        ValueError,
        match=r"duplicates=U\+4E00.*missing=U\+4E8C",
    ):
        evaluate_joyo_shards.merge_shards(
            [[_row("一", 80.0)], [_row("一", 90.0)]],
            [
                _summary(1, technique_count=1, finish=10.0, width=20.0),
                _summary(1, technique_count=1, finish=30.0, width=40.0),
            ],
            ("一", "二"),
        )


def test_merge_shards_accepts_exactly_six_a4_layouts_per_character() -> None:
    rows = []
    for character in ("一", "二"):
        for layout in range(6):
            row = _row(character, 80.0 + layout)
            row.update(layout_index=str(layout), writing_frame_size_m="0.085")
            rows.append(row)

    merged, result = evaluate_joyo_shards.merge_shards(
        [rows[:6], rows[6:]],
        [
            _summary(6, technique_count=1, finish=10.0, width=20.0),
            _summary(6, technique_count=1, finish=20.0, width=30.0),
        ],
        ("一", "二"),
    )

    assert len(merged) == 12
    assert result["count"] == 12
    assert result["layout_count"] == 6


def test_merge_shards_accepts_exactly_one_center_layout_per_character() -> None:
    rows = []
    for character in ("一", "二"):
        row = _row(character, 80.0)
        row.update(layout_index="0", writing_frame_size_m="0.110")
        rows.append(row)

    merged, result = evaluate_joyo_shards.merge_shards(
        [[rows[0]], [rows[1]]],
        [
            _summary(1, technique_count=1, finish=10.0, width=20.0),
            _summary(1, technique_count=1, finish=20.0, width=30.0),
        ],
        ("一", "二"),
        layouts=(0,),
    )

    assert len(merged) == 2
    assert result["count"] == 2
    assert result["unique_character_count"] == 2
    assert result["layout_count"] == 1
    assert result["layout_summaries"]["0"]["count"] == 2


def test_center_merge_rejects_duplicate_and_missing_layout_zero_rows() -> None:
    row = _row("一", 80.0)
    row["layout_index"] = "0"

    with pytest.raises(ValueError, match=r"duplicates=U\+4E00.*missing=U\+4E8C"):
        evaluate_joyo_shards.merge_shards(
            [[row], [row]],
            [
                _summary(1, technique_count=1, finish=10.0, width=20.0),
                _summary(1, technique_count=1, finish=20.0, width=30.0),
            ],
            ("一", "二"),
            layouts=(0,),
        )


def test_merge_reports_layout_and_pressure_calibration_aggregates() -> None:
    rows = _layout_rows("一二")
    summaries = [
        _summary(6, technique_count=1, finish=10.0, width=20.0),
        _summary(6, technique_count=1, finish=20.0, width=30.0),
    ]
    for summary in summaries:
        summary["pressure_calibration"] = {
            "schema_version": 1,
            "fingerprint": "abc123",
            "provenance": {"git_sha": "deadbeef"},
        }

    _, result = evaluate_joyo_shards.merge_shards(
        [rows[:6], rows[6:]], summaries, ("一", "二")
    )

    assert result["unique_character_count"] == 2
    assert set(result["layout_summaries"]) == {str(index) for index in range(6)}
    assert result["layout_summaries"]["3"] == {
        "count": 2,
        "mean_beauty_score": 73.0,
        "p10_beauty_score": 73.0,
    }
    assert result["pressure_calibration"]["fingerprint"] == "abc123"
    assert result["pressure_calibration_sample_count"] == 120
    assert result["pressure_calibration_clip_rate"] == pytest.approx(30 / 120)
    assert result["pressure_calibration_fallback_rate"] == pytest.approx(6 / 120)


def test_limited_128_character_shape_is_exactly_768_rows() -> None:
    characters = tuple(chr(0x4E00 + index) for index in range(128))
    rows = _layout_rows("".join(characters))
    _, result = evaluate_joyo_shards.merge_shards(
        [rows],
        [_summary(768, technique_count=1, finish=10.0, width=20.0)],
        characters,
    )
    assert result["count"] == 768
    assert result["unique_character_count"] == 128
    assert result["layout_count"] == 6


def test_full_evaluation_shape_requires_12816_rows() -> None:
    evaluate_joyo_shards.validate_evaluation_shape(
        count=12_816, unique_character_count=2_136, layout_count=6, full=True
    )
    with pytest.raises(ValueError, match="12,816"):
        evaluate_joyo_shards.validate_evaluation_shape(
            count=2_136, unique_character_count=2_136, layout_count=1, full=True
        )


def test_full_center_evaluation_shape_is_exactly_2136_rows() -> None:
    evaluate_joyo_shards.validate_evaluation_shape(
        count=2_136,
        unique_character_count=2_136,
        layout_count=1,
        full=True,
        layouts=(0,),
    )
    with pytest.raises(ValueError, match="2,136"):
        evaluate_joyo_shards.validate_evaluation_shape(
            count=2_135,
            unique_character_count=2_135,
            layout_count=1,
            full=True,
            layouts=(0,),
        )


def test_merge_shards_weights_endpoint_scores_by_exposed_end_count() -> None:
    first = _row("一", 80.0)
    first.update(
        endpoint_triangle_count="2",
        endpoint_triangle_sum="170",
        endpoint_triangle_minimum="80",
    )
    second = _row("十", 81.0)
    second.update(
        endpoint_triangle_count="1",
        endpoint_triangle_sum="70",
        endpoint_triangle_minimum="70",
    )

    _, result = evaluate_joyo_shards.merge_shards(
        [[first], [second]],
        [
            _summary(1, technique_count=1, finish=10.0, width=20.0),
            _summary(1, technique_count=1, finish=20.0, width=30.0),
        ],
        ("一", "十"),
    )

    assert result["endpoint_triangle"] == {
        "count": 3,
        "mean": 80.0,
        "minimum": 70.0,
    }


def test_limited_eval_uses_one_even_sample_across_all_shards() -> None:
    assert evaluate_joyo_shards.sample_expected_joyo(tuple("一二三四五六七八九十"), 3) == (
        "一",
        "五",
        "十",
    )


def test_dry_run_saves_every_complete_command_without_starting_evaluation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_popen(*_args, **_kwargs):
        raise AssertionError("dry-run must not launch subprocesses")

    monkeypatch.setattr(evaluate_joyo_shards.subprocess, "Popen", unexpected_popen)
    output = tmp_path / "evaluation output"
    model = tmp_path / "not-created-model.zip"
    calibration = tmp_path / "pressure.json"
    returncode = evaluate_joyo_shards.main(
        [
            "--model",
            str(model),
            "--output",
            str(output),
            "--shards",
            "3",
            "--device",
            "mps",
            "--seed",
            "91",
            "--eval-limit",
            "128",
            "--pressure-calibration",
            str(calibration),
            "--dry-run",
        ]
    )

    assert returncode == 0
    manifest = json.loads((output / "commands.json").read_text(encoding="utf-8"))
    assert len(manifest["commands"]) == 3
    assert capsys.readouterr().out.count("--expert-only") == 3
    for shard_index, entry in enumerate(manifest["commands"]):
        command = entry["argv"]
        assert command[:3] == [
            evaluate_joyo_shards.sys.executable,
            "-m",
            "so101_calligraphy.training.professional",
        ]
        assert command[command.index("--initial-model") + 1] == str(model.resolve())
        assert command[command.index("--eval-limit") + 1] == "128"
        assert command[command.index("--eval-shard-count") + 1] == "3"
        assert command[command.index("--eval-shard-index") + 1] == str(shard_index)
        assert "--save-all-ink" in command
        assert command[command.index("--device") + 1] == "mps"
        assert command[command.index("--seed") + 1] == "91"
        assert command[command.index("--pressure-calibration") + 1] == str(
            calibration.resolve()
        )
        assert "--require-pressure-calibration" in command
        assert entry["shell"]


def test_dry_run_center_analytical_control_omits_model_and_uses_layout_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_popen(*_args, **_kwargs):
        raise AssertionError("dry-run must not launch subprocesses")

    monkeypatch.setattr(evaluate_joyo_shards.subprocess, "Popen", unexpected_popen)
    output = tmp_path / "center-analytical"

    returncode = evaluate_joyo_shards.main(
        [
            "--output",
            str(output),
            "--shards",
            "4",
            "--brushmark-layout",
            "--center110-profile",
            "p10-80-v1",
            "--dry-run",
        ]
    )

    assert returncode == 0
    manifest = json.loads((output / "commands.json").read_text(encoding="utf-8"))
    assert manifest["model"] is None
    assert manifest["eval_layouts"] == [0]
    assert manifest["brushmark_layout"] is True
    assert manifest["center110_profile"] == "p10-80-v1"
    for entry in manifest["commands"]:
        command = entry["argv"]
        assert "--initial-model" not in command
        assert "--brushmark-layout" in command
        assert command[command.index("--center110-profile") + 1] == "p10-80-v1"
        assert command[command.index("--eval-layouts") + 1] == "0"
