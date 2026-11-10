from __future__ import annotations

from pathlib import Path

import scripts.run_gate3_hard_mining as hard
from scripts.search_gate_recovery import Candidate


def _row(character: str, layout: int, **changes: object) -> dict[str, object]:
    row: dict[str, object] = {
        "character": character,
        "layout_index": layout,
        "is_success": True,
        "progress": 1.0,
        "collision_types": [],
        "hard_limit": False,
        "beauty_score": 80.0,
        "beauty_components": {"line_width": 75.0, "brushwork": 75.0},
        "pressure_error_median_abs": 0.05,
        "pressure_error_p90_abs": 0.15,
        "width_ratio_median": 1.0,
        "lost_holes": 0,
    }
    row.update(changes)
    return row


def test_hard_pool_includes_failure_and_same_layout_control() -> None:
    rows = [
        _row("失", 1, pressure_error_p90_abs=0.2),
        _row("対", 1),
        _row("他", 2),
    ]

    selected = hard.select_hard_rows(rows)

    assert {(row["character"], row["layout_index"]) for row in selected} == {
        ("失", 1),
        ("対", 1),
    }


def test_gate3_hard_mining_is_capped_at_500k_and_selected_layouts(tmp_path: Path) -> None:
    command = hard.training_command(
        python=Path("python.exe"),
        parent=Path("model.zip"),
        output=tmp_path / "hard",
        calibration=Path("pressure.json"),
        hard_csv=tmp_path / "hard.csv",
        candidate=Candidate(0.002, 0.45, 0.85),
        layouts=(0, 1),
    )

    assert command[command.index("--timesteps") + 1] == "500000"
    assert command[command.index("--training-layouts") + 1] == "0,1"
    assert command[command.index("--start-stage") + 1] == "9"
    assert command[command.index("--end-stage") + 1] == "9"
