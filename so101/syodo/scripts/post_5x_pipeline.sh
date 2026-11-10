#!/usr/bin/env zsh
# 5x完了後の後続パイプライン。並列ベンチ → 全数評価 → hard-mining → contact sheet。
set -euo pipefail
if [[ -z "${SYODO_CAFFEINATE:-}" ]] && command -v caffeinate >/dev/null; then
  export SYODO_CAFFEINATE=1
  exec caffeinate -dims -- "$0" "$@"
fi
cd /Users/sugawaraichirou/Documents/syodo
source .venv/bin/activate
export PYTHONPATH=src PYTHONUNBUFFERED=1

MODEL=${1:-runs/kaisho-yohitsu-5x/final_model.zip}
N_ENVS=${N_ENVS:-6}
BC_WORKERS=${BC_WORKERS:-$N_ENVS}
DEVICE=${DEVICE:-mps}
SHARDS=${SHARDS:-8}
SEED=${SEED:-23}

if [[ ! -f "$MODEL" ]]; then
  echo "model missing: $MODEL" >&2
  exit 1
fi

echo "[1/5] parallel benchmark"
python scripts/benchmark_professional_parallelism.py \
  --model "$MODEL" \
  --output runs/parallel-benchmark \
  --envs 5,6,7 \
  --devices cpu,mps \
  --seeds 31,37 \
  --timesteps 8192 \
  --start-stage 8

if [[ -f runs/parallel-benchmark/benchmark.json ]]; then
  python - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("runs/parallel-benchmark/benchmark.json").read_text())
rec = payload.get("recommendation")
print("recommendation:", rec)
if rec:
    Path("runs/parallel-benchmark/recommended.env").write_text(
        f"N_ENVS={rec['n_envs']}\nDEVICE={rec['device']}\n"
    )
PY
  if [[ -f runs/parallel-benchmark/recommended.env ]]; then
    source runs/parallel-benchmark/recommended.env
  fi
fi

EVAL_OUT=runs/kaisho-yohitsu-5x-joyo-eval
echo "[2/5] joyo shard evaluation -> $EVAL_OUT"
python scripts/evaluate_joyo_shards.py \
  --model "$MODEL" \
  --output "$EVAL_OUT" \
  --shards "$SHARDS" \
  --device cpu \
  --seed "$SEED"

HARD_OUT=runs/kaisho-yohitsu-5x-hard
python - <<'PY'
import json
from pathlib import Path
summary = json.loads(Path("runs/kaisho-yohitsu-5x-joyo-eval/summary.json").read_text())
acc = summary.get("acceptance", {})
all_pass = bool(acc) and all(bool(v) for v in acc.values())
Path("runs/kaisho-yohitsu-5x-joyo-eval/acceptance.env").write_text(
    "ALL_PASS=" + ("1" if all_pass else "0") + "\n"
)
print(json.dumps(acc, ensure_ascii=False, indent=2))
print("ALL_PASS", all_pass)
PY
source runs/kaisho-yohitsu-5x-joyo-eval/acceptance.env

if [[ "$ALL_PASS" == "1" ]]; then
  echo "[3/5] calligrapher machine gates (C) already pass; skip hard-mining"
  HARD_MODEL=$MODEL
else
  echo "[3/5] hard-mining required (C gates open) -> $HARD_OUT"
  so101-train-professional \
    --ablation all \
    --run-purpose "書家レベル機械合格(C)未達字を hard-mining で重点再学習する" \
    --initial-model "$MODEL" \
    --start-stage 9 \
    --hard-csv "$EVAL_OUT/characters.csv" \
    --timesteps 450000 --kana-timesteps 450000 \
    --bc-steps 40000 --kana-bc-steps 40000 --bc-epochs 5 \
    --n-envs "$N_ENVS" --bc-workers "$BC_WORKERS" \
    --n-steps 2048 --batch-size 768 \
    --device "$DEVICE" --allow-gate-failure \
    --stage-eval-size 48 --eval-limit 96 \
    --output "$HARD_OUT" \
    --seed "$SEED" \
    2>&1 | tee "${HARD_OUT}-train.log"
  HARD_MODEL=$HARD_OUT/final_model.zip
  if [[ ! -f "$HARD_MODEL" ]]; then
    HARD_MODEL=$MODEL
  fi
fi

EVAL2=runs/kaisho-yohitsu-5x-joyo-eval-r2
echo "[4/5] re-evaluate after hard-mining -> $EVAL2"
python scripts/evaluate_joyo_shards.py \
  --model "$HARD_MODEL" \
  --output "$EVAL2" \
  --shards "$SHARDS" \
  --device cpu \
  --seed "$SEED"

echo "[5/5] select best + contact sheet"
python scripts/select_best_model.py \
  "$EVAL_OUT/summary.json" \
  "$EVAL2/summary.json" \
  --baseline runs/kaisho-yohitsu-5h/final/summary.json \
  --output runs/model-selection-5x.json

BEST=$(python - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("runs/model-selection-5x.json").read_text())
print(payload["selected"]["source"])
PY
)
# Prefer the evaluation directory that owns the selected summary.
BEST_DIR=$(dirname "$BEST")
if [[ -f "$EVAL2/characters.csv" ]]; then
  SHEET_DIR=$EVAL2
elif [[ -f "$EVAL_OUT/characters.csv" ]]; then
  SHEET_DIR=$EVAL_OUT
else
  SHEET_DIR=$BEST_DIR
fi

python scripts/render_ppo_contact_sheet.py \
  "$SHEET_DIR" \
  -o docs/results/2026-08-16-ppo-contact-sheet.png

echo "done"
echo "best summary: $BEST"
echo "contact sheet: docs/results/2026-08-16-ppo-contact-sheet.png"
