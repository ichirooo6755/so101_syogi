from __future__ import annotations

from so101_calligraphy.training.model_selection import (
    regression_reasons,
    select_best,
    snapshot_from_evaluation,
)


def evaluation(
    *,
    robust: float,
    width: float = 68.0,
    brushwork: float = 63.0,
    harai: float = 66.0,
    minimum: float = 72.0,
    collisions: int = 0,
) -> dict[str, object]:
    return {
        "success_rate": 1.0,
        "mean_beauty_score": 79.0,
        "p10_beauty_score": 77.0,
        "minimum_beauty_score": minimum,
        "robust_score": robust,
        "total_drips": 0,
        "collision_count": collisions,
        "component_means": {
            "line_width": width,
            "brushwork": brushwork,
            "glyph_shape": 50.0,
        },
        "technique_means": {"harai": {"finish": harai}},
    }


def test_safety_outranks_higher_robust_score() -> None:
    safe = snapshot_from_evaluation(evaluation(robust=78.0), source="safe")
    unsafe = snapshot_from_evaluation(
        evaluation(robust=90.0, collisions=1), source="unsafe"
    )
    assert select_best([unsafe, safe]) == safe


def test_regression_guard_keeps_baseline() -> None:
    baseline = snapshot_from_evaluation(evaluation(robust=78.0), source="baseline")
    candidate = snapshot_from_evaluation(
        evaluation(robust=82.0, brushwork=58.0), source="candidate"
    )
    assert regression_reasons(candidate, baseline) == ("brushwork",)
    assert select_best([candidate], baseline=baseline) == baseline


def test_regression_guard_rejects_harai_or_glyph_shape_drop() -> None:
    baseline = snapshot_from_evaluation(evaluation(robust=78.0), source="baseline")
    weak_harai = snapshot_from_evaluation(
        evaluation(robust=82.0, harai=60.0), source="weak-harai"
    )
    weak_glyph = snapshot_from_evaluation(
        {
            **evaluation(robust=82.0),
            "component_means": {
                "line_width": 68.0,
                "brushwork": 63.0,
                "glyph_shape": 40.0,
            },
        },
        source="weak-glyph",
    )
    assert regression_reasons(weak_harai, baseline) == ("harai_finish",)
    assert regression_reasons(weak_glyph, baseline) == ("glyph_shape",)
    assert select_best([weak_harai, weak_glyph], baseline=baseline) == baseline


def test_more_quality_gates_outrank_small_robust_gain() -> None:
    gated = snapshot_from_evaluation(evaluation(robust=78.0), source="gated")
    weak_harai = snapshot_from_evaluation(
        evaluation(robust=79.0, harai=60.0), source="weak"
    )
    assert select_best([weak_harai, gated]) == gated
