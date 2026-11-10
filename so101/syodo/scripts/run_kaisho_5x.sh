#!/bin/zsh
# 楷書用筆則 5倍継続学習。目的・期待値・出力先を自己記録する起動ラッパ。
# 並列度は docs/parallelism-notes.md / runs/parallel-benchmark の推奨に合わせる:
#   --n-envs 6 --bc-workers 6 --device mps（監視上限7、学習で8以上は避ける）
set -euo pipefail
if [[ -z "${SYODO_CAFFEINATE:-}" ]] && command -v caffeinate >/dev/null; then
  export SYODO_CAFFEINATE=1
  exec caffeinate -dims -- "$0" "$@"
fi
cd /Users/sugawaraichirou/Documents/syodo
source .venv/bin/activate
export PYTHONPATH=src
export PYTHONUNBUFFERED=1

PURPOSE='kaisho-yohitsu-5h の線幅改善を維持し、未達の運筆・払い収筆を5倍規模で改善する'
OUTPUT=runs/kaisho-yohitsu-5x
LOG=${OUTPUT}-train.log
mkdir -p "$OUTPUT"

{
  echo "# kaisho-yohitsu-5x launcher"
  echo "- started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "- purpose: $PURPOSE"
  echo "- parent: runs/kaisho-yohitsu-5h/final_model.zip"
  echo "- output: $OUTPUT"
  echo "- log: $LOG"
  echo "- expected: 96字で完筆100%、滴下0、衝突0、line_width>=65、brushwork>=62、harai finish>=65"
  echo "- next: 完了後に scripts/evaluate_joyo_shards.py で全2,136字評価→hard-mining"
} > "$OUTPUT/launcher.md"

exec > >(tee -a "$LOG") 2>&1
exec so101-train-professional \
  --ablation all \
  --run-purpose "$PURPOSE" \
  --initial-model runs/kaisho-yohitsu-5h/final_model.zip \
  --start-stage 5 \
  --timesteps 2250000 --kana-timesteps 4500000 \
  --bc-steps 200000 --kana-bc-steps 400000 --bc-epochs 5 \
  --n-envs 6 --bc-workers 6 --n-steps 2048 --batch-size 768 \
  --device mps --allow-gate-failure \
  --stage-eval-size 48 --eval-limit 96 \
  --output "$OUTPUT" \
  --seed 23
