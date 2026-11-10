from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from so101_calligraphy.brushwork import ProfessionalBrushworkPlanner
from so101_calligraphy.config import (
    BrushConfig,
    EnvConfig,
    JOINT_LIMITS,
    ModuleConfig,
    PaperConfig,
    WritingLayoutConfig,
)
from so101_calligraphy.envs.calligraphy_env import (
    CalligraphyEnv,
    _filter_contact_pressure,
    _interpolate_segment_progress,
    _next_contact_pressure_offset,
    _touchdown_error_scale,
)
from so101_calligraphy.ink import tip_pressure_from_width, tip_width_from_pressure
from so101_calligraphy.training.professional import professional_config
from so101_calligraphy.trajectory.layout import writing_frames
from so101_calligraphy.trajectory.types import Stroke, Trajectory


def _horizontal() -> Trajectory:
    x = np.linspace(0.22, 0.27, 24)
    return Trajectory(
        (Stroke(np.column_stack((x, np.zeros_like(x))), stroke_type="㇐"),),
        source="test:a4-tip-horizontal",
    )


def _cross() -> Trajectory:
    horizontal = np.column_stack((np.linspace(0.22, 0.27, 24), np.zeros(24)))
    vertical = np.column_stack((np.full(24, 0.245), np.linspace(-0.025, 0.025, 24)))
    return Trajectory(
        (
            Stroke(horizontal, stroke_type="㇐"),
            Stroke(vertical, stroke_type="㇑"),
        ),
        source="test:a4-tip-cross",
    )


def test_fixed_a4_frame_centres_and_sizes() -> None:
    config = EnvConfig()
    frames = writing_frames(config.paper, config.writing_layout)

    assert len(frames) == 6
    expected = (
        (0.245, 0.06675, 0.085),
        (0.245, -0.06675, 0.085),
        (0.155, 0.06675, 0.085),
        (0.155, -0.06675, 0.085),
        (0.200, 0.06675, 0.110),
        (0.200, -0.06675, 0.110),
    )
    for (center, size), values in zip(frames, expected, strict=True):
        assert center == pytest.approx(values[:2])
        assert size == pytest.approx((values[2], values[2]))


def test_brushmark_center_frame_matches_historical_paper() -> None:
    frames = writing_frames(
        PaperConfig(), WritingLayoutConfig.brushmark_center()
    )

    assert len(frames) == 1
    center, size = frames[0]
    assert center == pytest.approx((0.200, 0.0))
    assert size == pytest.approx((0.110, 0.110))


def test_professional_tip_calibration_tracks_layout_and_stroke_morphology() -> None:
    config = professional_config("all")
    env = CalligraphyEnv(trajectory=_cross(), config=config)
    try:
        env.reset(seed=4, options={"layout_index": 0})
        assert np.degrees(np.arctan(env._effective_entry_lean())) == pytest.approx(30.0)
        assert env._effective_nominal_force() == pytest.approx(1.20)
        assert env._effective_pressure_control() == pytest.approx(
            (0.348, 0.0234, 0.0045)
        )

        env.reset(seed=4, options={"layout_index": 4})
        assert np.degrees(np.arctan(env._effective_entry_lean())) == pytest.approx(25.0)
        assert env._effective_nominal_force() == pytest.approx(0.80)
        assert env._effective_pressure_control() == pytest.approx(
            (0.348, 0.0226, 0.0045)
        )
    finally:
        env.close()

    horizontal = CalligraphyEnv(trajectory=_horizontal(), config=config)
    try:
        horizontal.reset(seed=4, options={"layout_index": 4})
        assert horizontal._effective_pressure_control() == pytest.approx(
            (0.27, 0.016, 0.0045)
        )
        assert horizontal.config.contact_tilt_max_speed == pytest.approx(1.1)
    finally:
        horizontal.close()


def test_professional_config_forwards_pressure_calibration_options() -> None:
    config = professional_config(
        "all",
        pressure_calibration_path=Path("candidate.json"),
        require_pressure_calibration=True,
        residual_pressure_integral_scale=0.25,
        pressure_calibration_clip_rate_limit=0.05,
    )

    assert config.pressure_calibration_path == "candidate.json"
    assert config.require_pressure_calibration
    assert config.residual_pressure_integral_scale == pytest.approx(0.25)
    assert config.pressure_calibration_clip_rate_limit == pytest.approx(0.05)


def test_tip_pressure_width_curve_is_reversible() -> None:
    brush = EnvConfig().brush
    pressure = np.asarray((0.0, 0.10, 0.20, 0.30, 0.45, 1.0))
    width = np.asarray((0.0018, 0.0025, 0.0040, 0.0062, 0.0090, 0.0130))

    assert tip_width_from_pressure(pressure, brush) == pytest.approx(width)
    assert tip_pressure_from_width(width, brush) == pytest.approx(pressure)


def test_professional_pressure_stays_in_tip_only_range() -> None:
    progress = np.linspace(0.0, 0.08, 32)
    profile = ProfessionalBrushworkPlanner().plan(
        Stroke(np.column_stack((progress, np.zeros_like(progress))), stroke_type="㇐"),
        EnvConfig().brush,
    )

    sending = profile.pressure[
        (profile.progress >= 0.30) & (profile.progress <= 0.70)
    ]
    assert float(np.median(sending)) == pytest.approx(0.20, abs=0.03)
    assert float(np.max(profile.pressure)) <= 0.45


def test_contact_angle_progress_interpolates_within_sparse_waypoint_segment() -> None:
    assert _interpolate_segment_progress(
        np.asarray([0.0, 0.0]),
        np.asarray([0.010, 0.0]),
        np.asarray([0.003, 0.0]),
        0.0,
        0.20,
    ) == pytest.approx(0.06)


def test_contact_dls_keeps_position_primary_over_tilt() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        error = np.asarray((0.006, -0.004, 0.002))
        axis = np.asarray((0.45, 0.0, -0.89302855))
        axis /= np.linalg.norm(axis)
        prioritised = env._dls_delta(
            error,
            axis,
            include_tilt=True,
            directional_axis=True,
            position_priority=True,
        )
        jacobian = np.zeros((3, env.model.nv))
        rotation = np.zeros((3, env.model.nv))
        import mujoco

        mujoco.mj_jacSite(
            env.model,
            env.data,
            jacobian,
            rotation,
            env._brush_site_id,
        )
        position = jacobian[:, env._qvel_indices]
        damping = 2e-4
        six_dof = (
            position.T
            @ np.linalg.solve(
                position @ position.T + damping * np.eye(3), np.eye(3)
            )
            @ error
        )
        assert position @ prioritised == pytest.approx(error, abs=5e-4)
        assert position @ prioritised == pytest.approx(position @ six_dof, abs=5e-4)
    finally:
        env.close()


def test_legacy_compensation_reaches_brushmark_center_frame() -> None:
    config = professional_config("all")
    config = replace(
        config,
        legacy_attachment_compensation=True,
        reset_noise=0.0,
        writing_layout=WritingLayoutConfig.brushmark_center(),
    )
    env = CalligraphyEnv(trajectory=_horizontal(), config=config)
    try:
        env.reset(seed=4, options={"layout_index": 0})
        assert env._layout_index == 0
        assert env.controlled_brush_position == pytest.approx(env.brush_position)
        assert env.data.qpos[env._qpos_indices[-1]] == pytest.approx(0.0)
    finally:
        env.close()


def test_legacy_attachment_compensation_uses_actual_tip_and_five_axes() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            legacy_attachment_compensation=True,
        ),
    )
    try:
        observation, _ = env.reset(seed=4)

        assert env.controlled_brush_position == pytest.approx(env.brush_position)
        assert observation[12:15] == pytest.approx(env.controlled_brush_position)
        assert env.data.qpos[env._qpos_indices[-1]] == pytest.approx(0.0)
        phases = set(env.waypoints.phases)
        assert "tilted_approach" not in phases
        assert "tilt_prepare" not in phases
        assert env._dls_delta(
            np.asarray((0.004, -0.003, 0.002)), include_tilt=True
        ).shape == (5,)
        lower = next(
            index
            for index, phase in enumerate(env.waypoints.phases)
            if phase == "lower"
        )
        env._target_index = lower
        assert env._target_reached(env.target_position)
    finally:
        env.close()


def test_legacy_compensation_keeps_contact_tip_on_the_stroke() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            legacy_attachment_compensation=True,
        ),
    )
    try:
        env.reset(seed=4)
        errors: list[float] = []
        for _ in range(12_000):
            _, _, terminated, truncated, info = env.step(np.zeros(6, dtype=np.float32))
            if info.get("pen_down"):
                errors.append(
                    float(np.linalg.norm(env.target_position[:2] - env.brush_position[:2]))
                )
            if terminated or truncated:
                break
        assert info["is_success"]
        assert errors
        assert np.percentile(errors, 90) < 0.016
    finally:
        env.close()


def test_legacy_attachment_compensation_ignores_policy_tilt_output() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            legacy_attachment_compensation=True,
        ),
    )
    try:
        env.reset(seed=4)
        action = np.zeros(6, dtype=np.float32)
        action[-1] = 1.0
        env.step(action)

        assert env._joint_targets[-1] == pytest.approx(0.0)
    finally:
        env.close()


def test_contact_expert_does_not_slow_xy_for_tilt_lag() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            contact_pressure_gain=0.0,
            large_frame_contact_pressure_gain=0.0,
            horizontal_contact_pressure_gain=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        env.waypoints.positions[env._target_index] = env.brush_position + np.asarray(
            [0.010, 0.0, 0.0]
        )
        env._contact_force = 1.0
        desired_axis = np.asarray([0.5, 0.0, -np.sqrt(0.75)])
        env._desired_brush_axis = lambda index=None, **kwargs: desired_axis  # type: ignore[method-assign]
        errors: list[np.ndarray] = []

        def record(
            error: np.ndarray,
            desired_axis: np.ndarray | None = None,
            **kwargs: object,
        ) -> np.ndarray:
            errors.append(error.copy())
            return np.zeros(6, dtype=np.float64)

        env._dls_delta = record  # type: ignore[method-assign]
        env.expert_action()

        assert errors[0][0] == pytest.approx(0.010)
    finally:
        env.close()


def test_entry_lean_uses_send_angle_until_tip_is_near_target() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            index
            for index, down in enumerate(env.waypoints.pen_down)
            if down and env.waypoints.stroke_progress[index] <= 0.02
        )
        send_deg = float(np.degrees(np.arctan(env.config.brush.desired_lean)))
        env.waypoints.positions[env._target_index] = env.brush_position + np.asarray(
            [0.030, 0.0, 0.0]
        )
        far = env._desired_brush_axis(follow_tip=True)
        far_deg = float(np.degrees(np.arccos(np.clip(-far[2], -1.0, 1.0))))
        env.waypoints.positions[env._target_index] = env.brush_position.copy()
        near = env._desired_brush_axis(follow_tip=True)
        near_deg = float(np.degrees(np.arccos(np.clip(-near[2], -1.0, 1.0))))
        assert far_deg == pytest.approx(send_deg, abs=2.0)
        assert near_deg > far_deg + 8.0
    finally:
        env.close()


def test_fixed_contact_lean_holds_one_axis_through_the_stroke() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            brush=BrushConfig(fixed_contact_lean=1.0),
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4, options={"layout_index": 1})
        indices = [
            next(
                index
                for index, phase in enumerate(env.waypoints.brushwork_phases)
                if phase == wanted and env.waypoints.pen_down[index]
            )
            for wanted in ("entry", "send", "finish")
        ]
        axes = [env._desired_brush_axis(index) for index in indices]
        for axis in axes[1:]:
            assert axis == pytest.approx(axes[0])
        assert np.degrees(np.arccos(-axes[0][2])) == pytest.approx(45.0)
    finally:
        env.close()


def test_fixed_contact_lean_uses_mild_lean_in_far_upper_frame() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            brush=BrushConfig(fixed_contact_lean=1.0),
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4, options={"layout_index": 0})
        index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        axis = env._desired_brush_axis(index)
        assert env._uses_fixed_contact_lean(index)
        assert np.degrees(np.arccos(-axis[2])) == pytest.approx(30.0)
    finally:
        env.close()


def test_fixed_contact_lean_leaves_joined_vertical_stroke_dynamic() -> None:
    env = CalligraphyEnv(
        trajectory=_cross(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            brush=BrushConfig(fixed_contact_lean=1.0),
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send"
            and env.waypoints.pen_down[index]
            and env.waypoints.stroke_indices[index] == 1
        )
        axis = env._desired_brush_axis(index)
        angle = float(np.degrees(np.arccos(np.clip(-axis[2], -1.0, 1.0))))

        assert not env._uses_fixed_contact_lean(index)
        assert angle == pytest.approx(
            np.degrees(np.arctan(env.config.brush.desired_lean)), abs=1.0
        )
    finally:
        env.close()


def test_fixed_contact_lean_leaves_complex_glyph_dynamic() -> None:
    x = np.linspace(0.22, 0.27, 24)
    trajectory = Trajectory(
        tuple(
            Stroke(
                np.column_stack((x, np.full_like(x, offset))),
                stroke_type="㇐",
            )
            for offset in (-0.03, -0.01, 0.01, 0.03)
        ),
        source="test:a4-tip-complex-horizontal",
    )
    env = CalligraphyEnv(
        trajectory=trajectory,
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            brush=BrushConfig(fixed_contact_lean=1.0),
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        assert not env._uses_fixed_contact_lean(index)
    finally:
        env.close()


def test_fixed_contact_lean_ignores_policy_tilt_residual() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            brush=BrushConfig(fixed_contact_lean=1.0),
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4, options={"layout_index": 1})
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        before = float(env._joint_targets[-1])
        env.expert_action = lambda: np.zeros(6, dtype=np.float32)  # type: ignore[method-assign]
        env.step(np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 1.0], dtype=np.float32))

        assert env._joint_targets[-1] == pytest.approx(before)
    finally:
        env.close()


def test_fixed_contact_lean_uses_xyz_only_after_touchdown() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            brush=BrushConfig(fixed_contact_lean=1.0),
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4, options={"layout_index": 1})
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        calls: list[tuple[np.ndarray | None, bool]] = []

        def record_dls(
            error: np.ndarray,
            desired_axis: np.ndarray | None = None,
            *,
            include_tilt: bool = False,
            **_: object,
        ) -> np.ndarray:
            calls.append((desired_axis, include_tilt))
            return np.zeros(6 if include_tilt else 5, dtype=np.float64)

        env._dls_delta = record_dls  # type: ignore[method-assign]
        action = env.expert_action()

        assert calls == [(None, False)]
        assert action[-1] == pytest.approx(0.0)
    finally:
        env.close()


def test_fixed_contact_lean_uses_tilt_only_for_stalled_xyz_recovery() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            brush=BrushConfig(fixed_contact_lean=1.0),
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4, options={"layout_index": 1})
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        env.waypoints.positions[env._target_index] = env.brush_position + np.asarray(
            [0.010, 0.0, 0.0]
        )
        env._target_dwell = 160
        env._contact_force = 1.0
        calls: list[bool] = []

        def record_dls(
            error: np.ndarray,
            desired_axis: np.ndarray | None = None,
            *,
            include_tilt: bool = False,
            **_: object,
        ) -> np.ndarray:
            calls.append(include_tilt)
            delta = np.zeros(6 if include_tilt else 5, dtype=np.float64)
            if include_tilt:
                delta[-1] = 0.01
            return delta

        env._dls_delta = record_dls  # type: ignore[method-assign]
        action = env.expert_action()

        assert calls == [False, True]
        assert action[-1] == pytest.approx(0.01 / env.config.action_delta)
    finally:
        env.close()


def test_pressure_loop_tracks_the_same_interpolated_target_as_ink() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="legacy"),
        ),
    )
    try:
        env.reset(seed=4)
        index = next(
            i for i, down in enumerate(env.waypoints.pen_down) if bool(down)
        )
        metadata = env._target_metadata(index)
        metadata.update(pressure=0.0, stroke_progress=0.5, technique="tome")
        env._target_metadata = lambda _: metadata  # type: ignore[method-assign]
        env._pressure = 0.5
        env._contact_force = 1.0
        env._contact_pressure_offset = 0.0

        env._update_contact_pressure_control(index)

        assert env._contact_pressure_offset == pytest.approx(
            _next_contact_pressure_offset(
                0.0,
                0.5,
                env.config.contact_pressure_gain,
                env.config.contact_pressure_limit,
            )
        )
    finally:
        env.close()


def test_pressure_loop_discards_lift_windup_when_contact_is_required() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="legacy"),
        ),
    )
    try:
        env.reset(seed=4)
        index = next(i for i, down in enumerate(env.waypoints.pen_down) if bool(down))
        metadata = env._target_metadata(index)
        metadata.update(pressure=0.2, brushwork_phase="finish", technique="tome")
        env._target_metadata = lambda _: metadata  # type: ignore[method-assign]
        env._contact_force = 0.0
        env._pressure = 0.0
        env._contact_pressure_offset = 0.003
        stroke_index = int(env.waypoints.stroke_indices[index])
        env._stroke_records[stroke_index]["pressure"].append(0.2)

        env._update_contact_pressure_control(index)

        assert env._target_requires_contact(index)
        assert env._contact_pressure_offset == pytest.approx(
            _next_contact_pressure_offset(
                0.0,
                -0.2 * 0.10,
                env.config.contact_pressure_gain,
                env.config.contact_pressure_limit,
            )
        )
    finally:
        env.close()


def test_pressure_loop_does_not_force_contact_during_harai_release() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="legacy"),
        ),
    )
    try:
        env.reset(seed=4)
        index = next(i for i, down in enumerate(env.waypoints.pen_down) if bool(down))
        metadata = env._target_metadata(index)
        metadata.update(pressure=0.2, brushwork_phase="finish", technique="harai")
        env._target_metadata = lambda _: metadata  # type: ignore[method-assign]
        env._contact_force = 0.0
        env._pressure = 0.0
        env._contact_pressure_offset = 0.003
        stroke_index = int(env.waypoints.stroke_indices[index])
        env._stroke_records[stroke_index]["pressure"].append(0.2)

        env._update_contact_pressure_control(index)

        assert not env._target_requires_contact(index)
        assert 0.0 < env._contact_pressure_offset < 0.003
    finally:
        env.close()


def test_long_tuft_filters_force_spikes_and_releases_immediately() -> None:
    pressure = _filter_contact_pressure(0.0, 1.0, contact=True)
    assert pressure == pytest.approx(0.12)
    assert _filter_contact_pressure(
        0.0, 1.0, contact=True, maximum_change=0.08
    ) == pytest.approx(0.08)
    assert _filter_contact_pressure(
        0.0, 1.0, contact=True, maximum_change=0.12, response=0.5
    ) == pytest.approx(0.06)
    assert _filter_contact_pressure(
        0.50, 0.0, contact=True, maximum_change=0.12, response=0.5
    ) == pytest.approx(0.38)
    for _ in range(8):
        pressure = _filter_contact_pressure(pressure, 1.0, contact=True)
    assert pressure == pytest.approx(1.0)
    assert _filter_contact_pressure(pressure, 0.0, contact=False) == 0.0


def test_soft_touchdown_restores_full_descent_authority() -> None:
    assert _touchdown_error_scale(0) == pytest.approx(0.05)
    assert _touchdown_error_scale(20) == pytest.approx(0.525)
    assert _touchdown_error_scale(40) == 1.0
    assert _touchdown_error_scale(400) == 1.0


def test_model_uses_fixed_a4_and_reachable_150mm_base() -> None:
    config = EnvConfig(reset_noise=0.0)
    env = CalligraphyEnv(config=config)
    try:
        paper = env.model.geom_pos[env._paper_geom_id]
        assert paper[:2] == pytest.approx((0.200, 0.0))
        assert paper[2] + env.model.geom_size[env._paper_geom_id, 2] == pytest.approx(
            config.paper.surface_z
        )
        assert env.model.body_pos[env._base_body_id] == pytest.approx(
            (0.030, 0.0, 0.150)
        )
    finally:
        env.close()


def test_multistart_reset_ik_meets_position_orientation_and_margin() -> None:
    env = CalligraphyEnv(config=EnvConfig(reset_noise=0.0))
    try:
        env.reset(seed=4)
        qpos = env.data.qpos[env._qpos_indices]
        margin = np.min(
            np.minimum(qpos - JOINT_LIMITS[:, 0], JOINT_LIMITS[:, 1] - qpos)
        )
        axis_error = np.degrees(
            np.arccos(
                np.clip(env.brush_mount_axis @ env._desired_brush_axis(), -1.0, 1.0)
            )
        )
        collision, _ = env._collision_state()
        assert np.linalg.norm(env.target_position - env.brush_position) <= 0.003
        assert axis_error <= 5.0
        assert margin >= np.deg2rad(5.0) - 1e-8
        assert not collision
    finally:
        env.close()


def test_multistart_ik_reaches_all_a4_entry_send_and_finish_poses() -> None:
    config = EnvConfig(
        ik_assist=True,
        reset_noise=0.0,
        modules=ModuleConfig(brushwork="professional"),
    )
    for center, size in writing_frames(config.paper, config.writing_layout):
        x = np.linspace(center[0] - 0.4 * size[0], center[0] + 0.4 * size[0], 24)
        y = np.full_like(x, center[1])
        trajectory = Trajectory(
            (Stroke(np.column_stack((x, y)), stroke_type="㇐"),),
            source="test:a4-frame-horizontal",
        )
        env = CalligraphyEnv(trajectory=trajectory, config=config)
        try:
            env.reset(seed=4)
            assert env._exposed_horizontal.tolist() == [[True, True]]
            for brush_phase in ("entry", "send", "finish"):
                target = next(
                    index
                    for index, phase in enumerate(env.waypoints.brushwork_phases)
                    if env.waypoints.pen_down[index] and phase == brush_phase
                )
                env._target_index = target
                env._solve_position_ik(
                    env.target_position,
                    directional_axis=False,
                    orientation_tolerance=config.tilt_residual_limit,
                )
                qpos = env.data.qpos[env._qpos_indices]
                margin = np.min(
                    np.minimum(qpos - JOINT_LIMITS[:, 0], JOINT_LIMITS[:, 1] - qpos)
                )
                desired = env._desired_brush_axis()
                axis_error = abs(
                    np.arccos(np.clip(-env.brush_mount_axis[2], -1.0, 1.0))
                    - np.arccos(np.clip(-desired[2], -1.0, 1.0))
                )
                collision, _ = env._collision_state()
                assert np.linalg.norm(env.target_position - env.brush_position) <= 0.003
                assert axis_error <= config.tilt_residual_limit
                assert margin >= np.deg2rad(5.0) - 1e-8
                assert not collision
        finally:
            env.close()


def test_six_dimensional_policy_keeps_bounded_contact_tilt_residual() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            observation_version=3,
            contact_tilt_max_speed=0.4,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        observation, _ = env.reset(seed=4)
        assert observation.shape == (371,)
        assert env.action_space.shape == (6,)
        finish = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "finish" and env.waypoints.pen_down[index]
        )
        env._target_index = finish
        env._set_target_marker()
        before = float(env._joint_targets[-1])
        env.expert_action = lambda: np.zeros(6, dtype=np.float32)  # type: ignore[method-assign]
        env.step(np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 1.0], dtype=np.float32))
        change = float(env._joint_targets[-1] - before)
        assert change > 0.0
        assert change <= env.config.tilt_residual_limit
        control_dt = env.model.opt.timestep * env.config.frame_skip
        assert change <= env.config.contact_tilt_max_speed * control_dt
    finally:
        env.close()


def test_contact_tilt_speed_limit_applies_to_mixed_glyph() -> None:
    env = CalligraphyEnv(
        trajectory=_cross(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            observation_version=3,
            contact_tilt_max_speed=0.4,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        before = float(env._joint_targets[-1])
        env.expert_action = lambda: np.zeros(6, dtype=np.float32)  # type: ignore[method-assign]
        env.step(np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 1.0], dtype=np.float32))

        control_dt = env.model.opt.timestep * env.config.frame_skip
        change = float(env._joint_targets[-1] - before)
        assert 0.0 < change <= env.config.contact_tilt_max_speed * control_dt + 1e-12
    finally:
        env.close()


def test_lost_contact_on_send_still_avoids_airborne_multistart() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        env._target_dwell = 80
        env._contact_force = 0.0

        def fail_if_called(_: int) -> np.ndarray:
            raise AssertionError("airborne multi-start must not run on paper")

        env._tilt_prepare_goal = fail_if_called  # type: ignore[method-assign]
        assert env.expert_action().shape == (6,)
    finally:
        env.close()


def test_contact_dwell_keeps_working_pressure_corrected_dls() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        env.waypoints.positions[env._target_index] = env.brush_position
        env._target_dwell = 160
        env._contact_force = 1.0

        def fail_if_called(_: int) -> np.ndarray:
            raise AssertionError("airborne multi-start must not run on paper")

        env._tilt_prepare_goal = fail_if_called  # type: ignore[method-assign]
        desired_axes: list[np.ndarray | None] = []

        def record(
            error: np.ndarray,
            desired_axis: np.ndarray | None = None,
            **kwargs: object,
        ) -> np.ndarray:
            desired_axes.append(desired_axis)
            return np.full(6, 1e-4, dtype=np.float64)

        env._dls_delta = record  # type: ignore[method-assign]
        assert env.expert_action().shape == (6,)
        assert len(desired_axes) == 1
        assert desired_axes[0] is not None
    finally:
        env.close()


def test_contact_dwell_holds_lateral_position_inside_tolerance() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            target_tolerance_xy=0.0015,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        env.waypoints.positions[env._target_index] = (
            env.controlled_brush_position + np.asarray([0.001, 0.0, 0.0])
        )
        env._target_dwell = 80
        env._contact_force = 1.0
        calls: list[np.ndarray] = []

        def record(
            error: np.ndarray,
            desired_axis: np.ndarray | None = None,
            **kwargs: object,
        ) -> np.ndarray:
            del desired_axis, kwargs
            calls.append(error.copy())
            return np.zeros(6, dtype=np.float64)

        env._dls_delta = record  # type: ignore[method-assign]
        env.expert_action()

        assert len(calls) == 1
        assert calls[0][0] == pytest.approx(0.0)
    finally:
        env.close()


def test_contact_dwell_releases_orientation_outside_cartesian_tolerance() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        env.waypoints.positions[env._target_index] = env.brush_position + np.asarray(
            [0.010, 0.0, 0.0]
        )
        env._target_dwell = 160
        env._contact_force = 1.0
        calls: list[tuple[np.ndarray, np.ndarray | None]] = []

        def stalled_then_recover(
            error: np.ndarray,
            desired_axis: np.ndarray | None = None,
            **kwargs: object,
        ) -> np.ndarray:
            calls.append((error.copy(), desired_axis))
            delta = np.zeros(6, dtype=np.float64)
            if desired_axis is not None:
                # Null-space tilt motion alone does not advance the Cartesian
                # waypoint and must not hide a stalled five-axis arm solve.
                delta[-1] = 0.1
            else:
                delta[0] = 0.01
            return delta

        env._dls_delta = stalled_then_recover  # type: ignore[method-assign]
        action = env.expert_action()
        assert action.shape == (6,)
        assert len(calls) == 2
        assert calls[0][1] is not None
        assert calls[1][1] is None
        assert action[0] == pytest.approx(0.01 / env.config.action_delta)
    finally:
        env.close()


def test_lost_contact_inside_cartesian_tolerance_recovers_pressure_depth() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "send" and env.waypoints.pen_down[index]
        )
        env.waypoints.positions[env._target_index] = env.brush_position
        env._target_dwell = 160
        env._contact_force = 0.0
        env._contact_pressure_offset = -0.004
        calls: list[tuple[np.ndarray, np.ndarray | None]] = []

        def record(
            error: np.ndarray,
            desired_axis: np.ndarray | None = None,
            **kwargs: object,
        ) -> np.ndarray:
            calls.append((error.copy(), desired_axis))
            return np.zeros(6, dtype=np.float64)

        env._dls_delta = record  # type: ignore[method-assign]
        env.expert_action()

        assert len(calls) == 2
        assert calls[0][1] is not None
        assert calls[1][1] is None
        assert calls[1][0][2] == pytest.approx(-0.004)
    finally:
        env.close()


def test_air_gap_at_finish_does_not_restart_entry_multistart() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            index
            for index, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "finish" and env.waypoints.pen_down[index]
        )
        env._target_dwell = 80
        env._contact_force = 0.0

        def fail_if_called(_: int) -> np.ndarray:
            raise AssertionError("entry multi-start must not restart at finish")

        env._tilt_prepare_goal = fail_if_called  # type: ignore[method-assign]
        assert env.expert_action().shape == (6,)
    finally:
        env.close()


def test_expert_controls_full_attachment_axis_at_exposed_endpoints() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        original = env._dls_delta
        directional: list[bool] = []

        def record(*args: object, **kwargs: object) -> np.ndarray:
            directional.append(bool(kwargs["directional_axis"]))
            return original(*args, **kwargs)

        env._dls_delta = record  # type: ignore[method-assign]
        for brushwork_phase in ("entry", "finish"):
            env._target_index = next(
                i
                for i, phase in enumerate(env.waypoints.brushwork_phases)
                if phase == brushwork_phase and env.waypoints.pen_down[i]
            )
            env._contact_force = 1.0
            env.expert_action()

        assert directional == [True, True]
    finally:
        env.close()


def test_exposed_finish_is_not_accepted_six_millimetres_early() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            i
            for i, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "finish" and env.waypoints.pen_down[i]
        )
        six_millimetres_early = env.target_position.copy()
        six_millimetres_early[0] -= 0.006

        assert not env._target_reached(six_millimetres_early)

        env._target_index = max(
            i
            for i, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "finish" and env.waypoints.pen_down[i]
        )
        env._contact_force = 0.0
        assert not env._target_reached(env.target_position)
    finally:
        env.close()


def test_finish_reach_accounts_for_upward_pressure_correction() -> None:
    points = np.column_stack(
        (np.linspace(0.20, 0.25, 24), np.linspace(0.02, -0.02, 24))
    )
    env = CalligraphyEnv(
        trajectory=Trajectory((Stroke(points, stroke_type="㇒"),), source="test:harai"),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = max(
            i
            for i, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "finish" and env.waypoints.pen_down[i]
        )
        env._contact_pressure_offset = env.config.contact_pressure_limit
        pressure_adjusted = env.target_position.copy()
        pressure_adjusted[2] += env._contact_pressure_offset

        assert env._target_reached(pressure_adjusted)
    finally:
        env.close()


def test_entry_stall_accounts_for_signed_pressure_correction() -> None:
    env = CalligraphyEnv(
        trajectory=_horizontal(),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = next(
            i
            for i, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "entry" and env.waypoints.pen_down[i]
        )
        env._contact_pressure_offset = -env.config.contact_pressure_limit
        pressure_adjusted = env.target_position.copy()
        pressure_adjusted[2] += env._contact_pressure_offset
        env._contact_force = 1.0

        assert not env._target_reached(pressure_adjusted)

        env._target_dwell = 40
        assert env._target_reached(pressure_adjusted)

        env._contact_force = 0.0
        assert not env._target_reached(pressure_adjusted)
    finally:
        env.close()


def test_finish_reach_advances_when_unload_is_saturated() -> None:
    points = np.column_stack(
        (np.linspace(0.20, 0.28, 24), np.zeros(24))
    )
    env = CalligraphyEnv(
        trajectory=Trajectory((Stroke(points, stroke_type="㇐", technique="tome"),), source="test:heng"),
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=4)
        env._target_index = max(
            i
            for i, phase in enumerate(env.waypoints.brushwork_phases)
            if phase == "finish" and env.waypoints.pen_down[i]
        )
        env._contact_pressure_offset = env.config.contact_pressure_limit
        env._pressure = float(env.waypoints.target_pressure[env._target_index]) + 0.20
        env._contact_force = 1.0
        # Unreachable unload height must not freeze the waypoint forever.
        assert env._pressure_unload_saturated(env._target_index)
        assert env._target_reached(env.target_position)
    finally:
        env.close()


def test_upright_cli_zeros_large_frame_and_airborne_lean() -> None:
    text = Path(__file__).resolve().parents[1].joinpath(
        "scripts/diagnose_stroke_merge.py"
    ).read_text(encoding="utf-8")
    assert "large_frame_entry_lean=0.0" in text
    assert "airborne_lean=0.0" in text
