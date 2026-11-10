#!/usr/bin/env python3
"""Rescore representative glyphs under legacy vs current beauty weights."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import PPO

from so101_calligraphy.metrics import (
    BEAUTY_COMPONENT_WEIGHTS,
    LEGACY_BEAUTY_COMPONENT_WEIGHTS,
    aggregate_beauty_components,
)
from so101_calligraphy.training.professional import COMPONENTS, evaluate
from so101_calligraphy.trajectory.education import load_joyo_kanji, load_joyo_trajectories


DEFAULT_CHARACTERS = ("一", "十", "書", "水", "永", "竜", "道", "飛", "乙")


def _rescore(row: dict[str, str], weights: dict[str, float]) -> float:
    components = {
        name: float(row[name]) / 100.0 for name in COMPONENTS if name in row
    }
    score, _ = aggregate_beauty_components(components, weights=weights)
    return score


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--characters",
        nargs="+",
        default=list(DEFAULT_CHARACTERS),
    )
    parser.add_argument("--device", default="mps")
    args = parser.parse_args()

    model_path = args.model.expanduser().resolve()
    if not model_path.is_file() and model_path.with_suffix(".zip").is_file():
        model_path = model_path.with_suffix(".zip")
    model = PPO.load(str(model_path), device=args.device)

    entries = load_joyo_kanji()
    by_char = {entry.character: index for index, entry in enumerate(entries)}
    missing = [character for character in args.characters if character not in by_char]
    if missing:
        raise SystemExit(f"Unknown characters: {', '.join(missing)}")
    indices = [by_char[character] for character in args.characters]
    dataset = load_joyo_trajectories(entries)
    work = args.output.parent / "weight-compare-work"
    result = evaluate(
        model,
        entries,
        dataset,
        indices,
        work,
        ablation="all",
        save_characters=tuple(args.characters),
    )

    rows: list[dict[str, str]] = []
    with (work / "characters.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    figure, axes = plt.subplots(
        len(args.characters), 1, figsize=(4.2, 2.4 * len(args.characters)), constrained_layout=True
    )
    if len(args.characters) == 1:
        axes = [axes]
    summary_lines: list[str] = []
    for axis, row in zip(axes, rows, strict=True):
        character = row["character"]
        ink_path = work / "ink" / f"{ord(character):05x}-{character}.png"
        image = plt.imread(ink_path)
        axis.imshow(image)
        legacy = _rescore(row, LEGACY_BEAUTY_COMPONENT_WEIGHTS)
        current = _rescore(row, BEAUTY_COMPONENT_WEIGHTS)
        brushwork = float(row["brushwork"])
        glyph = float(row.get("glyph_shape", row.get("glyph_shape", 0.0)))
        iou = float(row.get("exemplar_mask_iou", 0.0))
        axis.set_title(
            f"{character} bw={brushwork:.0f} shape={glyph:.0f} "
            f"beauty {legacy:.0f}->{current:.0f} iou={iou:.0f}"
        )
        axis.axis("off")
        summary_lines.append(
            f"{character}: brushwork={brushwork:.1f} glyph_shape={glyph:.1f} "
            f"legacy_beauty={legacy:.1f} new_beauty={current:.1f} iou={iou:.1f}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180)
    plt.close(figure)

    summary_path = args.output.with_suffix(".txt")
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"wrote {summary_path}")
    print(f"evaluation mean beauty (env): {result['mean_beauty_score']:.2f}")


if __name__ == "__main__":
    main()
