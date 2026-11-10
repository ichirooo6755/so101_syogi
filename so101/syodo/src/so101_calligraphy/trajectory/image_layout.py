"""画像に書かれた文字を読み取り、その大きさと位置のまま書く。

外部の OCR に頼らず、既にお手本用に持っているフォント字形マスク
(`_raw_glyph_mask`) をテンプレートとして照合する。手本と同じ土俵で比べるので
依存が増えず、認識に使った字形をそのまま書字目標に流用できる。

手順:
  1. 画像を二値化し、連結成分から文字らしい塊を切り出す
  2. 各塊を常用漢字のフォント字形と照合して字を決める
  3. 画像内の位置と大きさを紙面座標へ写し、その桝目に配置する
"""

from __future__ import annotations

from dataclasses import replace
import numpy as np
from PIL import Image
from scipy import ndimage

from so101_calligraphy.config import PaperConfig
from so101_calligraphy.trajectory.layout import place_in_cell
from so101_calligraphy.trajectory.professional import (
    _raw_glyph_mask,
    resolve_exemplar_font,
)
from so101_calligraphy.trajectory.types import Trajectory


def binarize(image: Image.Image, *, invert: bool | None = None) -> np.ndarray:
    """文字が True になる二値画像。明暗はどちらでも受ける。"""

    gray = np.asarray(image.convert("L"), dtype=np.float64) / 255.0
    # 大津の方法
    hist, edges = np.histogram(gray, bins=256, range=(0.0, 1.0))
    total = hist.sum()
    if total == 0:
        raise ValueError("画像が空です。")
    weight = np.cumsum(hist)
    mean = np.cumsum(hist * (edges[:-1] + edges[1:]) * 0.5)
    valid = (weight > 0) & (total - weight > 0)
    between = np.zeros(256)
    between[valid] = (
        (mean[valid] / weight[valid] - (mean[-1] - mean[valid]) / (total - weight[valid])) ** 2
        * weight[valid] * (total - weight[valid])
    )
    threshold = float((edges[:-1] + edges[1:])[int(between.argmax())] * 0.5)
    dark = gray <= threshold
    if invert is None:
        # 少数派を文字とみなす（紙に墨で書かれている想定）
        invert = dark.mean() > 0.5
    return ~dark if invert else dark


def find_glyph_boxes(
    mask: np.ndarray,
    *,
    minimum_area_ratio: float = 0.0006,
    merge_gap_ratio: float = 0.22,
) -> list[tuple[int, int, int, int]]:
    """文字ごとの外接矩形 (row0, row1, col0, col1) を返す。

    偏と旁のように 1 字が複数の連結成分に割れるため、近い成分は束ねる。
    """

    labels, count = ndimage.label(mask)
    if count == 0:
        return []
    boxes = []
    minimum = minimum_area_ratio * mask.size
    for row_slice, column_slice in ndimage.find_objects(labels):
        area = (row_slice.stop - row_slice.start) * (column_slice.stop - column_slice.start)
        if area >= minimum:
            boxes.append([row_slice.start, row_slice.stop,
                          column_slice.start, column_slice.stop])
    if not boxes:
        return []
    # 大きさの目安から結合距離を決める
    sizes = [max(b[1] - b[0], b[3] - b[2]) for b in boxes]
    gap = merge_gap_ratio * float(np.median(sizes))
    merged = True
    while merged:
        merged = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                row_gap = max(a[0] - b[1], b[0] - a[1], 0)
                col_gap = max(a[2] - b[3], b[2] - a[3], 0)
                if row_gap <= gap and col_gap <= gap:
                    boxes[i] = [min(a[0], b[0]), max(a[1], b[1]),
                                min(a[2], b[2]), max(a[3], b[3])]
                    boxes.pop(j)
                    merged = True
                    break
            if merged:
                break
    return [tuple(b) for b in boxes]


def _normalize(patch: np.ndarray, size: int = 64) -> np.ndarray:
    """外接矩形で切り、**縦横比を保ったまま**正方形の枠に収める（照合用）。

    正方形へ引き伸ばすと縦横比の情報が失われ、山と出、田と回のように
    輪郭が似た字を取り違える。書の字形は縦横比そのものが特徴なので保つ。
    """

    rows, columns = np.nonzero(patch)
    if len(rows) == 0:
        return np.zeros((size, size), dtype=np.float64)
    cropped = patch[rows.min(): rows.max() + 1, columns.min(): columns.max() + 1]
    height, width = cropped.shape
    scale = (size - 2) / max(height, width)
    new_h = max(1, int(round(height * scale)))
    new_w = max(1, int(round(width * scale)))
    image = Image.fromarray((cropped * 255).astype(np.uint8)).resize(
        (new_w, new_h), Image.Resampling.LANCZOS
    )
    canvas = np.zeros((size, size), dtype=np.float64)
    row0 = (size - new_h) // 2
    column0 = (size - new_w) // 2
    canvas[row0:row0 + new_h, column0:column0 + new_w] = (
        np.asarray(image, dtype=np.float64) / 255.0
    )
    return canvas


def _hole_signature(normalized: np.ndarray, threshold: float = 0.45) -> int:
    """筆画に囲まれた白（布白）の数。田は 4、目は 3、山は 0。

    書体が変わっても位相は変わらないので、書体差に強い手がかりになる。
    """

    solid = normalized >= threshold
    if not solid.any():
        return 0
    labels, count = ndimage.label(~solid, structure=np.array(
        [[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.int8
    ))
    if count == 0:
        return 0
    border = set(labels[0, :]) | set(labels[-1, :])
    border |= set(labels[:, 0]) | set(labels[:, -1])
    border.discard(0)
    areas = np.bincount(labels.ravel(), minlength=count + 1)
    minimum = 0.004 * normalized.size
    return int(sum(
        1 for i in range(1, count + 1)
        if i not in border and areas[i] >= minimum
    ))


def recognize(
    patch: np.ndarray,
    candidates: str,
    font_path,
    *,
    top: int = 1,
    size: int = 64,
) -> list[tuple[str, float]]:
    """フォント字形との重なりで字を当てる。上位 ``top`` 件を返す。"""

    target = _normalize(patch, size)
    scores: list[tuple[str, float]] = []
    for character in candidates:
        try:
            glyph = _raw_glyph_mask(character, font_path)
        except Exception:
            continue
        reference = _normalize(np.asarray(glyph, dtype=np.float64) >= 0.5, size)
        intersection = float(np.minimum(target, reference).sum())
        union = float(np.maximum(target, reference).sum())
        iou = intersection / max(union, 1e-9)
        # 書体差（入力がゴシック、手本が楷書など）で線幅も細部も違うので、
        # 画素の重なりだけでは足りない。字の骨格が同じかを見る指標を足す。
        #   1. 粗いブロック平均: 墨の分布が似ているか
        #   2. 白（布白）の位相: 囲まれた空白の数と配置が合うか
        #   3. 投影: 行方向・列方向の墨の量の分布
        block = 8
        step = size // block
        coarse_t = target.reshape(block, step, block, step).mean((1, 3))
        coarse_r = reference.reshape(block, step, block, step).mean((1, 3))
        coarse = 1.0 - float(np.mean(np.abs(coarse_t - coarse_r)))
        holes_t = _hole_signature(target)
        holes_r = _hole_signature(reference)
        holes = 1.0 / (1.0 + abs(holes_t - holes_r))
        row_t = target.mean(axis=1); row_r = reference.mean(axis=1)
        col_t = target.mean(axis=0); col_r = reference.mean(axis=0)
        span = max(float(row_t.max()), float(row_r.max()),
                   float(col_t.max()), float(col_r.max()), 1e-9)
        projection = 1.0 - 0.5 * (
            float(np.mean(np.abs(row_t - row_r))) + float(np.mean(np.abs(col_t - col_r)))
        ) / span
        # 上下・左右の重心も見る。山と出のように「下に一画足しただけ」の関係は
        # 墨の重心が縦にずれるので、これが決め手になる。
        grid = np.arange(size, dtype=np.float64)
        def centroid(image: np.ndarray) -> tuple[float, float]:
            total = float(image.sum()) or 1e-9
            return (
                float((image.sum(axis=1) * grid).sum()) / total / size,
                float((image.sum(axis=0) * grid).sum()) / total / size,
            )
        cy_t, cx_t = centroid(target)
        cy_r, cx_r = centroid(reference)
        balance = 1.0 - min(1.0, 3.2 * (abs(cy_t - cy_r) + abs(cx_t - cx_r)))
        scores.append((
            character,
            0.24 * iou + 0.24 * coarse + 0.18 * holes
            + 0.18 * projection + 0.16 * balance,
        ))
    scores.sort(key=lambda item: -item[1])
    return scores[:top]


def layout_from_image(
    image: Image.Image,
    trajectories_by_character: dict,
    paper: PaperConfig,
    *,
    candidates: str,
    font_path=None,
    fit_ratio: float = 0.92,
) -> tuple[Trajectory, list[dict]]:
    """画像の文字を認識し、その位置と大きさのまま紙面へ写す。

    画像の縦横比は保ったまま書き枠へ収める。桝目に割り付ける
    ``compose_sheet`` と違い、**画像どおりの配置**を再現する。
    """

    resolved, _ = resolve_exemplar_font(font_path)
    mask = binarize(image)
    boxes = find_glyph_boxes(mask)
    if not boxes:
        raise ValueError("画像から文字を見つけられませんでした。")
    usable_x = paper.width - 2.0 * paper.margin
    usable_y = paper.height - 2.0 * paper.margin
    # 画像の余白ではなく**文字が占める範囲**を書き枠に合わせる。
    # 画像全体で合わせると余白ぶん字が小さくなり、筆の太さ（約 11mm）に対して
    # 字が小さすぎて布白が潰れる。文字の外接範囲を基準にすれば同じ配置のまま
    # 最大限大きく書ける。
    row0 = min(b[0] for b in boxes); row1 = max(b[1] for b in boxes)
    col0 = min(b[2] for b in boxes); col1 = max(b[3] for b in boxes)
    width = max(col1 - col0, 1)
    height = max(row1 - row0, 1)
    scale = min(usable_x / width, usable_y / height) * fit_ratio
    origin = np.asarray([paper.center_x, paper.center_y])
    # 文字範囲の中心を紙面中心に合わせる
    image_center = np.asarray([0.5 * (col0 + col1), 0.5 * (row0 + row1)])
    strokes = []
    report: list[dict] = []
    for row0, row1, col0, col1 in sorted(boxes, key=lambda b: (b[2], b[0])):
        patch = mask[row0:row1, col0:col1]
        guesses = recognize(patch, candidates, resolved, top=3)
        if not guesses:
            continue
        character, score = guesses[0]
        trajectory = trajectories_by_character.get(character)
        if trajectory is None:
            continue
        # 画像座標 -> 紙面座標（画像の y 下向きを紙面の y 上向きへ）
        center_col = 0.5 * (col0 + col1)
        center_row = 0.5 * (row0 + row1)
        center = origin + np.asarray([
            (center_col - image_center[0]) * scale,
            -(center_row - image_center[1]) * scale,
        ])
        size = np.asarray([(col1 - col0) * scale, (row1 - row0) * scale])
        placed = place_in_cell(trajectory, center, size)
        strokes.extend(placed.strokes)
        report.append({
            "character": character,
            "score": round(score, 3),
            "alternatives": [(c, round(s, 3)) for c, s in guesses[1:]],
            "center_mm": (round(center[0] * 1000, 1), round(center[1] * 1000, 1)),
            "size_mm": (round(size[0] * 1000, 1), round(size[1] * 1000, 1)),
        })
    if not strokes:
        raise ValueError("認識できた字がありません。")
    return (
        Trajectory(
            strokes=tuple(strokes),
            source="image-layout " + "".join(r["character"] for r in report),
            character=None,
        ),
        report,
    )
