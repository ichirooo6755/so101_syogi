from __future__ import annotations

from pathlib import Path
import math

import scripts.run_gate3_recovery as gate3
from scripts.search_gate_recovery import Candidate


def _row(character: str, layout: int) -> dict[str, object]:
    return {
        "character": character,
        "layout_index": layout,
        "is_success": True,
        "collision_types": [],
        "hard_limit": False,
        "lost_holes": 0,
        "pressure_error_median_abs": 0.05,
        "pressure_error_p90_abs": 0.15,
        "width_ratio_median": 1.0,
        "opening_p90": 1.0,
        "beauty_score": 80.0,
        "pressure_calibration_samples": [],
    }


def test_gate3_uses_eight_disjoint_shards_of_128_characters(tmp_path: Path) -> None:
    command = gate3.shard_command(
        output=tmp_path / "shard-3.json",
        calibration=tmp_path / "pressure.json",
        candidate=Candidate(0.002, 0.45, 0.85),
        shard_index=3,
        model=tmp_path / "model.zip",
    )

    assert command[command.index("--eval-limit") + 1] == "128"
    assert command[command.index("--eval-shard-count") + 1] == "8"
    assert command[command.index("--eval-shard-index") + 1] == "3"
    assert command[command.index("--gate-level") + 1] == "0"


def test_gate3_shard_command_propagates_relaxed_profile(tmp_path: Path) -> None:
    command = gate3.shard_command(
        output=tmp_path / "shard-0.json",
        calibration=tmp_path / "pressure.json",
        candidate=Candidate(0.002, 0.45, 0.85),
        shard_index=0,
        model=None,
        threshold_profile="relaxed-recovery",
    )

    assert command[command.index("--threshold-profile") + 1] == "relaxed-recovery"


def test_gate3_shard_command_can_explicitly_omit_calibration_for_relaxed_profile(
    tmp_path: Path,
) -> None:
    command = gate3.shard_command(
        output=tmp_path / "shard-0.json",
        calibration=None,
        candidate=Candidate(0.002, 0.45, 0.85),
        shard_index=0,
        model=None,
        threshold_profile="relaxed-recovery",
    )

    assert "--pressure-calibration" not in command


def test_gate3_merge_requires_exact_128_by_six_shape() -> None:
    characters = [chr(0x4E00 + index) for index in range(128)]
    reports = []
    for shard in range(8):
        shard_chars = characters[shard::8]
        reports.append(
            {
                "summary": {"configuration_fingerprint": "config-1"},
                "results": [_row(character, layout) for character in shard_chars for layout in range(6)],
            }
        )

    merged = gate3.merge_reports(reports)

    assert merged["summary"]["evaluations"] == 768
    assert merged["summary"]["passed"]
    assert merged["summary"]["ready_for_r1"]

    reports[0]["results"].pop()
    invalid = gate3.merge_reports(reports)
    assert not invalid["summary"]["gates"]["evaluation_count"]


def test_relaxed_gate3_merge_passes_but_has_no_r1_authority() -> None:
    characters = [chr(0x4E00 + index) for index in range(128)]
    reports = []
    for shard in range(8):
        shard_chars = characters[shard::8]
        rows = [_row(character, layout) for character in shard_chars for layout in range(6)]
        if shard == 0:
            for row in rows[:14]:
                row["is_success"] = False
                row["collision_types"] = ["arm-floor"]
                row["lost_holes"] = 1
                row["pressure_error_p90_abs"] = 0.60
                row["width_ratio_median"] = 0.71
        reports.append(
            {
                "summary": {"configuration_fingerprint": "config-1"},
                "results": rows,
            }
        )

    merged = gate3.merge_reports(reports, threshold_profile="relaxed-recovery")

    assert merged["summary"]["passed"]
    assert not merged["summary"]["ready_for_r1"]


def test_relaxed_r1_gate3_merge_is_explicitly_authorized() -> None:
    characters = [chr(0x4E00 + index) for index in range(128)]
    reports = [
        {
            "summary": {"configuration_fingerprint": "config-1"},
            "results": [
                _row(character, layout)
                for character in characters[shard::8]
                for layout in range(6)
            ],
        }
        for shard in range(8)
    ]

    merged = gate3.merge_reports(reports, threshold_profile="relaxed-r1")

    assert merged["summary"]["passed"]
    assert merged["summary"]["ready_for_r1"]


def test_gate3_evidence_paths_are_portable_inside_the_repository(tmp_path: Path) -> None:
    assert gate3._evidence_path(gate3.ROOT / "runs" / "gate.json") == "runs/gate.json"
    assert gate3._evidence_path(tmp_path / "external.json") == str(
        tmp_path / "external.json"
    )


def test_gate3_uses_canonical_parent_for_expert_evaluation_evidence(
    tmp_path: Path,
) -> None:
    candidate_model = tmp_path / "candidate.zip"
    explicit_parent = tmp_path / "parent.zip"

    assert gate3.r1_parent_model(None, None) == gate3.DEFAULT_R1_PARENT
    assert gate3.r1_parent_model(candidate_model, None) == candidate_model
    assert gate3.r1_parent_model(candidate_model, explicit_parent) == explicit_parent


def test_gate3_json_safe_replaces_non_finite_shard_values() -> None:
    assert gate3._json_safe({"bad": math.inf, "nested": [math.nan]}) == {
        "bad": None,
        "nested": [None],
    }
