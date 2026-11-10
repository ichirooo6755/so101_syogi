from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).parents[1] / "scripts" / "benchmark_professional_parallelism.py"
)
SPEC = importlib.util.spec_from_file_location("benchmark_professional_parallelism", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


def test_parse_fps_and_swap() -> None:
    log = """
    |    fps             | 813      |
    |    fps             | 792.5    |
    """
    assert benchmark.parse_fps(log) == (813.0, 792.5)
    assert benchmark.swap_used_mb(
        "total = 2048.00M used = 1.50G free = 512.00M"
    ) == pytest.approx(1536.0)


def test_make_command_uses_divisible_rollout_batch(tmp_path: Path) -> None:
    command = benchmark.make_command(
        model=tmp_path / "model.zip",
        output=tmp_path / "out",
        n_envs=7,
        device="cpu",
        timesteps=32768,
        seed=31,
    )
    n_envs = int(command[command.index("--n-envs") + 1])
    n_steps = int(command[command.index("--n-steps") + 1])
    batch = int(command[command.index("--batch-size") + 1])
    assert n_envs * n_steps % batch == 0
    assert command[command.index("--device") + 1] == "cpu"
    assert command[command.index("--start-stage") + 1] == "8"
    assert command[command.index("--bc-workers") + 1] == "6"


def test_select_recommendation_prefers_stable_high_fps() -> None:
    rows = [
        {
            "n_envs": 7,
            "device": "mps",
            "seed": 1,
            "returncode": 0,
            "subproc_ready": True,
            "traceback": False,
            "median_fps": 900.0,
            "peak_cpu_percent": 500.0,
            "swap_delta_mb": 400.0,
            "peak_rss_bytes": 4 * 1024**3,
        },
        {
            "n_envs": 6,
            "device": "mps",
            "seed": 1,
            "returncode": 0,
            "subproc_ready": True,
            "traceback": False,
            "median_fps": 820.0,
            "peak_cpu_percent": 420.0,
            "swap_delta_mb": 40.0,
            "peak_rss_bytes": 3 * 1024**3,
        },
        {
            "n_envs": 5,
            "device": "cpu",
            "seed": 1,
            "returncode": 1,
            "subproc_ready": False,
            "traceback": True,
            "median_fps": 0.0,
            "peak_cpu_percent": 0.0,
            "swap_delta_mb": 0.0,
            "peak_rss_bytes": 1 * 1024**3,
        },
    ]
    chosen = benchmark.select_recommendation(rows)
    assert chosen is not None
    assert chosen["n_envs"] == 6
    assert "--n-envs 6" in benchmark.markdown(rows)
