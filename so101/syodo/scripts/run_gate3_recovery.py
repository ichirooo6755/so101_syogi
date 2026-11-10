"""Run and merge the strict 128-character x six-layout Gate 3 in eight shards."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import scripts.diagnose_stroke_merge as diagnostics
from scripts.search_gate_recovery import Candidate
from so101_calligraphy.pressure_calibration import PressureCalibration
from so101_calligraphy.training.provenance import collect_run_metadata


DEFAULT_R1_PARENT = (
    ROOT / "runs" / "kaisho-yohitsu-brushmark-joyo" / "08-joyo" / "model.zip"
)


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


def r1_parent_model(
    candidate_model: Path | None,
    explicit_parent: Path | None,
) -> Path:
    return explicit_parent or candidate_model or DEFAULT_R1_PARENT


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _evidence_path(path: Path) -> str:
    resolved = path.expanduser().resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def shard_command(
    *,
    output: Path,
    calibration: Path | None,
    candidate: Candidate,
    shard_index: int,
    model: Path | None,
    threshold_profile: str = "strict",
) -> list[str]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "diagnose_stroke_merge.py"),
        "--eval-limit",
        "128",
        "--eval-shard-count",
        "8",
        "--eval-shard-index",
        str(shard_index),
        "--layouts",
        "0,1,2,3,4,5",
        "--minimum-gap",
        str(candidate.minimum_gap_m),
        "--clearance-floor",
        str(candidate.clearance_floor),
        "--exemplar-motion-strength",
        str(candidate.exemplar_motion_strength),
        "--gate-level",
        "0",
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
    return command


def merge_reports(
    reports: Sequence[dict[str, Any]], *, threshold_profile: str = "strict"
) -> dict[str, Any]:
    rows = [row for report in reports for row in report.get("results", [])]
    samples = [
        sample
        for row in rows
        for sample in row.get("pressure_calibration_samples", [])
    ]
    count = len(samples)
    clip_rate = (
        sum(bool(sample.get("clipped", False)) for sample in samples) / count
        if count
        else 0.0
    )
    fallback_rate = (
        sum(bool(sample.get("fallback", False)) for sample in samples) / count
        if count
        else 0.0
    )
    summary = diagnostics.summarize_physical_gate(
        rows,
        gate_level=3,
        endpoint_improvement=None,
        calibration_clip_rate=clip_rate,
        calibration_fallback_rate=fallback_rate,
        clip_rate_limit=0.05,
        fallback_rate_limit=0.05,
        threshold_profile=threshold_profile,
    )
    pairs = [
        (str(row.get("character", "")), int(row.get("layout_index", -1)))
        for row in rows
    ]
    characters = {character for character, _ in pairs if character}
    exact_shape = bool(
        len(rows) == 768
        and len(pairs) == len(set(pairs))
        and len(characters) == 128
        and all(
            {layout for character, layout in pairs if character == glyph}
            == set(range(6))
            for glyph in characters
        )
    )
    summary["gates"]["evaluation_count"] = exact_shape
    summary["passed"] = bool(all(summary["gates"].values()))
    summary["ready_for_r1"] = bool(
        threshold_profile in diagnostics.TRAINING_AUTHORITY_PROFILES
        and summary["passed"]
    )
    fingerprints = {
        str(report.get("summary", {}).get("configuration_fingerprint", ""))
        for report in reports
    }
    summary["configuration_fingerprint"] = (
        next(iter(fingerprints)) if len(fingerprints) == 1 else "mismatch"
    )
    summary["unique_character_count"] = len(characters)
    summary["layout_count"] = len({layout for _, layout in pairs})
    return {"summary": summary, "results": rows}


def main(argv: Sequence[str] | None = None) -> int:
    started_at = datetime.now().astimezone()
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate2-evidence", type=Path, required=True)
    parser.add_argument("--model", type=Path)
    parser.add_argument(
        "--r1-parent-model",
        type=Path,
        help="Model recorded for r1 preflight; defaults to --model or the canonical parent.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--reuse-shards",
        type=Path,
        help="merge existing shard-0..7 JSONs from this directory without rerunning them",
    )
    parser.add_argument(
        "--threshold-profile",
        choices=tuple(diagnostics.GATE_THRESHOLD_PROFILES),
        default=None,
        help="defaults to the profile recorded in Gate 2 evidence",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    gate2_path = args.gate2_evidence.expanduser().resolve()
    gate2 = json.loads(gate2_path.read_text(encoding="utf-8"))
    summary = gate2.get("summary", gate2.get("gate2", {}))
    if not isinstance(summary, dict) or summary.get("gate_level") != 2 or not summary.get("passed"):
        raise SystemExit("Gate 3 requires passed Gate 2 evidence")
    config = gate2.get("config", gate2.get("candidate"))
    if not isinstance(config, dict):
        raise SystemExit("Gate 2 evidence is missing the selected config")
    candidate = Candidate(
        float(config["minimum_gap_m"]),
        float(config["clearance_floor"]),
        float(config["exemplar_motion_strength"]),
    )
    threshold_profile = args.threshold_profile or str(
        summary.get("threshold_profile", "strict")
    )
    if threshold_profile not in diagnostics.GATE_THRESHOLD_PROFILES:
        raise SystemExit(f"unknown threshold profile: {threshold_profile}")
    calibration_value = gate2.get("calibration")
    calibration = (
        None
        if calibration_value in (None, "")
        else Path(str(calibration_value)).expanduser()
    )
    if calibration is not None:
        if not calibration.is_absolute():
            calibration = ROOT / calibration
        calibration = calibration.resolve()
    if calibration is None and threshold_profile == "strict":
        raise SystemExit("strict Gate 3 requires a pressure calibration")
    model = None if args.model is None else args.model.expanduser().resolve()
    explicit_parent = (
        None
        if args.r1_parent_model is None
        else args.r1_parent_model.expanduser().resolve()
    )
    parent_model = r1_parent_model(model, explicit_parent)
    output = args.output.expanduser().resolve()
    if output.exists() and not args.dry_run:
        raise SystemExit(f"refusing to overwrite: {output}")
    if not args.dry_run:
        if calibration is not None and not calibration.is_file():
            raise SystemExit(f"missing calibration: {calibration}")
        if model is not None and not model.is_file():
            raise SystemExit(f"missing model: {model}")
        if not parent_model.is_file():
            raise SystemExit(f"missing r1 parent model: {parent_model}")
        if args.reuse_shards is not None:
            shard_source = args.reuse_shards.expanduser().resolve()
            if not shard_source.is_dir():
                raise SystemExit(f"missing shard directory: {shard_source}")
            missing = [
                shard_source / f"shard-{index}.json"
                for index in range(8)
                if not (shard_source / f"shard-{index}.json").is_file()
            ]
            if missing:
                raise SystemExit(
                    "missing existing shards: " + ", ".join(map(str, missing))
                )
    output.mkdir(parents=True, exist_ok=args.dry_run)
    commands = [
        shard_command(
            output=output / f"shard-{index}.json",
            calibration=calibration,
            candidate=candidate,
            shard_index=index,
            model=model,
            threshold_profile=threshold_profile,
        )
        for index in range(8)
    ]
    if args.dry_run:
        print("\n".join(shlex.join(command) for command in commands))
        return 0

    env = os.environ | {"PYTHONPATH": str(ROOT / "src"), "MPLBACKEND": "Agg"}

    def run(command: Sequence[str]) -> None:
        subprocess.run(command, cwd=ROOT, env=env, check=True)

    if args.reuse_shards is None:
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as executor:
            list(executor.map(run, commands))
        shard_source = output
    else:
        shard_source = args.reuse_shards.expanduser().resolve()
    reports = [
        _json_safe(
            json.loads(
                (shard_source / f"shard-{index}.json").read_text(encoding="utf-8")
            )
        )
        for index in range(8)
    ]
    merged = merge_reports(reports, threshold_profile=threshold_profile)
    (output / "gate3.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    calibration_model = (
        None if calibration is None else PressureCalibration.load(calibration)
    )
    shard_evidence = [
        {
            "path": str(shard_source / f"shard-{index}.json"),
            "sha256": _sha256(shard_source / f"shard-{index}.json"),
            "command": shlex.join(commands[index]),
        }
        for index in range(8)
    ]
    gate3_summary = merged["summary"]
    run_argv = (
        None
        if argv is None
        else (sys.executable, str(Path(__file__).resolve()), *argv)
    )
    run_metadata = collect_run_metadata(
        purpose=f"{threshold_profile} Gate 3 recovery evaluation",
        parent_model=parent_model,
        started_at=started_at,
        cwd=ROOT,
        argv=run_argv,
        extra={
            "device": "cpu",
            "calibration_sha256": (
                None if calibration is None else _sha256(calibration)
            ),
            "accepted": bool(gate3_summary["ready_for_r1"]),
            "threshold_profile": threshold_profile,
        },
    )
    run_metadata["elapsed_seconds"] = time.monotonic() - started
    run_metadata["status"] = (
        "passed"
        if gate3_summary["ready_for_r1"]
        else "passed_diagnostic"
        if gate3_summary["passed"]
        else "failed"
    )
    upright_raw = gate2.get("upright_baseline")
    upright = None
    if isinstance(upright_raw, str) and upright_raw:
        upright_path = Path(upright_raw).expanduser()
        if not upright_path.is_absolute():
            upright_path = ROOT / upright_path
        upright = _evidence_path(upright_path)
    evidence = {
        "passed": bool(gate3_summary["passed"]),
        "diagnostic_only": threshold_profile == "relaxed-recovery",
        "canonical_eligible": threshold_profile == "strict",
        "ready_for_r1": bool(gate3_summary["ready_for_r1"]),
        "gate_schema_version": gate3_summary["gate_schema_version"],
        "gate_level": 3,
        "threshold_profile": threshold_profile,
        "evaluation_count": gate3_summary["evaluations"],
        "model": _evidence_path(parent_model),
        "model_sha256": _sha256(parent_model),
        "config": config,
        "config_sha256": _json_sha256(config),
        "configuration_fingerprint": gate3_summary["configuration_fingerprint"],
        "calibration": None if calibration is None else _evidence_path(calibration),
        "calibration_sha256": (
            None if calibration is None else _sha256(calibration)
        ),
        "calibration_schema_version": (
            None if calibration_model is None else calibration_model.schema_version
        ),
        "cad_fingerprint": (
            None if calibration_model is None else calibration_model.cad_fingerprint
        ),
        "brush_fingerprint": (
            None if calibration_model is None else calibration_model.brush_fingerprint
        ),
        "gate2_evidence": _evidence_path(gate2_path),
        "gate2_evidence_sha256": _sha256(gate2_path),
        "upright_baseline": upright,
        "summary": gate3_summary,
        "shards": shard_evidence,
        "run": run_metadata,
        "next_action": (
            "start_r1"
            if gate3_summary["ready_for_r1"]
            else "return_to_controller_once"
            if not gate3_summary["gates"]["complete"]
            or not gate3_summary["gates"]["collision_and_hard_limit_free"]
            else "hard_mine_quality_failures_max_500k"
        ),
    }
    (output / "gate3-evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    return 0 if evidence["ready_for_r1"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
