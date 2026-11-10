from __future__ import annotations

from pathlib import Path
import math

import scripts.search_gate_recovery as search


def _row(**changes: object) -> dict[str, object]:
    row: dict[str, object] = {
        "is_success": True,
        "collision_types": [],
        "hard_limit": False,
        "pressure_error_median_abs": 0.05,
        "pressure_error_p90_abs": 0.15,
        "width_ratio_median": 1.0,
        "lost_holes": 0,
        "beauty_score": 75.0,
    }
    row.update(changes)
    return row


def test_candidate_grid_is_exactly_the_approved_eighteen() -> None:
    candidates = search.candidates()

    assert len(candidates) == 18
    assert {candidate.minimum_gap_m for candidate in candidates} == {
        0.0015,
        0.0020,
        0.0025,
    }
    assert {candidate.clearance_floor for candidate in candidates} == {0.35, 0.45}
    assert {candidate.exemplar_motion_strength for candidate in candidates} == {
        0.72,
        0.85,
        1.0,
    }


def test_screen_rejects_incomplete_collision_and_width_below_ninety_percent() -> None:
    assert search.screen_rows([_row()])["eligible"]
    assert not search.screen_rows([_row(is_success=False)])["eligible"]
    assert not search.screen_rows([_row(collision_types=["arm-floor"])])["eligible"]
    assert not search.screen_rows([_row(width_ratio_median=0.899)])["eligible"]


def test_relaxed_screen_uses_named_profile_without_changing_strict_default() -> None:
    rows = [_row() for _ in range(18)]
    rows[0]["is_success"] = False
    rows[0]["width_ratio_median"] = 0.71

    assert not search.screen_rows(rows)["eligible"]
    assert search.screen_rows(rows, threshold_profile="relaxed-recovery")["eligible"]


def test_rank_orders_tracking_then_holes_then_beauty_after_safety() -> None:
    good = search.candidate_rank([_row(beauty_score=72.0)])
    tracking_fail = search.candidate_rank([_row(pressure_error_p90_abs=0.19, beauty_score=90.0)])
    holes = search.candidate_rank([_row(lost_holes=1, beauty_score=90.0)])

    assert good > tracking_fail
    assert good > holes


def test_diagnostic_command_pins_calibration_limits_and_candidate(tmp_path: Path) -> None:
    candidate = search.candidates()[0]
    command = search.diagnostic_command(
        tmp_path / "result.json",
        calibration=tmp_path / "pressure.json",
        candidate=candidate,
        characters="一三十",
        layouts="0,1,2,3,4,5",
        gate_level=1,
    )

    assert command[command.index("--minimum-gap") + 1] == "0.0015"
    assert command[command.index("--clearance-floor") + 1] == "0.35"
    assert command[command.index("--exemplar-motion-strength") + 1] == "0.72"
    assert command[command.index("--pressure-calibration-clip-rate-limit") + 1] == "0.05"
    assert command[command.index("--pressure-calibration-fallback-rate-limit") + 1] == "0.05"
    assert "--base-x" not in command


def test_diagnostic_command_records_relaxed_profile(tmp_path: Path) -> None:
    command = search.diagnostic_command(
        tmp_path / "result.json",
        calibration=tmp_path / "pressure.json",
        candidate=search.candidates()[0],
        characters="一三十",
        layouts="0,1,2,3,4,5",
        gate_level=1,
        threshold_profile="relaxed-recovery",
    )

    assert command[command.index("--threshold-profile") + 1] == "relaxed-recovery"


def test_diagnostic_command_can_match_an_uncalibrated_relaxed_run(tmp_path: Path) -> None:
    command = search.diagnostic_command(
        tmp_path / "result.json",
        calibration=None,
        candidate=search.candidates()[0],
        characters="一三十",
        layouts="0,1,2,3,4,5",
        gate_level=1,
        threshold_profile="relaxed-r1",
    )

    assert "--pressure-calibration" not in command
    assert "--require-pressure-calibration" not in command
    assert command[command.index("--threshold-profile") + 1] == "relaxed-r1"


def test_worker_count_is_bounded_by_requested_candidates() -> None:
    assert search.worker_count(6, 18) == 6
    assert search.worker_count(64, 18) == 18
    assert search.worker_count(0, 18) == 1


def test_json_safe_replaces_non_finite_diagnostic_values() -> None:
    assert search._json_safe({"bad": math.inf, "nested": [math.nan]}) == {
        "bad": None,
        "nested": [None],
    }
