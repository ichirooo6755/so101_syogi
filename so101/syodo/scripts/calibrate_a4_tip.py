"""Select low-pressure and entry-angle calibration before Windows CUDA training."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.diagnose_stroke_merge import GATE_THRESHOLD_PROFILES


DEFAULT_OUTPUT = ROOT / "runs" / "kaisho-yohitsu-brush-tilt-a4-tip-calibration"
CHARS = "一三十目書飛鬱誠砕案"
LAYOUTS = "0,1,2,3,4,5"
DEFAULT_PRESSURE_GAIN = 0.014


def _command(
    output: Path,
    *,
    gain: float = DEFAULT_PRESSURE_GAIN,
    limit: float = 0.0035,
    angle: float = 30.0,
    upright: bool = False,
    baseline: Path | None = None,
    images: Path | None = None,
    legacy_sixty_mm: bool = False,
    gate_level: int = 2,
    pressure_calibration: Path | None = None,
    threshold_profile: str = "strict",
) -> list[str]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "diagnose_stroke_merge.py"),
        "--chars",
        "一三十" if gate_level == 1 else CHARS,
        "--layouts",
        LAYOUTS,
        "--pressure-gain",
        str(gain),
        "--pressure-limit",
        str(limit),
        "--entry-angle",
        str(angle),
        "--max-steps",
        "25000",
        "--output",
        str(output),
        "--gate-level",
        str(gate_level),
        "--threshold-profile",
        threshold_profile,
    ]
    if pressure_calibration is not None:
        command.extend(
            (
                "--pressure-calibration",
                str(pressure_calibration),
                "--require-pressure-calibration",
                "--pressure-calibration-clip-rate-limit",
                "0.05",
                "--pressure-calibration-fallback-rate-limit",
                "0.05",
            )
        )
    if upright:
        command.append("--upright")
    if baseline is not None:
        command.extend(("--upright-baseline", str(baseline)))
    if images is not None:
        command.extend(("--images-dir", str(images)))
    if legacy_sixty_mm:
        command.append("--legacy-sixty-mm")
    return command


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_selection(
    *,
    summary: dict[str, Any],
    calibration: Path,
    diagnostic: Path,
) -> dict[str, Any]:
    gate_level = int(summary.get("gate_level", 0))
    evaluations = int(summary.get("evaluations", 0))
    ready = bool(
        gate_level == 2
        and evaluations == 60
        and summary.get("passed") is True
        and summary.get("ready_for_cuda") is True
    )
    resolved_calibration = calibration.resolve()
    try:
        calibration_reference = str(resolved_calibration.relative_to(ROOT))
    except ValueError:
        calibration_reference = str(resolved_calibration)
    return {
        "ready_for_cuda": ready,
        "gate_schema_version": int(summary.get("gate_schema_version", 0)),
        "gate_level": gate_level,
        "evaluation_count": evaluations,
        "calibration": calibration_reference,
        "calibration_sha256": sha256_file(calibration),
        "calibration_clip_rate": float(summary.get("calibration_clip_rate", 0.0)),
        "calibration_fallback_rate": float(
            summary.get("calibration_fallback_rate", 0.0)
        ),
        "summary": summary,
        "diagnostic": str(diagnostic.resolve()),
    }


def _run(command: Sequence[str], *, dry_run: bool) -> dict[str, Any]:
    print(subprocess.list2cmdline(command), flush=True)
    if dry_run:
        return {"summary": {}, "results": []}
    env = os.environ | {"PYTHONPATH": str(ROOT / "src"), "MPLBACKEND": "Agg"}
    subprocess.run(command, cwd=ROOT, env=env, check=True)
    output = Path(command[command.index("--output") + 1])
    return json.loads(output.read_text(encoding="utf-8"))


def _pressure_rank(report: dict[str, Any]) -> tuple[float, ...]:
    rows = report["results"]
    width_error = np.mean(
        [abs(np.log(max(float(row["width_ratio_median"]), 1e-9))) for row in rows]
    )
    return (
        float(sum(bool(row["is_success"]) for row in rows)),
        -float(np.mean([row["pressure_error_median_abs"] for row in rows])),
        -float(np.mean([row["pressure_error_p90_abs"] for row in rows])),
        -float(width_error),
        -float(sum(row["lost_holes"] for row in rows)),
        float(np.mean([row["beauty_score"] for row in rows])),
    )


def _angle_rank(report: dict[str, Any]) -> tuple[float, ...]:
    rows = report["results"]
    endpoint_count = sum(int(row["endpoint_triangle_count"]) for row in rows)
    endpoint = (
        sum(
            float(row["endpoint_triangle_mean"])
            * int(row["endpoint_triangle_count"])
            for row in rows
        )
        / endpoint_count
        if endpoint_count
        else 0.0
    )
    unexpected = sum(
        len(row["collision_types"]) + int(row["merged_pairs"])
        for row in rows
    )
    return (
        float(sum(bool(row["is_success"]) for row in rows)),
        -float(unexpected),
        endpoint,
        float(np.mean([row["beauty_score"] for row in rows])),
    )


def _contact_sheet(images: Path, destination: Path) -> None:
    paths = sorted(images.glob("*.png"))
    if not paths:
        return
    cell_width, cell_height = 180, 260
    columns = 6
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(paths):
        with Image.open(path) as source:
            image = source.convert("RGB")
            image.thumbnail((cell_width - 12, cell_height - 28))
        x = (index % columns) * cell_width + (cell_width - image.width) // 2
        y = (index // columns) * cell_height + 20
        sheet.paste(image, (x, y))
        draw.text((index % columns * cell_width + 5, index // columns * cell_height + 4), path.stem, fill="black")
    sheet.save(destination)


def _comparison(old_images: Path, new_images: Path, destination: Path) -> None:
    old = sorted(old_images.glob("*.png"))
    new = sorted(new_images.glob("*.png"))
    if not old or len(old) != len(new):
        return
    pairs: list[Image.Image] = []
    for old_path, new_path in zip(old, new, strict=True):
        with Image.open(old_path) as first, Image.open(new_path) as second:
            left = first.convert("RGB")
            right = second.convert("RGB")
            left.thumbnail((210, 297))
            right.thumbnail((210, 297))
            pair = Image.new("RGB", (420, 317), "white")
            pair.paste(left, (0, 20))
            pair.paste(right, (210, 20))
            ImageDraw.Draw(pair).text((4, 3), f"60mm | A4 85/110mm  {new_path.stem}", fill="black")
            pairs.append(pair)
    sheet = Image.new("RGB", (840, ((len(pairs) + 1) // 2) * 317), "white")
    for index, pair in enumerate(pairs):
        sheet.paste(pair, ((index % 2) * 420, (index // 2) * 317))
    sheet.save(destination)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pressure-calibration", type=Path, required=True)
    parser.add_argument("--gate-level", type=int, choices=(1, 2), default=2)
    parser.add_argument(
        "--threshold-profile",
        choices=tuple(GATE_THRESHOLD_PROFILES),
        default="strict",
    )
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.exists() and not args.dry_run:
        raise SystemExit(f"refusing to overwrite calibration output: {output}")
    output.mkdir(parents=True, exist_ok=args.dry_run)
    pressure_calibration = args.pressure_calibration.resolve()
    if not args.dry_run and not pressure_calibration.is_file():
        raise SystemExit(f"pressure calibration does not exist: {pressure_calibration}")

    def command(path: Path, **options: Any) -> list[str]:
        return _command(
            path,
            gate_level=args.gate_level,
            pressure_calibration=pressure_calibration,
            threshold_profile=args.threshold_profile,
            **options,
        )

    baseline_path = output / "upright.json"
    _run(command(baseline_path, upright=True), dry_run=args.dry_run)

    initial_path = output / "pressure-g0.014-l0.0035.json"
    initial = _run(command(initial_path), dry_run=args.dry_run)
    pressure_candidates: list[tuple[float, float, Path, dict[str, Any]]] = [
        (DEFAULT_PRESSURE_GAIN, 0.0035, initial_path, initial)
    ]
    if args.dry_run:
        for gain in (0.010, 0.014, 0.018):
            for limit in (0.0025, 0.0035, 0.0045):
                _run(
                    command(
                        output / f"pressure-g{gain:.3f}-l{limit:.4f}.json",
                        gain=gain,
                        limit=limit,
                    ),
                    dry_run=True,
                )
        for angle in (25.0, 30.0, 35.0):
            _run(
                command(output / f"angle-{int(angle)}.json", angle=angle),
                dry_run=True,
            )
        _run(
            command(
                output / "selected-diagnostic.json",
                baseline=baseline_path,
                images=output / "images-a4",
            ),
            dry_run=True,
        )
        _run(
            command(
                output / "legacy-60mm.json",
                images=output / "images-60mm",
                legacy_sixty_mm=True,
            ),
            dry_run=True,
        )
        return 0
    if not args.dry_run and not initial["summary"]["gates"]["pressure_tracking"]:
        for gain in (0.010, 0.014, 0.018):
            for limit in (0.0025, 0.0035, 0.0045):
                path = output / f"pressure-g{gain:.3f}-l{limit:.4f}.json"
                report = _run(
                    command(path, gain=gain, limit=limit), dry_run=args.dry_run
                )
                pressure_candidates.append((gain, limit, path, report))
    gain, limit, _, _ = max(
        pressure_candidates, key=lambda candidate: _pressure_rank(candidate[3])
    )

    # The initial report is already the 30 degree candidate.
    angle_candidates: list[tuple[float, Path, dict[str, Any]]] = [
        (30.0, initial_path, initial)
    ]
    for angle in (25.0, 35.0):
        path = output / f"angle-{int(angle)}.json"
        report = _run(
            command(path, gain=gain, limit=limit, angle=angle), dry_run=False
        )
        angle_candidates.append((angle, path, report))
    angle, _, _ = max(angle_candidates, key=lambda candidate: _angle_rank(candidate[2]))

    images = output / "images-a4"
    final_path = output / "selected-diagnostic.json"
    final = _run(
        command(
            final_path,
            gain=gain,
            limit=limit,
            angle=angle,
            baseline=baseline_path,
            images=images,
        ),
        dry_run=False,
    )
    old_images = output / "images-60mm"
    _run(
        command(
            output / "legacy-60mm.json",
            gain=gain,
            limit=limit,
            angle=angle,
            images=old_images,
            legacy_sixty_mm=True,
        ),
        dry_run=False,
    )
    _contact_sheet(images, output / "representative-contact-sheet.png")
    _comparison(old_images, images, output / "old-60mm-vs-a4.png")
    selected = build_selection(
        summary=final["summary"],
        calibration=pressure_calibration,
        diagnostic=final_path,
    ) | {
        "pressure_gain": gain,
        "pressure_limit": limit,
        "entry_angle_deg": angle,
        "contact_sheet": str(output / "representative-contact-sheet.png"),
        "comparison": str(output / "old-60mm-vs-a4.png"),
    }
    (output / "selected.json").write_text(
        json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(output / "selected.json")
    return 0 if selected["ready_for_cuda"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
