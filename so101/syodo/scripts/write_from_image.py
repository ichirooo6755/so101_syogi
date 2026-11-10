"""画像に書かれた文字を認識し、その大きさと位置のまま書道で書く。

例:
  python scripts/write_from_image.py --image photo.png --output /tmp/out.png
  python scripts/write_from_image.py --image photo.png --candidates 山川田
"""

from __future__ import annotations

import argparse
import json
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
from so101_calligraphy.trajectory.image_layout import layout_from_image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument(
        "--candidates",
        default="",
        help="照合する字を絞る（省略時は常用漢字 2136 字すべて。遅い）",
    )
    parser.add_argument("--model", type=Path, default=None, help="省略時は IK 天井")
    parser.add_argument("--output", type=Path, default=Path("/tmp/written.png"))
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    entries = load_joyo_kanji(Path("data/kanjidic2"))
    dataset = lazy_joyo_trajectories(
        entries,
        kanjivg_cache=Path("data/kanjivg"),
        animcjk_cache=Path("data/animcjk"),
        use_animcjk_medians=True,
    )
    index_of = {entry.character: i for i, entry in enumerate(entries)}
    candidates = args.candidates or "".join(index_of)
    font = Path(Path("runs/selected-exemplar-font.txt").read_text().strip())
    config = professional_config("all", motoya_font_path=font)

    # 認識に使う字だけ軌道を用意する（全字を読むと重い）
    by_character = {c: dataset[index_of[c]] for c in candidates if c in index_of}
    sheet, report = layout_from_image(
        Image.open(args.image),
        by_character,
        config.paper,
        candidates=candidates,
        font_path=font,
    )
    print(f"認識 {len(report)} 字:")
    for item in report:
        print(f"  {item['character']}  一致度 {item['score']:.3f}  "
              f"中心 {item['center_mm']} mm  大きさ {item['size_mm']} mm"
              + (f"  次点 {item['alternatives']}" if item["alternatives"] else ""))
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    env = CalligraphyEnv(task="image-sheet", trajectory=sheet, config=config)
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
        if terminated or truncated or steps > 40000:
            break
    print(f"{len(sheet.strokes)}画 {steps}ステップ 完筆={bool(info['is_success'])}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(
        (255 * (1.0 - np.clip(env.ink.pigment, 0.0, 1.0))).astype(np.uint8)
    ).save(args.output)
    print(f"-> {args.output}")
    env.close()


if __name__ == "__main__":
    main()
