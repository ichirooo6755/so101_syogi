"""Independent legacy and capillary-reservoir brush ink models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from so101_calligraphy.config import BrushConfig, InkConfig, PaperConfig
from so101_calligraphy.ink import InkCanvas, InkDeposit


@dataclass(frozen=True)
class DripEvent:
    position: np.ndarray
    mass: float
    over_paper: bool


class LegacyInkModel(InkCanvas):
    """Compatibility adapter exposing the professional model protocol."""

    core_ink = 1.0
    surface_ink = 1.0
    excess_ink = 0.0
    drip_risk = 0.0
    drip_count = 0

    def load_from_inkstone(self, *, contact: bool, immersion: float) -> None:
        return None

    def wipe_on_lip(self, *, contact: bool, speed: float) -> None:
        return None

    def advance_airborne(
        self,
        *,
        position: np.ndarray,
        uprightness: float,
        acceleration: float,
        over_paper: bool,
    ) -> DripEvent | None:
        self.dry()
        return None

    def deposit(
        self,
        position: np.ndarray,
        *,
        pressure: float,
        speed: float,
        deflection: np.ndarray,
        tangent: np.ndarray,
        intended: bool,
        stroke_index: int,
        opening: float = 1.0,
        roll: float = 0.0,
        phase: str = "send",
        technique: str = "tome",
        shaft_direction: np.ndarray | None = None,
        lean: float = 0.0,
    ) -> InkDeposit | None:
        return super().deposit(
            position,
            pressure=pressure,
            speed=speed,
            deflection=deflection,
            tangent=tangent,
            intended=intended,
            stroke_index=stroke_index,
            opening=opening,
            shaft_direction=shaft_direction,
            lean=lean,
        )


class ReservoirInkModel(InkCanvas):
    """Two-reservoir capillary ink, loading, wiping, dripping, and tuft bundles."""

    def __init__(
        self,
        paper: PaperConfig,
        brush: BrushConfig,
        ink: InkConfig,
    ) -> None:
        super().__init__(paper, brush, ink)
        self.core_ink = 0.06
        self.surface_ink = 0.03
        self.excess_ink = 0.0
        self.drip_risk = 0.0
        self.drip_count = 0
        self.drip_mass = 0.0
        self.drips: list[DripEvent] = []
        self.bundle_ink = np.full(7, 0.35, dtype=np.float64)
        self._previous_bundle_position: np.ndarray | None = None
        self._previous_bundle_stroke = -1

    def reset(self, *, ink_load: float | None = None, water: float | None = None) -> None:
        super().reset(ink_load=0.03, water=0.25 if water is None else water)
        self.core_ink = 0.06
        self.surface_ink = 0.03
        self.excess_ink = 0.0
        self.drip_risk = 0.0
        self.drip_count = 0
        self.drip_mass = 0.0
        self.drips = []
        self.bundle_ink.fill(0.35)
        self._previous_bundle_position = None
        self._previous_bundle_stroke = -1

    def _sync(self) -> None:
        self.ink_load = float(
            np.clip(
                0.38 * self.core_ink / self.config.core_capacity
                + 0.62 * self.surface_ink / self.config.surface_capacity,
                0.0,
                1.0,
            )
        )

    def load_from_inkstone(self, *, contact: bool, immersion: float) -> None:
        if not contact:
            return
        if (
            self.core_ink >= 0.85 * self.config.core_capacity
            and self.surface_ink >= self.config.target_surface_ink + 0.02
        ):
            # The fixed curriculum includes periodic opportunities to re-ink,
            # but a well-loaded tuft should dip only when predicted reserves
            # are inadequate.
            return
        amount = self.config.loading_rate * float(np.clip(immersion, 0.15, 1.0))
        # Immersion loads the inner hair reservoir first. The exposed surface
        # is allowed only a small wipeable surplus; creating an arbitrarily
        # overloaded shell here would guarantee a drip before reaching the lip.
        self.core_ink = min(self.config.core_capacity, self.core_ink + amount * 0.95)
        surface_limit = min(
            self.config.surface_capacity,
            self.config.target_surface_ink + 0.04,
        )
        self.surface_ink = min(
            surface_limit,
            self.surface_ink + amount * 0.24,
        )
        self.excess_ink = max(
            self.excess_ink,
            self.surface_ink - self.config.target_surface_ink,
        )
        self.water = min(1.0, self.water + amount * 0.34)
        self.bundle_ink[:] = np.minimum(1.0, self.bundle_ink + amount * 2.4)
        self._sync()

    def wipe_on_lip(self, *, contact: bool, speed: float) -> None:
        if not contact:
            return
        self.excess_ink = max(
            self.excess_ink,
            self.surface_ink - self.config.target_surface_ink,
        )
        removal = self.config.wiping_rate * (0.65 + 2.2 * min(speed, 0.20))
        removed = min(self.excess_ink, removal)
        self.excess_ink -= removed
        self.surface_ink = max(0.0, self.surface_ink - removed)
        self.drip_mass *= 0.20
        self.drip_risk *= 0.35
        self._sync()

    def advance_airborne(
        self,
        *,
        position: np.ndarray,
        uprightness: float,
        acceleration: float,
        over_paper: bool,
    ) -> DripEvent | None:
        tilt = 1.0 - float(np.clip(uprightness, 0.0, 1.0))
        overload = max(
            self.surface_ink - self.config.drip_surface_threshold,
            0.0,
        ) + self.excess_ink
        self.drip_risk = float(
            np.clip(overload * (0.55 + 1.8 * tilt + 0.035 * acceleration), 0.0, 1.0)
        )
        self.drip_mass += self.drip_risk * 0.00085
        self.surface_ink = max(0.0, self.surface_ink - self.config.airborne_evaporation)
        self.water = max(0.0, self.water - self.config.airborne_evaporation * 0.7)
        self._sync()
        if self.drip_mass < self.config.drip_mass_threshold:
            return None
        mass = self.drip_mass
        self.drip_mass = 0.0
        self.drip_count += 1
        self.surface_ink = max(0.0, self.surface_ink - mass * 3.0)
        event = DripEvent(np.asarray(position[:2], dtype=np.float64).copy(), mass, over_paper)
        self.drips.append(event)
        if over_paper:
            self.ink_load = max(self.ink_load, 0.2)
            self._stamp(
                event.position,
                major=0.0028,
                minor=0.0028,
                angle=0.0,
                density=min(1.0, 0.35 + 40.0 * mass),
                stroke_index=-1,
            )
        return event

    def deposit(
        self,
        position: np.ndarray,
        *,
        pressure: float,
        speed: float,
        deflection: np.ndarray,
        tangent: np.ndarray,
        intended: bool,
        stroke_index: int,
        opening: float = 1.0,
        roll: float = 0.0,
        phase: str = "send",
        technique: str = "tome",
        shaft_direction: np.ndarray | None = None,
        lean: float = 0.0,
    ) -> InkDeposit | None:
        capillary = min(
            self.core_ink,
            self.config.capillary_rate
            * max(self.config.target_surface_ink - self.surface_ink, 0.0),
        )
        self.core_ink -= capillary
        self.surface_ink = min(
            self.config.surface_capacity, self.surface_ink + capillary
        )
        bundle_target = np.clip(
            self.surface_ink / max(self.config.surface_capacity, 1e-9), 0.0, 1.0
        )
        self.bundle_ink += 0.025 * (bundle_target - self.bundle_ink)
        self._sync()
        before = self.ink_load
        mark = super().deposit(
            position,
            pressure=pressure,
            speed=speed,
            deflection=np.asarray(deflection) * opening,
            tangent=tangent,
            intended=intended,
            stroke_index=stroke_index,
            footprint_scale=self.config.professional_footprint_scale,
            opening=opening,
            shaft_direction=shaft_direction,
            lean=lean,
        )
        used = max(before - self.ink_load, 0.0)
        self.surface_ink = max(0.0, self.surface_ink - used * 0.95)
        self.excess_ink = max(0.0, self.excess_ink - used * 0.30)
        self._sync()
        if mark is not None and pressure > 0.10:
            # Seven independently loaded virtual hair bundles create a
            # directional gyakunyu head, live body edges, and converging
            # hane/harai tails without changing the authored centreline.
            tangent_xy = np.asarray(tangent, dtype=np.float64)
            tangent_xy /= max(float(np.linalg.norm(tangent_xy)), 1e-12)
            normal = np.asarray([-tangent_xy[1], tangent_xy[0]])
            offsets = np.linspace(-1.0, 1.0, len(self.bundle_ink))
            spread = mark.minor_radius * (0.58 + 0.16 * opening)
            if phase == "finish" and technique in ("hane", "harai"):
                spread *= 0.36
            entry_shift = -0.34 * mark.major_radius if phase == "entry" else 0.0
            current = np.asarray(position[:2], dtype=np.float64)
            if (
                self._previous_bundle_position is not None
                and self._previous_bundle_stroke == stroke_index
            ):
                distance = float(np.linalg.norm(current - self._previous_bundle_position))
                steps = min(8, max(1, int(np.ceil(distance / max(mark.major_radius * 0.55, 1e-5)))))
                centers = np.linspace(
                    self._previous_bundle_position,
                    current,
                    steps + 1,
                    endpoint=True,
                )[1:]
            else:
                centers = current[None, :]
            # MuJoCo control samples can be farther apart than one tuft radius.
            # Sweep the coherent core between them before laying down the hair
            # bundles; otherwise a physically continuous stroke appears as a
            # row of isolated circular stamps in the saved raster.
            for center in centers[:-1]:
                self._stamp(
                    center,
                    major=mark.major_radius,
                    minor=mark.minor_radius,
                    angle=mark.angle,
                    density=mark.density * 0.86,
                    stroke_index=stroke_index,
                    texture_offset=0.0,
                )
            for index, offset in enumerate(offsets):
                roll_shift = 0.16 * np.sin(roll) * mark.major_radius * offset
                edge = 1.0 - 0.25 * abs(offset)
                phase_density = 1.15 if phase == "entry" and offset < 0.0 else 1.0
                available = float(np.clip(self.bundle_ink[index], 0.08, 1.0))
                for center in centers:
                    bundle_position = (
                        center
                        + offset * spread * normal
                        + (entry_shift * (0.25 + 0.75 * abs(offset)) + roll_shift)
                        * tangent_xy
                    )
                    self._stamp(
                        bundle_position,
                        major=mark.major_radius * (0.54 + 0.08 * edge),
                        minor=max(
                            self.brush.minimum_width * 0.12,
                            mark.minor_radius * 0.25 * edge,
                        ),
                        angle=mark.angle,
                        density=min(
                            1.0,
                            mark.density * 0.34 * phase_density * available,
                        ),
                        stroke_index=stroke_index,
                        texture_offset=0.025 * (1.0 - available),
                    )
                self.bundle_ink[index] = max(
                    0.0,
                    self.bundle_ink[index]
                    - 0.0024 * pressure * (1.15 - 0.25 * edge),
                )
            self._previous_bundle_position = current.copy()
            self._previous_bundle_stroke = stroke_index
        return mark


def make_ink_model(
    mode: str,
    paper: PaperConfig,
    brush: BrushConfig,
    ink: InkConfig,
) -> InkCanvas:
    if mode == "legacy":
        return LegacyInkModel(paper, brush, ink)
    if mode == "professional":
        return ReservoirInkModel(paper, brush, ink)
    raise ValueError(f"Unknown ink model: {mode!r}")
