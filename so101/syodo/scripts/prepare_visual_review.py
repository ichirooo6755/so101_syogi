#!/usr/bin/env python3
"""Prepare a reproducible C-to-A review from an existing full PPO evaluation.

This never reruns, modifies or approves a policy. PNGs are the original PPO
evaluation outputs; the comparison panels retain their exemplar/trajectory labels.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_joyo_shards import (
    build_calligrapher_acceptance, load_expected_joyo, merge_shards,
)
from scripts.render_ppo_contact_sheet import (
    ContactSheetError, load_character_rows, render_contact_sheet, resolve_images, select_rows,
)

REPRESENTATIVES = tuple("一十永水小語教鬱")
VISUAL_METRICS = ("glyph_shape", "exemplar_mask_iou")


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def review_rows(rows: list[dict[str, str]], *, seed: int, weakest: int) -> list[dict[str, str]]:
    """Fixed representatives, two seeded examples per grade, both visual tails."""
    if weakest < 1:
        raise ContactSheetError("weakest must be positive")
    selected = select_rows(
        rows, representatives=REPRESENTATIVES, grade_per_stratum=0,
        beauty_quantiles=(), weakest_count=weakest, weakest_metrics=VISUAL_METRICS,
    )
    strata = defaultdict(list)
    for row in rows:
        strata[row["grade"]].append(row)
    rng = random.Random(seed)
    for grade in sorted(strata):
        group = sorted(strata[grade], key=lambda row: row["character"])
        selected.extend(rng.sample(group, min(2, len(group))))
    return list({row["character"]: row for row in selected}.values())


def prepare_review(
    evaluation_dir: Path, output: Path, *, expected: tuple[str, ...],
    model: Path, seed: int = 17, weakest: int = 6,
) -> dict:
    if output.exists():
        raise ContactSheetError(f"Output already exists; choose a new directory: {output}")
    rows = load_character_rows(evaluation_dir / "characters.csv")
    summary = json.loads((evaluation_dir / "summary.json").read_text(encoding="utf-8"))
    if summary.get("all_joyo_evaluated") is not True:
        raise ContactSheetError("A review requires an all-joyo evaluation")
    if not isinstance(summary.get("model"), str) or not summary["model"].strip():
        raise ContactSheetError("PPO model provenance is missing")
    if summary.get("evaluation", {}).get("ablation") != "all":
        raise ContactSheetError("A review requires the full all-modules evaluation")
    if not summary.get("acceptance") or not all(value is True for value in summary["acceptance"].values()):
        raise ContactSheetError("Stored C acceptance has not passed")
    for row in rows:
        for metric in (*VISUAL_METRICS, "progress"):
            try:
                value = float(row[metric])
            except (KeyError, TypeError, ValueError) as exc:
                raise ContactSheetError(f"{row['character']}: missing/invalid {metric}") from exc
            maximum = 1.0 if metric == "progress" else 100.0
            if not math.isfinite(value) or not 0 <= value <= maximum:
                raise ContactSheetError(f"{row['character']}: invalid {metric}")
        if row["progress"] and float(row["progress"]) != 1.0:
            raise ContactSheetError(f"Incomplete character: {row['character']}")
        if str(row.get("hard_limit", "")).lower() not in ("0", "false"):
            raise ContactSheetError(f"Hard-limit result missing or failed: {row['character']}")
    # Recompute C from the exact corpus rows; a stale all-true summary is not
    # sufficient. The existing merger also rejects duplicated/missing layouts.
    _, evaluation = merge_shards([rows], [summary], expected, layouts=(0,))
    if "finish" not in evaluation.get("technique_means", {}).get("harai", {}):
        raise ContactSheetError("Full joyo review requires harai.finish evidence")
    acceptance = build_calligrapher_acceptance(evaluation, rows)
    if not all(acceptance.values()):
        raise ContactSheetError(f"Recomputed C acceptance failed: {[k for k, v in acceptance.items() if not v]}")
    # This CLI takes a model explicitly so historical absolute paths can move.
    # Its current hash identifies the supplied artifact, not an unrecorded
    # historical training-time hash.
    model_hash = sha256(model)
    recorded_hash = summary.get("model_sha256")
    if recorded_hash is not None and recorded_hash != model_hash:
        raise ContactSheetError("Model SHA-256 does not match the evaluation")
    selected = review_rows(rows, seed=seed, weakest=weakest)
    inks = resolve_images(selected, evaluation_dir, "ink")
    comparisons = resolve_images(selected, evaluation_dir, "comparisons")
    ranked = sorted(rows, key=lambda row: (float(row["glyph_shape"]), float(row["exemplar_mask_iou"]), row["character"]))
    manifest = {
        "schema": 1, "issue": 17, "visual_acceptance": "pending_human_review",
        "source": "existing_ppo_evaluation", "evaluation_dir": str(evaluation_dir.resolve()),
        "model": str(model.resolve()), "model_sha256_at_review": model_hash,
        "historical_model_hash_verified": recorded_hash == model_hash,
        "characters_csv_sha256": sha256(evaluation_dir / "characters.csv"),
        "summary_json_sha256": sha256(evaluation_dir / "summary.json"),
        "count": len(rows), "seed": seed, "weakest_per_metric": weakest,
        "acceptance": acceptance, "evaluation": evaluation,
        "visual_metrics": {
            metric: {
                "mean": sum(float(row[metric]) for row in rows) / len(rows),
                "minimum": min(float(row[metric]) for row in rows),
                "below_50": sum(float(row[metric]) < 50 for row in rows),
            } for metric in VISUAL_METRICS
        },
        "selected": [
            {
                "character": row["character"], "grade": row["grade"],
                "glyph_shape": float(row["glyph_shape"]), "exemplar_mask_iou": float(row["exemplar_mask_iou"]),
                "ink_path": str(ink.relative_to(evaluation_dir)), "ink_sha256": sha256(ink),
                "comparison_path": str(comparison.relative_to(evaluation_dir)),
                "comparison_sha256": sha256(comparison),
            } for (row, ink), (_, comparison) in zip(inks, comparisons)
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    with (output / "ranked-characters.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(ranked)
    render_contact_sheet(inks, output / "ink-contact-sheet.png", columns=4, cell_width=400, cell_height=430)
    render_contact_sheet(comparisons, output / "comparison-contact-sheet.png", columns=3, cell_width=760, cell_height=390)
    (output / "review.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    worst_lines = "\n".join(
        f"| {r['character']} | {float(r['glyph_shape']):.2f} | {float(r['exemplar_mask_iou']):.2f} |"
        for r in ranked[:12]
    )
    identity_note = (
        "The supplied model matches the SHA-256 recorded by the evaluation.\n\n"
        if recorded_hash else
        "The model hash was measured when this review was built. The historical evaluation "
        "did not record a model hash, so identity with its training-time file is unverified.\n\n"
    )
    (output / "review.md").write_text(
        f"# Issue #17: PPO visual review\n\n"
        f"Existing evaluation: **{len(rows)} characters**, recomputed C gates passed. "
        f"**A: pending human review.** No new training or evaluation was run.\n\n"
        f"Glyph mean: {manifest['visual_metrics']['glyph_shape']['mean']:.4f}; "
        f"exemplar IoU mean: {manifest['visual_metrics']['exemplar_mask_iou']['mean']:.4f}.\n\n"
        f"[PPO ink](ink-contact-sheet.png) · [Original comparisons](comparison-contact-sheet.png) · "
        f"[All characters, ranked](ranked-characters.csv) · [Provenance](review.json)\n\n"
        f"Selection: fixed 一十永水小語教鬱, two seeded samples per grade (seed {seed}), "
        f"and the weakest {weakest} characters for each of glyph and IoU. "
        "Selection is made before images are resolved; missing images stop generation.\n\n"
        "Inspect stroke placement/proportions, enclosed white spaces, and entry/finish shapes. "
        "Record a pass/fail decision with character names and reasons; this bundle does not approve A. "
        "The historical evaluation predates current hardware geometry; it does not certify "
        "the tilt attachment or the physical 80 mm rigid shaft plus 40 mm tuft.\n\n"
        f"{identity_note}"
        "| Character | Glyph | IoU |\n| --- | ---: | ---: |\n" + worst_lines + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evaluation_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--kanjidic2-cache", type=Path, default=Path("data/kanjidic2/kanjidic2.xml.gz"))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--weakest", type=int, default=6)
    args = parser.parse_args(argv)
    try:
        result = prepare_review(
            args.evaluation_dir.resolve(), args.output.resolve(),
            expected=load_expected_joyo(args.kanjidic2_cache), model=args.model,
            seed=args.seed, weakest=args.weakest,
        )
    except (ContactSheetError, OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(f"{args.output}: {result['count']} evaluated, {len(result['selected'])} selected, A pending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
