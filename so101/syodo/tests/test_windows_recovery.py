from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import os

import scripts.spawn_windows_recovery as recovery
from scripts.spawn_windows_recovery import (
    build_eval_command,
    build_train_command,
    candidate_rank,
    parse_deadline,
)


def _write_gate(tmp_path: Path) -> tuple[Path, Path]:
    calibration = tmp_path / "pressure.json"
    calibration.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "cad_fingerprint": "pivot30-offset7.764571-tip38",
                "brush_fingerprint": "tip-only-v1",
                "maximum_offset_m": 0.0045,
                "curves": {},
                "provenance": {},
            }
        ),
        encoding="utf-8",
    )
    fingerprint = hashlib.sha256(calibration.read_bytes()).hexdigest()
    model = tmp_path / "model.zip"
    model.write_bytes(b"model")
    config = {
        "minimum_gap_m": 0.002,
        "clearance_floor": 0.45,
        "exemplar_motion_strength": 0.85,
    }
    gate = tmp_path / "selected.json"
    gate.write_text(
        json.dumps(
            {
                "ready_for_r1": True,
                "gate_schema_version": 2,
                "gate_level": 3,
                "evaluation_count": 768,
                "model": str(model),
                "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
                "config": config,
                "config_sha256": recovery._json_sha256(config),
                "configuration_fingerprint": "full-config-123",
                "calibration": str(calibration),
                "calibration_sha256": fingerprint,
                "calibration_schema_version": 2,
                "cad_fingerprint": "pivot30-offset7.764571-tip38",
                "brush_fingerprint": "tip-only-v1",
                "summary": {
                    "gate_schema_version": 2,
                    "gate_level": 3,
                    "evaluations": 768,
                    "ready_for_r1": True,
                    "configuration_fingerprint": "full-config-123",
                    "passed": True,
                    "gates": {"complete": True, "width": True},
                },
            }
        ),
        encoding="utf-8",
    )
    return gate, calibration


def test_preflight_evidence_requires_gate3_model_config_and_calibration_hashes(
    tmp_path: Path,
) -> None:
    gate, calibration = _write_gate(tmp_path)
    assert recovery._physical_gate_passed(gate)

    value = json.loads(gate.read_text(encoding="utf-8"))
    value["evaluation_count"] = 60
    gate.write_text(json.dumps(value), encoding="utf-8")
    assert not recovery._physical_gate_passed(gate)

    gate, calibration = _write_gate(tmp_path)
    calibration.write_text('{"schema_version": 2}', encoding="utf-8")
    assert not recovery._physical_gate_passed(gate)


def test_relaxed_r1_gate_allows_explicitly_uncalibrated_evidence(tmp_path: Path) -> None:
    gate, _ = _write_gate(tmp_path)
    value = json.loads(gate.read_text(encoding="utf-8"))
    value["threshold_profile"] = "relaxed-r1"
    value["summary"]["threshold_profile"] = "relaxed-r1"
    for name in (
        "calibration",
        "calibration_sha256",
        "calibration_schema_version",
        "cad_fingerprint",
        "brush_fingerprint",
    ):
        value[name] = None
    gate.write_text(json.dumps(value), encoding="utf-8")

    assert recovery._physical_gate_passed(gate)
    assert recovery._physical_gate_calibration(gate) is None

    value["threshold_profile"] = "relaxed-recovery"
    value["summary"]["threshold_profile"] = "relaxed-recovery"
    gate.write_text(json.dumps(value), encoding="utf-8")
    assert not recovery._physical_gate_passed(gate)


def test_cuda_recovery_command_keeps_windows_parallel_policy() -> None:
    command = build_train_command(
        python=Path("python.exe"),
        round_number=2,
        parent=Path("parent.zip"),
        hard_csv=Path("characters.csv"),
        output=Path("r2"),
        learning_rate=1e-4,
        pressure_calibration=Path("pressure.json"),
    )

    assert command[command.index("--device") + 1] == "cuda"
    assert command[command.index("--n-envs") + 1] == "8"
    assert command[command.index("--bc-workers") + 1] == "8"
    assert "--require-subproc" in command
    assert command[command.index("--start-stage") + 1] == "9"
    assert command[command.index("--end-stage") + 1] == "9"
    assert command[command.index("--pressure-calibration") + 1] == "pressure.json"
    assert "--require-pressure-calibration" in command


def test_first_round_broadly_readapts_from_stage_eight() -> None:
    command = build_train_command(
        python=Path("python.exe"),
        round_number=1,
        parent=Path("historical-best.zip"),
        output=Path("r1"),
        learning_rate=1e-4,
        pressure_calibration=Path("pressure.json"),
    )

    assert command[command.index("--start-stage") + 1] == "8"
    assert command[command.index("--end-stage") + 1] == "8"
    assert "--hard-csv" not in command
    assert command[command.index("--timesteps") + 1] == "2500000"
    assert command[command.index("--learning-rate") + 1] == "0.0001"


def test_r1_is_ten_safety_screened_250k_chunks() -> None:
    config = {
        "minimum_gap_m": 0.002,
        "clearance_floor": 0.45,
        "exemplar_motion_strength": 0.85,
    }
    first = recovery.build_r1_chunk_command(
        python=Path("python.exe"),
        parent=Path("parent.zip"),
        output=Path("chunk-1"),
        pressure_calibration=Path("pressure.json"),
        config=config,
        first_chunk=True,
    )
    later = recovery.build_r1_chunk_command(
        python=Path("python.exe"),
        parent=Path("chunk-1.zip"),
        output=Path("chunk-2"),
        pressure_calibration=Path("pressure.json"),
        config=config,
        first_chunk=False,
    )

    assert recovery.R1_CHUNKS == 10
    assert recovery.R1_CHUNK_STEPS * recovery.R1_CHUNKS == 2_500_000
    assert first[first.index("--timesteps") + 1] == "250000"
    assert "--policy-only-warm-start" in first
    assert "--skip-bc" in later
    assert later[later.index("--clip-range") + 1] == "0.1"
    assert later[later.index("--target-kl") + 1] == "0.03"


def test_relaxed_r1_chunk_is_uncalibrated_and_keeps_cuda_parallelism() -> None:
    command = recovery.build_r1_chunk_command(
        python=Path("python.exe"),
        parent=Path("parent.zip"),
        output=Path("relaxed-r1/chunk-1"),
        pressure_calibration=None,
        config={
            "minimum_gap_m": 0.0015,
            "clearance_floor": 0.35,
            "exemplar_motion_strength": 0.72,
        },
        first_chunk=True,
        threshold_profile="relaxed-r1",
    )

    assert "--pressure-calibration" not in command
    assert "--require-pressure-calibration" not in command
    assert command[command.index("--device") + 1] == "cuda"
    assert command[command.index("--n-envs") + 1] == "8"
    assert command[command.index("--bc-workers") + 1] == "4"
    assert command[command.index("--timesteps") + 1] == "250000"


def test_relaxed_r1_uses_an_isolated_default_run_name() -> None:
    assert recovery._default_base_run("strict") == recovery.DEFAULT_BASE_RUN
    assert recovery._default_base_run("relaxed-recovery") == recovery.DEFAULT_BASE_RUN
    assert recovery._default_base_run("relaxed-r1") == (
        recovery.DEFAULT_BASE_RUN + "-relaxed"
    )


def test_worker_environment_can_import_source_and_scripts_packages() -> None:
    python_path = recovery._environment()["PYTHONPATH"].split(os.pathsep)

    assert str(recovery.ROOT / "src") in python_path
    assert str(recovery.ROOT) in python_path


def test_full_eval_stays_cpu_and_uses_eight_shards() -> None:
    command = build_eval_command(
        python=Path("python.exe"),
        model=Path("model.zip"),
        output=Path("eval"),
        seed=92,
        pressure_calibration=Path("pressure.json"),
    )

    assert command[command.index("--device") + 1] == "cpu"
    assert command[command.index("--shards") + 1] == "8"
    assert command[command.index("--eval-limit") + 1] == "0"
    assert command[command.index("--pressure-calibration") + 1] == "pressure.json"


def test_parent_gate_is_a_total_128_glyph_sample() -> None:
    command = build_eval_command(
        python=Path("python.exe"),
        model=Path("model.zip"),
        output=Path("eval"),
        seed=91,
        eval_limit=128,
        pressure_calibration=Path("pressure.json"),
    )

    assert command[command.index("--eval-limit") + 1] == "128"


def test_parent_smoke_requires_128_characters_six_layouts_and_full_completion() -> None:
    summary = {
        "evaluation": {
            "count": 768,
            "unique_character_count": 128,
            "layout_count": 6,
            "success_rate": 1.0,
        }
    }
    assert recovery.parent_smoke_passed(summary)
    summary["evaluation"]["count"] = 767
    assert not recovery.parent_smoke_passed(summary)


def test_past_best_recovery_requires_exact_full_safe_shape(tmp_path: Path) -> None:
    model = tmp_path / "model.zip"
    model.write_bytes(b"model")
    evaluation = tmp_path / "eval"
    evaluation.mkdir()
    summary = {
        "acceptance": {"a": True, "b": True},
        "evaluation": {
            "count": 12_816,
            "unique_character_count": 2_136,
            "layout_count": 6,
            "success_rate": 1.0,
            "mean_beauty_score": recovery.RECOVERY_MEAN + 0.01,
            "p10_beauty_score": recovery.RECOVERY_P10,
            "total_drips": 0,
            "collision_count": 0,
            "component_means": {"line_width": 70.0, "brushwork": 70.0},
            "endpoint_triangle": {"mean": 80.0},
            "technique_means": {"harai": {"finish": 75.0}},
        },
    }
    (evaluation / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (evaluation / "characters.csv").write_text(
        "character,line_width,brushwork\n一,70,70\n", encoding="utf-8"
    )
    candidate = recovery._read_candidate(1, model, evaluation)
    assert not candidate["past_best_recovered"]

    rows = "character,line_width,brushwork\n" + "".join(
        f"{chr(0x4E00 + index % 2136)},70,70\n" for index in range(12_816)
    )
    (evaluation / "characters.csv").write_text(rows, encoding="utf-8")
    candidate = recovery._read_candidate(1, model, evaluation)
    assert candidate["past_best_recovered"]


def test_candidate_rank_uses_declared_priority_order() -> None:
    summary = {
        "acceptance": {"a": True, "b": False},
        "evaluation": {
            "success_rate": 0.9,
            "mean_beauty_score": 80.0,
            "p10_beauty_score": 77.0,
            "component_means": {"line_width": 66.0, "brushwork": 63.0},
            "endpoint_triangle": {"mean": 72.0},
            "technique_means": {"harai": {"finish": 70.0}},
        },
    }
    rows = [{"line_width": "70", "brushwork": "65"}]

    assert candidate_rank(summary, rows) == (
        1.0,
        0.9,
        80.0,
        77.0,
        130.0,
        72.0,
        70.0,
    )


def test_deadline_parser_accepts_shell_safe_iso_form() -> None:
    assert parse_deadline("2026-08-26 12:00:00").isoformat() == "2026-08-26T12:00:00"
    assert parse_deadline("2026-08-26T12:00:00").isoformat() == "2026-08-26T12:00:00"
    assert parse_deadline("none") is None
    assert parse_deadline("off") is None
    assert parse_deadline("  ") is None


def test_round_phase_skips_train_when_model_exists(tmp_path: Path) -> None:
    output = tmp_path / "r1"
    evaluation = tmp_path / "r1-eval"
    assert recovery.round_phase(output, evaluation) == "train"

    output.mkdir()
    (output / "final_model.zip").write_bytes(b"zip")
    assert recovery.round_phase(output, evaluation) == "eval"

    evaluation.mkdir()
    (evaluation / "summary.json").write_text("{}", encoding="utf-8")
    assert recovery.round_phase(output, evaluation) == "done"


def test_parent_is_the_brushmark_joyo_model() -> None:
    assert recovery.PARENT.name == "model.zip"
    assert recovery.PARENT.parent.name == "08-joyo"
    assert recovery.PARENT.parent.parent.name == "kaisho-yohitsu-brushmark-joyo"


def test_cuda_preflight_requires_a_passed_physical_gate(tmp_path: Path) -> None:
    gate = tmp_path / "selected.json"
    assert not recovery._physical_gate_passed(gate)
    gate.write_text(
        '{"ready_for_cuda": false, "summary": {'
        '"ready_for_cuda": false, "gates": {"complete": true}}}',
        encoding="utf-8",
    )
    assert not recovery._physical_gate_passed(gate)


def test_deadline_reached_compares_against_now() -> None:
    assert recovery._deadline_reached(parse_deadline("2020-01-01 00:00:00"))
    assert not recovery._deadline_reached(parse_deadline("2099-01-01 00:00:00"))
    assert not recovery._deadline_reached(None)


def test_stale_pid_tolerates_tasklist_no_match(monkeypatch) -> None:
    monkeypatch.setattr(
        recovery.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="INFO: No tasks\n"),
    )

    assert not recovery._alive(12345)
