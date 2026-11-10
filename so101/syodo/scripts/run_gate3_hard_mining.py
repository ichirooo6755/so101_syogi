"""Build the bounded Gate 3 quality hard-mining pool and 500k CUDA command."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any, Sequence

from scripts.search_gate_recovery import Candidate


ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "fonts" / "A-OTF-KaishoMCBK1Pro-DeBold.otf"


def _quality_failure(row: dict[str, Any]) -> bool:
    return bool(
        float(row.get("pressure_error_median_abs", 1.0)) > 0.08
        or float(row.get("pressure_error_p90_abs", 1.0)) > 0.18
        or not 0.90 <= float(row.get("width_ratio_median", 0.0)) <= 1.10
        or int(row.get("lost_holes", 0)) > 0
    )


def select_hard_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    failures = [row for row in rows if _quality_failure(row)]
    selected: list[dict[str, Any]] = list(failures)
    for layout in sorted({int(row["layout_index"]) for row in failures}):
        control = next(
            (
                row
                for row in rows
                if int(row.get("layout_index", -1)) == layout
                and not _quality_failure(row)
                and not row.get("collision_types", [])
                and bool(row.get("is_success", False))
            ),
            None,
        )
        if control is not None:
            selected.append(control)
    return selected


def training_command(
    *,
    python: Path,
    parent: Path,
    output: Path,
    calibration: Path,
    hard_csv: Path,
    candidate: Candidate,
    layouts: Sequence[int],
) -> list[str]:
    return [
        str(python),
        "-u",
        "-m",
        "so101_calligraphy.training.professional",
        "--ablation",
        "all",
        "--run-purpose",
        "Gate 3 pressure-width-negative-space hard mining",
        "--initial-model",
        str(parent),
        "--policy-only-warm-start",
        "--exemplar-font",
        str(FONT),
        "--start-stage",
        "9",
        "--end-stage",
        "9",
        "--hard-csv",
        str(hard_csv),
        "--training-layouts",
        ",".join(str(layout) for layout in layouts),
        "--timesteps",
        "500000",
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


def _csv_row(row: dict[str, Any], *, force_hard: bool) -> dict[str, object]:
    components = row.get("beauty_components", {})
    return {
        "character": row["character"],
        "layout_index": row["layout_index"],
        "success": int(bool(row.get("is_success", False))),
        "progress": float(row.get("progress", 1.0)),
        "beauty_score": float(row.get("beauty_score", 0.0)),
        "line_width": 0.0 if force_hard else float(components.get("line_width", 100.0)),
        "brushwork": float(components.get("brushwork", 100.0)),
        "drip_count": 0,
        "unintended_ink_fraction": 0.0,
        "collision": ";".join(row.get("collision_types", [])),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate3", type=Path, required=True)
    parser.add_argument("--gate2-evidence", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    gate3 = json.loads(args.gate3.read_text(encoding="utf-8"))
    summary = gate3["summary"]
    if not summary["gates"]["complete"] or not summary["gates"]["collision_and_hard_limit_free"]:
        raise SystemExit("safety/completion failures must return to controller, not hard mining")
    selected_rows = select_hard_rows(gate3["results"])
    if not selected_rows:
        raise SystemExit("Gate 3 has no pressure, width, or negative-space failures")
    evidence = json.loads(args.gate2_evidence.read_text(encoding="utf-8"))
    config = evidence.get("config", evidence.get("candidate"))
    candidate = Candidate(
        float(config["minimum_gap_m"]),
        float(config["clearance_floor"]),
        float(config["exemplar_motion_strength"]),
    )
    calibration = Path(str(evidence["calibration"]))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=args.dry_run)
    hard_csv = output / "hard-characters.csv"
    if not args.dry_run:
        by_character: dict[str, dict[str, Any]] = {}
        for row in selected_rows:
            by_character.setdefault(str(row["character"]), row)
        with hard_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(_csv_row(next(iter(by_character.values())), force_hard=True)),
            )
            writer.writeheader()
            for row in by_character.values():
                # Controls are intentionally sampled with failures, so both
                # groups must enter the stage-9 pool.
                writer.writerow(_csv_row(row, force_hard=True))
    layouts = tuple(sorted({int(row["layout_index"]) for row in selected_rows}))
    command = training_command(
        python=args.python,
        parent=args.model,
        output=output / "train",
        calibration=calibration,
        hard_csv=hard_csv,
        candidate=candidate,
        layouts=layouts,
    )
    if args.dry_run:
        print(shlex.join(command))
        return 0
    subprocess.run(command, cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
