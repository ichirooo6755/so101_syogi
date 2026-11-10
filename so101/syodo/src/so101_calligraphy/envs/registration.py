"""Gymnasium registry integration."""

from __future__ import annotations

import gymnasium as gym


ENV_ID = "SO101Calligraphy-v0"


def register_envs() -> None:
    if ENV_ID not in gym.registry:
        gym.register(
            id=ENV_ID,
            entry_point="so101_calligraphy.envs.calligraphy_env:CalligraphyEnv",
        )

