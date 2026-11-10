"""Hardware calibration offsets for sim↔real SO-101 transfer."""

from __future__ import annotations

import numpy as np
import pytest

from so101_calligraphy.config import EnvConfig, HardwareCalibrationConfig, ModuleConfig
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv


def test_hardware_offsets_move_brush_mount_and_inkstone() -> None:
    config = EnvConfig(
        modules=ModuleConfig.professional(),
        hardware=HardwareCalibrationConfig(
            brush_mount_offset_m=(0.004, 0.0, 0.0),
            brush_tip_length_scale=1.10,
            brush_tuft_length_m=0.038 * 1.10,
            inkstone_offset_m=(0.01, -0.008, 0.0),
        ),
        domain_randomization=False,
        reset_noise=0.0,
    )
    env = CalligraphyEnv(task="line", config=config)
    try:
        mount = env.model.site_pos[env._brush_mount_site_id]
        rest = env.model.site_pos[env._brush_rest_tip_site_id]
        assert mount[0] == pytest.approx(env._base_brush_mount_site[0] + 0.004)
        span = float(np.linalg.norm(rest - mount))
        # The configured geometry is compiled before the base values are saved;
        # the offset changes its position, not its 41.8 mm total length.
        assert span == pytest.approx(0.038 * 1.10, rel=1e-6)
        inkstone = env._effective_inkstone()
        assert inkstone is not None
        assert inkstone.center_x == pytest.approx(config.inkstone.center_x + 0.01)
        assert inkstone.center_y == pytest.approx(config.inkstone.center_y - 0.008)
        env.reset(seed=0)
        assert env._effective_inkstone().center_x == pytest.approx(
            config.inkstone.center_x + 0.01
        )
    finally:
        env.close()


def test_measured_total_length_keeps_four_cm_tuft_after_rigid_holder() -> None:
    env = CalligraphyEnv(
        task="line",
        config=EnvConfig(
            hardware=HardwareCalibrationConfig(
                brush_tip_length_scale=12.0 / 3.8,
                brush_tuft_length_m=0.04,
            ),
            domain_randomization=False,
            reset_noise=0.0,
        ),
    )
    try:
        span = float(
            np.linalg.norm(
                env.model.site_pos[env._brush_rest_tip_site_id]
                - env.model.site_pos[env._brush_mount_site_id]
            )
        )
        assert span == pytest.approx(0.12, rel=1e-6)
        env.reset(seed=0)
        root = env.data.xpos[env._brush_bristle_body_id]
        mount = env.data.site_xpos[env._brush_mount_site_id]
        tip = env.data.site_xpos[env._brush_site_id]
        assert np.linalg.norm(root - mount) == pytest.approx(0.08)
        assert np.linalg.norm(tip - root) == pytest.approx(0.04)
    finally:
        env.close()


def test_measured_tuft_is_not_clipped_by_domain_randomization() -> None:
    env = CalligraphyEnv(
        task="line",
        config=EnvConfig(
            hardware=HardwareCalibrationConfig(
                brush_tip_length_scale=12.0 / 3.8,
                brush_tuft_length_m=0.04,
            ),
            domain_randomization=True,
            reset_noise=0.0,
        ),
    )
    try:
        env.reset(seed=0)
        span = float(
            np.linalg.norm(
                env.model.site_pos[env._brush_rest_tip_site_id]
                - env.model.site_pos[env._brush_mount_site_id]
            )
        )
        assert span > 0.038 * 2.0
        assert span == pytest.approx(0.12, rel=1e-6)
    finally:
        env.close()
