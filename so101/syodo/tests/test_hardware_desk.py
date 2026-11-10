"""Desk calibration: paper box, suzuri, tilt sign, tuft length."""

from __future__ import annotations

import numpy as np
import pytest

from so101_calligraphy.config import PaperConfig, JOINT_NAMES
from so101_calligraphy.hardware_desk import (
    SIM_HOME_POSE,
    GRIPPER_DEG_PER_PCT,
    GRIPPER_FIT_MAX_RESID_DEG,
    empty_desk,
    env_config_from_desk,
    check_taught_plane,
    desk_fingerprint,
    desk_joint_ranges,
    fit_gripper_zero,
    fit_paper,
    format_desk,
    format_joints,
    glyph_cells,
    write_z_along_depth,
    infer_tilt_sign,
    joint_offsets_from_sim_home,
    lerobot_to_qpos,
    qpos_to_lerobot,
    overlay_desk_hardware,
    pose_deg,
    require_ready,
    geometry_fingerprint,
    REQUIRED_POSES,
    taught_ichi_waypoints,
    tuft_scale,
    brush_geometry,
    upright_on_paper,
    place_on_paper,
)


def _ready_desk() -> dict:
    desk = empty_desk()
    desk.update(
        {
            "ready": True,
            "tilt_sign": -1,
            "brush_total_cm": 5.0,
            "brush_rigid_cm": 0.0,
            "brush_tuft_cm": 5.0,
            "brush_tip_length_scale": brush_geometry(5.0, 5.0)[0],
            "paper": {
                "width": 0.242,
                "height": 0.333,
                "center_x": 0.30,
                "center_y": 0.0,
                "surface_z": 0.012,
                "margin": 0.015,
            },
            "inkstone_offset_m": [0.01, 0.0, 0.0],
            "tilt_range": [10.0, 70.0],
            "safe_height_m": 0.04,
            "tip_points_down": True,
            "gripper_map_rad": [-0.17, 1.74],
            "joint_offsets_deg": {name: 0.0 for name in JOINT_NAMES[:-1]},
            "sim_home_qpos_deg": {name: 0.0 for name in JOINT_NAMES},
            "poses": {
                pose: {name: 0.0 for name in JOINT_NAMES}
                for pose in (*REQUIRED_POSES, SIM_HOME_POSE)
            },
        }
    )
    return desk


@pytest.mark.parametrize("value", ["true", "false", 1, None])
def test_ready_must_be_a_boolean(value) -> None:
    desk = _ready_desk()
    desk["ready"] = value
    with pytest.raises(SystemExit, match="未完了"):
        require_ready(desk)


@pytest.mark.parametrize("field,value", [
    ("poses", {}), ("tip_points_down", False),
    ("brush_tip_length_scale", 1.0), ("safe_height_m", float("nan")),
    ("safe_height_m", 0.014), ("gripper_map_rad", [0.0, 0.0]),
    ("tilt_range", [70.0, 10.0]), ("inkstone_offset_m", [0.0, 0.0]),
])
def test_ready_flag_cannot_bypass_missing_or_invalid_measurements(field, value) -> None:
    desk = _ready_desk()
    desk[field] = value
    with pytest.raises(SystemExit, match="較正が不正"):
        require_ready(desk)


def test_solve_fingerprint_detects_changed_pose_but_allows_usb_binding() -> None:
    desk = _ready_desk()
    desk["geometry_fingerprint"] = geometry_fingerprint(desk)
    desk["follower_usb_serial"] = "offline-test"
    assert require_ready(desk) is desk
    desk["poses"]["paper_center_touch"]["elbow_flex"] += 1.0
    with pytest.raises(SystemExit, match="solve 後"):
        require_ready(desk)


def test_one_glyph_cell_sits_in_the_paper_center() -> None:
    paper = PaperConfig(width=0.168, height=0.173, center_x=0.251, center_y=-0.010)
    (cell,) = glyph_cells(paper, 1)
    assert cell.center_x == pytest.approx(paper.center_x)
    assert cell.center_y == pytest.approx(paper.center_y)
    assert cell.width == pytest.approx(cell.height)
    assert cell.width < paper.width
    top = np.array([[paper.center_x, paper.center_y + 0.04]])
    rotated = upright_on_paper(top, paper)
    # お手本の天 +y は紙の奥 +x、字の右 +x は下手右 +y。
    assert rotated[0, 0] > paper.center_x
    assert rotated[0, 1] == pytest.approx(paper.center_y)
    right = np.array([[paper.center_x + 0.04, paper.center_y]])
    rotated_right = upright_on_paper(right, paper)
    assert rotated_right[0, 0] == pytest.approx(paper.center_x)
    assert rotated_right[0, 1] > paper.center_y
    placed = place_on_paper(top, paper)
    assert placed[0, 0] == pytest.approx(rotated[0, 0])
    assert placed[0, 1] == pytest.approx(rotated[0, 1])


def test_write_z_falls_from_far_to_near() -> None:
    far_x, near_x = 0.30, 0.20
    far_z, near_z = 0.020, 0.000
    z = write_z_along_depth(
        np.array([far_x, 0.25, near_x]), far_x, near_x, far_z, near_z
    )
    assert z[0] == pytest.approx(far_z)
    assert z[1] == pytest.approx(0.010)
    assert z[2] == pytest.approx(near_z)
    assert write_z_along_depth(far_x + 0.05, far_x, near_x, far_z, near_z) == pytest.approx(
        far_z
    )
    assert write_z_along_depth(near_x - 0.05, far_x, near_x, far_z, near_z) == pytest.approx(
        near_z
    )


def test_two_glyph_cells_respect_paper_margin() -> None:
    paper = PaperConfig(
        width=0.266756,
        height=0.153905,
        center_x=0.235381,
        center_y=-0.017128,
        margin=0.015,
    )
    cells = glyph_cells(paper, 2)
    assert len(cells) == 2
    for cell in cells:
        assert cell.width == pytest.approx((paper.width - 2 * paper.margin) / 2)
        assert cell.center_x - cell.width / 2 >= paper.center_x - paper.width / 2 + paper.margin - 1e-9
        assert cell.center_x + cell.width / 2 <= paper.center_x + paper.width / 2 - paper.margin + 1e-9
        assert cell.center_y - cell.height / 2 >= paper.center_y - paper.height / 2 + paper.margin - 1e-9
        assert cell.center_y + cell.height / 2 <= paper.center_y + paper.height / 2 - paper.margin + 1e-9
    assert cells[0].center_x > cells[1].center_x


@pytest.mark.parametrize("count", (1, 2, 3, 4))
def test_hardware_frames_fill_sheet_without_overlap(count: int) -> None:
    paper = PaperConfig(width=0.27, height=0.16, margin=0.015)
    cells = glyph_cells(paper, count)
    assert len(cells) == count
    expected = min(0.24 / (1 if count == 1 else 2), 0.13 / (2 if count >= 3 else 1))
    for cell in cells:
        assert cell.width == pytest.approx(expected)
        assert cell.height == pytest.approx(expected)
        assert cell.margin == 0
        assert abs(cell.center_x - paper.center_x) + expected/2 <= 0.12 + 1e-9
        assert abs(cell.center_y - paper.center_y) + expected/2 <= 0.065 + 1e-9
    for i, cell in enumerate(cells):
        for other in cells[i+1:]:
            assert max(abs(cell.center_x-other.center_x), abs(cell.center_y-other.center_y)) >= expected - 1e-9
    if count >= 3:
        assert cells[0].center_x == cells[2].center_x
        assert cells[0].center_y > cells[2].center_y
        assert cells[0].center_x > cells[1].center_x


def test_measured_joint_ranges_are_valid_and_fingerprint_changes() -> None:
    desk = _ready_desk()
    desk["joint_ranges_rad"] = [[-1.0, 1.0]] * 6
    assert desk_joint_ranges(desk) == ((-1.0, 1.0),) * 6
    original = desk_fingerprint(desk)
    desk["paper"]["surface_z"] += 0.001
    assert desk_fingerprint(desk) != original
    desk["joint_ranges_rad"] = [[0.0, 0.0]] * 6
    with pytest.raises(ValueError, match="increasing"):
        desk_joint_ranges(desk)


def test_desk_safe_height_is_absolute_above_the_measured_paper() -> None:
    """desk は紙面からの余裕、env は絶対 z。取り違えると pen_down_z より下になる。"""
    desk = _ready_desk()
    desk["paper"]["surface_z"] = 0.1015
    config = env_config_from_desk(desk)
    assert config.safe_height == pytest.approx(0.1015 + desk["safe_height_m"])
    assert config.safe_height > config.pen_down_z
    assert config.hardware.upright_transport_height_m > config.safe_height


def test_gripper_zero_ignores_one_laid_pose() -> None:
    """寝たまま取った教示が 1 つ混ざっても、ゼロ点は正しい群に残る。"""
    pct = np.array([55.0, 55.0, 44.6, 44.6, 44.6, 56.9])
    deg = GRIPPER_DEG_PER_PCT * pct + 52.4
    deg[-1] += 85.0  # upright を寝たまま取った状態
    zero, resid = fit_gripper_zero(pct, deg)
    assert abs(zero - 52.4) < 1e-6
    assert (np.abs(resid[:-1]) < GRIPPER_FIT_MAX_RESID_DEG).all()
    assert abs(resid[-1]) > GRIPPER_FIT_MAX_RESID_DEG


def test_qpos_roundtrip_and_inverted_tilt() -> None:
    q = np.zeros(6)
    q[0] = np.deg2rad(10.0)
    q[-1] = 0.0
    forward = qpos_to_lerobot(q, tilt_sign=1)
    assert abs(forward["shoulder_pan"] - 10.0) < 1e-9
    back = lerobot_to_qpos(forward, tilt_sign=1)
    assert abs(back[0] - q[0]) < 1e-9
    flipped = qpos_to_lerobot(q, tilt_sign=-1)
    assert abs(flipped["gripper"] + forward["gripper"] - 100.0) < 1e-6
    offset = {"wrist_roll": 110.0}
    q[4] = np.deg2rad(-20.0)
    taught = qpos_to_lerobot(q, offsets=offset)
    assert taught["wrist_roll"] == pytest.approx(-130.0)
    assert lerobot_to_qpos(taught, offsets=offset)[4] == pytest.approx(q[4])


def test_fit_paper_from_hanshi_corners() -> None:
    corners = np.array(
        [
            [0.20, -0.12, 0.012],
            [0.20, 0.12, 0.012],
            [0.53, 0.12, 0.013],
            [0.53, -0.12, 0.011],
        ]
    )
    paper = fit_paper(corners, touch_z=0.012)
    assert paper["width"] == pytest.approx(0.33)
    assert paper["height"] == pytest.approx(0.24)
    assert paper["center_x"] == pytest.approx(0.365)
    assert paper["surface_z"] == pytest.approx(0.012)


def test_fit_paper_rejects_tiny_sheet() -> None:
    corners = np.array(
        [
            [0.0, 0.0, 0.01],
            [0.02, 0.0, 0.01],
            [0.02, 0.02, 0.01],
            [0.0, 0.02, 0.01],
        ]
    )
    with pytest.raises(ValueError, match="小さすぎ"):
        fit_paper(corners, 0.01)


def test_taught_corners_must_share_a_table_plane() -> None:
    corners = np.array(
        [
            [0.20, -0.12, 0.32],
            [0.20, 0.12, 0.32],
            [0.53, 0.12, 0.13],
            [0.53, -0.12, 0.13],
        ]
    )
    with pytest.raises(ValueError, match="同じ机の高さ"):
        check_taught_plane(corners)
    check_taught_plane(np.array([[0.2, -0.1, 0.012], [0.2, 0.1, 0.013], [0.4, 0.1, 0.011], [0.4, -0.1, 0.012]]))


def test_infer_tilt_sign_and_tuft_scale() -> None:
    upright = np.array([0.0, 0.0, -1.0])
    lean = np.array([0.5, 0.0, -0.866])
    assert infer_tilt_sign(upright, lean) == 1
    assert infer_tilt_sign(lean, upright) == -1
    assert tuft_scale(3.8) == pytest.approx(1.0)
    assert tuft_scale(5.7) == pytest.approx(1.5)
    total_scale, rigid_m, tuft_m = brush_geometry(12.0, 4.0)
    assert total_scale == pytest.approx(12.0 / 3.8)
    assert rigid_m == pytest.approx(0.08)
    assert tuft_m == pytest.approx(0.04)
    with pytest.raises(ValueError, match="2"):
        tuft_scale(1.0)


def test_require_ready_and_env_uses_tuft_scale() -> None:
    desk = empty_desk()
    with pytest.raises(SystemExit):
        require_ready(desk)
    assert "brush_tuft_cm" in format_desk(desk)
    config = env_config_from_desk(_ready_desk())
    assert config.hardware.brush_tip_length_scale == pytest.approx(5.0 / 3.8)
    assert config.hardware.brush_tuft_length_m == pytest.approx(0.05)
    assert config.paper.width == pytest.approx(0.242)
    clipped = qpos_to_lerobot(
        np.zeros(6), tilt_sign=-1, tilt_range=(10.0, 70.0)
    )
    assert 10.0 <= clipped["gripper"] <= 70.0


def test_env_applies_all_measured_joint_ranges() -> None:
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv

    desk = _ready_desk()
    values = tuple((-(index + 1.0), index + 2.0) for index in range(6))
    desk["joint_ranges_rad"] = [list(pair) for pair in values]
    env = CalligraphyEnv(task="line", config=env_config_from_desk(desk))
    try:
        assert np.allclose(env._joint_limits, np.asarray(values))
        assert np.allclose(env.model.actuator_ctrlrange[:6], np.asarray(values))
    finally:
        env.close()


def test_taught_ichi_waypoints_use_near_edge() -> None:
    zero = {
        "shoulder_pan": 0.0,
        "shoulder_lift": 0.0,
        "elbow_flex": 0.0,
        "wrist_flex": 0.0,
        "wrist_roll": 0.0,
        "gripper": 0.0,
    }
    desk = empty_desk()
    desk["poses"] = {
        "hover_center": {**zero, "shoulder_lift": 50.0},
        "paper_near_left": {**zero, "shoulder_pan": -40.0, "gripper": 20.0},
        "paper_near_right": {**zero, "shoulder_pan": 30.0, "gripper": 35.0},
    }
    labels, goals = zip(*taught_ichi_waypoints(desk))
    assert labels == ("hover", "start", "end", "hover")
    assert goals[1][0] == pytest.approx(-40.0)
    assert goals[2][0] == pytest.approx(30.0)
    # hover は下手左の折りのまま土台だけ中央。hover_center の肩は使わない。
    assert goals[0][1] == pytest.approx(0.0)
    assert goals[0][2] == pytest.approx(0.0)
    assert goals[0][5] == pytest.approx(20.0)
    assert goals[2][2] == pytest.approx(0.0)
    assert goals[2][5] == pytest.approx(20.0)
    with pytest.raises(ValueError, match="未記録"):
        pose_deg(empty_desk(), "hover_center")
    assert "ID6" in format_joints(desk["poses"]["paper_near_left"])


def test_sim_home_offsets_are_sim_minus_taught() -> None:
    desk = empty_desk()
    desk["sim_home_qpos_deg"] = {
        "shoulder_pan": 0.0,
        "shoulder_lift": -90.0,
        "elbow_flex": 90.0,
        "wrist_flex": 0.0,
        "wrist_roll": 0.0,
        "gripper": 64.0,
    }
    desk["poses"] = {
        SIM_HOME_POSE: {
            "shoulder_pan": 1.0,
            "shoulder_lift": 10.0,
            "elbow_flex": 50.0,
            "wrist_flex": -40.0,
            "wrist_roll": -108.0,
            "gripper": 0.0,
        }
    }
    offsets = joint_offsets_from_sim_home(desk)
    assert offsets["shoulder_lift"] == pytest.approx(-100.0)
    assert offsets["elbow_flex"] == pytest.approx(40.0)
    assert offsets["wrist_roll"] == pytest.approx(108.0)
    assert "gripper" not in offsets


def test_overlay_desk_hardware_applies_tuft_before_paper_is_ready() -> None:
    from so101_calligraphy.config import EnvConfig
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv

    desk = empty_desk()
    desk["brush_total_cm"] = 12.0
    desk["brush_rigid_cm"] = 8.0
    desk["brush_tuft_cm"] = 4.0
    config = overlay_desk_hardware(EnvConfig(), desk)
    assert config.hardware.brush_tip_length_scale == pytest.approx(12.0 / 3.8)
    assert config.hardware.brush_tuft_length_m == pytest.approx(0.04)
    assert config.paper.width == pytest.approx(0.333)
    assert config.paper.height == pytest.approx(0.242)
    assert config.hardware.base_riser_height_m == 0.0
    with pytest.raises(ValueError, match="全長と穂長"):
        overlay_desk_hardware(EnvConfig(), empty_desk())
    # 縦置き半紙は既定の桝目に収まらない。solve もこの config で env を建てる。
    env = CalligraphyEnv(task="line", config=config)
    env.close()
