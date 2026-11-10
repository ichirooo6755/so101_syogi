"""Merge parallel stroke-merge diagnostic shards into one gate artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from diagnose_stroke_merge import summarize_physical_gate


def merge_diagnostics(paths: list[Path], *, gate_level: int, output: Path) -> dict[str, object]:
    results: list[dict[str, object]] = []
    fingerprints: set[str] = set()
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise ValueError(f"invalid diagnostic shard: {path}")
        summary = payload.get("summary", {})
        if isinstance(summary, dict) and summary.get("configuration_fingerprint"):
            fingerprints.add(str(summary["configuration_fingerprint"]))
        results.extend(payload["results"])
    keys = [(str(row["character"]), int(row["layout_index"])) for row in results]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate character/layout result in diagnostic shards")
    expected = {1: 18, 2: 60, 3: 768}[gate_level]
    if len(results) != expected:
        raise ValueError(f"expected {expected} rows for gate {gate_level}, got {len(results)}")
    results.sort(key=lambda row: (str(row["character"]), int(row["layout_index"])))
    samples = [
        sample
        for row in results
        for sample in row.get("pressure_calibration_samples", [])
    ]
    sample_count = len(samples)
    clip_rate = (
        sum(bool(sample.get("clipped", False)) for sample in samples) / sample_count
        if sample_count
        else 0.0
    )
    fallback_rate = (
        sum(bool(sample.get("fallback", False)) for sample in samples) / sample_count
        if sample_count
        else 0.0
    )
    summary = summarize_physical_gate(
        results,
        gate_level=gate_level,
        endpoint_improvement=None,
        calibration_clip_rate=clip_rate,
        calibration_fallback_rate=fallback_rate,
        clip_rate_limit=0.05,
    )
    summary.update(
        configuration_fingerprint=next(iter(fingerprints), None),
        pressure_calibration_samples=sample_count,
        shard_count=len(paths),
    )
    merged = {"summary": summary, "results": results}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shards", nargs="+", type=Path)
    parser.add_argument("--gate-level", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    merged = merge_diagnostics(args.shards, gate_level=args.gate_level, output=args.output)
    summary = merged["summary"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"-> {args.output}")


if __name__ == "__main__":
    main()
