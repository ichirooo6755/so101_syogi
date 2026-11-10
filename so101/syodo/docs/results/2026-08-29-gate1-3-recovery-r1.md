# Gate 1〜3回復＋Windows r1 実行結果（2026-08-29）

## 結論

提示された計画の実装、圧力probe、18候補のGate 1探索、および最新の
position-priority DLS修正を含む最良候補の再評価を完了した。既存の閾値、採点式、
canonical best、ベース位置 `0.030 m` は変更していない。

Gate 1は固定閾値のまま **FAIL** だったため、計画の停止条件に従い、このrunでは
Gate 2、Gate 3、限定RL、Windows CUDA r1を起動していない。既存のGate 2/3診断と
非採択smoke成果物は履歴として保持し、採択モデルには反映していない。

## 実装済みの計画項目

- 圧力較正をschema v2へ更新。`PressureCurve.offset_m`は正が上昇、負が押し込みで、
  高圧ほど単調非増加になるよう符号反転して重み付きPAVAを適用した。
- exact角度カテゴリ `0/4/8/12/20/30/45` と `layout_class/angle_deg/phase` lookupを
  実装。最近傍角度補間は行わず、未観測カテゴリはoffset 0の明示fallbackとした。
- 7点（`-4.5/-3/-1.5/0/1.5/3/4.5 mm`）のfeedback=0 probeを、一三十目書飛×6配置
  （fit）と鬱誠砕案×6配置（held-out）で収集した。
- 診断JSONへbeauty全成分、width detail、指令角カテゴリ、実角度、probe情報、
  完全CLI・git dirty状態・CPU/GPUデバイス・較正SHA・経過時間・採否を記録した。
- `apply_clearance_caps()`へ実測幅p90を渡し、layout 0/1の接触停滞後にposition-priority
  DLSへ切り替える安全制御を追加した。衝突line searchは `1.0 → 0.5 → 0.25` を維持した。
- 18候補（gap 3 × floor 2 × motion 3）を並列screenし、Gate 1未達候補をGate 2へ
  渡さない厳格な探索、Gate 2限定RL、Gate 3 8-shard、Windows r1 preflightを実装した。

## 圧力probe・較正

| 項目 | 結果 |
|---|---:|
| probe評価 | 420（7 offsets × 10字 × 6配置） |
| fit / held-out | 一三十目書飛 / 鬱誠砕案 |
| accepted / fit / held-out samples | 191,288 / 77,418 / 113,870 |
| 除外samples | 5,397,459 |
| 曲線 | 12（85/110 mm × 6 phases） |
| held-out median absolute error | 0.0007173 m（0.717 mm） |
| runtime clip / fallback（Gate 1再評価） | 0% / 0% |

較正JSONのSHA-256は
`73ecc23f8c7af57d7b1097df368551185b6f484a1322408cca8f33313d244769`。
fitter内部の範囲外率44.93%はprobe fitの検証値であり、Gate判定にはruntimeのclip率を
使用した。成果物は `runs/brush-tilt-gate-recovery-v2-20260829/` に保存している。

## Gate 1探索と最良候補

18候補の全screenでGate 1を通過する候補はなかった。順位上位の
`minimum_gap=1.5 mm / clearance_floor=0.35 / exemplar_motion_strength=1.00` を、
position-priority DLS修正後に同じ条件で再評価した。

| 指標 | upright baseline | 最良候補（tilt） | Gate 1条件 |
|---|---:|---:|---:|
| 評価数 | 18/18 | 18/18 | 18/18 |
| 完筆 | 16/18 | **17/18** | 18/18 |
| 衝突・hard-limit | 0 | **0** | 0 |
| 消失布白 | 0 | **0** | 0 |
| beauty mean | 65.621811 | **70.957650** | >69.8 |
| endpoint triangle mean | 19.927244 | 26.539786 | — |
| endpoint改善 | — | **+6.612542** | ≥+10 |
| runtime clip / fallback | 0% / 0% | **0% / 0%** | ≤5% / ≤5% |

最良候補のゲート内訳は `complete=false`、`pressure_tracking=false`、
`width_tracking=false`、`endpoint_ablation=false`、`beauty=true` で、
`passed=false` / `ready_for_cuda=false` / `ready_for_r1=false` だった。主な残存箇所は
`三/0`の圧力p90 0.536、`一/1`の幅比0.72、複数配置の圧力p90 0.18超、endpoint改善
不足である。最新修正後も三/0は最終target付近で停滞し、完筆条件を満たさなかった。

使用した再評価CLI（uprightは `--upright` を付与し、Gate 1は同じ出力を
`--upright-baseline` に渡した）は次のとおり。

```bash
env PYTHONPATH=src MPLBACKEND=Agg .venv/bin/python -u scripts/diagnose_stroke_merge.py \
  --chars 一三十 --layouts 0,1,2,3,4,5 \
  --minimum-gap 0.0015 --clearance-floor 0.35 --exemplar-motion-strength 1.0 \
  --pressure-calibration runs/brush-tilt-gate-recovery-v2-20260829/pressure-calibration-v2.json \
  --require-pressure-calibration \
  --pressure-calibration-clip-rate-limit 0.05 \
  --pressure-calibration-fallback-rate-limit 0.05 \
  --gate-level 1 \
  --upright-baseline runs/brush-tilt-gate-recovery-v2-20260829/gate1-best-retest-upright.json \
  --output runs/brush-tilt-gate-recovery-v2-20260829/gate1-best-retest.json
```

## 停止判定と次の条件

- Gate 1未達のため、Gate 2の60件、Gate 3の768件、限定RL、Windows r1はこのrunでは
  **未起動**。r1のpreflightはGate 3の768/768完筆・安全・圧力・幅・穴・openingを
  すべて要求するため、現時点でCUDA権限を発行しない。
- `runs/brush-tilt-gate-recovery-v2-20260829/search/search-summary.json` に18候補の
  全結果を保存した。`selected=null`、`rl_candidate=null` である。
- canonical `runs/kaisho-yohitsu-sansetsu/final_model.zip`、既存run、
  `.vscode/extensions.json` は変更していない。

## 検証・再現性

- `PYTHONPATH=src .venv/bin/python -m pytest -ra`: **252 passed in 8.72s**
- `PYTHONPATH=src .venv/bin/python -m compileall -q src scripts tests`: PASS
- `git diff --check`: PASS
- probe/search/fit/retestの主要JSONはApple Silicon Mac（Apple M1 Pro、8 CPU、16 GiB RAM、
  CPU）で実行し、各主要成果物の `run` に開始時刻、完全CLI、commit、dirty状態、環境、
  経過時間、採否を保存した。
- probe、fit、search、Gate 1再評価時のgit SHAは、実行時の作業ツリー（ユーザー管理の
  `.vscode/extensions.json`を含む）がdirtyだったことを明記している。コードの最終変更は
  この報告と同じブランチへコミットしてpushする。
