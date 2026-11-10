"""Replay a trained PPO policy in the native MuJoCo Viewer or to MP4."""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from pathlib import Path
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import mujoco.viewer
import numpy as np
from stable_baselines3 import PPO

from so101_calligraphy.config import EnvConfig, ModuleConfig
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.trajectory.kanjivg import (
    RADICAL_STAGES,
    TECHNIQUE_STAGES,
    kanjivg_stage,
    load_kanjivg_character,
    load_kanjivg_stage,
)
from so101_calligraphy.trajectory.animcjk import enrich_with_animcjk_widths
from so101_calligraphy.trajectory.professional import MotoyaFontError


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="Stable-Baselines3 .zip model.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--task", choices=("line", "circle", "cross"), default="cross")
    source.add_argument("--svg", help="SVG used for training/evaluation.")
    source.add_argument("--kanji", help="Complete KanjiVG character used for training.")
    source.add_argument(
        "--kanjivg-stage",
        choices=tuple(stage.slug for stage in (*TECHNIQUE_STAGES, *RADICAL_STAGES)),
    )
    parser.add_argument(
        "--kanjivg-cache", type=Path, default=Path("data/kanjivg")
    )
    parser.add_argument("--animcjk-cache", type=Path, default=Path("data/animcjk"))
    parser.add_argument(
        "--no-animcjk",
        action="store_true",
        help="Replay generated widths instead of AnimCJK Japanese outlines.",
    )
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier.")
    parser.add_argument(
        "--stochastic",
        action="store_true",
        help="Sample rather than use PPO mean action.",
    )
    parser.add_argument(
        "--ik-assist",
        action="store_true",
        help="Use DLS nominal control plus the policy's residual joint commands.",
    )
    parser.add_argument(
        "--professional",
        action="store_true",
        help="Replay segmented brush, inkstone, reservoir ink, and professional brushwork.",
    )
    parser.add_argument(
        "--motoya-font",
        type=Path,
        help="Optional licensed S Motoya Seikaisho 5 ProN image teacher.",
    )
    parser.add_argument(
        "--no-exemplar",
        action="store_true",
        help="Replay professional brush physics without the image exemplar.",
    )
    parser.add_argument(
        "--save-ink",
        type=Path,
        help="Save the final A4 ink raster as a PNG.",
    )
    parser.add_argument(
        "--save-video",
        type=Path,
        help="Write an MP4 of the overview camera (headless; no Viewer window).",
    )
    parser.add_argument(
        "--video-fps",
        type=float,
        default=30.0,
        help="Output MP4 frame rate when --save-video is set.",
    )
    parser.add_argument(
        "--video-stride",
        type=int,
        default=2,
        help="Keep every Nth control step when writing MP4 (default 2).",
    )
    parser.add_argument(
        "--video-width",
        type=int,
        default=640,
        help="MP4 width in pixels (must fit the model offscreen framebuffer).",
    )
    parser.add_argument(
        "--video-height",
        type=int,
        default=480,
        help="MP4 height in pixels.",
    )
    parser.add_argument(
        "--no-viewer",
        action="store_true",
        help="Skip the interactive MuJoCo Viewer (implied by --save-video).",
    )
    return parser.parse_args()


def _open_video_writer(path: Path, *, fps: float, macro_block_size: int = 1):
    try:
        import imageio.v2 as imageio
    except ImportError as exc:  # pragma: no cover - exercised when optional dep missing
        raise SystemExit(
            "MP4 export requires imageio and imageio-ffmpeg. "
            'Install with: python -m pip install "imageio>=2.34" "imageio-ffmpeg>=0.5"'
        ) from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    return imageio.get_writer(
        path,
        fps=fps,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        macro_block_size=macro_block_size,
    )


def _print_episode(args: argparse.Namespace, episode: int, info: dict) -> None:
    print(
        f"episode={episode + 1} success={info['is_success']} "
        f"progress={info['progress']:.1%} "
        f"beauty={info['beauty_score']:.1f} "
        f"technique={info['technique']}"
    )
    if args.professional:
        breakdown = " ".join(
            f"{name}={score:.1f}" for name, score in info["beauty_components"].items()
        )
        print(
            f"ink core={info['core_ink']:.3f} "
            f"surface={info['surface_ink']:.3f} "
            f"drips={info['drip_count']} "
            f"collisions={','.join(info['collision_types']) or 'none'}"
        )
        print(breakdown)


def _save_ink_if_requested(
    args: argparse.Namespace, env: CalligraphyEnv, episode: int
) -> None:
    if not args.save_ink:
        return
    destination = args.save_ink.expanduser().resolve()
    if args.episodes > 1:
        destination = destination.with_stem(f"{destination.stem}-{episode + 1}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    plt.imsave(destination, env.ink.rgb_image())


def _iter_policy_frames(
    *,
    env: CalligraphyEnv,
    policy: PPO,
    episodes: int,
    stochastic: bool,
) -> Iterator[tuple[int, np.ndarray | None, dict, bool]]:
    """Yield (episode_index, observation, info, done) after each env step."""

    for episode in range(episodes):
        observation, info = env.reset(seed=episode)
        terminated = truncated = False
        while not (terminated or truncated):
            action, _ = policy.predict(observation, deterministic=not stochastic)
            observation, _, terminated, truncated, info = env.step(action)
            yield episode, observation, info, bool(terminated or truncated)


def main() -> None:
    args = _parse_args()
    if args.episodes <= 0 or args.speed <= 0:
        raise SystemExit("--episodes and --speed must be positive")
    if args.video_fps <= 0 or args.video_stride <= 0:
        raise SystemExit("--video-fps and --video-stride must be positive")
    if args.video_width < 16 or args.video_height < 16:
        raise SystemExit("--video-width/--video-height must be at least 16")
    model_path = args.model.expanduser().resolve()
    if not model_path.exists() and model_path.with_suffix(".zip").exists():
        model_path = model_path.with_suffix(".zip")
    if not model_path.is_file():
        raise SystemExit(f"Model not found: {model_path}")

    try:
        if args.kanji:
            trajectory = load_kanjivg_character(
                args.kanji, cache_dir=args.kanjivg_cache
            )
            if not args.no_animcjk:
                trajectory = enrich_with_animcjk_widths(
                    trajectory,
                    args.kanji,
                    cache_dir=args.animcjk_cache,
                    use_medians=args.professional,
                )
            task = f"kanji-{ord(args.kanji):05x}"
        elif args.kanjivg_stage:
            task = args.kanjivg_stage
            stage = kanjivg_stage(task)
            trajectory = load_kanjivg_stage(stage, cache_dir=args.kanjivg_cache)
            if not args.no_animcjk and stage.stroke_number is not None:
                trajectory = enrich_with_animcjk_widths(
                    trajectory,
                    stage.character,
                    stroke_numbers=(int(stage.stroke_number),),
                    cache_dir=args.animcjk_cache,
                    use_medians=args.professional,
                )
        else:
            task = args.task if args.svg is None else Path(args.svg).stem
            trajectory = None
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    professional_modules = (
        ModuleConfig(
            brush_physics="professional",
            ink_model="professional",
            brushwork="professional",
            inkstone=True,
        )
        if args.no_exemplar
        else ModuleConfig.professional()
    )
    record_video = args.save_video is not None
    use_viewer = not args.no_viewer and not record_video
    render_mode = "rgb_array" if record_video else None
    try:
        env = CalligraphyEnv(
            task=task,
            svg_path=args.svg,
            trajectory=trajectory,
            render_mode=render_mode,
            config=EnvConfig(
                ik_assist=args.ik_assist or args.professional,
                modules=professional_modules if args.professional else ModuleConfig(),
                motoya_font_path=(
                    str(args.motoya_font.expanduser()) if args.motoya_font else None
                ),
                observation_version=(
                    3 if args.professional and not args.no_exemplar
                    else 2 if args.professional
                    else None
                ),
                reset_noise=0.0,
            ),
        )
    except MotoyaFontError as exc:
        raise SystemExit(str(exc)) from exc
    if record_video and env._renderer is None:
        # Force renderer size before the first frame.
        env._renderer = mujoco.Renderer(
            env.model, height=args.video_height, width=args.video_width
        )
    policy = PPO.load(model_path, device="cpu")
    expected = policy.observation_space.shape
    if expected != env.observation_space.shape:
        env.close()
        raise SystemExit(
            f"Model expects observation {expected}, environment provides "
            f"{env.observation_space.shape}. Use the same professional/exemplar mode "
            "that was used during training."
        )
    frame_seconds = env.model.opt.timestep * env.config.frame_skip / args.speed
    camera_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_CAMERA, "overview")

    writer = None
    try:
        if record_video:
            assert args.save_video is not None
            video_path = args.save_video.expanduser().resolve()
            if args.episodes > 1:
                # One file; episodes are concatenated.
                pass
            writer = _open_video_writer(video_path, fps=args.video_fps)
            print(f"recording MP4 → {video_path}", flush=True)
            step_index = 0
            current_episode = -1
            info: dict = {}
            for episode, _observation, info, done in _iter_policy_frames(
                env=env,
                policy=policy,
                episodes=args.episodes,
                stochastic=args.stochastic,
            ):
                if episode != current_episode:
                    current_episode = episode
                    step_index = 0
                if step_index % args.video_stride == 0:
                    frame = env.render()
                    if frame is None:
                        raise SystemExit("rgb_array render returned no frame")
                    writer.append_data(np.asarray(frame, dtype=np.uint8))
                step_index += 1
                if done:
                    _print_episode(args, episode, info)
                    _save_ink_if_requested(args, env, episode)
            print(f"wrote {video_path}", flush=True)
            return

        if not use_viewer:
            info = {}
            for episode, _observation, info, done in _iter_policy_frames(
                env=env,
                policy=policy,
                episodes=args.episodes,
                stochastic=args.stochastic,
            ):
                if done:
                    _print_episode(args, episode, info)
                    _save_ink_if_requested(args, env, episode)
            return

        with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
            if camera_id >= 0:
                viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FIXED
                viewer.cam.fixedcamid = camera_id
            for episode in range(args.episodes):
                observation, info = env.reset(seed=episode)
                terminated = truncated = False
                while viewer.is_running() and not (terminated or truncated):
                    started = time.perf_counter()
                    action, _ = policy.predict(
                        observation, deterministic=not args.stochastic
                    )
                    observation, _, terminated, truncated, info = env.step(action)
                    env.ink.draw_mjv_scene(viewer.user_scn, clear=True)
                    viewer.sync()
                    remaining = frame_seconds - (time.perf_counter() - started)
                    if remaining > 0:
                        time.sleep(remaining)
                _print_episode(args, episode, info)
                _save_ink_if_requested(args, env, episode)
                if not viewer.is_running():
                    break
    finally:
        if writer is not None:
            writer.close()
        env.close()


if __name__ == "__main__":
    main()
