"""MuJoCo/Gymnasium SO-101 trajectory-following environment."""

from __future__ import annotations

from dataclasses import replace
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping, Sequence

import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

from so101_calligraphy.brush_physics import BrushPhysics, BrushState, brush_model_xml, refresh_world_collision_bounds
from so101_calligraphy.config import (
    EnvConfig,
    InkstoneConfig,
    JOINT_LIMITS,
    JOINT_NAMES,
)
from so101_calligraphy.ink_model import make_ink_model
from so101_calligraphy.metrics import (
    BEAUTY_COMPONENT_WEIGHTS,
    WIDTH_DETAIL_KEYS,
    aggregate_beauty_components,
    character_balance,
    glyph_mask_quality,
    endpoint_shape_quality,
    smooth_motion_quality,
    stroke_quality,
)
from so101_calligraphy.trajectory import (
    Trajectory,
    build_waypoint_sequence,
    load_svg_trajectory,
    primitive_trajectory,
)
from so101_calligraphy.trajectory.layout import (
    frame_paper,
    place_in_cell,
    writing_frames,
)
from so101_calligraphy.trajectory.profile import technique_one_hot
from so101_calligraphy.trajectory.clearance import (
    CONTACT_REQUIRED_PRESSURE,
    exposed_horizontal_endpoints,
)
from so101_calligraphy.trajectory.professional import (
    exemplar_thumbnail,
    fit_trajectory_to_exemplar_shape,
    refine_trajectory_to_exemplar,
    render_professional_mask,
    sample_paper_mask,
)
from so101_calligraphy.pressure_calibration import (
    DEFAULT_BRUSH_FINGERPRINT,
    DEFAULT_CAD_FINGERPRINT,
    PressureCalibration,
)


EPISODE_PHASES = ("load", "wipe", "carry", "draw", "transition", "finish")
EXEMPLAR_THUMBNAIL_SIZE = 16
EXEMPLAR_PATCH_SIZE = 5
EXEMPLAR_OBSERVATION_SIZE = (
    EXEMPLAR_THUMBNAIL_SIZE**2 + 2 * EXEMPLAR_PATCH_SIZE**2
)


def _interpolate_segment_progress(
    start: np.ndarray,
    end: np.ndarray,
    point: np.ndarray,
    start_progress: float,
    end_progress: float,
) -> float:
    """Project the live tip onto one waypoint segment for smooth phase control."""

    segment = np.asarray(end, dtype=np.float64) - np.asarray(start, dtype=np.float64)
    length_sq = float(segment @ segment)
    if length_sq <= 1e-12:
        return float(end_progress)
    fraction = float(
        np.clip(
            (np.asarray(point, dtype=np.float64) - start) @ segment / length_sq,
            0.0,
            1.0,
        )
    )
    return float(start_progress + fraction * (end_progress - start_progress))


def contact_pressure_gain_scale(
    technique: str,
    progress: float,
    *,
    harai_scale: float = 1.6,
    hane_release_scale: float = 1.0,
) -> float:
    """Scale contact-pressure feedback by stroke technique.

    払いは抜きなので持ち上げが有利。はねは蓄力してから趯するので、
    一律の持ち上げは蓄力を潰す。
    """

    # 2026-08-20: gain を 0.005 -> 0.015 に上げたのに合わせて再調整。
    # 払い 1.4 -> 1.6 で IoU +1.0 / glyph_shape +0.9（払い finish は -0.5）。
    # はねは 0.35 -> 0.20 でも回復しなかったが、払い 1.6 との組み合わせが最良。
    if technique == "harai":
        return harai_scale
    if technique == "hane":
        return 0.20 if progress < 0.85 else hane_release_scale
    return 1.0


def contact_pressure_direction_scale(
    family: str,
    tangent: np.ndarray,
    *,
    turning_glyph: bool = False,
    left_horizontal_glyph: bool = False,
) -> float:
    """Compensate straight vertical strokes without overdriving turns."""

    direction = np.asarray(tangent, dtype=np.float64)
    if turning_glyph or left_horizontal_glyph or family == "zhe":
        return 7.0 / 6.0
    return (
        9.0 / 7.0
        if family == "shu" and abs(direction[1]) > abs(direction[0])
        else 1.0
    )


def contact_orientation_family_scale(
    family: str,
    *,
    turning_glyph: bool = False,
) -> float:
    """Keep tip position primary while the analytical hinge turns a corner."""

    return 1.0 / 3.0 if turning_glyph or family == "zhe" else 1.0


def _pressure_from_contact_force(contact_force: float, nominal_force: float) -> float:
    """Map measured normal force to calligraphy pressure."""

    return float(
        np.clip(1.0 - np.exp(-max(contact_force, 0.0) / nominal_force), 0.0, 1.5)
    )


def _filter_contact_pressure(
    previous: float,
    measured: float,
    *,
    contact: bool,
    maximum_change: float = 0.12,
    response: float = 1.0,
) -> float:
    """Model the short elastic response of a 38 mm tuft to solver force."""

    if not contact:
        return 0.0
    limited_change = np.clip(measured - previous, -maximum_change, maximum_change)
    # The bundle opens progressively under load but springs back as soon as
    # the robot unloads it. Delaying both directions leaves false pressure at
    # hane/harai/tome finishes even after the physical force has dropped.
    applied_response = 1.0 if measured < previous else response
    return float(previous + applied_response * limited_change)


def _next_contact_pressure_offset(
    current: float,
    error: float,
    gain: float,
    limit: float,
) -> float:
    """Leaky integral pressure control bounded by physical travel."""

    return float(np.clip(0.995 * current + 0.10 * gain * error, -limit, limit))


def _touchdown_error_scale(dwell: int) -> float:
    """Start softly, then restore full descent authority within 40 steps."""

    return float(np.clip(0.05 + 0.95 * max(0, dwell) / 40.0, 0.05, 1.0))


def harai_finish_release(
    *,
    width: float,
    target_width: float,
    pressure: float,
    target_pressure: float,
    speed: float,
    target_speed: float,
) -> float:
    """Match evaluation finish (width/pressure/speed; outgoing is already saturated)."""

    finish_width = float(
        np.exp(
            -(((width - target_width) / max(0.32 * target_width, 0.0012)) ** 2)
        )
    )
    finish_pressure = float(
        np.exp(-(((pressure - target_pressure) / 0.24) ** 2))
    )
    finish_speed = float(
        np.exp(-(((speed - target_speed) / 0.065) ** 2))
    )
    return (
        0.417 * finish_width + 0.333 * finish_pressure + 0.250 * finish_speed
    )


class CalligraphyEnv(gym.Env[np.ndarray, np.ndarray]):
    """Trace ordered strokes on A4 paper using SO-101 joint commands.

    Actions are normalized incremental targets for the five arm joints and the
    gripper joint. The gripper is the brush-tilt hinge (Fusion `so101書道`).
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 50}

    def __init__(
        self,
        task: str = "line",
        *,
        svg_path: str | Path | None = None,
        trajectory: Trajectory | None = None,
        trajectories: Sequence[Trajectory] | None = None,
        config: EnvConfig | None = None,
        render_mode: str | None = None,
    ) -> None:
        super().__init__()
        if render_mode not in (*self.metadata["render_modes"], None):
            raise ValueError(f"Unsupported render_mode: {render_mode!r}")
        supplied = sum(value is not None for value in (svg_path, trajectory, trajectories))
        if supplied > 1:
            raise ValueError("Pass at most one of svg_path, trajectory and trajectories.")
        if trajectories is not None and not trajectories:
            raise ValueError("trajectories must not be empty.")

        self.config = config or EnvConfig()
        self._pressure_calibration = self._load_pressure_calibration()
        self._layout_index = 0
        source_paper = frame_paper(
            self.config.paper, self.config.writing_layout, self._layout_index
        )
        self._inkstone_pose_offset = np.zeros(3, dtype=np.float64)
        self.task = task
        if trajectories is not None:
            # Preserve lazy random-access datasets; materializing all 2,136
            # joyo trajectories at every vector-env construction is wasteful.
            self.trajectories = trajectories
        elif trajectory is not None:
            self.trajectories = (trajectory,)
        elif svg_path is not None:
            self.trajectories = (
                load_svg_trajectory(
                    svg_path, paper=source_paper, spacing=self.config.path_spacing
                ),
            )
        else:
            self.trajectories = (
                primitive_trajectory(
                    task, paper=source_paper, spacing=self.config.path_spacing
                ),
            )
        self._trajectory_index = 0
        self._professional_mask: np.ndarray | None = None
        self._exemplar_thumbnail = np.zeros(
            (EXEMPLAR_THUMBNAIL_SIZE, EXEMPLAR_THUMBNAIL_SIZE),
            dtype=np.float32,
        )
        self._pressure_scale = 1.0
        self._pressure_scale_cache: dict[str, float] = {}
        self._tilt_prepare_goals: dict[int, np.ndarray] = {}
        self._unavailable_tilt_prepare_goals: set[int] = set()
        self.trajectory = self._prepare_trajectory(
            self._trajectory_for_layout(self.trajectories[0], self._layout_index)
        )
        self._exposed_horizontal = exposed_horizontal_endpoints(
            self.trajectory.strokes,
            junction_tolerance=self.config.stroke_junction_tolerance,
        )
        self.waypoints = build_waypoint_sequence(
            self.trajectory,
            pen_down_z=self.config.pen_down_z,
            safe_height=self.config.safe_height,
            transition_spacing=self.config.transition_spacing,
            brush=self.config.brush,
            brushwork_mode=self.config.modules.brushwork,
            inkstone=self._effective_inkstone(),
            stroke_minimum_gap=self.config.stroke_minimum_gap,
            pressure_scale=self._pressure_scale,
            entry_descent_ratio=self.config.entry_descent_ratio,
            stroke_junction_tolerance=self.config.stroke_junction_tolerance,
            stroke_clearance_floor=self.config.stroke_clearance_floor,
            observed_width_p90_by_phase=self._probe_width_p90_by_phase(),
            staging_xy=(
                self.config.hardware.base_position_xy_m[0]
                + self.config.hardware.shoulder_pivot_offset_x_m
                + self.config.hardware.upright_transport_radius_m,
                self.config.hardware.base_position_xy_m[1],
            ),
            transport_origin_xy=(
                self.config.hardware.base_position_xy_m[0]
                + self.config.hardware.shoulder_pivot_offset_x_m,
                self.config.hardware.base_position_xy_m[1],
            ),
            transport_radius=self.config.hardware.upright_transport_radius_m,
            transport_height=self.config.hardware.upright_transport_height_m,
        )

        model_resource = files("so101_calligraphy").joinpath("assets/so101_calligraphy.xml")
        # MuJoCo fopen fails on non-ASCII user paths (Windows 電研). Load as text.
        self.model = mujoco.MjModel.from_xml_string(
            brush_model_xml(
                total_length_m=(
                    0.038 * self.config.hardware.brush_tip_length_scale
                ),
                tuft_length_m=self.config.hardware.brush_tuft_length_m,
                distributed_contact=self.config.brush.distributed_contact,
            )
            if (
                self.config.brush.distributed_contact
                or self.config.hardware.brush_tip_length_scale != 1.0
                or self.config.hardware.brush_tuft_length_m != 0.038
            )
            else model_resource.read_text(encoding="utf-8")
        )
        self.data = mujoco.MjData(self.model)
        self._safety_data = mujoco.MjData(self.model)
        self.render_mode = render_mode
        self._renderer: mujoco.Renderer | None = None
        self._viewer: Any | None = None

        self._joint_ids = np.asarray(
            [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, name) for name in JOINT_NAMES]
        )
        if np.any(self._joint_ids < 0):
            raise RuntimeError("Bundled MJCF is missing one or more SO-101 joints.")
        self._qpos_indices = np.asarray([self.model.jnt_qposadr[jid] for jid in self._joint_ids])
        self._qvel_indices = np.asarray([self.model.jnt_dofadr[jid] for jid in self._joint_ids])
        self._brush_site_id = self._named_id(mujoco.mjtObj.mjOBJ_SITE, "brush_tip_site")
        self._brush_mount_site_id = self._named_id(
            mujoco.mjtObj.mjOBJ_SITE, "brush_mount_site"
        )
        self._brush_rest_tip_site_id = self._named_id(
            mujoco.mjtObj.mjOBJ_SITE, "brush_rest_tip_site"
        )
        self.brush_physics = BrushPhysics(
            self.model,
            mode=self.config.modules.brush_physics,
            brush=self.config.brush,
            paper=self.config.paper,
        )
        self._brush_joint_ids = self.brush_physics.joint_ids
        self._target_body_id = self._named_id(mujoco.mjtObj.mjOBJ_BODY, "target_mocap")
        self._target_mocap_id = int(self.model.body_mocapid[self._target_body_id])
        self._paper_geom_id = self._named_id(mujoco.mjtObj.mjOBJ_GEOM, "paper")
        self._base_body_id = self._named_id(mujoco.mjtObj.mjOBJ_BODY, "base_link")
        self._floor_geom_id = self._named_id(mujoco.mjtObj.mjOBJ_GEOM, "floor")
        self._brush_geom_id = self._named_id(mujoco.mjtObj.mjOBJ_GEOM, "brush_tip")
        self._base_geom_id = self._named_id(mujoco.mjtObj.mjOBJ_GEOM, "base_geom")
        self._ink_pool_geom_id = self._named_id(mujoco.mjtObj.mjOBJ_GEOM, "ink_pool")
        self._inkstone_lip_geom_id = self._named_id(
            mujoco.mjtObj.mjOBJ_GEOM, "inkstone_lip"
        )
        self._inkstone_base_geom_id = self._named_id(
            mujoco.mjtObj.mjOBJ_GEOM, "inkstone_base"
        )
        self._wrist_flex_geom_id = self._named_id(
            mujoco.mjtObj.mjOBJ_GEOM, "wrist_flex_geom"
        )
        self._wrist_roll_geom_id = self._named_id(
            mujoco.mjtObj.mjOBJ_GEOM, "wrist_roll_geom"
        )
        self._gripper_body_geom_id = self._named_id(
            mujoco.mjtObj.mjOBJ_GEOM, "gripper_body_geom"
        )
        self._path_site_ids = np.asarray(
            [
                self._named_id(mujoco.mjtObj.mjOBJ_SITE, f"path_marker_{index:03d}")
                for index in range(96)
            ]
        )
        robot_geom_names = (
            "base_geom",
            "shoulder_pan_geom",
            "upper_arm_geom",
            "elbow_motor_geom",
            "lower_arm_geom",
            "wrist_flex_geom",
            "wrist_roll_geom",
            "gripper_body_geom",
            "tilt_yoke_geom",
            "brush_shaft",
            "brush_bristles",
            "brush_bristles_mid",
            "brush_bristles_tip",
            "brush_tip",
        )
        self._robot_geom_ids = {
            self._named_id(mujoco.mjtObj.mjOBJ_GEOM, name) for name in robot_geom_names
        }
        self._apply_fixed_layout()

        self._joint_limits = JOINT_LIMITS.copy()
        measured_ranges = self.config.hardware.joint_ranges_rad
        if measured_ranges is not None:
            ranges = np.asarray(measured_ranges, dtype=np.float64)
            if ranges.shape != (len(JOINT_NAMES), 2):
                raise ValueError("joint_ranges_rad must have shape (6, 2)")
            if not np.isfinite(ranges).all() or np.any(ranges[:, 1] <= ranges[:, 0]):
                raise ValueError("joint_ranges_rad must contain finite increasing ranges")
            self._joint_limits = np.sort(ranges, axis=1)
            for index, joint_id in enumerate(self._joint_ids):
                self.model.jnt_range[joint_id] = self._joint_limits[index]
                actuator_id = mujoco.mj_name2id(
                    self.model,
                    mujoco.mjtObj.mjOBJ_ACTUATOR,
                    f"{JOINT_NAMES[index]}_motor",
                )
                if actuator_id >= 0:
                    self.model.actuator_ctrlrange[actuator_id] = self._joint_limits[index]
        else:
            measured = self.config.hardware.gripper_range_rad
            if measured is not None:
                self._joint_limits[-1] = sorted(float(v) for v in measured)
                self.model.jnt_range[self._joint_ids[-1]] = self._joint_limits[-1]

        self.action_space = spaces.Box(-1.0, 1.0, shape=(len(JOINT_NAMES),), dtype=np.float32)
        observation_low = np.concatenate(
            (
                self._joint_limits[:, 0],
                np.full(6, -100.0),
                np.full(3, -2.0),
                np.full(3, -4.0),
                [0.0, 0.0],
                np.full(3, -10.0),
                np.full(3, -1.0),
                np.full(3, -0.1),
                [0.0, 0.0, 0.0],
                np.full(2, -1.0),
                [0.0, 0.0, 0.0, 0.0],
                np.zeros(3),
                [0.0],
            )
        )
        observation_high = np.concatenate(
            (
                self._joint_limits[:, 1],
                np.full(6, 100.0),
                np.full(3, 2.0),
                np.full(3, 4.0),
                [1.0, 1.0],
                np.full(3, 10.0),
                np.full(3, 1.0),
                np.full(3, 0.1),
                [2.0, 1.5, 1.5],
                np.full(2, 1.0),
                [1.5, 0.5, 0.03, 1.0],
                np.ones(3),
                [1.0],
            )
        )
        self.observation_version = self.config.observation_version or (
            2 if self.config.modules != type(self.config.modules)() else 1
        )
        if self.observation_version >= 2:
            observation_low = np.concatenate(
                (
                    observation_low,
                    np.full(3, -2.0),
                    np.zeros(4),
                    np.full(6, -20.0),
                    np.full(3, -1.0),
                    [-np.pi],
                    np.zeros(len(EPISODE_PHASES)),
                )
            )
            observation_high = np.concatenate(
                (
                    observation_high,
                    np.full(3, 2.0),
                    [1.5, 1.5, 1.0, 1.0],
                    np.full(6, 20.0),
                    np.full(3, 1.0),
                    [np.pi],
                    np.ones(len(EPISODE_PHASES)),
                )
            )
        if self.observation_version == 3:
            observation_low = np.concatenate(
                (observation_low, np.zeros(EXEMPLAR_OBSERVATION_SIZE))
            )
            observation_high = np.concatenate(
                (observation_high, np.ones(EXEMPLAR_OBSERVATION_SIZE))
            )
        self.observation_space = spaces.Box(
            low=observation_low.astype(np.float32),
            high=observation_high.astype(np.float32),
            dtype=np.float32,
        )

        self._target_index = 0
        self._target_dwell = 0
        self._step_count = 0
        self._previous_action = np.zeros(len(JOINT_NAMES), dtype=np.float64)
        self._previous_qvel = np.zeros(len(JOINT_NAMES), dtype=np.float64)
        self._joint_targets = np.zeros(len(JOINT_NAMES), dtype=np.float64)
        self._previous_brush_position = np.zeros(3, dtype=np.float64)
        self._tip_velocity = np.zeros(3, dtype=np.float64)
        self._previous_tip_velocity = np.zeros(3, dtype=np.float64)
        self._pressure = 0.0
        self._contact_pressure_offset = 0.0
        self._feedforward_pressure_offset = 0.0
        self._residual_pressure_offset = 0.0
        self._pressure_calibration_clipped = False
        self._pressure_calibration_fallback = False
        self._contact_dwell = 0
        self._contact_force = 0.0
        self._last_width = 0.0
        self._brush_state: BrushState | None = None
        self._latency_steps = self.config.servo_latency_steps
        self._command_queue: list[np.ndarray] = []
        self.ink = make_ink_model(
            self.config.modules.ink_model,
            self.config.paper,
            self.config.brush,
            self.config.ink,
        )
        self._stroke_records: list[dict[str, list[Any]]] = []
        self._pressure_calibration_samples: list[dict[str, Any]] = []
        self._stroke_scores: dict[int, dict[str, float]] = {}
        self._endpoint_scores: list[dict[str, float | int | str]] = []
        self._balance_metrics = {
            "centroid": 0.0,
            "scale": 0.0,
            "tilt": 0.0,
            "score": 0.0,
        }
        self._beauty_score = 0.0
        self._beauty_components = {
            name: 0.0 for name in BEAUTY_COMPONENT_WEIGHTS
        }
        self._width_details = {
            name: 0.0
            for name in (*WIDTH_DETAIL_KEYS, "stroke_width_hierarchy")
        }
        self._glyph_metrics = {
            "iou": 0.0,
            "dice": 0.0,
            "negative_space": 0.0,
            "score": 0.0,
        }
        self._motion_metrics = {
            "tip_jerk": 0.0,
            "joint_jerk": 0.0,
            "vertical": 0.0,
            "score": 0.0,
        }
        self._tip_velocity_history: list[np.ndarray] = []
        self._joint_acceleration_history: list[np.ndarray] = []
        self._episode_collision = False
        self._collision_line_search_stalls = 0
        self._loaded_ink_peak = 0.0
        self._wiped_excess_min = 1.0
        self._image_error = 0.0

        self._base_paper_friction = self.model.geom_friction[self._paper_geom_id].copy()
        self._base_dof_damping = self.model.dof_damping.copy()
        self._base_dof_friction = self.model.dof_frictionloss.copy()
        self._base_actuator_gain = self.model.actuator_gainprm.copy()
        self._base_actuator_bias = self.model.actuator_biasprm.copy()
        self._base_brush_stiffness = self.model.jnt_stiffness[self._brush_joint_ids].copy()
        self._brush_bristle_body_id = self._named_id(
            mujoco.mjtObj.mjOBJ_BODY, "brush_bristle_link"
        )
        self._base_brush_mount_site = self.model.site_pos[
            self._brush_mount_site_id
        ].copy()
        self._base_brush_rest_tip_site = self.model.site_pos[
            self._brush_rest_tip_site_id
        ].copy()
        self._base_brush_bristle_body = self.model.body_pos[
            self._brush_bristle_body_id
        ].copy()
        self._base_inkstone_base_pos = self.model.geom_pos[
            self._inkstone_base_geom_id
        ].copy()
        self._base_ink_pool_pos = self.model.geom_pos[self._ink_pool_geom_id].copy()
        self._base_inkstone_lip_pos = self.model.geom_pos[
            self._inkstone_lip_geom_id
        ].copy()
        self._inkstone_pose_offset = np.zeros(3, dtype=np.float64)
        self._apply_hardware_pose()
        self._set_path_markers()

    def _named_id(self, object_type: mujoco.mjtObj, name: str) -> int:
        object_id = mujoco.mj_name2id(self.model, object_type, name)
        if object_id < 0:
            raise RuntimeError(f"Bundled MJCF is missing {name!r}.")
        return object_id

    @property
    def target_position(self) -> np.ndarray:
        index = min(self._target_index, len(self.waypoints) - 1)
        return self.waypoints.positions[index]

    @property
    def progress(self) -> float:
        return min(self._target_index / max(len(self.waypoints) - 1, 1), 1.0)

    @property
    def brush_position(self) -> np.ndarray:
        return self.data.site_xpos[self._brush_site_id].copy()

    @property
    def controlled_brush_position(self) -> np.ndarray:
        """Contact tip the controller tracks. Ink uses the same site."""

        return self.brush_position

    @property
    def brush_axis(self) -> np.ndarray:
        axis = (
            self.data.site_xpos[self._brush_site_id]
            - self.data.site_xpos[self._brush_mount_site_id]
        )
        return axis / max(float(np.linalg.norm(axis)), 1e-12)

    @property
    def brush_mount_axis(self) -> np.ndarray:
        return self.data.site_xmat[self._brush_mount_site_id].reshape(3, 3)[:, 0].copy()

    @property
    def brush_deflection(self) -> np.ndarray:
        return (
            self.data.site_xpos[self._brush_site_id]
            - self.data.site_xpos[self._brush_rest_tip_site_id]
        ).copy()

    @property
    def beauty_score(self) -> float:
        return self._beauty_score

    @property
    def beauty_components(self) -> dict[str, float]:
        return self._beauty_components.copy()

    @property
    def endpoint_metrics(self) -> dict[str, float | int]:
        scores = [
            float(item.get("wedge", item["score"])) for item in self._endpoint_scores
        ]
        return {
            "count": len(scores),
            "sum": 100.0 * float(sum(scores)),
            "mean": 100.0 * float(np.mean(scores)) if scores else 100.0,
            "minimum": 100.0 * float(np.min(scores)) if scores else 100.0,
        }

    def _prepare_trajectory(self, trajectory: Trajectory) -> Trajectory:
        if (
            not self.config.modules.professional_exemplar
            or trajectory.character is None
        ):
            self._professional_mask = None
            self._exemplar_thumbnail.fill(0.0)
            return trajectory
        # 骨格とお手本で字の縦横比が食い違うため、まず外形を合わせる。
        # 局所リファインは法線方向 ±8mm しか動けず、数十 mm の寸法差は直せない。
        trajectory = fit_trajectory_to_exemplar_shape(
            trajectory,
            frame_paper(
                self.config.paper,
                self.config.writing_layout,
                self._layout_index,
            ),
            font_path=self.config.motoya_font_path,
            strength=self.config.exemplar_shape_fit,
        )
        target_points = np.concatenate(
            [stroke.points for stroke in trajectory.strokes], axis=0
        )
        self._professional_mask = render_professional_mask(
            trajectory.character,
            target_points,
            self.config.paper,
            self.config.ink,
            self.config.motoya_font_path,
        )
        self._exemplar_thumbnail = exemplar_thumbnail(
            self._professional_mask,
            EXEMPLAR_THUMBNAIL_SIZE,
        )
        self._pressure_scale = self._resolve_pressure_scale(trajectory)
        return refine_trajectory_to_exemplar(
            trajectory,
            self._professional_mask,
            self.config.paper,
            self.config.ink,
            strength=self.config.exemplar_motion_strength,
        )

    def _trajectory_for_layout(
        self, trajectory: Trajectory, layout_index: int
    ) -> Trajectory:
        """Place one glyph in one of the six fixed A4 writing frames."""

        if trajectory.character is None:
            return trajectory
        center, size = writing_frames(
            self.config.paper, self.config.writing_layout
        )[layout_index]
        return place_in_cell(trajectory, center, size)

    def _small_glyph_scales(self, trajectory: Trajectory) -> np.ndarray:
        """画ごとの筆圧倍率。小さく書く字は線も細くする。

        線幅 11mm のままだと、田のように内部に線が入る字は 60mm を切ると
        布白が潰れる。実際の書でも小さい字は細い筆に持ち替える。
        一枚に複数字を置くと字ごとに大きさが違うので、画単位で決める。
        """

        count = len(trajectory.strokes)
        reference = self.config.small_glyph_reference
        if reference <= 0.0:
            return np.ones(count)
        # 近接する画を一字とみなしてまとめ、その広がりで判断する。
        spans = np.empty(count)
        centers = np.asarray([s.points.mean(axis=0) for s in trajectory.strokes])
        extents = np.asarray([
            np.max(s.points.max(axis=0) - s.points.min(axis=0))
            for s in trajectory.strokes
        ])
        for index in range(count):
            near = np.linalg.norm(centers - centers[index], axis=1) <= max(
                float(extents[index]), reference
            )
            points = np.concatenate(
                [trajectory.strokes[j].points for j in np.flatnonzero(near)], axis=0
            )
            spans[index] = float(np.max(points.max(axis=0) - points.min(axis=0)))
        ratio = np.clip(spans / reference, 0.0, 1.0) ** 1.5
        return np.maximum(self.config.small_glyph_floor, ratio)

    def _resolve_pressure_scale(self, trajectory: Trajectory):
        """字ごとの筆圧倍率。同じ字なら使い回す（1 字あたり十数 ms かかる）。"""

        small = self._small_glyph_scales(trajectory)
        strength = self.config.exemplar_density_fit
        if strength <= 0.0 or self._professional_mask is None:
            return small
        key = f"{trajectory.character or ''}:{self._layout_index}"
        cached = self._pressure_scale_cache.get(key)
        if cached is None:
            # brushwork -> trajectory -> sequence -> brushwork の循環を避けるため
            # ここで読み込む。
            from so101_calligraphy.brushwork import make_brushwork_planner
            from so101_calligraphy.trajectory.density import exemplar_pressure_scale

            planner = make_brushwork_planner(self.config.modules.brushwork)
            profiles = tuple(
                planner.plan(stroke, self.config.brush)
                for stroke in trajectory.strokes
            )
            cached = exemplar_pressure_scale(
                trajectory.strokes,
                profiles,
                self._professional_mask,
                self.config.paper,
                self.config.ink,
                self.config.brush,
            )
            self._pressure_scale_cache[key] = cached
        return small * (1.0 + strength * (cached - 1.0))

    def _exemplar_observation(self) -> np.ndarray:
        if self._professional_mask is None:
            return np.zeros(EXEMPLAR_OBSERVATION_SIZE, dtype=np.float64)
        tangent = np.asarray(self._target_metadata()["tangent"], dtype=np.float64)
        tangent /= max(float(np.linalg.norm(tangent)), 1e-12)
        normal = np.asarray([-tangent[1], tangent[0]], dtype=np.float64)
        offsets = np.linspace(-0.012, 0.012, EXEMPLAR_PATCH_SIZE)
        along, across = np.meshgrid(offsets, offsets)
        points = (
            self.controlled_brush_position[:2]
            + along.reshape(-1, 1) * tangent
            + across.reshape(-1, 1) * normal
        )
        target_patch = sample_paper_mask(
            self._professional_mask,
            points,
            self.config.paper,
            self.config.ink,
        )
        actual_patch = sample_paper_mask(
            self.ink.pigment,
            points,
            self.config.paper,
            self.config.ink,
        )
        return np.concatenate(
            (self._exemplar_thumbnail.reshape(-1), target_patch, actual_patch)
        )

    def _normalized_image_error(self) -> float:
        if self._professional_mask is None:
            return 0.0
        difference = np.mean(np.abs(self.ink.pigment - self._professional_mask))
        return float(difference / max(float(self._professional_mask.mean()), 0.01))

    def _episode_phase(self, index: int | None = None) -> str:
        target_index = min(
            self._target_index if index is None else index, len(self.waypoints) - 1
        )
        phase = self.waypoints.phases[target_index]
        if phase == "ink_load":
            return "load"
        if "wipe" in phase:
            return "wipe"
        if phase == "draw":
            return "draw"
        if phase == "finish_lift":
            return "finish"
        if phase in (
            "travel",
            "tilted_travel",
            "tilted_approach",
            "tilted_retreat",
            "inkstone_approach",
            "inkstone_lift",
            "inkstone_return",
        ):
            return "carry"
        return "transition"

    def _phase_one_hot(self, index: int | None = None) -> np.ndarray:
        result = np.zeros(len(EPISODE_PHASES), dtype=np.float64)
        result[EPISODE_PHASES.index(self._episode_phase(index))] = 1.0
        return result

    def _target_metadata(self, index: int | None = None) -> dict[str, Any]:
        target_index = min(
            self._target_index if index is None else index, len(self.waypoints) - 1
        )
        metadata = {
            "index": target_index,
            "phase": self.waypoints.phases[target_index],
            "stroke_index": int(self.waypoints.stroke_indices[target_index]),
            "down": bool(self.waypoints.pen_down[target_index]),
            "tangent": self.waypoints.target_tangents[target_index],
            "pressure": float(self.waypoints.target_pressure[target_index]),
            "speed": float(self.waypoints.target_speed[target_index]),
            "width": float(self.waypoints.target_width[target_index]),
            "roll": float(self.waypoints.target_roll[target_index]),
            "stroke_progress": float(self.waypoints.stroke_progress[target_index]),
            "technique": self.waypoints.techniques[target_index],
            "brushwork_phase": self.waypoints.brushwork_phases[target_index],
        }
        if (
            target_index == self._target_index
            and target_index > 0
            and metadata["down"]
            and self.waypoints.pen_down[target_index - 1]
            and self.waypoints.stroke_indices[target_index - 1]
            == metadata["stroke_index"]
        ):
            # Pressure and width are continuous physical quantities. Chasing
            # the next sparse waypoint's endpoint value for the whole segment
            # made the pressure loop lag and then overshoot at every sample.
            fraction = _interpolate_segment_progress(
                self.waypoints.positions[target_index - 1, :2],
                self.waypoints.positions[target_index, :2],
                self.controlled_brush_position[:2],
                0.0,
                1.0,
            )
            previous_weight = 1.0 - fraction
            for key, values in (
                ("pressure", self.waypoints.target_pressure),
                ("speed", self.waypoints.target_speed),
                ("width", self.waypoints.target_width),
                ("roll", self.waypoints.target_roll),
                ("stroke_progress", self.waypoints.stroke_progress),
            ):
                metadata[key] = float(
                    previous_weight * values[target_index - 1]
                    + fraction * values[target_index]
                )
            tangent = (
                previous_weight * self.waypoints.target_tangents[target_index - 1]
                + fraction * self.waypoints.target_tangents[target_index]
            )
            norm = float(np.linalg.norm(tangent))
            if norm > 1e-12:
                metadata["tangent"] = tangent / norm
        return metadata

    def _desired_brush_axis(
        self,
        index: int | None = None,
        *,
        follow_tip: bool = False,
    ) -> np.ndarray:
        """穂の狙いの姿勢。相によって寝かせ方と向きを変える。

        従来は接地中つねに「進行方向の逆へ一定量だけ寝かせる」だけだった。
        楷書の起筆が三角に見えるのは、穂を斜めに寝かせて押し当てるから接地面が
        その向きへ伸びるためで、姿勢が一定では原理的に出ない。
        """

        target_index = min(
            self._target_index if index is None else index,
            len(self.waypoints) - 1,
        )
        metadata = self._target_metadata(index)
        motion_progress = float(metadata["stroke_progress"])
        brush = self.config.brush
        tangent = np.asarray(metadata["tangent"], dtype=np.float64)
        norm = float(np.linalg.norm(tangent))
        tangent = tangent / norm if norm > 1e-9 else np.asarray([1.0, 0.0])
        phase = metadata["brushwork_phase"]
        waypoint_phase = metadata["phase"]
        stroke_index = metadata["stroke_index"]
        has_stroke = 0 <= stroke_index < len(self.trajectory.strokes)
        # Local import avoids brushwork -> trajectory.sequence -> environment
        # initialization cycle.
        from so101_calligraphy.brushwork import classify_stroke_family

        family = (
            classify_stroke_family(self.trajectory.strokes[stroke_index])
            if has_stroke
            else "heng"
        )
        fixed_phases = (
            "tilt_prepare",
            "tilted_approach",
            "lower",
            "lift",
            "finish_lift",
            "tilted_retreat",
        )
        if self._uses_fixed_contact_lean(target_index) and (
            metadata["down"] or waypoint_phase in fixed_phases
        ):
            # Hold one physical lean opposite the stroke (逆入). The far upper
            # 85 mm frame floors at 45°, so it keeps a 30° fixed lean instead.
            lean = brush.fixed_contact_lean
            if self._layout_index == 0:
                lean = min(lean, float(np.tan(np.deg2rad(30.0))))
            direction = -tangent
            axis = np.asarray(
                [
                    lean * direction[0],
                    lean * direction[1],
                    -1.0,
                ],
                dtype=np.float64,
            )
            return axis / np.linalg.norm(axis)
        if waypoint_phase in (
            "tilt_prepare",
            "tilted_approach",
            "lift",
            "finish_lift",
            "tilted_retreat",
        ):
            axis = np.asarray(
                [
                    -brush.airborne_lean * tangent[0],
                    -brush.airborne_lean * tangent[1],
                    -1.0,
                ],
                dtype=np.float64,
            )
            return axis / np.linalg.norm(axis)
        exposed_start = bool(has_stroke and self._exposed_horizontal[stroke_index, 0])
        exposed_finish = bool(has_stroke and self._exposed_horizontal[stroke_index, 1])
        prepares_entry = waypoint_phase in (
            "tilt_prepare",
            "tilted_approach",
            "lower",
        )
        holds_finish = waypoint_phase in (
            "lift",
            "finish_lift",
            "tilted_retreat",
        )
        if not metadata["down"] and not prepares_entry and not holds_finish:
            return np.asarray([0.0, 0.0, -1.0], dtype=np.float64)
        lean = brush.sweep_lean if family in {"pie", "na"} else brush.desired_lean
        if phase == "corner":
            lean = brush.corner_lean
        entry_lean = self._effective_entry_lean()
        # 既定は進行方向の逆へ寝かせる（穂が後ろに従う）。
        direction = -tangent
        send_lean = brush.sweep_lean if family in {"pie", "na"} else brush.desired_lean
        # Live control only: 30° is for a seated tip. Reset IK still solves
        # the full entry pose so the approach starts already leaned.
        seated = 1.0
        if follow_tip:
            seated = float(
                np.clip(
                    1.0
                    - np.linalg.norm(
                        (self.target_position - self.controlled_brush_position)[:2]
                    )
                    / 0.016,
                    0.0,
                    1.0,
                )
            )
        if (
            (motion_progress <= brush.entry_lean_end or prepares_entry)
            and exposed_start
            and entry_lean > 0.0
        ):
            # Exposed horizontal entry: 30° contact returning to send by 5%.
            blend = 0.0
            if metadata["down"]:
                value = np.clip(
                    motion_progress / brush.entry_lean_end,
                    0.0,
                    1.0,
                )
                blend = float(value * value * (3.0 - 2.0 * value))
            lean = (1.0 - blend) * entry_lean + blend * send_lean
            lean = send_lean + seated * (lean - send_lean)
            # The attachment has one tilt hinge. Keep one shaft azimuth for
            # the whole stroke and vary only its lean magnitude (30 -> 8 deg),
            # otherwise the wrist must cross a different IK basin on paper.
            direction = -tangent
        elif (
            (phase == "finish" or holds_finish)
            and metadata["technique"] == "tome"
            and exposed_finish
        ):
            # Stop / return: continuously raise through vertical, then lean
            # 30 degrees into the return direction while the tuft leaves.
            value = np.clip((motion_progress - 0.84) / 0.16, 0.0, 1.0)
            blend = 1.0 if holds_finish else float(value * value * (3.0 - 2.0 * value))
            signed_lean = -(1.0 - blend) * lean + blend * brush.finish_lean
            direction = tangent if signed_lean >= 0.0 else -tangent
            lean = abs(signed_lean)
            lean = send_lean + seated * (lean - send_lean)
        elif phase == "finish" and metadata["technique"] in ("hane", "harai"):
            # Lift the shaft continuously to 4° through a hook/sweep release.
            release_start = 0.58 if metadata["technique"] == "harai" else 0.65
            value = np.clip(
                (motion_progress - release_start) / (1.0 - release_start),
                0.0,
                1.0,
            )
            blend = float(value * value * (3.0 - 2.0 * value))
            lean = (1.0 - blend) * lean + blend * brush.release_lean
        axis = np.asarray(
            [lean * direction[0], lean * direction[1], -1.0], dtype=np.float64
        )
        return axis / np.linalg.norm(axis)

    def _set_path_markers(self) -> None:
        points = np.concatenate([stroke.points for stroke in self.trajectory.strokes], axis=0)
        if len(points) > len(self._path_site_ids):
            indices = np.linspace(0, len(points) - 1, len(self._path_site_ids)).round().astype(int)
            points = points[indices]
        for marker_index, site_id in enumerate(self._path_site_ids):
            if marker_index < len(points):
                self.model.site_pos[site_id] = (
                    points[marker_index, 0],
                    points[marker_index, 1],
                    self.config.paper.surface_z + 0.001,
                )
                self.model.site_rgba[site_id] = (0.15, 0.45, 0.95, 0.55)
            else:
                self.model.site_pos[site_id] = (0.0, 0.0, -1.0)
                self.model.site_rgba[site_id, 3] = 0.0

    def _set_target_marker(self) -> None:
        self.data.mocap_pos[self._target_mocap_id] = self.target_position
        target_site_id = self._named_id(mujoco.mjtObj.mjOBJ_SITE, "target_marker")
        if self._episode_phase() in ("load", "wipe"):
            self.model.site_rgba[target_site_id] = (0.55, 0.15, 0.80, 0.9)
        elif self.waypoints.pen_down[min(self._target_index, len(self.waypoints) - 1)]:
            self.model.site_rgba[target_site_id] = (0.95, 0.12, 0.12, 0.9)
        else:
            self.model.site_rgba[target_site_id] = (0.10, 0.75, 0.35, 0.9)

    def _solve_position_ik(
        self,
        target: np.ndarray,
        *,
        directional_axis: bool | None = True,
        orientation_tolerance: float = np.deg2rad(5.0),
    ) -> np.ndarray:
        """Deterministic multi-start DLS reset IK; policy stays joint-space."""

        base_xy = self.model.body_pos[self._base_body_id, :2]
        radial = float(
            np.arctan2(
                target[1] - base_xy[1],
                target[0]
                - (base_xy[0] + self.config.hardware.shoulder_pivot_offset_x_m),
            )
        )
        # Start with the historical elbow-up seed, then try distinct elbow-up
        # basins. This uses only NumPy/MuJoCo and is deterministic across envs.
        seeds = (
            tuple(self.data.qpos[self._qpos_indices]),
            *((radial, *fold) for fold in self.config.hardware.reset_ik_seed_folds_rad),
            (radial, -1.00, 1.50, -1.50, 0.00, np.pi / 4.0),
            (radial, -1.30, 1.50, -1.10, 0.00, np.pi / 4.0),
            (radial, -0.72, 1.22, -1.32, 0.00, np.pi / 4.0),
            (radial, -0.42, 0.92, -1.08, 0.00, np.pi / 4.0),
            # The near-left A4 frames use the same elbow-up arm posture but
            # need the wrist rolled around the attachment axis. Without these
            # two basins DLS converges to the gripper limit even though a
            # zero-error, five-degree-margin solution exists.
            (radial, -0.10, 1.20, 0.95, 2.35, 0.00),
            (radial, -0.10, 1.20, 0.95, -2.35, 0.00),
            (radial - 0.25, -1.05, 1.42, -1.35, 0.25, np.pi / 4.0),
            (radial + 0.25, -1.05, 1.42, -1.35, -0.25, np.pi / 4.0),
            (radial - 0.18, -0.65, 1.12, -1.08, -0.35, np.pi / 4.0),
            (radial + 0.18, -0.65, 1.12, -1.08, 0.35, np.pi / 4.0),
        )
        if self.config.legacy_attachment_compensation:
            fixed = self.config.hardware.fixed_attachment_servo_angle_rad
            seeds = tuple((*seed[:5], fixed) for seed in seeds)
            desired_axis = None
        else:
            desired_axis = self._desired_brush_axis()

        def orientation_error(mount_axis: np.ndarray) -> float:
            if desired_axis is None:
                return 0.0
            if directional_axis:
                return float(
                    np.arccos(np.clip(mount_axis @ desired_axis, -1.0, 1.0))
                )
            actual_lean = np.arccos(np.clip(-mount_axis[2], -1.0, 1.0))
            desired_lean = np.arccos(np.clip(-desired_axis[2], -1.0, 1.0))
            return float(abs(actual_lean - desired_lean))

        margin = np.deg2rad(5.0)
        lower = self._joint_limits[:, 0] + margin
        upper = self._joint_limits[:, 1] - margin
        best: tuple[float, np.ndarray, float, float, bool, float] | None = None
        for seed in seeds:
            self.data.qpos[self._qpos_indices] = np.clip(seed, lower, upper)
            for _ in range(220):
                mujoco.mj_forward(self.model, self.data)
                error = target - self.controlled_brush_position
                mount_axis = self.data.site_xmat[self._brush_mount_site_id].reshape(
                    3, 3
                )[:, 0]
                axis_error = orientation_error(mount_axis)
                if np.linalg.norm(error) < 5e-4 and axis_error < np.deg2rad(2.0):
                    break
                delta = np.clip(
                    self._dls_delta(
                        error,
                        desired_axis if directional_axis is not None else None,
                        include_tilt=True,
                        center_tilt=False,
                        directional_axis=directional_axis,
                    ),
                    -0.08,
                    0.08,
                )
                controlled = self._qpos_indices[: len(delta)]
                qpos = self.data.qpos[controlled] + delta
                self.data.qpos[controlled] = np.clip(
                    qpos, lower[: len(delta)], upper[: len(delta)]
                )
            mujoco.mj_forward(self.model, self.data)
            position_error = float(
                np.linalg.norm(target - self.controlled_brush_position)
            )
            mount_axis = self.data.site_xmat[self._brush_mount_site_id].reshape(
                3, 3
            )[:, 0]
            axis_error = orientation_error(mount_axis)
            qpos = self.data.qpos[self._qpos_indices].copy()
            joint_margin = float(
                np.min(np.minimum(qpos - self._joint_limits[:, 0], self._joint_limits[:, 1] - qpos))
            )
            collision, _ = self._collision_state()
            valid = bool(
                position_error <= 0.003
                and axis_error <= orientation_tolerance
                and joint_margin >= margin - 1e-8
                and not collision
            )
            score = position_error + 0.010 * axis_error + 0.050 * collision
            candidate = (score, qpos, position_error, axis_error, collision, joint_margin)
            if best is None or candidate[0] < best[0]:
                best = candidate
            if valid:
                best = candidate
                break
        assert best is not None
        _, qpos, position_error, axis_error, collision, joint_margin = best
        self.data.qpos[self._qpos_indices] = qpos
        mujoco.mj_forward(self.model, self.data)
        if (
            position_error > 0.003
            or axis_error > orientation_tolerance
            or collision
            or joint_margin < margin - 1e-8
        ):
            raise RuntimeError(
                "No collision-free reset IK solution: "
                f"position={position_error * 1000.0:.2f}mm "
                f"orientation={np.degrees(axis_error):.2f}deg "
                f"margin={np.degrees(joint_margin):.2f}deg collision={collision}"
            )
        return qpos.copy()

    def _tilt_prepare_goal(self, index: int) -> np.ndarray | None:
        """Return a collision-checked multi-start IK goal for one airborne tilt."""

        cached = self._tilt_prepare_goals.get(index)
        if cached is not None:
            return cached
        if index in self._unavailable_tilt_prepare_goals:
            return None

        saved_qpos = self.data.qpos.copy()
        current = saved_qpos[self._qpos_indices].copy()
        saved_target_index = self._target_index
        phase = self.waypoints.phases[index]
        stop = index + 1
        if phase in ("tilt_prepare", "tilt_release"):
            while stop < len(self.waypoints) and self.waypoints.phases[stop] == phase:
                stop += 1
        route_stop = stop
        if phase == "tilt_prepare":
            while (
                route_stop < len(self.waypoints)
                and self.waypoints.phases[route_stop] == "tilted_approach"
            ):
                route_stop += 1

        def transition_is_safe(
            start: np.ndarray, goal: np.ndarray, target_index: int
        ) -> bool:
            count = max(
                2,
                int(np.ceil(np.max(np.abs(goal - start)) / np.deg2rad(2.0))),
            )
            for joints in np.linspace(start, goal, count):
                self.data.qpos[self._qpos_indices] = joints
                mujoco.mj_forward(self.model, self.data)
                collision, _ = self._collision_state()
                clearance = (
                    self.brush_position[2]
                    - self.config.paper.surface_z
                    - self.config.brush.tip_radius
                )
                if collision or (
                    not self.waypoints.pen_down[target_index]
                    and self.waypoints.phases[target_index]
                    not in ("lower", "wipe_lower", "inkstone_lower")
                    and clearance < 0.008
                ):
                    return False
            return True

        goals: dict[int, np.ndarray] = {}
        try:
            if phase == "tilt_prepare" and route_stop > stop:
                # Start from the actual glyph entry and solve backwards. The
                # inner A4 points have a different continuous wrist branch
                # from the first valid solution at the transport circle.
                for target_index in range(route_stop - 1, stop - 1, -1):
                    self._target_index = target_index
                    goals[target_index] = self._solve_position_ik(
                        self.waypoints.positions[target_index],
                        directional_axis=False,
                        orientation_tolerance=(
                            self.config.attachment_orientation_tolerance
                        ),
                    )
                self._target_index = index
                preparation = self._solve_position_ik(
                    self.waypoints.positions[index],
                    directional_axis=False,
                    orientation_tolerance=(
                        self.config.attachment_orientation_tolerance
                    ),
                )
                for target_index in range(index, stop):
                    goals[target_index] = preparation.copy()
            else:
                self._target_index = index
                desired_axis = self._desired_brush_axis(index)
                goal = self._solve_position_ik(
                    self.waypoints.positions[index],
                    directional_axis=bool(np.linalg.norm(desired_axis[:2]) < 1e-6),
                    orientation_tolerance=(
                        self.config.attachment_orientation_tolerance
                    ),
                )
                for target_index in range(index, stop):
                    goals[target_index] = goal.copy()

            previous = current
            safe = True
            for target_index in range(index, route_stop):
                goal = goals[target_index]
                if not np.allclose(previous, goal) and not transition_is_safe(
                    previous, goal, target_index
                ):
                    safe = False
                    break
                previous = goal
        except RuntimeError:
            safe = False
        finally:
            self.data.qpos[:] = saved_qpos
            self._target_index = saved_target_index
            mujoco.mj_forward(self.model, self.data)

        if not safe:
            self._unavailable_tilt_prepare_goals.update(range(index, route_stop))
            return None
        self._tilt_prepare_goals.update(goals)
        return self._tilt_prepare_goals[index]

    def _dls_delta(
        self,
        error: np.ndarray,
        desired_axis: np.ndarray | None = None,
        *,
        include_tilt: bool = False,
        orientation_weight: float | None = None,
        center_tilt: bool = True,
        directional_axis: bool = True,
        position_priority: bool = False,
    ) -> np.ndarray:
        jacobian_position = np.zeros((3, self.model.nv), dtype=np.float64)
        jacobian_rotation = np.zeros((3, self.model.nv), dtype=np.float64)
        mujoco.mj_jacSite(
            self.model,
            self.data,
            jacobian_position,
            jacobian_rotation,
            self._brush_site_id,
        )
        # Tilt (gripper) supplies the sixth DOF needed to keep the offset brush
        # upright during transfers as well as to lean it while writing.
        n_joints = (
            5
            if self.config.legacy_attachment_compensation
            else 6 if include_tilt else 5
        )
        actuated = self._qvel_indices[:n_joints]
        position = jacobian_position[:, actuated]
        if desired_axis is None:
            jacobian = position
            objective = error
        else:
            mount_position = np.zeros((3, self.model.nv), dtype=np.float64)
            mount_rotation = np.zeros((3, self.model.nv), dtype=np.float64)
            mujoco.mj_jacSite(
                self.model,
                self.data,
                mount_position,
                mount_rotation,
                self._brush_mount_site_id,
            )
            mount_axis = self.data.site_xmat[self._brush_mount_site_id].reshape(3, 3)[:, 0]
            skew = np.asarray(
                [
                    [0.0, -mount_axis[2], mount_axis[1]],
                    [mount_axis[2], 0.0, -mount_axis[0]],
                    [-mount_axis[1], mount_axis[0], 0.0],
                ]
            )
            axis_jacobian = -skew @ mount_rotation[:, actuated]
            axis_error = desired_axis - mount_axis
            if not directional_axis:
                # Ordinary sending/corner/sweep motion specifies brush angle,
                # not a globally fixed azimuth. Keeping only the vertical axis
                # component preserves that angle and leaves enough redundancy
                # to follow paper positions throughout all six A4 frames.
                axis_jacobian = axis_jacobian[2:3]
                axis_error = axis_error[2:3]
            weight = (
                self.config.orientation_ik_weight
                if orientation_weight is None
                else orientation_weight
            )
            jacobian = np.vstack((position, weight * axis_jacobian))
            objective = np.concatenate((error, weight * axis_error))
        damping = 2e-4
        if desired_axis is not None and position_priority:
            position_inverse = position.T @ np.linalg.solve(
                position @ position.T + damping * np.eye(3), np.eye(3)
            )
            delta = position_inverse @ error
            position_null = np.eye(n_joints) - np.linalg.pinv(position) @ position
            secondary = weight * axis_jacobian @ position_null
            residual = weight * (axis_error - axis_jacobian @ delta)
            delta += position_null @ secondary.T @ np.linalg.solve(
                secondary @ secondary.T + damping * np.eye(len(residual)),
                residual,
            )
        else:
            delta = jacobian.T @ np.linalg.solve(
                jacobian @ jacobian.T + damping * np.eye(len(objective)), objective
            )
        if (
            desired_axis is not None
            and include_tilt
            and n_joints == 6
            and center_tilt
            and not position_priority
        ):
            # Axis direction + XYZ leaves one physical redundancy. Use it to
            # keep the dedicated tilt servo near its 45-degree electrical
            # centre instead of drifting to -10/100 degrees across a stroke.
            null_space = np.eye(n_joints) - np.linalg.pinv(jacobian) @ jacobian
            posture = np.zeros(n_joints, dtype=np.float64)
            posture[-2] = -self.data.qpos[self._qpos_indices[-2]]
            posture[-1] = np.pi / 4.0 - self.data.qpos[self._qpos_indices[-1]]
            delta += 0.15 * (null_space @ posture)
        return delta

    def _attachment_delta(self, error: np.ndarray, desired_axis: np.ndarray) -> np.ndarray:
        """Prioritise the real mount axis, then recover tip position in its null space."""

        position_jacobian = np.zeros((3, self.model.nv), dtype=np.float64)
        rotation_jacobian = np.zeros((3, self.model.nv), dtype=np.float64)
        mujoco.mj_jacSite(
            self.model,
            self.data,
            position_jacobian,
            rotation_jacobian,
            self._brush_site_id,
        )
        mount_position = np.zeros((3, self.model.nv), dtype=np.float64)
        mount_rotation = np.zeros((3, self.model.nv), dtype=np.float64)
        mujoco.mj_jacSite(
            self.model,
            self.data,
            mount_position,
            mount_rotation,
            self._brush_mount_site_id,
        )
        actuated = self._qvel_indices
        axis = self.brush_mount_axis
        skew = np.asarray(
            [[0.0, -axis[2], axis[1]], [axis[2], 0.0, -axis[0]], [-axis[1], axis[0], 0.0]]
        )
        orientation = -skew @ mount_rotation[:, actuated]
        damping = 2e-4
        orientation_inverse = orientation.T @ np.linalg.solve(
            orientation @ orientation.T + damping * np.eye(3), np.eye(3)
        )
        orientation_delta = orientation_inverse @ (desired_axis - axis)
        null_space = np.eye(len(actuated)) - orientation_inverse @ orientation
        position = position_jacobian[:, actuated]
        secondary = position @ null_space
        position_delta = null_space @ secondary.T @ np.linalg.solve(
            secondary @ secondary.T + damping * np.eye(3),
            error - position @ orientation_delta,
        )
        delta = orientation_delta + position_delta
        task = np.vstack((orientation, position))
        task_null = np.eye(len(actuated)) - np.linalg.pinv(task) @ task
        posture = np.zeros(len(actuated), dtype=np.float64)
        posture[-1] = np.pi / 4.0 - self.data.qpos[self._qpos_indices[-1]]
        return delta + 0.15 * (task_null @ posture)

    def _uses_attachment_priority(self, index: int | None = None) -> bool:
        if (
            self.config.legacy_attachment_compensation
            or not self.config.attachment_pose_control
            or self.config.modules.brushwork != "professional"
        ):
            return False
        target_index = min(
            self._target_index if index is None else index,
            len(self.waypoints) - 1,
        )
        metadata = self._target_metadata(target_index)
        stroke_index = metadata["stroke_index"]
        exposed_start = bool(self._exposed_horizontal[stroke_index, 0])
        if metadata["phase"] == "tilt_prepare":
            return True
        return bool(
            self._exposed_horizontal[stroke_index, 1]
            and metadata["technique"] == "tome"
            and (
                metadata["brushwork_phase"] == "finish"
                or metadata["phase"] in ("lift", "finish_lift")
            )
        )

    def _is_exposed_entry_phase(self, index: int | None = None) -> bool:
        if self.config.modules.brushwork != "professional":
            return False
        metadata = self._target_metadata(index)
        stroke_index = metadata["stroke_index"]
        return bool(
            self._exposed_horizontal[stroke_index, 0]
            and metadata["down"]
            and metadata["brushwork_phase"] == "entry"
            and metadata["stroke_progress"] <= 0.02
        )

    def _uses_fixed_contact_lean(self, index: int | None = None) -> bool:
        """Use the fixed 45-degree attachment only on exposed horizontals."""

        if self.config.brush.fixed_contact_lean is None:
            return False
        metadata = self._target_metadata(index)
        stroke_index = int(metadata["stroke_index"])
        return bool(
            0 <= stroke_index < len(self._exposed_horizontal)
            and np.any(self._exposed_horizontal[stroke_index])
            and len(self.trajectory.strokes) <= 3
        )

    def _is_exposed_endpoint_phase(self, index: int | None = None) -> bool:
        """Return whether the tip is forming an exposed horizontal endpoint."""

        if self._is_exposed_entry_phase(index):
            return True
        return self._is_exposed_finish_phase(index)

    def _is_exposed_finish_phase(self, index: int | None = None) -> bool:
        if self.config.modules.brushwork != "professional":
            return False
        metadata = self._target_metadata(index)
        stroke_index = metadata["stroke_index"]
        return bool(
            self._exposed_horizontal[stroke_index, 1]
            and metadata["technique"] == "tome"
            and (
                metadata["brushwork_phase"] == "finish"
                or metadata["phase"] in ("lift", "finish_lift")
            )
        )

    def _load_pressure_calibration(self) -> PressureCalibration | None:
        path_str = self.config.pressure_calibration_path
        if path_str is None:
            if self.config.require_pressure_calibration:
                raise ValueError("pressure_calibration_path is required but was not provided.")
            return None
        path = Path(path_str)
        if not path.is_file():
            raise FileNotFoundError(f"Pressure calibration file not found: {path}")
        calibration = PressureCalibration.load(path)
        if calibration.cad_fingerprint != DEFAULT_CAD_FINGERPRINT:
            raise ValueError(
                f"CAD fingerprint mismatch: expected {DEFAULT_CAD_FINGERPRINT!r}, "
                f"got {calibration.cad_fingerprint!r}"
            )
        if calibration.brush_fingerprint != DEFAULT_BRUSH_FINGERPRINT:
            raise ValueError(
                f"Brush fingerprint mismatch: expected {DEFAULT_BRUSH_FINGERPRINT!r}, "
                f"got {calibration.brush_fingerprint!r}"
            )
        return calibration

    def _current_layout_class(self) -> str:
        return "110mm" if self._uses_large_frame_calibration() else "85mm"

    def _probe_width_p90_by_phase(self) -> dict[str, float]:
        if self._pressure_calibration is None:
            return {}
        values = self._pressure_calibration.provenance.get("actual_width_p90_m", {})
        if not isinstance(values, Mapping):
            return {}
        layout_class = "110mm" if self._layout_index in (4, 5) else "85mm"
        result: dict[str, float] = {}
        for key, value in values.items():
            parts = str(key).split("/")
            if len(parts) != 3 or parts[0] != layout_class:
                continue
            try:
                width = float(value)
            except (TypeError, ValueError):
                continue
            if np.isfinite(width) and width > 0.0:
                result[parts[2]] = max(result.get(parts[2], 0.0), width)
        return result

    def _lookup_feedforward_pressure_offset(self, index: int) -> tuple[float, bool, bool]:
        if self._pressure_calibration is None:
            return 0.0, False, False
        layout_cls = self._current_layout_class()
        calibration_angle_deg = self._pressure_calibration_angle_deg(index)
        metadata = self._target_metadata(index)
        phase = str(metadata.get("brushwork_phase", "send"))
        if phase not in ("entry", "send", "corner", "finish"):
            phase = "send"
        target_pressure = float(metadata.get("pressure", 0.0))
        res = self._pressure_calibration.lookup(
            layout_cls, calibration_angle_deg, phase, target_pressure
        )
        return res.offset_m, res.clipped, res.fallback

    def _pressure_calibration_angle_deg(self, index: int) -> float:
        """Return the controller's exact category, never a rounded live angle."""

        metadata = self._target_metadata(index)
        if self._uses_fixed_contact_lean(index):
            return 30.0 if self._layout_index == 0 else 45.0
        phase = str(metadata.get("brushwork_phase", "send"))
        technique = str(metadata.get("technique", ""))
        if phase == "entry":
            return 30.0
        if phase == "corner":
            return 20.0
        if phase == "finish":
            if technique in ("hane", "harai"):
                return 4.0
            if technique == "tome":
                return 30.0
        from so101_calligraphy.brushwork import classify_stroke_family

        stroke_index = int(metadata.get("stroke_index", -1))
        if 0 <= stroke_index < len(self.trajectory.strokes):
            family = classify_stroke_family(self.trajectory.strokes[stroke_index])
            if family in {"pie", "na"}:
                return 12.0
        return 8.0

    def _uses_large_frame_calibration(self) -> bool:
        frame_size = writing_frames(
            self.config.paper, self.config.writing_layout
        )[self._layout_index][1][0]
        return bool(
            frame_size > self.config.writing_layout.two_by_two_size + 1e-9
        )

    def _all_strokes_are_horizontal(self) -> bool:
        return bool(len(self._exposed_horizontal) and np.all(self._exposed_horizontal))

    def _effective_entry_lean(self) -> float:
        return (
            self.config.brush.large_frame_entry_lean
            if self._uses_large_frame_calibration()
            else self.config.brush.entry_lean
        )

    def _effective_nominal_force(self) -> float:
        return (
            self.config.brush.large_frame_nominal_force
            if self._uses_large_frame_calibration()
            else self.config.brush.nominal_force
        )

    def _effective_pressure_control(self) -> tuple[float, float, float]:
        """Return response, gain and travel for the selected physical layout."""

        if self._all_strokes_are_horizontal():
            return (
                self.config.brush.horizontal_pressure_response,
                self.config.horizontal_contact_pressure_gain,
                self.config.horizontal_contact_pressure_limit,
            )
        gain = (
            self.config.large_frame_contact_pressure_gain
            if self._uses_large_frame_calibration()
            else self.config.contact_pressure_gain
        )
        return (
            self.config.brush.pressure_response,
            gain,
            self.config.contact_pressure_limit,
        )

    def _contact_pressure_correction(self, index: int) -> float:
        _, gain, _ = self._effective_pressure_control()
        if not self.waypoints.pen_down[index]:
            return 0.0
        if self.config.pressure_probe_offset_m is not None:
            return self.config.pressure_probe_offset_m
        if gain <= 0.0:
            return 0.0
        return self._contact_pressure_offset

    def _pressure_probe_settle_required(self, index: int) -> bool:
        """Hold only the first contact target of each stroke for probe settling."""

        if (
            self.config.pressure_probe_offset_m is None
            or not self.waypoints.pen_down[index]
        ):
            return False
        if index == 0 or not self.waypoints.pen_down[index - 1]:
            return True
        return bool(
            self.waypoints.stroke_indices[index - 1]
            != self.waypoints.stroke_indices[index]
        )

    def _pressure_probe_should_wait(self, index: int) -> bool:
        return bool(
            self._pressure_probe_settle_required(index)
            and self._contact_dwell < 40
            and self._target_dwell < 80
        )

    def _pressure_unload_saturated(self, index: int) -> bool:
        """True when lift authority is maxed but measured pressure stays high.

        The tip is commanded above the geometric waypoint, yet IK cannot raise
        it further under the current pose. Holding the waypoint forever only
        rubs ink; callers should drop orientation and advance on geometric Z.
        """

        _, gain, pressure_limit = self._effective_pressure_control()
        if (
            not self.waypoints.pen_down[index]
            or gain <= 0.0
            or pressure_limit <= 0.0
        ):
            return False
        if self._contact_pressure_offset < pressure_limit * 0.99:
            return False
        metadata = self._target_metadata(index)
        return bool(self._pressure > float(metadata["pressure"]) + 0.02)

    def _target_requires_contact(self, index: int) -> bool:
        metadata = self._target_metadata(index)
        return bool(
            self.waypoints.pen_down[index]
            and metadata["pressure"] > CONTACT_REQUIRED_PRESSURE
            and (
                metadata["brushwork_phase"] != "finish"
                or metadata["technique"] == "tome"
            )
        )

    def _update_contact_pressure_control(self, index: int) -> None:
        _, base_gain, pressure_limit = self._effective_pressure_control()
        if not self.waypoints.pen_down[index]:
            self._contact_pressure_offset = 0.0
            self._feedforward_pressure_offset = 0.0
            self._residual_pressure_offset = 0.0
            self._pressure_calibration_clipped = False
            self._pressure_calibration_fallback = False
            self._contact_dwell = 0
            return
        if self.config.pressure_probe_offset_m is not None:
            offset = float(self.config.pressure_probe_offset_m)
            self._contact_pressure_offset = offset
            self._feedforward_pressure_offset = offset
            self._residual_pressure_offset = 0.0
            self._pressure_calibration_clipped = False
            self._pressure_calibration_fallback = False
            self._contact_dwell = (
                self._contact_dwell + 1 if self._contact_force > 1e-7 else 0
            )
            return
        if base_gain <= 0.0:
            self._contact_pressure_offset = 0.0
            self._feedforward_pressure_offset = 0.0
            self._residual_pressure_offset = 0.0
            self._pressure_calibration_clipped = False
            self._pressure_calibration_fallback = False
            self._contact_dwell = 0
            return
        stroke_index = int(self.waypoints.stroke_indices[index])
        stroke_has_contact = bool(self._stroke_records[stroke_index]["pressure"])
        metadata = self._target_metadata(index)
        pressure_error = self._pressure - float(metadata["pressure"])
        no_contact = self._contact_force <= 1e-7
        contact_required = self._target_requires_contact(index)
        if no_contact and stroke_has_contact and self._pressure_calibration is None:
            # A solver contact gap is not a reliable zero-force sample. Keep
            # enough downward feedback to regain paper, but avoid winding the
            # integrator to its lower bound before the next impact.
            # If this target must stay on paper, first discard any stale
            # positive (lifting) offset. Otherwise that offset can hold a tome
            # finish in the air while the deliberately softened feedback takes
            # dozens of steps to unwind it.
            if contact_required:
                self._contact_pressure_offset = min(
                    self._contact_pressure_offset, 0.0
                )
            pressure_error *= 0.10
        gain = base_gain * contact_pressure_gain_scale(
            str(metadata["technique"]),
            float(metadata["stroke_progress"]),
            harai_scale=self.config.harai_pressure_gain_scale,
            hane_release_scale=self.config.hane_release_pressure_gain_scale,
        )
        if self.config.modules.brushwork == "professional":
            from so101_calligraphy.brushwork import classify_stroke_family

            stroke_index = int(self.waypoints.stroke_indices[index])
            families = tuple(
                classify_stroke_family(stroke) for stroke in self.trajectory.strokes
            )
            gain *= contact_pressure_direction_scale(
                families[stroke_index],
                np.asarray(metadata["tangent"], dtype=np.float64),
                turning_glyph="zhe" in families,
                left_horizontal_glyph=(
                    self._layout_index in (2, 3)
                    and all(family == "heng" for family in families)
                ),
            )
        ff_offset, ff_clipped, ff_fallback = self._lookup_feedforward_pressure_offset(index)
        if no_contact and ff_offset > 0.0:
            # A positive Z feedforward lifts the brush. Do not let it preserve
            # a contact gap; the nominal trajectory can re-touch safely.
            ff_offset = 0.0
        self._feedforward_pressure_offset = ff_offset
        self._pressure_calibration_clipped = ff_clipped
        self._pressure_calibration_fallback = ff_fallback
        residual_gain = gain * self.config.residual_pressure_integral_scale
        if self._pressure_calibration is not None:
            if no_contact:
                self._contact_dwell = 0
                if contact_required:
                    self._residual_pressure_offset = min(
                        self._residual_pressure_offset, 0.0
                    )
                else:
                    self._residual_pressure_offset *= 0.95
            else:
                self._contact_dwell += 1
                self._residual_pressure_offset = _next_contact_pressure_offset(
                    self._residual_pressure_offset,
                    pressure_error * _touchdown_error_scale(self._contact_dwell),
                    residual_gain,
                    pressure_limit,
                )
            total = self._feedforward_pressure_offset + self._residual_pressure_offset
            self._contact_pressure_offset = float(np.clip(total, -pressure_limit, pressure_limit))
        else:
            self._contact_pressure_offset = _next_contact_pressure_offset(
                self._contact_pressure_offset,
                pressure_error,
                gain,
                pressure_limit,
            )
            self._residual_pressure_offset = self._contact_pressure_offset
            self._contact_dwell = self._contact_dwell + 1 if not no_contact else 0

    def expert_action(self) -> np.ndarray:
        """Return a joint-space DLS action for efficient policy warm-starting."""

        index = min(self._target_index, len(self.waypoints) - 1)
        phase = self.waypoints.phases[index]
        down = bool(self.waypoints.pen_down[index])
        needs_ik_goal = (
            phase == "tilt_prepare" and self._uses_attachment_priority(index)
        ) or (
            phase == "tilt_release"
        ) or (
            phase in ("tilted_approach", "tilted_retreat")
            and index in self._tilt_prepare_goals
        ) or (
            not self.waypoints.pen_down[index]
            and phase not in ("wipe_lower", "inkstone_lower")
            and self._target_dwell >= 40
        ) or (
            self.waypoints.pen_down[index]
            and self.waypoints.brushwork_phases[index] == "entry"
            and self._contact_force <= 1e-7
            and self._target_dwell >= 80
        )
        if needs_ik_goal:
            goal = self._tilt_prepare_goal(index)
            goal_error = (
                np.inf
                if goal is None
                else float(
                    np.max(
                        np.abs(
                            goal - self.data.qpos[self._qpos_indices]
                        )
                    )
                )
            )
            contact_phase = phase in ("ink_load", "ink_wipe")
            if goal is not None and (
                (not down and not contact_phase)
                or goal_error > np.deg2rad(2.0)
            ):
                stiffness = self.model.actuator_gainprm[: len(JOINT_NAMES), 0]
                desired = goal + self.data.qfrc_bias[
                    self._qvel_indices
                ] / np.maximum(stiffness, 1e-9)
                difference = desired - self._joint_targets
                scale = min(
                    1.0,
                    self.config.action_delta
                    / max(float(np.max(np.abs(difference))), 1e-12),
                )
                return np.clip(
                    scale * difference / self.config.action_delta,
                    -1.0,
                    1.0,
                ).astype(np.float32)
        position_error = self.target_position - self.controlled_brush_position
        error = position_error.copy()
        if down:
            frame_size = writing_frames(
                self.config.paper, self.config.writing_layout
            )[self._layout_index][1][0]
            # Layout placement scales the same sampled trajectory from 85 to
            # 110 mm. Compensate that geometric scale so a larger character
            # does not automatically drive the physical brush 29% faster.
            layout_scale = min(
                1.0, self.config.writing_layout.two_by_two_size / frame_size
            )
            error[:2] *= layout_scale**1.5
        lateral_recovery_required = bool(
            np.linalg.norm(position_error[:2])
            > min(self.config.target_tolerance_xy, 0.0045)
        )
        if down and not lateral_recovery_required:
            # Pressure and orientation can need several contact steps after XY
            # is already good enough. Hold that lateral position instead of
            # tracing sub-tolerance servo error back and forth while Z settles;
            # lateral feedback automatically resumes if paper drag moves the
            # tip outside the same reachability tolerance.
            error = error.copy()
            error[:2] = 0.0
        elif (
            self._is_exposed_finish_phase(index)
            and down
        ):
            # Contact bends the terminal tuft across the paper. The position
            # term must overcome that elastic offset while orientation remains
            # the primary task of the attachment controller.
            error = error.copy()
            error[:2] *= 4.0
        elif down and self._target_dwell >= 40:
            # Preserve precise 4.5 mm tracking during normal motion. Only a
            # point that has stopped advancing gets extra lateral authority
            # to overcome static paper drag; this is feedback, not a skip.
            error = error.copy()
            error[:2] *= 4.0
        desired_axis = (
            None
            if self.config.legacy_attachment_compensation
            else self._desired_brush_axis(follow_tip=True)
        )
        fixed_contact_tilt = bool(
            down
            and self._uses_fixed_contact_lean(index)
            and not self.config.legacy_attachment_compensation
        )
        solver_axis = None if fixed_contact_tilt else desired_axis
        directional_contact = bool(down and self._is_exposed_endpoint_phase(index))
        if down:
            if self._contact_force <= 1e-7:
                # Approach the first real contact without carrying the 10 mm
                # airborne descent velocity into the soft tip. Do not retain
                # the 0.05 scale forever when a remote A4 pose needs more
                # servo authority to touch: ramp to full Z over 40 steps.
                error = error.copy()
                error[2] *= _touchdown_error_scale(self._target_dwell)
        _, effective_pressure_gain, _ = self._effective_pressure_control()
        unload_saturated = bool(down and self._pressure_unload_saturated(index))
        if down and (
            effective_pressure_gain > 0.0
            or self.config.pressure_probe_offset_m is not None
        ):
            # 位置サーボ単独では接触抗力とつり合った深さで止まり、穂先が目標より
            # 沈んだまま線が太る。筆圧誤差を高さに戻して「穂先の感触」で書く。
            error = error.copy()
            error[2] += self._contact_pressure_correction(index)
        if down and self._target_dwell >= 40:
            error[2] *= 2.0
        # The physical attachment leaves 18 mm of shaft behind the tuft. Keep
        # it upright throughout every pen-up transfer; waiting until the final
        # descent is too late to turn it clear of the paper or inkstone.
        # Full orientation priority is safe while airborne. On paper it can
        # lift the tip several millimetres to win the orientation task, so the
        # contact endpoints use the weighted position+axis solve below.
        strict_attachment = (
            phase == "tilt_release"
            and not self.config.legacy_attachment_compensation
        )
        contact_orientation_weight = None
        if down or phase == "lower":
            from so101_calligraphy.brushwork import classify_stroke_family

            stroke_index = int(self.waypoints.stroke_indices[index])
            families = tuple(
                classify_stroke_family(stroke) for stroke in self.trajectory.strokes
            )
            contact_orientation_weight = (
                self.config.contact_orientation_ik_weight
                * contact_orientation_family_scale(
                    families[stroke_index],
                    turning_glyph="zhe" in families,
                )
            )
            if unload_saturated:
                # Orientation was winning over the unload Z task and left the
                # tip rubbing at max lift command. XYZ recovery comes first.
                contact_orientation_weight = 0.0
        collision_recovery = self._collision_recovery_active(command_down=down)
        delta = (
            self._dls_delta(
                error,
                desired_axis,
                include_tilt=True,
                orientation_weight=0.0,
                position_priority=True,
            )
            if collision_recovery
            else self._attachment_delta(error, desired_axis)
            if strict_attachment
            else self._dls_delta(
                error,
                solver_axis,
                include_tilt=not fixed_contact_tilt,
                orientation_weight=contact_orientation_weight,
                directional_axis=(
                    True
                    if self.config.legacy_attachment_compensation
                    else directional_contact
                    or (
                        not down
                        and phase
                        not in (
                            "tilt_prepare",
                            "tilted_approach",
                            "lower",
                            "lift",
                            "finish_lift",
                            "tilted_retreat",
                        )
                    )
                ),
                position_priority=(
                    False if self.config.legacy_attachment_compensation else down
                ),
            )
        )
        cartesian_unreached = bool(
            np.linalg.norm(position_error[:2])
            > min(self.config.target_tolerance_xy, 0.0045)
            or abs(position_error[2]) > min(self.config.target_tolerance_z, 0.0018)
        )
        contact_unreached = bool(
            self._target_requires_contact(index) and self._contact_force <= 1e-7
        )
        recovering_cartesian = bool(
            self._target_dwell >= 160
            and (cartesian_unreached or contact_unreached)
            and phase not in ("tilt_prepare", "tilt_release", "lower")
        )
        if recovering_cartesian:
            # A Cartesian waypoint must never be skipped. If its requested
            # orientation has no local solution, release only that secondary
            # task and recover the same tip position with all six joints.
            # This also applies while contacting, but only after 160 cycles
            # outside the Cartesian tolerance. Replacing an in-tolerance solve would
            # discard its pressure-relative Z target and pin the tip in place.
            recovery_error = position_error.copy()
            if contact_unreached:
                # Inside the Cartesian tolerance, a dry point can otherwise
                # settle at a zero-action pose forever. Reuse the bounded tip
                # pressure offset to descend; do not skip or force completion.
                recovery_error[2] += self._contact_pressure_correction(index)
            delta = self._dls_delta(
                recovery_error,
                include_tilt=True,
                position_priority=True,
            )
        arm_delta = np.clip(
            delta,
            -self.config.action_delta,
            self.config.action_delta,
        )
        desired = (
            self._joint_targets.copy()
            if recovering_cartesian
            else self.data.qpos[self._qpos_indices].copy()
        )
        desired[: len(arm_delta)] += arm_delta
        if recovering_cartesian:
            qpos = self.data.qpos[self._qpos_indices]
            maximum_servo_deflection = 2.0 * self.config.action_delta
            desired = np.clip(
                desired,
                qpos - maximum_servo_deflection,
                qpos + maximum_servo_deflection,
            )
        # MuJoCo's position actuators are proportional servos. Cancel static
        # gravity droop at the low-level joint target; external paper force is
        # handled separately by the bounded tip-pressure loop.
        stiffness = self.model.actuator_gainprm[: len(JOINT_NAMES), 0]
        if not recovering_cartesian:
            desired += self.data.qfrc_bias[self._qvel_indices] / np.maximum(
                stiffness, 1e-9
            )
        if fixed_contact_tilt and not recovering_cartesian and not collision_recovery:
            desired[-1] = self._joint_targets[-1]
        if self.config.legacy_attachment_compensation:
            desired[-1] = self.config.hardware.fixed_attachment_servo_angle_rad
        action = (desired - self._joint_targets) / self.config.action_delta
        return np.clip(action, -1.0, 1.0).astype(np.float32)

    def _select_trajectory(self, index: int, layout_index: int) -> None:
        if not 0 <= index < len(self.trajectories):
            raise ValueError(
                f"trajectory_index must be in [0, {len(self.trajectories) - 1}]"
            )
        frames = writing_frames(self.config.paper, self.config.writing_layout)
        if not 0 <= layout_index < len(frames):
            raise ValueError(f"layout_index must be in [0, {len(frames) - 1}]")
        self._trajectory_index = index
        self._layout_index = layout_index
        self._tilt_prepare_goals.clear()
        self._unavailable_tilt_prepare_goals.clear()
        self.trajectory = self._prepare_trajectory(
            self._trajectory_for_layout(self.trajectories[index], layout_index)
        )
        self._exposed_horizontal = exposed_horizontal_endpoints(
            self.trajectory.strokes,
            junction_tolerance=self.config.stroke_junction_tolerance,
        )
        sequence_brush = self.config.brush
        transport_origin: tuple[float, float] | None = (
            self.config.hardware.base_position_xy_m[0]
            + self.config.hardware.shoulder_pivot_offset_x_m,
            self.config.hardware.base_position_xy_m[1],
        )
        if self.config.legacy_attachment_compensation:
            sequence_brush = replace(sequence_brush, tilt_prepare_steps=0)
            transport_origin = None
        self.waypoints = build_waypoint_sequence(
            self.trajectory,
            pen_down_z=self.config.pen_down_z,
            safe_height=self.config.safe_height,
            transition_spacing=self.config.transition_spacing,
            brush=sequence_brush,
            brushwork_mode=self.config.modules.brushwork,
            inkstone=self._effective_inkstone(),
            stroke_minimum_gap=self.config.stroke_minimum_gap,
            pressure_scale=self._pressure_scale,
            entry_descent_ratio=self.config.entry_descent_ratio,
            stroke_junction_tolerance=self.config.stroke_junction_tolerance,
            stroke_clearance_floor=self.config.stroke_clearance_floor,
            observed_width_p90_by_phase=self._probe_width_p90_by_phase(),
            staging_xy=(
                self.config.hardware.base_position_xy_m[0]
                + self.config.hardware.shoulder_pivot_offset_x_m
                + self.config.hardware.upright_transport_radius_m,
                self.config.hardware.base_position_xy_m[1],
            ),
            transport_origin_xy=transport_origin,
            transport_radius=self.config.hardware.upright_transport_radius_m,
            transport_height=self.config.hardware.upright_transport_height_m,
        )
        self._set_path_markers()

    def _effective_inkstone(
        self,
        *,
        offset: np.ndarray | None = None,
    ) -> InkstoneConfig | None:
        if not self.config.modules.inkstone:
            return None
        base = self.config.inkstone
        pose = np.asarray(self._inkstone_pose_offset, dtype=np.float64)
        extra = (
            np.zeros(3, dtype=np.float64)
            if offset is None
            else np.asarray(offset, dtype=np.float64)
        )
        # pose already includes hardware.inkstone_offset_m after _apply_hardware_pose.
        total = pose + extra
        return InkstoneConfig(
            center_x=base.center_x + float(total[0]),
            center_y=base.center_y + float(total[1]),
            pool_surface_z=base.pool_surface_z + float(total[2]),
            lip_y=base.lip_y + float(total[1]),
            lip_surface_z=base.lip_surface_z + float(total[2]),
            safe_height=base.safe_height + float(total[2]),
            pool_half_width=base.pool_half_width,
            loading_steps=base.loading_steps,
            wiping_points=base.wiping_points,
            reink_interval_strokes=base.reink_interval_strokes,
        )

    def _get_obs(self) -> np.ndarray:
        qpos = self.data.qpos[self._qpos_indices]
        qvel = self.data.qvel[self._qvel_indices]
        brush = self.controlled_brush_position
        relative_target = self.target_position - brush
        metadata = self._target_metadata()
        pen_down = float(metadata["down"])
        latency_fraction = self._latency_steps / max(
            self.config.servo_latency_steps + self.config.latency_randomization, 1
        )
        observation = np.concatenate(
            (
                qpos,
                qvel,
                brush,
                relative_target,
                [self.progress, pen_down],
                self._tip_velocity,
                self.brush_axis,
                self.brush_deflection,
                [self._pressure, self.ink.ink_load, self.ink.water],
                metadata["tangent"],
                [
                    metadata["pressure"],
                    metadata["speed"],
                    metadata["width"],
                    metadata["stroke_progress"],
                ],
                technique_one_hot(metadata["technique"]),
                [latency_fraction],
            )
        )
        if self.observation_version >= 2:
            state = self.brush_physics.observe(
                self.data,
                contact_force=self._contact_force,
                tip_velocity=self._tip_velocity,
            )
            inkstone_target = np.asarray(
                [
                    self.config.inkstone.center_x,
                    self.config.inkstone.center_y,
                    self.config.inkstone.pool_surface_z,
                ]
            )
            observation = np.concatenate(
                (
                    observation,
                    inkstone_target - brush,
                    [
                        float(getattr(self.ink, "core_ink", self.ink.ink_load)),
                        float(getattr(self.ink, "surface_ink", self.ink.ink_load)),
                        float(getattr(self.ink, "excess_ink", 0.0)),
                        float(getattr(self.ink, "drip_risk", 0.0)),
                    ],
                    state.bend_rate,
                    state.terminal_axis,
                    [metadata["roll"]],
                    self._phase_one_hot(),
                )
            )
        if self.observation_version == 3:
            observation = np.concatenate((observation, self._exemplar_observation()))
        return observation.astype(np.float32)

    def _target_reached(self, brush: np.ndarray) -> bool:
        error = self.target_position - brush
        index = min(self._target_index, len(self.waypoints) - 1)
        phase = self.waypoints.phases[index]
        down = bool(self.waypoints.pen_down[index])
        metadata = self._target_metadata(index)
        goal = self._tilt_prepare_goals.get(index)
        if (
            goal is not None
            and not down
            and phase not in ("ink_load", "ink_wipe", "lower")
        ):
            clearance = (
                brush[2]
                - self.config.paper.surface_z
                - self.config.brush.tip_radius
            )
            return bool(
                np.max(
                    np.abs(goal - self.data.qpos[self._qpos_indices])
                )
                <= np.deg2rad(2.0)
                and clearance >= 0.008
            )
        if phase == "tilt_release" or (
            phase == "tilt_prepare" and self._uses_attachment_priority(index)
        ):
            desired_axis = self._desired_brush_axis(index)
            actual_lean = np.arccos(
                np.clip(-self.brush_mount_axis[2], -1.0, 1.0)
            )
            desired_lean = np.arccos(np.clip(-desired_axis[2], -1.0, 1.0))
            clearance = (
                brush[2]
                - self.config.paper.surface_z
                - self.config.brush.tip_radius
            )
            return bool(
                abs(actual_lean - desired_lean)
                <= self.config.attachment_orientation_tolerance
                and clearance >= 0.008
            )
        if self.config.modules.brushwork == "professional" and down:
            xy_tolerance = min(self.config.target_tolerance_xy, 0.0045)
            if metadata["brushwork_phase"] == "entry":
                xy_tolerance = max(xy_tolerance, 0.0055)
        elif phase in ("travel", "tilted_travel", "tilted_approach", "tilted_retreat"):
            xy_tolerance = max(self.config.target_tolerance_xy, 0.0200)
        elif phase in ("lift", "finish_lift", "tilt_prepare", "tilt_release"):
            xy_tolerance = max(self.config.target_tolerance_xy, 0.0160)
        elif phase == "lower":
            # The following pen-down waypoint, not this airborne approach,
            # owns contact accuracy.
            xy_tolerance = max(self.config.target_tolerance_xy, 0.0160)
        elif phase in ("ink_load", "ink_wipe"):
            xy_tolerance = min(self.config.target_tolerance_xy, 0.0030)
        else:
            xy_tolerance = self.config.target_tolerance_xy
        xy_ok = np.linalg.norm(error[:2]) <= xy_tolerance
        if down:
            # The tilted 38mm tuft settles up to 1.6mm from the geometric Z
            # target. 1.8mm avoids indefinite rubbing without a dwell skip.
            z_tolerance = min(self.config.target_tolerance_z, 0.0018)
        elif phase in ("ink_load", "ink_wipe"):
            z_tolerance = min(self.config.target_tolerance_z, 0.0015)
        elif phase in (
            "travel",
            "tilted_travel",
            "tilted_approach",
            "tilted_retreat",
            "lift",
            "finish_lift",
            "tilt_prepare",
            "tilt_release",
            "inkstone_approach",
            "inkstone_lift",
            "inkstone_return",
            "wipe_lift",
        ):
            # A high transfer point may settle above its nominal Z under the
            # offset attachment. It remains more airborne, so 16 mm is safe
            # and prevents dense glyphs waiting forever before descent.
            z_tolerance = max(self.config.target_tolerance_z, 0.0160)
        elif phase == "wipe_lower":
            z_tolerance = max(self.config.target_tolerance_z, 0.0090)
        elif phase == "lower":
            # Stop close to the zero-pressure surface before declaring the
            # brush down. The previous 15 mm tolerance skipped this phase
            # entirely after the 10 mm approach and drove the soft tip into
            # paper at full joint speed, creating a large entry blot.
            z_tolerance = min(self.config.target_tolerance_z, 0.0025)
        elif phase == "inkstone_lower":
            z_tolerance = min(self.config.target_tolerance_z, 0.0025)
        else:
            z_tolerance = self.config.target_tolerance_z
        z_error = float(error[2])
        if (
            down
            and metadata["brushwork_phase"] == "entry"
            and self._target_dwell >= 40
            and not self._pressure_unload_saturated(index)
        ):
            # Entry pressure feedback can deliberately move the tip below the
            # geometric waypoint. Judge reachability at that corrected height
            # after the normal settling window; otherwise the controller
            # writes back and forth while the Z gate waits for a position it
            # is no longer commanding.
            z_error += self._contact_pressure_correction(index)
        elif down and metadata["brushwork_phase"] in ("send", "corner", "finish"):
            # Excess pressure can be relieved upward without holding a dry
            # low-pressure point below the paper. Finish must use the same
            # pressure-relative height or a release is pulled back down to
            # the geometric waypoint and leaves a terminal ink pool.
            # When lift authority is already saturated and pressure stays high,
            # requiring that unreachable height freezes the stroke in place.
            if not self._pressure_unload_saturated(index):
                z_error += max(self._contact_pressure_correction(index), 0.0)
        z_ok = abs(z_error) <= z_tolerance
        orientation_required = (
            not self.config.legacy_attachment_compensation
            and (
                phase == "tilt_release"
                or (
                    self._uses_attachment_priority(index)
                    and phase == "tilt_prepare"
                )
                or (
                    phase == "lower"
                    and index + 1 < len(self.waypoints)
                    and self.waypoints.phases[index + 1] == "draw"
                )
            )
        )
        orientation_ok = True
        if orientation_required:
            desired_axis = self._desired_brush_axis(index)
            actual_lean = np.arccos(
                np.clip(-self.brush_mount_axis[2], -1.0, 1.0)
            )
            desired_lean = np.arccos(np.clip(-desired_axis[2], -1.0, 1.0))
            orientation_error = abs(actual_lean - desired_lean)
            orientation_ok = (
                orientation_error <= self.config.attachment_orientation_tolerance
            )
        contact_ok = True
        if phase == "ink_load":
            contact_ok = self._has_contact(
                self._brush_geom_id, self._ink_pool_geom_id
            )
        elif phase == "ink_wipe":
            contact_ok = self._has_contact(
                self._brush_geom_id, self._inkstone_lip_geom_id
            )
        elif self._target_requires_contact(index):
            # Completing a Cartesian waypoint in the air is not a written
            # stroke. A tome retains pressure through its finish; only the
            # explicit hane/harai release may complete after leaving paper.
            contact_ok = self._contact_force > 1e-7
        return bool(xy_ok and z_ok and orientation_ok and contact_ok)

    def _collision_state(
        self, data: mujoco.MjData | None = None
    ) -> tuple[bool, list[str]]:
        collision_data = self.data if data is None else data
        severe = False
        labels: list[str] = []
        for contact_index in range(collision_data.ncon):
            contact = collision_data.contact[contact_index]
            if contact.dist > 0:
                continue
            pair = {int(contact.geom1), int(contact.geom2)}
            if pair == {self._brush_geom_id, self._paper_geom_id}:
                continue
            if pair in (
                {self._brush_geom_id, self._ink_pool_geom_id},
                {self._brush_geom_id, self._inkstone_lip_geom_id},
            ):
                continue
            if pair == {self._base_geom_id, self._floor_geom_id}:
                continue
            # Short tilt holder sits beside the pool; primitive wrist geoms graze
            # the lip even when the tuft is wiping cleanly.
            if pair & {
                self._ink_pool_geom_id,
                self._inkstone_lip_geom_id,
                self._inkstone_base_geom_id,
            } and pair & {
                self._wrist_roll_geom_id,
                self._gripper_body_geom_id,
            }:
                continue
            if self._paper_geom_id in pair and pair & self._robot_geom_ids:
                # ponytail: short tilt EE puts wrist primitives within a hair of
                # the paper; 1mm is still a real hit, 10µm is solver noise.
                # Upgrade: CAD meshes for wrist_flex / wrist_roll collision.
                if contact.dist > -0.001:
                    continue
                severe = True
                labels.append("arm-paper")
            elif self._floor_geom_id in pair and pair & self._robot_geom_ids:
                tolerance = 0.002 if self._wrist_flex_geom_id in pair else 0.001
                if contact.dist > -tolerance:
                    continue
                severe = True
                labels.append("arm-floor")
            elif pair & {
                self._ink_pool_geom_id,
                self._inkstone_lip_geom_id,
                self._inkstone_base_geom_id,
            } and pair & self._robot_geom_ids:
                if contact.dist > -0.0005:
                    continue
                severe = True
                labels.append("arm-inkstone")
            elif len(pair & self._robot_geom_ids) == 2:
                if self._brush_geom_id in pair:
                    continue
                # Display capsules overlap by sub-millimetres at calibrated
                # joint poses; CAD meshes are required before treating that as
                # a real link collision.
                if contact.dist > -0.0005:
                    continue
                severe = True
                labels.append("self-collision")
        return severe, sorted(set(labels))

    def _prospective_collision(self, joint_target: np.ndarray) -> bool:
        self._safety_data.qpos[:] = self.data.qpos
        self._safety_data.qvel[:] = 0.0
        self._safety_data.qpos[self._qpos_indices] = joint_target
        mujoco.mj_forward(self.model, self._safety_data)
        return self._collision_state(self._safety_data)[0]

    def _uses_left_a4_collision_line_search(self) -> bool:
        """Limit the reach workaround to the two left cells of six-up A4."""

        return bool(
            self.config.writing_layout.single_center_size is None
            and self._layout_index in (0, 1)
        )

    def _collision_recovery_active(self, *, command_down: bool) -> bool:
        return bool(
            command_down
            and self._uses_left_a4_collision_line_search()
            and self._collision_line_search_stalls >= 20
        )

    def _collision_checked_target(
        self, requested: np.ndarray, *, command_down: bool
    ) -> np.ndarray:
        if not command_down or not self._uses_left_a4_collision_line_search():
            self._collision_line_search_stalls = 0
            return requested
        current = self._joint_targets
        difference = requested - current
        for scale in (1.0, 0.5, 0.25):
            candidate = current + scale * difference
            if not self._prospective_collision(candidate):
                self._collision_line_search_stalls = 0
                return candidate
        self._collision_line_search_stalls += 1
        return current.copy()

    def _has_contact(self, first: int, second: int) -> bool:
        target = {first, second}
        if any(
            self.data.contact[index].dist <= 0
            and {
                int(self.data.contact[index].geom1),
                int(self.data.contact[index].geom2),
            }
            == target
            for index in range(self.data.ncon)
        ):
            return True
        # Inkstone geoms are calibrated in model space. MuJoCo's compiled
        # static broad phase can omit a moved world geom even though the exact
        # signed distance is negative; loading/wiping needs geometric overlap,
        # not a contact impulse.
        return bool(
            mujoco.mj_geomDistance(
                self.model,
                self.data,
                first,
                second,
                1.0,
                None,
            )
            <= 0.0
        )

    def _joint_limit_cost(self, qpos: np.ndarray) -> tuple[float, bool]:
        ranges = self._joint_limits[:, 1] - self._joint_limits[:, 0]
        distance = np.minimum(qpos - self._joint_limits[:, 0], self._joint_limits[:, 1] - qpos)
        normalized_distance = distance / ranges
        proximity = np.clip(
            (self.config.limit_margin_fraction - normalized_distance)
            / self.config.limit_margin_fraction,
            0.0,
            1.0,
        )
        hard_limit = bool(np.any(distance <= 1e-4))
        return float(proximity.sum()), hard_limit

    def _brush_contact_force(self) -> float:
        force = np.zeros(6, dtype=np.float64)
        total = 0.0
        for contact_index in range(self.data.ncon):
            contact = self.data.contact[contact_index]
            pair = {int(contact.geom1), int(contact.geom2)}
            if pair == {self._brush_geom_id, self._paper_geom_id}:
                mujoco.mj_contactForce(self.model, self.data, contact_index, force)
                total += max(float(force[0]), 0.0)
        return total

    def _apply_hardware_pose(
        self,
        *,
        mount_noise: np.ndarray | None = None,
        tip_scale_noise: float = 0.0,
        inkstone_noise: np.ndarray | None = None,
    ) -> None:
        """Apply measured brush/inkstone offsets (plus optional DR noise) to MJCF."""

        hardware = self.config.hardware
        mount = np.asarray(hardware.brush_mount_offset_m, dtype=np.float64)
        if mount_noise is not None:
            mount = mount + np.asarray(mount_noise, dtype=np.float64)
        # The model is compiled at the configured grip-to-tip length. Reset
        # randomization is a relative perturbation of its rigid reference only;
        # hardware diagnostics keep the measured geometry exactly.
        tip_scale = 1.0 + tip_scale_noise
        measured = float(hardware.brush_tip_length_scale)
        in_stock_band = 0.75 <= measured <= 1.35
        tip_scale = float(
            np.clip(tip_scale, 0.75, 1.35)
            if tip_scale_noise != 0.0 and in_stock_band
            else 1.0
        )
        inkstone = np.asarray(hardware.inkstone_offset_m, dtype=np.float64)
        if inkstone_noise is not None:
            inkstone = inkstone + np.asarray(inkstone_noise, dtype=np.float64)
        self._inkstone_pose_offset = inkstone.copy()

        mount_pos = self._base_brush_mount_site + mount
        rest_span = self._base_brush_rest_tip_site - self._base_brush_mount_site
        self.model.site_pos[self._brush_mount_site_id] = mount_pos
        self.model.site_pos[self._brush_rest_tip_site_id] = mount_pos + rest_span * tip_scale
        self.model.body_pos[self._brush_bristle_body_id] = (
            self._base_brush_bristle_body + mount
        )
        self.model.geom_pos[self._inkstone_base_geom_id] = (
            self._base_inkstone_base_pos + inkstone
        )
        self.model.geom_pos[self._ink_pool_geom_id] = self._base_ink_pool_pos + inkstone
        self.model.geom_pos[self._inkstone_lip_geom_id] = (
            self._base_inkstone_lip_pos + inkstone
        )
        # mj_setConst updates inertia, but does NOT rebuild collision bounds.
        # Recompile the static geometry after moving/resizing paper/inkstone.
        # Hardware replay needs the measured paper/inkstone collision bounds.
        # Keep the historical stock training scene reproducible until its
        # changed contact physics can pass the full adoption evaluation.
        if (hardware.brush_tip_length_scale != 1.0
                or hardware.brush_tuft_length_m != 0.038
                or self.config.brush.distributed_contact):
            refresh_world_collision_bounds(self.model)
        mujoco.mj_setConst(self.model, self.data)

    def _apply_fixed_layout(self) -> None:
        """Apply the configured paper and robot-base pose to the MJCF model."""

        paper = self.config.paper
        self.model.geom_size[self._paper_geom_id, :2] = (
            paper.width * 0.5,
            paper.height * 0.5,
        )
        self.model.geom_pos[self._paper_geom_id] = (
            paper.center_x,
            paper.center_y,
            paper.surface_z - self.model.geom_size[self._paper_geom_id, 2],
        )
        self.model.body_pos[self._base_body_id, :2] = (
            self.config.hardware.base_position_xy_m
        )
        self.model.body_pos[self._base_body_id, 2] = self.config.hardware.base_riser_height_m

    def _apply_domain_randomization(self) -> tuple[float, float]:
        self.model.geom_friction[self._paper_geom_id] = self._base_paper_friction
        self.model.dof_damping[:] = self._base_dof_damping
        self.model.dof_frictionloss[:] = self._base_dof_friction
        self.model.actuator_gainprm[:] = self._base_actuator_gain
        self.model.actuator_biasprm[:] = self._base_actuator_bias
        self.model.jnt_stiffness[self._brush_joint_ids] = self._base_brush_stiffness
        self._latency_steps = self.config.servo_latency_steps
        ink_load = self.config.ink.initial_ink
        water = self.config.ink.initial_water
        mount_noise = None
        tip_noise = 0.0
        inkstone_noise = None
        if self.config.domain_randomization:
            hardware = self.config.hardware
            amplitude = hardware.mount_offset_randomization_m
            mount_noise = self.np_random.uniform(-amplitude, amplitude, size=3)
            tip_noise = float(
                self.np_random.uniform(
                    -hardware.tip_length_randomization,
                    hardware.tip_length_randomization,
                )
            )
            ink_amp = hardware.inkstone_offset_randomization_m
            inkstone_noise = self.np_random.uniform(-ink_amp, ink_amp, size=3)
            friction_scale = self.np_random.uniform(
                1.0 - self.config.friction_randomization,
                1.0 + self.config.friction_randomization,
            )
            self.model.geom_friction[self._paper_geom_id] *= friction_scale
            dof_scale = self.np_random.uniform(
                1.0 - self.config.friction_randomization,
                1.0 + self.config.friction_randomization,
                size=len(self._qvel_indices),
            )
            self.model.dof_damping[self._qvel_indices] *= dof_scale
            self.model.dof_frictionloss[self._qvel_indices] *= dof_scale
            actuator_scale = self.np_random.uniform(
                1.0 - self.config.actuator_randomization,
                1.0 + self.config.actuator_randomization,
                size=(self.model.nu, 1),
            )
            self.model.actuator_gainprm[:] *= actuator_scale
            self.model.actuator_biasprm[:] *= actuator_scale
            stiffness_scale = self.np_random.uniform(
                1.0 - self.config.brush_stiffness_randomization,
                1.0 + self.config.brush_stiffness_randomization,
                size=len(self._brush_joint_ids),
            )
            self.model.jnt_stiffness[self._brush_joint_ids] *= stiffness_scale
            low = max(
                0, self.config.servo_latency_steps - self.config.latency_randomization
            )
            high = self.config.servo_latency_steps + self.config.latency_randomization
            self._latency_steps = int(self.np_random.integers(low, high + 1))
            ink_load = float(
                np.clip(
                    self.config.ink.initial_ink + self.np_random.uniform(-0.12, 0.05),
                    0.55,
                    1.0,
                )
            )
            water = float(
                np.clip(
                    self.config.ink.initial_water + self.np_random.uniform(-0.15, 0.15),
                    0.25,
                    1.0,
                )
            )
        self._apply_hardware_pose(
            mount_noise=mount_noise,
            tip_scale_noise=tip_noise,
            inkstone_noise=inkstone_noise,
        )
        return ink_load, water

    def _reset_quality_state(self, ink_load: float, water: float) -> None:
        self.ink.reset(ink_load=ink_load, water=water)
        self._stroke_records = [
            {
                "points": [],
                "progress": [],
                "width": [],
                "pressure": [],
                "target_width": [],
                "target_pressure": [],
                "target_index": [],
                "xy_error": [],
                "z_error": [],
                "pressure_offset": [],
                "pressure_offset_feedforward": [],
                "pressure_offset_residual": [],
                "pressure_calibration_clipped": [],
                "pressure_calibration_fallback": [],
                "speed": [],
                "opening": [],
                "actual_angle_deg": [],
                "target_angle_deg": [],
            }
            for _ in self.trajectory.strokes
        ]
        self._pressure_calibration_samples = []
        self._stroke_scores.clear()
        self._endpoint_scores = []
        self._balance_metrics = {
            "centroid": 0.0,
            "scale": 0.0,
            "tilt": 0.0,
            "score": 0.0,
        }
        self._beauty_score = 0.0
        self._beauty_components = {name: 0.0 for name in self._beauty_components}
        self._width_details = {name: 0.0 for name in self._width_details}
        self._glyph_metrics = {name: 0.0 for name in self._glyph_metrics}
        self._motion_metrics = {name: 0.0 for name in self._motion_metrics}
        self._tip_velocity_history = []
        self._joint_acceleration_history = []
        self._episode_collision = False
        self._collision_line_search_stalls = 0
        self._loaded_ink_peak = 0.0
        self._wiped_excess_min = 1.0

    def _complete_stroke(self, stroke_index: int) -> dict[str, float]:
        if stroke_index in self._stroke_scores:
            return self._stroke_scores[stroke_index]
        record = self._stroke_records[stroke_index]
        mask = np.logical_and(
            self.waypoints.pen_down,
            self.waypoints.stroke_indices == stroke_index,
        )
        target_tangents = self.waypoints.target_tangents[mask]
        if len(target_tangents) >= 2:
            turn = np.linalg.norm(np.diff(target_tangents, axis=0), axis=1)
            curvature = np.concatenate(([0.0], turn))
        else:
            curvature = None
        metrics = stroke_quality(
            actual_points=np.asarray(record["points"], dtype=np.float64).reshape(-1, 2),
            actual_progress=np.asarray(record["progress"], dtype=np.float64),
            actual_width=np.asarray(record["width"], dtype=np.float64),
            actual_pressure=np.asarray(record["pressure"], dtype=np.float64),
            actual_speed=np.asarray(record["speed"], dtype=np.float64),
            target_points=self.waypoints.positions[mask, :2],
            target_progress=self.waypoints.stroke_progress[mask],
            target_width=self.waypoints.target_width[mask],
            target_pressure=self.waypoints.target_pressure[mask],
            target_speed=self.waypoints.target_speed[mask],
            target_tangent=target_tangents[-1],
            technique=self.waypoints.techniques[np.flatnonzero(mask)[-1]],
            curvature=curvature,
        )
        endpoint_values: list[float] = []
        if self._professional_mask is not None:
            for endpoint in np.flatnonzero(self._exposed_horizontal[stroke_index]):
                quality = self._endpoint_quality(stroke_index, int(endpoint))
                endpoint_values.append(float(quality["wedge"]))
                self._endpoint_scores.append(
                    {
                        "stroke_index": stroke_index,
                        "endpoint": "start" if endpoint == 0 else "finish",
                        **quality,
                    }
                )
        if endpoint_values:
            metrics["endpoint_shape"] = float(np.mean(endpoint_values))
        self._stroke_scores[stroke_index] = metrics
        self._update_beauty(final=False)
        return metrics

    def _endpoint_quality(self, stroke_index: int, endpoint: int) -> dict[str, float]:
        """Score an exposed end in local stroke coordinates."""

        if self._professional_mask is None:
            raise RuntimeError("endpoint quality requires a professional exemplar")
        mask = np.logical_and(
            self.waypoints.pen_down,
            self.waypoints.stroke_indices == stroke_index,
        )
        # Score the endpoint that is actually authored after 逆入/回鋒 path
        # deltas. Using the source skeleton made a deliberate 3 mm reverse
        # entry look like stray ink and gave an unmarked finish a perfect
        # wedge score.
        points = np.asarray(self.waypoints.positions[mask, :2], dtype=np.float64)
        point = points[0] if endpoint == 0 else points[-1]
        neighbour = points[1] if endpoint == 0 else points[-2]
        inward = neighbour - point
        inward /= max(float(np.linalg.norm(inward)), 1e-12)
        normal = np.asarray([-inward[1], inward[0]], dtype=np.float64)
        widths = self.waypoints.target_width[mask]
        width = float(widths[0] if endpoint == 0 else widths[-1])
        width = max(width, self.config.brush.minimum_width)
        along = np.linspace(-0.5 * width, 1.5 * width, 32)
        across = np.linspace(-1.25 * width, 1.25 * width, 32)
        local_along, local_across = np.meshgrid(along, across, indexing="ij")
        samples = (
            point
            + local_along.reshape(-1, 1) * inward
            + local_across.reshape(-1, 1) * normal
        )
        actual = sample_paper_mask(
            self.ink.pigment,
            samples,
            self.config.paper,
            self.config.ink,
        ).reshape(32, 32)
        target = sample_paper_mask(
            self._professional_mask,
            samples,
            self.config.paper,
            self.config.ink,
        ).reshape(32, 32)
        return endpoint_shape_quality(actual, target)

    def _outside_ink_fraction(self) -> float:
        ink_points = self.ink.ink_points(maximum=1200)
        if len(ink_points) == 0:
            return 1.0
        target_points = np.concatenate(
            [stroke.points for stroke in self.trajectory.strokes], axis=0
        )
        distance = np.linalg.norm(
            ink_points[:, None, :] - target_points[None, :, :], axis=2
        ).min(axis=1)
        band = self.config.brush.maximum_width * 0.5 + 0.004
        return float(np.mean(distance > band))

    def _update_beauty(self, *, final: bool) -> None:
        qualities = tuple(self._stroke_scores.values())
        stroke_score = (
            float(np.mean([value["score"] for value in qualities]))
            if qualities
            else 0.0
        )
        unintended = max(self.ink.unintended_fraction, self._outside_ink_fraction())
        if final:
            ink_points = self.ink.ink_points()
            target_points = np.concatenate(
                [stroke.points for stroke in self.trajectory.strokes], axis=0
            )
            self._balance_metrics = character_balance(ink_points, target_points)
            if self._professional_mask is not None:
                self._glyph_metrics = glyph_mask_quality(
                    self.ink.pigment,
                    self._professional_mask,
                )
            self._motion_metrics = smooth_motion_quality(
                np.asarray(self._tip_velocity_history, dtype=np.float64),
                np.asarray(self._joint_acceleration_history, dtype=np.float64),
            )
        shape = (
            self._glyph_metrics["score"]
            if self._professional_mask is not None and final
            else float(np.mean([value["shape"] for value in qualities]))
            if qualities
            else 0.0
        )
        width = (
            float(np.mean([value["width"] for value in qualities]))
            if qualities
            else 0.0
        )
        width_details = {
            name: (
                float(np.mean([value[name] for value in qualities]))
                if qualities
                else 0.0
            )
            for name in WIDTH_DETAIL_KEYS
        }
        hierarchy = 1.0
        if len(qualities) >= 2:
            actual_medians = np.asarray(
                [
                    float(
                        np.median(
                            np.asarray(
                                self._stroke_records[index]["width"], dtype=np.float64
                            )
                        )
                    )
                    for index in self._stroke_scores
                    if self._stroke_records[index]["width"]
                ],
                dtype=np.float64,
            )
            target_medians = []
            for stroke_index in self._stroke_scores:
                mask = np.logical_and(
                    self.waypoints.pen_down,
                    self.waypoints.stroke_indices == stroke_index,
                )
                if np.any(mask):
                    target_medians.append(
                        float(np.median(self.waypoints.target_width[mask]))
                    )
            if len(actual_medians) >= 2 and len(target_medians) == len(actual_medians):
                actual_rel = actual_medians / max(float(np.median(actual_medians)), 1e-9)
                target_rel = np.asarray(target_medians) / max(
                    float(np.median(target_medians)), 1e-9
                )
                hierarchy = float(
                    np.exp(-float(np.mean(np.square(np.log(actual_rel / target_rel)))) / 0.18**2)
                )
        width_details["stroke_width_hierarchy"] = hierarchy
        self._width_details = {
            name: 100.0 * float(value) for name, value in width_details.items()
        }
        trajectory = (
            float(
                np.mean(
                    [0.58 * value["shape"] + 0.42 * value["frechet"] for value in qualities]
                )
            )
            if qualities
            else 0.0
        )
        brushwork = (
            float(
                np.mean(
                    [
                        0.64 * value["finish"]
                        + 0.20 * value["pressure"]
                        + 0.16 * value["speed"]
                        for value in qualities
                    ]
                )
            )
            if qualities
            else 0.0
        )
        if self.config.modules.inkstone:
            core = float(getattr(self.ink, "core_ink", 0.0))
            surface = float(getattr(self.ink, "surface_ink", 0.0))
            load_amount = np.clip(
                self._loaded_ink_peak
                / (self.config.ink.core_capacity + self.config.ink.target_surface_ink),
                0.0,
                1.0,
            )
            surface_control = np.exp(
                -((surface - self.config.ink.target_surface_ink) / 0.30) ** 2
            )
            wipe_control = np.exp(-((self._wiped_excess_min / 0.12) ** 2))
            ink_loading = float(
                0.42 * load_amount
                + 0.28 * surface_control
                + 0.22 * wipe_control
                + 0.08 * min(core / self.config.ink.core_capacity, 1.0)
            )
        else:
            ink_loading = 1.0
        drips = int(getattr(self.ink, "drip_count", 0))
        completed_fraction = len(self._stroke_scores) / len(self.trajectory.strokes)
        components = {
            "glyph_shape": shape,
            "stroke_placement": float(
                np.mean([value["placement"] for value in qualities])
            ) if qualities else 0.0,
            "stroke_length": float(
                np.mean([value["length"] for value in qualities])
            ) if qualities else 0.0,
            "stroke_angle": float(
                np.mean([value["angle"] for value in qualities])
            ) if qualities else 0.0,
            "line_width": width,
            "trajectory": trajectory,
            "stroke_order": 1.0 if final else completed_fraction,
            "smoothness": self._motion_metrics["score"] if final else 0.0,
            "brushwork": brushwork,
            "ink_quality": float(
                0.64 * (1.0 - unintended)
                + 0.36 * min(self.ink.ink_load / 0.55, 1.0)
            ),
            "ink_loading": ink_loading,
            "drip_control": float(np.exp(-1.4 * drips)),
            "collision_safety": 0.0 if self._episode_collision else 1.0,
            "balance": self._balance_metrics["score"] if final else 0.0,
        }
        self._beauty_score, self._beauty_components = aggregate_beauty_components(
            components
        )

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        if options and "trajectory_index" in options:
            trajectory_index = int(options["trajectory_index"])
        elif len(self.trajectories) > 1:
            trajectory_index = int(self.np_random.integers(len(self.trajectories)))
        else:
            trajectory_index = 0
        if options and "layout_index" in options:
            layout_index = int(options["layout_index"])
        elif self.config.domain_randomization:
            layouts = self.config.training_layout_indices or tuple(
                range(len(writing_frames(self.config.paper, self.config.writing_layout)))
            )
            layout_index = int(self.np_random.choice(layouts))
        else:
            layout_index = 0
        mujoco.mj_resetData(self.model, self.data)
        ink_load, water = self._apply_domain_randomization()
        self._select_trajectory(trajectory_index, layout_index)
        target_index = int(options.get("target_index", 0)) if options else 0
        if not 0 <= target_index < len(self.waypoints):
            raise ValueError(f"target_index must be in [0, {len(self.waypoints) - 1}]")
        self._target_index = target_index
        self._target_dwell = 0
        self._step_count = 0
        self._solve_position_ik(self.target_position)
        if self.config.reset_noise > 0:
            noise = self.np_random.uniform(
                -self.config.reset_noise, self.config.reset_noise, size=len(JOINT_NAMES)
            )
            noisy_qpos = self.data.qpos[self._qpos_indices] + noise
            self.data.qpos[self._qpos_indices] = np.clip(
                noisy_qpos, self._joint_limits[:, 0] + 0.005, self._joint_limits[:, 1] - 0.005
            )
        if self.config.legacy_attachment_compensation:
            self.data.qpos[self._qpos_indices[-1]] = (
                self.config.hardware.fixed_attachment_servo_angle_rad
            )
        self.data.qvel[:] = 0.0
        self._joint_targets = self.data.qpos[self._qpos_indices].copy()
        self.data.ctrl[:] = self._joint_targets
        self._command_queue = [
            self._joint_targets.copy() for _ in range(self._latency_steps)
        ]
        self._previous_action.fill(0.0)
        self._previous_qvel.fill(0.0)
        self._tip_velocity.fill(0.0)
        self._previous_tip_velocity.fill(0.0)
        self._pressure = 0.0
        self._contact_pressure_offset = 0.0
        self._feedforward_pressure_offset = 0.0
        self._residual_pressure_offset = 0.0
        self._pressure_calibration_clipped = False
        self._pressure_calibration_fallback = False
        self._contact_dwell = 0
        self._contact_force = 0.0
        self._last_width = 0.0
        self._reset_quality_state(ink_load, water)
        self._image_error = self._normalized_image_error()
        self._set_target_marker()
        mujoco.mj_forward(self.model, self.data)
        self._previous_brush_position = self.brush_position
        self._brush_state = self.brush_physics.observe(
            self.data,
            contact_force=0.0,
            tip_velocity=self._tip_velocity,
        )
        info = {
            "task": self.task,
            "trajectory_source": self.trajectory.source,
            "trajectory_index": self._trajectory_index,
            "layout_index": self._layout_index,
            "writing_frame_size_m": float(
                writing_frames(self.config.paper, self.config.writing_layout)[
                    self._layout_index
                ][1][0]
            ),
            "target_index": self._target_index,
            "progress": self.progress,
            "is_success": False,
            "beauty_score": self.beauty_score,
            "beauty_components": self.beauty_components,
            "width_details": self._width_details.copy(),
            "ink_load": self.ink.ink_load,
            "water": self.ink.water,
            "latency_steps": self._latency_steps,
            "observation_version": self.observation_version,
            "core_ink": float(getattr(self.ink, "core_ink", self.ink.ink_load)),
            "surface_ink": float(
                getattr(self.ink, "surface_ink", self.ink.ink_load)
            ),
            "drip_risk": float(getattr(self.ink, "drip_risk", 0.0)),
            "drip_count": int(getattr(self.ink, "drip_count", 0)),
            "pressure_calibration_clipped": False,
            "pressure_calibration_fallback": False,
        }
        if self.render_mode == "human":
            self.render()
        return self._get_obs(), info

    def step(
        self, action: np.ndarray
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        action = np.asarray(action, dtype=np.float64)
        if action.shape != self.action_space.shape:
            raise ValueError(
                f"Action must have shape {self.action_space.shape}, got {action.shape}."
            )
        action = np.clip(action, -1.0, 1.0)
        joint_command = action
        analytical_tilt_target: float | None = None
        command_down = bool(self._target_metadata()["down"])
        if self.config.ik_assist:
            residual = action.copy()
            self._update_contact_pressure_control(
                min(self._target_index, len(self.waypoints) - 1)
            )
            expert = self.expert_action()
            if (
                self.config.attachment_pose_control
                and self.config.modules.brushwork == "professional"
            ):
                analytical_tilt_target = float(
                    np.clip(
                        self._joint_targets[-1]
                        + float(expert[-1]) * self.config.action_delta,
                        self._joint_limits[-1, 0] + self.config.command_limit_margin,
                        self._joint_limits[-1, 1] - self.config.command_limit_margin,
                    )
                )
                if command_down:
                    if self._uses_fixed_contact_lean():
                        residual[-1] = 0.0
                    else:
                        residual[-1] *= self.config.tilt_residual_scale
                else:
                    residual[-1] = 0.0
            joint_command = np.clip(
                expert + self.config.residual_action_scale * residual,
                -1.0,
                1.0,
            )
        control_dt = self.model.opt.timestep * self.config.frame_skip
        requested_targets = np.clip(
            self._joint_targets + joint_command * self.config.action_delta,
            self._joint_limits[:, 0] + self.config.command_limit_margin,
            self._joint_limits[:, 1] - self.config.command_limit_margin,
        )
        if self.config.legacy_attachment_compensation:
            requested_targets[-1] = (
                self.config.hardware.fixed_attachment_servo_angle_rad
            )
        elif analytical_tilt_target is not None:
            if command_down:
                requested_targets[-1] = np.clip(
                    requested_targets[-1],
                    analytical_tilt_target - self.config.tilt_residual_limit,
                    analytical_tilt_target + self.config.tilt_residual_limit,
                )
            else:
                requested_targets[-1] = analytical_tilt_target
        maximum_delta = np.full(
            len(JOINT_NAMES), self.config.max_joint_speed * control_dt
        )
        if command_down:
            maximum_delta[-1] = min(
                maximum_delta[-1],
                self.config.contact_tilt_max_speed * control_dt,
            )
        next_joint_targets = self._joint_targets + np.clip(
            requested_targets - self._joint_targets, -maximum_delta, maximum_delta
        )
        self._joint_targets = self._collision_checked_target(
            next_joint_targets,
            command_down=command_down,
        )
        self._command_queue.append(self._joint_targets.copy())
        applied_targets = self._command_queue.pop(0)
        self.data.ctrl[:] = applied_targets
        for _ in range(self.config.frame_skip):
            mujoco.mj_step(self.model, self.data)
        self._step_count += 1

        qpos = self.data.qpos[self._qpos_indices].copy()
        qvel = self.data.qvel[self._qvel_indices].copy()
        acceleration = (qvel - self._previous_qvel) / control_dt
        action_change = action - self._previous_action
        brush = self.brush_position
        controlled_brush = self.controlled_brush_position
        self._tip_velocity = (brush - self._previous_brush_position) / control_dt
        tip_acceleration = float(
            np.linalg.norm(self._tip_velocity - self._previous_tip_velocity) / control_dt
        )
        tip_speed = float(np.linalg.norm(self._tip_velocity[:2]))
        self._contact_force = self._brush_contact_force()
        self._brush_state = self.brush_physics.observe(
            self.data,
            contact_force=self._contact_force,
            tip_velocity=self._tip_velocity,
        )
        if self._contact_force > 1e-7:
            # The 38mm tuft can sink about 0.6mm into MuJoCo's soft contact
            # while carrying very little load. Bend/opening still shapes the
            # deposited mark; pressure itself follows measured normal force.
            self._pressure = _filter_contact_pressure(
                self._pressure,
                _pressure_from_contact_force(
                    self._contact_force, self._effective_nominal_force()
                ),
                contact=True,
                maximum_change=self.config.brush.pressure_slew_per_step,
                response=self._effective_pressure_control()[0],
            )
        else:
            self._pressure = _filter_contact_pressure(
                self._pressure,
                0.0,
                contact=False,
            )
        target = self.target_position
        target_index = min(self._target_index, len(self.waypoints) - 1)
        metadata = self._target_metadata(target_index)
        down = bool(metadata["down"])
        target_brush_axis = self._desired_brush_axis(target_index)
        actual_attachment_axis = self.brush_mount_axis
        actual_lean_deg = float(
            np.degrees(
                np.arctan2(
                    np.linalg.norm(actual_attachment_axis[:2]),
                    max(-float(actual_attachment_axis[2]), 1e-12),
                )
            )
        )
        target_lean_deg = float(
            np.degrees(
                np.arctan2(
                    np.linalg.norm(target_brush_axis[:2]),
                    max(-float(target_brush_axis[2]), 1e-12),
                )
            )
        )
        phase = self.waypoints.phases[target_index]
        drips_before = int(getattr(self.ink, "drip_count", 0))
        pool_contact = self._has_contact(self._brush_geom_id, self._ink_pool_geom_id)
        lip_contact = self._has_contact(
            self._brush_geom_id, self._inkstone_lip_geom_id
        )
        if phase == "ink_load":
            pool_surface_z = float(
                self.model.geom_pos[self._ink_pool_geom_id, 2]
                + self.model.geom_size[self._ink_pool_geom_id, 2]
            )
            self.ink.load_from_inkstone(
                contact=pool_contact,
                immersion=float(
                    np.clip(
                        (
                            pool_surface_z
                            + self.config.brush.tip_radius
                            - brush[2]
                        )
                        / max(self.config.brush.tip_radius, 1e-9),
                        0.0,
                        1.0,
                    )
                ),
            )
            self._loaded_ink_peak = max(
                self._loaded_ink_peak,
                float(getattr(self.ink, "core_ink", 0.0))
                + float(getattr(self.ink, "surface_ink", 0.0)),
            )
        elif phase == "ink_wipe":
            self.ink.wipe_on_lip(contact=lip_contact, speed=tip_speed)
            self._wiped_excess_min = min(
                self._wiped_excess_min,
                float(getattr(self.ink, "excess_ink", 0.0)),
            )
        elif self._contact_force <= 1e-7:
            paper = self.config.paper
            over_paper = bool(
                abs(brush[0] - paper.center_x) <= paper.width * 0.5
                and abs(brush[1] - paper.center_y) <= paper.height * 0.5
            )
            self.ink.advance_airborne(
                position=brush,
                uprightness=float(
                    np.clip(
                        np.dot(self._brush_state.shaft_axis, np.asarray([0.0, 0.0, -1.0])),
                        0.0,
                        1.0,
                    )
                ),
                acceleration=tip_acceleration,
                over_paper=over_paper,
            )
        new_drips = int(getattr(self.ink, "drip_count", 0)) - drips_before
        previous_image_error = self._image_error
        mark = None
        if self._contact_force > 1e-7:
            # 穂の軸を紙面に落とした向きと、紙面法線からの傾き。
            # 筆は円錐なので、寝かせた向きへ接地面が伸び穂先側が尖る。
            axis = np.asarray(self.brush_mount_axis, dtype=np.float64)
            shaft_xy = axis[:2]
            shaft_lean = float(np.clip(np.linalg.norm(shaft_xy), 0.0, 1.0))
            mark = self.ink.deposit(
                brush,
                pressure=self._pressure,
                speed=tip_speed,
                deflection=self.brush_deflection,
                tangent=metadata["tangent"],
                intended=down,
                stroke_index=int(self.waypoints.stroke_indices[target_index]),
                opening=self._brush_state.opening,
                roll=self._brush_state.roll,
                phase=metadata["brushwork_phase"],
                technique=metadata["technique"],
                shaft_direction=shaft_xy,
                lean=shaft_lean,
            )
        if mark is not None and self._professional_mask is not None:
            self._image_error = self._normalized_image_error()
        image_improvement = previous_image_error - self._image_error
        exemplar_occupancy = (
            float(
                sample_paper_mask(
                    self._professional_mask,
                    brush[None, :2],
                    self.config.paper,
                    self.config.ink,
                )[0]
            )
            if self._professional_mask is not None and mark is not None and down
            else 1.0
        )
        self._last_width = mark.width if mark is not None else 0.0
        if down and mark is not None:
            record = self._stroke_records[int(self.waypoints.stroke_indices[target_index])]
            record["points"].append(brush[:2].copy())
            record["progress"].append(metadata["stroke_progress"])
            record["width"].append(self._last_width)
            record["pressure"].append(self._pressure)
            record["target_width"].append(metadata["width"])
            record["target_pressure"].append(metadata["pressure"])
            record["target_index"].append(target_index)
            record["xy_error"].append(float(np.linalg.norm(target[:2] - brush[:2])))
            record["z_error"].append(float(target[2] - brush[2]))
            record["pressure_offset"].append(self._contact_pressure_offset)
            record["pressure_offset_feedforward"].append(self._feedforward_pressure_offset)
            record["pressure_offset_residual"].append(self._residual_pressure_offset)
            record["pressure_calibration_clipped"].append(
                1.0 if self._pressure_calibration_clipped else 0.0
            )
            record["pressure_calibration_fallback"].append(
                1.0 if self._pressure_calibration_fallback else 0.0
            )
            record["speed"].append(tip_speed)
            record["opening"].append(self._brush_state.opening)
            record["actual_angle_deg"].append(actual_lean_deg)
            record["target_angle_deg"].append(target_lean_deg)
        if down:
            self._pressure_calibration_samples.append(
                {
                    "layout_class": self._current_layout_class(),
                    "commanded_angle_deg": self._pressure_calibration_angle_deg(
                        self._target_index
                    ),
                    "actual_angle_deg": actual_lean_deg,
                    "phase": str(metadata.get("brushwork_phase", "send")),
                    "target_pressure": float(metadata["pressure"]),
                    "actual_pressure": self._pressure,
                    "z_offset_m": self._contact_pressure_offset,
                    "contact_force": self._contact_force,
                    "actual_width_m": self._last_width,
                    "target_width_m": float(metadata["width"]),
                    "opening": self._brush_state.opening,
                    "xy_error_m": float(np.linalg.norm(target[:2] - brush[:2])),
                    "z_error_m": float(abs(target[2] - brush[2])),
                    "dwell": self._contact_dwell,
                    "contact": self._contact_force > 1e-7,
                    "clipped": self._pressure_calibration_clipped,
                    "fallback": self._pressure_calibration_fallback,
                    "probe": self.config.pressure_probe_offset_m is not None,
                    "probe_offset_m": self.config.pressure_probe_offset_m,
                    "probe_feedback_gain": 0.0
                    if self.config.pressure_probe_offset_m is not None
                    else None,
                }
            )
        error = target - controlled_brush
        xy_distance = float(np.linalg.norm(error[:2]))
        z_distance = float(abs(error[2]))
        spatial_distance = float(np.linalg.norm(error))

        if down:
            tracking = np.exp(-((xy_distance / 0.020) ** 2))
            height_tracking = np.exp(-((z_distance / 0.012) ** 2))
        else:
            tracking = np.exp(-((spatial_distance / 0.030) ** 2))
            height_tracking = np.exp(-((z_distance / 0.018) ** 2))

        reached = self._target_reached(controlled_brush)
        self._target_dwell += 1
        if self._pressure_probe_should_wait(target_index):
            reached = False
        tilt_unreachable = bool(
            not reached
            and self._uses_attachment_priority(target_index)
            and phase == "tilt_prepare"
            and self._target_dwell >= self.config.attachment_max_dwell
        )
        if (
            not reached
            and self.config.max_pen_down_dwell > 0
            and down
            and self._target_dwell >= self.config.max_pen_down_dwell
        ):
            # 到達判定が成立しないまま擦り続けると、末端に墨が溜まり画が癒着する。
            # 書き手は届かない一点に留まらず次へ運ぶので、滞留上限で先へ進める。
            reached = True
        advanced = 0
        is_success = False
        completed_stroke_metrics: dict[str, float] | None = None
        if reached:
            next_index = target_index + 1
            finishes_stroke = (
                self.waypoints.phases[target_index] == "draw"
                and (
                    next_index >= len(self.waypoints)
                    or self.waypoints.phases[next_index] != "draw"
                    or self.waypoints.stroke_indices[next_index]
                    != self.waypoints.stroke_indices[target_index]
                )
            )
            if finishes_stroke:
                completed_stroke_metrics = self._complete_stroke(
                    int(self.waypoints.stroke_indices[target_index])
                )
            self._target_index += 1
            self._target_dwell = 0
            advanced = 1
            if self._target_index >= len(self.waypoints):
                is_success = True
                self._target_index = len(self.waypoints)
            self._set_target_marker()

        limit_cost, hard_limit = self._joint_limit_cost(qpos)
        collision, collision_types = self._collision_state()
        self._episode_collision = self._episode_collision or collision
        if self._contact_force > self.config.brush.maximum_force:
            collision = True
            collision_types.append("excessive-brush-force")
            collision_types = sorted(set(collision_types))
            self._episode_collision = True

        if is_success:
            self._tip_velocity_history.append(self._tip_velocity.copy())
            self._joint_acceleration_history.append(acceleration.copy())
            self._update_beauty(final=True)

        if down:
            pressure_tracking = np.exp(-(((self._pressure - metadata["pressure"]) / 0.28) ** 2))
            speed_tracking = np.exp(-(((tip_speed - metadata["speed"]) / 0.12) ** 2))
            # Match the kaisho planner target width, not AnimCJK outline samples.
            width_tracking = np.exp(-(((self._last_width - metadata["width"]) / 0.0045) ** 2))
        elif phase in ("ink_load", "ink_wipe"):
            pressure_tracking = 1.0
            speed_tracking = 1.0
            width_tracking = 1.0
        else:
            pressure_tracking = np.exp(-((self._pressure / 0.12) ** 2))
            speed_tracking = 1.0
            width_tracking = 1.0 if mark is None else 0.0
        orientation_alignment = float(
            np.clip(np.dot(self.brush_axis, target_brush_axis), -1.0, 1.0)
        )
        orientation_tracking = np.exp(-(((1.0 - orientation_alignment) / 0.20) ** 2))

        weights = self.config.reward
        ink_transfer_score = (
            float(mark.density if mark is not None else 0.0) if down else 1.0
        )
        if phase == "ink_load":
            total_ink = float(getattr(self.ink, "core_ink", 0.0)) + float(
                getattr(self.ink, "surface_ink", 0.0)
            )
            loading_score = float(
                np.clip(
                    total_ink
                    / (self.config.ink.core_capacity + self.config.ink.target_surface_ink),
                    0.0,
                    1.0,
                )
            )
        elif phase == "ink_wipe":
            loading_score = float(
                np.exp(-((float(getattr(self.ink, "excess_ink", 0.0)) / 0.12) ** 2))
            )
        else:
            loading_score = float(
                1.0 - np.clip(float(getattr(self.ink, "drip_risk", 0.0)), 0.0, 1.0)
            )
        tome_finish_violation = 0.0
        if (
            down
            and metadata["brushwork_phase"] == "finish"
            and metadata["technique"] == "tome"
        ):
            if error[2] > 0.002:
                tome_finish_violation += (error[2] / 0.010) ** 2
            if metadata["width"] > 1e-9 and self._last_width > metadata["width"] * 1.10:
                tome_finish_violation += (
                    (self._last_width / metadata["width"] - 1.10) / 0.15
                ) ** 2
        harai_finish_bonus = 0.0
        if (
            down
            and metadata["brushwork_phase"] == "finish"
            and metadata["technique"] in ("harai", "hane")
        ):
            # 評価 (metrics の非 tome finish) と同じ成分・同じ許容で採点する。
            # 従来は速度許容 0.12（評価は 0.065）で、しかも評価側で最大重み
            # 0.30 の終端幅に対応する項が無く、抜きの勾配が届いていなかった。
            release = harai_finish_release(
                width=self._last_width,
                target_width=metadata["width"],
                pressure=self._pressure,
                target_pressure=metadata["pressure"],
                speed=tip_speed,
                target_speed=metadata["speed"],
            )
            harai_finish_bonus = weights.harai_finish_bonus * release
        smoothness_score = float(
            np.exp(-4.0 * np.mean(np.square(action_change)))
        )
        reward_terms = {
            # Dense quality terms are zero at perfection and negative otherwise.
            # This prevents a policy from lingering to collect a positive reward
            # repeatedly; ordered waypoint progress remains the positive signal.
            "tracking": weights.tracking * (float(tracking) - 1.0),
            "height": weights.height_tracking * (float(height_tracking) - 1.0),
            "pressure": weights.pressure_tracking
            * (float(pressure_tracking) - 1.0),
            "speed": weights.speed_tracking * (float(speed_tracking) - 1.0),
            "width": weights.width_tracking * (float(width_tracking) - 1.0),
            "orientation": weights.orientation_tracking
            * (float(orientation_tracking) - 1.0),
            "ink_transfer": weights.ink_transfer * (ink_transfer_score - 1.0),
            "ink_loading": weights.ink_loading * (loading_score - 1.0),
            "exemplar_tracking": weights.exemplar_tracking
            * (exemplar_occupancy - 1.0),
            "exemplar_image": weights.exemplar_image_improvement
            * image_improvement,
            "drip": -weights.drip_penalty * new_drips,
            "unintended_ink": -weights.unintended_ink_penalty
            * float(mark is not None and not down),
            "stroke_quality": weights.stroke_quality
            * float(
                completed_stroke_metrics["score"]
                if completed_stroke_metrics is not None
                else 0.0
            ),
            "character_balance": weights.character_balance
            * float(self._balance_metrics["score"])
            * float(is_success),
            "professional_shape": weights.professional_shape
            * (self._beauty_components["glyph_shape"] / 100.0)
            * float(is_success),
            "brushwork_quality": weights.brushwork_quality
            * float(
                completed_stroke_metrics["finish"]
                if completed_stroke_metrics is not None
                else 0.0
            ),
            "endpoint_shape": weights.endpoint_shape
            * float(
                completed_stroke_metrics.get("endpoint_shape", 0.0)
                if completed_stroke_metrics is not None
                else 0.0
            ),
            "tome_finish": -weights.tome_finish_penalty * tome_finish_violation,
            "harai_finish": harai_finish_bonus,
            "progress": weights.progress * advanced,
            "smoothness": weights.smoothness_bonus * (smoothness_score - 1.0),
            "action": -weights.action_penalty * float(np.mean(np.square(action))),
            "velocity": -weights.velocity_penalty * float(np.mean(np.square(qvel))),
            "acceleration": -weights.acceleration_penalty
            * float(np.mean(np.square(acceleration))),
            "gripper_motion": -weights.gripper_motion_penalty * float(abs(qvel[-1])),
            "joint_limit": -weights.joint_limit_penalty * limit_cost,
            "collision": -weights.collision_penalty * float(collision),
            "hard_limit": -weights.hard_limit_penalty * float(hard_limit),
            "completion": weights.completion * float(is_success),
        }
        reward = float(sum(reward_terms.values()))
        terminated = bool(
            is_success
            or collision
            or hard_limit
            or tilt_unreachable
        )
        truncated = False

        self._previous_action = action.copy()
        self._previous_qvel = qvel
        self._previous_tip_velocity = self._tip_velocity.copy()
        self._previous_brush_position = brush.copy()
        if not is_success:
            self._tip_velocity_history.append(self._tip_velocity.copy())
            self._joint_acceleration_history.append(acceleration.copy())
        pressure_response, pressure_gain, pressure_limit = (
            self._effective_pressure_control()
        )
        info: dict[str, Any] = {
            "task": self.task,
            "trajectory_source": self.trajectory.source,
            "trajectory_index": self._trajectory_index,
            "layout_index": self._layout_index,
            "writing_frame_size_m": float(
                writing_frames(self.config.paper, self.config.writing_layout)[
                    self._layout_index
                ][1][0]
            ),
            "target_index": self._target_index,
            "target_count": len(self.waypoints),
            "target_dwell": self._target_dwell,
            "stroke_index": int(self.waypoints.stroke_indices[target_index]),
            "phase": self.waypoints.phases[target_index],
            "episode_phase": self._episode_phase(target_index),
            "brushwork_phase": metadata["brushwork_phase"],
            "pen_down": down,
            "distance_xy": xy_distance,
            "distance_z": z_distance,
            "tip_speed": tip_speed,
            "brush_axis": self.brush_axis.copy(),
            "brush_deflection": self.brush_deflection,
            "brush_bend": self._brush_state.bend.copy(),
            "brush_bend_rate": self._brush_state.bend_rate.copy(),
            "terminal_brush_axis": self._brush_state.terminal_axis.copy(),
            "target_brush_axis": target_brush_axis,
            "brush_lean_deg": actual_lean_deg,
            "target_lean_deg": target_lean_deg,
            "attachment_axis_error_deg": float(
                np.degrees(
                    np.arccos(
                        np.clip(
                            self.brush_mount_axis @ target_brush_axis,
                            -1.0,
                            1.0,
                        )
                    )
                )
            ),
            "brush_opening": self._brush_state.opening,
            "brush_roll": self._brush_state.roll,
            "contact_force": self._contact_force,
            "pressure": self._pressure,
            "target_pressure": metadata["pressure"],
            "effective_nominal_force": self._effective_nominal_force(),
            "effective_pressure_response": pressure_response,
            "effective_contact_pressure_gain": pressure_gain,
            "effective_contact_pressure_limit": pressure_limit,
            "contact_pressure_offset": self._contact_pressure_offset,
            "feedforward_pressure_offset": self._feedforward_pressure_offset,
            "residual_pressure_offset": self._residual_pressure_offset,
            "pressure_calibration_clipped": self._pressure_calibration_clipped,
            "pressure_calibration_fallback": self._pressure_calibration_fallback,
            "collision_line_search_stalls": self._collision_line_search_stalls,
            "effective_entry_angle_deg": float(
                np.degrees(np.arctan(self._effective_entry_lean()))
            ),
            "target_speed": metadata["speed"],
            "target_width": metadata["width"],
            "target_roll": metadata["roll"],
            "line_width": self._last_width,
            "technique": metadata["technique"],
            "stroke_progress": metadata["stroke_progress"],
            "ink_load": self.ink.ink_load,
            "water": self.ink.water,
            "core_ink": float(getattr(self.ink, "core_ink", self.ink.ink_load)),
            "surface_ink": float(
                getattr(self.ink, "surface_ink", self.ink.ink_load)
            ),
            "excess_ink": float(getattr(self.ink, "excess_ink", 0.0)),
            "drip_risk": float(getattr(self.ink, "drip_risk", 0.0)),
            "drip_count": int(getattr(self.ink, "drip_count", 0)),
            "exemplar_occupancy": exemplar_occupancy,
            "exemplar_image_error": self._image_error,
            "unintended_ink_fraction": self.ink.unintended_fraction,
            "beauty_score": self.beauty_score,
            "beauty_components": self.beauty_components,
            "endpoint_metrics": self.endpoint_metrics,
            "endpoint_scores": tuple(self._endpoint_scores),
            "endpoint_triangle_count": int(self.endpoint_metrics["count"]),
            "endpoint_triangle_sum": float(self.endpoint_metrics["sum"]),
            "endpoint_triangle_mean": float(self.endpoint_metrics["mean"]),
            "endpoint_triangle_minimum": float(self.endpoint_metrics["minimum"]),
            "width_details": self._width_details.copy(),
            "glyph_metrics": self._glyph_metrics.copy(),
            "exemplar_mask_iou": 100.0 * float(self._glyph_metrics.get("iou", 0.0)),
            "motion_metrics": self._motion_metrics.copy(),
            "stroke_quality": completed_stroke_metrics,
            "balance": self._balance_metrics.copy(),
            "progress": self.progress,
            "is_success": is_success,
            "hard_limit": hard_limit,
            "termination_reason": (
                "success"
                if is_success
                else "hard_limit"
                if hard_limit
                else "tilt_unreachable"
                if tilt_unreachable
                else "collision"
                if collision
                else "running"
            ),
            "collision_types": collision_types,
            "reward_terms": reward_terms,
            "observation_version": self.observation_version,
        }
        info.update(
            {
                f"beauty_{name}": value
                for name, value in self._beauty_components.items()
            }
        )
        if self.render_mode == "human":
            self.render()
        return self._get_obs(), reward, terminated, truncated, info

    def render(self) -> np.ndarray | None:
        if self.render_mode == "rgb_array":
            if self._renderer is None:
                self._renderer = mujoco.Renderer(self.model, height=480, width=640)
            self._renderer.update_scene(self.data, camera="overview")
            self.ink.draw_mjv_scene(self._renderer.scene, clear=False)
            return self._renderer.render()
        if self.render_mode == "human":
            if self._viewer is None:
                from mujoco import viewer as mujoco_viewer

                self._viewer = mujoco_viewer.launch_passive(self.model, self.data)
            if self._viewer.is_running():
                self.ink.draw_mjv_scene(self._viewer.user_scn, clear=True)
                self._viewer.sync()
        return None

    def close(self) -> None:
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
