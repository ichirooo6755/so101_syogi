from __future__ import annotations

import numpy as np

from so101_calligraphy.config import BrushConfig, InkConfig, PaperConfig
from so101_calligraphy.ink import InkCanvas


def test_hard_stamp_edge_is_sharper_than_soft() -> None:
    paper = PaperConfig()
    brush = BrushConfig()
    soft = InkCanvas(paper, brush, InkConfig(stamp_edge="soft"))
    hard = InkCanvas(paper, brush, InkConfig(stamp_edge="hard"))
    position = np.asarray([paper.center_x, paper.center_y])
    for canvas in (soft, hard):
        canvas.deposit(
            position,
            pressure=0.8,
            speed=0.08,
            deflection=np.asarray([0.0, 0.0, 0.0]),
            tangent=np.asarray([1.0, 0.0]),
            intended=True,
            stroke_index=0,
        )
    soft_edge = float(np.std(np.diff(soft.pigment.max(axis=0))))
    hard_edge = float(np.std(np.diff(hard.pigment.max(axis=0))))
    assert hard.pigment.sum() > 0.0
    assert hard_edge > soft_edge * 1.15
