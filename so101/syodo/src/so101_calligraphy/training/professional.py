"""Train and audit the complete inkstone-to-kaisho PPO curriculum."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
import csv
from dataclasses import asdict, replace
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Callable

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import FloatSchedule
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecEnv

from so101_calligraphy.config import (
    EnvConfig,
    InkConfig,
    ModuleConfig,
    WritingLayoutConfig,
)
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.hardware_desk import load_desk, overlay_desk_hardware
from so101_calligraphy.metrics import BEAUTY_COMPONENT_WEIGHTS, WIDTH_DETAIL_KEYS
from so101_calligraphy.training.hard_mining import (
    MiningThresholds,
    assess_characters,
    read_character_csv,
)
from so101_calligraphy.training.model_selection import snapshot_from_evaluation
from so101_calligraphy.training.provenance import (
    collect_run_metadata,
    format_command,
    write_command_file,
    write_run_metadata,
    write_status_markdown,
)
from so101_calligraphy.training.education import _behavior_clone
from so101_calligraphy.training.train import _plot_rewards
from so101_calligraphy.trajectory.animcjk import ANIMCJK_REVISION, animcjk_coverage
from so101_calligraphy.trajectory.education import (
    EducationKanji,
    lazy_joyo_trajectories,
    load_joyo_kanji,
)
from so101_calligraphy.trajectory.kana import kana_characters, load_kana_trajectories
from so101_calligraphy.trajectory.kanjivg import KANJIVG_REVISION
from so101_calligraphy.trajectory.layout import frame_paper, writing_frames
from so101_calligraphy.trajectory.profile import resolve_technique
from so101_calligraphy.trajectory.professional import (
    MotoyaFontError,
    font_coverage,
    resolve_exemplar_font,
)
from so101_calligraphy.trajectory.types import Trajectory


COMPONENTS = tuple(BEAUTY_COMPONENT_WEIGHTS)
WIDTH_COMPONENTS = (*WIDTH_DETAIL_KEYS, "stroke_width_hierarchy")
WIDTH_GATES = {
    "width_contrast": 60.0,
    "taper": 58.0,
    "width_smoothness": 58.0,
}
QUALITY_GATES = {
    "glyph_shape": 50.0,
}
ABLATIONS = (
    "legacy",
    "brush",
    "brush-ink",
    "all",
    "no-brush",
    "no-ink",
    "no-brushwork",
    "no-exemplar",
)
CENTER110_PROFILES = ("p10-80-v1",)


def _set_learning_rate(model: PPO, learning_rate: float) -> None:
    """Apply a resumed run's CLI rate to PPO and its existing optimizer."""

    model.learning_rate = learning_rate
    model.lr_schedule = FloatSchedule(learning_rate)
    for group in model.policy.optimizer.param_groups:
        group["lr"] = learning_rate


def _copy_policy_only(parent: PPO, fresh: PPO) -> None:
    """Copy policy tensors without carrying optimizer state or timestep history."""

    fresh.policy.load_state_dict(parent.policy.state_dict())
    fresh.num_timesteps = 0


def _pyplot():
    """Lazy Agg backend import — avoids macOS font-cache I/O hangs at process start."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


class RewardTraceCallback(BaseCallback):
    """Persist rollout reward means even when a long glyph has not terminated."""

    def __init__(self, output: Path) -> None:
        super().__init__(verbose=0)
        self.output = output
        self._rollout_rewards: list[float] = []
        self.rows: list[tuple[int, float, float]] = []

    def _on_step(self) -> bool:
        self._rollout_rewards.extend(
            np.asarray(self.locals["rewards"], dtype=np.float64).reshape(-1).tolist()
        )
        return True

    def _on_rollout_end(self) -> None:
        values = np.asarray(self._rollout_rewards, dtype=np.float64)
        if len(values):
            self.rows.append((self.num_timesteps, float(values.mean()), float(values.std())))
        self._rollout_rewards.clear()
        self.save()

    def save(self) -> None:
        if not self.rows:
            return
        self.output.parent.mkdir(parents=True, exist_ok=True)
        with self.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("timesteps", "mean_step_reward", "std_step_reward"))
            writer.writerows(self.rows)

    def plot(self, destination: Path) -> None:
        if not self.rows:
            return
        plt = _pyplot()
        values = np.asarray(self.rows, dtype=np.float64)
        figure, axis = plt.subplots(figsize=(8, 4.5))
        axis.plot(values[:, 0], values[:, 1], color="#1d4ed8", linewidth=2)
        axis.fill_between(
            values[:, 0],
            values[:, 1] - values[:, 2],
            values[:, 1] + values[:, 2],
            color="#93c5fd",
            alpha=0.35,
        )
        axis.set(
            title="PPO rollout reward",
            xlabel="timesteps",
            ylabel="mean reward per control step",
        )
        axis.grid(alpha=0.2)
        figure.tight_layout()
        figure.savefig(destination, dpi=160)
        plt.close(figure)


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m{secs:02d}s"


class ProgressETACallback(BaseCallback):
    """Print and persist overall training ETA across curriculum stages."""

    def __init__(
        self,
        *,
        progress_path: Path,
        stage_name: str,
        stage_number: int,
        stage_count: int,
        stage_timesteps: int,
        stage_weight: float,
        completed_weight: float,
        total_weight: float,
        run_started_at: float,
        log_every_rollouts: int = 1,
    ) -> None:
        super().__init__(verbose=0)
        self.progress_path = progress_path
        self.stage_name = stage_name
        self.stage_number = stage_number
        self.stage_count = stage_count
        self.stage_timesteps = max(1, stage_timesteps)
        self.stage_weight = max(stage_weight, 1e-6)
        self.completed_weight = completed_weight
        self.total_weight = max(total_weight, 1e-6)
        self.run_started_at = run_started_at
        self.stage_started_at = run_started_at
        self._rollouts = 0
        self._log_every = max(1, log_every_rollouts)
        self._stage_start_timesteps = 0

    def _on_training_start(self) -> None:
        self.stage_started_at = datetime.now().timestamp()
        self._stage_start_timesteps = int(self.model.num_timesteps)

    def _on_step(self) -> bool:
        return True

    def _on_rollout_end(self) -> bool:
        self._rollouts += 1
        if self._rollouts % self._log_every:
            return True
        now = datetime.now().timestamp()
        done_in_stage = max(
            0, int(self.model.num_timesteps) - self._stage_start_timesteps
        )
        stage_frac = min(1.0, done_in_stage / self.stage_timesteps)
        overall = (
            self.completed_weight + self.stage_weight * stage_frac
        ) / self.total_weight
        elapsed = now - self.run_started_at
        eta = (elapsed / max(overall, 1e-6)) - elapsed if overall > 0.01 else float("nan")
        remaining = eta if eta == eta else float("nan")
        payload = {
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "stage": self.stage_name,
            "stage_number": self.stage_number,
            "stage_count": self.stage_count,
            "stage_progress": round(stage_frac, 4),
            "overall_progress": round(float(overall), 4),
            "elapsed_sec": round(elapsed, 1),
            "remaining_sec": None if remaining != remaining else round(remaining, 1),
            "eta_finish": (
                None
                if remaining != remaining
                else datetime.fromtimestamp(now + remaining).isoformat(timespec="seconds")
            ),
            "stage_timesteps_done": done_in_stage,
            "stage_timesteps_total": self.stage_timesteps,
            "cumulative_timesteps": int(self.model.num_timesteps),
        }
        self.progress_path.parent.mkdir(parents=True, exist_ok=True)
        self.progress_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        rem_txt = (
            "estimating..."
            if remaining != remaining
            else _format_duration(remaining)
        )
        print(
            f"[progress] {self.stage_number}/{self.stage_count} {self.stage_name} "
            f"stage={stage_frac*100:.1f}% overall={overall*100:.1f}% "
            f"elapsed={_format_duration(elapsed)} remaining~{rem_txt}",
            flush=True,
        )
        return True


class IndexedTrajectories(Sequence[Trajectory]):
    """A zero-copy view used to build cumulative curriculum pools."""

    def __init__(
        self,
        dataset: Sequence[Trajectory],
        indices: Sequence[int],
    ) -> None:
        self.dataset = dataset
        self.indices = tuple(int(index) for index in indices)

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, index: int | slice) -> Trajectory | tuple[Trajectory, ...]:
        if isinstance(index, slice):
            return tuple(self[position] for position in range(*index.indices(len(self))))
        return self.dataset[self.indices[index]]


class CombinedGlyphDataset(Sequence[Trajectory]):
    """Joyo trajectories plus KanjiVG kana; indices are contiguous."""

    def __init__(
        self,
        joyo: Sequence[Trajectory],
        kana: Sequence[Trajectory],
    ) -> None:
        self.joyo = joyo
        self.kana = tuple(kana)
        self.joyo_count = len(joyo)

    def __len__(self) -> int:
        return self.joyo_count + len(self.kana)

    def __getitem__(self, index: int) -> Trajectory:
        if index < 0:
            index += len(self)
        if index < self.joyo_count:
            return self.joyo[index]
        return self.kana[index - self.joyo_count]


def module_preset(name: str) -> ModuleConfig:
    """Matched incremental configurations for safe feature rollback."""

    if name == "legacy":
        return ModuleConfig()
    if name == "brush":
        return ModuleConfig(brush_physics="professional")
    if name == "brush-ink":
        return ModuleConfig(
            brush_physics="professional",
            ink_model="professional",
            inkstone=True,
        )
    if name == "all":
        return ModuleConfig.professional()
    if name == "no-brush":
        return ModuleConfig(
            ink_model="professional",
            brushwork="professional",
            inkstone=True,
            professional_exemplar=True,
        )
    if name == "no-ink":
        return ModuleConfig(
            brush_physics="professional",
            brushwork="professional",
            professional_exemplar=True,
        )
    if name == "no-brushwork":
        return ModuleConfig(
            brush_physics="professional",
            ink_model="professional",
            inkstone=True,
            professional_exemplar=True,
        )
    if name == "no-exemplar":
        return ModuleConfig(
            brush_physics="professional",
            ink_model="professional",
            brushwork="professional",
            inkstone=True,
        )
    raise ValueError(f"Unknown ablation {name!r}.")


def professional_config(
    ablation: str = "all",
    *,
    randomized: bool = False,
    motoya_font_path: str | Path | None = None,
    pressure_calibration_path: str | Path | None = None,
    require_pressure_calibration: bool = False,
    residual_pressure_integral_scale: float = 1.0,
    pressure_calibration_clip_rate_limit: float = 1.0,
) -> EnvConfig:
    modules = module_preset(ablation)
    ink = InkConfig()
    if modules.ink_model == "professional":
        ink = replace(ink, stamp_edge="hard")
    brush = EnvConfig().brush
    if modules.brushwork == "professional":
        brush = replace(
            brush,
            nominal_compression=0.001,
            nominal_force=1.20,
            large_frame_nominal_force=0.80,
            pressure_response=0.348,
            horizontal_pressure_response=0.27,
            tip_pressure_scale=0.45,
            large_frame_entry_lean=float(np.tan(np.deg2rad(25.0))),
        )
    return EnvConfig(
        ik_assist=True,
        modules=modules,
        brush=brush,
        ink=ink,
        motoya_font_path=None if motoya_font_path is None else str(motoya_font_path),
        observation_version=3,
        path_spacing=0.006,
        contact_tilt_max_speed=1.1,
        contact_pressure_gain=0.0234,
        large_frame_contact_pressure_gain=0.0226,
        horizontal_contact_pressure_gain=0.016,
        pressure_calibration_path=(
            None
            if pressure_calibration_path is None
            else str(pressure_calibration_path)
        ),
        require_pressure_calibration=require_pressure_calibration,
        residual_pressure_integral_scale=residual_pressure_integral_scale,
        pressure_calibration_clip_rate_limit=pressure_calibration_clip_rate_limit,
        domain_randomization=randomized,
        reset_noise=0.01 if randomized else 0.0,
    )


def apply_center110_profile(config: EnvConfig, name: str | None) -> EnvConfig:
    """Apply one versioned, reproducible centered-110mm recovery profile."""

    if name is None:
        return config
    if name not in CENTER110_PROFILES:
        raise ValueError(f"Unknown center110 profile {name!r}.")
    frames = writing_frames(config.paper, config.writing_layout)
    if len(frames) != 1 or not np.allclose(
        frames[0][0], (0.200, 0.0)
    ) or not np.allclose(frames[0][1], (0.110, 0.110)):
        raise ValueError("center110 profiles require the centered 110 mm layout.")
    return replace(
        config,
        brush=replace(
            config.brush,
            minimum_width=0.0063,
            maximum_width=0.024,
        ),
        target_tolerance_xy=0.0015,
        contact_pressure_gain=0.0234,
        large_frame_contact_pressure_gain=0.0226,
        horizontal_contact_pressure_gain=0.019,
        contact_pressure_limit=0.007,
        horizontal_contact_pressure_limit=0.007,
        exemplar_motion_strength=0.50,
        stroke_minimum_gap=0.003,
        stroke_clearance_floor=0.25,
    )


def _sample_indices(indices: Sequence[int], count: int) -> tuple[int, ...]:
    if count <= 0 or count >= len(indices):
        return tuple(indices)
    positions = np.linspace(0, len(indices) - 1, count).round().astype(int)
    return tuple(indices[position] for position in positions)


def _env_factory(
    trajectories: Sequence[Trajectory],
    monitor_path: Path,
    *,
    ablation: str,
    config: EnvConfig,
) -> Callable[[], Monitor]:
    monitor = str(monitor_path)

    def create() -> Monitor:
        Path(monitor).parent.mkdir(parents=True, exist_ok=True)
        info_keywords = (
            "is_success",
            "progress",
            "beauty_score",
            "endpoint_triangle_mean",
            "drip_count",
            *(f"beauty_{name}" for name in COMPONENTS),
        )
        return Monitor(
            CalligraphyEnv(
                task=f"professional-{ablation}",
                trajectories=trajectories,
                config=replace(
                    config,
                    domain_randomization=True,
                    reset_noise=0.01,
                ),
            ),
            filename=monitor,
            info_keywords=info_keywords,
        )

    return create


def _make_vec_env(env_fns: list[Callable[[], Monitor]], n_envs: int) -> VecEnv:
    """Use subprocesses so MuJoCo rollouts actually occupy multiple cores."""

    if n_envs <= 1:
        return DummyVecEnv(env_fns)
    # macOS cannot reliably fork after Objective-C / MuJoCo init.
    return SubprocVecEnv(env_fns, start_method="spawn")


def _training_layouts(config: EnvConfig) -> tuple[int, ...]:
    """Return the configured training layouts that physically exist."""

    if config.training_layout_indices is not None:
        return config.training_layout_indices
    return tuple(range(len(writing_frames(config.paper, config.writing_layout))))


def _collect_demonstration_chunk(
    trajectories: Sequence[Trajectory],
    total_steps: int,
    ablation: str,
    seed: int,
    config: EnvConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Collect residual-zero demonstrations from the analytical controller."""

    env = CalligraphyEnv(
        task="professional-demonstrations",
        trajectories=trajectories,
        config=config,
    )
    rng = np.random.default_rng(seed)
    layouts = _training_layouts(config)
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    try:
        while len(observations) < total_steps:
            trajectory_index = int(rng.integers(len(trajectories)))
            observation, _ = env.reset(
                seed=int(rng.integers(2**31 - 1)),
                options={
                    "trajectory_index": trajectory_index,
                    "layout_index": layouts[int(rng.integers(len(layouts)))],
                },
            )
            for _ in range(48):
                action = np.zeros(6, dtype=np.float32)
                observations.append(observation)
                actions.append(action)
                observation, _, terminated, truncated, _ = env.step(action)
                if len(observations) >= total_steps or terminated or truncated:
                    break
    finally:
        env.close()
    return np.asarray(observations), np.asarray(actions)


def _collect_demonstrations(
    trajectories: Sequence[Trajectory],
    total_steps: int,
    *,
    ablation: str,
    seed: int,
    config: EnvConfig,
    workers: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Collect BC demos; optional process pool for large demonstration budgets."""

    worker_count = max(1, min(int(workers), int(total_steps)))
    if worker_count == 1:
        return _collect_demonstration_chunk(
            trajectories, total_steps, ablation, seed, config
        )

    base, remainder = divmod(total_steps, worker_count)
    chunk_sizes = [base + (1 if index < remainder else 0) for index in range(worker_count)]
    chunk_sizes = [size for size in chunk_sizes if size > 0]
    # Separate processes: MuJoCo is not safe to step from multiple threads.
    with ProcessPoolExecutor(max_workers=len(chunk_sizes)) as pool:
        futures = [
            pool.submit(
                _collect_demonstration_chunk,
                trajectories,
                size,
                ablation,
                seed + offset * 17,
                config,
            )
            for offset, size in enumerate(chunk_sizes)
        ]
        chunks = [future.result() for future in futures]
    observations = np.concatenate([chunk[0] for chunk in chunks], axis=0)
    actions = np.concatenate([chunk[1] for chunk in chunks], axis=0)
    return observations[:total_steps], actions[:total_steps]


def _target_rgb(mask: np.ndarray) -> np.ndarray:
    paper = np.asarray([0.98, 0.97, 0.91], dtype=np.float32)
    ink = np.asarray([0.025, 0.018, 0.012], dtype=np.float32)
    alpha = np.clip(mask[..., None], 0.0, 1.0)
    return paper * (1.0 - alpha) + ink * alpha


def _save_comparison(
    destination: Path,
    character: str,
    actual: np.ndarray,
    target: np.ndarray | None,
) -> None:
    plt = _pyplot()
    destination.parent.mkdir(parents=True, exist_ok=True)
    target_mask = np.zeros(actual.shape[:2], dtype=np.float32) if target is None else target
    difference = np.abs((1.0 - actual.mean(axis=2)) - target_mask)
    figure, axes = plt.subplots(1, 3, figsize=(9.6, 5.2), constrained_layout=True)
    axes[0].imshow(actual)
    axes[0].set_title(f"simulation (U+{ord(character):04X})")
    axes[1].imshow(_target_rgb(target_mask))
    axes[1].set_title("professional image exemplar" if target is not None else "no image exemplar")
    axes[2].imshow(difference, cmap="magma", vmin=0.0, vmax=1.0)
    axes[2].set_title("absolute difference")
    for axis in axes:
        axis.axis("off")
    figure.savefig(destination, dpi=180)
    plt.close(figure)


def evaluate(
    model: PPO | None,
    entries: Sequence[EducationKanji],
    dataset: Sequence[Trajectory],
    indices: Sequence[int],
    output: Path,
    *,
    ablation: str = "all",
    seed: int = 17,
    save_characters: Sequence[str] = (),
    motoya_font_path: Path | None = None,
    progress_path: Path | None = None,
    layout_indices: Sequence[int] = (0,),
    config: EnvConfig | None = None,
) -> dict[str, object]:
    """Evaluate each selected glyph/layout and retain every beauty component."""

    selected = tuple(int(index) for index in indices)
    trajectories = IndexedTrajectories(dataset, selected)
    env = CalligraphyEnv(
        task=f"professional-evaluation-{ablation}",
        trajectories=trajectories,
        config=(
            config
            if config is not None
            else professional_config(ablation, motoya_font_path=motoya_font_path)
        ),
    )
    rows: list[dict[str, object]] = []
    technique_values: dict[str, dict[str, list[float]]] = {
        name: {"finish": [], "width": []} for name in ("tome", "hane", "harai")
    }
    save_set = set(save_characters)
    layouts = tuple(int(index) for index in layout_indices)
    layout_count = len(writing_frames(env.config.paper, env.config.writing_layout))
    if (
        not layouts
        or len(set(layouts)) != len(layouts)
        or any(not 0 <= index < layout_count for index in layouts)
    ):
        raise ValueError(
            f"layout_indices must contain unique values in 0..{layout_count - 1}"
        )
    evaluation_count = len(selected) * len(layouts)
    try:
        for evaluation_index, (local_index, entry_index, layout_index) in enumerate(
            (
                (local_index, entry_index, layout_index)
                for local_index, entry_index in enumerate(selected)
                for layout_index in layouts
            )
        ):
            entry = entries[entry_index]
            observation, _ = env.reset(
                seed=seed + entry_index * 6 + layout_index,
                options={
                    "trajectory_index": local_index,
                    "layout_index": layout_index,
                },
            )
            info: dict[str, object] = {}
            steps = 0
            # 収束しない字で無限に回るのを防ぐ安全弁。環境自体にステップ上限は
            # 無く、2026-08-21 に紙を可動ボディにしたとき評価が CPU 95% のまま
            # 1 時間 45 分止まった。最長の鬱でも 9027 歩なので 40000 は十分広い。
            step_limit = 40_000
            while True:
                steps += 1
                if model is None:
                    action = np.zeros(6, dtype=np.float32)
                else:
                    action, _ = model.predict(observation, deterministic=True)
                observation, _, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    break
                if steps >= step_limit:
                    print(
                        f"[warn] {entry.character} did not finish in {step_limit} "
                        f"steps (progress {float(info['progress']):.2f}); giving up",
                        flush=True,
                    )
                    break
            row: dict[str, object] = {
                "character": entry.character,
                "layout_index": layout_index,
                "writing_frame_size_m": float(info["writing_frame_size_m"]),
                "grade": entry.grade,
                "stroke_count": entry.stroke_count,
                "success": int(bool(info["is_success"])),
                "progress": float(info["progress"]),
                "steps": steps,
                "beauty_score": float(info["beauty_score"]),
                "drip_count": int(info["drip_count"]),
                "collision": ";".join(info["collision_types"]),
                "hard_limit": int(bool(info.get("hard_limit", False))),
                "termination_reason": str(info.get("termination_reason", "")),
                "pressure_calibration_sample_count": len(
                    env._pressure_calibration_samples
                ),
                "pressure_calibration_clipped_count": sum(
                    bool(sample.get("clipped", False))
                    for sample in env._pressure_calibration_samples
                ),
                "pressure_calibration_fallback_count": sum(
                    bool(sample.get("fallback", False))
                    for sample in env._pressure_calibration_samples
                ),
                "unintended_ink_fraction": float(info["unintended_ink_fraction"]),
                "endpoint_triangle_count": int(info.get("endpoint_triangle_count", 0)),
                "endpoint_triangle_sum": float(info.get("endpoint_triangle_sum", 0.0)),
                "endpoint_triangle_mean": float(info.get("endpoint_triangle_mean", 100.0)),
                "endpoint_triangle_minimum": float(
                    info.get("endpoint_triangle_minimum", 100.0)
                ),
            }
            components = info["beauty_components"]
            row.update({name: float(components[name]) for name in COMPONENTS})
            glyph_metrics = info.get("glyph_metrics", {})
            if isinstance(glyph_metrics, dict):
                row["exemplar_mask_iou"] = 100.0 * float(glyph_metrics.get("iou", 0.0))
            width_details = info.get("width_details", {})
            if isinstance(width_details, dict):
                row.update(
                    {
                        name: float(width_details.get(name, 0.0))
                        for name in WIDTH_COMPONENTS
                    }
                )
            rows.append(row)
            for stroke_index, metrics in env._stroke_scores.items():
                technique = resolve_technique(env.trajectory.strokes[stroke_index])
                technique_values[technique]["finish"].append(100.0 * metrics["finish"])
                technique_values[technique]["width"].append(100.0 * metrics["width"])
            if entry.character in save_set:
                suffix = f"layout-{layout_index}"
                ink_path = output / "ink" / (
                    f"{ord(entry.character):05x}-{entry.character}-{suffix}.png"
                )
                ink_path.parent.mkdir(parents=True, exist_ok=True)
                _pyplot().imsave(ink_path, env.ink.rgb_image())
                _save_comparison(
                    output
                    / "comparisons"
                    / f"{ord(entry.character):05x}-{entry.character}-{suffix}.png",
                    entry.character,
                    env.ink.rgb_image(),
                    env._professional_mask,
                )
            completed = evaluation_index + 1
            report_every = 10 if evaluation_count < 100 else 100
            if completed % report_every == 0 or completed == evaluation_count:
                print(f"evaluation {completed}/{evaluation_count}", flush=True)
                if progress_path is not None:
                    progress_path.write_text(
                        json.dumps(
                            {
                                "updated_at": datetime.now().isoformat(timespec="seconds"),
                                "phase": "final_eval",
                                "eval_progress": f"{completed}/{evaluation_count}",
                                "stage_progress": round(
                                    completed / max(evaluation_count, 1), 4
                                ),
                                "overall_progress": 1.0,
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
    finally:
        env.close()

    output.mkdir(parents=True, exist_ok=True)
    with (output / "characters.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    beauty = np.asarray([float(row["beauty_score"]) for row in rows])
    endpoint_count = sum(int(row["endpoint_triangle_count"]) for row in rows)
    endpoint_rows = [row for row in rows if int(row["endpoint_triangle_count"]) > 0]
    result: dict[str, object] = {
        "ablation": ablation,
        "count": len(rows),
        "unique_character_count": len({str(row["character"]) for row in rows}),
        "layout_count": len(layouts),
        "success_rate": float(np.mean([int(row["success"]) for row in rows])),
        "mean_beauty_score": float(np.mean(beauty)),
        "p10_beauty_score": float(np.percentile(beauty, 10)),
        "minimum_beauty_score": float(np.min(beauty)),
        "total_drips": int(sum(int(row["drip_count"]) for row in rows)),
        "collision_count": int(sum(bool(row["collision"]) for row in rows)),
        "endpoint_triangle": {
            "count": endpoint_count,
            "mean": (
                sum(float(row["endpoint_triangle_sum"]) for row in rows)
                / endpoint_count
                if endpoint_count
                else 100.0
            ),
            "minimum": (
                min(float(row["endpoint_triangle_minimum"]) for row in endpoint_rows)
                if endpoint_rows
                else 100.0
            ),
        },
        "component_means": {
            name: float(np.mean([float(row[name]) for row in rows]))
            for name in COMPONENTS
        },
        "component_minimums": {
            name: float(np.min([float(row[name]) for row in rows]))
            for name in COMPONENTS
        },
        "width_detail_means": {
            name: float(np.mean([float(row.get(name, 0.0)) for row in rows]))
            for name in WIDTH_COMPONENTS
            if name in rows[0]
        },
        "technique_means": {
            technique: {
                "count": len(values["finish"]),
                "finish": float(np.mean(values["finish"])),
                "width": float(np.mean(values["width"])),
            }
            for technique, values in technique_values.items()
            if values["finish"]
        },
    }
    result["layout_summaries"] = {
        str(layout): {
            "count": len(layout_rows),
            "mean_beauty_score": float(
                np.mean([float(row["beauty_score"]) for row in layout_rows])
            ),
            "p10_beauty_score": float(
                np.percentile(
                    [float(row["beauty_score"]) for row in layout_rows], 10
                )
            ),
        }
        for layout in layouts
        if (
            layout_rows := [
                row for row in rows if int(row["layout_index"]) == layout
            ]
        )
    }
    calibration_sample_count = sum(
        int(row["pressure_calibration_sample_count"]) for row in rows
    )
    calibration_clipped_count = sum(
        int(row["pressure_calibration_clipped_count"]) for row in rows
    )
    calibration_fallback_count = sum(
        int(row["pressure_calibration_fallback_count"]) for row in rows
    )
    result.update(
        {
            "pressure_calibration_sample_count": calibration_sample_count,
            "pressure_calibration_clipped_count": calibration_clipped_count,
            "pressure_calibration_fallback_count": calibration_fallback_count,
            "pressure_calibration_clip_rate": (
                calibration_clipped_count / calibration_sample_count
                if calibration_sample_count
                else 0.0
            ),
            "pressure_calibration_fallback_rate": (
                calibration_fallback_count / calibration_sample_count
                if calibration_sample_count
                else 0.0
            ),
        }
    )
    result["robust_score"] = float(
        0.55 * result["mean_beauty_score"]
        + 0.25 * result["p10_beauty_score"]
        + 0.20 * result["minimum_beauty_score"]
        - 2.0 * result["total_drips"] / len(rows)
        - 5.0 * result["collision_count"] / len(rows)
    )
    (output / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def _curriculum(
    entries: Sequence[EducationKanji],
    *,
    joyo_count: int,
    kana_count: int,
) -> tuple[tuple[str, tuple[int, ...]], ...]:
    """Radical-first drills, strong kana, then elementary/joyo transfer."""

    def selected(characters: str) -> tuple[int, ...]:
        requested = set(characters)
        return tuple(
            index for index, entry in enumerate(entries) if entry.character in requested
        )

    kana_indices = tuple(range(joyo_count, joyo_count + kana_count))
    # Broader radical carriers so the radical stage already covers joyo components.
    radical_pool = (
        "休体林森明好語道海情持花"
        "信何作住位体例係"
        "清活流消深温港湖"
        "快性急思情意"
        "打投持指掃"
        "花草茶落葉"
        "近返送通進運道遠"
        "記計訓話詩読語調"
    )
    return (
        ("brush-handling", selected("一")),
        ("start-send-finish", selected("一十人入八大小上土")),
        ("tome-hane-harai", selected("永水小木火人子心手")),
        ("turns-curves-folds", selected("口日月山田川力也九乃")),
        ("radicals", selected(radical_pool)),
        ("kana", kana_indices),
        (
            "elementary",
            tuple(index for index, entry in enumerate(entries[:joyo_count]) if entry.grade <= 6),
        ),
        ("joyo", tuple(range(joyo_count))),
    )


STAGE_GATES = {
    "success_rate": 1.0,
    "trajectory": 75.0,
    "line_width": 65.0,
    "stroke_placement": 72.0,
    "stroke_angle": 72.0,
    "brushwork": 62.0,
    "smoothness": 45.0,
}
TECHNIQUE_GATES = {"finish": 65.0, "width": 55.0}


def stage_gate(result: dict[str, object]) -> tuple[bool, tuple[str, ...]]:
    """Require technique and safety before curriculum promotion."""

    component_means = result["component_means"]
    failures: list[str] = []
    if float(result["success_rate"]) < STAGE_GATES["success_rate"]:
        failures.append("completion")
    for name, threshold in STAGE_GATES.items():
        if name == "success_rate":
            continue
        if float(component_means[name]) < threshold:
            failures.append(name)
    width_means = result.get("width_detail_means", {})
    if isinstance(width_means, dict):
        for name, threshold in WIDTH_GATES.items():
            if name in width_means and float(width_means[name]) < threshold:
                failures.append(name)
    if int(result["total_drips"]):
        failures.append("drips")
    if int(result["collision_count"]):
        failures.append("collisions")
    for technique, scores in result.get("technique_means", {}).items():
        for name, threshold in TECHNIQUE_GATES.items():
            if float(scores[name]) < threshold:
                failures.append(f"{technique}_{name}")
    return not failures, tuple(failures)


def _parse_layout_indices(
    value: str | None, *, layout_count: int, option: str
) -> tuple[int, ...]:
    """Parse a layout subset, defaulting to every frame in the active layout."""

    if value is None:
        return tuple(range(layout_count))
    try:
        layouts = tuple(int(item) for item in value.split(","))
    except ValueError as exc:
        raise SystemExit(f"{option} must be comma-separated integers") from exc
    if (
        not layouts
        or len(set(layouts)) != len(layouts)
        or any(not 0 <= layout < layout_count for layout in layouts)
    ):
        upper = layout_count - 1
        raise SystemExit(f"{option} must contain unique values in 0..{upper}")
    return layouts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--initial-model", type=Path)
    parser.add_argument(
        "--run-purpose",
        default="",
        help="Human-readable purpose recorded into command.txt/run.json/status.md.",
    )
    parser.add_argument(
        "--hard-csv",
        type=Path,
        help=(
            "Optional characters.csv used to append a hard-mining stage focused on "
            "failing joyo glyphs (plus a small regression core)."
        ),
    )
    parser.add_argument(
        "--hard-beauty-threshold",
        type=float,
        default=60.0,
        help="Beauty score below which a row enters hard mining (default: 60).",
    )
    parser.add_argument(
        "--start-stage",
        type=int,
        default=1,
        help="Start at curriculum stage 1-9 when resuming from --initial-model.",
    )
    parser.add_argument(
        "--end-stage",
        type=int,
        default=9,
        help="Stop after this curriculum stage (inclusive). Use with --start-stage to run one stage.",
    )
    parser.add_argument("--expert-only", action="store_true")
    parser.add_argument("--ablation", choices=ABLATIONS, default="all")
    parser.add_argument("--timesteps", type=int, default=50_000, help="PPO steps per stage.")
    parser.add_argument(
        "--kana-timesteps",
        type=int,
        default=0,
        help="Override PPO steps for the kana stage; 0 uses 2x --timesteps.",
    )
    parser.add_argument(
        "--elementary-timesteps",
        type=int,
        default=0,
        help="Override PPO steps for elementary kanji; 0 uses --timesteps.",
    )
    parser.add_argument(
        "--joyo-timesteps",
        type=int,
        default=0,
        help="Override PPO steps for joyo kanji; 0 uses --timesteps.",
    )
    parser.add_argument("--bc-steps", type=int, default=12_000, help="DLS demonstrations per stage.")
    parser.add_argument(
        "--kana-bc-steps",
        type=int,
        default=0,
        help="Override BC demos for kana; 0 uses 2x --bc-steps.",
    )
    parser.add_argument("--bc-epochs", type=int, default=3)
    parser.add_argument("--n-envs", type=int, default=4)
    parser.add_argument(
        "--require-subproc",
        action="store_true",
        help="Fail instead of falling back to DummyVecEnv when subprocess startup fails.",
    )
    parser.add_argument(
        "--bc-workers",
        type=int,
        default=0,
        help="Process workers for BC demo collection; 0 uses min(n_envs, CPU count).",
    )
    parser.add_argument("--n-steps", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--clip-range", type=float, default=0.2)
    parser.add_argument("--target-kl", type=float, default=None)
    parser.add_argument(
        "--policy-only-warm-start",
        action="store_true",
        help="Copy only parent policy tensors into a fresh PPO and optimizer.",
    )
    parser.add_argument("--skip-bc", action="store_true")
    parser.add_argument("--train-only", action="store_true")
    parser.add_argument("--minimum-gap", type=float, default=None)
    parser.add_argument("--clearance-floor", type=float, default=None)
    parser.add_argument("--exemplar-motion-strength", type=float, default=None)
    parser.add_argument(
        "--training-layouts",
        default=None,
        help="Optional comma-separated layout subset for bounded hard mining.",
    )
    parser.add_argument(
        "--brushmark-layout",
        action="store_true",
        help="Use one centered 110 mm writing frame for training and evaluation.",
    )
    parser.add_argument(
        "--center110-profile",
        choices=CENTER110_PROFILES,
        help="Apply a versioned centered-110mm control profile.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "mps", "auto"),
        default="cpu",
        help="PPO policy device; MuJoCo vector environments remain CPU-based.",
    )
    parser.add_argument("--stage-eval-size", type=int, default=32)
    parser.add_argument("--eval-limit", type=int, default=0, help="0 evaluates all 2,136.")
    parser.add_argument("--eval-shard-count", type=int, default=1)
    parser.add_argument("--eval-shard-index", type=int, default=0)
    parser.add_argument(
        "--eval-layouts",
        default=None,
        help="Optional comma-separated layout subset; defaults to every active frame.",
    )
    parser.add_argument(
        "--pressure-calibration",
        type=Path,
        help="Versioned pressure calibration JSON used by every train/eval environment.",
    )
    parser.add_argument(
        "--desk",
        type=Path,
        help="Hardware desk JSON. Applies measured tuft length even if paper FK is not ready.",
    )
    parser.add_argument("--require-pressure-calibration", action="store_true")
    parser.add_argument("--residual-pressure-integral-scale", type=float, default=1.0)
    parser.add_argument(
        "--pressure-calibration-clip-rate-limit", type=float, default=1.0
    )
    parser.add_argument(
        "--save-all-ink",
        action="store_true",
        help="Save ink/comparison PNGs for every evaluated glyph (needed for contact sheets).",
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--kanjidic-cache", type=Path, default=Path("data/kanjidic2"))
    parser.add_argument("--kanjivg-cache", type=Path, default=Path("data/kanjivg"))
    parser.add_argument("--animcjk-cache", type=Path, default=Path("data/animcjk"))
    parser.add_argument(
        "--exemplar-font",
        type=Path,
        help=(
            "Licensed teacher font (e.g. Morisawa Kaisho/Ryumin). "
            "Takes precedence over --motoya-font."
        ),
    )
    parser.add_argument(
        "--motoya-font",
        type=Path,
        help=(
            "Optional licensed S Motoya Seikaisho 5 ProN font. When omitted, "
            "the verified free Aoyagi Kouzan image exemplar is used."
        ),
    )
    parser.add_argument("--no-animcjk", action="store_true")
    parser.add_argument(
        "--allow-gate-failure",
        action="store_true",
        help="Continue after a failed curriculum gate (for diagnostics only).",
    )
    return parser.parse_args()


def _validate_args(args: argparse.Namespace) -> None:
    for name in (
        "timesteps",
        "bc_steps",
        "bc_epochs",
        "n_envs",
        "n_steps",
        "batch_size",
        "stage_eval_size",
    ):
        if getattr(args, name) <= 0:
            raise SystemExit(f"--{name.replace('_', '-')} must be positive")
    if args.kana_timesteps < 0 or args.kana_bc_steps < 0:
        raise SystemExit("--kana-timesteps and --kana-bc-steps cannot be negative")
    if args.elementary_timesteps < 0 or args.joyo_timesteps < 0:
        raise SystemExit("--elementary-timesteps and --joyo-timesteps cannot be negative")
    if args.eval_limit < 0:
        raise SystemExit("--eval-limit cannot be negative")
    if args.eval_shard_count <= 0:
        raise SystemExit("--eval-shard-count must be positive")
    if not 0 <= args.eval_shard_index < args.eval_shard_count:
        raise SystemExit("--eval-shard-index must be in [0, --eval-shard-count)")
    layout_count = 1 if args.brushmark_layout else 6
    if args.center110_profile and not args.brushmark_layout:
        raise SystemExit("--center110-profile requires --brushmark-layout")
    if args.center110_profile and any(
        value is not None
        for value in (
            args.minimum_gap,
            args.clearance_floor,
            args.exemplar_motion_strength,
        )
    ):
        raise SystemExit(
            "--center110-profile cannot be combined with individual control overrides"
        )
    _parse_layout_indices(
        args.eval_layouts, layout_count=layout_count, option="--eval-layouts"
    )
    if args.require_pressure_calibration and args.pressure_calibration is None:
        raise SystemExit(
            "--require-pressure-calibration requires --pressure-calibration"
        )
    if args.desk is not None and not args.desk.expanduser().is_file():
        raise SystemExit(f"Desk file does not exist: {args.desk}")
    if args.pressure_calibration and not args.pressure_calibration.expanduser().is_file():
        raise SystemExit(
            f"Pressure calibration does not exist: {args.pressure_calibration}"
        )
    if args.residual_pressure_integral_scale < 0.0:
        raise SystemExit("--residual-pressure-integral-scale cannot be negative")
    if not 0.0 < args.clip_range <= 1.0:
        raise SystemExit("--clip-range must be in (0, 1]")
    if args.target_kl is not None and args.target_kl <= 0.0:
        raise SystemExit("--target-kl must be positive")
    if args.policy_only_warm_start and not args.initial_model:
        raise SystemExit("--policy-only-warm-start requires --initial-model")
    if not np.isfinite(args.hard_beauty_threshold) or args.hard_beauty_threshold < 0:
        raise SystemExit("--hard-beauty-threshold must be finite and non-negative")
    if args.training_layouts is not None:
        _parse_layout_indices(
            args.training_layouts,
            layout_count=layout_count,
            option="--training-layouts",
        )
    if not 0.0 <= args.pressure_calibration_clip_rate_limit <= 1.0:
        raise SystemExit("--pressure-calibration-clip-rate-limit must be in [0, 1]")
    if (args.n_steps * args.n_envs) % args.batch_size:
        raise SystemExit("--batch-size must divide --n-steps * --n-envs")
    if not 1 <= args.start_stage <= 9:
        raise SystemExit("--start-stage must be in 1..9")
    if not 1 <= args.end_stage <= 9:
        raise SystemExit("--end-stage must be in 1..9")
    if args.end_stage < args.start_stage:
        raise SystemExit("--end-stage must be >= --start-stage")
    if args.start_stage > 1 and not args.initial_model:
        raise SystemExit("--start-stage above 1 requires --initial-model")
    if args.initial_model and not args.initial_model.expanduser().is_file():
        raise SystemExit(f"Initial model does not exist: {args.initial_model}")
    if args.hard_csv and not args.hard_csv.expanduser().is_file():
        raise SystemExit(f"--hard-csv does not exist: {args.hard_csv}")
    if args.device == "auto":
        raise SystemExit("--device auto is not implemented; use cpu, cuda, or mps")
    if args.device == "cuda":
        import torch

        if not torch.cuda.is_available():
            raise SystemExit("--device cuda requires a CUDA build of torch")
    if args.start_stage == 9 and not args.hard_csv:
        raise SystemExit("--start-stage 9 requires --hard-csv")


def main() -> None:
    args = _parse_args()
    _validate_args(args)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = (args.output or Path("runs") / f"professional-{timestamp}").resolve()
    output.mkdir(parents=True, exist_ok=True)

    entries = load_joyo_kanji(args.kanjidic_cache)
    joyo_count = len(entries)
    kana_glyphs = kana_characters()
    kana_entries = tuple(
        EducationKanji(character=character, grade=0, stroke_count=0)
        for character in kana_glyphs
    )
    all_entries = tuple(entries) + kana_entries
    characters = [entry.character for entry in entries]
    needs_exemplar = module_preset(args.ablation).professional_exemplar
    try:
        if needs_exemplar:
            exemplar_font, exemplar_source = resolve_exemplar_font(
                args.exemplar_font,
                motoya_path=args.motoya_font,
            )
        else:
            exemplar_font, exemplar_source = None, None
    except (MotoyaFontError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    calibration_path = (
        None
        if args.pressure_calibration is None
        else args.pressure_calibration.expanduser().resolve()
    )
    run_config = professional_config(
        args.ablation,
        motoya_font_path=exemplar_font,
        pressure_calibration_path=calibration_path,
        require_pressure_calibration=args.require_pressure_calibration,
        residual_pressure_integral_scale=args.residual_pressure_integral_scale,
        pressure_calibration_clip_rate_limit=(
            args.pressure_calibration_clip_rate_limit
        ),
    )
    if args.brushmark_layout:
        run_config = replace(
            run_config, writing_layout=WritingLayoutConfig.brushmark_center()
        )
    run_config = apply_center110_profile(run_config, args.center110_profile)
    if args.desk is not None:
        try:
            run_config = overlay_desk_hardware(run_config, load_desk(args.desk))
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    config_updates = {
        name: value
        for name, value in (
            ("stroke_minimum_gap", args.minimum_gap),
            ("stroke_clearance_floor", args.clearance_floor),
            ("exemplar_motion_strength", args.exemplar_motion_strength),
        )
        if value is not None
    }
    if config_updates:
        run_config = replace(run_config, **config_updates)
    if args.training_layouts is not None:
        run_config = replace(
            run_config,
            training_layout_indices=_parse_layout_indices(
                args.training_layouts,
                layout_count=len(
                    writing_frames(run_config.paper, run_config.writing_layout)
                ),
                option="--training-layouts",
            ),
        )
    eval_layouts = _parse_layout_indices(
        args.eval_layouts,
        layout_count=len(writing_frames(run_config.paper, run_config.writing_layout)),
        option="--eval-layouts",
    )
    coverage_chars = characters + list(kana_glyphs) if needs_exemplar else characters
    missing_font = font_coverage(coverage_chars, exemplar_font) if exemplar_font else ()
    missing_animcjk = () if args.no_animcjk else animcjk_coverage(
        characters, args.animcjk_cache
    )
    # Kana is KanjiVG-only for motion; AnimCJK is required only for joyo.
    if missing_animcjk or (needs_exemplar and missing_font):
        raise SystemExit(
            "Professional data coverage failed: "
            f"font_missing={''.join(missing_font)} "
            f"AnimCJK={''.join(missing_animcjk)}"
        )
    source_paper = frame_paper(
        run_config.paper, run_config.writing_layout, 0
    )
    joyo_dataset = lazy_joyo_trajectories(
        entries,
        kanjivg_cache=args.kanjivg_cache,
        animcjk_cache=None if args.no_animcjk else args.animcjk_cache,
        use_animcjk_medians=not args.no_animcjk,
        paper=source_paper,
        spacing=run_config.path_spacing,
    )
    kana_dataset = load_kana_trajectories(
        kana_glyphs, kanjivg_cache=args.kanjivg_cache, paper=source_paper
    )
    dataset = CombinedGlyphDataset(joyo_dataset, kana_dataset)
    purpose = (
        args.run_purpose.strip()
        or "Professional calligraphy curriculum training/evaluation"
    )
    provenance = collect_run_metadata(
        purpose=purpose,
        parent_model=args.initial_model,
        extra={
            "ablation": args.ablation,
            "start_stage": args.start_stage,
            "hard_csv": None if not args.hard_csv else str(args.hard_csv),
            "desk": None if not args.desk else str(args.desk.expanduser().resolve()),
        },
    )
    write_command_file(output, format_command())
    write_status_markdown(
        output,
        provenance,
        status="running",
        next_action="Wait for curriculum completion, then full joyo evaluation.",
    )
    metadata = {
        "created_at": datetime.now().isoformat(),
        "algorithm": "DLS residual PPO with behavior-cloning warm start",
        "device": args.device,
        "joyo_count": joyo_count,
        "kana_count": len(kana_glyphs),
        "kanjivg_revision": KANJIVG_REVISION,
        "animcjk_revision": None if args.no_animcjk else ANIMCJK_REVISION,
        "animcjk_japanese_medians": not args.no_animcjk,
        "professional_exemplar": exemplar_source,
        "professional_exemplar_role": "observation, dense reward, and final-image critic",
        "font_contours_used_for_motion": bool(exemplar_font),
        "exemplar_motion_fit": "per-stroke cubic normal offset, topology preserved",
        "exemplar_font": None if exemplar_font is None else str(exemplar_font),
        "ablation": args.ablation,
        "modules": asdict(module_preset(args.ablation)),
        "environment_config": asdict(
            run_config
        ),
        "observation_version": 3,
        "observation_size": 371,
        "action_size": 6,
        "beauty_weights": BEAUTY_COMPONENT_WEIGHTS,
        "arguments": vars(args)
        | {"output": str(output), "initial_model": str(args.initial_model or "")},
        "provenance": provenance,
    }
    write_run_metadata(output, metadata)

    model: PPO | None = None
    policy_parent: PPO | None = None
    if args.initial_model:
        loaded = PPO.load(args.initial_model.expanduser(), device=args.device)
        if loaded.observation_space.shape != (371,):
            raise SystemExit(
                "--initial-model must use version-3 image observations (371 values); "
                f"this model expects {loaded.observation_space.shape}."
            )
        if args.policy_only_warm_start:
            policy_parent = loaded
        else:
            model = loaded
            _set_learning_rate(model, args.learning_rate)

    curriculum = list(
        _curriculum(all_entries, joyo_count=joyo_count, kana_count=len(kana_glyphs))
    )
    if args.hard_csv:
        rows = read_character_csv(args.hard_csv)
        expected = "".join(entry.character for entry in entries)
        # Partial evaluation CSVs are accepted: assess only characters present.
        present = "".join(str(row["character"]) for row in rows)
        available = set(rows[0].keys()) if rows else set()
        extra = tuple(
            (name, WIDTH_GATES[name]) for name in WIDTH_GATES if name in available
        ) + tuple(
            (name, QUALITY_GATES[name]) for name in QUALITY_GATES if name in available
        )
        assessment = assess_characters(
            rows,
            present,
            thresholds=MiningThresholds(
                beauty=args.hard_beauty_threshold,
                additional_width_minima=extra,
            ),
        )
        by_character = {
            entry.character: index for index, entry in enumerate(entries)
        }
        failed = [
            by_character[item.character]
            for item in assessment.assessments
            if not item.passed and item.character in by_character
        ]
        regression = tuple(
            by_character[character]
            for character in (
                "一",
                "十",
                "永",
                "水",
                "小",
                "書",
                "道",
                "飛",
                "鬱",
                "竜",
                "支",
                "誠",
                "措",
                "拷",
                "砕",
                "案",
            )
            if character in by_character
        )
        hard_indices = tuple(dict.fromkeys([*failed, *regression]))
        if not hard_indices:
            raise SystemExit("--hard-csv produced an empty hard-mining pool")
        curriculum.append(("hard-mining", hard_indices))
        (output / "hard_mining_pool.json").write_text(
            json.dumps(
                {
                    "count": len(hard_indices),
                    "failing": len(failed),
                    "beauty_threshold": args.hard_beauty_threshold,
                    "characters": [
                        entries[index].character for index in hard_indices
                    ],
                    "coverage_note": (
                        "partial CSV" if len(present) != len(expected) else "full CSV"
                    ),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    kana_timesteps = args.kana_timesteps or (2 * args.timesteps)
    kana_bc_steps = args.kana_bc_steps or (2 * args.bc_steps)
    planned_stages = [
        (stage_number, stage_name, stage_indices)
        for stage_number, (stage_name, stage_indices) in enumerate(curriculum, start=1)
        if args.start_stage <= stage_number <= args.end_stage and stage_indices
    ]
    stage_plans: list[dict[str, object]] = []
    for stage_number, stage_name, stage_indices in planned_stages:
        if stage_name == "kana":
            ppo_steps = kana_timesteps
        elif stage_name == "elementary" and args.elementary_timesteps:
            ppo_steps = args.elementary_timesteps
        elif stage_name == "joyo" and args.joyo_timesteps:
            ppo_steps = args.joyo_timesteps
        else:
            ppo_steps = args.timesteps
        bc_steps = 0 if args.skip_bc else (
            kana_bc_steps if stage_name == "kana" else args.bc_steps
        )
        # BC demo collection dominates wall time; weight it explicitly.
        weight = float(ppo_steps) + float(bc_steps) * float(args.bc_epochs) * 12.0
        stage_plans.append(
            {
                "stage_number": stage_number,
                "stage_name": stage_name,
                "characters": len(stage_indices),
                "ppo_steps": ppo_steps,
                "bc_steps": bc_steps,
                "weight": weight,
            }
        )
    total_weight = sum(float(plan["weight"]) for plan in stage_plans) or 1.0
    run_started_at = datetime.now().timestamp()
    progress_path = output / "progress.json"
    (output / "schedule.json").write_text(
        json.dumps(
            {
                "target_wall_hours": "~5",
                "planned_stages": stage_plans,
                "total_weight": total_weight,
                "started_at": datetime.now().isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"Scheduled {len(stage_plans)} stages from #{args.start_stage}; "
        f"progress → {progress_path}",
        flush=True,
    )

    if not args.expert_only:
        completed_weight = 0.0
        for plan_index, (stage_number, stage_name, stage_indices) in enumerate(
            planned_stages
        ):
            plan = stage_plans[plan_index]
            stage_dir = output / f"{stage_number:02d}-{stage_name}"
            trajectories = IndexedTrajectories(dataset, stage_indices)
            validation = _sample_indices(stage_indices, args.stage_eval_size)
            stage_timesteps = int(plan["ppo_steps"])
            stage_bc_steps = int(plan["bc_steps"])
            stage_weight = float(plan["weight"])
            print(
                f"\n>>> starting {stage_number}/{planned_stages[-1][0]} {stage_name}: "
                f"{len(trajectories)} glyphs, ppo={stage_timesteps}, bc={stage_bc_steps}",
                flush=True,
            )
            bc_workers = (
                args.bc_workers
                if args.bc_workers > 0
                else max(1, min(args.n_envs, os.cpu_count() or 1))
            )
            # Collect BC before SubprocVecEnv so we do not hold 8+ MuJoCo
            # processes idle while spawning another 8 demo workers (OOM on 16GB).
            bc_started = datetime.now().timestamp()
            demonstrations: np.ndarray | None = None
            actions: np.ndarray | None = None
            if stage_bc_steps:
                print(
                    f"[progress] collecting BC demos for {stage_name} "
                    f"({stage_bc_steps} steps × {args.bc_epochs} epochs, "
                    f"workers={bc_workers}, envs={args.n_envs})...",
                    flush=True,
                )
                demonstrations, actions = _collect_demonstrations(
                    trajectories,
                    stage_bc_steps,
                    ablation=args.ablation,
                    seed=args.seed + stage_number,
                    config=run_config,
                    workers=bc_workers,
                )
                print(
                    f"[progress] BC demos ready for {stage_name} in "
                    f"{_format_duration(datetime.now().timestamp() - bc_started)}",
                    flush=True,
                )
            # Stage-local copy keeps Subproc pickles small (not the full joyo+kana view).
            stage_pool: Sequence[Trajectory] = tuple(
                trajectories[index] for index in range(len(trajectories))
            )
            # BC against one Dummy env first; Subproc workers come after demos are freed.
            print("[progress] bootstrap DummyVecEnv×1 for BC...", flush=True)
            bootstrap_env = DummyVecEnv(
                [
                    _env_factory(
                        stage_pool,
                        stage_dir / "train_logs" / "bootstrap-0.monitor.csv",
                        ablation=args.ablation,
                        config=run_config,
                    )
                ]
            )
            bootstrap_env.seed(args.seed + stage_number * 100)
            if model is None:
                model = PPO(
                    "MlpPolicy",
                    bootstrap_env,
                    learning_rate=args.learning_rate,
                    n_steps=args.n_steps,
                    batch_size=args.batch_size,
                    gamma=0.995,
                    gae_lambda=0.95,
                    ent_coef=0.002,
                    clip_range=args.clip_range,
                    target_kl=args.target_kl,
                    policy_kwargs={"net_arch": [512, 256]},
                    seed=args.seed,
                    device=args.device,
                    verbose=1,
                )
                if policy_parent is not None:
                    _copy_policy_only(policy_parent, model)
                    policy_parent = None
            elif model.n_envs != bootstrap_env.num_envs:
                # Reload against the bootstrap env count (always 1 here).
                bootstrap_path = stage_dir / "bootstrap_policy.zip"
                model.save(bootstrap_path)
                model = PPO.load(bootstrap_path, env=bootstrap_env, device=args.device)
                _set_learning_rate(model, args.learning_rate)
            else:
                model.set_env(bootstrap_env)
            bc_loss: float | None = None
            if demonstrations is not None and actions is not None:
                print("[progress] behavior cloning...", flush=True)
                bc_loss = _behavior_clone(
                    model,
                    demonstrations,
                    actions,
                    epochs=args.bc_epochs,
                    batch_size=args.batch_size,
                    seed=args.seed + stage_number,
                )
                print(
                    f"[progress] BC done for {stage_name} in "
                    f"{_format_duration(datetime.now().timestamp() - bc_started)} "
                    f"(loss={bc_loss:.5f})",
                    flush=True,
                )
                model.save(stage_dir / "post_bc_model")
                (stage_dir / "post_bc.json").write_text(
                    json.dumps(
                        {
                            "demonstration_steps": stage_bc_steps,
                            "epochs": args.bc_epochs,
                            "loss": bc_loss,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            bootstrap_env.close()
            del demonstrations, actions
            print(
                f"[progress] building {args.n_envs} SubprocVecEnv workers "
                f"({len(stage_pool)} glyphs)...",
                flush=True,
            )
            try:
                train_env = _make_vec_env(
                    [
                        _env_factory(
                            stage_pool,
                            stage_dir / "train_logs" / f"train-{index}.monitor.csv",
                            ablation=args.ablation,
                            config=run_config,
                        )
                        for index in range(args.n_envs)
                    ],
                    args.n_envs,
                )
            except Exception as exc:  # noqa: BLE001 - fall back to keep long runs alive
                if args.require_subproc:
                    raise RuntimeError(
                        f"required SubprocVecEnv failed to start: {exc!r}"
                    ) from exc
                print(
                    f"[progress] SubprocVecEnv failed ({exc!r}); falling back to DummyVecEnv",
                    flush=True,
                )
                train_env = DummyVecEnv(
                    [
                        _env_factory(
                            stage_pool,
                            stage_dir / "train_logs" / f"train-{index}.monitor.csv",
                            ablation=args.ablation,
                            config=run_config,
                        )
                        for index in range(args.n_envs)
                    ]
                )
            train_env.seed(args.seed + stage_number * 100)
            if model.n_envs != train_env.num_envs:
                bridge = stage_dir / "parallel_policy.zip"
                model.save(bridge)
                model = PPO.load(bridge, env=train_env, device=args.device)
                _set_learning_rate(model, args.learning_rate)
            else:
                model.set_env(train_env)
            print(
                f"[progress] vec env ready: {type(train_env).__name__}",
                flush=True,
            )
            checkpoint = CheckpointCallback(
                # ~every 100k env steps: enough for resume, far less SSD wear.
                save_freq=max(1, 100_000 // args.n_envs),
                save_path=str(stage_dir / "checkpoints"),
                name_prefix=stage_name,
            )
            reward_trace = RewardTraceCallback(stage_dir / "rollout_rewards.csv")
            progress = ProgressETACallback(
                progress_path=progress_path,
                stage_name=stage_name,
                stage_number=plan_index + 1,
                stage_count=len(planned_stages),
                stage_timesteps=stage_timesteps,
                stage_weight=stage_weight,
                completed_weight=completed_weight,
                total_weight=total_weight,
                run_started_at=run_started_at,
                log_every_rollouts=5,
            )
            print(
                f"\n=== {stage_name}: {len(trajectories)} characters "
                f"(ppo={stage_timesteps}, bc={stage_bc_steps}) ===",
                flush=True,
            )
            model.learn(
                total_timesteps=stage_timesteps,
                callback=[checkpoint, reward_trace, progress],
                reset_num_timesteps=False,
                progress_bar=False,
            )
            model.save(stage_dir / "model")
            train_env.close()
            _plot_rewards(stage_dir, stage_dir / "train_logs")
            reward_trace.plot(stage_dir / "reward_curve.png")
            result = evaluate(
                model,
                all_entries,
                dataset,
                validation,
                stage_dir / "validation",
                ablation=args.ablation,
                seed=args.seed,
                motoya_font_path=exemplar_font,
                config=run_config,
            )
            passed, gate_failures = stage_gate(result)
            (stage_dir / "training.json").write_text(
                json.dumps(
                    {
                        "stage": stage_name,
                        "pool_size": len(trajectories),
                        "bc_loss": bc_loss,
                        "ppo_timesteps": stage_timesteps,
                        "bc_steps": stage_bc_steps,
                        "cumulative_timesteps": model.num_timesteps,
                        "validation": result,
                        "gate_passed": passed,
                        "gate_failures": gate_failures,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            completed_weight += stage_weight
            elapsed = datetime.now().timestamp() - run_started_at
            overall = completed_weight / total_weight
            remaining = (elapsed / max(overall, 1e-6)) - elapsed
            print(
                f"[progress] finished {stage_name}: beauty="
                f"{float(result['mean_beauty_score']):.2f} "
                f"overall={overall*100:.1f}% elapsed={_format_duration(elapsed)} "
                f"remaining~{_format_duration(remaining)}",
                flush=True,
            )
            if not passed and not args.allow_gate_failure:
                raise SystemExit(
                    f"Curriculum gate failed at {stage_name}: "
                    + ", ".join(gate_failures)
                )
        assert model is not None
        model.save(output / "final_model")
        progress_path.write_text(
            json.dumps(
                {
                    "updated_at": datetime.now().isoformat(timespec="seconds"),
                    "phase": "final_eval",
                    "eval_progress": "0/pending",
                    "overall_progress": 1.0,
                    "note": "PPO finished; running final evaluation (progress.json was PPO-only before this)",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    if args.train_only:
        if model is None:
            raise SystemExit("--train-only requires a trained or initial model")
        write_status_markdown(
            output,
            provenance,
            status="completed",
            summary="training-only checkpoint saved; external Gate screen pending",
            next_action="Run Gate 1 and Gate 2 safety screens before continuing.",
        )
        return

    final_indices = _sample_indices(tuple(range(len(entries))), args.eval_limit)
    final_indices = final_indices[args.eval_shard_index :: args.eval_shard_count]
    representative = tuple("一十水永書道飛龍鬱")
    if args.save_all_ink or args.eval_limit == 0:
        save_characters = tuple(entries[index].character for index in final_indices)
    else:
        save_characters = representative
    final = evaluate(
        model,
        entries,
        dataset,
        final_indices,
        output / "final",
        ablation=args.ablation,
        seed=args.seed,
        save_characters=save_characters,
        motoya_font_path=exemplar_font,
        progress_path=progress_path,
        layout_indices=eval_layouts,
        config=run_config,
    )
    pressure_calibration_summary = None
    if calibration_path is not None:
        calibration_data = json.loads(calibration_path.read_text(encoding="utf-8"))
        pressure_calibration_summary = {
            "schema_version": calibration_data["schema_version"],
            "cad_fingerprint": calibration_data["cad_fingerprint"],
            "brush_fingerprint": calibration_data["brush_fingerprint"],
            "provenance": calibration_data["provenance"],
            "file_sha256": hashlib.sha256(calibration_path.read_bytes()).hexdigest(),
        }
    (output / "summary.json").write_text(
        json.dumps(
            {
                "model": (
                    None
                    if model is None
                    else str(args.initial_model.expanduser().resolve())
                    if args.expert_only and args.initial_model
                    else str(output / "final_model.zip")
                ),
                "all_joyo_evaluated": len(final_indices) == len(entries),
                "evaluation_shard": {
                    "index": args.eval_shard_index,
                    "count": args.eval_shard_count,
                },
                "pressure_calibration": pressure_calibration_summary,
                "acceptance": {
                    "mean_at_least_75": float(final["mean_beauty_score"]) >= 75.0,
                    "mean_at_least_80": float(final["mean_beauty_score"]) >= 80.0,
                    "p10_at_least_80": float(final["p10_beauty_score"]) >= 80.0,
                    "minimum_at_least_60": float(final["minimum_beauty_score"]) >= 60.0,
                    "all_complete": float(final["success_rate"]) == 1.0,
                    "zero_drips": int(final["total_drips"]) == 0,
                    "zero_collisions": int(final["collision_count"]) == 0,
                },
                "evaluation": final,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    snapshot = snapshot_from_evaluation(final, source=str(output / "summary.json"))
    write_status_markdown(
        output,
        provenance,
        status="completed",
        summary=(
            f"beauty={snapshot.mean_beauty:.2f}, line_width={snapshot.line_width:.2f}, "
            f"brushwork={snapshot.brushwork:.2f}, safe={snapshot.safe}, "
            f"gates={snapshot.gates_passed}"
        ),
        next_action=(
            "If gates remain open, run shard evaluation then hard-mining resume "
            "with --hard-csv and --start-stage 9."
        ),
    )
    print(json.dumps(final, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
