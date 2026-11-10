#!/usr/bin/env python3
"""Worker: evaluate a single joyo entry index and write row.json + ink."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from so101_calligraphy.brushwork import resolve_technique
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.metrics import BEAUTY_COMPONENT_WEIGHTS, WIDTH_DETAIL_KEYS
from so101_calligraphy.training.professional import professional_config, _pyplot, _save_comparison
from so101_calligraphy.trajectory.education import lazy_joyo_trajectories, load_joyo_kanji

COMPONENTS = tuple(BEAUTY_COMPONENT_WEIGHTS)
WIDTH_COMPONENTS = (*WIDTH_DETAIL_KEYS, "stroke_width_hierarchy")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--entry-index", type=int, required=True)
    parser.add_argument("--dwell", type=int, default=120)
    parser.add_argument("--seed", type=int, default=141)
    parser.add_argument("--exemplar-font", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    entries = load_joyo_kanji(Path("data"))
    entry = entries[args.entry_index]
    cfg = replace(
        professional_config("all", motoya_font_path=args.exemplar_font),
        max_pen_down_dwell=args.dwell,
    )
    dataset = lazy_joyo_trajectories(entries, spacing=cfg.path_spacing)
    traj = dataset[args.entry_index]
    env = CalligraphyEnv(task=f"one-{entry.character}", trajectories=[traj], config=cfg)
    model = PPO.load(str(args.model), device=args.device)
    observation, _ = env.reset(seed=args.seed + args.entry_index)
    info: dict = {}
    steps = 0
    while True:
        steps += 1
        action, _ = model.predict(observation, deterministic=True)
        observation, _, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
        if steps > 50_000:
            break

    row: dict = {
        "character": entry.character,
        "grade": entry.grade,
        "stroke_count": entry.stroke_count,
        "success": int(bool(info.get("is_success", False))),
        "progress": float(info.get("progress", 0.0)),
        "steps": steps,
        "beauty_score": float(info.get("beauty_score", 0.0)),
        "drip_count": int(info.get("drip_count", 0)),
        "collision": ";".join(info.get("collision_types", ()) or ()),
        "hard_limit": int(bool(info.get("hard_limit", False))),
        "termination_reason": str(info.get("termination_reason", "")),
        "unintended_ink_fraction": float(info.get("unintended_ink_fraction", 0.0)),
    }
    components = info.get("beauty_components", {})
    row.update({name: float(components.get(name, 0.0)) for name in COMPONENTS})
    glyph_metrics = info.get("glyph_metrics", {})
    if isinstance(glyph_metrics, dict):
        row["exemplar_mask_iou"] = 100.0 * float(glyph_metrics.get("iou", 0.0))
    width_details = info.get("width_details", {})
    if isinstance(width_details, dict):
        row.update({name: float(width_details.get(name, 0.0)) for name in WIDTH_COMPONENTS})

    harai_f, harai_w, tome_f = [], [], []
    for stroke_index, metrics in env._stroke_scores.items():
        technique = resolve_technique(env.trajectory.strokes[stroke_index])
        if technique == "harai":
            harai_f.append(100.0 * metrics["finish"])
            harai_w.append(100.0 * metrics["width"])
        elif technique == "tome":
            tome_f.append(100.0 * metrics["finish"])
    if harai_f:
        row["harai_finish"] = float(np.mean(harai_f))
        row["harai_width"] = float(np.mean(harai_w))
    if tome_f:
        row["tome_finish"] = float(np.mean(tome_f))

    ink_dir = args.output / "ink"
    ink_dir.mkdir(exist_ok=True)
    ink_path = ink_dir / f"{ord(entry.character):05x}-{entry.character}.png"
    _pyplot().imsave(ink_path, env.ink.rgb_image())
    _save_comparison(
        args.output / "comparisons" / f"{ord(entry.character):05x}-{entry.character}.png",
        entry.character,
        env.ink.rgb_image(),
        env._professional_mask,
    )
    (args.output / "row.json").write_text(
        json.dumps(row, ensure_ascii=False), encoding="utf-8"
    )
    env.close()
    print(f"ok {entry.character} beauty={row['beauty_score']:.2f}", flush=True)


if __name__ == "__main__":
    main()
