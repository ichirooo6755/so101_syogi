#!/bin/zsh
# 字形補正後の適応不足を埋めるための継続学習。
#
# 前提:
#   exemplar_shape_fit=1.0 / exemplar_density_fit=0.5 は導入済み（commit aa54010）。
#   1 回目の学習 kaisho-yohitsu-shapefit は glyph_shape 59.03->62.25 と改善したが、
#   line_width -1.34 / brushwork -1.56 で非退行チェックに落ちて不採択。
#
#   天井との差: shapefit の lw は天井 90.36 に対し 86.96（-3.40）、
#   sansetsu は天井 90.97 に対し 88.29（-2.68）。shapefit のほうが天井から遠く、
#   大きな幾何変更に 1 回の学習では追いつけていない = 方策の適応不足が主因。
#   IK 天井で見た変更そのものの代償は lw -0.6 / bw -0.9 にとどまる。
#
#   そこで shapefit を親に同設定で継続学習し、天井との差を詰める。
#   非退行の基準は現ベストの sansetsu のまま（shapefit は不採択なので基準にしない）。
#
# 方針は contact-fix と同じ「hard-mining なしの広い再適応」。
#   教訓: 同一親からの hard-mining 連打は lw/bw を壊す
#   （docs/results/2026-08-18-current-challenges.md）。
#
# 非退行の基準は現ベストの harai-finish。
set -euo pipefail

if [[ -z "${SYODO_CAFFEINATE:-}" ]] && command -v caffeinate >/dev/null; then
  export SYODO_CAFFEINATE=1
  exec caffeinate -dims -- "$0" "$@"
fi

cd /Users/sugawaraichirou/Documents/syodo
source .venv/bin/activate
export PYTHONPATH=src PYTHONUNBUFFERED=1
export MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mplconfig-syodo
export PYTHONPYCACHEPREFIX=/tmp/pycache-syodo
mkdir -p "$MPLCONFIGDIR" "$PYTHONPYCACHEPREFIX" docs/results

RUN=${RUN:-kaisho-yohitsu-shapefit-cont}
OUT=runs/${RUN}
EVALDIR=runs/${RUN}-joyo-eval
LOG=runs/${RUN}-train.log
MASTER=runs/${RUN}-overnight.log
PIDFILE=runs/${RUN}.pid
PARENT=${PARENT:-runs/kaisho-yohitsu-shapefit/final_model.zip}
BASELINE=${BASELINE:-runs/kaisho-yohitsu-sansetsu-joyo-eval}
FONT=$(cat runs/selected-exemplar-font.txt)
DEADLINE=${DEADLINE:-"2026-08-20 07:00:00"}
# contact-fix の実績: 1.2M steps x stage5-8 で 5h11m、全数評価 8 シャードで 27分。
TIMESTEPS=${TIMESTEPS:-1300000}
EVAL_RESERVE_SEC=${EVAL_RESERVE_SEC:-3000}

mkdir -p "$OUT"
echo $$ > "$PIDFILE"
log() { echo "==== $(date '+%Y-%m-%d %H:%M:%S %Z') $* ====" | tee -a "$MASTER"; }

seconds_left() {
  python3 - "$DEADLINE" <<'PY'
from datetime import datetime
import sys, time
from zoneinfo import ZoneInfo
dt = datetime.strptime(sys.argv[1], "%Y-%m-%d %H:%M:%S").replace(
    tzinfo=ZoneInfo("Asia/Tokyo")
)
print(max(0, int(dt.timestamp() - time.time())))
PY
}

if [[ ! -f "$PARENT" ]]; then
  log "parent model missing: $PARENT"
  exit 1
fi
if pgrep -f "so101-train-professional" >/dev/null 2>&1; then
  log "training already running; abort duplicate launch"
  exit 0
fi

{
  echo "# ${RUN} launcher"
  echo "- started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "- deadline: $DEADLINE"
  echo "- parent: $PARENT"
  echo "- baseline: $BASELINE"
  echo "- exemplar: $FONT"
  echo "- change 1: exemplar_shape_fit 1.0（字の外形比）"
  echo "- change 2: exemplar_density_fit 0.5（字ごとの線の太さ）"
  echo "- stages: 5(radicals) .. 8(joyo), hard-mining なし"
  echo "- timesteps: $TIMESTEPS / stage"
  echo "- expected: glyph_shape を保ったまま lw/bw が天井へ近づき非退行になる"
} | tee "$OUT/launcher.md" | tee -a "$MASTER"

log "training start (remaining $(seconds_left)s)"
so101-train-professional \
  --ablation all \
  --run-purpose "字形補正後の適応不足を埋める継続学習（shapefit 親, stage5-8）" \
  --initial-model "$PARENT" \
  --exemplar-font "$FONT" \
  --start-stage 5 --end-stage 8 \
  --timesteps "$TIMESTEPS" --kana-timesteps "$TIMESTEPS" \
  --bc-steps 120000 --kana-bc-steps 120000 --bc-epochs 5 \
  --n-envs 6 --bc-workers 6 \
  --n-steps 2048 --batch-size 768 \
  --learning-rate 3e-4 \
  --device mps --allow-gate-failure \
  --stage-eval-size 64 --eval-limit 128 \
  --output "$OUT" \
  --seed 111 \
  >> "$LOG" 2>&1

MODEL="$OUT/final_model.zip"
if [[ ! -f "$MODEL" ]]; then
  log "training finished without final_model.zip; see $LOG"
  exit 1
fi
log "training done -> $MODEL"

LEFT=$(seconds_left)
if (( LEFT < EVAL_RESERVE_SEC )); then
  log "only ${LEFT}s before deadline; skip full joyo evaluation (run it in the morning)"
  echo "AGENT_NOTIFY_TRAIN_DONE_EVAL_SKIPPED model=$MODEL" | tee -a "$MASTER"
  exit 0
fi

log "full joyo evaluation (8 shards) -> $EVALDIR"
python3 -u scripts/evaluate_joyo_shards.py \
  --model "$MODEL" \
  --output "$EVALDIR" \
  --shards 8 \
  --device cpu \
  --seed 111 \
  --exemplar-font "$FONT" \
  >> "$LOG" 2>&1

log "non-regression check against $BASELINE"
python3 - "$EVALDIR/summary.json" "$BASELINE" >> "$MASTER" 2>&1 <<'PY'
import csv, json, sys
from pathlib import Path

BASELINE = Path(sys.argv[2])


def digest(directory: Path) -> dict[str, float]:
    summary = json.loads((directory / "summary.json").read_text())
    scores = summary["evaluation"]
    rows = list(csv.DictReader((directory / "characters.csv").open(encoding="utf-8-sig")))
    both = sum(
        1
        for row in rows
        if float(row["line_width"]) >= 65.0 and float(row["brushwork"]) >= 62.0
    )
    means = scores["component_means"]
    harai = (scores.get("technique_means") or {}).get("harai") or {}
    return {
        "beauty": float(scores["mean_beauty_score"]),
        "line_width": means["line_width"],
        "brushwork": means["brushwork"],
        "glyph_shape": means["glyph_shape"],
        "harai_finish": float(harai.get("finish", 0.0)),
        "per_char": 100.0 * both / max(len(rows), 1),
        "success": 100.0 * float(scores["success_rate"]),
    }


new = digest(Path(sys.argv[1]).parent)
old = digest(BASELINE) if (BASELINE / "summary.json").is_file() else None
print(f"{'metric':14s} {'baseline':>9s} {'new':>9s} {'delta':>8s}")
regressions = []
for key, value in new.items():
    if old is None:
        print(f"{key:14s} {'-':>9s} {value:9.2f} {'-':>8s}")
        continue
    delta = value - old[key]
    print(f"{key:14s} {old[key]:9.2f} {value:9.2f} {delta:+8.2f}")
    if key in ("line_width", "brushwork", "per_char", "success") and delta < -1.0:
        regressions.append(f"{key} {delta:+.2f}")
print()
print(f"払い finish 65 ゲート: {'PASS' if new['harai_finish'] >= 65.0 else 'FAIL'} ({new['harai_finish']:.2f})")
print(f"完筆 100% ゲート:      {'PASS' if new['success'] >= 100.0 else 'FAIL'} ({new['success']:.2f}%)")
print()
if regressions:
    print("REGRESSION: " + ", ".join(regressions))
    print("→ contact-fix を保持し、この run は採択しないこと。")
else:
    print("NO REGRESSION: 新しい親として採用可。")
PY

log "overnight pipeline complete"
echo "AGENT_NOTIFY_OVERNIGHT_DONE eval=$EVALDIR" | tee -a "$MASTER"
