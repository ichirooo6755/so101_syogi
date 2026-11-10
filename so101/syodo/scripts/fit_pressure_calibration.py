"""Fit monotonic pressure-to-Z lookup tables from diagnostic run outputs."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np

from so101_calligraphy.pressure_calibration import (
    CALIBRATION_SCHEMA_VERSION,
    DEFAULT_BRUSH_FINGERPRINT,
    DEFAULT_CAD_FINGERPRINT,
    PressureCalibration,
    PressureCurve,
    SUPPORTED_ANGLES_DEG,
    monotone_non_decreasing,
)
from so101_calligraphy.training.provenance import collect_run_metadata


SUPPORTED_PHASES = ("entry", "send", "corner", "finish")
PRESSURE_KNOTS = (0.01, 0.08, 0.15, 0.22, 0.30, 0.38, 0.45)
MIN_SETTLED_DWELL = 40
MAX_XY_ERROR_M = 0.015


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _finite_values(
    sample: Mapping[str, Any], names: Sequence[str]
) -> dict[str, float] | None:
    values: dict[str, float] = {}
    try:
        for name in names:
            values[name] = float(sample[name])
    except (KeyError, TypeError, ValueError):
        return None
    return values if all(math.isfinite(value) for value in values.values()) else None


def _extract_samples(
    diagnostic_data: Mapping[str, Any], maximum_offset_m: float
) -> tuple[list[dict[str, Any]], int]:
    accepted: list[dict[str, Any]] = []
    total = 0
    for result in diagnostic_data.get("results", []):
        raw_samples = result.get("pressure_calibration_samples")
        legacy = raw_samples is None
        if legacy:
            raw_samples = result.get("longest_contact_targets", [])
        raw_samples = raw_samples if isinstance(raw_samples, list) else []
        total += len(raw_samples)
        if (
            not bool(result.get("is_success", False))
            or result.get("collision_types", [])
            or bool(result.get("hard_limit", False))
        ):
            continue

        layout_index = int(result.get("layout_index", 0))
        default_layout = "110mm" if layout_index in (4, 5) else "85mm"
        character = str(result.get("character", ""))
        for raw in raw_samples:
            if not isinstance(raw, Mapping):
                continue
            if legacy:
                sample = {
                    "layout_class": default_layout,
                    "commanded_angle_deg": result.get("commanded_angle_deg"),
                    "actual_angle_deg": result.get(
                        "actual_angle_median_deg",
                        result.get("final_actual_angle_deg", 0.0),
                    ),
                    "phase": raw.get("phase", "send"),
                    "target_pressure": raw.get("target_pressure"),
                    "actual_pressure": raw.get("actual_pressure_median"),
                    "z_offset_m": raw.get("pressure_offset_median_m"),
                    "contact_force": 1.0,
                    "actual_width_m": 1.0,
                    "target_width_m": 1.0,
                    "opening": 1.0,
                    "xy_error_m": raw.get("xy_error_last_m"),
                    "z_error_m": raw.get("z_error_last_m", 0.0),
                    "dwell": MIN_SETTLED_DWELL,
                    "contact": True,
                }
            else:
                sample = raw

            values = _finite_values(
                sample,
                (
                    "actual_angle_deg",
                    "target_pressure",
                    "actual_pressure",
                    "z_offset_m",
                    "contact_force",
                    "actual_width_m",
                    "target_width_m",
                    "opening",
                    "xy_error_m",
                    "z_error_m",
                    "dwell",
                ),
            )
            if values is None:
                continue
            try:
                commanded_angle = float(sample["commanded_angle_deg"])
            except (KeyError, TypeError, ValueError):
                continue
            if not math.isfinite(commanded_angle) or not commanded_angle.is_integer():
                continue
            angle = int(commanded_angle)
            phase = str(sample.get("phase", ""))
            layout_class = str(sample.get("layout_class", default_layout))
            if (
                not bool(sample.get("contact", False))
                or values["dwell"] < MIN_SETTLED_DWELL
                or values["contact_force"] <= 0.0
                or values["xy_error_m"] > MAX_XY_ERROR_M
                or angle not in SUPPORTED_ANGLES_DEG
                or phase not in SUPPORTED_PHASES
                or layout_class not in ("85mm", "110mm")
            ):
                continue
            # Positive Z raises the brush and reduces pressure. Therefore an
            # under-pressure sample needs a more negative (downward) offset.
            required_offset = values["z_offset_m"] + 0.006 * (
                values["actual_pressure"] - values["target_pressure"]
            )
            is_probe = bool(sample.get("probe", False))
            if is_probe:
                try:
                    probe_offset = float(sample["probe_offset_m"])
                except (KeyError, TypeError, ValueError):
                    continue
                if not math.isfinite(probe_offset):
                    continue
                required_offset = probe_offset
            accepted.append(
                {
                    "character": character,
                    "layout_index": layout_index,
                    "key": f"{layout_class}/{angle}/{phase}",
                    "target_pressure": (
                        values["actual_pressure"] if is_probe else values["target_pressure"]
                    ),
                    "required_offset_m": float(
                        np.clip(
                            required_offset,
                            -maximum_offset_m,
                            maximum_offset_m,
                        )
                    ),
                    "actual_width_m": values["actual_width_m"],
                    "probe": is_probe,
                    "probe_split": str(
                        sample.get("probe_split", result.get("probe_split", "fit"))
                    ),
                }
            )
    return accepted, total


def _fit_curves(
    samples: Sequence[Mapping[str, Any]], maximum_offset_m: float
) -> dict[str, PressureCurve]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for sample in samples:
        groups.setdefault(str(sample["key"]), []).append(sample)

    curves: dict[str, PressureCurve] = {}
    for key, group in groups.items():
        if len(group) < 2:
            continue
        is_probe_group = all(bool(sample.get("probe", False)) for sample in group)
        if is_probe_group:
            observed = sorted(
                (
                    float(sample["target_pressure"]),
                    float(sample["required_offset_m"]),
                )
                for sample in group
            )
            observed_pressure = np.asarray([row[0] for row in observed])
            observed_offset = np.asarray([row[1] for row in observed])
            knots = tuple(
                knot
                for knot in PRESSURE_KNOTS
                if observed_pressure[0] - 1e-12 <= knot <= observed_pressure[-1] + 1e-12
            )
            if len(knots) < 2:
                continue
            points = [
                (
                    knot,
                    float(np.interp(knot, observed_pressure, observed_offset)),
                    float(len(group)),
                )
                for knot in knots
            ]
        else:
            by_pressure: dict[float, list[float]] = {}
            for sample in group:
                by_pressure.setdefault(float(sample["target_pressure"]), []).append(
                    float(sample["required_offset_m"])
                )
            points = [
                (pressure, float(np.median(offsets)), float(len(offsets)))
                for pressure, offsets in sorted(by_pressure.items())
            ]
        if len(points) == 1:
            pressure, offset, weight = points[0]
            points = [
                (max(0.0, pressure - 0.025), offset, weight),
                (pressure + 0.025, offset, weight),
            ]
        elif len(points) > 4 and not is_probe_group:
            compressed = [
                (
                    float(np.median(chunk[:, 0])),
                    float(np.median(chunk[:, 1])),
                    float(np.sum(chunk[:, 2])),
                )
                for chunk in np.array_split(np.asarray(points), 4)
                if len(chunk)
            ]
            compressed[0] = (points[0][0], compressed[0][1], compressed[0][2])
            compressed[-1] = (
                points[-1][0],
                compressed[-1][1],
                compressed[-1][2],
            )
            points = compressed
        pressures = tuple(point[0] for point in points)
        weights = tuple(point[2] for point in points)
        offsets = tuple(
            -value
            for value in monotone_non_decreasing(
                tuple(-point[1] for point in points), weights
            )
        )
        curves[key] = PressureCurve(
            pressure=pressures,
            offset_m=tuple(
                float(np.clip(value, -maximum_offset_m, maximum_offset_m))
                for value in offsets
            ),
            sample_weight=weights,
        )
    return curves


def _validation(
    samples: Sequence[Mapping[str, Any]],
    curves: Mapping[str, PressureCurve],
    maximum_offset_m: float,
) -> dict[str, float]:
    def holdout_error(field: str) -> float:
        errors: list[float] = []
        for value in {sample[field] for sample in samples}:
            training = [sample for sample in samples if sample[field] != value]
            held_out = [sample for sample in samples if sample[field] == value]
            held_curves = _fit_curves(training, maximum_offset_m)
            for sample in held_out:
                curve = held_curves.get(str(sample["key"]))
                predicted = (
                    0.0
                    if curve is None
                    else curve.lookup(float(sample["target_pressure"]))[0]
                )
                errors.append(abs(predicted - float(sample["required_offset_m"])))
        return float(np.median(errors)) if errors else 0.0

    clipped = 0
    fallback = 0
    for sample in samples:
        curve = curves.get(str(sample["key"]))
        if curve is None:
            fallback += 1
        elif curve.lookup(float(sample["target_pressure"]))[1]:
            clipped += 1
    count = max(1, len(samples))
    return {
        "leave_one_character_median_abs_error_m": holdout_error("character"),
        "leave_one_layout_median_abs_error_m": holdout_error("layout_index"),
        "clip_rate": clipped / count,
        "fallback_rate": fallback / count,
    }


def _held_out_error(
    samples: Sequence[Mapping[str, Any]],
    curves: Mapping[str, PressureCurve],
) -> float:
    errors: list[float] = []
    for sample in samples:
        curve = curves.get(str(sample["key"]))
        if curve is None:
            continue
        prediction, clipped = curve.lookup(float(sample["target_pressure"]))
        if not clipped:
            errors.append(abs(prediction - float(sample["required_offset_m"])))
    return float(np.median(errors)) if errors else 0.0


def fit_calibration_from_diagnostics(
    diagnostic_data: dict[str, Any],
    *,
    maximum_offset_m: float = 0.0045,
    git_sha: str = "unknown",
    command_str: str = "fit_pressure_calibration",
    source_diagnostic_sha256: str = "unknown",
) -> PressureCalibration:
    samples, total_samples = _extract_samples(diagnostic_data, maximum_offset_m)
    fit_samples = [
        sample for sample in samples if sample.get("probe_split") != "held-out"
    ]
    held_out_samples = [
        sample for sample in samples if sample.get("probe_split") == "held-out"
    ]
    curves = _fit_curves(fit_samples, maximum_offset_m)
    summary = diagnostic_data.get("summary", {})
    config_fingerprint = (
        summary.get("configuration_fingerprint", "unknown")
        if isinstance(summary, Mapping)
        else "unknown"
    )
    validation = _validation(fit_samples, curves, maximum_offset_m)
    validation["held_out_median_abs_error_m"] = _held_out_error(
        held_out_samples, curves
    )
    width_groups: dict[str, list[float]] = {}
    for sample in fit_samples:
        if bool(sample.get("probe", False)):
            width_groups.setdefault(str(sample["key"]), []).append(
                float(sample["actual_width_m"])
            )
    return PressureCalibration(
        schema_version=CALIBRATION_SCHEMA_VERSION,
        cad_fingerprint=DEFAULT_CAD_FINGERPRINT,
        brush_fingerprint=DEFAULT_BRUSH_FINGERPRINT,
        maximum_offset_m=maximum_offset_m,
        curves=curves,
        provenance={
            "git_sha": git_sha,
            "command": command_str,
            "source_diagnostic_sha256": source_diagnostic_sha256,
            "configuration_fingerprint": str(config_fingerprint),
            "total_results": len(diagnostic_data.get("results", [])),
            "accepted_samples": len(samples),
            "fit_samples": len(fit_samples),
            "held_out_samples": len(held_out_samples),
            "excluded_samples": total_samples - len(samples),
            "pressure_knots": list(PRESSURE_KNOTS),
            "actual_width_p90_m": {
                key: float(np.percentile(values, 90))
                for key, values in sorted(width_groups.items())
            },
            "validation": validation,
        },
    )


def main(argv: Sequence[str] | None = None) -> int:
    started_at = datetime.now().astimezone()
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostic", type=Path, required=True, help="Input diagnostic JSON")
    parser.add_argument("--output", type=Path, required=True, help="Candidate calibration JSON")
    parser.add_argument("--max-offset", type=float, default=0.0045)
    args = parser.parse_args(argv)

    with args.diagnostic.open(encoding="utf-8") as handle:
        data = json.load(handle)
    command = shlex.join(
        [
            "fit_pressure_calibration",
            "--diagnostic",
            str(args.diagnostic),
            "--output",
            str(args.output),
            "--max-offset",
            str(args.max_offset),
        ]
    )
    source_sha256 = sha256_file(args.diagnostic)
    calibration = fit_calibration_from_diagnostics(
        data,
        maximum_offset_m=args.max_offset,
        git_sha=_git_sha(),
        command_str=command,
        source_diagnostic_sha256=source_sha256,
    )
    run_argv = (
        None
        if argv is None
        else (sys.executable, str(Path(__file__).resolve()), *argv)
    )
    run_metadata = collect_run_metadata(
        purpose="fit schema-v2 pressure calibration",
        started_at=started_at,
        cwd=Path(__file__).resolve().parents[1],
        argv=run_argv,
        extra={
            "device": "cpu",
            "calibration_sha256": None,
            "source_diagnostic_sha256": source_sha256,
        },
    )
    run_metadata["elapsed_seconds"] = time.monotonic() - started
    run_metadata["status"] = "completed"
    calibration = replace(
        calibration,
        provenance={**calibration.provenance, "run": run_metadata},
    )
    calibration.save(args.output)
    print(f"Saved calibration to {args.output} with {len(calibration.curves)} curves.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
