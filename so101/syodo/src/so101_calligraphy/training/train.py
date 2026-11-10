"""Train PPO on primitives, arbitrary SVG, or real KanjiVG data."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.trajectory.kanjivg import (
    KANJIVG_REVISION,
    kanjivg_curriculum,
    load_kanjivg_character,
    load_kanjivg_stage,
)
from so101_calligraphy.trajectory.types import Trajectory


CURRICULUM = ("line", "circle", "cross")


def _env_factory(
    *,
    task: str,
    svg_path: str | None,
    trajectory: Trajectory | None,
    monitor_path: Path,
) -> Callable[[], Monitor]:
    def create() -> Monitor:
        monitor_path.parent.mkdir(parents=True, exist_ok=True)
        env = CalligraphyEnv(task=task, svg_path=svg_path, trajectory=trajectory)
        return Monitor(
            env,
            filename=str(monitor_path),
            info_keywords=("is_success", "progress", "beauty_score"),
        )

    return create


def _plot_rewards(stage_dir: Path, monitor_dir: Path) -> None:
    episode_lengths: list[int] = []
    episode_rewards: list[float] = []
    for monitor_file in sorted(monitor_dir.glob("*.monitor.csv")):
        with monitor_file.open(encoding="utf-8") as handle:
            next(handle, None)  # Stable-Baselines3 metadata header.
            for row in csv.DictReader(handle):
                episode_lengths.append(int(row["l"]))
                episode_rewards.append(float(row["r"]))
    rewards = np.asarray(episode_rewards, dtype=np.float64)
    x = np.cumsum(np.asarray(episode_lengths, dtype=np.int64))
    if len(rewards) == 0:
        return
    window = min(20, len(rewards))
    if window > 1:
        kernel = np.ones(window, dtype=np.float64) / window
        smooth = np.convolve(rewards, kernel, mode="valid")
        smooth_x = x[window - 1 :]
    else:
        smooth, smooth_x = rewards, x
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(x, rewards, color="#94a3b8", alpha=0.45, linewidth=1, label="episode")
    axis.plot(smooth_x, smooth, color="#2563eb", linewidth=2, label=f"mean ({window})")
    axis.set(title="PPO episode reward", xlabel="timesteps", ylabel="reward")
    axis.grid(alpha=0.2)
    axis.legend()
    figure.tight_layout()
    figure.savefig(stage_dir / "reward_curve.png", dpi=160)
    plt.close(figure)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--curriculum",
        choices=("all", *CURRICULUM),
        help="all transfers the policy through line -> circle -> cross.",
    )
    source.add_argument("--svg", help="Train one stage from an arbitrary SVG file.")
    source.add_argument(
        "--kanjivg-curriculum",
        choices=("techniques", "radicals", "foundations"),
        help="Train real KanjiVG stroke techniques, radicals, or both.",
    )
    source.add_argument("--kanji", help="Train one complete character from KanjiVG.")
    parser.add_argument(
        "--kanjivg-cache", type=Path, default=Path("data/kanjivg")
    )
    parser.add_argument("--timesteps", type=int, default=200_000, help="PPO steps per stage.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", type=Path, help="Run directory (default: timestamped runs/ path).")
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--n-steps", type=int, default=2048)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--eval-freq", type=int, default=10_000)
    parser.add_argument("--checkpoint-freq", type=int, default=25_000)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.timesteps <= 0:
        raise SystemExit("--timesteps must be positive")
    if args.batch_size <= 0 or args.n_steps <= 0:
        raise SystemExit("--batch-size and --n-steps must be positive")
    if args.n_steps % args.batch_size != 0:
        raise SystemExit("--batch-size must divide --n-steps for this single-env trainer")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = (args.output or Path("runs") / timestamp).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    try:
        if args.svg:
            svg_path = str(Path(args.svg).expanduser().resolve())
            stages = [(Path(svg_path).stem, svg_path, None)]
        elif args.kanjivg_curriculum:
            stages = [
                (
                    stage.slug,
                    None,
                    load_kanjivg_stage(stage, cache_dir=args.kanjivg_cache),
                )
                for stage in kanjivg_curriculum(args.kanjivg_curriculum)
            ]
        elif args.kanji:
            trajectory = load_kanjivg_character(
                args.kanji, cache_dir=args.kanjivg_cache
            )
            stages = [(f"kanji-{ord(args.kanji):05x}", None, trajectory)]
        elif args.curriculum in (None, "all"):
            stages = [(task, None, None) for task in CURRICULUM]
        else:
            stages = [(args.curriculum, None, None)]
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    metadata = {
        "created_at": datetime.now().isoformat(),
        "stages": [name for name, _, _ in stages],
        "trajectory_sources": [
            trajectory.source if trajectory else svg_path or f"primitive:{name}"
            for name, svg_path, trajectory in stages
        ],
        "timesteps_per_stage": args.timesteps,
        "seed": args.seed,
        "algorithm": "PPO",
        "device": "cpu",
        "learning_rate": args.learning_rate,
        "n_steps": args.n_steps,
        "batch_size": args.batch_size,
    }
    if args.kanjivg_curriculum or args.kanji:
        metadata["kanjivg_revision"] = KANJIVG_REVISION
    (output / "run.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    model: PPO | None = None
    total_steps = 0
    for stage_number, (task, svg_path, trajectory) in enumerate(stages, start=1):
        stage_dir = output / f"{stage_number:02d}-{task}"
        stage_dir.mkdir(parents=True, exist_ok=True)
        train_env = DummyVecEnv(
            [
                _env_factory(
                    task=task,
                    svg_path=svg_path,
                    trajectory=trajectory,
                    monitor_path=stage_dir / "train_logs" / "train.monitor.csv",
                )
            ]
        )
        eval_env = DummyVecEnv(
            [
                _env_factory(
                    task=task,
                    svg_path=svg_path,
                    trajectory=trajectory,
                    monitor_path=stage_dir / "eval_logs" / "eval.monitor.csv",
                )
            ]
        )

        if model is None:
            model = PPO(
                "MlpPolicy",
                train_env,
                learning_rate=args.learning_rate,
                n_steps=args.n_steps,
                batch_size=args.batch_size,
                gamma=0.995,
                gae_lambda=0.95,
                ent_coef=0.005,
                policy_kwargs={"net_arch": [256, 256]},
                seed=args.seed,
                device="cpu",
                verbose=1,
                tensorboard_log=None,
            )
        else:
            model.set_env(train_env)

        checkpoint_callback = CheckpointCallback(
            save_freq=max(1, args.checkpoint_freq),
            save_path=str(stage_dir / "checkpoints"),
            name_prefix=task,
        )
        eval_callback = EvalCallback(
            eval_env,
            best_model_save_path=str(stage_dir / "best"),
            log_path=str(stage_dir / "evaluation"),
            eval_freq=max(1, args.eval_freq),
            n_eval_episodes=3,
            deterministic=True,
            render=False,
        )
        print(f"\n=== Stage {stage_number}/{len(stages)}: {task} ===")
        steps_before_stage = model.num_timesteps
        model.learn(
            total_timesteps=args.timesteps,
            callback=[checkpoint_callback, eval_callback],
            reset_num_timesteps=(stage_number == 1),
            progress_bar=False,
        )
        actual_stage_steps = model.num_timesteps - steps_before_stage
        total_steps = model.num_timesteps
        model_path = stage_dir / "final_model"
        model.save(model_path)
        mean_reward, std_reward = evaluate_policy(
            model, eval_env, n_eval_episodes=5, deterministic=True, warn=False
        )
        results = {
            "stage": task,
            "requested_stage_timesteps": args.timesteps,
            "actual_stage_timesteps": actual_stage_steps,
            "cumulative_timesteps": total_steps,
            "mean_reward": float(mean_reward),
            "std_reward": float(std_reward),
            "model": str(model_path.with_suffix(".zip")),
        }
        (stage_dir / "summary.json").write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )
        train_env.close()
        eval_env.close()
        _plot_rewards(stage_dir, stage_dir / "train_logs")

    assert model is not None
    final_path = output / "final_model"
    model.save(final_path)
    print(f"\nTraining complete: {final_path.with_suffix('.zip')}")
    print(f"Reward logs and plots: {output}")


if __name__ == "__main__":
    main()
