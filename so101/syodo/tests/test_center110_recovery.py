from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "run_center110_recovery.py"
SPEC = importlib.util.spec_from_file_location("run_center110_recovery", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
recovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recovery)


def _value(command: list[str], option: str) -> str:
    return command[command.index(option) + 1]


def test_first_center_chunk_is_exact_cuda_subproc_bc_command() -> None:
    command = recovery.build_train_command(
        python=Path("C:/syodo/.venv/Scripts/python.exe"),
        parent=Path("C:/syodo/runs/brushmark/model.zip"),
        hard_csv=Path("C:/syodo/runs/baseline/characters.csv"),
        output=Path("C:/syodo/runs/center/chunk-01"),
        font=Path("C:/syodo/fonts/teacher.otf"),
        first_chunk=True,
        learning_rate=5e-5,
    )

    assert _value(command, "--device") == "cuda"
    assert _value(command, "--n-envs") == "4"
    assert "--require-subproc" in command
    assert _value(command, "--n-steps") == "2048"
    assert _value(command, "--batch-size") == "1024"
    assert _value(command, "--learning-rate") == "5e-05"
    assert _value(command, "--clip-range") == "0.1"
    assert _value(command, "--target-kl") == "0.03"
    assert _value(command, "--timesteps") == "250000"
    assert _value(command, "--bc-steps") == "100000"
    assert _value(command, "--bc-epochs") == "3"
    assert _value(command, "--hard-beauty-threshold") == "80"
    assert _value(command, "--training-layouts") == "0"
    assert _value(command, "--center110-profile") == "p10-80-v1"
    assert "--brushmark-layout" in command
    assert "--policy-only-warm-start" in command
    assert "--skip-bc" not in command
    assert "--train-only" in command


def test_later_center_chunk_resumes_best_checkpoint_without_bc() -> None:
    command = recovery.build_train_command(
        python=Path("python.exe"),
        parent=Path("best.zip"),
        hard_csv=Path("latest.csv"),
        output=Path("chunk-02"),
        font=Path("teacher.otf"),
        first_chunk=False,
        learning_rate=2.5e-5,
        n_envs=2,
    )

    assert "--skip-bc" in command
    assert "--policy-only-warm-start" not in command
    assert _value(command, "--learning-rate") == "2.5e-05"
    assert _value(command, "--n-envs") == "2"
    assert "--require-subproc" in command


def test_center_eval_command_can_run_analytical_control() -> None:
    command = recovery.build_eval_command(
        python=Path("python.exe"),
        model=None,
        output=Path("baseline"),
        font=Path("teacher.otf"),
        limit=0,
    )

    assert "--model" not in command
    assert "--brushmark-layout" in command
    assert _value(command, "--center110-profile") == "p10-80-v1"
    assert _value(command, "--eval-layouts") == "0"
    assert _value(command, "--shards") == "4"
    assert _value(command, "--eval-limit") == "0"


def test_rank_and_full_acceptance_use_strict_contract() -> None:
    evaluation = {
        "count": 2_136,
        "unique_character_count": 2_136,
        "layout_count": 1,
        "success_rate": 1.0,
        "mean_beauty_score": 82.0,
        "p10_beauty_score": 80.5,
        "minimum_beauty_score": 61.0,
        "total_drips": 0,
        "collision_count": 0,
    }
    summary = {
        "all_joyo_evaluated": True,
        "eval_layouts": [0],
        "brushmark_layout": True,
        "center110_profile": "p10-80-v1",
        "evaluation": evaluation,
        "acceptance": {
            "mean_at_least_80": True,
            "p10_at_least_80": True,
            "minimum_at_least_60": True,
            "all_complete": True,
            "zero_drips": True,
            "zero_collisions": True,
            "c_gate": True,
        },
    }

    assert recovery.candidate_rank(evaluation) == (1.0, 1.0, 80.5, 82.0, 61.0)
    assert recovery.accepted_full(summary)
    summary["acceptance"]["c_gate"] = False
    assert not recovery.accepted_full(summary)
