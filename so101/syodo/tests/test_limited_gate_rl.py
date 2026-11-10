from __future__ import annotations

from pathlib import Path

import scripts.run_limited_gate_rl as limited
from scripts.search_gate_recovery import Candidate


def test_limited_rl_starts_only_when_beauty_is_the_only_failed_gate() -> None:
    summary = {
        "gate_level": 2,
        "gates": {
            "complete": True,
            "collision_and_hard_limit_free": True,
            "pressure_tracking": True,
            "width_tracking": True,
            "negative_space": True,
            "tip_opening": True,
            "calibration_clip_rate": True,
            "calibration_fallback_rate": True,
            "beauty": False,
        },
        "passed": False,
    }
    assert limited.beauty_only_failure(summary)
    summary["gates"]["width_tracking"] = False
    assert not limited.beauty_only_failure(summary)


def test_limited_rl_command_resets_policy_optimizer_and_caps_ppo(tmp_path: Path) -> None:
    command = limited.training_command(
        python=Path("python.exe"),
        parent=Path("parent.zip"),
        output=tmp_path / "chunk-1",
        calibration=Path("pressure.json"),
        candidate=Candidate(0.002, 0.45, 0.85),
        first_chunk=True,
    )

    assert "--policy-only-warm-start" in command
    assert command[command.index("--bc-steps") + 1] == "100000"
    assert command[command.index("--timesteps") + 1] == "100000"
    assert command[command.index("--n-envs") + 1] == "8"
    assert command[command.index("--learning-rate") + 1] == "5e-05"
    assert command[command.index("--clip-range") + 1] == "0.1"
    assert command[command.index("--target-kl") + 1] == "0.03"
    assert command[command.index("--device") + 1] == "cuda"


def test_later_limited_rl_chunk_keeps_optimizer_and_skips_bc(tmp_path: Path) -> None:
    command = limited.training_command(
        python=Path("python.exe"),
        parent=Path("chunk-1.zip"),
        output=tmp_path / "chunk-2",
        calibration=Path("pressure.json"),
        candidate=Candidate(0.002, 0.45, 0.85),
        first_chunk=False,
    )

    assert "--policy-only-warm-start" not in command
    assert "--skip-bc" in command
