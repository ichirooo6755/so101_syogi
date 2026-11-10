#!/bin/zsh
# 線を太らせすぎず、くっつくべきでない画を癒着させないための夜通し再適応。
#
# 前提となる2つの修正:
#   1. BrushConfig.tuft_opening 1.12 -> 1.34
#      用筆プランナは穂先の開きを定数 1.12 と仮定していたが、墨モデルは筆の
#      曲がりに応じて 1.0-1.25 まで開く。このため同じ筆圧でも実際の墨は目標幅
#      より 12-18% 太く、「細いつもりで太く書く」状態だった。実測に合わせて
#      較正（IK 天井で実測幅/目標幅 1.16 -> 1.02）。
#      IK 天井の効果: beauty 83.5->84.7 / lw 83.4->85.8 / bw 79.7->83.6 /
#      harai finish 66.7->71.6。
#   2. EnvConfig.stroke_minimum_gap=0.0015（画間クリアランス）
#      交差・T 字接合の相手とはつながったまま、それ以外の画とは白を残すよう
#      混み合った箇所だけ筆圧を落とす。字全体を一律に細くはしない。
#      お手本基準の超過癒着 14 -> 13、lw 85.8->87.0、bw 83.6->84.7。
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

RUN=${RUN:-kaisho-yohitsu-stroke-separation}
OUT=runs/${RUN}
EVALDIR=runs/${RUN}-joyo-eval
LOG=runs/${RUN}-train.log
MASTER=runs/${RUN}-overnight.log
PIDFILE=runs/${RUN}.pid
PARENT=${PARENT:-runs/kaisho-yohitsu-harai-finish/final_model.zip}
BASELINE=${BASELINE:-runs/kaisho-yohitsu-harai-finish-joyo-eval}
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
  echo "- change 1: BrushConfig.tuft_opening 1.12 -> 1.34（幅モデルの較正）"
  echo "- change 2: EnvConfig.stroke_minimum_gap=0.0015（画間クリアランス）"
  echo "- stages: 5(radicals) .. 8(joyo), hard-mining なし"
  echo "- timesteps: $TIMESTEPS / stage"
  echo "- expected: 線幅が手本に近づき、超過癒着が減る。lw/bw/完筆は非退行"
} | tee "$OUT/launcher.md" | tee -a "$MASTER"

log "training start (remaining $(seconds_left)s)"
so101-train-professional \
  --ablation all \
  --run-purpose "線幅較正と画間クリアランス後の再適応（tuft_opening + stroke_minimum_gap, stage5-8）" \
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
  --seed 81 \
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
  --seed 81 \
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
