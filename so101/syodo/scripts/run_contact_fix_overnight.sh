#!/bin/zsh
# 接地筆圧フィードバック導入後の再適応を朝まで回す。
#
# 背景: 位置サーボ単独では接触抗力とつり合う深さで穂先が止まり、目標より
# 0.3-0.5mm 沈み込んだまま書いていた。IK エキスパート天井(19字)で
#   line_width 67.0 -> 83.6 / brushwork 65.3 -> 76.4 / 字単位ゲート 11/19 -> 18/19
# を確認済み（docs/results/2026-08-19-contact-pressure-fix.md）。
# 方針は「hard-mining をやめ、環境変更に対する広い再適応」。
#   docs/results/2026-08-18-current-challenges.md の教訓:
#   同一親からの hard-mining 連打は lw/bw を壊す。
#
# SSD復旧プロセスには触らない。
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

RUN=${RUN:-kaisho-yohitsu-contact-fix}
OUT=runs/${RUN}
EVAL=runs/${RUN}-joyo-eval
LOG=runs/${RUN}-train.log
MASTER=runs/${RUN}-overnight.log
PIDFILE=runs/${RUN}.pid
PARENT=${PARENT:-runs/kaisho-yohitsu-visual-ab/final_model.zip}
FONT=$(cat runs/selected-exemplar-font.txt)
DEADLINE=${DEADLINE:-"2026-08-19 07:00:00"}
# 全数評価(8シャード)に確保する時間。これを切ったら評価は翌朝に回す。
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
  echo "- exemplar: $FONT"
  echo "- change: EnvConfig.contact_pressure_gain=0.0050 / limit=0.0015"
  echo "- stages: 5(radicals) .. 8(joyo), hard-mining なし"
  echo "- parallel: n_envs=6 bc_workers=6 device=mps"
  echo "- expected: 字単位 lw>=65 かつ bw>=62 が 95% 以上、払い finish の改善"
} | tee "$OUT/launcher.md" | tee -a "$MASTER"

log "training start (remaining $(seconds_left)s)"
so101-train-professional \
  --ablation all \
  --run-purpose "接地筆圧フィードバック導入後の再適応（stage5-8, hard-mining なし）" \
  --initial-model "$PARENT" \
  --exemplar-font "$FONT" \
  --start-stage 5 --end-stage 8 \
  --timesteps 1200000 --kana-timesteps 1200000 \
  --bc-steps 120000 --kana-bc-steps 120000 --bc-epochs 5 \
  --n-envs 6 --bc-workers 6 \
  --n-steps 2048 --batch-size 768 \
  --learning-rate 3e-4 \
  --device mps --allow-gate-failure \
  --stage-eval-size 64 --eval-limit 128 \
  --output "$OUT" \
  --seed 51 \
  >> "$LOG" 2>&1

MODEL="$OUT/final_model.zip"
if [[ ! -f "$MODEL" ]]; then
  log "training finished without final_model.zip; see $LOG"
  exit 1
fi
log "training done -> $MODEL"

LEFT=$(seconds_left)
if (( LEFT < EVAL_RESERVE_SEC )); then
  log "only ${LEFT}s before deadline; skip full joyo eval (run it in the morning)"
  echo "AGENT_NOTIFY_TRAIN_DONE_EVAL_SKIPPED model=$MODEL" | tee -a "$MASTER"
  exit 0
fi

log "full joyo evaluation (8 shards) -> $EVAL"
python3 -u scripts/evaluate_joyo_shards.py \
  --model "$MODEL" \
  --output "$EVAL" \
  --shards 8 \
  --device cpu \
  --seed 51 \
  --exemplar-font "$FONT" \
  >> "$LOG" 2>&1

log "non-regression check against the retained visual-ab baseline"
python3 - "$EVAL/summary.json" >> "$MASTER" 2>&1 <<'PY'
import csv, json, sys
from pathlib import Path

BASELINE = Path("runs/kaisho-yohitsu-visual-ab-morisawa-joyo-eval")


def digest(directory: Path) -> dict[str, float]:
    summary = json.loads((directory / "summary.json").read_text())
    evaluation = summary["evaluation"]
    rows = list(csv.DictReader((directory / "characters.csv").open(encoding="utf-8-sig")))
    both = sum(
        1
        for row in rows
        if float(row["line_width"]) >= 65.0 and float(row["brushwork"]) >= 62.0
    )
    means = evaluation["component_means"]
    harai = (evaluation.get("technique_means") or {}).get("harai") or {}
    return {
        "beauty": float(evaluation["mean_beauty_score"]),
        "line_width": means["line_width"],
        "brushwork": means["brushwork"],
        "glyph_shape": means["glyph_shape"],
        "harai_finish": float(harai.get("finish", 0.0)),
        "per_char": 100.0 * both / max(len(rows), 1),
        "success": 100.0 * float(evaluation["success_rate"]),
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
    if key in ("line_width", "brushwork", "per_char") and delta < -1.0:
        regressions.append(f"{key} {delta:+.2f}")
print()
if regressions:
    print("REGRESSION: " + ", ".join(regressions))
    print("→ visual-ab を保持し、contact-fix は採択しないこと。")
else:
    print("NO REGRESSION: contact-fix を新しい親として採用可。")
PY

log "overnight pipeline complete"
echo "AGENT_NOTIFY_OVERNIGHT_DONE eval=$EVAL" | tee -a "$MASTER"
