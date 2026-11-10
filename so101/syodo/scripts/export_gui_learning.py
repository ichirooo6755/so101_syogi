#!/usr/bin/env python3
"""Export reviewed robot + single-cell observations with explicit clock bounds.

This exports training observations, not a learned policy. Split evaluation by
session, and identify gravity/inertia before treating axial force as tip force.
"""
from __future__ import annotations
import argparse
import bisect
import csv
import json
import math
from pathlib import Path

JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")


def export(session: Path, out: Path):
    review = json.loads((session / "review.json").read_text())
    if review.get("physical_result_reviewed") is not True or review.get("result") not in ("good", "bad"):
        raise ValueError("先に実物の結果を「良い／やり直し」で記録してください")
    rows = [json.loads(line) for line in (session / "loadcell.jsonl").read_text().splitlines() if line.strip()]
    header = next((r for r in rows if r.get("event") == "session"), None)
    if not header or header["calibration"].get("validated") is not True:
        raise ValueError("独立した重りで確認したロードセル較正が必要です")
    cal = header["calibration"]
    samples = sorted((r for r in rows if "host_sample_monotonic_s" in r), key=lambda r: r["host_sample_monotonic_s"])
    times = [r["host_sample_monotonic_s"] for r in samples]
    observations = []
    rejected = 0
    seen = set()
    with (session / "write.csv").open() as source:
        for robot in csv.DictReader(source):
            try:
                if robot.get("phase") not in ("write", "bilateral"):
                    continue
                stamp = float(robot["host_monotonic_s"])
                i = bisect.bisect_left(times, stamp)
                candidates = samples[max(0, i - 1):i + 1]
                if not candidates:
                    raise ValueError("missing")
                force = min(candidates, key=lambda r: abs(r["host_sample_monotonic_s"] - stamp))
                separation = abs(force["host_sample_monotonic_s"] - stamp)
                uncertainty = float(force["clock_uncertainty_s"])
                if separation + uncertainty > .06 or uncertainty > .03:
                    raise ValueError("synchronization")
                if force.get("binding") != cal.get("binding") or force.get("boot_id") != cal["tare_boot_id"] or force.get("ready") is not True or force.get("saturated") is not False:
                    raise ValueError("invalid force")
                identity = (force["boot_id"], force["sequence"])
                if identity in seen:
                    continue  # Do not inflate a 10 Hz ADC into 30 Hz measurements.
                seen.add(identity)
                actual = [float(robot[f"position_deg:{j}"]) for j in JOINTS]
                requested = [float(robot[f"command_deg:{j}"]) for j in JOINTS]
                value = (force["raw_counts"] - cal["zero_counts"]) * cal["newtons_per_count"]
                if not all(math.isfinite(v) for v in [stamp, value, *actual, *requested]):
                    raise ValueError("nonfinite")
                row = {"session": session.name, "force_session": header["force_session"],
                       "time_monotonic_s": stamp, "force_sensor_axis_n": value,
                       "sync_bound_s": separation + uncertainty,
                       "phase": robot["phase"], "pen_down_command": robot.get("pen_down", ""),
                       "human_result": review["result"], "target_pressure_normalized": robot.get("target_pressure", "")}
                row.update({f"position_deg:{j}": v for j, v in zip(JOINTS, actual)})
                row.update({f"action_delta_deg:{j}": b - a for j, a, b in zip(JOINTS, actual, requested)})
                observations.append(row)
            except (ValueError, KeyError, TypeError):
                rejected += 1
    if len(observations) < 20:
        raise ValueError(f"同期した有効な観測が不足しています（{len(observations)}件）。実測データを記録してください")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "observations.csv").open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(observations[0]))
        writer.writeheader()
        writer.writerows(observations)
    report = {"observations": len(observations), "rejected": rejected, "review": review,
              "source_session": str(session.resolve()), "policy_trained": False,
              "force_semantics": "sensor_axis_including_gravity_and_inertia",
              "tip_force_measured": False, "evaluation_split": "hold_out_complete_sessions"}
    (out / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("session", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        print(json.dumps(export(args.session, args.out), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    main()
