#!/usr/bin/env python3
"""Compose visual-ab / brushwork-feedback / IK ceiling contact sheets."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _load(path: Path, character: str) -> Image.Image:
    code = f"{ord(character):05x}"
    for name in (f"{code}-{character}.png", f"{character}.png"):
        candidate = path / name
        if candidate.is_file():
            return Image.open(candidate).convert("RGB")
    raise FileNotFoundError(f"missing ink for {character!r} in {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visual-ab", type=Path, required=True)
    parser.add_argument("--brushwork-feedback", type=Path, required=True)
    parser.add_argument("--ik-ceiling", type=Path, required=True)
    parser.add_argument(
        "--labels",
        default="visual-ab,brushwork-feedback,IK ceiling",
        help="Comma-separated lane labels (3 values).",
    )
    parser.add_argument(
        "--characters",
        default="一十書水永竜道飛鬱田園央案支誠措八拷砕",
    )
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--columns", type=int, default=4)
    args = parser.parse_args()

    chars = tuple(args.characters)
    labels = tuple(part.strip() for part in args.labels.split(","))
    if len(labels) != 3:
        raise SystemExit("--labels must contain exactly 3 comma-separated names")
    dirs = (args.visual_ab, args.brushwork_feedback, args.ik_ceiling)
    cell_w, cell_h = 220, 260
    pad = 8
    header_h = 24
    cols = args.columns
    rows = (len(chars) + cols - 1) // cols
    width = cols * (cell_w + pad) + pad
    height = header_h + rows * (len(labels) * cell_h + pad) + pad
    canvas = Image.new("RGB", (width, height), "#f5f2ea")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
    except OSError:
        font = ImageFont.load_default()

    for index, character in enumerate(chars):
        row, col = divmod(index, cols)
        x0 = pad + col * (cell_w + pad)
        y0 = header_h + pad + row * (len(labels) * cell_h + pad)
        for lane, (label, directory) in enumerate(zip(labels, dirs, strict=True)):
            y = y0 + lane * cell_h
            ink_dir = directory / "ink"
            image = _load(ink_dir, character)
            scale = min((cell_w - 12) / image.width, (cell_h - 36) / image.height)
            resized = image.resize(
                (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
                Image.Resampling.LANCZOS,
            )
            ix = x0 + (cell_w - resized.width) // 2
            iy = y + 18 + (cell_h - 36 - resized.height) // 2
            canvas.paste(resized, (ix, iy))
            draw.rectangle((x0, y, x0 + cell_w - 1, y + cell_h - 1), outline="#aaa59a")
            draw.text((x0 + 4, y + 2), f"{character} · {label}", fill="#333", font=font)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, format="PNG")
    print(f"wrote {args.output} ({len(chars)} chars × {len(labels)} lanes)")


if __name__ == "__main__":
    main()
