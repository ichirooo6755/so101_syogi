"""Unicode-safe hard-example mining for per-character evaluation rows.

This module intentionally has no dependency on the training environment.  It
accepts dictionaries produced by ``csv.DictReader`` (including the rows from
``characters.csv``), so a future training loop can use it without importing
MuJoCo or Stable-Baselines3.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, replace
import math
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence
import unicodedata

import numpy as np


Row = Mapping[str, object]
MetricThreshold = tuple[str, float]


@dataclass(frozen=True)
class MiningThresholds:
    """Acceptance gates for one evaluated character.

    ``additional_width_minima`` supports score-like width columns, while
    ``additional_width_maxima`` supports error-like columns.  This avoids
    baking a particular future width metric into the mining core.
    """

    completion_progress: float = 1.0
    beauty: float = 60.0
    line_width: float = 65.0
    brushwork: float = 62.0
    maximum_drips: int = 0
    maximum_unintended_ink_fraction: float = 0.05
    additional_width_minima: tuple[MetricThreshold, ...] = ()
    additional_width_maxima: tuple[MetricThreshold, ...] = ()

    def __post_init__(self) -> None:
        minimum_values = (
            self.completion_progress,
            self.beauty,
            self.line_width,
            self.brushwork,
            self.maximum_unintended_ink_fraction,
        )
        if not all(math.isfinite(float(value)) and float(value) >= 0 for value in minimum_values):
            raise ValueError("Mining thresholds must be finite and non-negative")
        if self.maximum_drips < 0:
            raise ValueError("maximum_drips must be non-negative")

        names: list[str] = []
        for name, threshold in (
            *self.additional_width_minima,
            *self.additional_width_maxima,
        ):
            if not name or name == "character":
                raise ValueError("Additional width metric names must be non-empty")
            if not math.isfinite(float(threshold)):
                raise ValueError(f"Threshold for {name!r} must be finite")
            if float(threshold) < 0:
                raise ValueError(f"Threshold for {name!r} must be non-negative")
            names.append(name)
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(
                "Additional width metrics must be unique: " + ", ".join(duplicates)
            )


@dataclass(frozen=True)
class CoverageReport:
    """Exact Unicode coverage comparison between rows and an expected corpus."""

    expected_count: int
    row_count: int
    duplicate_characters: tuple[str, ...] = ()
    missing_characters: tuple[str, ...] = ()
    unexpected_characters: tuple[str, ...] = ()
    duplicate_expected_characters: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return not (
            self.duplicate_characters
            or self.missing_characters
            or self.unexpected_characters
            or self.duplicate_expected_characters
        )


class CoverageError(ValueError):
    """Raised when evaluation rows are not a one-to-one corpus match."""

    def __init__(self, report: CoverageReport) -> None:
        self.report = report
        details: list[str] = []
        for label, values in (
            ("duplicates", report.duplicate_characters),
            ("missing", report.missing_characters),
            ("unexpected", report.unexpected_characters),
            ("expected_duplicates", report.duplicate_expected_characters),
        ):
            if values:
                details.append(f"{label}={''.join(values)}")
        super().__init__("Unicode coverage mismatch: " + ", ".join(details))


@dataclass(frozen=True)
class CharacterAssessment:
    """Gate outcomes and sampling weight for one corpus character."""

    index: int
    character: str
    passed: bool
    checks: Mapping[str, bool]
    values: Mapping[str, float]
    weakest_component: str
    sampling_weight: float = 0.0


@dataclass(frozen=True)
class HardMiningResult:
    """Complete mining output in expected-character order."""

    assessments: tuple[CharacterAssessment, ...]
    failed_indices: tuple[int, ...]
    sampling_weights: np.ndarray
    coverage: CoverageReport

    @property
    def failed_characters(self) -> tuple[str, ...]:
        return tuple(self.assessments[index].character for index in self.failed_indices)

    def sample_indices(
        self,
        count: int,
        *,
        rng: np.random.Generator | int | None = None,
        replace: bool = True,
    ) -> np.ndarray:
        """Draw expected-corpus indices using the mined probabilities."""

        if count < 0:
            raise ValueError("count must be non-negative")
        if not replace and count > len(self.assessments):
            raise ValueError("count cannot exceed corpus size without replacement")
        generator = rng if isinstance(rng, np.random.Generator) else np.random.default_rng(rng)
        return generator.choice(
            len(self.assessments),
            size=count,
            replace=replace,
            p=self.sampling_weights,
        )


def _normalise_character(value: object, *, location: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{location} character must be text")
    character = unicodedata.normalize("NFC", value)
    if len(character) != 1:
        raise ValueError(
            f"{location} must contain exactly one Unicode character, got {value!r}"
        )
    return character


def _normalise_expected(expected_characters: Sequence[str] | str) -> tuple[str, ...]:
    return tuple(
        _normalise_character(character, location=f"expected[{index}]")
        for index, character in enumerate(expected_characters)
    )


def validate_unicode_coverage(
    rows: Iterable[Row],
    expected_characters: Sequence[str] | str,
    *,
    raise_on_error: bool = False,
) -> CoverageReport:
    """Validate NFC-normalised duplicates, missing glyphs, and extras."""

    materialised = tuple(rows)
    expected = _normalise_expected(expected_characters)
    actual = tuple(
        _normalise_character(row.get("character"), location=f"row[{index}]")
        for index, row in enumerate(materialised)
    )

    def duplicates(values: Sequence[str]) -> tuple[str, ...]:
        counts: dict[str, int] = {}
        order: list[str] = []
        for value in values:
            if value not in counts:
                order.append(value)
            counts[value] = counts.get(value, 0) + 1
        return tuple(value for value in order if counts[value] > 1)

    expected_set = set(expected)
    actual_set = set(actual)
    report = CoverageReport(
        expected_count=len(expected),
        row_count=len(actual),
        duplicate_characters=duplicates(actual),
        missing_characters=tuple(value for value in expected if value not in actual_set),
        unexpected_characters=tuple(value for value in actual if value not in expected_set),
        duplicate_expected_characters=duplicates(expected),
    )
    if raise_on_error and not report.valid:
        raise CoverageError(report)
    return report


def _float_value(row: Row, name: str, *, row_index: int) -> float:
    if name not in row:
        raise ValueError(f"row[{row_index}] is missing required column {name!r}")
    try:
        value = float(row[name])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"row[{row_index}] column {name!r} must be numeric, got {row[name]!r}"
        ) from exc
    if not math.isfinite(value):
        raise ValueError(f"row[{row_index}] column {name!r} must be finite")
    return value


def _bool_value(row: Row, name: str, *, row_index: int) -> bool:
    if name not in row:
        raise ValueError(f"row[{row_index}] is missing required column {name!r}")
    value = row[name]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    text = str(value).strip().casefold()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    raise ValueError(
        f"row[{row_index}] column {name!r} must be boolean-like, got {value!r}"
    )


def _has_collision(row: Row, *, row_index: int) -> bool:
    if "collision" not in row:
        raise ValueError(f"row[{row_index}] is missing required column 'collision'")
    value = row["collision"]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    return str(value).strip().casefold() not in {"", "0", "false", "none", "[]"}


def _minimum_score(value: float, threshold: float) -> float:
    if threshold == 0:
        return 1.0 if value >= 0 else 0.0
    return max(0.0, value / threshold)


def _maximum_score(value: float, threshold: float) -> float:
    if value <= threshold:
        return 1.0
    if threshold <= 0:
        return 0.0
    return max(0.0, threshold / value)


def assess_characters(
    rows: Iterable[Row],
    expected_characters: Sequence[str] | str,
    *,
    thresholds: MiningThresholds = MiningThresholds(),
    failure_boost: float = 3.0,
    hardness_scale: float = 4.0,
) -> HardMiningResult:
    """Assess every character and build hard-example sampling probabilities.

    The returned indices always refer to ``expected_characters``, not shard or
    CSV row order.  Any duplicate, missing, or unexpected Unicode character is
    rejected before scores are calculated.
    """

    if not math.isfinite(failure_boost) or failure_boost < 0:
        raise ValueError("failure_boost must be finite and non-negative")
    if not math.isfinite(hardness_scale) or hardness_scale < 0:
        raise ValueError("hardness_scale must be finite and non-negative")

    materialised = tuple(dict(row) for row in rows)
    expected = _normalise_expected(expected_characters)
    coverage = validate_unicode_coverage(
        materialised, expected, raise_on_error=True
    )
    row_by_character = {
        _normalise_character(row["character"], location=f"row[{index}]"): (index, row)
        for index, row in enumerate(materialised)
    }

    assessments: list[CharacterAssessment] = []
    raw_weights: list[float] = []
    quality_names = {"beauty", "line_width", "brushwork"}
    for corpus_index, character in enumerate(expected):
        row_index, row = row_by_character[character]
        success = _bool_value(row, "success", row_index=row_index)
        progress = _float_value(row, "progress", row_index=row_index)
        beauty = _float_value(row, "beauty_score", row_index=row_index)
        line_width = _float_value(row, "line_width", row_index=row_index)
        brushwork = _float_value(row, "brushwork", row_index=row_index)
        drips = _float_value(row, "drip_count", row_index=row_index)
        unintended = _float_value(
            row, "unintended_ink_fraction", row_index=row_index
        )
        collision = _has_collision(row, row_index=row_index)

        completion_ok = success and progress >= thresholds.completion_progress
        safety_ok = (
            drips <= thresholds.maximum_drips
            and not collision
            and unintended <= thresholds.maximum_unintended_ink_fraction
        )
        checks: dict[str, bool] = {
            "completion": completion_ok,
            "safety": safety_ok,
            "beauty": beauty >= thresholds.beauty,
            "line_width": line_width >= thresholds.line_width,
            "brushwork": brushwork >= thresholds.brushwork,
        }
        values: dict[str, float] = {
            "completion": progress,
            "safety": 1.0 if safety_ok else 0.0,
            "beauty": beauty,
            "line_width": line_width,
            "brushwork": brushwork,
        }
        scores: dict[str, float] = {
            "completion": (
                _minimum_score(progress, thresholds.completion_progress)
                if success
                else 0.0
            ),
            "safety": min(
                _maximum_score(drips, float(thresholds.maximum_drips)),
                0.0 if collision else 1.0,
                _maximum_score(
                    unintended, thresholds.maximum_unintended_ink_fraction
                ),
            ),
            "beauty": _minimum_score(beauty, thresholds.beauty),
            "line_width": _minimum_score(line_width, thresholds.line_width),
            "brushwork": _minimum_score(brushwork, thresholds.brushwork),
        }

        for name, threshold in thresholds.additional_width_minima:
            key = f"width:{name}"
            value = _float_value(row, name, row_index=row_index)
            checks[key] = value >= threshold
            values[key] = value
            scores[key] = _minimum_score(value, threshold)
            quality_names.add(key)
        for name, threshold in thresholds.additional_width_maxima:
            key = f"width:{name}"
            value = _float_value(row, name, row_index=row_index)
            checks[key] = value <= threshold
            values[key] = value
            scores[key] = _maximum_score(value, threshold)
            quality_names.add(key)

        failed = [name for name, passed in checks.items() if not passed]
        weakest_pool = failed or [
            name for name in checks if name in quality_names
        ]
        weakest = min(weakest_pool, key=lambda name: scores[name])
        severity = sum(max(0.0, 1.0 - score) for score in scores.values())
        raw_weight = 1.0 + hardness_scale * severity
        if failed:
            raw_weight += failure_boost
        if progress < thresholds.completion_progress:
            raw_weight += failure_boost * 2.0
        raw_weights.append(raw_weight)
        assessments.append(
            CharacterAssessment(
                index=corpus_index,
                character=character,
                passed=not failed,
                checks=MappingProxyType(checks),
                values=MappingProxyType(values),
                weakest_component=weakest,
            )
        )

    weights = np.asarray(raw_weights, dtype=np.float64)
    weights /= weights.sum()
    weights.setflags(write=False)
    weighted_assessments = tuple(
        replace(assessment, sampling_weight=float(weights[index]))
        for index, assessment in enumerate(assessments)
    )
    failed_indices = tuple(
        assessment.index for assessment in weighted_assessments if not assessment.passed
    )
    return HardMiningResult(
        assessments=weighted_assessments,
        failed_indices=failed_indices,
        sampling_weights=weights,
        coverage=coverage,
    )


def _read_character_csv(
    path: str | Path,
) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    source = Path(path)
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {source}")
        fieldnames = tuple(reader.fieldnames)
        if len(set(fieldnames)) != len(fieldnames):
            raise ValueError(f"CSV has duplicate columns: {source}")
        if "character" not in fieldnames:
            raise ValueError(f"CSV is missing 'character' column: {source}")
        return fieldnames, tuple(dict(row) for row in reader)


def read_character_csv(path: str | Path) -> tuple[dict[str, str], ...]:
    """Read one ``characters.csv``-compatible file."""

    return _read_character_csv(path)[1]


def merge_shard_csvs(
    shard_paths: Sequence[str | Path],
    expected_characters: Sequence[str] | str,
    *,
    output_path: str | Path | None = None,
) -> tuple[dict[str, str], ...]:
    """Merge, validate, and corpus-order evaluation shard CSV files.

    Shards must have identical schemas.  Validation happens before an optional
    output file is written, so an invalid partial evaluation cannot replace a
    previously valid merged file.
    """

    if not shard_paths:
        raise ValueError("At least one shard path is required")
    expected = _normalise_expected(expected_characters)
    fieldnames: tuple[str, ...] | None = None
    merged: list[dict[str, str]] = []
    for shard_path in shard_paths:
        shard_fields, rows = _read_character_csv(shard_path)
        if fieldnames is None:
            fieldnames = shard_fields
        elif shard_fields != fieldnames:
            raise ValueError(
                f"Shard schema mismatch: {Path(shard_path)} has "
                f"{shard_fields!r}, expected {fieldnames!r}"
            )
        merged.extend(rows)

    validate_unicode_coverage(merged, expected, raise_on_error=True)
    by_character: dict[str, dict[str, str]] = {}
    for index, row in enumerate(merged):
        character = _normalise_character(
            row["character"], location=f"merged row[{index}]"
        )
        canonical_row = dict(row)
        canonical_row["character"] = character
        by_character[character] = canonical_row
    ordered = tuple(by_character[character] for character in expected)

    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        assert fieldnames is not None
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(ordered)
    return ordered


__all__ = [
    "CharacterAssessment",
    "CoverageError",
    "CoverageReport",
    "HardMiningResult",
    "MiningThresholds",
    "assess_characters",
    "merge_shard_csvs",
    "read_character_csv",
    "validate_unicode_coverage",
]
