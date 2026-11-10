"""Expand 2-D strokes into ordered pen-down and pen-up 3-D waypoints."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

import numpy as np

from so101_calligraphy.brushwork import _width_from_pressure, make_brushwork_planner
from so101_calligraphy.config import BrushConfig, InkstoneConfig
from so101_calligraphy.trajectory.clearance import (
    apply_clearance_caps,
    exposed_horizontal_endpoints,
)
from so101_calligraphy.trajectory.types import Trajectory


@dataclass(frozen=True)
class WaypointSequence:
    positions: np.ndarray
    pen_down: np.ndarray
    stroke_indices: np.ndarray
    phases: tuple[str, ...]
    stroke_progress: np.ndarray
    target_tangents: np.ndarray
    target_pressure: np.ndarray
    target_speed: np.ndarray
    target_width: np.ndarray
    target_roll: np.ndarray
    techniques: tuple[str, ...]
    brushwork_phases: tuple[str, ...]

    def __post_init__(self) -> None:
        positions = np.asarray(self.positions, dtype=np.float64)
        pen_down = np.asarray(self.pen_down, dtype=np.bool_)
        stroke_indices = np.asarray(self.stroke_indices, dtype=np.int32)
        stroke_progress = np.asarray(self.stroke_progress, dtype=np.float64)
        target_tangents = np.asarray(self.target_tangents, dtype=np.float64)
        target_pressure = np.asarray(self.target_pressure, dtype=np.float64)
        target_speed = np.asarray(self.target_speed, dtype=np.float64)
        target_width = np.asarray(self.target_width, dtype=np.float64)
        target_roll = np.asarray(self.target_roll, dtype=np.float64)
        count = len(positions)
        if positions.shape != (count, 3):
            raise ValueError("Waypoint positions must have shape (N, 3).")
        if pen_down.shape != (count,) or stroke_indices.shape != (count,):
            raise ValueError("Waypoint metadata lengths do not match positions.")
        if len(self.phases) != count:
            raise ValueError("Waypoint phase count does not match positions.")
        scalar_metadata = (
            stroke_progress,
            target_pressure,
            target_speed,
            target_width,
            target_roll,
        )
        if any(values.shape != (count,) for values in scalar_metadata):
            raise ValueError("Waypoint profile lengths do not match positions.")
        if target_tangents.shape != (count, 2):
            raise ValueError("Target tangents must have shape (N, 2).")
        if len(self.techniques) != count:
            raise ValueError("Waypoint technique count does not match positions.")
        if len(self.brushwork_phases) != count:
            raise ValueError("Brushwork phase count does not match positions.")
        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "pen_down", pen_down)
        object.__setattr__(self, "stroke_indices", stroke_indices)
        object.__setattr__(self, "stroke_progress", stroke_progress)
        object.__setattr__(self, "target_tangents", target_tangents)
        object.__setattr__(self, "target_pressure", target_pressure)
        object.__setattr__(self, "target_speed", target_speed)
        object.__setattr__(self, "target_width", target_width)
        object.__setattr__(self, "target_roll", target_roll)

    def __len__(self) -> int:
        return len(self.positions)


def _release_envelope(pressure: np.ndarray) -> np.ndarray:
    """圧が抜けるほど穂が浮く量（0-1）。"""

    release = np.clip((0.22 - np.asarray(pressure)) / 0.22, 0.0, 1.0)
    return release * release * (3.0 - 2.0 * release)


def _segment(start: np.ndarray, end: np.ndarray, spacing: float) -> np.ndarray:
    distance = float(np.linalg.norm(end - start))
    count = max(1, int(np.ceil(distance / spacing)))
    # Exclude start because the preceding phase already owns it.
    return np.linspace(start, end, count + 1, dtype=np.float64)[1:]


def _upright_transport_point(
    xy: np.ndarray,
    origin: np.ndarray,
    target_radius: float,
) -> np.ndarray:
    """Project one paper point onto the collision-free upright circle."""

    offset = np.asarray(xy, dtype=np.float64) - origin
    current_radius = float(np.linalg.norm(offset))
    direction = (
        np.asarray([1.0, 0.0])
        if current_radius < 1e-12
        else offset / current_radius
    )
    return origin + direction * target_radius


def _upright_transport_route(
    start: np.ndarray,
    end: np.ndarray,
    *,
    origin: np.ndarray,
    arc_radius: float,
    spacing: float,
) -> np.ndarray:
    """Route upright motion radially and around an annulus without cutting inside."""

    start = np.asarray(start, dtype=np.float64)
    end = np.asarray(end, dtype=np.float64)
    if np.allclose(start, end):
        return np.empty((0, 3), dtype=np.float64)
    start_angle = float(np.arctan2(*(start[:2] - origin)[::-1]))
    end_angle = float(np.arctan2(*(end[:2] - origin)[::-1]))
    delta = (end_angle - start_angle + np.pi) % (2.0 * np.pi) - np.pi
    start_arc = np.asarray(
        [
            origin[0] + arc_radius * np.cos(start_angle),
            origin[1] + arc_radius * np.sin(start_angle),
            start[2],
        ]
    )
    end_arc = np.asarray(
        [
            origin[0] + arc_radius * np.cos(end_angle),
            origin[1] + arc_radius * np.sin(end_angle),
            end[2],
        ]
    )
    chunks: list[np.ndarray] = []
    if not np.allclose(start, start_arc):
        chunks.append(_segment(start, start_arc, spacing))
    if abs(delta) > 1e-12:
        count = max(1, int(np.ceil(abs(delta) * arc_radius / spacing)))
        angles = start_angle + np.linspace(0.0, delta, count + 1)[1:]
        chunks.append(
            np.column_stack(
                (
                    origin[0] + arc_radius * np.cos(angles),
                    origin[1] + arc_radius * np.sin(angles),
                    np.full(count, start[2]),
                )
            )
        )
    if not np.allclose(end_arc, end):
        chunks.append(_segment(end_arc, end, spacing))
    return np.concatenate(chunks) if chunks else end[None, :]


def build_waypoint_sequence(
    trajectory: Trajectory,
    *,
    pen_down_z: float,
    safe_height: float,
    transition_spacing: float = 0.014,
    brush: BrushConfig | None = None,
    brushwork_mode: str = "legacy",
    inkstone: InkstoneConfig | None = None,
    stroke_minimum_gap: float = 0.0,
    pressure_scale = 1.0,
    entry_descent_ratio: float = 1.0,
    stroke_junction_tolerance: float = 0.009,
    stroke_clearance_floor: float = 0.55,
    observed_width_p90_by_phase: Mapping[str, float] | None = None,
    staging_xy: tuple[float, float] | np.ndarray | None = None,
    transport_origin_xy: tuple[float, float] | np.ndarray | None = None,
    transport_radius: float | None = None,
    transport_height: float | None = None,
) -> WaypointSequence:
    """Insert approach, lift, travel, and lower phases around ordered strokes."""

    if safe_height <= pen_down_z:
        raise ValueError("safe_height must be above pen_down_z")
    if transition_spacing <= 0:
        raise ValueError("transition_spacing must be positive")
    if not 0.0 < entry_descent_ratio <= 1.0:
        raise ValueError("entry_descent_ratio must be in (0, 1]")

    transport_origin = (
        None
        if transport_origin_xy is None
        else np.asarray(transport_origin_xy, dtype=np.float64)
    )
    routed_transport = brushwork_mode == "professional" and transport_origin is not None
    if routed_transport:
        if transport_origin.shape != (2,):
            raise ValueError("transport_origin_xy must have shape (2,)")
        if transport_radius is None or transport_radius <= 0.0:
            raise ValueError("routed transport requires a positive radius")
        if transport_height is None or transport_height <= safe_height:
            raise ValueError("transport_height must exceed safe_height")

    positions: list[np.ndarray] = []
    pen_down: list[bool] = []
    stroke_indices: list[int] = []
    phases: list[str] = []
    stroke_progress: list[float] = []
    target_tangents: list[np.ndarray] = []
    target_pressure: list[float] = []
    target_speed: list[float] = []
    target_width: list[float] = []
    target_roll: list[float] = []
    techniques: list[str] = []
    brushwork_phases: list[str] = []

    brush = brush or BrushConfig()
    exposed_horizontal = exposed_horizontal_endpoints(
        trajectory.strokes,
        junction_tolerance=stroke_junction_tolerance,
    )
    strokes = trajectory.strokes
    planner = make_brushwork_planner(brushwork_mode)
    profiles = tuple(planner.plan(stroke, brush) for stroke in strokes)
    scales = np.broadcast_to(
        np.asarray(pressure_scale, dtype=np.float64), (len(profiles),)
    )
    if not np.allclose(scales, 1.0):
        # 太さをお手本の墨の量や字の大きさに合わせる。プロファイルの形は変えず
        # 倍率だけ掛けるので、三折法（トン・スー・トン）は保たれる。
        # 一枚に複数字を置くときは字ごとに大きさが違うため、画ごとに倍率を持つ。
        profiles = tuple(
            profile if np.isclose(factor, 1.0) else replace(
                profile,
                pressure=np.clip(profile.pressure * factor, 0.0, 1.5),
                width=_width_from_pressure(
                    np.clip(profile.pressure * factor, 0.0, 1.5),
                    profile.body_width
                    or 0.55 * (brush.minimum_width + brush.maximum_width),
                    brush,
                ),
            )
            for profile, factor in zip(profiles, scales)
        )
    # 一画ずつ独立に計画したあと、隣の画との距離を見て混み合った箇所だけ細める。
    # 交差・T 字接合の相手は対象外なので、つながるべき画はつながったまま残る。
    profiles = apply_clearance_caps(
        strokes,
        profiles,
        brush,
        junction_tolerance=stroke_junction_tolerance,
        minimum_gap=stroke_minimum_gap,
        floor_ratio=stroke_clearance_floor,
        observed_width_p90_by_phase=observed_width_p90_by_phase,
    )

    def append(
        points: np.ndarray,
        down: bool,
        stroke_index: int,
        phase: str,
        *,
        progress: float | np.ndarray,
        tangent: np.ndarray,
        pressure: float | np.ndarray = 0.0,
        speed: float | np.ndarray = 0.0,
        width: float | np.ndarray | None = None,
        roll: float | np.ndarray = 0.0,
        brush_phase: str | tuple[str, ...] = "transport",
    ) -> None:
        rows = np.atleast_2d(points)
        count = len(rows)

        def values(value: float | np.ndarray) -> np.ndarray:
            array = np.asarray(value, dtype=np.float64)
            return np.full(count, float(array)) if array.ndim == 0 else array

        progress_values = values(progress)
        pressure_values = values(pressure)
        speed_values = values(speed)
        width_values = values(brush.minimum_width if width is None else width)
        roll_values = values(roll)
        tangent_values = np.asarray(tangent, dtype=np.float64)
        if tangent_values.ndim == 1:
            tangent_values = np.repeat(tangent_values[None, :], count, axis=0)
        if any(
            len(array) != count
            for array in (
                progress_values,
                pressure_values,
                speed_values,
                width_values,
                roll_values,
            )
        ) or tangent_values.shape != (count, 2):
            raise ValueError("Waypoint profile does not match appended points.")
        phase_values = (
            (brush_phase,) * count if isinstance(brush_phase, str) else brush_phase
        )
        if len(phase_values) != count:
            raise ValueError("Brushwork phases do not match appended points.")

        for row, point in enumerate(rows):
            positions.append(np.asarray(point, dtype=np.float64))
            pen_down.append(down)
            stroke_indices.append(stroke_index)
            phases.append(phase)
            stroke_progress.append(float(progress_values[row]))
            target_tangents.append(tangent_values[row])
            target_pressure.append(float(pressure_values[row]))
            target_speed.append(float(speed_values[row]))
            target_width.append(float(width_values[row]))
            target_roll.append(float(roll_values[row]))
            techniques.append(profiles[stroke_index].technique)
            brushwork_phases.append(phase_values[row])

    first_xy = trajectory.strokes[0].points[0]
    staging = first_xy if staging_xy is None else np.asarray(staging_xy, dtype=np.float64)
    if np.asarray(staging).shape != (2,):
        raise ValueError("staging_xy must have shape (2,)")
    staging_height = transport_height if routed_transport else safe_height
    current = np.asarray([staging[0], staging[1], staging_height])

    def append_ink_cycle(stroke_index: int) -> None:
        nonlocal current
        assert inkstone is not None
        tangent = profiles[stroke_index].tangents[0]
        pool_safe = np.asarray(
            [inkstone.center_x, inkstone.center_y, inkstone.safe_height]
        )
        pool_contact = np.asarray(
            [
                inkstone.center_x,
                inkstone.center_y,
                inkstone.pool_surface_z + brush.tip_radius - 0.0012,
            ]
        )
        append(
            _segment(current, pool_safe, transition_spacing),
            False,
            stroke_index,
            "inkstone_approach",
            progress=0.0,
            tangent=tangent,
        )
        append(
            _segment(pool_safe, pool_contact, transition_spacing),
            False,
            stroke_index,
            "inkstone_lower",
            progress=0.0,
            tangent=tangent,
        )
        append(
            np.repeat(pool_contact[None, :], inkstone.loading_steps, axis=0),
            False,
            stroke_index,
            "ink_load",
            progress=0.0,
            tangent=tangent,
        )
        append(
            _segment(pool_contact, pool_safe, transition_spacing),
            False,
            stroke_index,
            "inkstone_lift",
            progress=0.0,
            tangent=tangent,
        )
        wipe_z = inkstone.lip_surface_z + brush.tip_radius - 0.0010
        wipe_left = np.asarray(
            [inkstone.center_x - inkstone.pool_half_width, inkstone.lip_y, wipe_z]
        )
        wipe_right = np.asarray(
            [inkstone.center_x + inkstone.pool_half_width, inkstone.lip_y, wipe_z]
        )
        append(
            _segment(pool_safe, wipe_left, transition_spacing),
            False,
            stroke_index,
            "wipe_lower",
            progress=0.0,
            tangent=tangent,
        )
        append(
            np.linspace(wipe_left, wipe_right, inkstone.wiping_points),
            False,
            stroke_index,
            "ink_wipe",
            progress=0.0,
            tangent=np.asarray([1.0, 0.0]),
        )
        append(
            np.linspace(wipe_right, wipe_left, inkstone.wiping_points),
            False,
            stroke_index,
            "ink_wipe",
            progress=0.0,
            tangent=np.asarray([-1.0, 0.0]),
        )
        current = np.asarray([*wipe_left[:2], inkstone.safe_height])
        append(
            _segment(wipe_left, current, transition_spacing),
            False,
            stroke_index,
            "wipe_lift",
            progress=0.0,
            tangent=tangent,
        )
        paper_staging = np.asarray([staging[0], staging[1], staging_height])
        append(
            _segment(current, paper_staging, transition_spacing),
            False,
            stroke_index,
            "inkstone_return",
            progress=0.0,
            tangent=tangent,
        )
        current = paper_staging

    if inkstone is not None:
        append_ink_cycle(0)
    else:
        append(
            current,
            False,
            0,
            "approach",
            progress=0.0,
            tangent=profiles[0].tangents[0],
        )

    for stroke_index, stroke in enumerate(strokes):
        if (
            inkstone is not None
            and stroke_index > 0
            and stroke_index % inkstone.reink_interval_strokes == 0
        ):
            append_ink_cycle(stroke_index)
        profile = profiles[stroke_index]
        # Kaisho XY micro-motions (逆入・回鋒・転折) live in path_delta; Z
        # follows calligraphy pressure, not AnimCJK sample widths.
        draw_xy = stroke.points + profile.path_delta
        pressure_track = profile.pressure.copy()
        width_track = profile.width.copy()
        # Seat the tip lightly at the first real XY sample.  The following
        # sample performs the pressure transition while moving, so no
        # duplicate pen-down point can turn the entry into an ink blob.
        if len(pressure_track):
            pressure_track[0] *= entry_descent_ratio
            entry_width = _width_from_pressure(
                pressure_track[:1],
                profile.body_width
                or 0.55 * (brush.minimum_width + brush.maximum_width),
                brush,
            )[0]
            width_track[0] = min(width_track[0], entry_width)
        neutral_contact_z = pen_down_z + brush.nominal_compression
        draw_z = (
            neutral_contact_z
            - brush.nominal_compression * pressure_track
            + brush.release_clearance * _release_envelope(pressure_track)
        )
        start = np.asarray([*draw_xy[0], draw_z[0]])
        contact_ready = np.asarray([*start[:2], neutral_contact_z])
        start_safe = np.asarray([*start[:2], safe_height])
        if routed_transport:
            preparation = np.asarray(
                [
                    *_upright_transport_point(
                        start[:2],
                        transport_origin,
                        transport_radius,
                    ),
                    transport_height,
                ]
            )
            route = _upright_transport_route(
                current,
                preparation,
                origin=transport_origin,
                arc_radius=transport_radius,
                spacing=transition_spacing,
            )
            if len(route):
                append(
                    route,
                    False,
                    stroke_index,
                    "travel",
                    progress=0.0,
                    tangent=profile.tangents[0],
                )
            current = preparation
        elif not np.allclose(current[:2], start[:2]):
            travel_target = start_safe
            append(
                _segment(current, travel_target, transition_spacing),
                False,
                stroke_index,
                "tilted_travel" if brushwork_mode == "professional" else "travel",
                progress=0.0,
                tangent=profile.tangents[0],
            )
            current = travel_target
        if (
            brushwork_mode == "professional"
            and brush.tilt_prepare_steps
            and (routed_transport or exposed_horizontal[stroke_index, 0])
        ):
            # Turn the one-axis attachment inside its upright-reachable annulus,
            # then make only the short out-of-annulus approach while tilted.
            append(
                np.repeat(current[None, :], brush.tilt_prepare_steps, axis=0),
                False,
                stroke_index,
                "tilt_prepare",
                progress=0.0,
                tangent=profile.tangents[0],
                roll=profile.roll[0],
                brush_phase="entry",
            )
        if routed_transport:
            # A low horizontal traverse folds the wrist into a second IK
            # branch over the inner A4 cells. Approach diagonally from the
            # transport circle and leave only the final 10 mm for descent.
            approach = contact_ready.copy()
            approach[2] += 0.010
            append(
                _segment(current, approach, transition_spacing),
                False,
                stroke_index,
                "tilted_approach",
                progress=0.0,
                tangent=profile.tangents[0],
                roll=profile.roll[0],
                brush_phase="entry",
            )
            current = approach

        append(
            _segment(current, contact_ready, transition_spacing),
            False,
            stroke_index,
            "lower",
            progress=0.0,
            tangent=profile.tangents[0],
        )
        current = contact_ready
        down_points = np.column_stack((draw_xy, draw_z))
        profile_indices = np.arange(len(down_points))
        append(
            down_points,
            True,
            stroke_index,
            "draw",
            progress=profile.progress[profile_indices],
            tangent=profile.tangents[profile_indices],
            pressure=pressure_track,
            speed=profile.speed[profile_indices],
            width=width_track,
            roll=profile.roll[profile_indices],
            brush_phase=tuple(profile.phases[index] for index in profile_indices),
        )
        current = down_points[-1]

        lift_xy = current[:2].copy()
        if profile.technique in ("hane", "harai"):
            # Continue along the real outgoing path while releasing pressure;
            # tome remains a nearly vertical lift from a full terminal.
            lift_xy += profile.tangents[-1] * 0.008
        lift_height = (
            float(current[2] + 0.010) if routed_transport else safe_height
        )
        lift_target = np.asarray([*lift_xy, lift_height])
        phase = "finish_lift" if stroke_index == len(trajectory.strokes) - 1 else "lift"
        append(
            _segment(current, lift_target, transition_spacing),
            False,
            stroke_index,
            phase,
            progress=1.0,
            tangent=profile.tangents[-1],
            roll=profile.roll[-1],
            brush_phase=profile.phases[-1],
        )
        current = lift_target
        if routed_transport:
            release = np.asarray(
                [
                    *_upright_transport_point(
                        lift_xy,
                        transport_origin,
                        transport_radius,
                    ),
                    transport_height,
                ]
            )
            if not np.allclose(current, release):
                append(
                    _segment(current, release, transition_spacing),
                    False,
                    stroke_index,
                    "tilted_retreat",
                    progress=1.0,
                    tangent=profile.tangents[-1],
                    roll=profile.roll[-1],
                    brush_phase=profile.phases[-1],
                )
                current = release
        if brushwork_mode == "professional" and brush.tilt_prepare_steps:
            # Finish lifting and, if necessary, retreat into the reachable
            # annulus before changing attachment angle.
            append(
                np.repeat(current[None, :], brush.tilt_prepare_steps, axis=0),
                False,
                stroke_index,
                "tilt_release",
                progress=1.0,
                tangent=profile.tangents[-1],
                roll=profile.roll[-1],
                brush_phase="transport",
            )

    return WaypointSequence(
        positions=np.asarray(positions),
        pen_down=np.asarray(pen_down),
        stroke_indices=np.asarray(stroke_indices),
        phases=tuple(phases),
        stroke_progress=np.asarray(stroke_progress),
        target_tangents=np.asarray(target_tangents),
        target_pressure=np.asarray(target_pressure),
        target_speed=np.asarray(target_speed),
        target_width=np.asarray(target_width),
        target_roll=np.asarray(target_roll),
        techniques=tuple(techniques),
        brushwork_phases=tuple(brushwork_phases),
    )
