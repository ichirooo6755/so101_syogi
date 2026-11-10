from __future__ import annotations

import ast
from dataclasses import asdict
import json
from pathlib import Path
import sys

import numpy as np
import pytest

from so101_calligraphy.pressure_calibration import (
    CALIBRATION_SCHEMA_VERSION,
    DEFAULT_BRUSH_FINGERPRINT,
    DEFAULT_CAD_FINGERPRINT,
    PressureCalibration,
    PressureCurve,
    PressureLookup,
    monotone_non_decreasing,
)


def _calibration() -> PressureCalibration:
    return PressureCalibration(
        schema_version=CALIBRATION_SCHEMA_VERSION,
        cad_fingerprint=DEFAULT_CAD_FINGERPRINT,
        brush_fingerprint=DEFAULT_BRUSH_FINGERPRINT,
        maximum_offset_m=0.0045,
        curves={
            "85mm/30/entry": PressureCurve(
                pressure=(0.10, 0.20, 0.40),
                offset_m=(0.0010, -0.0020, -0.0030),
                sample_weight=(12.0, 18.0, 10.0),
            ),
            "110mm/45/send": PressureCurve(
                pressure=(0.10, 0.30, 0.45),
                offset_m=(0.0020, 0.0005, -0.0025),
                sample_weight=(8.0, 20.0, 9.0),
            ),
        },
        provenance={"git_sha": "abc123", "command": "fit"},
    )


def test_weighted_pava_makes_values_monotone_without_moving_valid_values() -> None:
    valid = monotone_non_decreasing((0.0, 0.5, 0.8), (1.0, 2.0, 1.0))
    assert valid == pytest.approx((0.0, 0.5, 0.8))

    fitted = monotone_non_decreasing((0.0, 0.8, 0.4, 1.0), (1.0, 3.0, 1.0, 1.0))
    assert fitted == pytest.approx((0.0, 0.7, 0.7, 1.0))


def test_weighted_pava_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="same length"):
        monotone_non_decreasing((), (1.0,))
    with pytest.raises(ValueError, match="positive and finite"):
        monotone_non_decreasing((0.0,), (0.0,))
    with pytest.raises(ValueError, match="values must be finite"):
        monotone_non_decreasing((np.nan,), (1.0,))


def test_lookup_interpolates_and_reports_pressure_clipping() -> None:
    calibration = _calibration()

    middle = calibration.lookup("85mm", 30, "entry", 0.30)
    assert isinstance(middle, PressureLookup)
    assert asdict(middle) == {
        "offset_m": pytest.approx(-0.0025),
        "clipped": False,
        "fallback": False,
    }
    assert middle.offset_m == pytest.approx(-0.0025)
    assert not middle.clipped
    assert not middle.fallback

    low = calibration.lookup("85mm", 30.0, "entry", -1.0)
    assert low.offset_m == pytest.approx(0.0010)
    assert low.clipped
    assert not low.fallback


def test_lookup_does_not_silently_use_a_neighbouring_category() -> None:
    result = _calibration().lookup("85mm", 45, "entry", 0.20)

    assert result.offset_m == 0.0
    assert not result.clipped
    assert result.fallback


def test_lookup_does_not_round_an_unobserved_angle_to_a_category() -> None:
    result = _calibration().lookup("85mm", 30.4, "entry", 0.20)

    assert result == PressureLookup(offset_m=0.0, clipped=False, fallback=True)


def test_exact_curve_endpoints_are_not_reported_as_clipped() -> None:
    calibration = _calibration()

    low = calibration.lookup("85mm", 30, "entry", 0.10)
    high = calibration.lookup("85mm", 30, "entry", 0.40)

    assert low == PressureLookup(offset_m=0.0010, clipped=False, fallback=False)
    assert high == PressureLookup(offset_m=-0.0030, clipped=False, fallback=False)


def test_corner_is_a_valid_exact_phase_category() -> None:
    data = _calibration().to_dict()
    data["curves"]["85mm/30/corner"] = data["curves"].pop("85mm/30/entry")

    calibration = PressureCalibration.from_dict(data)

    assert not calibration.lookup("85mm", 30, "corner", 0.20).fallback


def test_pressure_model_uses_only_standard_library_dependencies() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "so101_calligraphy"
        / "pressure_calibration.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    assert imports <= sys.stdlib_module_names, imports - sys.stdlib_module_names


def test_json_round_trip_is_stable(tmp_path: Path) -> None:
    path = tmp_path / "pressure.json"
    original = _calibration()
    original.save(path)

    loaded = PressureCalibration.load(path)
    assert loaded == original
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 2


def test_schema_v1_is_rejected_without_implicit_conversion() -> None:
    data = _calibration().to_dict()
    data["schema_version"] = 1

    with pytest.raises(ValueError, match="Unsupported schema_version: 1"):
        PressureCalibration.from_dict(data)


def test_calibration_mappings_are_immutable() -> None:
    calibration = _calibration()

    with pytest.raises(TypeError):
        calibration.curves["85mm/30/send"] = calibration.curves["85mm/30/entry"]
    with pytest.raises(TypeError):
        calibration.provenance["git_sha"] = "changed"


@pytest.mark.parametrize(
    ("curve", "message"),
    [
        (PressureCurve((0.2, 0.1), (0.0, 0.001), (1.0, 1.0)), "increasing"),
        (PressureCurve((0.1, 0.2), (0.0,), (1.0, 1.0)), "same length"),
        (PressureCurve((0.1, 0.2), (0.0, 0.001, 0.002), (1.0, 1.0)), "same length"),
        (PressureCurve((0.1, np.nan), (0.0, 0.001), (1.0, 1.0)), "finite"),
        (PressureCurve((0.1, 0.2), (0.0, 0.001), (1.0, 1.0)), "monotone"),
        (PressureCurve((0.1, 0.2), (0.0, 0.001), (1.0, 0.0)), "positive"),
    ],
)
def test_invalid_curve_is_rejected(curve: PressureCurve, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        curve.validate(maximum_offset_m=0.0045)


def test_invalid_calibration_metadata_and_offset_are_rejected() -> None:
    base = _calibration().to_dict()
    base["schema_version"] = 999
    with pytest.raises(ValueError, match="schema_version"):
        PressureCalibration.from_dict(base)

    base = _calibration().to_dict()
    base["cad_fingerprint"] = ""
    with pytest.raises(ValueError, match="cad_fingerprint"):
        PressureCalibration.from_dict(base)

    base = _calibration().to_dict()
    base["curves"]["85mm/30/entry"]["offset_m"][-1] = 0.006
    with pytest.raises(ValueError, match="maximum_offset_m"):
        PressureCalibration.from_dict(base)

    for required_field in ("curves", "provenance"):
        base = _calibration().to_dict()
        del base[required_field]
        with pytest.raises(ValueError, match=required_field):
            PressureCalibration.from_dict(base)


@pytest.mark.parametrize("required_field", ("pressure", "offset_m", "sample_weight"))
def test_curve_json_fields_are_required(required_field: str) -> None:
    curve = _calibration().to_dict()["curves"]["85mm/30/entry"]
    del curve[required_field]

    with pytest.raises(ValueError, match=required_field):
        PressureCurve.from_dict(curve)


def test_curve_keys_are_strict_and_supported() -> None:
    base = _calibration().to_dict()
    base["curves"]["85mm/31/entry"] = base["curves"].pop("85mm/30/entry")
    with pytest.raises(ValueError, match="curve key"):
        PressureCalibration.from_dict(base)


@pytest.mark.parametrize("angle", (0, 4, 8, 12, 20, 30, 45))
def test_schema_v2_accepts_each_exact_control_angle(angle: int) -> None:
    data = _calibration().to_dict()
    data["curves"][f"85mm/{angle}/send"] = data["curves"].pop(
        "85mm/30/entry"
    )

    calibration = PressureCalibration.from_dict(data)

    assert not calibration.lookup("85mm", angle, "send", 0.20).fallback

    base = _calibration().to_dict()
    base["curves"]["85mm/030/entry"] = base["curves"].pop("85mm/30/entry")
    with pytest.raises(ValueError, match="curve key"):
        PressureCalibration.from_dict(base)


def test_env_feedforward_pressure_control_integration(tmp_path: Path) -> None:
    from so101_calligraphy.config import BrushConfig, EnvConfig, ModuleConfig
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
    from so101_calligraphy.trajectory.types import Stroke, Trajectory

    calib = _calibration()
    calib_path = tmp_path / "calib.json"
    calib.save(calib_path)

    x = np.linspace(0.20, 0.28, 24)
    traj = Trajectory(
        strokes=[Stroke(points=np.column_stack((x, np.full_like(x, 0.05))))],
        character="一",
    )

    # 1. Without calibration: feedforward is 0, purely integrated
    env_no_calib = CalligraphyEnv(
        trajectory=traj,
        config=EnvConfig(
            ik_assist=True,
            modules=ModuleConfig(brushwork="professional"),
        ),
    )
    try:
        env_no_calib.reset(seed=0, options={"layout_index": 0})
        assert env_no_calib._feedforward_pressure_offset == 0.0
        assert env_no_calib._pressure_calibration is None
    finally:
        env_no_calib.close()

    # 2. With calibration: feedforward applies
    env_with_calib = CalligraphyEnv(
        trajectory=traj,
        config=EnvConfig(
            ik_assist=True,
            modules=ModuleConfig(brushwork="professional"),
            pressure_calibration_path=str(calib_path),
            require_pressure_calibration=True,
        ),
    )
    try:
        _, info = env_with_calib.reset(seed=0, options={"layout_index": 0})
        assert env_with_calib._pressure_calibration is not None
        assert "pressure_calibration_clipped" in info
        assert "pressure_calibration_fallback" in info
        assert "pressure_calibration_clipped" in env_with_calib._stroke_records[0]
    finally:
        env_with_calib.close()

    # 3. Required but missing raises error
    with pytest.raises(ValueError, match="pressure_calibration_path is required"):
        CalligraphyEnv(
            trajectory=traj,
            config=EnvConfig(require_pressure_calibration=True),
        )

    with pytest.raises(FileNotFoundError):
        CalligraphyEnv(
            trajectory=traj,
            config=EnvConfig(pressure_calibration_path=str(tmp_path / "nonexistent.json")),
        )

    base = _calibration().to_dict()
    base["curves"]["85mm/30/unknown"] = base["curves"].pop("85mm/30/entry")
    with pytest.raises(ValueError, match="curve key"):
        PressureCalibration.from_dict(base)


def test_calibrated_lift_residual_is_cleared_during_required_contact_loss(
    tmp_path: Path,
) -> None:
    from so101_calligraphy.config import EnvConfig, ModuleConfig
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
    from so101_calligraphy.trajectory.types import Stroke, Trajectory

    path = tmp_path / "calibration.json"
    _calibration().save(path)
    x = np.linspace(0.20, 0.28, 24)
    env = CalligraphyEnv(
        trajectory=Trajectory(
            strokes=[Stroke(points=np.column_stack((x, np.full_like(x, 0.05))))],
            character="一",
        ),
        config=EnvConfig(
            ik_assist=True,
            modules=ModuleConfig(brushwork="professional"),
            pressure_calibration_path=str(path),
            require_pressure_calibration=True,
        ),
    )
    try:
        env.reset(seed=0, options={"layout_index": 0})
        index = next(i for i, down in enumerate(env.waypoints.pen_down) if bool(down))
        stroke_index = int(env.waypoints.stroke_indices[index])
        env._stroke_records[stroke_index]["pressure"].append(0.2)
        env._contact_force = 0.0
        env._residual_pressure_offset = 0.002
        env._lookup_feedforward_pressure_offset = lambda _index: (0.001, False, False)

        env._update_contact_pressure_control(index)

        assert env._target_requires_contact(index)
        assert env._residual_pressure_offset == 0.0
        assert env._feedforward_pressure_offset == 0.0
        assert env._contact_pressure_offset == 0.0
        assert env._contact_dwell == 0
    finally:
        env.close()


def test_open_loop_probe_applies_fixed_z_offset_with_feedback_disabled() -> None:
    from so101_calligraphy.config import EnvConfig, ModuleConfig
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
    from so101_calligraphy.trajectory.types import Stroke, Trajectory

    x = np.linspace(0.20, 0.28, 24)
    env = CalligraphyEnv(
        trajectory=Trajectory(
            strokes=[Stroke(points=np.column_stack((x, np.full_like(x, 0.05))))],
            character="一",
        ),
        config=EnvConfig(
            ik_assist=True,
            modules=ModuleConfig(brushwork="professional"),
            contact_pressure_gain=0.0,
            large_frame_contact_pressure_gain=0.0,
            horizontal_contact_pressure_gain=0.0,
            pressure_probe_offset_m=-0.003,
        ),
    )
    try:
        env.reset(seed=0, options={"layout_index": 0})
        index = next(i for i, down in enumerate(env.waypoints.pen_down) if bool(down))
        stroke_index = int(env.waypoints.stroke_indices[index])

        env._update_contact_pressure_control(index)

        assert env._contact_pressure_correction(index) == pytest.approx(-0.003)
        assert env._feedforward_pressure_offset == pytest.approx(-0.003)
        assert env._residual_pressure_offset == 0.0

        env._target_index = index
        before = env._target_index
        env.step(np.zeros(6, dtype=np.float32))
        assert env._target_index == before

        later_same_stroke = next(
            i
            for i in range(index + 1, len(env.waypoints))
            if bool(env.waypoints.pen_down[i])
            and int(env.waypoints.stroke_indices[i]) == stroke_index
        )
        assert env._pressure_probe_settle_required(index)
        assert not env._pressure_probe_settle_required(later_same_stroke)
        assert env._pressure_probe_should_wait(index)
        env._target_dwell = 80
        assert not env._pressure_probe_should_wait(index)
    finally:
        env.close()


@pytest.mark.parametrize(
    ("phase", "technique", "expected"),
    (("entry", "tome", 30), ("corner", "tome", 20), ("finish", "tome", 30),
     ("finish", "hane", 4), ("finish", "harai", 4), ("send", "tome", 8)),
)
def test_environment_reports_controller_angle_category(
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
    technique: str,
    expected: int,
) -> None:
    from so101_calligraphy.config import EnvConfig, ModuleConfig
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv

    env = CalligraphyEnv(
        "line",
        config=EnvConfig(modules=ModuleConfig(brushwork="professional")),
    )
    try:
        metadata = env._target_metadata(0)
        metadata.update(brushwork_phase=phase, technique=technique, stroke_index=-1)
        monkeypatch.setattr(env, "_target_metadata", lambda _index=None: metadata)
        monkeypatch.setattr(env, "_uses_fixed_contact_lean", lambda _index=None: False)

        assert env._pressure_calibration_angle_deg(0) == expected
    finally:
        env.close()
