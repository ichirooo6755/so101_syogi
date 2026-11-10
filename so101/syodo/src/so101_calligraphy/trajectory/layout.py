"""一枚の紙に複数の字を配置する。

これまでは 1 枚 1 字で、しかも骨格 bbox を書き枠いっぱいに広げていたため
字の大きさを選べなかった（A4 で 11-12cm 固定）。実際の書は紙に入れる字数で
大きさが決まるので、桝目を切ってそこへ収める。

日本語の既定は縦書き（上から下、右から左）。
"""

from __future__ import annotations

from dataclasses import replace
import numpy as np

from so101_calligraphy.config import PaperConfig, WritingLayoutConfig
from so101_calligraphy.trajectory.types import Stroke, Trajectory


def grid_cells(
    paper: PaperConfig,
    rows: int,
    columns: int,
    *,
    cell_margin_ratio: float = 0.10,
    glyph_size: float | None = None,
    vertical: bool = True,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """書き枠を桝目に切り、各桝の (中心, 有効サイズ) を書き順に返す。

    ``vertical`` が True なら縦書き（上から下、右列から左列へ）。
    """

    if rows < 1 or columns < 1:
        raise ValueError("rows と columns は 1 以上である必要があります。")
    usable_x = paper.width - 2.0 * paper.margin
    usable_y = paper.height - 2.0 * paper.margin
    if usable_x <= 0.0 or usable_y <= 0.0:
        raise ValueError("余白が書き枠を潰しています。")
    cell_w = usable_x / columns
    cell_h = usable_y / rows
    inner = np.asarray(
        [cell_w * (1.0 - 2.0 * cell_margin_ratio), cell_h * (1.0 - 2.0 * cell_margin_ratio)]
    )
    if glyph_size is not None:
        if glyph_size <= 0.0 or glyph_size > min(cell_w, cell_h):
            raise ValueError("文字寸法が桝目に収まりません。")
        inner = np.full(2, glyph_size, dtype=np.float64)
    left = paper.center_x - usable_x * 0.5
    top = paper.center_y + usable_y * 0.5
    cells: list[tuple[np.ndarray, np.ndarray]] = []
    # 縦書きは右列から。横書きは左上から。
    column_order = range(columns - 1, -1, -1) if vertical else range(columns)
    if vertical:
        for column in column_order:
            for row in range(rows):
                cells.append((
                    np.asarray([left + (column + 0.5) * cell_w,
                                top - (row + 0.5) * cell_h]),
                    inner,
                ))
    else:
        for row in range(rows):
            for column in column_order:
                cells.append((
                    np.asarray([left + (column + 0.5) * cell_w,
                                top - (row + 0.5) * cell_h]),
                    inner,
                ))
    return cells


def writing_frames(
    paper: PaperConfig,
    layout: WritingLayoutConfig,
) -> tuple[tuple[np.ndarray, np.ndarray], ...]:
    """Return four 2x2 frames followed by two vertical two-character frames."""

    if layout.single_center_size is not None:
        if layout.single_center_size <= 0.0:
            raise ValueError("single_center_size must be positive")
        size = np.full(2, layout.single_center_size, dtype=np.float64)
        return (
            (
                np.asarray([paper.center_x, paper.center_y], dtype=np.float64),
                size,
            ),
        )

    four = grid_cells(
        paper,
        2,
        2,
        cell_margin_ratio=0.0,
        glyph_size=layout.two_by_two_size,
    )
    two = grid_cells(
        paper,
        2,
        1,
        cell_margin_ratio=0.0,
        glyph_size=layout.two_character_size,
    )
    return tuple((*four, *two))


def frame_paper(
    paper: PaperConfig,
    layout: WritingLayoutConfig,
    index: int,
) -> PaperConfig:
    """Paper-shaped adapter for loaders that fit one glyph into a writing box."""

    frames = writing_frames(paper, layout)
    if not 0 <= index < len(frames):
        raise IndexError(index)
    center, size = frames[index]
    return PaperConfig(
        width=float(size[0]),
        height=float(size[1]),
        center_x=float(center[0]),
        center_y=float(center[1]),
        surface_z=paper.surface_z,
        margin=0.0,
    )


def place_in_cell(
    trajectory: Trajectory,
    center: np.ndarray,
    size: np.ndarray,
    *,
    aspect: float | None = None,
) -> Trajectory:
    """1 字を桝目に収める。``aspect`` を与えると字の縦横比をそれに合わせる。"""

    points = np.concatenate([s.points for s in trajectory.strokes], axis=0)
    lower, upper = points.min(axis=0), points.max(axis=0)
    span = np.maximum(upper - lower, 1e-9)
    if aspect is None:
        # 等方: 桝目に収まる最大
        factor = float(min(size[0] / span[0], size[1] / span[1]))
        scale = np.asarray([factor, factor])
    else:
        # お手本の縦横比に合わせてから桝目に収める
        height = min(size[1], size[0] / aspect)
        target = np.asarray([height * aspect, height])
        scale = target / span
    source_center = 0.5 * (lower + upper)
    width_scale = float(np.sqrt(scale[0] * scale[1]))
    # 小さく書くときは線も細くしないと布白が潰れる。実際の書でも小さい字は
    # 細い筆に持ち替える。ここでは stroke.widths を縮めて body_width を下げる。
    strokes = tuple(
        replace(
            stroke,
            points=(stroke.points - source_center) * scale + center,
            widths=None if stroke.widths is None else stroke.widths * width_scale,
        )
        for stroke in trajectory.strokes
    )
    return replace(trajectory, strokes=strokes)


def compose_sheet(
    trajectories: list[Trajectory] | tuple[Trajectory, ...],
    paper: PaperConfig,
    *,
    rows: int | None = None,
    columns: int | None = None,
    cell_margin_ratio: float = 0.10,
    glyph_size: float | None = None,
    vertical: bool = True,
    aspects: list[float | None] | None = None,
) -> Trajectory:
    """複数の字を桝目に並べ、1 本の Trajectory にまとめる。

    ``rows`` / ``columns`` を省略すると、縦書きは 1 列 N 行、
    横書きは 1 行 N 列にする。
    """

    count = len(trajectories)
    if count == 0:
        raise ValueError("字がありません。")
    if rows is None and columns is None:
        rows, columns = (count, 1) if vertical else (1, count)
    elif rows is None:
        rows = -(-count // int(columns))
    elif columns is None:
        columns = -(-count // int(rows))
    rows, columns = int(rows), int(columns)
    if rows * columns < count:
        raise ValueError(
            f"桝目 {rows}x{columns} に {count} 字は入りません。"
        )
    cells = grid_cells(
        paper, rows, columns,
        cell_margin_ratio=cell_margin_ratio,
        glyph_size=glyph_size,
        vertical=vertical,
    )
    strokes: list[Stroke] = []
    for index, trajectory in enumerate(trajectories):
        center, size = cells[index]
        aspect = None if aspects is None else aspects[index]
        placed = place_in_cell(trajectory, center, size, aspect=aspect)
        strokes.extend(placed.strokes)
    text = "".join(t.character or "?" for t in trajectories)
    return Trajectory(
        strokes=tuple(strokes),
        source=f"composed-sheet[{rows}x{columns}] {text}",
        character=None,
    )
