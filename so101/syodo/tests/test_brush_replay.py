"""Geometry and state-history checks for the offline hardware brush replay."""

from __future__ import annotations

from dataclasses import replace

import mujoco
import numpy as np
import pytest

from so101_calligraphy.brush_physics import brush_model_xml
from so101_calligraphy.brush_replay import ReplayParameters, replay_brush
from so101_calligraphy.config import EnvConfig, HardwareCalibrationConfig
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv


def _hardware_config() -> EnvConfig:
    return EnvConfig(
        hardware=HardwareCalibrationConfig(
            brush_tip_length_scale=12.0 / 3.8,
            brush_tuft_length_m=0.04,
        ),
        domain_randomization=False,
        reset_noise=0.0,
    )


def _rest_path(config: EnvConfig, pan: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    env = CalligraphyEnv("line", config=config)
    try:
        env.reset(seed=0)
        initial = env.data.qpos[env._qpos_indices].copy()
        qpos, expected = [], []
        for value in pan:
            q = initial.copy()
            q[0] += value
            env.data.qpos[env._qpos_indices] = q
            env.data.qpos[env.brush_physics.qpos_indices] = 0.0
            mujoco.mj_forward(env.model, env.data)
            qpos.append(q)
            expected.append(env.data.site_xpos[env.brush_physics.rest_site].copy())
        return np.asarray(qpos), np.asarray(expected)
    finally:
        env.close()


def _paper_under(config: EnvConfig, points: np.ndarray, *, depth_m: float) -> EnvConfig:
    surface = float(np.min(points[:, 2]) - depth_m)
    paper = replace(
        config.paper,
        center_x=float(np.mean(points[:, 0])),
        center_y=float(np.mean(points[:, 1])),
        surface_z=surface,
        width=0.333,
        height=0.242,
        margin=0.005,
    )
    return replace(
        config,
        paper=paper,
        safe_height=surface + 0.05,
        hardware=replace(
            config.hardware,
            upright_transport_height_m=surface + 0.10,
        ),
    )


def test_model_splits_twelve_cm_reach_into_eight_cm_rigid_and_four_cm_tuft() -> None:
    model = mujoco.MjModel.from_xml_string(
        brush_model_xml(
            total_length_m=0.12,
            tuft_length_m=0.04,
            distributed_contact=True,
        )
    )
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    mount = data.site("brush_mount_site").xpos
    root = data.body("brush_bristle_link").xpos
    tip = data.site("brush_tip_site").xpos
    rest = data.site("brush_rest_tip_site").xpos
    assert np.linalg.norm(root - mount) == pytest.approx(0.08)
    assert np.linalg.norm(tip - root) == pytest.approx(0.04)
    assert np.linalg.norm(tip - mount) == pytest.approx(0.12)
    assert tip == pytest.approx(rest, abs=1e-12)
    for name in ("brush_bristles", "brush_bristles_mid", "brush_bristles_tip"):
        assert model.geom(name).contype == 2
        assert model.geom(name).conaffinity == 1


def test_moved_hardware_paper_rebuilds_collision_bounds() -> None:
    base = _hardware_config()
    probe = CalligraphyEnv("line", config=base)
    try:
        probe.reset(seed=0)
        qpos = probe.data.qpos[probe._qpos_indices].copy()
        qpos[0] = 1.0  # outside the bundled paper's original Y bounds
        probe.data.qpos[probe._qpos_indices] = qpos
        probe.data.qpos[probe.brush_physics.qpos_indices] = 0.0
        mujoco.mj_forward(probe.model, probe.data)
        tip = probe.data.site_xpos[probe.brush_physics.rest_site].copy()
    finally:
        probe.close()
    config = _paper_under(base, tip[None, :], depth_m=base.brush.tip_radius - 0.0005)
    env = CalligraphyEnv("line", config=config)
    try:
        env.data.qpos[env._qpos_indices] = qpos
        env.data.qpos[env.brush_physics.qpos_indices] = 0.0
        mujoco.mj_forward(env.model, env.data)
        pairs = [
            {int(contact.geom1), int(contact.geom2)}
            for contact in env.data.contact[: env.data.ncon]
        ]
        assert {env._paper_geom_id, env._brush_geom_id} in pairs
    finally:
        env.close()


def test_replay_retains_opposite_tip_history_at_the_same_final_arm_pose() -> None:
    base = _hardware_config()
    negative_q, negative_expected = _rest_path(base, np.linspace(-0.04, 0.0, 24))
    positive_q, positive_expected = _rest_path(base, np.linspace(0.04, 0.0, 24))
    config = _paper_under(
        base,
        np.concatenate((negative_expected, positive_expected)),
        depth_m=0.0015,
    )
    params = ReplayParameters(timestep_s=0.001, sample_period_s=0.005, settle_s=0.1)
    first, first_data, _ = replay_brush(
        config,
        negative_q,
        negative_expected,
        np.ones(len(negative_q), dtype=bool),
        0.05,
        parameters=params,
    )
    second, second_data, _ = replay_brush(
        config,
        positive_q,
        positive_expected,
        np.ones(len(positive_q), dtype=bool),
        0.05,
        parameters=params,
    )
    _, refined_data, _ = replay_brush(
        config,
        negative_q,
        negative_expected,
        np.ones(len(negative_q), dtype=bool),
        0.05,
        parameters=replace(params, timestep_s=0.0005),
    )
    assert negative_q[-1] == pytest.approx(positive_q[-1])
    assert first_data["deflection"][-1, 1] < -0.0001
    assert second_data["deflection"][-1, 1] > 0.0001
    assert np.linalg.norm(first_data["tip"][-1] - second_data["tip"][-1]) > 0.0005
    assert np.linalg.norm(first_data["tip"][-1] - refined_data["tip"][-1]) < 0.0002
    for summary in (first, second):
        assert summary["brush_total_length_mm"] == pytest.approx(120.0)
        assert summary["brush_rigid_length_mm"] == pytest.approx(80.0)
        assert summary["brush_tuft_length_mm"] == pytest.approx(40.0)
        assert summary["physical_writing_verified"] is False
        assert summary["material_calibrated"] is False
        assert summary["metrics"]["solver_warnings"] == 0


def test_high_air_replay_has_no_paper_contact_or_ink() -> None:
    base = _hardware_config()
    qpos, expected = _rest_path(base, np.asarray([0.0, 0.0]))
    config = _paper_under(base, expected, depth_m=0.030)
    summary, arrays, _ = replay_brush(
        config,
        qpos,
        expected,
        np.zeros(2, dtype=bool),
        0.05,
        parameters=ReplayParameters(settle_s=0.05),
    )
    assert not np.any(arrays["contact"])
    assert summary["metrics"]["high_air_contact_s"] == pytest.approx(0.0)
    assert summary["metrics"]["ink_area_mm2"] == pytest.approx(0.0)


def test_replay_rejects_a_timestep_larger_than_the_sample_period() -> None:
    with pytest.raises(ValueError, match="timestep"):
        ReplayParameters(timestep_s=0.02, sample_period_s=0.01)
