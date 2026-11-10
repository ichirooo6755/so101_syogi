from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from so101_calligraphy.config import EnvConfig, PaperConfig
from so101_calligraphy.trajectory.clearance import (
    CONTACT_REQUIRED_PRESSURE,
    apply_clearance_caps,
    designed_contact,
    exposed_horizontal_endpoints,
)
from so101_calligraphy.brushwork import make_brushwork_planner
from so101_calligraphy.trajectory.primitives import primitive_trajectory
from so101_calligraphy.trajectory.profile import build_stroke_profile
from so101_calligraphy.trajectory.sequence import build_waypoint_sequence
from so101_calligraphy.trajectory.svg import load_svg_trajectory
from so101_calligraphy.trajectory.types import Stroke


def test_primitive_curriculum_shapes() -> None:
    assert len(primitive_trajectory("line").strokes) == 1
    assert len(primitive_trajectory("circle").strokes) == 1
    assert len(primitive_trajectory("cross").strokes) == 2


def test_cross_inserts_ordered_pen_up_transition() -> None:
    config = EnvConfig()
    trajectory = primitive_trajectory("cross", spacing=config.path_spacing)
    sequence = build_waypoint_sequence(
        trajectory,
        pen_down_z=config.pen_down_z,
        safe_height=config.safe_height,
        transition_spacing=config.transition_spacing,
    )

    first_stroke_end = max(
        index
        for index, stroke_index in enumerate(sequence.stroke_indices)
        if stroke_index == 0 and sequence.pen_down[index]
    )
    second_stroke_start = min(
        index
        for index, stroke_index in enumerate(sequence.stroke_indices)
        if stroke_index == 1 and sequence.pen_down[index]
    )
    between = slice(first_stroke_end + 1, second_stroke_start)
    assert not sequence.pen_down[between].any()
    assert {"lift", "travel", "lower"}.issubset(set(sequence.phases[between]))
    assert sequence.positions[between, 2].max() == pytest.approx(config.safe_height)


def test_entry_descent_is_shallow_without_duplicate_pen_down_points() -> None:
    config = EnvConfig()
    trajectory = primitive_trajectory("line", spacing=config.path_spacing)
    ratio = 0.55
    sequence = build_waypoint_sequence(
        trajectory,
        pen_down_z=config.pen_down_z,
        safe_height=config.safe_height,
        transition_spacing=config.transition_spacing,
        brush=config.brush,
        brushwork_mode="professional",
        entry_descent_ratio=ratio,
    )
    baseline = build_waypoint_sequence(
        trajectory,
        pen_down_z=config.pen_down_z,
        safe_height=config.safe_height,
        transition_spacing=config.transition_spacing,
        brush=config.brush,
        brushwork_mode="professional",
    )
    down = np.flatnonzero(sequence.pen_down)
    baseline_down = np.flatnonzero(baseline.pen_down)
    lower = down[0] - 1

    assert sequence.target_pressure[down[0]] == pytest.approx(
        baseline.target_pressure[baseline_down[0]] * ratio
    )
    assert sequence.target_width[down[0]] <= baseline.target_width[baseline_down[0]]
    assert sequence.phases[lower] == "lower"
    assert sequence.positions[lower, :2] == pytest.approx(
        sequence.positions[down[0], :2]
    )
    assert sequence.positions[lower, 2] > sequence.positions[down[0], 2]
    assert np.all(
        np.linalg.norm(np.diff(sequence.positions[down, :2], axis=0), axis=1) > 0
    )


@pytest.mark.parametrize("ratio", [0.0, -0.1, 1.01])
def test_entry_descent_ratio_must_be_a_fraction(ratio: float) -> None:
    config = EnvConfig()
    with pytest.raises(ValueError, match="entry_descent_ratio"):
        build_waypoint_sequence(
            primitive_trajectory("line"),
            pen_down_z=config.pen_down_z,
            safe_height=config.safe_height,
            entry_descent_ratio=ratio,
        )


def test_five_mm_junction_tolerance_separates_only_unplanned_contacts() -> None:
    horizontal = Stroke(np.asarray([[0.0, 0.0], [0.04, 0.0]]))
    parallel = Stroke(np.asarray([[0.0, 0.006], [0.04, 0.006]]))
    crossing = Stroke(np.asarray([[0.02, -0.01], [0.02, 0.01]]))
    t_join = Stroke(np.asarray([[0.02, 0.004], [0.02, 0.02]]))

    assert not designed_contact(
        (horizontal, parallel), junction_tolerance=0.005
    )[0, 1]
    assert designed_contact((horizontal, crossing), junction_tolerance=0.005)[0, 1]
    assert designed_contact((horizontal, t_join), junction_tolerance=0.005)[0, 1]


def test_only_visible_horizontal_ends_receive_triangle_control() -> None:
    horizontal = Stroke(
        np.asarray([[-0.03, 0.0], [0.03, 0.0]]),
        stroke_type="㇐",
        technique="tome",
    )
    crossing = Stroke(
        np.asarray([[0.0, -0.03], [0.0, 0.03]]),
        stroke_type="㇑",
    )
    joined_left = Stroke(
        np.asarray([[-0.03, 0.0], [-0.03, 0.03]]),
        stroke_type="㇑",
    )

    cross = exposed_horizontal_endpoints(
        (horizontal, crossing), junction_tolerance=0.005
    )
    t_join = exposed_horizontal_endpoints(
        (horizontal, joined_left), junction_tolerance=0.005
    )

    assert cross[0].tolist() == [True, True]
    assert t_join[0].tolist() == [False, True]


def test_probe_width_p90_tightens_only_local_clearance_without_erasing_strokes() -> None:
    points = np.column_stack((np.linspace(0.0, 0.04, 20), np.zeros(20)))
    strokes = (
        Stroke(points, stroke_type="㇐"),
        Stroke(points + np.asarray([0.0, 0.010]), stroke_type="㇐"),
    )
    brush = EnvConfig().brush
    planner = make_brushwork_planner("professional")
    profiles = tuple(planner.plan(stroke, brush) for stroke in strokes)
    baseline = apply_clearance_caps(
        strokes,
        profiles,
        brush,
        junction_tolerance=0.005,
        minimum_gap=0.0015,
        floor_ratio=0.45,
    )
    calibrated = apply_clearance_caps(
        strokes,
        profiles,
        brush,
        junction_tolerance=0.005,
        minimum_gap=0.0015,
        floor_ratio=0.45,
        observed_width_p90_by_phase={"send": 0.009},
    )

    assert np.median(calibrated[0].width) < np.median(baseline[0].width)
    assert np.median(calibrated[0].width / profiles[0].width) >= 0.90


def test_impossible_clearance_uses_minimum_tip_without_erasing_strokes() -> None:
    points = np.column_stack((np.linspace(0.0, 0.04, 12), np.zeros(12)))
    strokes = (
        Stroke(points, stroke_type="㇐", technique="tome"),
        Stroke(points + np.asarray([0.0, 0.008]), stroke_type="㇐", technique="tome"),
    )
    brush = replace(EnvConfig().brush, minimum_width=0.0063, maximum_width=0.024)
    planner = make_brushwork_planner("professional")
    profiles = tuple(planner.plan(stroke, brush) for stroke in strokes)

    capped = apply_clearance_caps(
        strokes,
        profiles,
        brush,
        junction_tolerance=0.005,
        minimum_gap=0.003,
        floor_ratio=0.25,
    )

    for original, adjusted in zip(profiles, capped, strict=True):
        required = np.asarray(original.pressure) > CONTACT_REQUIRED_PRESSURE
        assert required.any()
        assert np.all(
            np.asarray(adjusted.pressure)[required] > CONTACT_REQUIRED_PRESSURE
        )
        assert np.all(np.asarray(adjusted.pressure) <= np.asarray(original.pressure))


def test_svg_document_order_spacing_and_a4_fit(tmp_path) -> None:
    svg = tmp_path / "ordered.svg"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <line x1="10" y1="20" x2="90" y2="20" />
        <g transform="translate(10 0)">
          <path d="M 40 30 L 40 90" />
        </g>
        </svg>""",
        encoding="utf-8",
    )
    paper = PaperConfig()
    trajectory = load_svg_trajectory(svg, paper=paper, spacing=0.01)

    assert len(trajectory.strokes) == 2
    first, second = trajectory.strokes
    assert np.ptp(first.points[:, 0]) > np.ptp(first.points[:, 1])
    assert np.ptp(second.points[:, 1]) > np.ptp(second.points[:, 0])
    for stroke in trajectory.strokes:
        distances = np.linalg.norm(np.diff(stroke.points, axis=0), axis=1)
        assert np.all(distances <= 0.0101)
        assert np.all(distances > 0)
        assert paper.center_x - paper.width / 2 <= stroke.points[:, 0].min()
        assert stroke.points[:, 0].max() <= paper.center_x + paper.width / 2
        assert paper.center_y - paper.height / 2 <= stroke.points[:, 1].min()
        assert stroke.points[:, 1].max() <= paper.center_y + paper.height / 2


def test_svg_rejects_empty_drawing(tmp_path) -> None:
    svg = tmp_path / "empty.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    with pytest.raises(ValueError, match="no drawable"):
        load_svg_trajectory(svg)


def test_unknown_primitive_has_actionable_error() -> None:
    with pytest.raises(ValueError, match="line, circle, cross"):
        primitive_trajectory("永")


def test_calligraphic_finish_profiles() -> None:
    points = np.column_stack((np.linspace(0.0, 0.1, 20), np.zeros(20)))
    tome = build_stroke_profile(
        primitive_trajectory("line").strokes[0]
    )
    hane = build_stroke_profile(Stroke(points, technique="hane"))
    harai = build_stroke_profile(Stroke(points, technique="harai"))
    assert tome.technique == "tome"
    assert tome.pressure[-1] > tome.pressure[len(tome.pressure) // 2]
    assert tome.speed[-1] < tome.speed[len(tome.speed) // 2]
    assert hane.pressure[-1] < hane.pressure[-4]
    assert harai.width[-1] < harai.width[len(harai.width) // 2]
    assert harai.speed[-1] > harai.speed[len(harai.speed) // 2]


def test_svg_preserves_technique_metadata(tmp_path) -> None:
    svg = tmp_path / "technique.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><path '
        'data-technique="harai" d="M0 0 L100 20"/></svg>',
        encoding="utf-8",
    )
    stroke = load_svg_trajectory(svg).strokes[0]
    assert stroke.technique == "harai"
