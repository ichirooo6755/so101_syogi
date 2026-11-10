from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.calibrate_a4_tip as calibration_gate
import scripts.diagnose_stroke_merge as diagnostics
import scripts.fit_pressure_calibration as fitter
from so101_calligraphy.pressure_calibration import PressureCalibration


def test_fit_calibration_from_diagnostics_creates_valid_calibration(tmp_path: Path) -> None:
    diag_data = {
        "results": [
            {
                "character": "一",
                "layout_index": 0,
                "is_success": True,
                "collision_types": [],
                "hard_limit": False,
                "commanded_angle_deg": 30,
                "final_actual_angle_deg": 30.0,
                "longest_contact_targets": [
                    {
                        "phase": "entry",
                        "target_pressure": 0.20,
                        "actual_pressure_median": 0.18,
                        "pressure_offset_median_m": -0.0010,
                        "xy_error_last_m": 0.002,
                    },
                    {
                        "phase": "entry",
                        "target_pressure": 0.35,
                        "actual_pressure_median": 0.30,
                        "pressure_offset_median_m": 0.0015,
                        "xy_error_last_m": 0.003,
                    },
                ],
            }
        ]
    }

    diag_path = tmp_path / "diag.json"
    out_path = tmp_path / "fitted_calib.json"
    diag_path.write_text(json.dumps(diag_data), encoding="utf-8")

    ret = fitter.main(["--diagnostic", str(diag_path), "--output", str(out_path)])
    assert ret == 0
    assert out_path.is_file()

    calib = PressureCalibration.load(out_path)
    assert "85mm/30/entry" in calib.curves
    curve = calib.curves["85mm/30/entry"]
    assert curve.offset_m[1] <= curve.offset_m[0]


def test_fit_excludes_collided_and_failed_runs(tmp_path: Path) -> None:
    diag_data = {
        "results": [
            {
                "character": "一",
                "layout_index": 0,
                "is_success": False,
                "collision_types": ["floor"],
                "hard_limit": False,
                "final_actual_angle_deg": 30.0,
                "longest_contact_targets": [
                    {
                        "phase": "entry",
                        "target_pressure": 0.20,
                        "actual_pressure_median": 0.18,
                        "pressure_offset_median_m": -0.0010,
                        "xy_error_last_m": 0.002,
                    }
                ],
            }
        ]
    }
    calib = fitter.fit_calibration_from_diagnostics(diag_data)
    assert len(calib.curves) == 0


def _sample(**changes: object) -> dict[str, object]:
    sample: dict[str, object] = {
        "layout_class": "85mm",
        "commanded_angle_deg": 30,
        "actual_angle_deg": 30.0,
        "phase": "entry",
        "target_pressure": 0.20,
        "actual_pressure": 0.18,
        "z_offset_m": -0.001,
        "contact_force": 0.5,
        "actual_width_m": 0.004,
        "target_width_m": 0.0042,
        "opening": 0.8,
        "xy_error_m": 0.002,
        "z_error_m": 0.0002,
        "dwell": 40,
        "contact": True,
    }
    sample.update(changes)
    return sample


def test_fit_filters_transient_contact_and_invalid_samples() -> None:
    diagnostic = {
        "summary": {"configuration_fingerprint": "config-123"},
        "results": [
            {
                "character": "一",
                "layout_index": 0,
                "is_success": True,
                "collision_types": [],
                "hard_limit": False,
                "pressure_calibration_samples": [
                    _sample(),
                    _sample(target_pressure=0.35, actual_pressure=0.30, z_offset_m=0.001),
                    _sample(dwell=10),
                    _sample(contact=False),
                    _sample(xy_error_m=0.02),
                    _sample(actual_pressure=float("nan")),
                    _sample(commanded_angle_deg=25),
                ],
            }
        ],
    }

    calibration = fitter.fit_calibration_from_diagnostics(diagnostic)

    assert tuple(calibration.curves) == ("85mm/30/entry",)
    assert calibration.provenance["accepted_samples"] == 2
    assert calibration.provenance["excluded_samples"] == 5
    assert calibration.provenance["configuration_fingerprint"] == "config-123"
    assert set(calibration.provenance["validation"]) == {
        "leave_one_character_median_abs_error_m",
            "leave_one_layout_median_abs_error_m",
            "clip_rate",
            "fallback_rate",
            "held_out_median_abs_error_m",
        }


def test_compressed_knots_keep_observed_pressure_endpoints_unclipped() -> None:
    samples = [
        _sample(
            target_pressure=0.10 + index * 0.05,
            actual_pressure=0.09 + index * 0.04,
            z_offset_m=-0.002 + index * 0.0004,
        )
        for index in range(8)
    ]
    diagnostic = {
        "results": [
            {
                "character": "一",
                "layout_index": 0,
                "is_success": True,
                "collision_types": [],
                "hard_limit": False,
                "pressure_calibration_samples": samples,
            }
        ]
    }

    calibration = fitter.fit_calibration_from_diagnostics(diagnostic)
    curve = calibration.curves["85mm/30/entry"]

    assert curve.pressure[0] == pytest.approx(0.10)
    assert curve.pressure[-1] == pytest.approx(0.45)
    assert calibration.provenance["validation"]["clip_rate"] == 0.0


def test_underpressure_fit_moves_z_downward() -> None:
    diagnostic = {
        "results": [
            {
                "character": "一",
                "layout_index": 0,
                "is_success": True,
                "collision_types": [],
                "hard_limit": False,
                "pressure_calibration_samples": [
                    _sample(target_pressure=0.2, actual_pressure=0.1, z_offset_m=0.0),
                    _sample(target_pressure=0.3, actual_pressure=0.2, z_offset_m=0.0),
                ],
            }
        ]
    }

    curve = fitter.fit_calibration_from_diagnostics(diagnostic).curves[
        "85mm/30/entry"
    ]

    assert all(offset < 0.0 for offset in curve.offset_m)


def test_fitter_uses_exact_command_category_and_never_rounds_actual_angle() -> None:
    diagnostic = {
        "results": [
            {
                "character": "一",
                "layout_index": 0,
                "is_success": True,
                "collision_types": [],
                "hard_limit": False,
                "pressure_calibration_samples": [
                    _sample(
                        commanded_angle_deg=8,
                        actual_angle_deg=10.7,
                        target_pressure=0.20,
                    ),
                    _sample(
                        commanded_angle_deg=8,
                        actual_angle_deg=11.2,
                        target_pressure=0.35,
                    ),
                ],
            }
        ]
    }

    calibration = fitter.fit_calibration_from_diagnostics(diagnostic)

    assert tuple(calibration.curves) == ("85mm/8/entry",)
    assert calibration.lookup("85mm", 11, "entry", 0.20).fallback


def test_fitter_applies_weighted_pava_with_physical_offset_sign() -> None:
    samples = [
        {
            "key": "85mm/8/send",
            "character": "一",
            "layout_index": 0,
            "target_pressure": pressure,
            "required_offset_m": offset,
        }
        for pressure, offset in ((0.10, 0.001), (0.20, -0.003), (0.30, -0.001))
    ]

    curve = fitter._fit_curves(samples, maximum_offset_m=0.0045)["85mm/8/send"]

    assert curve.offset_m == pytest.approx((0.001, -0.002, -0.002))


def _probe_sample(actual_pressure: float, offset_m: float, **changes: object) -> dict[str, object]:
    return _sample(
        probe=True,
        probe_offset_m=offset_m,
        z_offset_m=offset_m,
        actual_pressure=actual_pressure,
        **changes,
    )


def test_probe_fit_uses_fixed_pressure_knots_without_extrapolation() -> None:
    diagnostic = {
        "results": [
            {
                "character": "一",
                "layout_index": 0,
                "probe_split": "fit",
                "is_success": True,
                "collision_types": [],
                "hard_limit": False,
                "pressure_calibration_samples": [
                    _probe_sample(0.00, 0.0045),
                    _probe_sample(0.10, 0.0030),
                    _probe_sample(0.24, 0.0000),
                    _probe_sample(0.46, -0.0045),
                ],
            }
        ]
    }

    calibration = fitter.fit_calibration_from_diagnostics(diagnostic)
    curve = calibration.curves["85mm/30/entry"]

    assert curve.pressure == fitter.PRESSURE_KNOTS
    assert all(
        right <= left + 1e-12
        for left, right in zip(curve.offset_m, curve.offset_m[1:])
    )


def test_probe_category_without_two_covered_knots_is_explicit_fallback() -> None:
    diagnostic = {
        "results": [
            {
                "character": "一",
                "layout_index": 0,
                "probe_split": "fit",
                "is_success": True,
                "collision_types": [],
                "hard_limit": False,
                "pressure_calibration_samples": [
                    _probe_sample(0.20, 0.001),
                    _probe_sample(0.21, -0.001),
                ],
            }
        ]
    }

    calibration = fitter.fit_calibration_from_diagnostics(diagnostic)

    assert calibration.lookup("85mm", 30, "entry", 0.20).fallback


def test_probe_held_out_characters_validate_but_do_not_fit() -> None:
    fit_result = {
        "character": "一",
        "layout_index": 0,
        "probe_split": "fit",
        "is_success": True,
        "collision_types": [],
        "hard_limit": False,
        "pressure_calibration_samples": [
            _probe_sample(0.01, 0.0045),
            _probe_sample(0.45, -0.0045),
        ],
    }
    held_out_result = {
        **fit_result,
        "character": "鬱",
        "probe_split": "held-out",
        "pressure_calibration_samples": [
            _probe_sample(0.01, 0.0040),
            _probe_sample(0.45, -0.0040),
        ],
    }

    calibration = fitter.fit_calibration_from_diagnostics(
        {"results": [fit_result, held_out_result]}
    )

    assert calibration.provenance["fit_samples"] == 2
    assert calibration.provenance["held_out_samples"] == 2
    assert calibration.provenance["validation"][
        "held_out_median_abs_error_m"
    ] == pytest.approx(0.0005)
    assert calibration.provenance["actual_width_p90_m"]["85mm/30/entry"] == pytest.approx(
        0.004
    )


def test_fitting_cli_records_source_hash_and_command(tmp_path: Path) -> None:
    diagnostic = {
        "summary": {"configuration_fingerprint": "config-xyz"},
        "results": [
            {
                "character": "一",
                "layout_index": 0,
                "is_success": True,
                "collision_types": [],
                "hard_limit": False,
                "pressure_calibration_samples": [
                    _sample(),
                    _sample(target_pressure=0.35, actual_pressure=0.30, z_offset_m=0.001),
                ],
            }
        ],
    }
    source = tmp_path / "diagnostic.json"
    output = tmp_path / "candidate.json"
    source.write_text(json.dumps(diagnostic), encoding="utf-8")

    assert fitter.main(["--diagnostic", str(source), "--output", str(output)]) == 0

    provenance = PressureCalibration.load(output).provenance
    assert provenance["source_diagnostic_sha256"] == fitter.sha256_file(source)
    assert provenance["configuration_fingerprint"] == "config-xyz"
    assert str(source) in provenance["command"]
    assert provenance["run"]["status"] == "completed"
    assert provenance["run"]["extra"]["device"] == "cpu"
    assert provenance["run"]["extra"]["source_diagnostic_sha256"] == fitter.sha256_file(
        source
    )


def _gate_rows(count: int, *, beauty: float = 86.0) -> list[dict[str, object]]:
    return [
        {
            "is_success": True,
            "collision_types": [],
            "hard_limit": False,
            "lost_holes": 0,
            "pressure_error_median_abs": 0.05,
            "pressure_error_p90_abs": 0.15,
            "width_ratio_median": 1.0,
            "opening_p90": 1.0,
            "beauty_score": beauty,
        }
        for _ in range(count)
    ]


def test_gate_levels_are_strict_and_only_gate_two_enables_cuda() -> None:
    gate1 = diagnostics.summarize_physical_gate(
        _gate_rows(18), gate_level=1, endpoint_improvement=10.5
    )
    assert gate1["passed"]
    assert not gate1["ready_for_cuda"]
    assert gate1["gate_level"] == 1

    gate2 = diagnostics.summarize_physical_gate(
        _gate_rows(60), gate_level=2, endpoint_improvement=None
    )
    assert gate2["passed"]
    assert gate2["ready_for_cuda"]
    assert gate2["evaluations"] == 60

    too_small = diagnostics.summarize_physical_gate(
        _gate_rows(18), gate_level=2, endpoint_improvement=None
    )
    assert not too_small["passed"]
    assert not too_small["ready_for_cuda"]

    low_beauty = diagnostics.summarize_physical_gate(
        _gate_rows(60, beauty=84.9), gate_level=2, endpoint_improvement=None
    )
    assert not low_beauty["gates"]["beauty"]

    high_fallback = diagnostics.summarize_physical_gate(
        _gate_rows(60),
        gate_level=2,
        endpoint_improvement=None,
        calibration_fallback_rate=0.051,
        fallback_rate_limit=0.05,
    )
    assert not high_fallback["gates"]["calibration_fallback_rate"]


def test_gate_three_accepts_only_the_768_case_shape_without_cuda_authority() -> None:
    gate3 = diagnostics.summarize_physical_gate(
        _gate_rows(768), gate_level=3, endpoint_improvement=None
    )
    assert gate3["evaluations"] == 768
    assert gate3["expected_evaluations"] == 768
    assert gate3["gates"]["evaluation_count"]
    assert gate3["passed"]
    assert not gate3["ready_for_cuda"]
    assert gate3["ready_for_r1"]

    too_small = diagnostics.summarize_physical_gate(
        _gate_rows(60), gate_level=3, endpoint_improvement=None
    )
    assert not too_small["passed"]


def test_relaxed_recovery_profile_is_explicit_and_never_grants_cuda_authority() -> None:
    rows = _gate_rows(18, beauty=70.0)
    rows[0].update(
        is_success=False,
        pressure_error_median_abs=0.50,
        pressure_error_p90_abs=0.50,
        width_ratio_median=0.72,
    )
    gate1 = diagnostics.summarize_physical_gate(
        rows,
        gate_level=1,
        endpoint_improvement=6.1,
        threshold_profile="relaxed-recovery",
    )

    assert gate1["passed"]
    assert gate1["threshold_profile"] == "relaxed-recovery"
    assert not gate1["ready_for_cuda"]
    assert not gate1["ready_for_r1"]
    assert gate1["thresholds"]["min_successes"] == 17


def test_relaxed_recovery_gate_three_records_explicit_safety_debt() -> None:
    rows = _gate_rows(768)
    for index in range(14):
        rows[index]["is_success"] = False
        rows[index]["collision_types"] = ["arm-floor"]
        rows[index]["lost_holes"] = 1
        rows[index]["pressure_error_p90_abs"] = 0.60
        rows[index]["width_ratio_median"] = 0.71
    gate3 = diagnostics.summarize_physical_gate(
        rows,
        gate_level=3,
        endpoint_improvement=None,
        threshold_profile="relaxed-recovery",
    )

    assert gate3["passed"]
    assert not gate3["ready_for_r1"]
    assert gate3["thresholds"]["max_collision_cases"] == 14


def test_relaxed_r1_profile_grants_training_authority_without_changing_diagnostic_relaxed() -> None:
    gate2 = diagnostics.summarize_physical_gate(
        _gate_rows(60, beauty=73.0),
        gate_level=2,
        endpoint_improvement=None,
        threshold_profile="relaxed-r1",
    )
    gate3 = diagnostics.summarize_physical_gate(
        _gate_rows(768),
        gate_level=3,
        endpoint_improvement=None,
        threshold_profile="relaxed-r1",
    )

    assert gate2["passed"]
    assert gate2["ready_for_cuda"]
    assert gate3["passed"]
    assert gate3["ready_for_r1"]
    assert gate3["thresholds"] == diagnostics.GATE_THRESHOLD_PROFILES[
        "relaxed-recovery"
    ][3]


def test_unknown_threshold_profile_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown threshold profile"):
        diagnostics.summarize_physical_gate(
            _gate_rows(18),
            gate_level=1,
            endpoint_improvement=10.0,
            threshold_profile="not-a-profile",
        )


def test_gate_selection_records_schema_calibration_and_rates(tmp_path: Path) -> None:
    calibration = tmp_path / "candidate.json"
    calibration.write_text("{}", encoding="utf-8")
    summary = diagnostics.summarize_physical_gate(
        _gate_rows(60),
        gate_level=2,
        endpoint_improvement=None,
        calibration_clip_rate=0.02,
        calibration_fallback_rate=0.01,
    )

    selected = calibration_gate.build_selection(
        summary=summary,
        calibration=calibration,
        diagnostic=tmp_path / "gate2.json",
    )

    assert selected["ready_for_cuda"]
    assert selected["gate_schema_version"] == diagnostics.PHYSICAL_GATE_SCHEMA_VERSION
    assert selected["gate_level"] == 2
    assert selected["evaluation_count"] == 60
    assert selected["calibration_sha256"] == calibration_gate.sha256_file(calibration)
    assert selected["calibration_clip_rate"] == pytest.approx(0.02)
    assert selected["calibration_fallback_rate"] == pytest.approx(0.01)


def test_gate_diagnostic_command_is_explicit_about_level_and_calibration(
    tmp_path: Path,
) -> None:
    command = calibration_gate._command(
        tmp_path / "gate2.json",
        gate_level=2,
        pressure_calibration=tmp_path / "candidate.json",
    )

    assert command[command.index("--gate-level") + 1] == "2"
    assert command[command.index("--pressure-calibration") + 1].endswith(
        "candidate.json"
    )
    assert "--require-pressure-calibration" in command
    assert command[command.index("--pressure-calibration-clip-rate-limit") + 1] == "0.05"
    assert command[
        command.index("--pressure-calibration-fallback-rate-limit") + 1
    ] == "0.05"
