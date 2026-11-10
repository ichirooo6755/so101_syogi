"""字ごとの筆圧スケール — お手本の墨の量に合わせて線の太さを決める。

お手本フォントは画数が少ない字ほど線を太くしている（実効幅と画数の相関 −0.647、
鬱 9.55mm に対し 十 16.03mm）。一方こちらの目標幅はほぼ一定（範囲 15%）なので、
外形比を合わせたあとも 日・目・自 は墨が手本の 0.77-0.85 しか乗らない。

幅は `_width_from_pressure` で `0.82 × physical + 0.18 × calligraphy` と
**筆圧が 82% を支配する**ため、`stroke.widths`（= body_width）を触っても効かない。
そこで計画した筆圧プロファイルの形はそのままに、字ごとの倍率だけを掛ける。

倍率は「その倍率で描いたときの墨の面積」を実際にラスタライズして求め、
お手本の面積に一致する値を二分法で解く。画の重なりも含めて数えられるので、
画数の多い字で重なりぶんを過大評価することがない。
"""

from __future__ import annotations

import numpy as np

from so101_calligraphy.brushwork import BrushworkProfile, _width_from_pressure
from so101_calligraphy.config import BrushConfig, InkConfig, PaperConfig
from so101_calligraphy.trajectory.types import Stroke


def _stamp_area(
    strokes: tuple[Stroke, ...] | list[Stroke],
    widths: list[np.ndarray],
    paper: PaperConfig,
    ink: InkConfig,
) -> float:
    """計画した幅で描いたときに墨が乗る面積 [m^2]。重なりは一度だけ数える。"""

    points = np.concatenate([s.points for s in strokes], axis=0)
    radii = np.concatenate(widths) * 0.5
    lower = points.min(axis=0) - radii.max() - ink.pixel_size
    upper = points.max(axis=0) + radii.max() + ink.pixel_size
    columns = max(2, int(np.ceil((upper[0] - lower[0]) / ink.pixel_size)))
    rows = max(2, int(np.ceil((upper[1] - lower[1]) / ink.pixel_size)))
    grid = np.zeros((rows, columns), dtype=bool)
    # 画素中心の座標
    xs = lower[0] + (np.arange(columns) + 0.5) * ink.pixel_size
    ys = upper[1] - (np.arange(rows) + 0.5) * ink.pixel_size
    for point, radius in zip(points, radii):
        if radius <= 0.0:
            continue
        c0 = max(0, int((point[0] - radius - lower[0]) / ink.pixel_size))
        c1 = min(columns, int((point[0] + radius - lower[0]) / ink.pixel_size) + 2)
        r0 = max(0, int((upper[1] - point[1] - radius) / ink.pixel_size))
        r1 = min(rows, int((upper[1] - point[1] + radius) / ink.pixel_size) + 2)
        if c0 >= c1 or r0 >= r1:
            continue
        dx = xs[c0:c1] - point[0]
        dy = ys[r0:r1] - point[1]
        grid[r0:r1, c0:c1] |= (dy[:, None] ** 2 + dx[None, :] ** 2) <= radius * radius
    return float(grid.sum()) * ink.pixel_size * ink.pixel_size


def exemplar_pressure_scale(
    strokes: tuple[Stroke, ...] | list[Stroke],
    profiles: tuple[BrushworkProfile, ...],
    mask: np.ndarray,
    paper: PaperConfig,
    ink: InkConfig,
    brush: BrushConfig,
    *,
    bounds: tuple[float, float] = (0.55, 1.80),
    iterations: int = 12,
) -> float:
    """お手本と同じ量の墨が乗る筆圧倍率を二分法で求める。"""

    target_area = float(np.count_nonzero(np.asarray(mask) >= 0.5))
    target_area *= ink.pixel_size * ink.pixel_size
    if target_area <= 0.0:
        return 1.0

    def area_for(scale: float) -> float:
        widths = []
        for stroke, profile in zip(strokes, profiles):
            body = profile.body_width or 0.55 * (
                brush.minimum_width + brush.maximum_width
            )
            pressure = np.clip(np.asarray(profile.pressure) * scale, 0.0, 1.5)
            value = _width_from_pressure(pressure, body, brush)
            if len(value) != len(stroke.points):
                value = np.full(len(stroke.points), float(np.median(value)))
            widths.append(value)
        return _stamp_area(strokes, widths, paper, ink)

    low, high = bounds
    if area_for(low) >= target_area:
        return low
    if area_for(high) <= target_area:
        return high
    for _ in range(iterations):
        middle = 0.5 * (low + high)
        if area_for(middle) < target_area:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)
