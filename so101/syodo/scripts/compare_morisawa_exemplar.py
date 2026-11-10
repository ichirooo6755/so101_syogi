#!/usr/bin/env python3
"""Compare glyph_shape ceiling across Aoyagi and Morisawa teacher fonts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import PPO

from so101_calligraphy.metrics import glyph_mask_quality
from so101_calligraphy.trajectory.education import load_joyo_kanji, load_joyo_trajectories
from so101_calligraphy.trajectory.professional import (
    fetch_kouzan_font,
    resolve_exemplar_font,
    verify_licensed_exemplar_font,
)
from so101_calligraphy.training.professional import evaluate


DEFAULT_CHARACTERS = ("一", "十", "書", "水", "永", "竜", "道", "飛", "鬱")
DEFAULT_CANDIDATES = (
    Path.home() / "Library/Fonts/MorisawaFonts/A-OTF-KaishoMCBK1Pro-DeBold.otf",
    Path.home() / "Library/Fonts/MorisawaFonts/A-OTF-RyuminPro-Regular.otf",
    Path.home() / "Library/Fonts/MorisawaFonts/UDReiminSCGb6-Regular.otf",
)


def _mask_iou(ink: np.ndarray, mask: np.ndarray) -> float:
    return 100.0 * float(glyph_mask_quality(ink, mask).get("iou", 0.0))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--characters", nargs="+", default=list(DEFAULT_CHARACTERS))
    parser.add_argument("--device", default="mps")
    args = parser.parse_args()

    model_path = args.model.expanduser().resolve()
    if not model_path.is_file() and model_path.with_suffix(".zip").is_file():
        model_path = model_path.with_suffix(".zip")
    model = PPO.load(str(model_path), device=args.device)

    entries = load_joyo_kanji()
    by_char = {entry.character: index for index, entry in enumerate(entries)}
    indices = [by_char[character] for character in args.characters]
    dataset = load_joyo_trajectories(entries)

    fonts: list[tuple[str, Path]] = [("Aoyagi", fetch_kouzan_font())]
    for candidate in DEFAULT_CANDIDATES:
        if candidate.is_file():
            try:
                fonts.append((candidate.stem, verify_licensed_exemplar_font(candidate)))
            except Exception as exc:
                print(f"skip {candidate.name}: {exc}", flush=True)

    rows: list[dict[str, str | float]] = []
    work_root = args.output.parent / "morisawa-exemplar-work"
    for label, font_path in fonts:
        out = work_root / label
        result = evaluate(
            model,
            entries,
            dataset,
            indices,
            out,
            ablation="all",
            save_characters=tuple(args.characters),
            motoya_font_path=font_path,
        )
        with (out / "characters.csv").open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                rows.append(
                    {
                        "font": label,
                        "character": row["character"],
                        "glyph_shape": float(row["glyph_shape"]),
                        "exemplar_mask_iou": float(row.get("exemplar_mask_iou", 0.0)),
                        "beauty": float(row["beauty_score"]),
                        "brushwork": float(row["brushwork"]),
                    }
                )
        print(
            f"{label}: mean glyph_shape={result['component_means']['glyph_shape']:.1f} "
            f"mean IoU={float(np.mean([float(r['exemplar_mask_iou']) for r in rows if r['font']==label])):.1f}",
            flush=True,
        )

    best = max(
        fonts,
        key=lambda item: float(
            np.mean(
                [
                    float(row["glyph_shape"])
                    for row in rows
                    if row["font"] == item[0]
                ]
            )
        ),
    )
    selected_path = args.output.parent / "selected-exemplar-font.txt"
    selected_path.write_text(f"{best[1]}\n", encoding="utf-8")
    print(f"selected: {best[0]} -> {best[1]}", flush=True)
    print(f"wrote: {selected_path}", flush=True)

    figure, axis = plt.subplots(figsize=(10, 4))
    labels = [label for label, _ in fonts]
    means = [
        float(
            np.mean([float(row["glyph_shape"]) for row in rows if row["font"] == label])
        )
        for label in labels
    ]
    axis.bar(labels, means, color="#2563eb")
    axis.set_ylabel("mean glyph_shape")
    axis.set_title("Teacher font comparison (same PPO trajectory)")
    axis.tick_params(axis="x", rotation=20)
    figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180)
    plt.close(figure)
    print(f"wrote: {args.output}", flush=True)


if __name__ == "__main__":
    main()
