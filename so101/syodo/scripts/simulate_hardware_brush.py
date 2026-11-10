#!/usr/bin/env python3
"""Replay a saved hardware path with flexible hair and paper contact, offline."""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from scripts.hardware_write import _validate_trace_data
from so101_calligraphy.brush_replay import ReplayParameters, replay_brush
from so101_calligraphy.hardware_desk import DEFAULT_DESK_PATH, desk_fingerprint, env_config_from_desk, load_desk


def save_replay(out: Path, summary: dict, arrays: dict, rgb: np.ndarray, *, animation=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    np.savez_compressed(out / "dynamics.npz", **arrays)
    # Match the path plot: paper +X is up, +Y is right.
    paper_view = rgb.transpose(1, 0, 2)[::-1, ::-1]
    Image.fromarray(np.round(np.clip(paper_view, 0, 1) * 255).astype(np.uint8)).save(out / "ink.png")
    scalar_keys = [k for k, v in arrays.items() if v.ndim == 1]
    vectors = {key: arrays[key] for key in ("expected", "rest", "tip", "contact_point", "deflection", "terminal_axis")}
    headers = scalar_keys + [f"{key}_{axis}" for key in vectors for axis in "xyz"]
    with (out / "dynamics.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        for i in range(len(arrays["time_s"])):
            values = [arrays[k][i] for k in scalar_keys] + [x for v in vectors.values() for x in v[i]]
            writer.writerow(["" if isinstance(x, (float, np.floating)) and not np.isfinite(x) else x for x in values])
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), layout="constrained")
    target = arrays["expected"].copy() * 1000
    target[~arrays["pen_down"]] = np.nan
    contact = arrays["contact_point"] * 1000
    axes[0].plot(target[:, 1], target[:, 0], color="#555555", lw=.7, ls="--", label="Intended path")
    axes[0].plot(contact[:, 1], contact[:, 0], color="#bb4e3c", lw=.9, label="Simulated contact")
    axes[0].set(xlabel="Paper Y (mm)", ylabel="Paper X (mm)", title="Contact path", aspect="equal")
    axes[0].legend(fontsize=8)
    axes[1].imshow(paper_view)
    axes[1].axis("off")
    axes[1].set_title("Predicted ink (uncalibrated)")
    time = arrays["time_s"]
    axes[2].plot(time, np.linalg.norm(arrays["deflection"], axis=1) * 1000, color="#197970", lw=.7)
    axes[2].set(xlabel="Time (s)", ylabel="Tuft deflection (mm)", title="Hair movement / contact")
    force_ax = axes[2].twinx()
    force_ax.plot(time, arrays["force_n"], color="#bb4e3c", lw=.5, alpha=.7)
    force_ax.set_ylabel("Contact force (N)")
    for ax in (axes[0], axes[2]):
        ax.grid(alpha=.15)
    fig.suptitle("Flexible brush simulation — material and ink parameters unmeasured", fontsize=13)
    fig.savefig(out / "motion.png", dpi=150)
    plt.close(fig)
    if animation:
        fig, (xy, side) = plt.subplots(1, 2, figsize=(8, 4), layout="constrained")
        xy.plot(target[:, 1], target[:, 0], color="#999999", lw=.6)
        trail, = xy.plot([], [], color="#bb4e3c", lw=1)
        chain_xy, = xy.plot([], [], "o-", color="#197970", lw=2, ms=3)
        xy.set(xlabel="Paper Y (mm)", ylabel="Paper X (mm)", aspect="equal")
        chains = arrays["chain"] * 1000
        z0 = float(summary["paper_surface_z_m"]) * 1000
        side.axhline(z0, color="#999999", lw=1)
        chain_side, = side.plot([], [], "o-", color="#197970", lw=3, ms=4)
        side.set(xlim=(chains[:, :, 0].min() - 5, chains[:, :, 0].max() + 5),
                 ylim=(min(z0 - 10, chains[:, :, 2].min() - 5), chains[:, :, 2].max() + 5),
                 xlabel="Paper X (mm)", ylabel="Height Z (mm)", aspect="equal")
        for ax in (xy, side):
            ax.grid(alpha=.15)
        label = fig.suptitle("Simulation only")
        frames = []
        for i in np.linspace(0, len(time) - 1, min(120, len(time)), dtype=int):
            trail.set_data(contact[:i + 1, 1], contact[:i + 1, 0])
            chain_xy.set_data(chains[i, :, 1], chains[i, :, 0])
            chain_side.set_data(chains[i, :, 0], chains[i, :, 2])
            label.set_text(f"Uncalibrated simulation | {time[i]:.1f} s | contact {arrays['force_n'][i]:.2f} N")
            fig.canvas.draw()
            frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert("RGB"))
        frames[0].save(out / "brush-motion.gif", save_all=True, append_images=frames[1:], duration=80, loop=0)
        plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--desk", type=Path, default=DEFAULT_DESK_PATH)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--speed", type=float, default=1.5)
    parser.add_argument("--timestep", type=float, default=.001)
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Compare stiffness from 0.5x to 50x and lower/higher friction",
    )
    parser.add_argument("--animation", action="store_true")
    args = parser.parse_args(argv)
    if not np.isfinite(args.speed) or args.speed <= 0:
        parser.error("speed must be finite and positive")
    desk = load_desk(args.desk)
    with np.load(args.trace, allow_pickle=False) as data:
        _validate_trace_data(data, desk, False)
        qpos, targets, down = (data[k].copy() for k in ("qpos", "expected_tip_xyz", "pen_down"))
        period = float(data["dt"]) / args.speed
        word = str(data["kanji"].item())
    params = ReplayParameters(timestep_s=args.timestep)
    cases = {"nominal": params}
    if args.sweep:
        cases.update(
            half_timestep=replace(params, timestep_s=params.timestep_s / 2),
            soft=replace(params, stiffness_scale=.5),
            stiff=replace(params, stiffness_scale=2.),
            stiff_10x=replace(params, stiffness_scale=10.),
            stiff_50x=replace(params, stiffness_scale=50.),
            low_friction=replace(params, friction_scale=.5),
            high_friction=replace(params, friction_scale=1.5),
        )
    results = []
    for name, values in cases.items():
        summary, arrays, rgb = replay_brush(env_config_from_desk(desk), qpos, targets, down, period, parameters=values)
        summary.update(word=word, scenario=name, trace_sha256=hashlib.sha256(args.trace.read_bytes()).hexdigest(),
                       desk_fingerprint=desk_fingerprint(desk), paper_surface_z_m=float(desk["paper"]["surface_z"]), speed=args.speed)
        save_replay(args.out / name, summary, arrays, rgb, animation=args.animation and name == "nominal")
        results.append(summary)
        m = summary["metrics"]
        missed = m["missed_contact_fraction"]
        missed_text = f"{missed:.1%}" if missed is not None else "接地指令なし"
        print(f"{word} {name}: 接触不足={missed_text}, 最大たわみ={m['deflection_max_mm']:.1f} mm, 最大力={m['force_peak_n']:.3f} N（未較正シミュレーション）", flush=True)
    (args.out / "summary.json").write_text(json.dumps({"physical_writing_verified": False, "results": results}, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
