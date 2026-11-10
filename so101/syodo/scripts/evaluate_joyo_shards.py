"""Evaluate all joyo kanji in parallel shards and merge their results."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
import csv
from datetime import datetime
import gzip
import json
import math
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Any
import urllib.error
import urllib.request
import xml.etree.ElementTree as etree

import numpy as np


JOYO_COUNT = 2_136
JOYO_GRADES = {1, 2, 3, 4, 5, 6, 8}
EXPECTED_GRADE_COUNTS = {1: 80, 2: 160, 3: 200, 4: 202, 5: 193, 6: 191, 8: 1_110}
KANJIDIC2_URL = "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz"


def make_command(
    *,
    model: Path | None,
    output: Path,
    shards: int,
    shard_index: int,
    device: str,
    seed: int,
    exemplar_font: Path | None = None,
    eval_limit: int = 0,
    pressure_calibration: Path | None = None,
    eval_layouts: Sequence[int] = tuple(range(6)),
    brushmark_layout: bool = False,
    center110_profile: str | None = None,
) -> list[str]:
    """Build one complete professional-evaluation command."""

    command = [
        sys.executable,
        "-m",
        "so101_calligraphy.training.professional",
        "--expert-only",
        "--output",
        str(output),
        "--eval-limit",
        str(eval_limit),
        "--eval-shard-count",
        str(shards),
        "--eval-shard-index",
        str(shard_index),
        "--save-all-ink",
        "--eval-layouts",
        ",".join(str(layout) for layout in eval_layouts),
        "--device",
        device,
        "--seed",
        str(seed),
    ]
    if model is not None:
        command.extend(["--initial-model", str(model)])
    if brushmark_layout:
        command.append("--brushmark-layout")
    if center110_profile is not None:
        command.extend(["--center110-profile", center110_profile])
    if exemplar_font is not None:
        command.extend(["--exemplar-font", str(exemplar_font)])
    if pressure_calibration is not None:
        command.extend(
            [
                "--pressure-calibration",
                str(pressure_calibration),
                "--require-pressure-calibration",
            ]
        )
    return command


def validate_evaluation_shape(
    *,
    count: int,
    unique_character_count: int,
    layout_count: int,
    full: bool,
    layouts: Sequence[int] = tuple(range(6)),
) -> None:
    """Reject incomplete full evaluations before they can be reported as final."""

    expected_characters = JOYO_COUNT if full else unique_character_count
    expected_layouts = tuple(layouts)
    if not expected_layouts or len(set(expected_layouts)) != len(expected_layouts):
        raise ValueError("Expected layouts must be non-empty and unique.")
    expected_rows = expected_characters * len(expected_layouts)
    if (
        unique_character_count != expected_characters
        or layout_count != len(expected_layouts)
        or count != expected_rows
    ):
        raise ValueError(
            f"Evaluation must contain {expected_rows:,} rows "
            f"({expected_characters:,} unique characters x "
            f"{len(expected_layouts)} layouts); "
            f"got rows={count:,}, unique={unique_character_count:,}, layouts={layout_count}."
        )


def _evaluation(summary: Mapping[str, Any]) -> Mapping[str, Any]:
    value = summary.get("evaluation", summary)
    if not isinstance(value, Mapping):
        raise ValueError("Shard summary has no evaluation mapping.")
    return value


def _codepoint(character: str) -> str:
    if len(character) == 1:
        return f"U+{ord(character):04X} ({character})"
    return repr(character)


def _float(row: Mapping[str, str], name: str) -> float:
    try:
        value = float(row[name])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric column {name!r} for {row.get('character')!r}.") from exc
    if not math.isfinite(value):
        raise ValueError(f"Non-finite {name!r} for {row.get('character')!r}.")
    return value


def _int(row: Mapping[str, str], name: str) -> int:
    value = _float(row, name)
    if not value.is_integer():
        raise ValueError(f"Non-integral {name!r} for {row.get('character')!r}.")
    return int(value)


def _row_float(row: Mapping[str, str], name: str, default: float = 0.0) -> float:
    raw = row.get(name, default)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(default)


def build_calligrapher_acceptance(
    evaluation: Mapping[str, Any],
    rows: Sequence[Mapping[str, str]],
) -> dict[str, bool]:
    """Strict machine gates (C). Visual calligrapher sign-off (A) is separate.

    Beauty-only acceptance previously skipped hard-mining while thousands of
    glyphs still missed line_width / brushwork gates.
    """

    components = evaluation.get("component_means", {})
    if not isinstance(components, Mapping):
        components = {}
    techniques = evaluation.get("technique_means", {})
    if not isinstance(techniques, Mapping):
        techniques = {}
    harai = techniques.get("harai") if isinstance(techniques.get("harai"), Mapping) else None

    per_char_ok = 0
    for row in rows:
        if (
            _row_float(row, "line_width") >= 65.0
            and _row_float(row, "brushwork") >= 62.0
        ):
            per_char_ok += 1
    per_char_fraction = (per_char_ok / len(rows)) if rows else 0.0

    acceptance = {
        "mean_at_least_75": float(evaluation["mean_beauty_score"]) >= 75.0,
        "mean_at_least_80": float(evaluation["mean_beauty_score"]) >= 80.0,
        "p10_at_least_80": float(evaluation["p10_beauty_score"]) >= 80.0,
        "minimum_at_least_60": float(evaluation["minimum_beauty_score"]) >= 60.0,
        "all_complete": float(evaluation["success_rate"]) == 1.0,
        "zero_drips": int(evaluation["total_drips"]) == 0,
        "zero_collisions": int(evaluation["collision_count"]) == 0,
        "mean_line_width_at_least_65": float(components.get("line_width", 0.0)) >= 65.0,
        "mean_brushwork_at_least_62": float(components.get("brushwork", 0.0)) >= 62.0,
        "per_char_lw_bw_pass_fraction_at_least_95": per_char_fraction >= 0.95,
        # Log-only tracking for visual A; not a hard-mining skip gate yet.
        "mean_glyph_shape_at_least_50": float(components.get("glyph_shape", 0.0)) >= 50.0,
    }
    if harai is not None and "finish" in harai:
        acceptance["mean_harai_finish_at_least_65"] = float(harai["finish"]) >= 65.0
    return acceptance


def merge_shards(
    rows_by_shard: Sequence[Sequence[Mapping[str, str]]],
    summaries: Sequence[Mapping[str, Any]],
    expected_characters: Sequence[str],
    layouts: Sequence[int] = tuple(range(6)),
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Purely validate and merge already-loaded shard rows and summaries."""

    if not rows_by_shard or len(rows_by_shard) != len(summaries):
        raise ValueError("Shard rows and summaries must be non-empty and have equal lengths.")

    expected = tuple(expected_characters)
    expected_counts = Counter(expected)
    repeated_expected = [character for character, count in expected_counts.items() if count > 1]
    if repeated_expected:
        raise ValueError(
            "Expected character list contains duplicates: "
            + ", ".join(_codepoint(character) for character in repeated_expected)
        )
    if any(len(character) != 1 for character in expected):
        raise ValueError("Every expected character must be exactly one Unicode code point.")

    rows = [dict(row) for shard_rows in rows_by_shard for row in shard_rows]
    characters: list[str] = []
    has_layouts = any("layout_index" in row for row in rows)
    requested_layouts = tuple(int(layout) for layout in layouts)
    if (
        not requested_layouts
        or len(set(requested_layouts)) != len(requested_layouts)
        or any(not 0 <= layout < 6 for layout in requested_layouts)
    ):
        raise ValueError("Layouts must contain unique values in 0..5.")
    # Old test/result CSVs without layout_index represent one logical layout.
    effective_layouts = requested_layouts if has_layouts else (0,)
    keys: list[tuple[str, int]] = []
    for row in rows:
        character = row.get("character", "")
        if len(character) != 1:
            raise ValueError(
                f"CSV character must be exactly one Unicode code point, got {character!r}."
            )
        characters.append(character)
        if has_layouts:
            layout_index = _int(row, "layout_index")
            if layout_index not in effective_layouts:
                raise ValueError(f"Invalid layout_index={layout_index} for {character!r}.")
            keys.append((character, layout_index))

    expected_keys = (
        [(character, layout) for character in expected for layout in effective_layouts]
        if has_layouts
        else [(character, 0) for character in expected]
    )
    actual_keys = keys if has_layouts else [(character, 0) for character in characters]
    actual_counts = Counter(actual_keys)
    duplicates = [key for key, count in actual_counts.items() if count > 1]
    missing = [key for key in expected_keys if key not in actual_counts]
    expected_key_set = set(expected_keys)
    unexpected = [key for key in actual_counts if key not in expected_key_set]
    problems: list[str] = []
    if duplicates:
        problems.append(
            "duplicates="
            + ", ".join(
                f"{_codepoint(character)}@{layout}" for character, layout in duplicates
            )
        )
    if missing:
        problems.append(
            "missing="
            + ", ".join(
                f"{_codepoint(character)}@{layout}" for character, layout in missing
            )
        )
    if unexpected:
        problems.append(
            "unexpected="
            + ", ".join(
                f"{_codepoint(key[0])}@{key[1]}"
                for key in unexpected
            )
        )
    if problems:
        raise ValueError("Unicode coverage validation failed: " + "; ".join(problems))

    evaluations = [_evaluation(summary) for summary in summaries]
    for index, (shard_rows, evaluation) in enumerate(zip(rows_by_shard, evaluations)):
        try:
            reported_count = int(evaluation["count"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Shard {index} has an invalid evaluation count.") from exc
        if reported_count != len(shard_rows):
            raise ValueError(
                f"Shard {index} reports {reported_count} rows but CSV has {len(shard_rows)}."
            )

    order = {character: index for index, character in enumerate(expected)}
    rows.sort(
        key=lambda row: (
            order[row["character"]],
            int(row.get("layout_index", 0)),
        )
    )
    beauty = np.asarray([_float(row, "beauty_score") for row in rows], dtype=np.float64)
    endpoint_count = sum(int(row.get("endpoint_triangle_count", "0") or 0) for row in rows)
    endpoint_rows = [
        row for row in rows if int(row.get("endpoint_triangle_count", "0") or 0) > 0
    ]
    component_names = tuple(_evaluation(summaries[0]).get("component_means", {}))
    if not component_names:
        raise ValueError("Shard summaries contain no component means.")
    for index, evaluation in enumerate(evaluations):
        if set(evaluation.get("component_means", {})) != set(component_names):
            raise ValueError(f"Shard {index} has inconsistent component names.")

    ablations = {str(evaluation.get("ablation", "")) for evaluation in evaluations}
    if len(ablations) != 1:
        raise ValueError("Shard summaries have inconsistent ablations.")

    technique_names = sorted(
        {
            str(name)
            for evaluation in evaluations
            for name in evaluation.get("technique_means", {})
        }
    )
    technique_means: dict[str, dict[str, float | int]] = {}
    for technique in technique_names:
        count = 0
        weighted_finish = 0.0
        weighted_width = 0.0
        for evaluation in evaluations:
            values = evaluation.get("technique_means", {}).get(technique)
            if values is None:
                continue
            shard_count = int(values["count"])
            if shard_count < 0:
                raise ValueError(f"Technique {technique!r} has a negative count.")
            count += shard_count
            weighted_finish += shard_count * float(values["finish"])
            weighted_width += shard_count * float(values["width"])
        if count:
            technique_means[technique] = {
                "count": count,
                "finish": weighted_finish / count,
                "width": weighted_width / count,
            }

    result: dict[str, Any] = {
        "ablation": ablations.pop(),
        "count": len(rows),
        "unique_character_count": len(set(characters)),
        "layout_count": len(effective_layouts),
        "success_rate": float(np.mean([_int(row, "success") for row in rows])),
        "mean_beauty_score": float(np.mean(beauty)),
        "p10_beauty_score": float(np.percentile(beauty, 10)),
        "minimum_beauty_score": float(np.min(beauty)),
        "total_drips": sum(_int(row, "drip_count") for row in rows),
        "collision_count": sum(bool(row.get("collision", "")) for row in rows),
        "endpoint_triangle": {
            "count": endpoint_count,
            "mean": (
                sum(float(row.get("endpoint_triangle_sum", "0") or 0.0) for row in rows)
                / endpoint_count
                if endpoint_count
                else 100.0
            ),
            "minimum": (
                min(
                    float(row.get("endpoint_triangle_minimum", "100") or 100.0)
                    for row in endpoint_rows
                )
                if endpoint_rows
                else 100.0
            ),
        },
        "component_means": {
            name: float(np.mean([_float(row, name) for row in rows]))
            for name in component_names
        },
        "component_minimums": {
            name: float(np.min([_float(row, name) for row in rows]))
            for name in component_names
        },
        "technique_means": technique_means,
    }
    layout_summaries: dict[str, dict[str, float | int]] = {}
    if has_layouts:
        for layout in effective_layouts:
            layout_beauty = np.asarray(
                [
                    _float(row, "beauty_score")
                    for row in rows
                    if _int(row, "layout_index") == layout
                ],
                dtype=np.float64,
            )
            layout_summaries[str(layout)] = {
                "count": int(layout_beauty.size),
                "mean_beauty_score": float(np.mean(layout_beauty)),
                "p10_beauty_score": float(np.percentile(layout_beauty, 10)),
            }
    result["layout_summaries"] = layout_summaries

    calibration_values = [summary.get("pressure_calibration") for summary in summaries]
    present_calibrations = [value for value in calibration_values if value is not None]
    if present_calibrations:
        if len(present_calibrations) != len(summaries) or any(
            value != present_calibrations[0] for value in present_calibrations[1:]
        ):
            raise ValueError("Shard summaries have inconsistent pressure calibrations.")
        result["pressure_calibration"] = present_calibrations[0]
    sample_count = sum(
        _int(row, "pressure_calibration_sample_count")
        if "pressure_calibration_sample_count" in row
        else 0
        for row in rows
    )
    clipped_count = sum(
        _int(row, "pressure_calibration_clipped_count")
        if "pressure_calibration_clipped_count" in row
        else 0
        for row in rows
    )
    fallback_count = sum(
        _int(row, "pressure_calibration_fallback_count")
        if "pressure_calibration_fallback_count" in row
        else 0
        for row in rows
    )
    result.update(
        {
            "pressure_calibration_sample_count": sample_count,
            "pressure_calibration_clipped_count": clipped_count,
            "pressure_calibration_fallback_count": fallback_count,
            "pressure_calibration_clip_rate": (
                clipped_count / sample_count if sample_count else 0.0
            ),
            "pressure_calibration_fallback_rate": (
                fallback_count / sample_count if sample_count else 0.0
            ),
        }
    )
    result["robust_score"] = float(
        0.55 * result["mean_beauty_score"]
        + 0.25 * result["p10_beauty_score"]
        + 0.20 * result["minimum_beauty_score"]
        - 2.0 * result["total_drips"] / len(rows)
        - 5.0 * result["collision_count"] / len(rows)
    )
    return rows, result


def _download_kanjidic2(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.{os.getpid()}.tmp")
    request = urllib.request.Request(
        KANJIDIC2_URL,
        headers={"User-Agent": "so101-calligraphy/0.5"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            temporary.write_bytes(response.read())
        with gzip.open(temporary, "rb") as handle:
            etree.parse(handle)
        temporary.replace(target)
    except (OSError, etree.ParseError, urllib.error.URLError) as exc:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Could not fetch KANJIDIC2: {exc}") from exc


def load_expected_joyo(
    cache_path: Path = Path("data/kanjidic2/kanjidic2.xml.gz"),
) -> tuple[str, ...]:
    """Load the exact ordered 2,136-character set used by professional.py."""

    cache_path = cache_path.expanduser().resolve()
    if not cache_path.exists():
        _download_kanjidic2(cache_path)
    try:
        with gzip.open(cache_path, "rb") as handle:
            root = etree.parse(handle).getroot()
    except (OSError, etree.ParseError) as exc:
        raise ValueError(f"Invalid KANJIDIC2 cache {cache_path}: {exc}") from exc

    entries: list[tuple[int, int, str]] = []
    for element in root.findall("character"):
        grade_text = element.findtext("misc/grade")
        if grade_text is None or int(grade_text) not in JOYO_GRADES:
            continue
        character = element.findtext("literal")
        stroke_text = element.findtext("misc/stroke_count")
        if character is None or stroke_text is None:
            raise ValueError("KANJIDIC2 joyo entry is incomplete.")
        entries.append((int(grade_text), int(stroke_text), character))

    grade_counts = Counter(grade for grade, _, _ in entries)
    if dict(sorted(grade_counts.items())) != EXPECTED_GRADE_COUNTS:
        raise ValueError(
            f"KANJIDIC2 grade counts are {dict(sorted(grade_counts.items()))}, "
            f"expected {EXPECTED_GRADE_COUNTS}."
        )
    entries.sort()
    characters = tuple(character for _, _, character in entries)
    if len(characters) != JOYO_COUNT:
        raise ValueError(f"Expected {JOYO_COUNT} joyo characters, found {len(characters)}.")
    return characters


def sample_expected_joyo(characters: Sequence[str], count: int) -> tuple[str, ...]:
    """Mirror professional._sample_indices without importing its heavy stack."""

    if count <= 0 or count >= len(characters):
        return tuple(characters)
    positions = np.linspace(0, len(characters) - 1, count).round().astype(int)
    return tuple(characters[position] for position in positions)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError(f"CSV has no header: {path}")
            return list(reader.fieldnames), list(reader)
    except OSError as exc:
        raise ValueError(f"Could not read shard CSV {path}: {exc}") from exc


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read shard summary {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Shard summary must be a JSON object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _command_manifest(
    *,
    model: Path | None,
    output: Path,
    shards: int,
    device: str,
    seed: int,
    exemplar_font: Path | None = None,
    eval_limit: int = 0,
    pressure_calibration: Path | None = None,
    eval_layouts: Sequence[int] = tuple(range(6)),
    brushmark_layout: bool = False,
    center110_profile: str | None = None,
) -> dict[str, Any]:
    commands: list[dict[str, Any]] = []
    for shard_index in range(shards):
        shard_output = output / "shards" / f"shard-{shard_index:04d}"
        command = make_command(
            model=model,
            output=shard_output,
            shards=shards,
            shard_index=shard_index,
            device=device,
            seed=seed,
            exemplar_font=exemplar_font,
            eval_limit=eval_limit,
            pressure_calibration=pressure_calibration,
            eval_layouts=eval_layouts,
            brushmark_layout=brushmark_layout,
            center110_profile=center110_profile,
        )
        commands.append(
            {
                "shard_index": shard_index,
                "output": str(shard_output),
                "log": str(output / "logs" / f"shard-{shard_index:04d}.log"),
                "argv": command,
                "shell": shlex.join(command),
            }
        )
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "model": None if model is None else str(model),
        "output": str(output),
        "shards": shards,
        "device": device,
        "seed": seed,
        "eval_limit": eval_limit,
        "eval_layouts": list(eval_layouts),
        "brushmark_layout": brushmark_layout,
        "center110_profile": center110_profile,
        "exemplar_font": None if exemplar_font is None else str(exemplar_font),
        "pressure_calibration": (
            None if pressure_calibration is None else str(pressure_calibration)
        ),
        "commands": commands,
    }


def _run_commands(manifest: dict[str, Any]) -> bool:
    processes: list[tuple[dict[str, Any], subprocess.Popen[bytes], Any]] = []
    try:
        for entry in manifest["commands"]:
            log_path = Path(entry["log"])
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log = log_path.open("wb")
            try:
                process = subprocess.Popen(
                    entry["argv"],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    env=os.environ | {"PYTHONUNBUFFERED": "1"},
                )
            except OSError:
                log.close()
                raise
            processes.append((entry, process, log))
        for entry, process, log in processes:
            entry["returncode"] = process.wait()
            log.close()
    except (KeyboardInterrupt, OSError) as exc:
        manifest["launch_error"] = repr(exc)
        for entry, process, log in processes:
            if process.poll() is None:
                process.terminate()
            entry["returncode"] = process.wait()
            if not log.closed:
                log.close()
        return False
    return all(entry.get("returncode") == 0 for entry in manifest["commands"])


def _merge_outputs(
    *,
    output: Path,
    model: Path | None,
    manifest: Mapping[str, Any],
) -> None:
    rows_by_shard: list[list[dict[str, str]]] = []
    summaries: list[dict[str, Any]] = []
    fieldnames: list[str] | None = None
    shard_count = int(manifest["shards"])
    for entry in manifest["commands"]:
        shard_index = int(entry["shard_index"])
        shard_output = Path(entry["output"])
        names, rows = _read_csv(shard_output / "final" / "characters.csv")
        if fieldnames is None:
            fieldnames = names
        elif names != fieldnames:
            raise ValueError(f"Shard {shard_index} has a different CSV header.")
        summary = _read_json(shard_output / "summary.json")
        shard_metadata = summary.get("evaluation_shard")
        expected_metadata = {"index": shard_index, "count": shard_count}
        if shard_metadata != expected_metadata:
            raise ValueError(
                f"Shard {shard_index} metadata is {shard_metadata!r}, "
                f"expected {expected_metadata!r}."
            )
        rows_by_shard.append(rows)
        summaries.append(summary)

    expected = sample_expected_joyo(
        load_expected_joyo(), int(manifest.get("eval_limit", 0))
    )
    layouts = tuple(int(layout) for layout in manifest["eval_layouts"])
    rows, evaluation = merge_shards(
        rows_by_shard, summaries, expected, layouts=layouts
    )
    validate_evaluation_shape(
        count=int(evaluation["count"]),
        unique_character_count=int(evaluation["unique_character_count"]),
        layout_count=int(evaluation["layout_count"]),
        full=int(manifest.get("eval_limit", 0)) == 0,
        layouts=layouts,
    )
    assert fieldnames is not None
    with (output / "characters.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    ink_dir = output / "ink"
    comparisons_dir = output / "comparisons"
    ink_dir.mkdir(parents=True, exist_ok=True)
    comparisons_dir.mkdir(parents=True, exist_ok=True)
    for entry in manifest["commands"]:
        shard_output = Path(entry["output"])
        for name in ("ink", "comparisons"):
            source = shard_output / "final" / name
            if not source.is_dir():
                continue
            destination = output / name
            for path in source.glob("*.png"):
                shutil.copy2(path, destination / path.name)

    summary = {
        "model": None if model is None else str(model),
        "all_joyo_evaluated": len(rows) == JOYO_COUNT * len(layouts),
        "evaluation_rows_expected": JOYO_COUNT * len(layouts),
        "eval_layouts": list(layouts),
        "brushmark_layout": bool(manifest.get("brushmark_layout", False)),
        "center110_profile": manifest.get("center110_profile"),
        "evaluation_shards": {
            "count": shard_count,
            "indices": list(range(shard_count)),
        },
        "ink_png_count": len(list(ink_dir.glob("*.png"))),
        "acceptance": build_calligrapher_acceptance(evaluation, rows),
        "evaluation": evaluation,
    }
    _write_json(output / "summary.json", summary)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        type=Path,
        help="Optional PPO model; omit it to evaluate the analytical controller.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shards", type=int, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda", "mps", "auto"), default="cpu")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--eval-limit",
        type=int,
        default=0,
        help="Evaluate this evenly sampled total across all shards; 0 means all 2,136.",
    )
    parser.add_argument(
        "--exemplar-font",
        type=Path,
        help="Licensed teacher font forwarded to each shard (Morisawa / Motoya).",
    )
    parser.add_argument(
        "--pressure-calibration",
        type=Path,
        help="Versioned pressure calibration required by every evaluation shard.",
    )
    parser.add_argument(
        "--brushmark-layout",
        action="store_true",
        help="Evaluate the centered 110 mm writing frame.",
    )
    parser.add_argument(
        "--center110-profile",
        choices=("p10-80-v1",),
        help="Forward one versioned centered-110mm control profile to every shard.",
    )
    parser.add_argument(
        "--eval-layouts",
        help="Optional comma-separated subset; defaults to every active layout.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.shards <= 0:
        parser.error("--shards must be positive")
    if args.eval_limit < 0:
        parser.error("--eval-limit cannot be negative")
    if args.center110_profile and not args.brushmark_layout:
        parser.error("--center110-profile requires --brushmark-layout")
    layout_count = 1 if args.brushmark_layout else 6
    try:
        args.eval_layouts = (
            tuple(range(layout_count))
            if args.eval_layouts is None
            else tuple(int(value) for value in args.eval_layouts.split(","))
        )
    except ValueError:
        parser.error("--eval-layouts must be comma-separated integers")
    if (
        not args.eval_layouts
        or len(set(args.eval_layouts)) != len(args.eval_layouts)
        or any(not 0 <= layout < layout_count for layout in args.eval_layouts)
    ):
        parser.error(
            f"--eval-layouts must contain unique values in 0..{layout_count - 1}"
        )
    if args.model is not None and not args.dry_run and not args.model.expanduser().is_file():
        parser.error(f"--model does not exist: {args.model}")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    model = None if args.model is None else args.model.expanduser().resolve()
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    exemplar_font = (
        None if args.exemplar_font is None else args.exemplar_font.expanduser().resolve()
    )
    pressure_calibration = (
        None
        if args.pressure_calibration is None
        else args.pressure_calibration.expanduser().resolve()
    )
    if exemplar_font is not None and not args.dry_run and not exemplar_font.is_file():
        print(f"--exemplar-font does not exist: {exemplar_font}", file=sys.stderr)
        return 1
    if (
        pressure_calibration is not None
        and not args.dry_run
        and not pressure_calibration.is_file()
    ):
        print(
            f"--pressure-calibration does not exist: {pressure_calibration}",
            file=sys.stderr,
        )
        return 1
    manifest = _command_manifest(
        model=model,
        output=output,
        shards=args.shards,
        device=args.device,
        seed=args.seed,
        exemplar_font=exemplar_font,
        eval_limit=args.eval_limit,
        pressure_calibration=pressure_calibration,
        eval_layouts=args.eval_layouts,
        brushmark_layout=args.brushmark_layout,
        center110_profile=args.center110_profile,
    )
    manifest_path = output / "commands.json"
    _write_json(manifest_path, manifest)

    if args.dry_run:
        for entry in manifest["commands"]:
            print(entry["shell"])
        return 0

    if not _run_commands(manifest):
        _write_json(manifest_path, manifest)
        failed = [
            str(entry["shard_index"])
            for entry in manifest["commands"]
            if entry.get("returncode") != 0
        ]
        print(f"Shard evaluation failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    _write_json(manifest_path, manifest)

    try:
        _merge_outputs(output=output, model=model, manifest=manifest)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Could not merge shard evaluations: {exc}", file=sys.stderr)
        return 1
    print(output / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
