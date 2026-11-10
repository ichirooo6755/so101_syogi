"""Collect the seven-point open-loop pressure probe through existing diagnostics."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys
import time
from typing import Sequence

from so101_calligraphy.training.provenance import collect_run_metadata


PROBE_OFFSETS_M = (-0.0045, -0.003, -0.0015, 0.0, 0.0015, 0.003, 0.0045)
FIT_CHARACTERS = "一三十目書飛"
HELD_OUT_CHARACTERS = "鬱誠砕案"
ALL_CHARACTERS = FIT_CHARACTERS + HELD_OUT_CHARACTERS


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def diagnostic_commands(output_dir: Path, *, python: str = sys.executable) -> list[list[str]]:
    commands: list[list[str]] = []
    for index, offset in enumerate(PROBE_OFFSETS_M):
        commands.append(
            [
                python,
                "-u",
                "scripts/diagnose_stroke_merge.py",
                "--chars",
                ALL_CHARACTERS,
                "--layouts",
                "0,1,2,3,4,5",
                "--pressure-gain",
                "0",
                "--large-frame-pressure-gain",
                "0",
                "--horizontal-pressure-gain",
                "0",
                "--residual-pressure-integral-scale",
                "0",
                "--pressure-probe-offset-m",
                str(offset),
                "--gate-level",
                "0",
                "--output",
                str(output_dir / f"probe-{index}.json"),
            ]
        )
    return commands


def main(argv: Sequence[str] | None = None) -> int:
    started_at = datetime.now().astimezone()
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--merge-only",
        action="store_true",
        help="Reuse the seven existing part JSON files without rerunning diagnostics.",
    )
    args = parser.parse_args(argv)
    output = args.output.expanduser().resolve()
    work_dir = (
        args.work_dir.expanduser().resolve()
        if args.work_dir is not None
        else output.parent / f"{output.stem}-parts"
    )
    commands = diagnostic_commands(work_dir, python=args.python)
    if args.dry_run:
        print("\n".join(shlex.join(command) for command in commands))
        return 0

    work_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    sources: list[dict[str, object]] = []
    source_fingerprints: list[str] = []

    def run(command: Sequence[str]) -> None:
        part_path = Path(command[command.index("--output") + 1])
        with part_path.with_suffix(".log").open("w", encoding="utf-8") as log:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)

    if not args.merge_only:
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 7))) as executor:
            list(executor.map(run, commands))
    for command in commands:
        part_path = Path(command[command.index("--output") + 1])
        data = json.loads(part_path.read_text(encoding="utf-8"))
        part_summary = data.get("summary", {})
        fingerprint = (
            part_summary.get("configuration_fingerprint")
            if isinstance(part_summary, dict)
            else None
        )
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError(f"missing configuration fingerprint in {part_path}")
        source_fingerprints.append(fingerprint)
        part_results = data.get("results", [])
        if not isinstance(part_results, list):
            raise ValueError(f"invalid results in {part_path}")
        for result in part_results:
            if not isinstance(result, dict):
                raise ValueError(f"invalid result in {part_path}")
            result = _json_safe(result)
            if not isinstance(result, dict):
                raise ValueError(f"invalid result in {part_path}")
            split = "fit" if str(result.get("character", "")) in FIT_CHARACTERS else "held-out"
            result["probe_split"] = split
            for sample in result.get("pressure_calibration_samples", []):
                if isinstance(sample, dict):
                    sample["probe_split"] = split
            results.append(result)
        sources.append(
            {
                "path": str(part_path),
                "sha256": _sha256(part_path),
                "command": shlex.join(command),
            }
        )

    expected = len(PROBE_OFFSETS_M) * len(ALL_CHARACTERS) * 6
    if len(results) != expected:
        raise RuntimeError(f"probe produced {len(results)} results, expected {expected}")
    aggregate_fingerprint = hashlib.sha256(
        json.dumps(
            source_fingerprints,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    run_argv = (
        None
        if argv is None
        else (sys.executable, str(Path(__file__).resolve()), *argv)
    )
    run_metadata = collect_run_metadata(
        purpose="seven-point open-loop pressure probe",
        started_at=started_at,
        cwd=Path(__file__).resolve().parents[1],
        argv=run_argv,
        extra={"device": "cpu", "calibration_sha256": None},
    )
    run_metadata["elapsed_seconds"] = time.monotonic() - started
    run_metadata["status"] = "completed"
    payload = {
        "summary": {
            "probe_schema_version": 1,
            "offsets_m": list(PROBE_OFFSETS_M),
            "pressure_knots": [0.01, 0.08, 0.15, 0.22, 0.30, 0.38, 0.45],
            "fit_characters": FIT_CHARACTERS,
            "held_out_characters": HELD_OUT_CHARACTERS,
            "layouts": [0, 1, 2, 3, 4, 5],
            "feedback_gain": 0.0,
            "results": len(results),
            "configuration_fingerprint": aggregate_fingerprint,
            "source_configuration_fingerprints": source_fingerprints,
            "sources": sources,
            "run": run_metadata,
        },
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    print(f"Saved {len(results)} probe results to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
