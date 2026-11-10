"""Train and exhaustively evaluate one PPO policy on all education kanji."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
import torch
from torch.nn import functional as F

from so101_calligraphy.config import EnvConfig
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.training.train import _plot_rewards
from so101_calligraphy.trajectory.education import (
    EducationKanji,
    EXPECTED_GRADE_COUNTS,
    KANJIDIC2_URL,
    load_education_kanji,
    load_education_trajectories,
)
from so101_calligraphy.trajectory.kanjivg import (
    KANJIVG_ARCHIVE_URL,
    KANJIVG_REVISION,
)
from so101_calligraphy.trajectory.animcjk import ANIMCJK_REVISION
from so101_calligraphy.trajectory.types import Trajectory


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--initial-model", type=Path)
    parser.add_argument(
        "--start-stage",
        type=int,
        default=1,
        help="Start at curriculum stage 1-7 when resuming from --initial-model.",
    )
    parser.add_argument("--kanjidic-cache", type=Path, default=Path("data/kanjidic2"))
    parser.add_argument("--kanjivg-cache", type=Path, default=Path("data/kanjivg"))
    parser.add_argument("--animcjk-cache", type=Path, default=Path("data/animcjk"))
    parser.add_argument(
        "--no-animcjk",
        action="store_true",
        help="Train without AnimCJK Japanese outline-derived widths.",
    )
    parser.add_argument(
        "--refresh-data",
        action="store_true",
        help="Refresh the current KANJIDIC2 metadata before training.",
    )
    parser.add_argument("--timesteps-per-round", type=int, default=250_000)
    parser.add_argument("--bc-steps", type=int, default=20_000)
    parser.add_argument("--bc-epochs", type=int, default=4)
    parser.add_argument("--n-envs", type=int, default=4)
    parser.add_argument("--n-steps", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--stage-eval-size", type=int, default=32)
    parser.add_argument("--stage-target", type=float, default=0.75)
    parser.add_argument("--target-success", type=float, default=0.80)
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=0,
        help="Rounds per stage; 0 keeps learning until the threshold is reached.",
    )
    parser.add_argument("--checkpoint-freq", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def _validate_args(args: argparse.Namespace) -> None:
    positive = (
        "timesteps_per_round",
        "bc_steps",
        "bc_epochs",
        "n_envs",
        "n_steps",
        "batch_size",
        "stage_eval_size",
        "checkpoint_freq",
    )
    if any(getattr(args, name) <= 0 for name in positive):
        raise SystemExit("Training sizes and frequencies must be positive.")
    if args.max_rounds < 0:
        raise SystemExit("--max-rounds must be non-negative.")
    if not 1 <= args.start_stage <= 7:
        raise SystemExit("--start-stage must be in 1..7.")
    if args.start_stage > 1 and not args.initial_model:
        raise SystemExit("--start-stage greater than 1 requires --initial-model.")
    if (args.n_steps * args.n_envs) % args.batch_size:
        raise SystemExit("--batch-size must divide --n-steps * --n-envs.")
    if not 0 < args.stage_target <= args.target_success <= 1:
        raise SystemExit("Require 0 < stage-target <= target-success <= 1.")
    if args.initial_model and not args.initial_model.expanduser().exists():
        raise SystemExit(f"Initial model does not exist: {args.initial_model}")


def _env_factory(
    trajectories: Sequence[Trajectory], monitor_path: Path
) -> Callable[[], Monitor]:
    def create() -> Monitor:
        monitor_path.parent.mkdir(parents=True, exist_ok=True)
        return Monitor(
            CalligraphyEnv(
                task="education-kanji",
                trajectories=trajectories,
                config=EnvConfig(ik_assist=True),
            ),
            filename=str(monitor_path),
            info_keywords=("is_success", "progress", "beauty_score"),
        )

    return create


def _vec_env(
    trajectories: Sequence[Trajectory], n_envs: int, log_dir: Path, seed: int
) -> DummyVecEnv:
    env = DummyVecEnv(
        [
            _env_factory(trajectories, log_dir / f"train-{index}.monitor.csv")
            for index in range(n_envs)
        ]
    )
    env.seed(seed)
    return env


def _collect_demonstrations(
    trajectories: Sequence[Trajectory], total_steps: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    env = CalligraphyEnv(
        task="education-kanji",
        trajectories=trajectories,
        config=EnvConfig(ik_assist=True),
    )
    rng = np.random.default_rng(seed)
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    try:
        while len(observations) < total_steps:
            trajectory_index = int(rng.integers(len(trajectories)))
            env._select_trajectory(trajectory_index)
            target_index = int(rng.integers(len(env.waypoints)))
            observation, _ = env.reset(
                options={
                    "trajectory_index": trajectory_index,
                    "target_index": target_index,
                }
            )
            for _ in range(32):
                action = np.zeros(env.action_space.shape, dtype=np.float32)
                observations.append(observation)
                actions.append(action)
                observation, _, terminated, truncated, _ = env.step(action)
                if len(observations) >= total_steps or terminated or truncated:
                    break
    finally:
        env.close()
    return np.asarray(observations, dtype=np.float32), np.asarray(actions, dtype=np.float32)


def _behavior_clone(
    model: PPO,
    observations: np.ndarray,
    actions: np.ndarray,
    *,
    epochs: int,
    batch_size: int,
    seed: int,
) -> float:
    rng = np.random.default_rng(seed)
    policy = model.policy
    policy.set_training_mode(True)
    losses: list[float] = []
    for _ in range(epochs):
        for start in range(0, len(observations), batch_size):
            indices = rng.integers(
                len(observations),
                size=min(batch_size, len(observations) - start),
            )
            obs = torch.as_tensor(observations[indices], device=policy.device)
            expected = torch.as_tensor(actions[indices], device=policy.device)
            predicted = policy.get_distribution(obs).distribution.mean
            loss = F.mse_loss(predicted, expected)
            policy.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy.parameters(), 0.5)
            policy.optimizer.step()
            losses.append(float(loss.detach().cpu()))
    policy.set_training_mode(False)
    return float(np.mean(losses[-max(1, len(observations) // batch_size) :]))


def _sample_indices(count: int, sample_size: int) -> tuple[int, ...]:
    if sample_size >= count:
        return tuple(range(count))
    return tuple(np.linspace(0, count - 1, sample_size).round().astype(int))


def _evaluate(
    model: PPO,
    entries: Sequence[EducationKanji],
    trajectories: Sequence[Trajectory],
    output: Path,
    indices: Sequence[int] | None = None,
    *,
    seed: int = 7,
) -> tuple[float, tuple[int, ...]]:
    selected = tuple(indices) if indices is not None else tuple(range(len(entries)))
    env = CalligraphyEnv(
        task="education-kanji",
        trajectories=trajectories,
        config=EnvConfig(ik_assist=True),
    )
    failures: list[int] = []
    rows: list[dict[str, object]] = []
    try:
        for number, index in enumerate(selected, start=1):
            entry = entries[index]
            observation, _ = env.reset(
                seed=seed + index,
                options={"trajectory_index": index},
            )
            info: dict[str, object] = {}
            steps = 0
            while True:
                steps += 1
                action, _ = model.predict(observation, deterministic=True)
                observation, _, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    break
            success = bool(info["is_success"])
            if not success:
                failures.append(index)
            rows.append(
                {
                    "character": entry.character,
                    "grade": entry.grade,
                    "stroke_count": entry.stroke_count,
                    "success": int(success),
                    "progress": float(info["progress"]),
                    "steps": steps,
                    "collision": ";".join(info["collision_types"]),
                }
            )
            if number % 50 == 0 or number == len(selected):
                print(
                    f"evaluation {number}/{len(selected)} "
                    f"success={number - len(failures)}",
                    flush=True,
                )
    finally:
        env.close()

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return 1.0 - len(failures) / len(selected), tuple(failures)


def _stage_pools(
    entries: Sequence[EducationKanji],
) -> tuple[tuple[str, tuple[int, ...]], ...]:
    low = tuple(
        index for index, entry in enumerate(entries) if entry.grade == 1 and entry.stroke_count <= 4
    )
    grades = tuple(
        (
            f"grade-{grade}",
            tuple(index for index, entry in enumerate(entries) if entry.grade <= grade),
        )
        for grade in range(1, 7)
    )
    return (("grade-1-low-stroke", low), *grades)


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main() -> None:
    args = _parse_args()
    _validate_args(args)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = (args.output or Path("runs") / f"education-kanji-{timestamp}").expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    entries = load_education_kanji(args.kanjidic_cache, refresh=args.refresh_data)
    trajectories = load_education_trajectories(
        entries,
        kanjivg_cache=args.kanjivg_cache,
        animcjk_cache=None if args.no_animcjk else args.animcjk_cache,
    )
    metadata = {
        "created_at": datetime.now().isoformat(),
        "algorithm": "PPO with DLS behavior-cloning warm start",
        "device": "cpu",
        "controller": "DLS nominal plus PPO joint residual",
        "residual_action_scale": EnvConfig().residual_action_scale,
        "education_kanji_count": len(entries),
        "expected_grade_counts": EXPECTED_GRADE_COUNTS,
        "kanjidic2_url": KANJIDIC2_URL,
        "kanjidic2_sha256": _sha256(
            args.kanjidic_cache.expanduser().resolve() / "kanjidic2.xml.gz"
        ),
        "kanjivg_revision": KANJIVG_REVISION,
        "kanjivg_archive_url": KANJIVG_ARCHIVE_URL,
        "animcjk_revision": None if args.no_animcjk else ANIMCJK_REVISION,
        "target_success": args.target_success,
        "arguments": vars(args)
        | {"output": str(output), "initial_model": str(args.initial_model or "")},
    }
    (output / "run.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    model: PPO | None = None
    for stage_number, (name, pool_indices) in enumerate(_stage_pools(entries), start=1):
        if stage_number < args.start_stage:
            continue
        stage_dir = output / f"{stage_number:02d}-{name}"
        pool_entries = tuple(entries[index] for index in pool_indices)
        pool_trajectories = tuple(trajectories[index] for index in pool_indices)
        train_env = _vec_env(
            pool_trajectories,
            args.n_envs,
            stage_dir / "train_logs",
            args.seed + stage_number,
        )
        if model is None:
            if args.initial_model:
                model = PPO.load(
                    args.initial_model.expanduser(),
                    env=train_env,
                    device="cpu",
                    n_steps=args.n_steps,
                    batch_size=args.batch_size,
                    learning_rate=args.learning_rate,
                )
            else:
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
                )
        else:
            model.set_env(train_env)

        print(f"\n=== {name}: {len(pool_entries)} kanji ===", flush=True)
        round_number = 0
        success_rate = 0.0
        while success_rate < args.stage_target:
            round_number += 1
            demo_obs, demo_actions = _collect_demonstrations(
                pool_trajectories, args.bc_steps, args.seed + stage_number * 100 + round_number
            )
            bc_loss = _behavior_clone(
                model,
                demo_obs,
                demo_actions,
                epochs=args.bc_epochs,
                batch_size=args.batch_size,
                seed=args.seed + round_number,
            )
            checkpoint = CheckpointCallback(
                save_freq=max(1, args.checkpoint_freq // args.n_envs),
                save_path=str(stage_dir / "checkpoints"),
                name_prefix=name,
            )
            model.learn(
                total_timesteps=args.timesteps_per_round,
                callback=checkpoint,
                reset_num_timesteps=False,
                progress_bar=False,
            )
            model.save(stage_dir / "latest_model")
            sample = _sample_indices(len(pool_entries), args.stage_eval_size)
            success_rate, _ = _evaluate(
                model,
                pool_entries,
                pool_trajectories,
                stage_dir / f"round-{round_number}-evaluation.csv",
                sample,
                seed=args.seed,
            )
            summary = {
                "stage": name,
                "kanji_count": len(pool_entries),
                "round": round_number,
                "bc_loss": bc_loss,
                "sample_success_rate": success_rate,
                "cumulative_timesteps": model.num_timesteps,
            }
            (stage_dir / "summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(json.dumps(summary, ensure_ascii=False), flush=True)
            if args.max_rounds and round_number >= args.max_rounds:
                break
        train_env.close()
        _plot_rewards(stage_dir, stage_dir / "train_logs")

    assert model is not None
    final_round = 0
    while True:
        final_round += 1
        success_rate, failures = _evaluate(
            model,
            entries,
            trajectories,
            output / f"all-kanji-evaluation-{final_round}.csv",
            seed=args.seed,
        )
        grade_rates = {}
        evaluation = np.genfromtxt(
            output / f"all-kanji-evaluation-{final_round}.csv",
            delimiter=",",
            names=True,
            dtype=None,
            encoding="utf-8",
        )
        for grade in range(1, 7):
            selected = evaluation[evaluation["grade"] == grade]
            grade_rates[str(grade)] = float(np.mean(selected["success"]))
        result = {
            "round": final_round,
            "success_rate": success_rate,
            "success_count": len(entries) - len(failures),
            "total": len(entries),
            "grade_success_rates": grade_rates,
            "cumulative_timesteps": model.num_timesteps,
        }
        (output / "final_evaluation.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        model.save(output / "final_model")
        print(json.dumps(result, ensure_ascii=False), flush=True)
        reached_round_limit = args.max_rounds and final_round >= args.max_rounds
        if success_rate >= args.target_success or reached_round_limit:
            break
        failed_trajectories = tuple(trajectories[index] for index in failures)
        demo_obs, demo_actions = _collect_demonstrations(
            failed_trajectories, args.bc_steps, args.seed + 10_000 + final_round
        )
        _behavior_clone(
            model,
            demo_obs,
            demo_actions,
            epochs=args.bc_epochs,
            batch_size=args.batch_size,
            seed=args.seed + final_round,
        )
        final_env = _vec_env(trajectories, args.n_envs, output / "final_train_logs", args.seed)
        model.set_env(final_env)
        model.learn(total_timesteps=args.timesteps_per_round, reset_num_timesteps=False)
        final_env.close()

    print(f"Training complete: {output / 'final_model.zip'}", flush=True)


if __name__ == "__main__":
    main()
