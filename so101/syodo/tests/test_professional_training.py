from __future__ import annotations

from dataclasses import replace
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from so101_calligraphy.config import WritingLayoutConfig
import so101_calligraphy.training.professional as professional
from so101_calligraphy.training.professional import (
    _collect_demonstration_chunk,
    _copy_policy_only,
    _parse_args,
    _set_learning_rate,
    _training_layouts,
    _validate_args,
    apply_center110_profile,
    module_preset,
    professional_config,
    stage_gate,
)


def test_center110_profile_is_versioned_and_keeps_default_unchanged() -> None:
    default = professional_config()
    centered = replace(
        default,
        writing_layout=WritingLayoutConfig.brushmark_center(),
    )
    tuned = apply_center110_profile(centered, "p10-80-v1")

    assert apply_center110_profile(default, None) == default
    assert tuned.brush.minimum_width == 0.0063
    assert tuned.brush.maximum_width == 0.024
    assert tuned.target_tolerance_xy == 0.0015
    assert tuned.contact_pressure_gain == 0.0234
    assert tuned.large_frame_contact_pressure_gain == 0.0226
    assert tuned.horizontal_contact_pressure_gain == 0.019
    assert tuned.contact_pressure_limit == 0.007
    assert tuned.horizontal_contact_pressure_limit == 0.007
    assert tuned.exemplar_motion_strength == 0.50
    assert tuned.stroke_minimum_gap == 0.003
    assert tuned.stroke_clearance_floor == 0.25


def test_brushmark_cli_selects_only_center_layout_and_beauty_80(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "so101-train-professional",
            "--brushmark-layout",
            "--hard-beauty-threshold",
            "80",
        ],
    )

    args = _parse_args()
    _validate_args(args)
    config = replace(
        professional_config(),
        writing_layout=WritingLayoutConfig.brushmark_center(),
    )

    assert args.brushmark_layout
    assert args.hard_beauty_threshold == 80.0
    assert args.eval_layouts is None
    assert _training_layouts(config) == (0,)


def test_desk_flag_requires_an_existing_file(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["so101-train-professional", "--desk", "missing-desk.json"],
    )
    args = _parse_args()
    with pytest.raises(SystemExit, match="Desk file"):
        _validate_args(args)


def test_brushmark_bc_samples_only_the_real_center_layout(monkeypatch) -> None:
    sampled_layouts: list[int] = []

    class FakeEnv:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def reset(self, *, seed, options):
            sampled_layouts.append(options["layout_index"])
            return np.zeros(1, dtype=np.float32), {}

        def step(self, _action):
            return np.zeros(1, dtype=np.float32), 0.0, True, False, {}

        def close(self) -> None:
            pass

    monkeypatch.setattr(professional, "CalligraphyEnv", FakeEnv)
    config = replace(
        professional_config(),
        writing_layout=WritingLayoutConfig.brushmark_center(),
    )

    observations, actions = _collect_demonstration_chunk(
        [object()], 8, "all", 17, config
    )

    assert sampled_layouts == [0] * 8
    assert observations.shape == (8, 1)
    assert actions.shape == (8, 6)


def test_resumed_model_uses_cli_learning_rate() -> None:
    model = SimpleNamespace(
        learning_rate=2e-4,
        lr_schedule=lambda _: 2e-4,
        policy=SimpleNamespace(optimizer=SimpleNamespace(param_groups=[{"lr": 2e-4}])),
    )

    _set_learning_rate(model, 1e-4)

    assert model.learning_rate == 1e-4
    assert model.lr_schedule(1.0) == 1e-4
    assert model.policy.optimizer.param_groups[0]["lr"] == 1e-4


def test_policy_only_warm_start_keeps_fresh_optimizer_and_resets_steps() -> None:
    class Policy:
        def __init__(self, state: dict[str, int], optimizer: object) -> None:
            self._state = state
            self.optimizer = optimizer

        def state_dict(self) -> dict[str, int]:
            return dict(self._state)

        def load_state_dict(self, state: dict[str, int]) -> None:
            self._state = dict(state)

    old_optimizer = object()
    fresh_optimizer = object()
    parent = SimpleNamespace(policy=Policy({"weight": 7}, old_optimizer), num_timesteps=99)
    fresh = SimpleNamespace(policy=Policy({"weight": 0}, fresh_optimizer), num_timesteps=42)

    _copy_policy_only(parent, fresh)

    assert fresh.policy.state_dict() == {"weight": 7}
    assert fresh.policy.optimizer is fresh_optimizer
    assert fresh.policy.optimizer is not parent.policy.optimizer
    assert fresh.num_timesteps == 0


def test_professional_modules_are_independently_rollbackable() -> None:
    legacy = module_preset("legacy")
    brush = module_preset("brush")
    brush_ink = module_preset("brush-ink")
    complete = module_preset("all")

    assert legacy.brush_physics == "legacy"
    assert brush.brush_physics == "professional" and brush.ink_model == "legacy"
    assert brush_ink.ink_model == "professional" and brush_ink.brushwork == "legacy"
    assert complete.brushwork == "professional" and complete.professional_exemplar
    for preset, field in (
        ("no-brush", "brush_physics"),
        ("no-ink", "ink_model"),
        ("no-brushwork", "brushwork"),
    ):
        modules = module_preset(preset)
        assert getattr(modules, field) == "legacy"
    assert not module_preset("no-exemplar").professional_exemplar
    assert professional_config("legacy").observation_version == 3


def test_curriculum_gate_rejects_unsafe_or_weak_technique() -> None:
    components = {
        "trajectory": 90.0,
        "line_width": 90.0,
        "stroke_placement": 90.0,
        "stroke_angle": 90.0,
        "brushwork": 90.0,
        "smoothness": 90.0,
    }
    passed, failures = stage_gate(
        {
            "success_rate": 1.0,
            "component_means": components,
            "technique_means": {
                "tome": {"count": 1, "finish": 90.0, "width": 90.0}
            },
            "total_drips": 0,
            "collision_count": 0,
        }
    )
    assert passed and not failures
    components["brushwork"] = 20.0
    passed, failures = stage_gate(
        {
            "success_rate": 1.0,
            "component_means": components,
            "technique_means": {
                "hane": {"count": 1, "finish": 20.0, "width": 90.0}
            },
            "total_drips": 1,
            "collision_count": 0,
        }
    )
    assert not passed
    assert {"brushwork", "hane_finish", "drips"} <= set(failures)
