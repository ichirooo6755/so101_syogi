"""SO-101 calligraphy learning environment."""

from __future__ import annotations

from typing import Any

__all__ = ["CalligraphyEnv", "register_envs"]
__version__ = "0.4.0"


def __getattr__(name: str) -> Any:
    # Importing this package from the LeRobot venv (teach/play) must not pull MuJoCo.
    if name == "CalligraphyEnv":
        from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv

        return CalligraphyEnv
    if name == "register_envs":
        from so101_calligraphy.envs.registration import register_envs

        return register_envs
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
