#!/bin/zsh
# 墨の跡の形と、実機に合わせた紙での再適応。
#
# 前提となる修正（すべて commit 済み）:
#   1. 墨の跡を穂の姿勢で決まる涙滴型に（ink.py）
#      従来は「楕円を進行方向に並べる」だけで端が必ず丸くなり、起筆の三角が
#      原理的に作れなかった。roll も technique も deposit へ渡っていたのに
#      使われず捨てられていた。穂の軸を紙面に投影した向きを長軸にし、傾きに
#      応じて伸ばして穂先側を尖らせる。
#   2. 紙を実機に合わせた（MJCF）
#      厚さ 5mm の固定ブロック -> 下敷き＋厚さ 1mm の半紙。上端をヒンジで留め
#      下側は自由、上部に文鎮。筆に引かれて下端が最大 0.57mm 浮く。
#   3. 紙面の接触剛性 solref 0.02 -> 0.05（前コミット）
#
#   効果（83 字 層化標本・IK 天井）:
#     beauty 85.57->86.50 / line_width 88.05->90.01 / brushwork 82.68->86.06
#     払い taper 約21->27.62 / 滴下 0 / 衝突 0
#
#   非退行の基準は shapefit-cont の再評価（幅指標のバグ修正後に取り直したもの）。
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

RUN=${RUN:-kaisho-yohitsu-brushmark}
OUT=runs/${RUN}
EVALDIR=runs/${RUN}-joyo-eval
LOG=runs/${RUN}-train.log
MASTER=runs/${RUN}-overnight.log
PIDFILE=runs/${RUN}.pid
PARENT=${PARENT:-runs/kaisho-yohitsu-shapefit-cont/final_model.zip}
BASELINE=${BASELINE:-runs/kaisho-yohitsu-shapefit-cont-rebased-eval}
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
  echo "- change 1: 墨の跡を穂の姿勢で決まる涙滴型に"
  echo "- change 2: 紙を実機に（下敷き＋半紙、上端ヒンジ、文鎮）"
  echo "- stages: 5(radicals) .. 8(joyo), hard-mining なし"
  echo "- timesteps: $TIMESTEPS / stage"
  echo "- expected: 払い taper と brushwork の改善。完筆・滴下・衝突は非退行"
} | tee "$OUT/launcher.md" | tee -a "$MASTER"

log "training start (remaining $(seconds_left)s)"
so101-train-professional \
  --ablation all \
  --run-purpose "墨の跡の形と実機に合わせた紙での再適応（stage5-8）" \
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
  --seed 131 \
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
  --seed 131 \
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
