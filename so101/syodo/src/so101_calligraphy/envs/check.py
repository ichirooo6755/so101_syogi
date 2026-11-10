"""Command-line Gymnasium compliance check."""

from __future__ import annotations

import argparse

from gymnasium.utils.env_checker import check_env

from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("line", "circle", "cross"), default="line")
    parser.add_argument("--svg", help="Use an arbitrary SVG instead of a built-in task.")
    args = parser.parse_args()
    env = CalligraphyEnv(task=args.task, svg_path=args.svg)
    try:
        check_env(env, skip_render_check=True)
        print("Gymnasium environment check passed.")
    finally:
        env.close()


if __name__ == "__main__":
    main()
