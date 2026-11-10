"""Select a non-regressing calligraphy model from evaluation summaries."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from so101_calligraphy.training.model_selection import load_snapshot, select_best


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summaries", nargs="+", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("runs/model-selection.json")
    )
    args = parser.parse_args()

    candidates = [load_snapshot(path) for path in args.summaries]
    baseline = load_snapshot(args.baseline) if args.baseline else None
    selected = select_best(candidates, baseline=baseline)
    payload = {
        "selected": asdict(selected),
        "baseline": None if baseline is None else asdict(baseline),
        "candidates": [asdict(candidate) for candidate in candidates],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(selected.source)


if __name__ == "__main__":
    main()
