"""複数の字を一枚に配置して書かせ、画像に出す。

例:
  python scripts/render_sheet.py --text 一二三 --output /tmp/sheet.png
  python scripts/render_sheet.py --text 春夏秋冬 --rows 2 --columns 2
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "src")

from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.training.professional import professional_config
from so101_calligraphy.trajectory.education import (
    lazy_joyo_trajectories,
    load_joyo_kanji,
)
from so101_calligraphy.trajectory.layout import compose_sheet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="書く文字列")
    parser.add_argument("--rows", type=int, default=None)
    parser.add_argument("--columns", type=int, default=None)
    parser.add_argument("--horizontal", action="store_true", help="横書き")
    parser.add_argument("--cell-margin", type=float, default=0.10)
    parser.add_argument("--model", type=Path, default=None, help="省略時は IK 天井")
    parser.add_argument("--output", type=Path, default=Path("/tmp/sheet.png"))
    args = parser.parse_args()

    entries = load_joyo_kanji(Path("data/kanjidic2"))
    index_of = {entry.character: i for i, entry in enumerate(entries)}
    missing = [c for c in args.text if c not in index_of]
    if missing:
        raise SystemExit(f"常用漢字にない字: {''.join(missing)}")
    font = Path(Path("runs/selected-exemplar-font.txt").read_text().strip())
    config = professional_config("all", motoya_font_path=font)
    dataset = lazy_joyo_trajectories(
        entries,
        kanjivg_cache=Path("data/kanjivg"),
        animcjk_cache=Path("data/animcjk"),
        use_animcjk_medians=True,
        spacing=config.path_spacing,
    )
    sheet = compose_sheet(
        [dataset[index_of[c]] for c in args.text],
        config.paper,
        rows=args.rows,
        columns=args.columns,
        cell_margin_ratio=args.cell_margin,
        vertical=not args.horizontal,
    )
    # 合成した紙面はお手本マスクを持てない（1 字ではないため）。
    env = CalligraphyEnv(task="sheet", trajectory=sheet, config=config)
    model = None
    if args.model is not None:
        from stable_baselines3 import PPO

        model = PPO.load(args.model, device="cpu")
    observation, _ = env.reset(seed=17)
    steps = 0
    while True:
        steps += 1
        action = (
            np.zeros(6, dtype=np.float32)
            if model is None
            else model.predict(observation, deterministic=True)[0]
        )
        observation, _, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
    ink = env.ink.pigment
    paper = config.paper
    print(f"{args.text}  {len(sheet.strokes)}画  {steps}ステップ  "
          f"完筆={bool(info['is_success'])}")
    image = (255 * (1.0 - np.clip(ink, 0.0, 1.0))).astype(np.uint8)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(args.output)
    print(f"-> {args.output}  ({paper.width*1000:.0f}x{paper.height*1000:.0f} mm)")
    env.close()


if __name__ == "__main__":
    main()
