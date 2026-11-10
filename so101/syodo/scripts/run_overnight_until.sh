#!/bin/zsh
# r4 以降も朝まで hard-mining を続ける。現行 c-loop 終了を待ってから r5+ を回す。
# SSD復旧プロセスは触らない。
set -euo pipefail
# Idle/display/disk/AC-system sleep を抑止。蓋閉じは保証しない（電源接続のまま開ける）。
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

MASTER_LOG=runs/overnight-train.log
PIDFILE=runs/overnight.pid
DEADLINE=${DEADLINE:-"2026-08-18 08:00:00"}
# 1ラウンド目安: 学習~2h + 評価~30m
MIN_ROUND_SEC=${MIN_ROUND_SEC:-9000}

echo $$ > "$PIDFILE"
log() { echo "==== $(date '+%Y-%m-%d %H:%M:%S %Z') $* ====" | tee -a "$MASTER_LOG"; }

deadline_ts() {
  python3 - <<PY
from datetime import datetime
from zoneinfo import ZoneInfo
text = "${DEADLINE}"
for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
    try:
        dt = datetime.strptime(text, fmt).replace(tzinfo=ZoneInfo("Asia/Tokyo"))
        print(int(dt.timestamp()))
        break
    except ValueError:
        continue
else:
    raise SystemExit(f"bad DEADLINE: {text!r}")
PY
}

seconds_left() {
  python3 - <<PY
import time
print(max(0, int($1) - int(time.time())))
PY
}

check_c() {
  python3 - "$1" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
data = json.loads(path.read_text())
acc = data.get("acceptance") or {}
ok = bool(acc) and all(bool(v) for v in acc.values())
print("ALL_PASS=" + ("1" if ok else "0"))
for key, value in acc.items():
    print(f"  {key}: {value}")
sys.exit(0 if ok else 1)
PY
}

pick_best_parent() {
  python3 - <<'PY'
import csv
import json
from pathlib import Path

best_score = -1.0
best_frac = -1.0
best_model = ""
best_csv = ""
best_eval = ""

for summary_path in sorted(Path("runs").glob("*-joyo-eval/summary.json")):
    eval_dir = summary_path.parent
    csv_path = eval_dir / "characters.csv"
    if not csv_path.is_file():
        continue
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    if len(rows) < 2000:
        continue
    summary = json.loads(summary_path.read_text())
    evaluation = summary.get("evaluation") or {}
    success = float(evaluation.get("success_rate") or 0.0)
    lw_mean = float((evaluation.get("component_means") or {}).get("line_width") or 0.0)
    # r3/r4-style collapse: do not resume from a broken parent.
    if success < 0.995 or lw_mean < 65.0:
        continue
    both = sum(
        1
        for row in rows
        if float(row["line_width"]) >= 65.0 and float(row["brushwork"]) >= 62.0
    )
    frac = both / len(rows)
    harai = float(
        ((evaluation.get("technique_means") or {}).get("harai") or {}).get("finish") or 0.0
    )
    score = frac + 0.002 * harai
    model = summary.get("model") or ""
    if not model or not Path(model).is_file():
        resolved = (eval_dir / "../final_model.zip").resolve()
        if resolved.is_file():
            model = str(resolved)
    if score > best_score and model and Path(model).is_file():
        best_score = score
        best_frac = frac
        best_model = model
        best_csv = str(csv_path)
        best_eval = str(eval_dir)

if not best_model:
    raise SystemExit("no valid parent model found")

print(best_model)
print(best_csv)
print(f"{best_frac*100:.2f}")
print(best_eval)
PY
}

log "overnight start deadline=$DEADLINE pid=$$"

# 二重起動防止
if pgrep -f "so101-train-professional.*kaisho-yohitsu-c-r" >/dev/null 2>&1; then
  log "training already running; skip duplicate overnight launch"
  exit 0
fi
if [[ -f runs/overnight.lock ]]; then
  LOCK_PID=$(cat runs/overnight.lock)
  if kill -0 "$LOCK_PID" 2>/dev/null; then
    log "overnight already active pid=$LOCK_PID; skip"
    exit 0
  fi
fi
echo $$ > runs/overnight.lock

# 現行 c-loop（r4 まで）の完了を待つ。死んだ PID ファイルは無視。
if [[ -f runs/c-loop.pid ]]; then
  CLOOP_PID=$(cat runs/c-loop.pid)
  if kill -0 "$CLOOP_PID" 2>/dev/null; then
    log "waiting for c-loop pid=$CLOOP_PID to finish"
    while kill -0 "$CLOOP_PID" 2>/dev/null; do
      sleep 60
    done
    log "c-loop finished"
  else
    log "c-loop pid file stale ($CLOOP_PID); continue"
  fi
fi

END_TS=$(deadline_ts)
ROUND=${START_ROUND:-5}

while true; do
  LEFT=$(seconds_left "$END_TS")
  if (( LEFT < MIN_ROUND_SEC )); then
    log "deadline near (${LEFT}s left < ${MIN_ROUND_SEC}s); stop without new round"
    echo "AGENT_NOTIFY_OVERNIGHT_DEADLINE" | tee -a "$MASTER_LOG"
    exit 0
  fi

  PICK=("${(@f)$(pick_best_parent)}")
  # zsh arrays are 1-indexed; set -u would abort on PICK[0]
  MODEL="${PICK[1]}"
  CSV="${PICK[2]}"
  FRAC="${PICK[3]}"
  EVAL_BEST="${PICK[4]}"
  OUT="runs/kaisho-yohitsu-c-r${ROUND}"
  EVAL="runs/kaisho-yohitsu-c-r${ROUND}-joyo-eval"
  LOG="${OUT}-train.log"
  mkdir -p "$OUT"

  log "round $ROUND start parent=$MODEL lw_bw=${FRAC}% csv=$CSV remaining≈${LEFT}s"
  {
    echo "# overnight round $ROUND"
    echo "- started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "- deadline: $DEADLINE"
    echo "- parent: $MODEL"
    echo "- hard_csv: $CSV"
    echo "- best_eval_ref: $EVAL_BEST"
    echo "- parallel: n_envs=7 bc_workers=6 device=mps"
    echo "- budget: PPO 2500000 / BC 180000 × 5"
  } | tee "$OUT/launcher.md" | tee -a "$LOG" | tee -a "$MASTER_LOG"

  so101-train-professional \
    --ablation all \
    --run-purpose "夜通し r${ROUND}: 字単位lw/bwと払い hard-mining（朝${DEADLINE}まで）" \
    --initial-model "$MODEL" \
    --start-stage 9 \
    --hard-csv "$CSV" \
    --timesteps 2500000 --kana-timesteps 2500000 \
    --bc-steps 180000 --kana-bc-steps 180000 --bc-epochs 5 \
    --n-envs 7 --bc-workers 6 \
    --n-steps 4096 --batch-size 1024 \
    --learning-rate 3e-4 \
    --device mps --allow-gate-failure \
    --stage-eval-size 64 --eval-limit 128 \
    --output "$OUT" \
    --seed $((40 + ROUND)) \
    >> "$LOG" 2>&1

  MODEL="$OUT/final_model.zip"
  [[ -f "$MODEL" ]] || { log "round $ROUND missing final_model"; exit 1; }

  LEFT=$(seconds_left "$END_TS")
  if (( LEFT < 1800 )); then
    log "deadline after train (${LEFT}s); skip eval"
    exit 0
  fi

  log "round $ROUND joyo re-eval"
  python3 -u scripts/evaluate_joyo_shards.py \
    --model "$MODEL" \
    --output "$EVAL" \
    --shards 8 \
    --device cpu \
    --seed $((40 + ROUND)) \
    >> "$LOG" 2>&1

  CSV="$EVAL/characters.csv"
  python3 -u scripts/render_ppo_contact_sheet.py \
    "$EVAL" \
    -o docs/results/2026-08-16-ppo-contact-sheet.png \
    --allow-missing \
    >> "$LOG" 2>&1 || true

  log "round $ROUND C check"
  if check_c "$EVAL/summary.json" | tee -a "$MASTER_LOG" "$LOG"; then
    log "C PASSED at overnight round $ROUND"
    echo "AGENT_NOTIFY_C_PASSED round=$ROUND model=$MODEL" | tee -a "$MASTER_LOG"
    exit 0
  fi
  log "C still open after round $ROUND"
  ROUND=$((ROUND + 1))
done
