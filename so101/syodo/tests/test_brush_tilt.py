"""Brush-tilt hinge and the physical offset attachment from Fusion."""

from __future__ import annotations

import json
from pathlib import Path

import mujoco
import numpy as np
import pytest

from so101_calligraphy.config import (
    JOINT_LIMITS,
    EnvConfig,
    ModuleConfig,
    WritingLayoutConfig,
)
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.trajectory.types import Stroke, Trajectory


def _mount_axis(env: CalligraphyEnv) -> np.ndarray:
    return env.data.site_xmat[env._brush_mount_site_id].reshape(3, 3)[:, 0].copy()


def _body_id(env: CalligraphyEnv, name: str) -> int:
    body_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, name)
    assert body_id >= 0
    return body_id


def test_attachment_matches_fusion_axis_offset_and_tip_position() -> None:
    env = CalligraphyEnv("line", config=EnvConfig(reset_noise=0.0))
    try:
        mujoco.mj_resetData(env.model, env.data)
        env.data.qpos[env._qpos_indices] = np.asarray(
            [0.0, -1.25, 1.25, 1.35, 0.0, np.pi / 4.0]
        )
        mujoco.mj_forward(env.model, env.data)

        tilt_body = _body_id(env, "brush_tilt_link")
        pivot = env.data.xpos[tilt_body].copy()
        pivot_rotation = env.data.xmat[tilt_body].reshape(3, 3)
        tip_from_pivot = pivot_rotation.T @ (env.brush_position - pivot)
        mount_from_pivot = env.model.site_pos[env._brush_mount_site_id]
        brush_axis = tip_from_pivot - mount_from_pivot
        brush_axis /= np.linalg.norm(brush_axis)

        assert env.model.body_pos[tilt_body] == pytest.approx(
            np.asarray([0.020077, 0.0, 0.024350]), abs=1e-9
        )
        assert mount_from_pivot == pytest.approx(
            np.asarray([0.007764571, 0.0, 0.009022225]), abs=1e-9
        )
        assert tip_from_pivot == pytest.approx(
            np.asarray([0.007764571, 0.0, -0.028977775]), abs=2e-8
        )
        assert np.linalg.norm(tip_from_pivot) == pytest.approx(0.030, abs=2e-8)
        assert float(brush_axis @ np.asarray([0.0, 1.0, 0.0])) == pytest.approx(
            0.0, abs=1e-9
        )
        mount_axis_local = pivot_rotation.T @ _mount_axis(env)
        assert mount_axis_local == pytest.approx(brush_axis, abs=1e-9)
    finally:
        env.close()


def test_gripper_hinge_moves_offset_tip_on_30mm_radius() -> None:
    env = CalligraphyEnv("line", config=EnvConfig(reset_noise=0.0))
    try:
        mujoco.mj_resetData(env.model, env.data)
        env.data.qpos[env._qpos_indices] = np.asarray(
            [0.0, -1.25, 1.25, 1.35, 0.0, np.pi / 4.0]
        )
        mujoco.mj_forward(env.model, env.data)
        axis0 = _mount_axis(env)
        tip0 = env.data.site_xpos[env._brush_site_id].copy()

        env.data.qpos[env._qpos_indices[5]] = np.pi / 2.0
        mujoco.mj_forward(env.model, env.data)
        axis1 = _mount_axis(env)
        tip1 = env.data.site_xpos[env._brush_site_id].copy()

        delta = float(np.degrees(np.arccos(np.clip(axis0 @ axis1, -1.0, 1.0))))
        assert delta == pytest.approx(45.0, abs=1e-6)
        assert float(np.linalg.norm(tip1 - tip0)) == pytest.approx(
            2.0 * 0.030 * np.sin(np.pi / 8.0), abs=2e-8
        )
        assert JOINT_LIMITS[5, 0] == pytest.approx(-0.174533)
        assert JOINT_LIMITS[5, 1] == pytest.approx(1.74533)
    finally:
        env.close()


def test_entry_lean_is_steeper_than_sending() -> None:
    x = np.linspace(0.22, 0.27, 24)
    trajectory = Trajectory(
        (Stroke(np.column_stack((x, np.zeros_like(x))), stroke_type="㇐"),),
        source="test:exposed-horizontal",
    )
    env = CalligraphyEnv(
        trajectory=trajectory,
        config=EnvConfig(
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=3)
        phases = list(env.waypoints.brushwork_phases)
        entry = next(
            i
            for i, phase in enumerate(phases)
            if phase == "entry" and env.waypoints.pen_down[i]
        )
        sending = next(i for i, phase in enumerate(phases) if phase == "send")
        entry_axis = env._desired_brush_axis(entry)
        send_axis = env._desired_brush_axis(sending)
        # atan(lean): exposed entry 30° vs horizontal send 8°.
        assert abs(entry_axis[2]) < abs(send_axis[2])
        assert np.degrees(np.arctan(env.config.brush.entry_lean)) == pytest.approx(30.0)
        assert np.degrees(np.arctan(env.config.brush.desired_lean)) == pytest.approx(8.0)
        assert list(env.waypoints.phases).count("tilt_prepare") >= 12
    finally:
        env.close()


@pytest.mark.parametrize("angle_deg", [-15.0, 15.0, 30.0])
def test_six_axis_ik_compensates_tip_displacement_when_lean_changes(angle_deg) -> None:
    """Issue #13: actual FK axis changes, while XYZ stays at the same target."""
    env = CalligraphyEnv("line", config=EnvConfig(reset_noise=0.0, domain_randomization=False))
    try:
        mujoco.mj_resetData(env.model, env.data)
        start = np.array([0.0, -1.25, 1.25, 1.35, 0.0, np.pi / 4.0])
        env.data.qpos[env._qpos_indices] = start
        mujoco.mj_forward(env.model, env.data)
        tip = env.brush_position.copy()
        env.data.qpos[env._qpos_indices[-1]] += np.deg2rad(angle_deg)
        mujoco.mj_forward(env.model, env.data)
        desired_axis = env.brush_mount_axis.copy()
        assert np.linalg.norm(env.brush_position - tip) > 0.007

        env.data.qpos[env._qpos_indices] = start
        mujoco.mj_forward(env.model, env.data)
        for _ in range(220):
            delta = env._dls_delta(
                tip - env.brush_position, desired_axis,
                include_tilt=True, center_tilt=False,
            )
            env.data.qpos[env._qpos_indices] = np.clip(
                env.data.qpos[env._qpos_indices] + np.clip(delta, -0.08, 0.08),
                env._joint_limits[:, 0] + 0.01, env._joint_limits[:, 1] - 0.01,
            )
            mujoco.mj_forward(env.model, env.data)
        assert np.linalg.norm(env.brush_position - tip) < 0.0005
        assert env.brush_mount_axis @ desired_axis > np.cos(np.deg2rad(2.0))
        assert abs(env.data.qpos[env._qpos_indices[-1]] - start[-1]) > np.deg2rad(5.0)
    finally:
        env.close()


def test_legacy_policy_cannot_override_analytical_tilt_hinge() -> None:
    env = CalligraphyEnv(
        "line",
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env.reset(seed=3)
        before = float(env._joint_targets[-1])
        env.expert_action = lambda: np.zeros(6, dtype=np.float32)  # type: ignore[method-assign]
        env.step(np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 1.0], dtype=np.float32))
        assert env._joint_targets[-1] == pytest.approx(before)
    finally:
        env.close()


def test_a4_tip_mode_uses_recalibrated_brush_and_clearance() -> None:
    config = EnvConfig()

    assert config.paper.width == pytest.approx(0.210)
    assert config.paper.height == pytest.approx(0.297)
    assert config.writing_layout.two_by_two_size == pytest.approx(0.085)
    assert config.writing_layout.two_character_size == pytest.approx(0.110)
    legacy = WritingLayoutConfig.legacy_sixty_mm()
    assert legacy.two_by_two_size == legacy.two_character_size == pytest.approx(0.060)
    assert config.brush.bristle_length == pytest.approx(0.038)
    assert config.brush.nominal_force == pytest.approx(0.60)
    assert config.brush.pressure_slew_per_step == pytest.approx(0.12)
    assert config.brush.tip_pressure_floor == pytest.approx(0.01)
    assert config.brush.tuft_opening == pytest.approx(1.05)
    assert config.contact_pressure_gain == pytest.approx(0.014)
    assert config.harai_pressure_gain_scale == pytest.approx(1.6)
    assert config.hane_release_pressure_gain_scale == pytest.approx(1.0)
    assert config.contact_orientation_ik_weight == pytest.approx(0.12)
    assert config.contact_pressure_limit == pytest.approx(0.0045)
    assert config.stroke_junction_tolerance == pytest.approx(0.007)
    assert config.stroke_minimum_gap == pytest.approx(0.0015)
    assert config.stroke_clearance_floor == pytest.approx(0.45)
    assert config.max_pen_down_dwell == 0
    assert np.degrees(np.arctan(config.brush.finish_lean)) == pytest.approx(30.0)
    assert np.degrees(np.arctan(config.brush.corner_lean)) == pytest.approx(20.0)
    assert config.brush.tilt_prepare_steps == 12


def test_reset_ik_still_reaches_paper() -> None:
    env = CalligraphyEnv("line", config=EnvConfig(reset_noise=0.0))
    try:
        env.reset(seed=3)
        assert np.linalg.norm(env.target_position - env.brush_position) < 0.02
        axis_error = np.arccos(
            np.clip(env.brush_mount_axis @ env._desired_brush_axis(), -1.0, 1.0)
        )
        assert np.degrees(axis_error) <= 5.0
    finally:
        env.close()


def test_collision_line_search_uses_quarter_step_when_larger_targets_collide(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = CalligraphyEnv("line", config=EnvConfig(reset_noise=0.0))
    try:
        env.reset(seed=3, options={"layout_index": 0})
        current = env._joint_targets.copy()
        requested = current + 0.04
        monkeypatch.setattr(
            env,
            "_prospective_collision",
            lambda target: bool(np.max(np.abs(target - current)) > 0.011),
        )

        selected = env._collision_checked_target(requested, command_down=True)

        assert selected == pytest.approx(current + 0.25 * (requested - current))
        assert env._collision_line_search_stalls == 0
    finally:
        env.close()


def test_collision_line_search_bypasses_normal_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = CalligraphyEnv("line", config=EnvConfig(reset_noise=0.0))
    try:
        env.reset(seed=3, options={"layout_index": 2})
        requested = env._joint_targets + 0.01
        monkeypatch.setattr(
            env,
            "_prospective_collision",
            lambda _target: (_ for _ in ()).throw(AssertionError("must not run")),
        )

        assert env._collision_checked_target(
            requested, command_down=True
        ) == pytest.approx(requested)
    finally:
        env.close()


def test_collision_line_search_bypasses_center_110mm_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = CalligraphyEnv(
        "line",
        config=EnvConfig(
            reset_noise=0.0,
            writing_layout=WritingLayoutConfig.brushmark_center(),
        ),
    )
    try:
        env.reset(seed=3, options={"layout_index": 0})
        requested = env._joint_targets + 0.01
        env._collision_line_search_stalls = 20
        monkeypatch.setattr(
            env,
            "_prospective_collision",
            lambda _target: (_ for _ in ()).throw(AssertionError("must not run")),
        )

        assert env._collision_checked_target(
            requested, command_down=True
        ) == pytest.approx(requested)
        assert env._collision_line_search_stalls == 0
        assert not env._collision_recovery_active(command_down=True)
    finally:
        env.close()


def test_known_gate3_collision_fixture_activates_recovery_after_twenty_stalls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = json.loads(
        (Path(__file__).parent / "fixtures" / "gate3_collision_cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(fixture) == 14
    assert {row["layout_index"] for row in fixture} <= {0, 1}

    env = CalligraphyEnv("line", config=EnvConfig(reset_noise=0.0))
    try:
        env.reset(seed=3, options={"layout_index": fixture[0]["layout_index"]})
        current = env._joint_targets.copy()
        monkeypatch.setattr(env, "_prospective_collision", lambda _target: True)
        for _ in range(20):
            assert env._collision_checked_target(
                current + 0.01, command_down=True
            ) == pytest.approx(current)

        assert env._collision_recovery_active(command_down=True)
    finally:
        env.close()


def test_stalled_contact_recovery_uses_position_priority_dls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = CalligraphyEnv("line", config=EnvConfig(reset_noise=0.0))
    try:
        env.reset(seed=3, options={"layout_index": 0})
        index = next(i for i, down in enumerate(env.waypoints.pen_down) if bool(down))
        env._target_index = index
        env._target_dwell = 160
        calls: list[dict[str, object]] = []

        def capture(*_args: object, **kwargs: object) -> np.ndarray:
            calls.append(kwargs)
            return np.zeros(6, dtype=np.float64)

        monkeypatch.setattr(env, "_dls_delta", capture)
        env.expert_action()

        assert calls
        assert calls[-1].get("position_priority") is True
    finally:
        env.close()


def test_expert_only_completes_inkstone_and_line_without_dwell_skip() -> None:
    trajectory = Trajectory(
        strokes=(
            Stroke(
                np.column_stack((np.linspace(0.200, 0.250, 16), np.zeros(16))),
                "line",
            ),
        ),
        source="test:physical-attachment-line",
    )
    env = CalligraphyEnv(
        "physical-attachment-line",
        trajectories=[trajectory],
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig(
                brush_physics="professional",
                ink_model="professional",
                brushwork="professional",
                inkstone=True,
            ),
        ),
    )
    try:
        observation, _ = env.reset(seed=3)
        info: dict[str, object] = {}
        for _ in range(12_000):
            observation, _, terminated, truncated, info = env.step(
                np.zeros(6, dtype=np.float32)
            )
            if terminated or truncated:
                break
        assert info["is_success"] is True
        assert info["progress"] == pytest.approx(1.0)
        assert info["collision_types"] == []
        records = [record for record in env._stroke_records if record["width"]]
        assert records
        for record in records:
            assert len(record["width"]) == len(record["target_width"])
            assert len(record["pressure"]) == len(record["target_pressure"])
            assert len(record["width"]) == len(record["target_index"])
            assert np.isfinite(record["target_width"]).all()
            assert np.isfinite(record["target_pressure"]).all()
    finally:
        env.close()
