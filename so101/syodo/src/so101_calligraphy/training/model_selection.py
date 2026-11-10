"""Transparent model-selection rules for professional calligraphy runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class QualitySnapshot:
    source: str
    success_rate: float
    mean_beauty: float
    p10_beauty: float
    minimum_beauty: float
    robust_score: float
    line_width: float
    brushwork: float
    harai_finish: float
    glyph_shape: float
    drips: int
    collisions: int

    @property
    def safe(self) -> bool:
        return (
            self.success_rate == 1.0
            and self.drips == 0
            and self.collisions == 0
        )

    @property
    def gates_passed(self) -> int:
        return sum(
            (
                self.mean_beauty >= 75.0,
                self.minimum_beauty >= 60.0,
                self.line_width >= 65.0,
                self.brushwork >= 62.0,
                self.harai_finish >= 65.0,
            )
        )

    @property
    def rank(self) -> tuple[int, int, float, float, float]:
        """Lexicographic rank: safety and gates outrank small score gains."""

        return (
            int(self.safe),
            self.gates_passed,
            self.robust_score,
            self.p10_beauty,
            self.minimum_beauty,
        )


def snapshot_from_evaluation(
    evaluation: Mapping[str, object], *, source: str = ""
) -> QualitySnapshot:
    components = evaluation.get("component_means", {})
    if not isinstance(components, Mapping):
        components = {}
    techniques = evaluation.get("technique_means", {})
    if not isinstance(techniques, Mapping):
        techniques = {}
    harai = techniques.get("harai", {})
    if not isinstance(harai, Mapping):
        harai = {}
    mean = float(evaluation.get("mean_beauty_score", 0.0))
    p10 = float(evaluation.get("p10_beauty_score", mean))
    minimum = float(evaluation.get("minimum_beauty_score", p10))
    robust = float(
        evaluation.get(
            "robust_score",
            0.55 * mean + 0.25 * p10 + 0.20 * minimum,
        )
    )
    return QualitySnapshot(
        source=source,
        success_rate=float(evaluation.get("success_rate", 0.0)),
        mean_beauty=mean,
        p10_beauty=p10,
        minimum_beauty=minimum,
        robust_score=robust,
        line_width=float(components.get("line_width", 0.0)),
        brushwork=float(components.get("brushwork", 0.0)),
        harai_finish=float(harai.get("finish", 0.0)),
        glyph_shape=float(components.get("glyph_shape", 0.0)),
        drips=int(evaluation.get("total_drips", 0)),
        collisions=int(evaluation.get("collision_count", 0)),
    )


def load_snapshot(path: Path) -> QualitySnapshot:
    payload = json.loads(path.read_text(encoding="utf-8"))
    evaluation = payload.get("evaluation", payload)
    if not isinstance(evaluation, Mapping):
        raise ValueError(f"Evaluation is not an object: {path}")
    return snapshot_from_evaluation(evaluation, source=str(path))


def regression_reasons(
    candidate: QualitySnapshot,
    baseline: QualitySnapshot,
    *,
    beauty_tolerance: float = 0.5,
    component_tolerance: float = 1.0,
) -> tuple[str, ...]:
    failures: list[str] = []
    if not candidate.safe:
        failures.append("safety")
    if candidate.p10_beauty < baseline.p10_beauty - beauty_tolerance:
        failures.append("p10_beauty")
    if candidate.minimum_beauty < baseline.minimum_beauty - beauty_tolerance:
        failures.append("minimum_beauty")
    if candidate.line_width < baseline.line_width - component_tolerance:
        failures.append("line_width")
    if candidate.brushwork < baseline.brushwork - component_tolerance:
        failures.append("brushwork")
    if candidate.harai_finish < baseline.harai_finish - component_tolerance:
        failures.append("harai_finish")
    if candidate.glyph_shape < baseline.glyph_shape - component_tolerance:
        failures.append("glyph_shape")
    return tuple(failures)


def select_best(
    candidates: Sequence[QualitySnapshot],
    *,
    baseline: QualitySnapshot | None = None,
) -> QualitySnapshot:
    if not candidates:
        raise ValueError("At least one candidate is required.")
    eligible = list(candidates)
    if baseline is not None:
        non_regressing = [
            candidate
            for candidate in candidates
            if not regression_reasons(candidate, baseline)
        ]
        if non_regressing:
            eligible = non_regressing
        else:
            return baseline
    return max(eligible, key=lambda candidate: candidate.rank)
