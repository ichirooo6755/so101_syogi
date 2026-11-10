"""Bounded deterministic search for the approved Gate 1/2 controller settings."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.diagnose_stroke_merge import GATE_THRESHOLD_PROFILES
from so101_calligraphy.pressure_calibration import PressureCalibration
from so101_calligraphy.training.provenance import collect_run_metadata


GATE1_CHARACTERS = "一三十"
DENSE_CHARACTERS = "目書飛鬱砕"
GATE2_CHARACTERS = "一三十目書飛鬱誠砕案"
ALL_LAYOUTS = "0,1,2,3,4,5"
DENSE_LAYOUTS = "0,1,4,5"


def _json_safe(value: object) -> object:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


@dataclass(frozen=True)
class Candidate:
    minimum_gap_m: float
    clearance_floor: float
    exemplar_motion_strength: float

    @property
    def name(self) -> str:
        return (
            f"gap-{1000 * self.minimum_gap_m:.1f}mm"
            f"-floor-{self.clearance_floor:.2f}"
            f"-motion-{self.exemplar_motion_strength:.2f}"
        )


def candidates() -> tuple[Candidate, ...]:
    return tuple(
        Candidate(gap, floor, motion)
        for gap in (0.0015, 0.0020, 0.0025)
        for floor in (0.35, 0.45)
        for motion in (0.72, 0.85, 1.0)
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(args: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def diagnostic_command(
    output: Path,
    *,
    calibration: Path | None,
    candidate: Candidate,
    characters: str,
    layouts: str,
    gate_level: int,
    model: Path | None = None,
    upright: bool = False,
    upright_baseline: Path | None = None,
    threshold_profile: str = "strict",
) -> list[str]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "diagnose_stroke_merge.py"),
        "--chars",
        characters,
        "--layouts",
        layouts,
        "--minimum-gap",
        str(candidate.minimum_gap_m),
        "--clearance-floor",
        str(candidate.clearance_floor),
        "--exemplar-motion-strength",
        str(candidate.exemplar_motion_strength),
        "--gate-level",
        str(gate_level),
        "--threshold-profile",
        threshold_profile,
        "--output",
        str(output),
    ]
    if calibration is not None:
        command[command.index("--gate-level"):command.index("--gate-level")] = [
            "--pressure-calibration",
            str(calibration),
            "--require-pressure-calibration",
            "--pressure-calibration-clip-rate-limit",
            "0.05",
            "--pressure-calibration-fallback-rate-limit",
            "0.05",
        ]
    if model is not None:
        command.extend(("--model", str(model)))
    if upright:
        command.append("--upright")
    if upright_baseline is not None:
        command.extend(("--upright-baseline", str(upright_baseline)))
    return command


def screen_rows(
    rows: Sequence[dict[str, Any]], *, threshold_profile: str = "strict"
) -> dict[str, Any]:
    profile = GATE_THRESHOLD_PROFILES[threshold_profile][1]
    minimum_successes = math.ceil(
        len(rows) * int(profile["min_successes"]) / 18
    )
    complete = sum(bool(row.get("is_success", False)) for row in rows) >= minimum_successes
    collision_cases = sum(
        bool(row.get("collision_types", [])) or bool(row.get("hard_limit", False))
        for row in rows
    )
    safe = collision_cases <= int(profile["max_collision_cases"])
    width_floor = all(
        float(row.get("width_ratio_median", 0.0))
        >= float(profile["width_ratio_min"])
        for row in rows
    )
    return {
        "evaluations": len(rows),
        "complete": complete,
        "safe": safe,
        "width_floor": width_floor,
        "eligible": bool(rows and complete and safe and width_floor),
    }


def candidate_rank(rows: Sequence[dict[str, Any]]) -> tuple[float, ...]:
    complete = sum(bool(row.get("is_success", False)) for row in rows)
    safe = sum(
        not row.get("collision_types", []) and not bool(row.get("hard_limit", False))
        for row in rows
    )
    tracking_failures = sum(
        float(row.get("pressure_error_median_abs", 1.0)) > 0.08
        or float(row.get("pressure_error_p90_abs", 1.0)) > 0.18
        or not 0.90 <= float(row.get("width_ratio_median", 0.0)) <= 1.10
        for row in rows
    )
    holes = sum(int(row.get("lost_holes", 0)) for row in rows)
    beauty = (
        sum(float(row.get("beauty_score", 0.0)) for row in rows) / len(rows)
        if rows
        else 0.0
    )
    return float(complete), float(safe), -float(tracking_failures), -float(holes), beauty


def _run(
    command: Sequence[str],
    *,
    deadline: float,
    git_sha: str,
    dirty: str,
    calibration_sha256: str,
) -> dict[str, Any]:
    if time.monotonic() >= deadline:
        raise TimeoutError("48-hour recovery deadline reached")
    print(shlex.join(command), flush=True)
    started = time.monotonic()
    env = os.environ | {"PYTHONPATH": str(ROOT / "src"), "MPLBACKEND": "Agg"}
    subprocess.run(command, cwd=ROOT, env=env, check=True)
    output = Path(command[command.index("--output") + 1])
    report = _json_safe(json.loads(output.read_text(encoding="utf-8")))
    if not isinstance(report, dict):
        raise ValueError(f"diagnostic output is not an object: {output}")
    report["run"] = {
        "command": shlex.join(command),
        "git_sha": git_sha,
        "dirty": dirty,
        "calibration_sha256": calibration_sha256,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "device": "cpu" if "--model" not in command else "configured-by-model",
        },
        "elapsed_seconds": time.monotonic() - started,
    }
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return report


def worker_count(requested: int, candidate_count: int) -> int:
    return max(1, min(int(requested), max(1, int(candidate_count))))


def main(argv: Sequence[str] | None = None) -> int:
    started_at = datetime.now().astimezone()
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pressure-calibration", type=Path, required=True)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--hours", type=float, default=48.0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument(
        "--threshold-profile",
        choices=tuple(GATE_THRESHOLD_PROFILES),
        default="strict",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    output = args.output.expanduser().resolve()
    calibration_path = args.pressure_calibration.expanduser().resolve()
    model = None if args.model is None else args.model.expanduser().resolve()
    if not args.dry_run:
        if output.exists():
            raise SystemExit(f"refusing to overwrite: {output}")
        if not calibration_path.is_file():
            raise SystemExit(f"pressure calibration does not exist: {calibration_path}")
        if model is not None and not model.is_file():
            raise SystemExit(f"model does not exist: {model}")
    output.mkdir(parents=True, exist_ok=args.dry_run)
    deadline = time.monotonic() + args.hours * 3600.0
    git_sha = _git(("rev-parse", "HEAD"))
    dirty = _git(("status", "--short"))
    calibration_sha = _sha256(calibration_path) if calibration_path.is_file() else "dry-run"
    calibration = (
        PressureCalibration.load(calibration_path)
        if calibration_path.is_file()
        else None
    )
    records: list[dict[str, Any]] = []
    eligible: list[tuple[tuple[float, ...], Candidate, dict[str, Any]]] = []

    def evaluate(candidate: Candidate) -> tuple[dict[str, Any], tuple[float, ...] | None]:
        directory = output / candidate.name
        directory.mkdir(parents=True, exist_ok=True)
        baseline_path = directory / "gate1-upright.json"
        gate1_path = directory / "gate1.json"
        dense_path = directory / "dense-screen.json"
        commands = [
            diagnostic_command(
                baseline_path,
                calibration=calibration_path,
                candidate=candidate,
                characters=GATE1_CHARACTERS,
                layouts=ALL_LAYOUTS,
                gate_level=0,
                model=model,
                upright=True,
                threshold_profile=args.threshold_profile,
            ),
            diagnostic_command(
                gate1_path,
                calibration=calibration_path,
                candidate=candidate,
                characters=GATE1_CHARACTERS,
                layouts=ALL_LAYOUTS,
                gate_level=1,
                model=model,
                upright_baseline=baseline_path,
                threshold_profile=args.threshold_profile,
            ),
            diagnostic_command(
                dense_path,
                calibration=calibration_path,
                candidate=candidate,
                characters=DENSE_CHARACTERS,
                layouts=DENSE_LAYOUTS,
                gate_level=0,
                model=model,
                threshold_profile=args.threshold_profile,
            ),
        ]
        if args.dry_run:
            for command in commands:
                print(shlex.join(command))
            return {"candidate": asdict(candidate), "name": candidate.name}, None
        reports = [
            _run(
                command,
                deadline=deadline,
                git_sha=git_sha,
                dirty=dirty,
                calibration_sha256=calibration_sha,
            )
            for command in commands
        ]
        gate1, dense = reports[1], reports[2]
        rows = [*gate1["results"], *dense["results"]]
        screen = screen_rows(rows, threshold_profile=args.threshold_profile)
        rank = candidate_rank(rows)
        record = {
            "candidate": asdict(candidate),
            "name": candidate.name,
            "gate1": gate1["summary"],
            "dense_screen": screen,
            "rank": list(rank),
            "paths": {
                "upright": str(baseline_path),
                "gate1": str(gate1_path),
                "dense": str(dense_path),
            },
        }
        candidate_eligible = (
            rank
            if bool(gate1["summary"].get("passed", False)) and screen["eligible"]
            else None
        )
        return record, candidate_eligible

    candidate_list = candidates()
    if args.dry_run:
        for candidate in candidate_list:
            evaluate(candidate)
    else:
        with ThreadPoolExecutor(
            max_workers=worker_count(args.workers, len(candidate_list))
        ) as executor:
            evaluated = list(executor.map(evaluate, candidate_list))
        for candidate, (record, candidate_rank_value) in zip(candidate_list, evaluated):
            records.append(record)
            if candidate_rank_value is not None:
                eligible.append((candidate_rank_value, candidate, record))

    if args.dry_run:
        return 0
    top = sorted(eligible, key=lambda item: item[0], reverse=True)[:2]
    gate2_records: list[dict[str, Any]] = []
    for _, candidate, record in top:
        gate2_path = output / candidate.name / "gate2.json"
        command = diagnostic_command(
            gate2_path,
            calibration=calibration_path,
            candidate=candidate,
            characters=GATE2_CHARACTERS,
            layouts=ALL_LAYOUTS,
            gate_level=2,
            model=model,
            threshold_profile=args.threshold_profile,
        )
        report = _run(
            command,
            deadline=deadline,
            git_sha=git_sha,
            dirty=dirty,
            calibration_sha256=calibration_sha,
        )
        gate2_record = {
            "candidate": asdict(candidate),
            "name": candidate.name,
            "summary": report["summary"],
            "rank": list(candidate_rank(report["results"])),
            "path": str(gate2_path),
        }
        gate2_records.append(gate2_record)
        record["gate2"] = gate2_record

    passed = [row for row in gate2_records if row["summary"].get("passed") is True]
    selected = max(passed, key=lambda row: tuple(row["rank"])) if passed else None
    beauty_only = [
        row
        for row in gate2_records
        if isinstance(row["summary"].get("gates"), dict)
        and row["summary"]["gates"].get("beauty") is False
        and all(
            value is True
            for name, value in row["summary"]["gates"].items()
            if name != "beauty"
        )
    ]
    rl_candidate = (
        max(beauty_only, key=lambda row: tuple(row["rank"]))
        if selected is None and beauty_only
        else None
    )
    run_argv = (
        None
        if argv is None
        else (sys.executable, str(Path(__file__).resolve()), *argv)
    )
    run_metadata = collect_run_metadata(
        purpose=f"{args.threshold_profile} Gate 1 and Gate 2 controller search",
        parent_model=model,
        started_at=started_at,
        cwd=ROOT,
        argv=run_argv,
        extra={
            "device": "cpu",
            "calibration_sha256": calibration_sha,
            "accepted": selected is not None,
            "threshold_profile": args.threshold_profile,
        },
    )
    run_metadata["elapsed_seconds"] = time.monotonic() - started
    run_metadata["status"] = "passed" if selected is not None else "failed"
    summary = {
        "schema_version": 1,
        "git_sha": git_sha,
        "dirty": dirty,
        "wall_clock_limit_hours": args.hours,
        "base_position_x_m": 0.030,
        "threshold_profile": args.threshold_profile,
        "thresholds_changed": args.threshold_profile != "strict",
        "calibration": {
            "path": str(calibration_path),
            "sha256": calibration_sha,
            "schema_version": None if calibration is None else calibration.schema_version,
            "cad_fingerprint": None if calibration is None else calibration.cad_fingerprint,
            "brush_fingerprint": None if calibration is None else calibration.brush_fingerprint,
        },
        "candidates": records,
        "gate2_candidates": gate2_records,
        "selected": selected,
        "rl_candidate": rl_candidate,
        "passed": selected is not None,
        "run": run_metadata,
    }
    (output / "search-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    if selected is not None:
        gate2_summary = selected["summary"]
        source = next(record for record in records if record["name"] == selected["name"])
        selection = {
            "ready_for_cuda": args.threshold_profile == "strict",
            "gate_schema_version": gate2_summary["gate_schema_version"],
            "gate_level": 2,
            "threshold_profile": args.threshold_profile,
            "evaluation_count": gate2_summary["evaluations"],
            "calibration": str(calibration_path),
            "calibration_sha256": calibration_sha,
            "calibration_fingerprint": None
            if calibration is None
            else calibration.cad_fingerprint,
            "config": selected["candidate"],
            "summary": gate2_summary,
            "diagnostic": selected["path"],
            "gate1_diagnostic": source["paths"]["gate1"],
            "upright_baseline": source["paths"]["upright"],
        }
        (output / "selected.json").write_text(
            json.dumps(selection, ensure_ascii=False, indent=2, allow_nan=False),
            encoding="utf-8",
        )
    elif rl_candidate is not None:
        source = next(
            record for record in records if record["name"] == rl_candidate["name"]
        )
        (output / "rl-candidate.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "candidate": rl_candidate["candidate"],
                    "gate1": source["gate1"],
                    "gate1_path": source["paths"]["gate1"],
                    "upright_baseline": source["paths"]["upright"],
                    "gate2": rl_candidate["summary"],
                    "gate2_path": rl_candidate["path"],
                    "calibration": str(calibration_path),
                    "calibration_sha256": calibration_sha,
                    "git_sha": git_sha,
                    "dirty": dirty,
                },
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
    return 0 if selected is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
