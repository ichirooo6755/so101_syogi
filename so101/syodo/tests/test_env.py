from __future__ import annotations

import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from so101_calligraphy.config import EnvConfig, ModuleConfig, PaperConfig
from so101_calligraphy.metrics import BEAUTY_COMPONENT_WEIGHTS
from so101_calligraphy.envs.calligraphy_env import (
    CalligraphyEnv,
    _next_contact_pressure_offset,
    _pressure_from_contact_force,
    contact_orientation_family_scale,
    contact_pressure_direction_scale,
    contact_pressure_gain_scale,
    harai_finish_release,
)
from so101_calligraphy.trajectory.primitives import primitive_trajectory


def test_contact_pressure_uses_force_without_soft_contact_penetration() -> None:
    assert _pressure_from_contact_force(0.0, 1.5) == 0.0
    assert _pressure_from_contact_force(1.5, 1.5) == pytest.approx(1.0 - np.exp(-1.0))
    assert _pressure_from_contact_force(0.15, 1.5) < _pressure_from_contact_force(
        0.30, 1.5
    )


def test_contact_pressure_integrator_is_leaky_and_bounded() -> None:
    assert _next_contact_pressure_offset(0.003, 0.10, 0.012, 0.0035) > 0.003
    assert _next_contact_pressure_offset(0.0035, 1.0, 0.012, 0.0035) == 0.0035
    assert _next_contact_pressure_offset(0.003, -0.10, 0.012, 0.0035) < 0.003


@pytest.mark.parametrize("task", ["line", "circle", "cross"])
def test_reset_and_step_contract(task: str) -> None:
    env = CalligraphyEnv(task)
    try:
        observation, info = env.reset(seed=3)
        assert observation.shape == (42,)
        assert observation.dtype == np.float32
        assert env.observation_space.contains(observation)
        assert env.action_space.shape == (6,)
        assert np.linalg.norm(env.target_position - env.brush_position) < 0.02
        assert info["progress"] == 0.0

        result = env.step(np.zeros(6, dtype=np.float32))
        next_observation, reward, terminated, truncated, step_info = result
        assert env.observation_space.contains(next_observation)
        assert np.isfinite(reward)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert "reward_terms" in step_info
        assert {
            "tracking",
            "progress",
            "pressure",
            "width",
            "orientation",
            "collision",
            "joint_limit",
        }.issubset(
            step_info["reward_terms"]
        )
    finally:
        env.close()


def test_gymnasium_checker() -> None:
    env = CalligraphyEnv("line")
    try:
        check_env(env, skip_render_check=True)
    finally:
        env.close()


def test_action_shape_is_validated() -> None:
    env = CalligraphyEnv("line")
    try:
        env.reset()
        with pytest.raises(ValueError, match="Action must have shape"):
            env.step(np.zeros(5, dtype=np.float32))
    finally:
        env.close()


def test_environment_never_time_truncates() -> None:
    env = CalligraphyEnv("line")
    try:
        env.reset(seed=3)
        for _ in range(25):
            _, _, _, truncated, _ = env.step(np.zeros(6, dtype=np.float32))
            assert not truncated
    finally:
        env.close()


def test_multi_trajectory_selection_and_expert() -> None:
    trajectories = tuple(
        primitive_trajectory(task, paper=PaperConfig()) for task in ("line", "circle")
    )
    env = CalligraphyEnv(task="multi", trajectories=trajectories)
    try:
        _, info = env.reset(seed=7, options={"trajectory_index": 1, "target_index": 3})
        assert info["trajectory_index"] == 1
        assert info["target_index"] == 3
        assert env.expert_action().shape == (6,)

        env.reset(seed=7, options={"trajectory_index": 0})
        for _ in range(10_000):
            _, _, terminated, truncated, info = env.step(env.expert_action())
            if terminated or truncated:
                break
        assert info["is_success"]
    finally:
        env.close()


def test_ik_assist_tracks_with_zero_residual() -> None:
    env = CalligraphyEnv("line", config=EnvConfig(ik_assist=True))
    try:
        env.reset(seed=7)
        for _ in range(10_000):
            _, _, terminated, truncated, info = env.step(
                np.zeros(6, dtype=np.float32)
            )
            if terminated or truncated:
                break
        assert info["is_success"]
    finally:
        env.close()


def test_compliant_brush_writes_varying_width_ink() -> None:
    env = CalligraphyEnv("line", config=EnvConfig(ik_assist=True))
    try:
        env.reset(seed=7)
        widths: list[float] = []
        for _ in range(10_000):
            _, _, terminated, truncated, info = env.step(
                np.zeros(6, dtype=np.float32)
            )
            if info["line_width"] > 0:
                widths.append(info["line_width"])
            if terminated or truncated:
                break
        assert info["is_success"]
        assert len(env.ink.deposits) > 20
        assert env.ink.pigment.max() > 0.1
        assert max(widths) - min(widths) > 0.001
        assert 0.0 < info["beauty_score"] <= 100.0
        assert np.linalg.norm(info["brush_deflection"]) > 0.0
    finally:
        env.close()


def test_professional_episode_loads_wipes_and_writes_without_dripping() -> None:
    env = CalligraphyEnv(
        "line",
        config=EnvConfig(
            ik_assist=True,
            reset_noise=0.0,
            modules=ModuleConfig.professional(),
            observation_version=2,
        ),
    )
    phases: set[str] = set()
    try:
        observation, info = env.reset(seed=17)
        assert observation.shape == (65,)
        assert info["observation_version"] == 2
        for _ in range(10_000):
            observation, _, terminated, truncated, info = env.step(
                np.zeros(6, dtype=np.float32)
            )
            phases.add(info["episode_phase"])
            if terminated or truncated:
                break
        assert info["is_success"]
        assert {"load", "wipe", "carry", "draw", "finish"} <= phases
        assert info["drip_count"] == 0
        assert info["collision_types"] == []
        assert set(info["beauty_components"]) == set(BEAUTY_COMPONENT_WEIGHTS)
        assert info["beauty_score"] > 70.0
        assert env.ink.pigment.max() > 0.1
    finally:
        env.close()


def test_contact_pressure_gain_favors_harai_over_hane_store() -> None:
    # 係数そのものは gain の再調整で動く。守りたいのは技法間の関係:
    # 払いは抜くので持ち上げを強く、はねは蓄力中だけ弱く、蓄力後は通常に戻る。
    harai = contact_pressure_gain_scale("harai", 0.9)
    hane_store = contact_pressure_gain_scale("hane", 0.70)
    assert harai > 1.0
    assert hane_store < 1.0
    assert harai > hane_store
    assert contact_pressure_gain_scale("hane", 0.90) == 1.0
    assert contact_pressure_gain_scale(
        "hane", 0.90, hane_release_scale=3.0
    ) == 3.0
    assert contact_pressure_gain_scale("tome", 0.9) == 1.0
    assert contact_pressure_direction_scale("shu", np.asarray([1.0, 0.0])) == 1.0
    assert contact_pressure_direction_scale("zhe", np.asarray([0.0, 1.0])) == pytest.approx(
        7.0 / 6.0
    )
    assert contact_pressure_direction_scale("shu", np.asarray([0.0, 1.0])) == pytest.approx(
        9.0 / 7.0
    )
    assert contact_pressure_direction_scale("zhe", np.asarray([1.0, 0.0])) == pytest.approx(
        7.0 / 6.0
    )
    assert contact_orientation_family_scale("zhe") == pytest.approx(1.0 / 3.0)
    assert contact_orientation_family_scale("heng") == 1.0
    assert contact_orientation_family_scale("heng", turning_glyph=True) == pytest.approx(
        1.0 / 3.0
    )
    assert contact_pressure_direction_scale(
        "heng", np.asarray([1.0, 0.0]), turning_glyph=True
    ) == pytest.approx(7.0 / 6.0)
    assert contact_pressure_direction_scale(
        "heng", np.asarray([1.0, 0.0]), left_horizontal_glyph=True
    ) == pytest.approx(7.0 / 6.0)


def test_harai_finish_release_matches_eval_tolerances() -> None:
    perfect = harai_finish_release(
        width=0.004,
        target_width=0.004,
        pressure=0.05,
        target_pressure=0.05,
        speed=0.15,
        target_speed=0.15,
    )
    assert perfect == pytest.approx(1.0)
    wide = harai_finish_release(
        width=0.010,
        target_width=0.004,
        pressure=0.05,
        target_pressure=0.05,
        speed=0.15,
        target_speed=0.15,
    )
    assert wide == pytest.approx(0.333 + 0.250, rel=1e-6)
    slow = harai_finish_release(
        width=0.004,
        target_width=0.004,
        pressure=0.05,
        target_pressure=0.05,
        speed=0.085,
        target_speed=0.15,
    )
    # 評価許容 0.065 では |Δv|=0.065 で speed 成分が e^-1。学習許容 0.12 ならほぼ満点。
    assert slow == pytest.approx(0.417 + 0.333 + 0.250 * np.exp(-1.0), rel=1e-6)
