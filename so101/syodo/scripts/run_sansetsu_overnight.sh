#!/bin/zsh
# 三折法（トン・スー・トン）を実際に実行させるための夜通し再適応。
#
# 前提となる修正（すべて 12 字 IK 天井で A/B 済み）:
#   1. contact_pressure_gain 0.0050 -> 0.0150 / limit 0.0035 -> 0.0040
#      指令した筆圧に追従できず（誤差 0.135）、横画は「太・細・太」を計画しても
#      実行は単調増加の楔だった（契り 0.99）。0.020 以上は過補正で払いが崩れる。
#   2. EnvConfig.entry_descent_ratio = 0.55
#      起筆の保持 8 点がすべて同一座標で、Z 許容の内側にいる限り即座に到達判定
#      されて消費され、穂が沈む時間が無かった（起筆 計画 13.4mm / 実行 9.8mm）。
#      「浅く触れる → 座る」の行程にして、実際に降りないと進めなくする。
#   3. 技法別ゲイン係数 払い 1.4 -> 1.6 / はね 0.35 -> 0.20（IoU +1.0 / glyph +0.9）
#
#   効果（12 字 IK 天井）: 契り 0.99 -> 1.08、圧誤差 0.135 -> 0.086、
#   払い finish +8.5、線幅 +5.6、IoU は基準以上に回復。はね -2.0 が唯一の後退。
#
#   不採択: 収筆 3 拍（止め -15.5）／筆圧ゲート（払い -3.0）／
#           筆圧の上下動拡大・Z 許容厳格化・穂の開き飽和解除（いずれも契り不変）
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

RUN=${RUN:-kaisho-yohitsu-sansetsu}
OUT=runs/${RUN}
EVALDIR=runs/${RUN}-joyo-eval
LOG=runs/${RUN}-train.log
MASTER=runs/${RUN}-overnight.log
PIDFILE=runs/${RUN}.pid
PARENT=${PARENT:-runs/kaisho-yohitsu-stroke-separation/final_model.zip}
BASELINE=${BASELINE:-runs/kaisho-yohitsu-stroke-separation-joyo-eval}
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
  echo "- change 1: contact_pressure_gain 0.0150 / limit 0.0040"
  echo "- change 2: entry_descent_ratio 0.55（起筆の沈み込み）"
  echo "- change 3: 技法別ゲイン 払い1.6 / はね0.20"
  echo "- stages: 5(radicals) .. 8(joyo), hard-mining なし"
  echo "- timesteps: $TIMESTEPS / stage"
  echo "- expected: 起筆に押しが出て太細太になる。払い・線幅の改善、はねは -2 まで許容"
} | tee "$OUT/launcher.md" | tee -a "$MASTER"

log "training start (remaining $(seconds_left)s)"
so101-train-professional \
  --ablation all \
  --run-purpose "三折法を実行させるための再適応（contact_pressure_gain/limit 強化, stage5-8）" \
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
  --seed 91 \
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
  --seed 91 \
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
