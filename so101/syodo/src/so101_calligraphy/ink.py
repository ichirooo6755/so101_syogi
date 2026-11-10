"""Deterministic, CPU-cheap brush-ink transfer onto A4 paper."""

from __future__ import annotations

from dataclasses import dataclass

import mujoco
import numpy as np

from so101_calligraphy.config import BrushConfig, InkConfig, PaperConfig


TIP_PRESSURE_POINTS = np.asarray((0.0, 0.10, 0.20, 0.30, 0.45, 1.0))
TIP_WIDTH_POINTS_M = np.asarray((0.0018, 0.0025, 0.0040, 0.0062, 0.0090, 0.0130))


def tip_width_from_pressure(
    pressure: float | np.ndarray, brush: BrushConfig
) -> float | np.ndarray:
    """Reversible 38 mm tip-only pressure/width calibration."""

    calibrated = np.interp(
        np.clip(pressure, TIP_PRESSURE_POINTS[0], TIP_PRESSURE_POINTS[-1]),
        TIP_PRESSURE_POINTS,
        TIP_WIDTH_POINTS_M,
    )
    normalized = (calibrated - TIP_WIDTH_POINTS_M[0]) / (
        TIP_WIDTH_POINTS_M[-1] - TIP_WIDTH_POINTS_M[0]
    )
    result = brush.minimum_width + normalized * (
        brush.maximum_width - brush.minimum_width
    )
    return float(result) if np.ndim(pressure) == 0 else result


def tip_pressure_from_width(
    width: float | np.ndarray, brush: BrushConfig
) -> float | np.ndarray:
    """Inverse of :func:`tip_width_from_pressure` on the calibrated range."""

    normalized = (
        np.clip(width, brush.minimum_width, brush.maximum_width)
        - brush.minimum_width
    ) / max(brush.maximum_width - brush.minimum_width, 1e-12)
    calibrated = TIP_WIDTH_POINTS_M[0] + normalized * (
        TIP_WIDTH_POINTS_M[-1] - TIP_WIDTH_POINTS_M[0]
    )
    result = np.interp(calibrated, TIP_WIDTH_POINTS_M, TIP_PRESSURE_POINTS)
    return float(result) if np.ndim(width) == 0 else result


@dataclass(frozen=True)
class InkDeposit:
    position: np.ndarray
    major_radius: float
    minor_radius: float
    angle: float
    density: float
    intended: bool
    stroke_index: int

    @property
    def width(self) -> float:
        return 2.0 * self.minor_radius


class InkCanvas:
    """Raster paper plus bounded vector deposits for native Viewer replay."""

    def __init__(
        self,
        paper: PaperConfig,
        brush: BrushConfig,
        ink: InkConfig,
    ) -> None:
        self.paper = paper
        self.brush = brush
        self.config = ink
        rows = int(np.ceil(paper.height / ink.pixel_size))
        columns = int(np.ceil(paper.width / ink.pixel_size))
        self.pigment = np.zeros((rows, columns), dtype=np.float32)
        self.deposits: list[InkDeposit] = []
        self.ink_load = ink.initial_ink
        self.water = ink.initial_water
        self.total_mass = 0.0
        self.unintended_mass = 0.0

    def reset(self, *, ink_load: float | None = None, water: float | None = None) -> None:
        self.pigment.fill(0.0)
        self.deposits.clear()
        self.ink_load = float(self.config.initial_ink if ink_load is None else ink_load)
        self.water = float(self.config.initial_water if water is None else water)
        self.total_mass = 0.0
        self.unintended_mass = 0.0

    def dry(self) -> None:
        self.water = max(0.0, self.water - self.config.water_loss_rate * 0.15)

    def _world_grid(
        self, position: np.ndarray, major: float, minor: float
    ) -> tuple[slice, slice, np.ndarray, np.ndarray] | None:
        spread = max(major, minor) * (1.3 + self.config.water_spread * self.water)
        xmin = self.paper.center_x - self.paper.width * 0.5
        ymax = self.paper.center_y + self.paper.height * 0.5
        column = (float(position[0]) - xmin) / self.config.pixel_size
        row = (ymax - float(position[1])) / self.config.pixel_size
        radius = int(np.ceil(spread / self.config.pixel_size)) + 1
        c0 = max(0, int(np.floor(column)) - radius)
        c1 = min(self.pigment.shape[1], int(np.floor(column)) + radius + 1)
        r0 = max(0, int(np.floor(row)) - radius)
        r1 = min(self.pigment.shape[0], int(np.floor(row)) + radius + 1)
        if r0 >= r1 or c0 >= c1:
            return None
        columns = np.arange(c0, c1, dtype=np.float64)
        rows = np.arange(r0, r1, dtype=np.float64)
        x = xmin + (columns + 0.5) * self.config.pixel_size
        y = ymax - (rows + 0.5) * self.config.pixel_size
        return slice(r0, r1), slice(c0, c1), *np.meshgrid(x, y)

    def _stamp(
        self,
        position: np.ndarray,
        *,
        major: float,
        minor: float,
        angle: float,
        density: float,
        stroke_index: int,
        texture_offset: float = 0.0,
        taper: float = 0.0,
    ) -> float:
        """Apply one bundle footprint and return deposited pixel mass.

        ``taper`` は穂先側の尖り（0 で左右対称の楕円、1 で涙滴型）。
        実際の筆は円錐なので、寝かせた向きに沿って伸び、穂先側が尖った跡を残す。
        楕円のままだと端が必ず丸くなり、起筆の三角形が原理的に作れない。
        """

        grid = self._world_grid(position, major, minor)
        if grid is None:
            return 0.0
        row_slice, column_slice, x, y = grid
        dx = x - float(position[0])
        dy = y - float(position[1])
        cosine, sine = np.cos(angle), np.sin(angle)
        along = cosine * dx + sine * dy
        across = -sine * dx + cosine * dy
        if taper > 0.0:
            # +along 側を穂先とし、そちらへ行くほど幅を絞る。
            # 半幅 = minor * (1 - taper * clip(along/major, 0, 1))
            reach = np.clip(along / max(major, 1e-9), -1.0, 1.0)
            narrow = 1.0 - float(np.clip(taper, 0.0, 0.95)) * np.clip(reach, 0.0, 1.0)
            half = np.maximum(minor * narrow, 1e-9)
            radius_squared = (along / max(major, 1e-9)) ** 2 + (across / half) ** 2
        else:
            radius_squared = (along / max(major, 1e-9)) ** 2 + (
                across / max(minor, 1e-9)
            ) ** 2
        if self.config.stamp_edge == "hard":
            # ponytail: hard kaisho edge; upgrade path = per-technique edge profiles
            rim = min(0.18, self.config.pixel_size / max(minor, 1e-9))
            inner = max(0.0, 1.0 - rim * rim)
            core = np.where(
                radius_squared <= inner,
                1.0,
                np.where(
                    radius_squared <= 1.0,
                    np.clip((1.0 - radius_squared) / max(1.0 - inner, 1e-9), 0.0, 1.0),
                    0.0,
                ),
            )
            halo = np.zeros_like(core)
            absorption = 0.0
        else:
            core = np.exp(-2.2 * radius_squared) * (radius_squared <= 1.0)
            spread_scale = 1.0 + self.config.water_spread * self.water
            halo_radius = radius_squared / (spread_scale * spread_scale)
            halo = np.exp(-3.2 * halo_radius) * (halo_radius <= 1.0)
            absorption = self.config.absorption * self.water
        stamp = (1.0 - absorption) * core + absorption * halo
        speed_texture = texture_offset
        dryness = np.clip(
            (self.config.dry_brush_threshold - self.ink_load)
            / max(self.config.dry_brush_threshold, 1e-6)
            + speed_texture,
            0.0,
            0.82,
        )
        texture = 0.5 + 0.5 * np.sin(
            (x / self.config.pixel_size) * 12.9898
            + (y / self.config.pixel_size) * 78.233
            + stroke_index * 19.19
        )
        stamp *= (texture >= dryness).astype(np.float64)
        stamp = np.clip(stamp * density, 0.0, 1.0)
        destination = self.pigment[row_slice, column_slice]
        destination[:] = 1.0 - (1.0 - destination) * (1.0 - stamp)
        return float(stamp.sum())

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
        footprint_scale: float = 1.0,
        opening: float = 1.0,
        shaft_direction: np.ndarray | None = None,
        lean: float = 0.0,
    ) -> InkDeposit | None:
        """Transfer one pressure-dependent brush stamp shaped by the shaft pose."""

        pressure = float(np.clip(pressure, 0.0, 1.5))
        if pressure <= 0.01 or self.ink_load <= 0.002:
            self.dry()
            return None
        speed_ratio = np.clip(speed / max(self.brush.nominal_speed, 1e-6), 0.0, 3.0)
        width = tip_width_from_pressure(pressure, self.brush)
        width = self.brush.minimum_width + (
            width - self.brush.minimum_width
        ) * float(np.clip(footprint_scale, 0.25, 2.0))
        width = float(
            np.clip(
                width,
                self.brush.minimum_width,
                self.brush.maximum_width * 1.15,
            )
        )
        minor = width * 0.5
        major = minor * (1.0 + 0.30 * self.water + 0.22 * speed_ratio)

        # 穂の軸が紙面に落とす向きを跡の長軸にする。実際の筆は円錐なので、
        # 寝かせた方向へ接地面が伸び、穂先側が尖る。進行方向で楕円を置くだけ
        # だと端が必ず丸くなり、起筆の三角形も止めの角も作れない。
        shaft = np.asarray(shaft_direction, dtype=np.float64) if shaft_direction is not None \
            else np.zeros(2)
        taper = 0.0
        if np.linalg.norm(shaft) > 1e-8 and lean > np.sin(np.deg2rad(8.0)):
            direction = shaft / np.linalg.norm(shaft)
            # Eight degrees is the neutral sending posture. Only the extra
            # 8°..30° used at entries, corners, and returns opens the conical
            # tip into a wedge; otherwise the whole stroke becomes a chain of
            # elongated stamps and closes counters that should stay white.
            useful_lean = float(
                np.clip(
                    (lean - np.sin(np.deg2rad(8.0)))
                    / (np.sin(np.deg2rad(30.0)) - np.sin(np.deg2rad(8.0))),
                    0.0,
                    1.0,
                )
            )
            stretch = 1.0 + 0.65 * useful_lean
            major = minor * stretch * (1.0 + 0.18 * self.water + 0.12 * speed_ratio)
            taper = 0.95 * np.sqrt(useful_lean)
        else:
            direction = np.asarray(tangent, dtype=np.float64)
            if np.linalg.norm(direction) < 1e-8:
                direction = np.asarray(deflection[:2], dtype=np.float64)
            if np.linalg.norm(direction) < 1e-8:
                direction = np.asarray([1.0, 0.0])
            direction /= np.linalg.norm(direction)
        angle = float(np.arctan2(direction[1], direction[0]))

        density = self.ink_load * (0.55 + 0.45 * min(pressure, 1.0))
        density /= 1.0 + 0.38 * speed_ratio
        density = float(np.clip(density, 0.02, 1.0))
        deposited_mass = self._stamp(
            np.asarray(position),
            major=major,
            minor=minor,
            angle=angle,
            density=density,
            stroke_index=stroke_index,
            texture_offset=0.10 * max(speed_ratio - 1.0, 0.0),
            taper=taper,
        )

        area_scale = np.clip(width / self.brush.maximum_width, 0.1, 1.5)
        self.ink_load = max(
            0.0,
            self.ink_load
            - self.config.transfer_rate * pressure * area_scale * (0.7 + 0.3 * self.water),
        )
        self.water = max(
            0.0,
            self.water
            - self.config.water_loss_rate * (0.5 + pressure + 0.25 * speed_ratio),
        )
        self.total_mass += deposited_mass
        if not intended:
            self.unintended_mass += deposited_mass

        mark = InkDeposit(
            np.asarray(position[:2], dtype=np.float64).copy(),
            major,
            minor,
            angle,
            density,
            intended,
            stroke_index,
        )
        self.deposits.append(mark)
        if len(self.deposits) > self.config.viewer_deposit_limit:
            del self.deposits[: len(self.deposits) - self.config.viewer_deposit_limit]
        return mark

    @property
    def unintended_fraction(self) -> float:
        return self.unintended_mass / max(self.total_mass, 1e-9)

    def ink_points(self, threshold: float = 0.12, maximum: int = 1500) -> np.ndarray:
        rows, columns = np.nonzero(self.pigment >= threshold)
        if len(rows) == 0:
            return np.empty((0, 2), dtype=np.float64)
        if len(rows) > maximum:
            indices = np.linspace(0, len(rows) - 1, maximum).round().astype(int)
            rows, columns = rows[indices], columns[indices]
        xmin = self.paper.center_x - self.paper.width * 0.5
        ymax = self.paper.center_y + self.paper.height * 0.5
        x = xmin + (columns + 0.5) * self.config.pixel_size
        y = ymax - (rows + 0.5) * self.config.pixel_size
        return np.column_stack((x, y))

    def rgb_image(self) -> np.ndarray:
        paper = np.asarray([0.98, 0.97, 0.91], dtype=np.float32)
        ink = np.asarray([0.025, 0.018, 0.012], dtype=np.float32)
        alpha = np.clip(self.pigment[..., None], 0.0, 1.0)
        return np.clip(paper * (1.0 - alpha) + ink * alpha, 0.0, 1.0)

    def draw_mjv_scene(self, scene: mujoco.MjvScene, *, clear: bool) -> None:
        """Add bounded dark ellipsoids to a MuJoCo render scene."""

        if clear:
            scene.ngeom = 0
        available = max(0, scene.maxgeom - scene.ngeom)
        marks = self.deposits[-available:] if available else ()
        for mark in marks:
            cosine, sine = np.cos(mark.angle), np.sin(mark.angle)
            rotation = np.asarray(
                [[cosine, -sine, 0.0], [sine, cosine, 0.0], [0.0, 0.0, 1.0]],
                dtype=np.float64,
            )
            geom = scene.geoms[scene.ngeom]
            mujoco.mjv_initGeom(
                geom,
                mujoco.mjtGeom.mjGEOM_ELLIPSOID,
                np.asarray([mark.major_radius, mark.minor_radius, 0.00012]),
                np.asarray([mark.position[0], mark.position[1], self.paper.surface_z + 0.00015]),
                rotation.reshape(-1),
                np.asarray([0.018, 0.012, 0.008, min(0.96, 0.35 + 0.65 * mark.density)], dtype=np.float32),
            )
            geom.category = mujoco.mjtCatBit.mjCAT_DECOR
            scene.ngeom += 1
