from __future__ import annotations

import numpy as np

from so101_calligraphy.config import BrushConfig, InkConfig, PaperConfig
from so101_calligraphy.ink import InkCanvas, tip_width_from_pressure
from so101_calligraphy.ink_model import ReservoirInkModel


def test_reservoir_model_loads_wipes_and_drips() -> None:
    ink = ReservoirInkModel(PaperConfig(), BrushConfig(), InkConfig())
    ink.reset()
    initial = ink.core_ink + ink.surface_ink
    for _ in range(22):
        ink.load_from_inkstone(contact=True, immersion=1.0)
    loaded = ink.core_ink + ink.surface_ink
    assert loaded > initial
    excess = ink.excess_ink
    for _ in range(12):
        ink.wipe_on_lip(contact=True, speed=0.1)
    assert ink.excess_ink < excess

    ink.surface_ink = 0.9
    ink.excess_ink = 0.2
    event = None
    for _ in range(100):
        event = ink.advance_airborne(
            position=np.asarray([0.235, 0.0, 0.07]),
            uprightness=0.2,
            acceleration=10.0,
            over_paper=True,
        )
        if event is not None:
            break
    assert event is not None
    assert ink.drip_count == 1
    assert ink.pigment.max() > 0.0


def test_reservoir_model_transfers_multiple_bundles() -> None:
    ink = ReservoirInkModel(PaperConfig(), BrushConfig(), InkConfig())
    for _ in range(22):
        ink.load_from_inkstone(contact=True, immersion=1.0)
    for _ in range(12):
        ink.wipe_on_lip(contact=True, speed=0.1)
    mark = ink.deposit(
        np.asarray([0.235, 0.0, 0.012]),
        pressure=0.7,
        speed=0.08,
        deflection=np.asarray([0.002, 0.001, 0.0]),
        tangent=np.asarray([1.0, 0.0]),
        intended=True,
        stroke_index=0,
        opening=1.2,
        roll=0.3,
    )
    assert mark is not None
    assert mark.width == tip_width_from_pressure(0.7, ink.brush)
    assert ink.pigment.max() > 0.1
    assert ink.surface_ink > 0.0


def test_neutral_eight_degree_send_keeps_body_footprint() -> None:
    def deposit(lean_degrees: float):
        canvas = InkCanvas(PaperConfig(), BrushConfig(), InkConfig())
        return canvas.deposit(
            np.asarray([0.200, 0.0, 0.012]),
            pressure=0.30,
            speed=0.10,
            deflection=np.zeros(3),
            tangent=np.asarray([1.0, 0.0]),
            intended=True,
            stroke_index=0,
            shaft_direction=np.asarray([1.0, 0.0]),
            lean=float(np.sin(np.deg2rad(lean_degrees))),
        )

    upright = deposit(0.0)
    sending = deposit(8.0)
    entry = deposit(30.0)

    assert upright is not None and sending is not None and entry is not None
    assert sending.major_radius == upright.major_radius
    assert entry.major_radius > sending.major_radius
    assert entry.minor_radius == sending.minor_radius
