"""Run at most five 100k PPO chunks when Gate 2 fails only on beauty."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from typing import Any, Sequence

from scripts.search_gate_recovery import (
    ALL_LAYOUTS,
    GATE1_CHARACTERS,
    GATE2_CHARACTERS,
    Candidate,
    candidate_rank,
    diagnostic_command,
    screen_rows,
)


ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "fonts" / "A-OTF-KaishoMCBK1Pro-DeBold.otf"


def beauty_only_failure(summary: dict[str, Any]) -> bool:
    gates = summary.get("gates")
    return bool(
        summary.get("gate_level") == 2
        and summary.get("passed") is False
        and isinstance(gates, dict)
        and gates.get("beauty") is False
        and all(value is True for name, value in gates.items() if name != "beauty")
    )


def training_command(
    *,
    python: Path,
    parent: Path,
    output: Path,
    calibration: Path,
    candidate: Candidate,
    first_chunk: bool,
) -> list[str]:
    command = [
        str(python),
        "-u",
        "-m",
        "so101_calligraphy.training.professional",
        "--ablation",
        "all",
        "--run-purpose",
        "Gate 2 beauty-only bounded PPO",
        "--initial-model",
        str(parent),
        "--exemplar-font",
        str(FONT),
        "--start-stage",
        "8",
        "--end-stage",
        "8",
        "--timesteps",
        "100000",
        "--bc-steps",
        "100000",
        "--bc-epochs",
        "3",
        "--n-envs",
        "8",
        "--require-subproc",
        "--bc-workers",
        "8",
        "--n-steps",
        "2048",
        "--batch-size",
        "1024",
        "--learning-rate",
        "5e-05",
        "--clip-range",
        "0.1",
        "--target-kl",
        "0.03",
        "--device",
        "cuda",
        "--pressure-calibration",
        str(calibration),
        "--require-pressure-calibration",
        "--pressure-calibration-clip-rate-limit",
        "0.05",
        "--minimum-gap",
        str(candidate.minimum_gap_m),
        "--clearance-floor",
        str(candidate.clearance_floor),
        "--exemplar-motion-strength",
        str(candidate.exemplar_motion_strength),
        "--train-only",
        "--allow-gate-failure",
        "--output",
        str(output),
    ]
    command.append("--policy-only-warm-start" if first_chunk else "--skip-bc")
    return command


def _run(command: Sequence[str], *, deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise TimeoutError("48-hour deadline reached")
    print(shlex.join(command), flush=True)
    subprocess.run(
        command,
        cwd=ROOT,
        env=os.environ | {"PYTHONPATH": str(ROOT / "src"), "MPLBACKEND": "Agg"},
        check=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--parent-model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--hours", type=float, default=48.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    if not beauty_only_failure(evidence.get("gate2", {})):
        raise SystemExit("limited RL requires Gate 2 with beauty as the only failure")
    values = evidence["candidate"]
    candidate = Candidate(
        float(values["minimum_gap_m"]),
        float(values["clearance_floor"]),
        float(values["exemplar_motion_strength"]),
    )
    calibration = Path(evidence["calibration"]).resolve()
    baseline = Path(evidence["upright_baseline"]).resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=args.dry_run)
    deadline = time.monotonic() + args.hours * 3600.0
    baseline_report = json.loads(Path(evidence["gate2_path"]).read_text(encoding="utf-8"))
    best_rank = candidate_rank(baseline_report["results"])
    best_model = args.parent_model.resolve()
    no_improvement = 0
    records: list[dict[str, Any]] = []
    for chunk in range(1, 6):
        chunk_dir = output / f"chunk-{chunk}"
        first_chunk = best_model == args.parent_model.resolve()
        train = training_command(
            python=args.python,
            parent=best_model,
            output=chunk_dir,
            calibration=calibration,
            candidate=candidate,
            first_chunk=first_chunk,
        )
        model = chunk_dir / "final_model.zip"
        gate1_path = chunk_dir / "gate1.json"
        gate2_path = chunk_dir / "gate2.json"
        screens = [
            diagnostic_command(
                gate1_path,
                calibration=calibration,
                candidate=candidate,
                characters=GATE1_CHARACTERS,
                layouts=ALL_LAYOUTS,
                gate_level=1,
                model=model,
                upright_baseline=baseline,
            ),
            diagnostic_command(
                gate2_path,
                calibration=calibration,
                candidate=candidate,
                characters=GATE2_CHARACTERS,
                layouts=ALL_LAYOUTS,
                gate_level=2,
                model=model,
            ),
        ]
        if args.dry_run:
            print(shlex.join(train))
            for command in screens:
                print(shlex.join(command))
            continue
        _run(train, deadline=deadline)
        for command in screens:
            _run(command, deadline=deadline)
        gate1 = json.loads(gate1_path.read_text(encoding="utf-8"))
        gate2 = json.loads(gate2_path.read_text(encoding="utf-8"))
        rows = [*gate1["results"], *gate2["results"]]
        safety = screen_rows(rows)
        rank = candidate_rank(gate2["results"])
        improved = safety["eligible"] and rank > best_rank
        record = {
            "chunk": chunk,
            "model": str(model),
            "gate1": gate1["summary"],
            "gate2": gate2["summary"],
            "safety": safety,
            "rank": list(rank),
            "accepted": improved,
        }
        records.append(record)
        if not safety["complete"] or not safety["safe"]:
            no_improvement += 1
        elif improved:
            best_rank = rank
            best_model = model
            no_improvement = 0
        else:
            no_improvement += 1
        (output / "status.json").write_text(
            json.dumps(
                {"records": records, "best_model": str(best_model)},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        if gate1["summary"].get("passed") and gate2["summary"].get("passed"):
            (output / "selected.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return 0
        if no_improvement >= 2:
            break
    return 0 if args.dry_run else 2


if __name__ == "__main__":
    raise SystemExit(main())
