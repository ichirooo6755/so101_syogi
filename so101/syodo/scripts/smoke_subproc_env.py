"""Smoke-test SubprocVecEnv and parallel BC (must be a real module for spawn)."""

from __future__ import annotations

from pathlib import Path

from so101_calligraphy.training.professional import (
    IndexedTrajectories,
    _collect_demonstrations,
    _env_factory,
    _make_vec_env,
)
from so101_calligraphy.trajectory.education import lazy_joyo_trajectories, load_joyo_kanji


def main() -> None:
    entries = load_joyo_kanji(Path("data/kanjidic2"))
    dataset = lazy_joyo_trajectories(
        entries[:8],
        kanjivg_cache=Path("data/kanjivg"),
        animcjk_cache=Path("data/animcjk"),
        use_animcjk_medians=True,
    )
    trajectories = IndexedTrajectories(dataset, range(min(4, len(dataset))))
    _ = [trajectories[index] for index in range(len(trajectories))]
    output = Path("runs/_subproc_smoke")
    output.mkdir(parents=True, exist_ok=True)
    env = _make_vec_env(
        [
            _env_factory(
                trajectories,
                output / f"t-{index}.monitor.csv",
                ablation="all",
                motoya_font_path=None,
            )
            for index in range(4)
        ],
        4,
    )
    try:
        env.reset()
        env.step([[0.0] * 6] * 4)
        print("subproc ok", type(env).__name__)
    finally:
        env.close()
    observations, actions = _collect_demonstrations(
        trajectories,
        200,
        ablation="all",
        seed=1,
        motoya_font_path=None,
        workers=4,
    )
    print("bc parallel", observations.shape, actions.shape)


if __name__ == "__main__":
    main()
