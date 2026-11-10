#!/usr/bin/env python3
"""Evaluate N glyphs one process at a time so soft-paper cannot take down the batch."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--eval-limit", type=int, default=128)
    parser.add_argument("--dwell", type=int, default=120)
    parser.add_argument("--seed", type=int, default=141)
    parser.add_argument("--exemplar-font", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = out / "per_char"
    work.mkdir(exist_ok=True)
    (out / "final" / "ink").mkdir(parents=True, exist_ok=True)
    (out / "final" / "comparisons").mkdir(parents=True, exist_ok=True)

    # Resolve the same 128-sample character list professional.py uses.
    env = {
        **os.environ,
        "PYTHONPATH": str(root / "src"),
        "PYTHONUNBUFFERED": "1",
        "MPLBACKEND": "Agg",
    }
    listing = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "from pathlib import Path\n"
            "from so101_calligraphy.training.professional import _sample_indices\n"
            "from so101_calligraphy.trajectory.education import load_joyo_kanji\n"
            f"entries=load_joyo_kanji(Path('data'))\n"
            f"idx=_sample_indices(tuple(range(len(entries))), {args.eval_limit})\n"
            "print('\\n'.join(f'{i}\\t{entries[i].character}' for i in idx))\n",
        ],
        cwd=root,
        env=env,
        text=True,
    ).strip().splitlines()
    pairs = [line.split("\t", 1) for line in listing if line.strip()]
    print(f"one-proc-per-char n={len(pairs)} dwell={args.dwell}", flush=True)

    rows: list[dict[str, str]] = []
    failed: list[str] = []
    for n, (index, character) in enumerate(pairs, start=1):
        shard_out = work / f"{int(index):05d}-{character}"
        log = shard_out.with_suffix(".log")
        print(f"[{n}/{len(pairs)}] {character}", flush=True)
        # eval-limit=1 with seed offset is not the same index; call a tiny worker
        cmd = [
            sys.executable,
            "-u",
            str(root / "scripts" / "_eval_one_char_worker.py"),
            "--model",
            str(args.model.resolve()),
            "--output",
            str(shard_out),
            "--entry-index",
            index,
            "--dwell",
            str(args.dwell),
            "--seed",
            str(args.seed),
            "--exemplar-font",
            str(args.exemplar_font.resolve()),
            "--device",
            args.device,
        ]
        with open(log, "w", encoding="utf-8") as fh:
            proc = subprocess.run(cmd, cwd=root, env=env, stdout=fh, stderr=subprocess.STDOUT)
        if proc.returncode != 0 or not (shard_out / "row.json").is_file():
            failed.append(character)
            print(f"  FAIL {character} code={proc.returncode}", flush=True)
            continue
        row = json.loads((shard_out / "row.json").read_text(encoding="utf-8"))
        rows.append(row)
        for folder in ("ink", "comparisons"):
            src = shard_out / folder
            if src.is_dir():
                for png in src.glob("*.png"):
                    dest = out / "final" / folder / png.name
                    dest.write_bytes(png.read_bytes())
        (out / "progress.json").write_text(
            json.dumps(
                {
                    "eval_progress": f"{n}/{len(pairs)}",
                    "last_character": character,
                    "failed": failed,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    if not rows:
        raise SystemExit("no successful rows")
    fields = list(rows[0].keys())
    with open(out / "final" / "characters.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    def mean(key: str) -> float:
        vals = [float(r[key]) for r in rows if r.get(key) not in ("", None)]
        return sum(vals) / len(vals)

    summary = {
        "count": len(rows),
        "failed": failed,
        "mean_beauty_score": mean("beauty_score"),
        "component_means": {
            k: mean(k) for k in ("glyph_shape", "line_width", "brushwork") if k in rows[0]
        },
        "width_detail_means": {
            k: mean(k)
            for k in ("taper", "width_contrast", "width_scale", "corner_width", "width_smoothness")
            if k in rows[0]
        },
    }
    # technique means if present as columns — skip; worker can add later
    (out / "summary.json").write_text(
        json.dumps({"evaluation": summary}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    print("ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
