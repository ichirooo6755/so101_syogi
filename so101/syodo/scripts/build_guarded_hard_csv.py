#!/usr/bin/env python3
"""Build a guarded hard-mining CSV from baseline vs candidate joyo evals."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

REP19 = "一十書水永竜道飛鬱田園央案支誠措八拷砕"


@dataclass(frozen=True)
class CharDiff:
    character: str
    ab_lw: float
    ab_bw: float
    ab_glyph: float
    ab_beauty: float
    cand_lw: float
    cand_bw: float
    cand_glyph: float
    cand_beauty: float

    @property
    def lw_delta(self) -> float:
        return self.cand_lw - self.ab_lw

    @property
    def bw_delta(self) -> float:
        return self.cand_bw - self.ab_bw

    @property
    def glyph_delta(self) -> float:
        return self.cand_glyph - self.ab_glyph

    @property
    def lw_regressed(self) -> bool:
        return self.lw_delta < -1.0

    @property
    def bw_regressed(self) -> bool:
        return self.bw_delta < -1.0

    @property
    def ab_weak_glyph(self) -> bool:
        return self.ab_glyph < 55.0

    @property
    def ab_weak_bw(self) -> bool:
        return self.ab_bw < 62.0

    @property
    def ab_weak_lw(self) -> bool:
        return self.ab_lw < 65.0

    @property
    def train_score(self) -> float:
        """Higher = better guarded training target."""
        score = 0.0
        if self.ab_weak_glyph:
            score += max(0.0, 55.0 - self.ab_glyph) * 0.15
        if self.ab_weak_bw:
            score += max(0.0, 62.0 - self.ab_bw) * 0.10
        if self.ab_weak_lw:
            score += max(0.0, 65.0 - self.ab_lw) * 0.08
        if self.glyph_delta > 0:
            score += min(self.glyph_delta, 20.0) * 0.05
        if self.lw_regressed:
            score -= 8.0
        if self.bw_regressed:
            score -= 8.0
        if self.character in REP19:
            score += 5.0
        return score


def _load(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return {row["character"]: dict(row) for row in reader}


def _float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def build_diffs(baseline: Path, candidate: Path) -> list[CharDiff]:
    ab_rows = _load(baseline)
    cand_rows = _load(candidate)
    missing = sorted(set(ab_rows) - set(cand_rows))
    if missing:
        raise SystemExit(f"candidate missing {len(missing)} chars, e.g. {missing[:5]}")
    diffs: list[CharDiff] = []
    for character, ab in ab_rows.items():
        cand = cand_rows[character]
        diffs.append(
            CharDiff(
                character=character,
                ab_lw=_float(ab, "line_width"),
                ab_bw=_float(ab, "brushwork"),
                ab_glyph=_float(ab, "glyph_shape"),
                ab_beauty=_float(ab, "beauty_score"),
                cand_lw=_float(cand, "line_width"),
                cand_bw=_float(cand, "brushwork"),
                cand_glyph=_float(cand, "glyph_shape"),
                cand_beauty=_float(cand, "beauty_score"),
            )
        )
    return diffs


def select_targets(
    diffs: list[CharDiff],
    *,
    max_chars: int,
    lw_guard: float,
    bw_guard: float,
) -> tuple[list[CharDiff], dict[str, int]]:
    rep = [d for d in diffs if d.character in REP19]
    pool = [
        d
        for d in diffs
        if d.character not in REP19
        and (d.ab_weak_glyph or d.ab_weak_bw or d.ab_weak_lw)
        and d.ab_lw >= 65.0 - lw_guard
        and d.ab_bw >= 62.0 - bw_guard
        and not (d.lw_regressed and d.bw_regressed)
    ]
    pool.sort(key=lambda d: d.train_score, reverse=True)
    budget = max(0, max_chars - len(rep))
    selected = rep + pool[:budget]
    stats = {
        "total": len(diffs),
        "rep19": len(rep),
        "pool_eligible": len(pool),
        "selected": len(selected),
        "lw_regress_both": sum(1 for d in diffs if d.lw_regressed and d.bw_regressed),
        "glyph_improved": sum(1 for d in diffs if d.glyph_delta > 1.0),
        "ab_still_best_beauty": sum(
            1 for d in diffs if d.ab_beauty >= d.cand_beauty
        ),
    }
    return selected, stats


def write_outputs(
    *,
    baseline_rows: dict[str, dict[str, str]],
    selected: list[CharDiff],
    output_csv: Path,
    report_md: Path,
    stats: dict[str, int],
    baseline_label: str,
    candidate_label: str,
) -> None:
    fieldnames = tuple(baseline_rows[next(iter(baseline_rows))].keys())
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for diff in selected:
            writer.writerow(baseline_rows[diff.character])

    lines = [
        f"# {baseline_label} vs {candidate_label} 差分診断",
        "",
        "## サマリ",
        "",
        f"| 項目 | 値 |",
        f"|---|---:|",
    ]
    for key, value in stats.items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 選定方針",
            "",
            "- 親は visual-ab、改善対象は glyph_shape / brushwork / harai 弱字",
            "- lw/bw が baseline 比 -1pt 以上後退した字は除外",
            "- 代表19字は常に含める",
            "",
            f"## 選定 {len(selected)} 字（hard-mining 用）",
            "",
            "| 字 | ab_glyph | cand_glyph | Δglyph | ab_lw | cand_lw | ab_bw | cand_bw | score |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for diff in sorted(selected, key=lambda d: d.train_score, reverse=True):
        lines.append(
            f"| {diff.character} | {diff.ab_glyph:.1f} | {diff.cand_glyph:.1f} | "
            f"{diff.glyph_delta:+.1f} | {diff.ab_lw:.1f} | {diff.cand_lw:.1f} | "
            f"{diff.ab_bw:.1f} | {diff.cand_bw:.1f} | {diff.train_score:.1f} |"
        )
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    meta = {
        "baseline": baseline_label,
        "candidate": candidate_label,
        "stats": stats,
        "characters": [d.character for d in selected],
    }
    output_csv.with_name("pool.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--max-chars", type=int, default=250)
    parser.add_argument("--lw-guard", type=float, default=1.0)
    parser.add_argument("--bw-guard", type=float, default=1.0)
    args = parser.parse_args()

    diffs = build_diffs(args.baseline, args.candidate)
    baseline_rows = _load(args.baseline)
    selected, stats = select_targets(
        diffs,
        max_chars=args.max_chars,
        lw_guard=args.lw_guard,
        bw_guard=args.bw_guard,
    )
    write_outputs(
        baseline_rows=baseline_rows,
        selected=selected,
        output_csv=args.output,
        report_md=args.report,
        stats=stats,
        baseline_label=args.baseline.parent.name,
        candidate_label=args.candidate.parent.name,
    )
    print(f"wrote {args.output} ({len(selected)} chars)")
    print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
