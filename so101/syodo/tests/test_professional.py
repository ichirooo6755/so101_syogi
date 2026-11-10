from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from so101_calligraphy.config import EnvConfig, InkConfig, ModuleConfig, PaperConfig
from so101_calligraphy.brushwork import ProfessionalBrushworkPlanner
from so101_calligraphy.config import BrushConfig
from so101_calligraphy.envs import calligraphy_env
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.ink import tip_width_from_pressure
from so101_calligraphy.metrics import endpoint_shape_quality
from so101_calligraphy.trajectory import professional
from so101_calligraphy.trajectory.professional import (
    MotoyaFontError,
    align_glyph_mask,
    refine_trajectory_to_exemplar,
    verify_motoya_font,
)
from so101_calligraphy.trajectory.types import Stroke, Trajectory


def test_endpoint_shape_prefers_the_teacher_wedge() -> None:
    target = np.tri(32, 32, dtype=np.float64)
    matching = endpoint_shape_quality(target, target)
    blunt = endpoint_shape_quality(np.ones((32, 32)), target)

    assert matching["score"] == pytest.approx(1.0)
    assert matching["score"] > blunt["score"]


def test_endpoint_shape_does_not_reward_a_missing_endpoint() -> None:
    target = np.tri(32, 32, dtype=np.float64)
    missing = endpoint_shape_quality(np.zeros((32, 32)), target)

    assert missing["body_presence"] == 0.0
    assert missing["wedge"] == 0.0


def test_professional_mask_aligns_inside_paper() -> None:
    source = np.zeros((24, 12), dtype=np.float32)
    source[2:-2, 4:-4] = 1.0
    target = np.asarray([[0.21, -0.05], [0.26, 0.05]])
    result = align_glyph_mask(source, target, PaperConfig(), InkConfig())
    assert result.shape == (297, 210)
    assert 0.0 < result.mean() < 0.2
    assert result.max() == 1.0


def test_wrong_font_is_rejected(tmp_path: Path) -> None:
    impostor = tmp_path / "not-motoya.otf"
    impostor.write_bytes(b"not a font")
    with pytest.raises(MotoyaFontError, match="Could not inspect"):
        verify_motoya_font(impostor)


def test_verified_aoyagi_path_is_accepted(tmp_path: Path, monkeypatch) -> None:
    font = tmp_path / "KouzanMouhituFont.ttf"
    font.write_bytes(b"verified fixture")
    monkeypatch.setattr(
        professional,
        "_sha256",
        lambda _payload: professional.KOUZAN_TTF_SHA256,
    )
    resolved, source = professional.resolve_exemplar_font(font)
    assert resolved == font.resolve()
    assert source == professional.KOUZAN_SOURCE


def test_professional_mask_uses_resolved_image_teacher(monkeypatch) -> None:
    source = np.zeros((16, 16), dtype=np.float32)
    source[3:-3, 5:-5] = 1.0
    monkeypatch.setattr(
        professional,
        "resolve_exemplar_font",
        lambda _: (Path("fixture.otf"), "fixture"),
    )
    monkeypatch.setattr(professional, "_raw_glyph_mask", lambda *_args: source)
    target = np.asarray([[0.20, -0.04], [0.27, 0.04]])
    result = professional.render_professional_mask(
        "綻", target, PaperConfig(), InkConfig(), "fixture.otf"
    )
    assert result.max() == 1.0


def test_exemplar_fit_preserves_stroke_topology(monkeypatch) -> None:
    points = np.column_stack(
        (np.linspace(0.20, 0.27, 12), np.zeros(12, dtype=np.float64))
    )
    trajectory = Trajectory(
        (
            Stroke(
                points,
                name="horizontal",
                stroke_type="㇐",
                technique="tome",
                widths=np.linspace(0.006, 0.009, len(points)),
            ),
        ),
        source="AnimCJK Japanese median fixture",
        character="一",
    )
    monkeypatch.setattr(
        calligraphy_env,
        "render_professional_mask",
        lambda *_args: np.ones((297, 210), dtype=np.float32),
    )
    env = CalligraphyEnv(
        trajectory=trajectory,
        config=EnvConfig(
            modules=ModuleConfig(professional_exemplar=True),
            motoya_font_path="fixture.otf",
            reset_noise=0.0,
        ),
    )
    try:
        assert len(env.trajectory.strokes) == len(trajectory.strokes)
        assert len(env.trajectory.strokes[0].points) == len(points)
        assert env.trajectory.strokes[0].technique == "tome"
        assert "image-exemplar low-order fit" in env.trajectory.source
    finally:
        env.close()


def test_low_order_fit_moves_a_median_toward_nearby_ink() -> None:
    paper, ink = PaperConfig(), InkConfig()
    xmin = paper.center_x - paper.width * 0.5
    points = np.column_stack(
        (np.linspace(xmin + 0.01, xmin + 0.08, 16), np.zeros(16, dtype=np.float64))
    )
    trajectory = Trajectory(
        (Stroke(points, widths=np.full(len(points), 0.006)),),
        character="一",
    )
    mask = np.zeros((297, 210), dtype=np.float32)
    ymax = paper.center_y + paper.height * 0.5
    x0 = int(0.005 / ink.pixel_size)
    x1 = int(0.09 / ink.pixel_size)
    row = int((ymax - 0.004) / ink.pixel_size)
    mask[row - 3 : row + 4, x0:x1] = 1.0
    fitted = refine_trajectory_to_exemplar(trajectory, mask, paper, ink, strength=1.0)
    assert fitted.strokes[0].points[:, 1].mean() > 0.001
    np.testing.assert_allclose(
        np.asarray(fitted.strokes[0].widths),
        np.asarray(trajectory.strokes[0].widths),
    )


def test_image_exemplar_is_observed_and_rewarded(monkeypatch) -> None:
    points = np.column_stack(
        (np.linspace(0.20, 0.27, 12), np.zeros(12, dtype=np.float64))
    )
    trajectory = Trajectory(
        (Stroke(points, stroke_type="㇐", technique="tome"),),
        source="fixture",
        character="一",
    )
    target = np.zeros((297, 210), dtype=np.float32)
    target[115:180, 55:155] = 1.0
    monkeypatch.setattr(
        calligraphy_env,
        "render_professional_mask",
        lambda *_args: target,
    )
    env = CalligraphyEnv(
        trajectory=trajectory,
        config=EnvConfig(
            ik_assist=True,
            modules=ModuleConfig(professional_exemplar=True),
            observation_version=3,
            reset_noise=0.0,
        ),
    )
    try:
        observation, _ = env.reset(seed=4)
        assert observation.shape == (371,)
        assert np.count_nonzero(observation[65:321]) > 0
        observation, _, _, truncated, info = env.step(np.zeros(6, dtype=np.float32))
        assert env.observation_space.contains(observation)
        assert not truncated
        assert {"exemplar_tracking", "exemplar_image"} <= set(info["reward_terms"])
        assert np.isfinite(info["exemplar_image_error"])
    finally:
        env.close()


def test_heng_has_kaisho_press_release_press() -> None:
    """横画: 起筆押し → 送筆引き → 収筆押し, not AnimCJK mid-fat sausage."""

    brush = BrushConfig()
    points = np.column_stack((np.linspace(0.0, 0.08, 24), np.zeros(24)))
    # Deliberately mid-fat outline: the planner must ignore local samples.
    widths = 0.004 + 0.006 * np.sin(np.linspace(0.0, np.pi, len(points))) ** 2
    profile = ProfessionalBrushworkPlanner().plan(
        Stroke(points, stroke_type="㇐", technique="tome", widths=widths), brush
    )
    assert profile.stroke_family == "heng"
    entry = float(np.mean(profile.pressure[profile.progress <= 0.12]))
    mid = float(np.mean(profile.pressure[(profile.progress >= 0.35) & (profile.progress <= 0.65)]))
    finish = float(np.mean(profile.pressure[profile.progress >= 0.88]))
    assert entry > mid + 0.12
    assert finish > mid + 0.10
    assert finish < entry + 0.05  # トン・スー・トン: finish is light, not a heavy blob
    assert np.linalg.norm(profile.path_delta[0]) > 0.0010
    # Tip rides the upper edge (left normal of +X stroke ≈ +Y).
    mid_delta = profile.path_delta[(profile.progress >= 0.35) & (profile.progress <= 0.65)]
    assert float(np.mean(mid_delta[:, 1])) > 0.0004
    assert float(np.mean(np.abs(profile.roll[profile.progress <= 0.12]))) > 0.35
    assert np.linalg.norm(profile.path_delta[-1]) > 0.0006
    # Planning and deposited ink share one reversible tip-only curve.
    np.testing.assert_allclose(
        tip_width_from_pressure(profile.pressure, brush), profile.width
    )


def test_hane_holds_brush_roll_during_finish() -> None:
    points = np.column_stack(
        (np.linspace(0.0, 0.08, 20), np.linspace(0.0, 0.03, 20) ** 1.2)
    )
    profile = ProfessionalBrushworkPlanner().plan(
        Stroke(points, stroke_type="㇚", technique="hane"), BrushConfig()
    )
    assert profile.stroke_family == "gou"
    assert np.ptp(profile.roll[profile.progress >= 0.72]) == 0.0
