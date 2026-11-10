"""代表19字を IK エキスパート天井（action=0）で回し、払い finish の条件比較をする。

報酬側の修正は IK 天井には現れない。ここで測るのは軌道・物理側の天井。

    python3 scripts/ab_harai_ik_ceiling.py
    python3 scripts/ab_harai_ik_ceiling.py --only baseline
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.training.professional import (
    IndexedTrajectories,
    professional_config,
)
from so101_calligraphy.trajectory.education import (
    lazy_joyo_trajectories,
    load_joyo_kanji,
)
from so101_calligraphy.trajectory.profile import resolve_technique

REPRESENTATIVE = "一十書水永竜道飛鬱田園央案支誠措八拷砕"
FONT = Path((ROOT / "runs/selected-exemplar-font.txt").read_text().strip())

CONDITIONS: dict[str, dict[str, object]] = {
    "baseline": {},
    "plimit0025": {"contact_pressure_limit": 0.0025},
    "plimit0035": {"contact_pressure_limit": 0.0035},
    "clearance0012": {"brush.release_clearance": 0.0012},
    "plimit0025_clear0012": {
        "contact_pressure_limit": 0.0025,
        "brush.release_clearance": 0.0012,
    },
}


def build_config(overrides: dict[str, object]):
    config = professional_config("all", motoya_font_path=FONT)
    nested: dict[str, dict[str, object]] = {}
    flat: dict[str, object] = {}
    for key, value in overrides.items():
        if "." in key:
            group, name = key.split(".", 1)
            nested.setdefault(group, {})[name] = value
        else:
            flat[key] = value
    for group, values in nested.items():
        flat[group] = replace(getattr(config, group), **values)
    return replace(config, **flat) if flat else config


def run_condition(name: str, overrides: dict[str, object]) -> dict[str, object]:
    entries = load_joyo_kanji(ROOT / "data/kanjidic2")
    index_of = {entry.character: i for i, entry in enumerate(entries)}
    selected = tuple(index_of[c] for c in REPRESENTATIVE)
    dataset = lazy_joyo_trajectories(
        entries,
        kanjivg_cache=ROOT / "data/kanjivg",
        animcjk_cache=ROOT / "data/animcjk",
        use_animcjk_medians=True,
    )
    env = CalligraphyEnv(
        task="professional-evaluation-all",
        trajectories=IndexedTrajectories(dataset, selected),
        config=build_config(overrides),
    )
    technique: dict[str, list[float]] = {"tome": [], "hane": [], "harai": []}
    rows: list[dict[str, float | str]] = []
    try:
        for local_index, char in enumerate(REPRESENTATIVE):
            observation, _ = env.reset(
                seed=17 + selected[local_index],
                options={"trajectory_index": local_index},
            )
            info: dict = {}
            while True:
                observation, _, terminated, truncated, info = env.step(
                    np.zeros(6, dtype=np.float32)
                )
                if terminated or truncated:
                    break
            components = info["beauty_components"]
            rows.append(
                {
                    "character": char,
                    "success": float(bool(info["is_success"])),
                    "beauty": float(info["beauty_score"]),
                    "glyph_shape": float(components["glyph_shape"]),
                    "line_width": float(components["line_width"]),
                    "brushwork": float(components["brushwork"]),
                }
            )
            for stroke_index, metrics in env._stroke_scores.items():
                family = resolve_technique(env.trajectory.strokes[stroke_index])
                technique[family].append(100.0 * metrics["finish"])
            print(f"  {name} {local_index + 1}/{len(REPRESENTATIVE)} {char}", flush=True)
    finally:
        env.close()

    def mean(values: list[float]) -> float:
        return float(np.mean(values)) if values else 0.0

    gate = sum(
        1
        for r in rows
        if float(r["line_width"]) >= 65.0 and float(r["brushwork"]) >= 62.0
    )
    return {
        "condition": name,
        "beauty": mean([float(r["beauty"]) for r in rows]),
        "glyph": mean([float(r["glyph_shape"]) for r in rows]),
        "lw": mean([float(r["line_width"]) for r in rows]),
        "bw": mean([float(r["brushwork"]) for r in rows]),
        "harai": mean(technique["harai"]),
        "hane": mean(technique["hane"]),
        "tome": mean(technique["tome"]),
        "gate": f"{gate}/{len(rows)}",
        "success": mean([float(r["success"]) for r in rows]) * 100.0,
        "per_char": {str(r["character"]): round(float(r["brushwork"]), 1) for r in rows},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "runs/ab-harai-ik-ceiling.json",
    )
    args = parser.parse_args()
    names = args.only or list(CONDITIONS)
    results = []
    header = (
        f"{'condition':22s} {'beauty':>7s} {'lw':>6s} {'bw':>6s} "
        f"{'harai':>6s} {'hane':>6s} {'tome':>6s} {'gate':>6s} {'完筆':>6s}"
    )
    for name in names:
        result = run_condition(name, CONDITIONS[name])
        results.append(result)
        if len(results) == 1:
            print(header, flush=True)
        print(
            f"{result['condition']:22s} {result['beauty']:7.1f} {result['lw']:6.1f} "
            f"{result['bw']:6.1f} {result['harai']:6.1f} {result['hane']:6.1f} "
            f"{result['tome']:6.1f} {result['gate']:>6s} {result['success']:5.0f}%",
            flush=True,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n-> {args.output}")
    print("\n八 の brushwork（左右払いの対称性）:")
    for result in results:
        print(f"  {result['condition']:22s} 八={result['per_char'].get('八')}")


if __name__ == "__main__":
    main()
