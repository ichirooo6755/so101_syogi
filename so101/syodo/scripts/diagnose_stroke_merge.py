"""画同士の癒着（くっつくべきでない線が繋がる）を定量化する。

2 つの見方で測る。

1. 解析的クリアランス
   画 i と画 j の骨格（KanjiVG ポリライン）の最近接距離から、
   目標線幅で描いたときに墨が重なるかを予測する。
       clearance = min_skeleton_distance - (width_i + width_j) / 2
   設計上つながる画（端点共有・交差）は除外する。

2. 位相（穴の数）
   お手本マスクと実際の墨で「筆画に囲まれた白（布白）」の数を数える。
   実墨のほうが少なければ、白い隙間が墨で埋まった＝癒着。
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, replace
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy import ndimage

sys.path.insert(0, "src")

from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.config import WritingLayoutConfig
from so101_calligraphy.trajectory.clearance import (
    _point_to_polyline,
    designed_contact,
)
from so101_calligraphy.training.professional import (
    IndexedTrajectories,
    _sample_indices,
    professional_config,
)
from so101_calligraphy.training.provenance import collect_run_metadata
from so101_calligraphy.trajectory.education import (
    lazy_joyo_trajectories,
    load_joyo_kanji,
)
from so101_calligraphy.trajectory.layout import frame_paper, writing_frames


PHYSICAL_GATE_SCHEMA_VERSION = 2

# The strict profile is the release criterion. ``relaxed-recovery`` remains
# diagnostic-only; ``relaxed-r1`` uses the same measured envelope but may start
# an isolated non-canonical training run.
GATE_THRESHOLD_PROFILES: dict[str, dict[int, dict[str, float | int | bool]]] = {
    "strict": {
        1: {
            "min_successes": 18,
            "max_collision_cases": 0,
            "pressure_median_max": 0.08,
            "pressure_p90_max": 0.18,
            "width_ratio_min": 0.90,
            "width_ratio_max": 1.10,
            "max_lost_holes": 0,
            "endpoint_improvement_min": 10.0,
            "beauty_min": 69.8,
            "beauty_strict": True,
        },
        2: {
            "min_successes": 60,
            "max_collision_cases": 0,
            "pressure_median_max": 0.08,
            "pressure_p90_max": 0.18,
            "width_ratio_min": 0.90,
            "width_ratio_max": 1.10,
            "max_lost_holes": 14,
            "opening_p90_max": 1.12,
            "beauty_min": 85.0,
            "beauty_strict": False,
        },
        3: {
            "min_successes": 768,
            "max_collision_cases": 0,
            "pressure_median_max": 0.08,
            "pressure_p90_max": 0.18,
            "width_ratio_min": 0.90,
            "width_ratio_max": 1.10,
            "max_lost_holes": 14,
            "opening_p90_max": 1.12,
            "beauty_strict": False,
        },
    },
    "relaxed-recovery": {
        1: {
            "min_successes": 17,
            "max_collision_cases": 0,
            "pressure_median_max": 0.70,
            "pressure_p90_max": 0.70,
            "width_ratio_min": 0.70,
            "width_ratio_max": 1.25,
            "max_lost_holes": 0,
            "endpoint_improvement_min": 1.0,
            "beauty_min": 69.8,
            "beauty_strict": True,
        },
        2: {
            "min_successes": 56,
            "max_collision_cases": 0,
            "pressure_median_max": 0.70,
            "pressure_p90_max": 0.70,
            "width_ratio_min": 0.60,
            "width_ratio_max": 2.30,
            "max_lost_holes": 56,
            "opening_p90_max": 1.12,
            "beauty_min": 73.0,
            "beauty_strict": False,
        },
        3: {
            # Empirical recovery profile for the current non-RL parent.  These
            # limits describe the measured 768-case diagnostic envelope; they
            # intentionally never authorize CUDA/r1 (see summarize below).
            "min_successes": 675,
            "max_collision_cases": 14,
            "pressure_median_max": 0.78,
            "pressure_p90_max": 0.78,
            "width_ratio_min": 0.64,
            "width_ratio_max": 4.0,
            "max_lost_holes": 629,
            "opening_p90_max": 1.12,
            "beauty_strict": False,
        },
    },
}
GATE_THRESHOLD_PROFILES["relaxed-r1"] = GATE_THRESHOLD_PROFILES[
    "relaxed-recovery"
]
TRAINING_AUTHORITY_PROFILES = frozenset({"strict", "relaxed-r1"})


def configuration_fingerprint(config: object) -> str:
    def encode(value: object) -> object:
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, Path):
            return str(value)
        raise TypeError(f"Unsupported configuration value: {type(value).__name__}")

    payload = json.dumps(
        asdict(config),
        sort_keys=True,
        separators=(",", ":"),
        default=encode,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def summarize_physical_gate(
    results: list[dict[str, object]],
    *,
    gate_level: int,
    endpoint_improvement: float | None,
    calibration_clip_rate: float = 0.0,
    calibration_fallback_rate: float = 0.0,
    clip_rate_limit: float = 1.0,
    fallback_rate_limit: float = 1.0,
    threshold_profile: str = "strict",
) -> dict[str, object]:
    try:
        # Shard workers use gate_level=0 because they emit partial results that
        # are scored only after merge.  Keep that established CLI contract while
        # borrowing the Gate 3 limits for the non-authoritative per-shard summary.
        profile_level = gate_level if gate_level in (1, 2, 3) else 3
        profile = GATE_THRESHOLD_PROFILES[threshold_profile][profile_level]
    except KeyError as exc:
        raise ValueError(
            f"unknown threshold profile or gate level: {threshold_profile!r}/{gate_level}"
        ) from exc
    expected = {1: 18, 2: 60, 3: 768}.get(gate_level, 0)
    lost_total = sum(int(row["lost_holes"]) for row in results)
    beauty_mean = float(np.mean([float(row["beauty_score"]) for row in results]))
    successes = sum(bool(row["is_success"]) for row in results)
    collision_cases = sum(
        bool(row["collision_types"]) or bool(row["hard_limit"]) for row in results
    )
    gates: dict[str, bool] = {
        "evaluation_count": bool(expected and len(results) == expected),
        "complete": successes >= int(profile["min_successes"]),
        "collision_and_hard_limit_free": collision_cases
        <= int(profile["max_collision_cases"]),
        "pressure_tracking": all(
            float(row["pressure_error_median_abs"])
            <= float(profile["pressure_median_max"])
            and float(row["pressure_error_p90_abs"])
            <= float(profile["pressure_p90_max"])
            for row in results
        ),
        "width_tracking": all(
            float(profile["width_ratio_min"])
            <= float(row["width_ratio_median"])
            <= float(profile["width_ratio_max"])
            for row in results
        ),
        "calibration_clip_rate": calibration_clip_rate <= clip_rate_limit,
        "calibration_fallback_rate": (
            calibration_fallback_rate <= fallback_rate_limit
        ),
    }
    if gate_level == 1:
        beauty_gate = (
            beauty_mean > float(profile["beauty_min"])
            if bool(profile["beauty_strict"])
            else beauty_mean >= float(profile["beauty_min"])
        )
        gates.update(
            negative_space=lost_total <= int(profile["max_lost_holes"]),
            endpoint_ablation=(
                endpoint_improvement is not None
                and endpoint_improvement >= float(profile["endpoint_improvement_min"])
            ),
            beauty=beauty_gate,
        )
    elif gate_level == 2:
        beauty_gate = (
            beauty_mean > float(profile["beauty_min"])
            if bool(profile["beauty_strict"])
            else beauty_mean >= float(profile["beauty_min"])
        )
        gates.update(
            negative_space=lost_total <= int(profile["max_lost_holes"]),
            tip_opening=all(
                float(row["opening_p90"])
                <= float(profile["opening_p90_max"]) + 1e-9
                for row in results
            ),
            beauty=beauty_gate,
        )
    elif gate_level == 3:
        gates.update(
            negative_space=lost_total <= int(profile["max_lost_holes"]),
            tip_opening=all(
                float(row["opening_p90"])
                <= float(profile["opening_p90_max"]) + 1e-9
                for row in results
            ),
        )
    passed = bool(gates and all(gates.values()))
    return {
        "gate_schema_version": PHYSICAL_GATE_SCHEMA_VERSION,
        "threshold_profile": threshold_profile,
        "thresholds": dict(profile),
        "gate_level": gate_level,
        "expected_evaluations": expected,
        "evaluations": len(results),
        "successes": successes,
        "lost_holes": lost_total,
        "beauty_mean": beauty_mean,
        "calibration_clip_rate": calibration_clip_rate,
        "calibration_fallback_rate": calibration_fallback_rate,
        "gates": gates,
        "passed": passed,
        "ready_for_cuda": (
            threshold_profile in TRAINING_AUTHORITY_PROFILES
            and gate_level == 2
            and passed
        ),
        "ready_for_r1": (
            threshold_profile in TRAINING_AUTHORITY_PROFILES
            and gate_level == 3
            and passed
        ),
    }

def _polyline_min_distance(a: np.ndarray, b: np.ndarray) -> float:
    """2 本のポリライン間の最小距離（端点だけでなく本体も見る）。"""

    return min(
        float(_point_to_polyline(a, b).min()),
        float(_point_to_polyline(b, a).min()),
    )


# 布白として数える最小面積 [px]。墨のかすれが作る 1-2px の穴を除くため。
MINIMUM_HOLE_AREA = 12


def _hole_count(mask: np.ndarray, threshold: float = 0.35) -> int:
    """筆画に完全に囲まれた背景領域（布白）の数。かすれ由来の微小な穴は除く。"""

    solid = np.asarray(mask) >= threshold
    if not solid.any():
        return 0
    # 背景は 4 近傍、前景は 8 近傍が標準的な組み合わせ。
    labels, count = ndimage.label(~solid, structure=np.array(
        [[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.int8
    ))
    if count == 0:
        return 0
    border = set(labels[0, :]) | set(labels[-1, :])
    border |= set(labels[:, 0]) | set(labels[:, -1])
    border.discard(0)
    areas = np.bincount(labels.ravel(), minlength=count + 1)
    return int(
        sum(
            1
            for index in range(1, count + 1)
            if index not in border and areas[index] >= MINIMUM_HOLE_AREA
        )
    )


def analyse_character(env: CalligraphyEnv, character: str) -> dict[str, object]:
    strokes = env.trajectory.strokes
    waypoints = env.waypoints
    endpoint_clearances = [
        [
            min(
                float(
                    _point_to_polyline(
                        np.asarray(stroke.points[endpoint]).reshape(1, 2),
                        np.asarray(other.points),
                    )[0]
                )
                for other_index, other in enumerate(strokes)
                if other_index != stroke_index
            )
            if len(strokes) > 1
            else float("inf")
            for endpoint in (0, -1)
        ]
        for stroke_index, stroke in enumerate(strokes)
    ]
    # 画ごとの目標幅の代表値（胴体部の中央値）。
    widths: list[float] = []
    for index in range(len(strokes)):
        selected = (waypoints.stroke_indices == index) & waypoints.pen_down
        values = waypoints.target_width[selected]
        widths.append(float(np.median(values)) if len(values) else 0.0)

    contact = designed_contact(
        strokes, junction_tolerance=env.config.stroke_junction_tolerance
    )
    pairs: list[dict[str, object]] = []
    for i in range(len(strokes)):
        for j in range(i + 1, len(strokes)):
            distance = _polyline_min_distance(strokes[i].points, strokes[j].points)
            designed = bool(contact[i, j])
            clearance = distance - 0.5 * (widths[i] + widths[j])
            pairs.append(
                {
                    "i": i,
                    "j": j,
                    "skeleton_distance": distance,
                    "designed_contact": designed,
                    "clearance": clearance,
                }
            )
    separate = [p for p in pairs if not p["designed_contact"]]
    merged = [p for p in separate if p["clearance"] < 0.0]
    tight = [p for p in separate if 0.0 <= p["clearance"] < 0.0005]

    exemplar_holes = (
        _hole_count(env._professional_mask)
        if env._professional_mask is not None
        else -1
    )
    render_holes = _hole_count(env.ink.pigment)
    writing_samples = sum(len(record["width"]) for record in env._stroke_records)
    actual_width_values: list[float] = []
    actual_pressure_values: list[float] = []
    target_width_values: list[float] = []
    target_pressure_values: list[float] = []
    xy_error_values: list[float] = []
    z_error_values: list[float] = []
    opening_values: list[float] = []
    actual_angle_values: list[float] = []
    target_angle_values: list[float] = []
    actual_speed_values: list[float] = []
    target_speed_values: list[float] = []
    pressure_error_by_phase: dict[str, list[float]] = {}
    pressure_error_by_stroke: dict[int, list[float]] = {}
    dwell_by_phase: dict[str, list[int]] = {}
    dwell_details: list[dict[str, object]] = []
    stroke_geometry: list[dict[str, object]] = []
    for stroke_index, record in enumerate(env._stroke_records):
        indices = np.asarray(record["target_index"], dtype=np.int64)
        if not len(indices):
            continue
        actual_points = np.asarray(record["points"], dtype=np.float64).reshape(-1, 2)
        stroke_mask = np.logical_and(
            waypoints.pen_down,
            waypoints.stroke_indices == stroke_index,
        )
        target_points = np.asarray(
            waypoints.positions[stroke_mask, :2], dtype=np.float64
        )

        def arc_length(points: np.ndarray) -> float:
            if len(points) < 2:
                return 0.0
            return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())

        actual_length = arc_length(actual_points)
        target_length = arc_length(target_points)
        progress_values = np.asarray(record["progress"], dtype=np.float64)
        stroke_geometry.append(
            {
                "stroke_index": stroke_index,
                "actual_length_m": actual_length,
                "target_length_m": target_length,
                "length_ratio": actual_length / max(target_length, 1e-12),
                "centroid_error_m": float(
                    np.linalg.norm(
                        actual_points.mean(axis=0) - target_points.mean(axis=0)
                    )
                ),
                "start_error_m": float(
                    np.linalg.norm(actual_points[0] - target_points[0])
                ),
                "finish_error_m": float(
                    np.linalg.norm(actual_points[-1] - target_points[-1])
                ),
                "minimum_recorded_progress": float(np.min(progress_values)),
                "maximum_recorded_progress": float(np.max(progress_values)),
                "contact_samples": len(actual_points),
            }
        )
        # Every contact stamp is visible on paper. Measuring only the last
        # sample at each waypoint hid the pressure spikes that made round ink
        # pools between otherwise correctly sized strokes.
        samples = np.arange(len(indices), dtype=np.int64)
        body_samples = np.asarray(
            [
                row
                for row in samples
                if waypoints.brushwork_phases[indices[row]] in ("send", "corner")
            ],
            dtype=np.int64,
        )
        actual_width_values.extend(np.asarray(record["width"])[body_samples])
        actual_pressure_values.extend(np.asarray(record["pressure"])[samples])
        target_width_values.extend(np.asarray(record["target_width"])[body_samples])
        target_pressure_values.extend(np.asarray(record["target_pressure"])[samples])
        xy_error_values.extend(np.asarray(record["xy_error"])[samples])
        z_error_values.extend(np.asarray(record["z_error"])[samples])
        opening_values.extend(np.asarray(record["opening"])[samples])
        actual_angle_values.extend(np.asarray(record["actual_angle_deg"])[samples])
        target_angle_values.extend(np.asarray(record["target_angle_deg"])[samples])
        actual_speed_values.extend(np.asarray(record["speed"])[samples])
        target_speed_values.extend(waypoints.target_speed[indices[samples]])
        for row in samples:
            phase = str(waypoints.brushwork_phases[indices[row]])
            error = float(
                record["pressure"][row] - record["target_pressure"][row]
            )
            pressure_error_by_phase.setdefault(phase, []).append(error)
            pressure_error_by_stroke.setdefault(stroke_index, []).append(error)
        unique_indices, dwell_counts = np.unique(indices, return_counts=True)
        for target_index, count in zip(unique_indices, dwell_counts, strict=True):
            phase = str(waypoints.brushwork_phases[target_index])
            dwell_by_phase.setdefault(phase, []).append(int(count))
            rows = np.flatnonzero(indices == target_index)
            dwell_details.append(
                {
                    "target_index": int(target_index),
                    "stroke_index": int(waypoints.stroke_indices[target_index]),
                    "phase": phase,
                    "stroke_progress": float(
                        waypoints.stroke_progress[target_index]
                    ),
                    "samples": int(count),
                    "target_pressure": float(
                        waypoints.target_pressure[target_index]
                    ),
                    "actual_pressure_median": float(
                        np.median(np.asarray(record["pressure"])[rows])
                    ),
                    "pressure_offset_median_m": float(
                        np.median(np.asarray(record["pressure_offset"])[rows])
                    ),
                    "pressure_offset_max_m": float(
                        np.max(np.asarray(record["pressure_offset"])[rows])
                    ),
                    "xy_error_last_m": float(record["xy_error"][rows[-1]]),
                    "z_error_last_m": float(abs(record["z_error"][rows[-1]])),
                }
            )
    actual_width = np.asarray(actual_width_values, dtype=np.float64)
    actual_pressure = np.asarray(actual_pressure_values, dtype=np.float64)
    target_width = np.asarray(target_width_values, dtype=np.float64)
    target_pressure = np.asarray(target_pressure_values, dtype=np.float64)
    signed_pressure_error = actual_pressure - target_pressure
    pressure_error = np.abs(signed_pressure_error)
    width_ratio = actual_width / np.maximum(target_width, 1e-9)
    openings = np.asarray(opening_values, dtype=np.float64)
    actual_angles = np.asarray(actual_angle_values, dtype=np.float64)
    target_angles = np.asarray(target_angle_values, dtype=np.float64)
    angle_error = np.abs(actual_angles - target_angles)
    actual_speeds = np.asarray(actual_speed_values, dtype=np.float64)
    target_speeds = np.asarray(target_speed_values, dtype=np.float64)
    xy_errors = np.asarray(xy_error_values, dtype=np.float64)
    z_errors = np.abs(np.asarray(z_error_values, dtype=np.float64))

    return {
        "character": character,
        "strokes": len(strokes),
        "exposed_horizontal_endpoints": env._exposed_horizontal.tolist(),
        "endpoint_nearest_stroke_distance_m": endpoint_clearances,
        "median_width": float(np.median(widths)) if widths else 0.0,
        "separate_pairs": len(separate),
        "merged_pairs": len(merged),
        "tight_pairs": len(tight),
        "worst_clearance": min((p["clearance"] for p in separate), default=float("nan")),
        "exemplar_holes": exemplar_holes,
        "render_holes": render_holes,
        "lost_holes": max(0, exemplar_holes - render_holes),
        "writing_samples": writing_samples,
        "settled_samples": len(actual_width),
        "actual_width_median": float(np.median(actual_width)) if len(actual_width) else 0.0,
        "width_ratio_median": float(np.median(width_ratio)) if len(width_ratio) else 0.0,
        "width_ratio_p90": (
            float(np.percentile(width_ratio, 90)) if len(width_ratio) else 0.0
        ),
        "opening_median": float(np.median(openings)) if len(openings) else 0.0,
        "opening_p90": float(np.percentile(openings, 90)) if len(openings) else 0.0,
        "actual_angle_median_deg": (
            float(np.median(actual_angles)) if len(actual_angles) else 0.0
        ),
        "target_angle_median_deg": (
            float(np.median(target_angles)) if len(target_angles) else 0.0
        ),
        "angle_error_median_abs_deg": (
            float(np.median(angle_error)) if len(angle_error) else 0.0
        ),
        "angle_error_p90_abs_deg": (
            float(np.percentile(angle_error, 90)) if len(angle_error) else 0.0
        ),
        "actual_speed_median_m_s": (
            float(np.median(actual_speeds)) if len(actual_speeds) else 0.0
        ),
        "target_speed_median_m_s": (
            float(np.median(target_speeds)) if len(target_speeds) else 0.0
        ),
        "speed_ratio_median": (
            float(
                np.median(actual_speeds / np.maximum(target_speeds, 1e-9))
            )
            if len(actual_speeds)
            else 0.0
        ),
        "pressure_error_median_abs": (
            float(np.median(pressure_error)) if len(pressure_error) else 0.0
        ),
        "pressure_error_median": (
            float(np.median(signed_pressure_error)) if len(signed_pressure_error) else 0.0
        ),
        "pressure_error_p10": (
            float(np.percentile(signed_pressure_error, 10))
            if len(signed_pressure_error)
            else 0.0
        ),
        "pressure_error_p90": (
            float(np.percentile(signed_pressure_error, 90))
            if len(signed_pressure_error)
            else 0.0
        ),
        "pressure_error_p90_abs": (
            float(np.percentile(pressure_error, 90)) if len(pressure_error) else 0.0
        ),
        "xy_error_median_m": float(np.median(xy_errors)) if len(xy_errors) else 0.0,
        "xy_error_p90_m": (
            float(np.percentile(xy_errors, 90)) if len(xy_errors) else 0.0
        ),
        "z_error_median_abs_m": (
            float(np.median(z_errors)) if len(z_errors) else 0.0
        ),
        "z_error_p90_abs_m": (
            float(np.percentile(z_errors, 90)) if len(z_errors) else 0.0
        ),
        "pressure_error_by_phase": {
            phase: {
                "samples": len(values),
                "median_abs": float(np.median(np.abs(values))),
                "p90_abs": float(np.percentile(np.abs(values), 90)),
                "p90": float(np.percentile(values, 90)),
            }
            for phase, values in pressure_error_by_phase.items()
        },
        "pressure_error_by_stroke": {
            str(stroke_index): {
                "samples": len(values),
                "median_abs": float(np.median(np.abs(values))),
                "p90_abs": float(np.percentile(np.abs(values), 90)),
                "p90": float(np.percentile(values, 90)),
            }
            for stroke_index, values in pressure_error_by_stroke.items()
        },
        "contact_samples_per_target_by_phase": {
            phase: {
                "targets": len(values),
                "median": float(np.median(values)),
                "p90": float(np.percentile(values, 90)),
                "maximum": int(max(values)),
            }
            for phase, values in dwell_by_phase.items()
        },
        "longest_contact_targets": sorted(
            dwell_details, key=lambda row: int(row["samples"]), reverse=True
        )[:10],
        "stroke_geometry": stroke_geometry,
        "pressure_calibration_samples": list(env._pressure_calibration_samples),
        "beauty_score": float(env._beauty_score),
        "beauty_components": dict(env._beauty_components),
        "width_detail": dict(env._width_details),
        "commanded_angle_category_counts": {
            str(angle): sum(
                int(sample.get("commanded_angle_deg", -1)) == angle
                for sample in env._pressure_calibration_samples
            )
            for angle in (0, 4, 8, 12, 20, 30, 45)
        },
        "pressure_probe": {
            "enabled": env.config.pressure_probe_offset_m is not None,
            "offset_m": env.config.pressure_probe_offset_m,
            "feedback_gain": 0.0
            if env.config.pressure_probe_offset_m is not None
            else None,
        },
        "detail": merged,
    }


def main() -> None:
    started_at = datetime.now().astimezone()
    started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=None, help="省略時は IK 天井")
    parser.add_argument("--chars", default="一三十目書飛鬱誠砕案")
    parser.add_argument("--limit", type=int, default=0, help="0 は --chars のみ")
    parser.add_argument("--output", type=Path, default=Path("runs/stroke-merge-report.json"))
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--pressure-gain", type=float, default=None)
    parser.add_argument("--large-frame-pressure-gain", type=float, default=None)
    parser.add_argument("--horizontal-pressure-gain", type=float, default=None)
    parser.add_argument("--pressure-limit", type=float, default=None)
    parser.add_argument("--horizontal-pressure-limit", type=float, default=None)
    parser.add_argument("--tuft-opening", type=float, default=None)
    parser.add_argument("--nominal-force", type=float, default=None)
    parser.add_argument("--large-frame-nominal-force", type=float, default=None)
    parser.add_argument("--nominal-compression", type=float, default=None)
    parser.add_argument("--release-clearance", type=float, default=None)
    parser.add_argument("--pressure-slew", type=float, default=None)
    parser.add_argument("--pressure-response", type=float, default=None)
    parser.add_argument("--horizontal-pressure-response", type=float, default=None)
    parser.add_argument("--tip-pressure-floor", type=float, default=None)
    parser.add_argument("--tip-pressure-scale", type=float, default=None)
    parser.add_argument(
        "--brush-maximum-width",
        type=float,
        default=None,
        help="Override the calibrated maximum deposited brush width in metres.",
    )
    parser.add_argument(
        "--brush-minimum-width",
        type=float,
        default=None,
        help="Override the calibrated minimum deposited brush width in metres.",
    )
    parser.add_argument("--harai-gain-scale", type=float, default=None)
    parser.add_argument("--hane-release-gain-scale", type=float, default=None)
    parser.add_argument("--base-x", type=float, default=None)
    parser.add_argument("--base-y", type=float, default=None)
    parser.add_argument("--base-height", type=float, default=None)
    parser.add_argument("--xy-tolerance", type=float, default=None)
    parser.add_argument("--z-tolerance", type=float, default=None)
    parser.add_argument("--max-joint-speed", type=float, default=None)
    parser.add_argument("--junction-tolerance", type=float, default=None)
    parser.add_argument("--minimum-gap", type=float, default=None)
    parser.add_argument("--clearance-floor", type=float, default=None)
    parser.add_argument("--exemplar-motion-strength", type=float, default=None)
    parser.add_argument("--exemplar-density-fit", type=float, default=None)
    parser.add_argument("--small-glyph-reference", type=float, default=None)
    parser.add_argument("--entry-angle", type=float, choices=(25.0, 30.0, 35.0))
    parser.add_argument("--fixed-contact-angle", type=float, choices=(40.0, 45.0))
    parser.add_argument(
        "--large-frame-entry-angle", type=float, choices=(25.0, 30.0, 35.0)
    )
    parser.add_argument("--corner-angle", type=float, default=None)
    parser.add_argument("--finish-angle", type=float, default=None)
    parser.add_argument("--entry-descent-ratio", type=float, default=None)
    parser.add_argument("--contact-orientation-weight", type=float, default=None)
    parser.add_argument("--contact-tilt-speed", type=float, default=None)
    parser.add_argument("--upright", action="store_true")
    parser.add_argument("--upright-baseline", type=Path)
    parser.add_argument("--pressure-calibration", type=Path, default=None)
    parser.add_argument("--pressure-probe-offset-m", type=float, default=None)
    parser.add_argument("--require-pressure-calibration", action="store_true")
    parser.add_argument("--residual-pressure-integral-scale", type=float, default=1.0)
    parser.add_argument(
        "--pressure-calibration-clip-rate-limit", type=float, default=1.0
    )
    parser.add_argument(
        "--pressure-calibration-fallback-rate-limit", type=float, default=1.0
    )
    parser.add_argument("--images-dir", type=Path)
    parser.add_argument("--legacy-sixty-mm", action="store_true")
    parser.add_argument(
        "--legacy-attachment-compensation",
        action="store_true",
        help="fix the servo and drive the contact tip XYZ",
    )
    parser.add_argument(
        "--brushmark-layout",
        action="store_true",
        help="one 110 mm frame at the current paper centre (historical 1-glyph page)",
    )
    parser.add_argument(
        "--fixed-attachment-servo-angle",
        type=float,
        default=0.0,
        help="electrical degrees; 0deg is physical 45deg lean, 45deg is upright home",
    )
    parser.add_argument(
        "--layouts",
        default="0,1,2,3,4,5",
        help="comma-separated A4 layout indices (0-3:85mm, 4-5:110mm)",
    )
    parser.add_argument("--max-steps", type=int, default=25_000)
    parser.add_argument("--path-spacing", type=float, default=None)
    parser.add_argument(
        "--eval-limit",
        type=int,
        default=0,
        help="same linspace joyo sample as professional --eval-limit",
    )
    parser.add_argument("--eval-shard-count", type=int, default=1)
    parser.add_argument("--eval-shard-index", type=int, default=0)
    parser.add_argument(
        "--gate-level",
        type=int,
        choices=(0, 1, 2, 3),
        default=0,
        help="0 records diagnostics only; 1 requires 18; 2 requires 60; 3 requires 768 cases.",
    )
    parser.add_argument(
        "--threshold-profile",
        choices=tuple(GATE_THRESHOLD_PROFILES),
        default="strict",
        help=(
            "gate acceptance profile; relaxed-recovery is diagnostic-only and "
            "never grants CUDA/r1 authority"
        ),
    )
    args = parser.parse_args()
    if args.residual_pressure_integral_scale < 0.0:
        parser.error("--residual-pressure-integral-scale cannot be negative")
    if not 0.0 <= args.pressure_calibration_clip_rate_limit <= 1.0:
        parser.error("--pressure-calibration-clip-rate-limit must be in [0, 1]")
    if not 0.0 <= args.pressure_calibration_fallback_rate_limit <= 1.0:
        parser.error("--pressure-calibration-fallback-rate-limit must be in [0, 1]")
    if args.pressure_probe_offset_m is not None and args.pressure_calibration is not None:
        parser.error("--pressure-probe-offset-m cannot be combined with calibration")
    if args.eval_shard_count <= 0:
        parser.error("--eval-shard-count must be positive")
    if not 0 <= args.eval_shard_index < args.eval_shard_count:
        parser.error("--eval-shard-index must be in [0, --eval-shard-count)")

    entries = load_joyo_kanji(Path("data/kanjidic2"))
    index_of = {entry.character: i for i, entry in enumerate(entries)}
    if args.eval_limit:
        selected = _sample_indices(tuple(range(len(entries))), args.eval_limit)
        selected = selected[args.eval_shard_index :: args.eval_shard_count]
        chosen = [entries[index].character for index in selected]
    elif args.limit:
        chosen = [entry.character for entry in entries[: args.limit]]
    else:
        chosen = [c for c in args.chars if c in index_of]
    if not chosen:
        raise SystemExit("対象文字がありません（--chars か --limit / --eval-limit を指定）")
    selected = tuple(index_of[c] for c in chosen)
    font = Path(Path("runs/selected-exemplar-font.txt").read_text().strip())
    config = professional_config("all", motoya_font_path=font)
    if args.brushmark_layout:
        config = replace(
            config, writing_layout=WritingLayoutConfig.brushmark_center()
        )
    if args.legacy_attachment_compensation:
        config = replace(
            config,
            legacy_attachment_compensation=True,
            hardware=replace(
                config.hardware,
                fixed_attachment_servo_angle_rad=float(
                    np.deg2rad(args.fixed_attachment_servo_angle)
                ),
            ),
        )
    if args.legacy_sixty_mm:
        config = replace(
            config, writing_layout=WritingLayoutConfig.legacy_sixty_mm()
        )
    if args.pressure_gain is not None:
        config = replace(
            config,
            contact_pressure_gain=args.pressure_gain,
            large_frame_contact_pressure_gain=args.pressure_gain,
            horizontal_contact_pressure_gain=args.pressure_gain,
        )
    if args.large_frame_pressure_gain is not None:
        config = replace(
            config,
            large_frame_contact_pressure_gain=args.large_frame_pressure_gain,
        )
    if args.horizontal_pressure_gain is not None:
        config = replace(
            config,
            horizontal_contact_pressure_gain=args.horizontal_pressure_gain,
        )
    if args.pressure_limit is not None:
        config = replace(
            config,
            contact_pressure_limit=args.pressure_limit,
            horizontal_contact_pressure_limit=args.pressure_limit,
        )
    if args.horizontal_pressure_limit is not None:
        config = replace(
            config,
            horizontal_contact_pressure_limit=args.horizontal_pressure_limit,
        )
    if args.tuft_opening is not None:
        config = replace(config, brush=replace(config.brush, tuft_opening=args.tuft_opening))
    if args.nominal_force is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                nominal_force=args.nominal_force,
                large_frame_nominal_force=args.nominal_force,
            ),
        )
    if args.large_frame_nominal_force is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                large_frame_nominal_force=args.large_frame_nominal_force,
            ),
        )
    if args.nominal_compression is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                nominal_compression=args.nominal_compression,
            ),
        )
    if args.release_clearance is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                release_clearance=args.release_clearance,
            ),
        )
    if args.pressure_slew is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                pressure_slew_per_step=args.pressure_slew,
            ),
        )
    if args.pressure_response is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                pressure_response=args.pressure_response,
                horizontal_pressure_response=args.pressure_response,
            ),
        )
    if args.horizontal_pressure_response is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                horizontal_pressure_response=args.horizontal_pressure_response,
            ),
        )
    if args.tip_pressure_floor is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                tip_pressure_floor=args.tip_pressure_floor,
            ),
        )
    if args.tip_pressure_scale is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                tip_pressure_scale=args.tip_pressure_scale,
            ),
        )
    if (
        args.brush_minimum_width is not None
        or args.brush_maximum_width is not None
    ):
        minimum_width = (
            config.brush.minimum_width
            if args.brush_minimum_width is None
            else args.brush_minimum_width
        )
        maximum_width = (
            config.brush.maximum_width
            if args.brush_maximum_width is None
            else args.brush_maximum_width
        )
        if minimum_width <= 0.0:
            parser.error("--brush-minimum-width must be positive")
        if maximum_width <= minimum_width:
            parser.error("--brush-maximum-width must exceed --brush-minimum-width")
        config = replace(
            config,
            brush=replace(
                config.brush,
                minimum_width=minimum_width,
                maximum_width=maximum_width,
            ),
        )
    if args.harai_gain_scale is not None:
        config = replace(
            config,
            harai_pressure_gain_scale=args.harai_gain_scale,
        )
    if args.hane_release_gain_scale is not None:
        config = replace(
            config,
            hane_release_pressure_gain_scale=args.hane_release_gain_scale,
        )
    if any(value is not None for value in (args.base_x, args.base_y, args.base_height)):
        hardware = config.hardware
        config = replace(
            config,
            hardware=replace(
                hardware,
                base_position_xy_m=(
                    hardware.base_position_xy_m[0]
                    if args.base_x is None
                    else args.base_x,
                    hardware.base_position_xy_m[1]
                    if args.base_y is None
                    else args.base_y,
                ),
                base_riser_height_m=(
                    hardware.base_riser_height_m
                    if args.base_height is None
                    else args.base_height
                ),
            ),
        )
    if args.xy_tolerance is not None:
        config = replace(config, target_tolerance_xy=args.xy_tolerance)
    if args.z_tolerance is not None:
        if args.z_tolerance <= 0.0:
            parser.error("--z-tolerance must be positive")
        config = replace(config, target_tolerance_z=args.z_tolerance)
    if args.max_joint_speed is not None:
        if args.max_joint_speed <= 0.0:
            parser.error("--max-joint-speed must be positive")
        config = replace(config, max_joint_speed=args.max_joint_speed)
    if args.junction_tolerance is not None:
        config = replace(config, stroke_junction_tolerance=args.junction_tolerance)
    if args.minimum_gap is not None:
        config = replace(config, stroke_minimum_gap=args.minimum_gap)
    if args.clearance_floor is not None:
        config = replace(config, stroke_clearance_floor=args.clearance_floor)
    if args.exemplar_motion_strength is not None:
        config = replace(
            config,
            exemplar_motion_strength=args.exemplar_motion_strength,
        )
    if args.exemplar_density_fit is not None:
        if not 0.0 <= args.exemplar_density_fit <= 1.0:
            parser.error("--exemplar-density-fit must be in [0, 1]")
        config = replace(
            config,
            exemplar_density_fit=args.exemplar_density_fit,
        )
    if args.small_glyph_reference is not None:
        config = replace(
            config,
            small_glyph_reference=args.small_glyph_reference,
        )
    if args.entry_angle is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                entry_lean=float(np.tan(np.deg2rad(args.entry_angle))),
                large_frame_entry_lean=float(
                    np.tan(np.deg2rad(args.entry_angle))
                ),
            ),
        )
    if args.fixed_contact_angle is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                fixed_contact_lean=float(
                    np.tan(np.deg2rad(args.fixed_contact_angle))
                ),
            ),
        )
    if args.large_frame_entry_angle is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                large_frame_entry_lean=float(
                    np.tan(np.deg2rad(args.large_frame_entry_angle))
                ),
            ),
        )
    if args.corner_angle is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                corner_lean=float(np.tan(np.deg2rad(args.corner_angle))),
            ),
        )
    if args.finish_angle is not None:
        config = replace(
            config,
            brush=replace(
                config.brush,
                finish_lean=float(np.tan(np.deg2rad(args.finish_angle))),
            ),
        )
    if args.entry_descent_ratio is not None:
        config = replace(
            config,
            entry_descent_ratio=args.entry_descent_ratio,
        )
    if args.contact_orientation_weight is not None:
        config = replace(
            config,
            contact_orientation_ik_weight=args.contact_orientation_weight,
        )
    if args.contact_tilt_speed is not None:
        config = replace(config, contact_tilt_max_speed=args.contact_tilt_speed)
    if args.pressure_calibration is not None:
        config = replace(
            config,
            pressure_calibration_path=str(args.pressure_calibration),
            require_pressure_calibration=args.require_pressure_calibration,
            residual_pressure_integral_scale=args.residual_pressure_integral_scale,
            pressure_calibration_clip_rate_limit=(
                args.pressure_calibration_clip_rate_limit
            ),
        )
    if args.pressure_probe_offset_m is not None:
        config = replace(
            config,
            contact_pressure_gain=0.0,
            large_frame_contact_pressure_gain=0.0,
            horizontal_contact_pressure_gain=0.0,
            residual_pressure_integral_scale=0.0,
            pressure_probe_offset_m=args.pressure_probe_offset_m,
        )
    if args.upright:
        config = replace(
            config,
            brush=replace(
                config.brush,
                desired_lean=0.0,
                sweep_lean=0.0,
                corner_lean=0.0,
                release_lean=0.0,
                airborne_lean=0.0,
                entry_lean=0.0,
                large_frame_entry_lean=0.0,
                finish_lean=0.0,
            ),
        )
    dataset = lazy_joyo_trajectories(
        entries,
        kanjivg_cache=Path("data/kanjivg"),
        animcjk_cache=Path("data/animcjk"),
        use_animcjk_medians=True,
        paper=frame_paper(config.paper, config.writing_layout, 0),
        spacing=(
            config.path_spacing if args.path_spacing is None else args.path_spacing
        ),
    )
    n_frames = len(writing_frames(config.paper, config.writing_layout))
    if args.layouts == "0,1,2,3,4,5" and n_frames == 1:
        layouts = (0,)
    else:
        layouts = tuple(int(value) for value in args.layouts.split(","))
    if not layouts or any(not 0 <= value < n_frames for value in layouts):
        raise SystemExit(
            f"--layouts は 0..{n_frames - 1} のカンマ区切りで指定してください"
        )
    env = CalligraphyEnv(
        task="professional-evaluation-all",
        trajectories=IndexedTrajectories(dataset, selected),
        config=config,
    )
    model = None
    if args.model is not None:
        from stable_baselines3 import PPO

        model = PPO.load(args.model, device=args.device)

    results = []
    print(
        f"{'字':2s} {'画':>3s} {'計画幅':>6s} {'実幅':>6s} {'幅比':>5s} "
        f"{'圧誤差':>6s} {'p90':>6s} {'点数':>6s} {'癒着':>5s} {'穴(手本/実)':>11s}"
    )
    for local_index, character in enumerate(chosen):
        for layout_index in layouts:
            observation, _ = env.reset(
                seed=17 + selected[local_index] * 6 + layout_index,
                options={
                    "trajectory_index": local_index,
                    "layout_index": layout_index,
                },
            )
            info: dict[str, object] = {}
            axis_errors: dict[str, list[float]] = {"entry": [], "finish": []}
            terminated = truncated = False
            for _ in range(args.max_steps):
                action = (
                    np.zeros(6, dtype=np.float32)
                    if model is None
                    else model.predict(observation, deterministic=True)[0]
                )
                observation, _, terminated, truncated, info = env.step(action)
                brush_phase = str(info.get("brushwork_phase", ""))
                progress = float(info.get("stroke_progress", 0.0))
                at_endpoint = (
                    brush_phase == "entry" and progress <= 0.02
                ) or (brush_phase == "finish" and progress >= 0.98)
                if bool(info.get("pen_down")) and at_endpoint:
                    axis_errors[brush_phase].append(
                        float(info.get("attachment_axis_error_deg", 0.0))
                    )
                if terminated or truncated:
                    break
            result = analyse_character(env, character)
            all_axis_errors = np.asarray(
                axis_errors["entry"] + axis_errors["finish"], dtype=np.float64
            )
            endpoint = env.endpoint_metrics
            result.update(
                layout_index=layout_index,
                writing_frame_size_m=float(info.get("writing_frame_size_m", 0.0)),
                is_success=bool(info.get("is_success", False)),
                progress=float(info.get("progress", 0.0)),
                collision_types=list(info.get("collision_types", []) or []),
                collision_geom_pairs=[
                    {
                        "geoms": [
                            env.model.geom(int(contact.geom1)).name,
                            env.model.geom(int(contact.geom2)).name,
                        ],
                        "penetration_m": max(-float(contact.dist), 0.0),
                    }
                    for contact in env.data.contact
                    if contact.dist <= 0.0
                ],
                hard_limit=bool(info.get("hard_limit", False)),
                contact_pressure_gain=float(
                    info.get(
                        "effective_contact_pressure_gain",
                        config.contact_pressure_gain,
                    )
                ),
                contact_pressure_limit=float(
                    info.get(
                        "effective_contact_pressure_limit",
                        config.contact_pressure_limit,
                    )
                ),
                entry_angle_deg=float(
                    info.get(
                        "effective_entry_angle_deg",
                        np.degrees(np.arctan(config.brush.entry_lean)),
                    )
                ),
                tuft_opening=config.brush.tuft_opening,
                nominal_force=float(
                    info.get("effective_nominal_force", config.brush.nominal_force)
                ),
                pressure_response=float(
                    info.get(
                        "effective_pressure_response",
                        config.brush.pressure_response,
                    )
                ),
                contact_tilt_max_speed=config.contact_tilt_max_speed,
                target_tolerance_xy=config.target_tolerance_xy,
                stroke_junction_tolerance=config.stroke_junction_tolerance,
                step_limit_reached=not (terminated or truncated),
                termination_reason=str(info.get("termination_reason", "running")),
                final_target_index=int(info.get("target_index", env._target_index)),
                final_target_count=int(info.get("target_count", len(env.waypoints))),
                final_phase=str(info.get("phase", "")),
                final_brushwork_phase=str(info.get("brushwork_phase", "")),
                final_stroke_index=int(info.get("stroke_index", 0)),
                final_distance_xy=float(info.get("distance_xy", 0.0)),
                final_distance_z=float(info.get("distance_z", 0.0)),
                final_target_dwell=int(info.get("target_dwell", env._target_dwell)),
                final_pen_down=bool(info.get("pen_down", False)),
                final_contact_force=float(info.get("contact_force", 0.0)),
                final_pressure=float(info.get("pressure", 0.0)),
                final_target_pressure=float(info.get("target_pressure", 0.0)),
                final_pressure_offset_m=float(
                    info.get("contact_pressure_offset", env._contact_pressure_offset)
                ),
                final_actual_angle_deg=float(info.get("brush_lean_deg", 0.0)),
                final_target_angle_deg=float(info.get("target_lean_deg", 0.0)),
                final_brush_position_m=env.brush_position.tolist(),
                final_target_position_m=env.target_position.tolist(),
                final_joint_position_deg=np.degrees(
                    env.data.qpos[env._qpos_indices]
                ).tolist(),
                final_joint_target_deg=np.degrees(env._joint_targets).tolist(),
                final_expert_action=env.expert_action().tolist(),
                tilt_prepare_goal_count=len(env._tilt_prepare_goals),
                unavailable_tilt_prepare_goal_count=len(
                    env._unavailable_tilt_prepare_goals
                ),
                attachment_axis_error_median_deg=(
                    float(np.median(all_axis_errors)) if len(all_axis_errors) else 0.0
                ),
                attachment_axis_error_p90_deg=(
                    float(np.percentile(all_axis_errors, 90))
                    if len(all_axis_errors)
                    else 0.0
                ),
                attachment_entry_error_median_deg=(
                    float(np.median(axis_errors["entry"]))
                    if axis_errors["entry"]
                    else 0.0
                ),
                attachment_finish_error_median_deg=(
                    float(np.median(axis_errors["finish"]))
                    if axis_errors["finish"]
                    else 0.0
                ),
                endpoint_triangle_count=int(endpoint["count"]),
                endpoint_triangle_mean=float(endpoint["mean"]),
                endpoint_triangle_minimum=float(endpoint["minimum"]),
                endpoint_scores=list(env._endpoint_scores),
                pressure_probe={
                    "enabled": args.pressure_probe_offset_m is not None,
                    "offset_m": args.pressure_probe_offset_m,
                    "feedback_gain": 0.0
                    if args.pressure_probe_offset_m is not None
                    else None,
                },
            )
            results.append(result)
            if args.images_dir is not None:
                from PIL import Image

                args.images_dir.mkdir(parents=True, exist_ok=True)
                name = f"{ord(character):05x}-{character}-layout-{layout_index}.png"
                rgb = (255.0 * np.clip(env.ink.rgb_image(), 0.0, 1.0)).astype(
                    np.uint8
                )
                Image.fromarray(rgb).save(args.images_dir / name)
                if env._professional_mask is not None:
                    exemplar_dir = args.images_dir / "exemplars"
                    exemplar_dir.mkdir(exist_ok=True)
                    paper = np.asarray([0.98, 0.97, 0.91], dtype=np.float64)
                    ink = np.asarray([0.025, 0.018, 0.012], dtype=np.float64)
                    alpha = np.clip(env._professional_mask[..., None], 0.0, 1.0)
                    exemplar = paper * (1.0 - alpha) + ink * alpha
                    Image.fromarray((255.0 * exemplar).astype(np.uint8)).save(
                        exemplar_dir / name
                    )
            print(
                f"{result['character']:2s}/{layout_index} {result['strokes']:3d} "
                f"{1000 * result['median_width']:6.2f} "
                f"{1000 * result['actual_width_median']:6.2f} "
                f"{result['width_ratio_median']:5.2f} "
                f"{result['pressure_error_median']:+6.3f} "
                f"{result['pressure_error_p90_abs']:6.3f} "
                f"{result['writing_samples']:6d} {result['merged_pairs']:5d} "
                f"{result['exemplar_holes']:5d}/{result['render_holes']:<5d}"
            )
    env.close()

    merged_total = sum(r["merged_pairs"] for r in results)
    lost_total = sum(r["lost_holes"] for r in results)
    succeeded = sum(bool(r["is_success"]) for r in results)
    endpoint_count = sum(int(r["endpoint_triangle_count"]) for r in results)
    endpoint_mean = (
        sum(
            float(r["endpoint_triangle_mean"]) * int(r["endpoint_triangle_count"])
            for r in results
        )
        / endpoint_count
        if endpoint_count
        else 100.0
    )
    endpoint_improvement: float | None = None
    if args.upright_baseline is not None:
        baseline_data = json.loads(args.upright_baseline.read_text(encoding="utf-8"))
        baseline_summary = (
            baseline_data.get("summary", {})
            if isinstance(baseline_data, dict)
            else {}
        )
        endpoint_improvement = endpoint_mean - float(
            baseline_summary.get("endpoint_triangle_mean", 100.0)
        )
    calibration_samples = [
        sample
        for result in results
        for sample in result.get("pressure_calibration_samples", [])
    ]
    calibration_count = len(calibration_samples)
    clip_rate = (
        sum(bool(sample.get("clipped", False)) for sample in calibration_samples)
        / calibration_count
        if calibration_count
        else 0.0
    )
    fallback_rate = (
        sum(bool(sample.get("fallback", False)) for sample in calibration_samples)
        / calibration_count
        if calibration_count
        else 0.0
    )
    gate_level = args.gate_level or (
        1 if len(results) == 18 else 2 if len(results) == 60 else 3 if len(results) == 768 else 0
    )
    summary = summarize_physical_gate(
        results,
        gate_level=gate_level,
        endpoint_improvement=endpoint_improvement,
        calibration_clip_rate=clip_rate,
        calibration_fallback_rate=fallback_rate,
        clip_rate_limit=config.pressure_calibration_clip_rate_limit,
        fallback_rate_limit=args.pressure_calibration_fallback_rate_limit,
        threshold_profile=args.threshold_profile,
    )
    summary.update({
        "merged_pairs": merged_total,
        "endpoint_triangle_count": endpoint_count,
        "endpoint_triangle_mean": endpoint_mean,
        "endpoint_improvement_over_upright": endpoint_improvement,
        "configuration_fingerprint": configuration_fingerprint(config),
        "pressure_calibration_samples": calibration_count,
        "pressure_probe": {
            "enabled": args.pressure_probe_offset_m is not None,
            "offset_m": args.pressure_probe_offset_m,
            "feedback_gain": 0.0
            if args.pressure_probe_offset_m is not None
            else None,
        },
    })
    calibration_sha256 = None
    if args.pressure_calibration is not None and args.pressure_calibration.is_file():
        calibration_sha256 = hashlib.sha256(
            args.pressure_calibration.read_bytes()
        ).hexdigest()
    run_metadata = collect_run_metadata(
        purpose="stroke-merge physical gate diagnostic",
        parent_model=args.model,
        started_at=started_at,
        cwd=Path(__file__).resolve().parents[1],
        extra={
            "device": args.device,
            "calibration_sha256": calibration_sha256,
            "accepted": bool(summary["passed"]),
        },
    )
    run_metadata["elapsed_seconds"] = time.monotonic() - started
    run_metadata["status"] = "passed" if summary["passed"] else "failed"
    summary["calibration_sha256"] = calibration_sha256
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"summary": summary, "results": results, "run": run_metadata},
            ensure_ascii=False,
            indent=2,
            default=float,
        ),
        encoding="utf-8",
    )
    print(
        f"\n完筆 {succeeded}/{len(results)} / 癒着ペア合計 {merged_total} / "
        f"消えた穴合計 {lost_total}"
    )
    print(f"物理ゲート ready_for_cuda={summary['ready_for_cuda']}")
    print(f"-> {args.output}")


if __name__ == "__main__":
    main()
