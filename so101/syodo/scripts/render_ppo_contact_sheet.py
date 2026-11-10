#!/usr/bin/env python3
"""Render a labelled contact sheet from a PPO evaluation directory."""

from __future__ import annotations

import argparse
import csv
import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DEFAULT_REPRESENTATIVES = ("一", "十", "書", "水", "永", "竜", "道", "飛", "鬱")
DEFAULT_BEAUTY_QUANTILES = (0.0, 0.25, 0.5, 0.75, 1.0)
REQUIRED_COLUMNS = {
    "character",
    "grade",
    "beauty_score",
    "line_width",
    "brushwork",
}

Row = dict[str, str]


class ContactSheetError(ValueError):
    """Raised for invalid evaluation data or missing input images."""


def load_character_rows(csv_path: Path) -> list[Row]:
    """Load and validate character metrics without consulting image files."""

    if not csv_path.is_file():
        raise ContactSheetError(f"characters.csv が見つかりません: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise ContactSheetError(
                "characters.csv に必要な列がありません: " + ", ".join(sorted(missing))
            )
        rows = [dict(row) for row in reader]

    if not rows:
        raise ContactSheetError(f"characters.csv にデータ行がありません: {csv_path}")

    seen: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        character = row["character"].strip()
        if not character:
            raise ContactSheetError(f"characters.csv {line_number}行目のcharacterが空です")
        if character in seen:
            raise ContactSheetError(
                f"characters.csv にcharacterの重複があります: {character!r}"
            )
        seen.add(character)
        row["character"] = character
        for column in ("beauty_score", "line_width", "brushwork"):
            try:
                value = float(row[column])
            except (TypeError, ValueError) as exc:
                raise ContactSheetError(
                    f"characters.csv {line_number}行目の{column}が数値ではありません: "
                    f"{row[column]!r}"
                ) from exc
            if not math.isfinite(value):
                raise ContactSheetError(
                    f"characters.csv {line_number}行目の{column}が有限値ではありません"
                )
    return rows


def _quantile_rows(
    rows: Sequence[Row],
    quantiles: Sequence[float],
    *,
    metric: str = "beauty_score",
) -> list[Row]:
    if not rows or not quantiles:
        return []
    ordered = sorted(rows, key=lambda row: (float(row[metric]), row["character"]))
    selected: list[Row] = []
    for quantile in quantiles:
        if not 0.0 <= quantile <= 1.0:
            raise ContactSheetError(
                f"beauty分位は0以上1以下で指定してください: {quantile}"
            )
        position = quantile * (len(ordered) - 1)
        index = int(math.floor(position + 0.5))
        selected.append(ordered[index])
    return selected


def _grade_sort_key(grade: str) -> tuple[int, float | str]:
    try:
        return (0, float(grade))
    except ValueError:
        return (1, grade)


def select_rows(
    rows: Sequence[Row],
    *,
    representatives: Sequence[str] = DEFAULT_REPRESENTATIVES,
    grade_per_stratum: int = 1,
    beauty_quantiles: Sequence[float] = DEFAULT_BEAUTY_QUANTILES,
    weakest_count: int = 1,
    weakest_metrics: Sequence[str] = ("brushwork", "line_width"),
) -> list[Row]:
    """Select the ordered union of all strategies, independently of images."""

    if grade_per_stratum < 0:
        raise ContactSheetError("grade_per_stratum は0以上で指定してください")
    if weakest_count < 0:
        raise ContactSheetError("weakest_count は0以上で指定してください")
    if not rows:
        return []

    by_character = {row["character"]: row for row in rows}
    candidates: list[Row] = [
        by_character[character]
        for character in representatives
        if character in by_character
    ]

    if grade_per_stratum:
        strata: dict[str, list[Row]] = {}
        for row in rows:
            strata.setdefault(row["grade"].strip(), []).append(row)
        grade_quantiles = tuple(
            (index + 0.5) / grade_per_stratum
            for index in range(grade_per_stratum)
        )
        for grade in sorted(strata, key=_grade_sort_key):
            candidates.extend(_quantile_rows(strata[grade], grade_quantiles))

    candidates.extend(_quantile_rows(rows, beauty_quantiles))
    for metric in weakest_metrics:
        for row in rows:
            try:
                value = float(row[metric])
            except (KeyError, TypeError, ValueError) as exc:
                raise ContactSheetError(f"{row['character']}: {metric} が数値ではありません") from exc
            if not math.isfinite(value):
                raise ContactSheetError(f"{row['character']}: {metric} が有限値ではありません")
        candidates.extend(
            sorted(
                rows,
                key=lambda row: (float(row[metric]), row["character"]),
            )[:weakest_count]
        )

    selected: list[Row] = []
    seen: set[str] = set()
    for row in candidates:
        if row["character"] not in seen:
            selected.append(row)
            seen.add(row["character"])
    return selected


def _choose_image_directory(evaluation_dir: Path, source: str) -> Path:
    if source != "auto":
        directory = evaluation_dir / source
        if not directory.is_dir():
            raise ContactSheetError(f"画像ディレクトリが見つかりません: {directory}")
        return directory
    for name in ("ink", "comparisons"):
        directory = evaluation_dir / name
        if directory.is_dir():
            return directory
    raise ContactSheetError(
        f"ink/ または comparisons/ が見つかりません: {evaluation_dir}"
    )


def _image_for_character(image_dir: Path, character: str) -> Path | None:
    codepoint = f"{ord(character):05x}" if len(character) == 1 else None
    names = [f"{character}.png"]
    if codepoint is not None:
        names = [
            f"{codepoint}-{character}.png",
            f"{codepoint}.png",
            *names,
        ]
    for name in names:
        candidate = image_dir / name
        if candidate.is_file():
            return candidate
    if codepoint is not None:
        matches = sorted(image_dir.glob(f"{codepoint}-*.png"))
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ContactSheetError(
                f"{character!r} の画像候補が複数あります: "
                + ", ".join(path.name for path in matches)
            )
    return None


def resolve_images(
    rows: Sequence[Row], evaluation_dir: Path, source: str = "auto"
) -> list[tuple[Row, Path]]:
    """Resolve every selected row to one PNG, reporting all missing images."""

    image_dir = _choose_image_directory(evaluation_dir, source)
    resolved: list[tuple[Row, Path]] = []
    missing: list[str] = []
    for row in rows:
        image_path = _image_for_character(image_dir, row["character"])
        if image_path is None:
            missing.append(row["character"])
        else:
            resolved.append((row, image_path))
    if missing:
        raise ContactSheetError(
            f"{image_dir} に選択文字のPNGがありません: " + "、".join(missing)
        )
    return resolved


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _draw_label(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    row: Mapping[str, str],
    font: ImageFont.ImageFont,
) -> None:
    text = (
        f"字: {row['character']}  beauty: {float(row['beauty_score']):.1f}\n"
        f"line_width: {float(row['line_width']):.1f}  "
        f"brushwork: {float(row['brushwork']):.1f}"
    )
    if "glyph_shape" in row and "exemplar_mask_iou" in row:
        text += (
            f"\nglyph: {float(row['glyph_shape']):.1f}  "
            f"IoU: {float(row['exemplar_mask_iou']):.1f}"
        )
    try:
        draw.multiline_text(position, text, fill="#151515", font=font, spacing=4)
    except UnicodeEncodeError:
        character = row["character"]
        escaped = " ".join(f"U+{ord(value):04X}" for value in character)
        draw.multiline_text(
            position,
            text.replace(f"字: {character}", f"char: {escaped}"),
            fill="#151515",
            font=font,
            spacing=4,
        )


def render_contact_sheet(
    items: Sequence[tuple[Row, Path]],
    output_path: Path,
    *,
    columns: int = 4,
    cell_width: int = 520,
    cell_height: int = 520,
) -> Path:
    """Render resolved images and four requested labels to a PNG grid."""

    if not items:
        raise ContactSheetError("contact sheetへ描画する項目がありません")
    if columns <= 0:
        raise ContactSheetError("columns は1以上で指定してください")
    if cell_width < 100 or cell_height < 140:
        raise ContactSheetError("cell幅は100以上、高さは140以上で指定してください")

    padding = 16
    label_height = 86 if any("glyph_shape" in row and "exemplar_mask_iou" in row for row, _ in items) else 62
    rows_count = math.ceil(len(items) / columns)
    canvas = Image.new(
        "RGB",
        (columns * cell_width, rows_count * cell_height),
        "#eeeae0",
    )
    font = _load_font(18)
    draw = ImageDraw.Draw(canvas)

    for index, (row, image_path) in enumerate(items):
        column = index % columns
        grid_row = index // columns
        left = column * cell_width
        top = grid_row * cell_height
        image_box = (
            cell_width - 2 * padding,
            cell_height - label_height - 2 * padding,
        )
        try:
            with Image.open(image_path) as source:
                image = source.convert("RGB")
                image.thumbnail(image_box, Image.Resampling.LANCZOS)
        except (OSError, ValueError) as exc:
            raise ContactSheetError(f"PNGを読み込めません: {image_path}: {exc}") from exc
        image_left = left + (cell_width - image.width) // 2
        image_top = top + padding + max(0, (image_box[1] - image.height) // 2)
        canvas.paste(image, (image_left, image_top))
        draw.rectangle(
            (left, top, left + cell_width - 1, top + cell_height - 1),
            outline="#aaa59a",
            width=1,
        )
        _draw_label(
            draw,
            (left + padding, top + cell_height - label_height),
            row,
            font,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG")
    return output_path


def _parse_representatives(value: str) -> tuple[str, ...]:
    if not value.strip():
        return ()
    if "," in value:
        return tuple(part.strip() for part in value.split(",") if part.strip())
    return tuple(value.strip())


def _parse_quantiles(value: str) -> tuple[float, ...]:
    if not value.strip():
        return ()
    try:
        return tuple(float(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "分位はカンマ区切りの数値で指定してください"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "PPO評価の固定代表・学年層・beauty分位・弱点文字をまとめて"
            "contact sheetへ描画します。"
        )
    )
    parser.add_argument("evaluation_dir", type=Path, help="characters.csvがある評価dir")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="出力PNG（既定: <evaluation_dir>/contact-sheet.png）",
    )
    parser.add_argument("--columns", type=int, default=4, help="グリッド列数")
    parser.add_argument(
        "--image-source",
        choices=("auto", "ink", "comparisons"),
        default="auto",
        help="PNGの入力サブディレクトリ（autoはink優先）",
    )
    parser.add_argument(
        "--representatives",
        default=",".join(DEFAULT_REPRESENTATIVES),
        help="固定代表文字（カンマ区切り、または連続した1文字ずつ）",
    )
    parser.add_argument(
        "--grade-per-stratum",
        type=int,
        default=1,
        help="各学年からbeauty分位で選ぶ件数（0で無効）",
    )
    parser.add_argument(
        "--beauty-quantiles",
        type=_parse_quantiles,
        default=DEFAULT_BEAUTY_QUANTILES,
        help="全体から選ぶbeauty分位（既定: 0,.25,.5,.75,1、空で無効）",
    )
    parser.add_argument(
        "--weakest-count",
        type=int,
        default=1,
        help="brushworkとline_widthの下位から各々選ぶ件数（0で無効）",
    )
    parser.add_argument(
        "--weakest-metrics",
        default="brushwork,line_width",
        help="下位を選ぶ列（例: glyph_shape,exemplar_mask_iou）",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="画像が無い文字は飛ばして存在する分だけでシートを作る",
    )
    parser.add_argument("--cell-width", type=int, default=520)
    parser.add_argument("--cell-height", type=int, default=520)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    evaluation_dir = args.evaluation_dir.resolve()
    output = (
        args.output.resolve()
        if args.output is not None
        else evaluation_dir / "contact-sheet.png"
    )
    try:
        rows = load_character_rows(evaluation_dir / "characters.csv")
        selected = select_rows(
            rows,
            representatives=_parse_representatives(args.representatives),
            grade_per_stratum=args.grade_per_stratum,
            beauty_quantiles=args.beauty_quantiles,
            weakest_count=args.weakest_count,
            weakest_metrics=tuple(part.strip() for part in args.weakest_metrics.split(",") if part.strip()),
        )
        if args.allow_missing:
            image_dir = _choose_image_directory(evaluation_dir, args.image_source)
            items = []
            skipped: list[str] = []
            for row in selected:
                image_path = _image_for_character(image_dir, row["character"])
                if image_path is None:
                    skipped.append(row["character"])
                else:
                    items.append((row, image_path))
            if not items:
                raise ContactSheetError(
                    f"{image_dir} に選択文字のPNGが1枚もありません"
                    + (f"（欠落: {'、'.join(skipped)}）" if skipped else "")
                )
            if skipped:
                print("skip missing:", "、".join(skipped), flush=True)
        else:
            items = resolve_images(selected, evaluation_dir, args.image_source)
        render_contact_sheet(
            items,
            output,
            columns=args.columns,
            cell_width=args.cell_width,
            cell_height=args.cell_height,
        )
    except ContactSheetError as exc:
        parser.error(str(exc))
    print(f"{output} ({len(items)}文字)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
