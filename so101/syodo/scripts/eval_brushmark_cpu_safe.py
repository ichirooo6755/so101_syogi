#!/usr/bin/env python3
"""CPU eval with max_pen_down_dwell so soft-paper contact cannot hang forever."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from so101_calligraphy.training import professional as prof


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--eval-limit", type=int, default=19)
    parser.add_argument("--eval-shard-count", type=int, default=1)
    parser.add_argument("--eval-shard-index", type=int, default=0)
    parser.add_argument("--seed", type=int, default=141)
    parser.add_argument("--dwell", type=int, default=120, help="max_pen_down_dwell steps")
    parser.add_argument("--exemplar-font", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "mps"), default="cpu")
    args = parser.parse_args()

    original = prof.professional_config

    def capped_config(*a, **kw):
        return replace(original(*a, **kw), max_pen_down_dwell=int(args.dwell))

    prof.professional_config = capped_config  # type: ignore[assignment]

    # Print every glyph (default is every 10).
    _evaluate = prof.evaluate

    def evaluate_loud(*a, **kw):
        # Wrap by temporarily patching the module-level loop cadence via source
        # is fragile; instead monkeypatch print by wrapping CalligraphyEnv.step
        # counts in a thin proxy. Keep it simple: call original but force
        # report_every=1 by editing selected length trick — not possible.
        # So just call original; dwell is the hang fix. Progress.json updates
        # every 10 for limit>=100 and every 10 for <100 already.
        return _evaluate(*a, **kw)

    prof.evaluate = evaluate_loud  # type: ignore[assignment]

    sys.argv = [
        "eval_brushmark_cpu_safe",
        "--expert-only",
        "--ablation",
        "all",
        "--initial-model",
        str(args.model.resolve()),
        "--output",
        str(args.output.resolve()),
        "--eval-limit",
        str(args.eval_limit),
        "--eval-shard-count",
        str(args.eval_shard_count),
        "--eval-shard-index",
        str(args.eval_shard_index),
        "--save-all-ink",
        "--device",
        args.device,
        "--seed",
        str(args.seed),
        "--exemplar-font",
        str(args.exemplar_font.resolve()),
    ]
    print(
        f"safe-eval model={args.model} limit={args.eval_limit} "
        f"shard={args.eval_shard_index}/{args.eval_shard_count} dwell={args.dwell}",
        flush=True,
    )
    prof.main()


if __name__ == "__main__":
    main()
