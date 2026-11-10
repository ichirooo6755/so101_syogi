"""Train PPO residual control for tome, hane, harai, and brush-line quality."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Callable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from so101_calligraphy.config import EnvConfig
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.training.train import _plot_rewards
from so101_calligraphy.trajectory.animcjk import (
    ANIMCJK_REVISION,
    enrich_many_with_animcjk_widths,
)
from so101_calligraphy.trajectory.kanjivg import (
    KANJIVG_REVISION,
    TECHNIQUE_STAGES,
    load_kanjivg_stage,
)
from so101_calligraphy.trajectory.profile import resolve_technique
from so101_calligraphy.trajectory.types import Trajectory


def _stages(
    cache_dir: Path,
    animcjk_cache: Path | None,
) -> tuple[tuple[str, tuple[Trajectory, ...]], ...]:
    trajectories = tuple(
        load_kanjivg_stage(stage, cache_dir=cache_dir) for stage in TECHNIQUE_STAGES
    )
    if animcjk_cache is not None:
        trajectories = enrich_many_with_animcjk_widths(
            (
                (trajectory, stage.character, (int(stage.stroke_number),))
                for trajectory, stage in zip(
                    trajectories, TECHNIQUE_STAGES, strict=True
                )
            ),
            cache_dir=animcjk_cache,
        )
    by_slug = {
        stage.slug: trajectory
        for stage, trajectory in zip(TECHNIQUE_STAGES, trajectories, strict=True)
    }
    return (
        ("tome", (by_slug["horizontal"], by_slug["vertical"], by_slug["dot"])),
        ("hane", (by_slug["hook"],)),
        ("harai", (by_slug["left-sweep"], by_slug["right-sweep"])),
        ("mixed", tuple(by_slug.values())),
    )


def _env_factory(
    task: str,
    trajectories: Sequence[Trajectory],
    monitor_path: Path,
    *,
    randomized: bool,
) -> Callable[[], Monitor]:
    def create() -> Monitor:
        monitor_path.parent.mkdir(parents=True, exist_ok=True)
        env = CalligraphyEnv(
            task=task,
            trajectories=trajectories,
            config=EnvConfig(ik_assist=True, domain_randomization=randomized),
        )
        return Monitor(
            env,
            filename=str(monitor_path),
            info_keywords=(
                "is_success",
                "progress",
                "beauty_score",
                "unintended_ink_fraction",
            ),
        )

    return create


def _evaluate(
    model: PPO | None,
    trajectories: Sequence[Trajectory],
    output: Path,
    *,
    seed: int,
    save_ink: bool,
    randomized: bool = False,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for index, trajectory in enumerate(trajectories):
        env = CalligraphyEnv(
            task=f"beauty-eval-{index}",
            trajectory=trajectory,
            config=EnvConfig(
                ik_assist=True, domain_randomization=randomized
            ),
        )
        observation, _ = env.reset(seed=seed + index)
        peak_force = 0.0
        info: dict[str, object] = {}
        try:
            steps = 0
            while True:
                steps += 1
                if model is None:
                    action = np.zeros(env.action_space.shape, dtype=np.float32)
                else:
                    action, _ = model.predict(observation, deterministic=True)
                observation, _, terminated, truncated, info = env.step(action)
                peak_force = max(peak_force, float(info["contact_force"]))
                if terminated or truncated:
                    break
            qualities = tuple(env._stroke_scores.values())
            technique = resolve_technique(trajectory.strokes[0])
            quality_means = {
                name: float(np.mean([quality[name] for quality in qualities]))
                if qualities
                else 0.0
                for name in ("score", "finish", "width", "pressure")
            }
            rows.append(
                {
                    "source": trajectory.source,
                    "technique": technique,
                    "success": bool(info["is_success"]),
                    "steps": steps,
                    "beauty_score": float(info["beauty_score"]),
                    "stroke_score": quality_means["score"],
                    "finish_score": quality_means["finish"],
                    "width_score": quality_means["width"],
                    "pressure_score": quality_means["pressure"],
                    "peak_force": peak_force,
                    "unintended_ink_fraction": float(
                        info["unintended_ink_fraction"]
                    ),
                }
            )
            if save_ink:
                ink_dir = output / "ink"
                ink_dir.mkdir(parents=True, exist_ok=True)
                plt.imsave(
                    ink_dir / f"{index + 1:02d}-{technique}.png",
                    env.ink.rgb_image(),
                )
        finally:
            env.close()
    beauty = np.asarray([float(row["beauty_score"]) for row in rows])
    result: dict[str, object] = {
        "domain_randomization": randomized,
        "success_rate": float(np.mean([bool(row["success"]) for row in rows])),
        "mean_beauty_score": float(beauty.mean()),
        "minimum_beauty_score": float(beauty.min()),
        "trajectories": rows,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "evaluation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--initial-model", type=Path)
    parser.add_argument(
        "--start-stage",
        type=int,
        default=1,
        help="Start at stage 1-4; stages above 1 require --initial-model.",
    )
    parser.add_argument("--kanjivg-cache", type=Path, default=Path("data/kanjivg"))
    parser.add_argument("--animcjk-cache", type=Path, default=Path("data/animcjk"))
    parser.add_argument(
        "--no-animcjk",
        action="store_true",
        help="Use generated widths instead of pinned AnimCJK Japanese outlines.",
    )
    parser.add_argument("--timesteps", type=int, default=50_000, help="PPO steps per stage.")
    parser.add_argument("--n-envs", type=int, default=4)
    parser.add_argument("--n-steps", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--checkpoint-freq", type=int, default=25_000)
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if min(args.timesteps, args.n_envs, args.n_steps, args.batch_size) <= 0:
        raise SystemExit("Training sizes must be positive.")
    if (args.n_steps * args.n_envs) % args.batch_size:
        raise SystemExit("--batch-size must divide --n-steps * --n-envs.")
    if args.initial_model and not args.initial_model.expanduser().is_file():
        raise SystemExit(f"Initial model does not exist: {args.initial_model}")
    if not 1 <= args.start_stage <= 4:
        raise SystemExit("--start-stage must be in 1..4.")
    if args.start_stage > 1 and not args.initial_model:
        raise SystemExit("--start-stage above 1 requires --initial-model.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = (args.output or Path("runs") / f"beauty-{timestamp}").resolve()
    output.mkdir(parents=True, exist_ok=True)
    try:
        stages = _stages(
            args.kanjivg_cache,
            None if args.no_animcjk else args.animcjk_cache,
        )
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    all_trajectories = stages[-1][1]

    metadata = {
        "created_at": datetime.now().isoformat(),
        "algorithm": "PPO residual RL",
        "device": "cpu",
        "kanjivg_revision": KANJIVG_REVISION,
        "animcjk_revision": None if args.no_animcjk else ANIMCJK_REVISION,
        "stages": [name for name, _ in stages],
        "timesteps_per_stage": args.timesteps,
        "seed": args.seed,
        "domain_randomization": True,
        "observation_size": 42,
        "action_size": 6,
    }
    (output / "run.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    model: PPO | None = (
        PPO.load(args.initial_model.expanduser(), device="cpu")
        if args.initial_model
        else None
    )
    baseline = _evaluate(
        model, all_trajectories, output / "baseline", seed=args.seed, save_ink=False
    )
    best_robust_score = (
        0.70 * float(baseline["mean_beauty_score"])
        + 0.30 * float(baseline["minimum_beauty_score"])
        if model is not None
        else -np.inf
    )
    best_stage = "initial" if model is not None else ""
    if model is not None:
        model.save(output / "best_model")
    print(
        f"baseline success={baseline['success_rate']:.1%} "
        f"beauty={baseline['mean_beauty_score']:.2f}",
        flush=True,
    )

    for stage_number, (stage_name, trajectories) in enumerate(stages, start=1):
        if stage_number < args.start_stage:
            continue
        stage_dir = output / f"{stage_number:02d}-{stage_name}"
        env = DummyVecEnv(
            [
                _env_factory(
                    stage_name,
                    trajectories,
                    stage_dir / "train_logs" / f"train-{index}.monitor.csv",
                    randomized=True,
                )
                for index in range(args.n_envs)
            ]
        )
        env.seed(args.seed + stage_number * 100)
        if model is None:
            model = PPO(
                "MlpPolicy",
                env,
                learning_rate=args.learning_rate,
                n_steps=args.n_steps,
                batch_size=args.batch_size,
                gamma=0.995,
                gae_lambda=0.95,
                ent_coef=0.002,
                policy_kwargs={"net_arch": [256, 256]},
                seed=args.seed,
                device="cpu",
                verbose=1,
            )
        else:
            model.set_env(env)
        checkpoint = CheckpointCallback(
            save_freq=max(1, args.checkpoint_freq // args.n_envs),
            save_path=str(stage_dir / "checkpoints"),
            name_prefix=stage_name,
        )
        print(f"\n=== Beauty stage {stage_number}/{len(stages)}: {stage_name} ===")
        model.learn(
            total_timesteps=args.timesteps,
            reset_num_timesteps=(stage_number == 1 and not args.initial_model),
            callback=checkpoint,
            progress_bar=False,
        )
        model.save(stage_dir / "final_model")
        env.close()
        _plot_rewards(stage_dir, stage_dir / "train_logs")
        candidates: list[tuple[str, PPO]] = [(f"{stage_name}-final", model)]
        candidates.extend(
            (checkpoint_path.stem, PPO.load(checkpoint_path, device="cpu"))
            for checkpoint_path in sorted((stage_dir / "checkpoints").glob("*.zip"))
        )
        for candidate_name, candidate in candidates:
            stage_evaluation = _evaluate(
                candidate,
                all_trajectories,
                stage_dir / "evaluation" / candidate_name,
                seed=args.seed,
                save_ink=False,
            )
            robust_score = 0.70 * float(
                stage_evaluation["mean_beauty_score"]
            ) + 0.30 * float(stage_evaluation["minimum_beauty_score"])
            if robust_score > best_robust_score:
                best_robust_score = robust_score
                best_stage = candidate_name
                candidate.save(output / "best_model")

    assert model is not None
    model.save(output / "latest_model")
    selected_model = PPO.load(output / "best_model", device="cpu")
    selected_model.save(output / "final_model")
    final = _evaluate(
        selected_model,
        all_trajectories,
        output / "final",
        seed=args.seed,
        save_ink=True,
    )
    summary = {
        "baseline": baseline,
        "final": final,
        "cumulative_timesteps": model.num_timesteps,
        "selected_stage": best_stage,
        "selection_score": best_robust_score,
        "model": str(output / "final_model.zip"),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"training complete: success={final['success_rate']:.1%} "
        f"beauty={final['mean_beauty_score']:.2f} model={output / 'final_model.zip'}",
        flush=True,
    )


if __name__ == "__main__":
    main()
