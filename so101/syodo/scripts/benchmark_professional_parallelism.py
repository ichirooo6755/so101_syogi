"""Benchmark safe professional PPO parallelism on Apple Silicon.

This intentionally runs complete short curricula so startup, BC, rollout and
evaluation costs are represented. Do not run it beside a production training
run: the result would measure contention rather than the selected config.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shlex
import statistics
import subprocess
import sys
import time
from typing import Iterable


FPS_RE = re.compile(r"\|\s+fps\s+\|\s+([0-9.]+)")
SWAP_RE = re.compile(r"used\s*=\s*([0-9.]+)([MGT])")


def parse_int_list(value: str) -> tuple[int, ...]:
    result = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not result or any(item <= 0 for item in result):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return result


def parse_str_list(value: str) -> tuple[str, ...]:
    result = tuple(item.strip() for item in value.split(",") if item.strip())
    if not result:
        raise argparse.ArgumentTypeError("expected a comma-separated list")
    return result


def parse_fps(text: str) -> tuple[float, ...]:
    return tuple(float(match.group(1)) for match in FPS_RE.finditer(text))


def swap_used_mb(text: str) -> float:
    match = SWAP_RE.search(text)
    if not match:
        return 0.0
    value = float(match.group(1))
    return value * {"M": 1.0, "G": 1024.0, "T": 1024.0 * 1024.0}[match.group(2)]


def current_swap_mb() -> float:
    try:
        output = subprocess.run(
            ["sysctl", "-n", "vm.swapusage"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return 0.0
    return swap_used_mb(output)


def process_group_usage(pgid: int) -> tuple[float, int]:
    """Return aggregate CPU percent and RSS bytes for one process group."""

    try:
        output = subprocess.run(
            ["ps", "-axo", "pgid=,%cpu=,rss="],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return 0.0, 0
    cpu = 0.0
    rss_kib = 0
    for line in output.splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue
        try:
            row_pgid, row_cpu, row_rss = int(fields[0]), float(fields[1]), int(fields[2])
        except ValueError:
            continue
        if row_pgid == pgid:
            cpu += row_cpu
            rss_kib += row_rss
    return cpu, rss_kib * 1024


def make_command(
    *,
    model: Path,
    output: Path,
    n_envs: int,
    device: str,
    timesteps: int,
    seed: int,
    start_stage: int = 8,
) -> list[str]:
    """Build one short professional cell.

    Default ``start_stage=8`` (joyo only) so each matrix cell measures one
    Subproc/BC/PPO cycle instead of replaying radicals→kana→elementary→joyo.
    """

    bc_workers = min(n_envs, 6)
    return [
        sys.executable,
        "-m",
        "so101_calligraphy.training.professional",
        "--ablation",
        "all",
        "--run-purpose",
        "parallelism benchmark cell",
        "--initial-model",
        str(model),
        "--start-stage",
        str(start_stage),
        "--timesteps",
        str(timesteps),
        "--kana-timesteps",
        str(timesteps),
        "--bc-steps",
        "256",
        "--kana-bc-steps",
        "256",
        "--bc-epochs",
        "1",
        "--n-envs",
        str(n_envs),
        "--bc-workers",
        str(bc_workers),
        "--n-steps",
        "1024",
        "--batch-size",
        "512",
        "--device",
        device,
        "--allow-gate-failure",
        "--stage-eval-size",
        "2",
        "--eval-limit",
        "2",
        "--output",
        str(output),
        "--seed",
        str(seed),
    ]


def run_one(command: list[str], log_path: Path) -> dict[str, object]:
    started = time.monotonic()
    swap_before = current_swap_mb()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    peak_rss = 0
    peak_cpu = 0.0
    with log_path.open("w", encoding="utf-8") as log:
        env = dict(os.environ)
        env["PYTHONUNBUFFERED"] = "1"
        env.setdefault("MPLBACKEND", "Agg")
        env.setdefault("MPLCONFIGDIR", "/tmp/mplconfig-syodo")
        env.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[1] / "src"))
        process = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
            env=env,
        )
        pgid = os.getpgid(process.pid)
        while process.poll() is None:
            cpu, rss = process_group_usage(pgid)
            peak_cpu = max(peak_cpu, cpu)
            peak_rss = max(peak_rss, rss)
            time.sleep(1.0)
    text = log_path.read_text(encoding="utf-8")
    fps = parse_fps(text)
    return {
        "command": shlex.join(command),
        "returncode": process.returncode,
        "elapsed_sec": time.monotonic() - started,
        "median_fps": statistics.median(fps) if fps else 0.0,
        "last_fps": fps[-1] if fps else 0.0,
        "peak_cpu_percent": peak_cpu,
        "peak_rss_bytes": peak_rss,
        "swap_delta_mb": current_swap_mb() - swap_before,
        "subproc_ready": "vec env ready: SubprocVecEnv" in text,
        "traceback": "Traceback (most recent call last)" in text,
    }


def is_ok(row: dict[str, object]) -> bool:
    return (
        int(row["returncode"]) == 0
        and bool(row["subproc_ready"])
        and not bool(row.get("traceback"))
    )


def select_recommendation(
    results: Iterable[dict[str, object]],
    *,
    max_swap_delta_mb: float = 256.0,
    max_peak_rss_gib: float = 10.0,
) -> dict[str, object] | None:
    """Pick the highest-fps stable config under memory-pressure limits."""

    eligible: list[dict[str, object]] = []
    for row in results:
        if not is_ok(row):
            continue
        if float(row["swap_delta_mb"]) > max_swap_delta_mb:
            continue
        if float(row["peak_rss_bytes"]) / (1024**3) > max_peak_rss_gib:
            continue
        eligible.append(row)
    if not eligible:
        return None
    return max(
        eligible,
        key=lambda row: (
            float(row["median_fps"]),
            -float(row["swap_delta_mb"]),
            -float(row["peak_rss_bytes"]),
            -int(row["n_envs"]),
        ),
    )


def markdown(results: Iterable[dict[str, object]]) -> str:
    lines = [
        "# Professional parallelism benchmark",
        "",
        "| envs | device | seed | median fps | peak CPU | peak RSS GiB | swap Δ MiB | ok |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for row in results:
        ok = is_ok(row)
        lines.append(
            "| {n_envs} | {device} | {seed} | {median_fps:.1f} | {peak_cpu_percent:.0f}% | "
            "{rss:.2f} | {swap_delta_mb:.1f} | {ok} |".format(
                **row,
                rss=float(row["peak_rss_bytes"]) / (1024**3),
                ok="yes" if ok else "no",
            )
        )
    recommendation = select_recommendation(results)
    lines.extend(["", "## Recommendation", ""])
    if recommendation is None:
        lines.append("No stable configuration stayed within swap/RSS limits.")
    else:
        lines.append(
            "Use `--n-envs {n_envs} --bc-workers {n_envs} --device {device}` "
            "(median fps {median_fps:.1f}, swap Δ {swap_delta_mb:.1f} MiB).".format(
                **recommendation
            )
        )
        lines.append("")
        lines.append(
            "Keep `n_envs>=8` for evaluation shards only; training workers still "
            "duplicate trajectories into each process."
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("runs/parallel-benchmark"))
    parser.add_argument("--envs", type=parse_int_list, default=(5, 6, 7))
    parser.add_argument("--devices", type=parse_str_list, default=("cpu", "mps"))
    parser.add_argument("--timesteps", type=int, default=8_192)
    parser.add_argument("--seeds", type=parse_int_list, default=(31,))
    parser.add_argument(
        "--start-stage",
        type=int,
        default=8,
        help="Curriculum stage for each cell (8=joyo only; avoid 5 which runs 4 stages).",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.model.is_file():
        raise SystemExit(f"Model does not exist: {args.model}")
    if not 1 <= args.start_stage <= 8:
        raise SystemExit("--start-stage for benchmark must be in 1..8")
    args.output.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, object]] = []
    for seed in args.seeds:
        for device in args.devices:
            for n_envs in args.envs:
                name = f"env{n_envs}-{device}-seed{seed}"
                run_dir = args.output / name
                command = make_command(
                    model=args.model,
                    output=run_dir,
                    n_envs=n_envs,
                    device=device,
                    timesteps=args.timesteps,
                    seed=seed,
                    start_stage=args.start_stage,
                )
                if args.dry_run:
                    print(shlex.join(command))
                    continue
                result = run_one(command, args.output / f"{name}.log")
                result.update({"n_envs": n_envs, "device": device, "seed": seed})
                results.append(result)
                recommendation = select_recommendation(results)
                (args.output / "benchmark.json").write_text(
                    json.dumps(
                        {
                            "updated_at": datetime.now().isoformat(),
                            "model": str(args.model.resolve()),
                            "results": results,
                            "recommendation": recommendation,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                (args.output / "README.md").write_text(
                    markdown(results), encoding="utf-8"
                )
                if recommendation is not None:
                    print(
                        "recommendation: "
                        f"n_envs={recommendation['n_envs']} "
                        f"device={recommendation['device']} "
                        f"median_fps={recommendation['median_fps']:.1f}",
                        flush=True,
                    )


if __name__ == "__main__":
    main()
