#!/usr/bin/env python3
"""Compare soft vs hard ink stamp on fixed IK trajectories (no PPO)."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from so101_calligraphy.config import EnvConfig, InkConfig
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.training.professional import module_preset
from so101_calligraphy.trajectory.animcjk import enrich_with_animcjk_widths
from so101_calligraphy.trajectory.kanjivg import load_kanjivg_character


DEFAULT_CHARACTERS = ("一", "八", "永", "水")


def _render_character(
    character: str,
    *,
    stamp_edge: str,
    cache_dir: Path,
    seed: int,
) -> np.ndarray:
    trajectory = enrich_with_animcjk_widths(
        load_kanjivg_character(character, cache_dir=cache_dir),
        character,
        cache_dir=cache_dir / "animcjk",
        use_medians=True,
    )
    config = EnvConfig(
        ik_assist=True,
        modules=module_preset("all"),
        ink=replace(InkConfig(), stamp_edge=stamp_edge),
        observation_version=3,
    )
    env = CalligraphyEnv(
        task=f"ink-edge-{stamp_edge}",
        trajectories=(trajectory,),
        config=config,
    )
    try:
        observation, _ = env.reset(seed=seed, options={"trajectory_index": 0})
        while True:
            observation, _, terminated, truncated, _ = env.step(
                np.zeros(6, dtype=np.float32)
            )
            if terminated or truncated:
                break
        return env.ink.rgb_image()
    finally:
        env.close()


def _contact_sheet(
    characters: tuple[str, ...],
    *,
    cache_dir: Path,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    soft_rows: list[np.ndarray] = []
    hard_rows: list[np.ndarray] = []
    for character in characters:
        soft = _render_character(
            character, stamp_edge="soft", cache_dir=cache_dir, seed=seed
        )
        hard = _render_character(
            character, stamp_edge="hard", cache_dir=cache_dir, seed=seed
        )
        soft_rows.append(soft)
        hard_rows.append(hard)
    return np.concatenate(soft_rows, axis=0), np.concatenate(hard_rows, axis=0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--characters",
        nargs="+",
        default=list(DEFAULT_CHARACTERS),
        help="Kanji to render on the same IK baseline.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("data/kanjivg"))
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    characters = tuple(args.characters)
    soft, hard = _contact_sheet(characters, cache_dir=args.cache, seed=args.seed)
    height = soft.shape[0] // len(characters)
    width = soft.shape[1]

    figure, axes = plt.subplots(
        len(characters), 2, figsize=(6.4, 2.2 * len(characters)), constrained_layout=True
    )
    if len(characters) == 1:
        axes = np.asarray([axes])
    for row, character in enumerate(characters):
        y0, y1 = row * height, (row + 1) * height
        axes[row, 0].imshow(soft[y0:y1, :width])
        axes[row, 0].set_title(f"{character} soft")
        axes[row, 1].imshow(hard[y0:y1, :width])
        axes[row, 1].set_title(f"{character} hard")
        for column in range(2):
            axes[row, column].axis("off")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180)
    plt.close(figure)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
