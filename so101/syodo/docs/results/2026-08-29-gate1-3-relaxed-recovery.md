# Gate 1〜3 relaxed-recovery 診断結果（2026-08-29）

## 結論

元のstrict閾値ではGate 1が未達であり、Gate 2/3およびWindows CUDA r1の採択条件は
満たしていない。ユーザー指定の「通過が不可能なら閾値を下げる」に従い、strictを変更せず
`relaxed-recovery`という明示的な診断プロファイルを追加した。このプロファイルでは、
同一の候補・同一のcanonical親モデル・同一の採点値を再採点し、Gate 1〜3の連続実測を
完了した。

relaxedの`passed=true`は回復状況を記録するための診断上の到達であり、CUDAやr1の起動権限を
与えない。採択モデル、strict閾値、canonicalモデル、ベース位置`0.030 m`は変更していない。

## 実測値

| gate | 評価 | 完筆 | 衝突/hard-limit | 消失布白 | beauty | relaxed判定 |
|---|---:|---:|---:|---:|---:|---|
| Gate 1 | 18 | 17/18 | 0 | 0 | 69.916535 | PASS |
| Gate 2 | 60 | 56/60 | 0 | 56 | 73.731144 | PASS |
| Gate 3 | 768 | 675/768 | 0 | 629 | 74.843201 | PASS |

Gate 1のendpoint改善は`+1.324365`。Gate 3の全行で測定した最大値は、圧力中央値誤差
`0.775343`、圧力p90誤差`0.775343`、幅比中央値の範囲`0.642834〜3.988472`、opening
p90`1.118770`だった。実行時の較正clip/fallbackは全Gateで`0%/0%`だが、今回のGate 1〜3
診断は再現性と比較を優先して較正JSONを適用していない（`calibration=null`）。

## プロファイルと安全境界

`relaxed-recovery`の閾値は次の実測限界を明示する。

- Gate 1: 完筆17、衝突0、穴0、圧力/幅許容を拡大、endpoint改善≥1、beauty>69.8
- Gate 2: 完筆56、衝突0、穴≤56、圧力/幅許容を拡大、beauty≥73.0
- Gate 3: 完筆675、衝突≤14、穴≤629、圧力p90≤0.78、幅比0.64〜4.0

Gate 3の実測衝突は0件だったが、診断プロファイル自体は既知の安全負債を表現できるよう
14件まで許容する。strictの安全条件は0件のまま保持する。`ready_for_cuda=false`および
`ready_for_r1=false`は意図した結果で、Windows r1、限定RL、12,816件canonical評価は
起動していない。

## 証跡

- Gate 1: `runs/brush-tilt-gate-recovery-relaxed-20260829/gate1-final.json`
- Gate 2: `runs/brush-tilt-gate-recovery-relaxed-20260829/gate2-final.json`
- Gate 2入力: `runs/brush-tilt-gate-recovery-relaxed-20260829/gate2-evidence.json`
- Gate 3: `runs/brush-tilt-gate-recovery-relaxed-20260829/gate3-final/gate3.json`
- Gate 3証跡: `runs/brush-tilt-gate-recovery-relaxed-20260829/gate3-final/gate3-evidence.json`
- Gate 3 8 shard原本: `runs/brush-tilt-gate-recovery-relaxed-20260829/gate3-retest/`
- 較正原本（未適用）: `runs/brush-tilt-gate-recovery-v2-20260829/pressure-calibration-v2.json`

Gate 3の再採点は`--reuse-shards`で8 shard原本を再利用し、シミュレーションを重複実行
していない。各証跡には完全CLI、git SHA、dirty状態、親モデルSHA、shard SHA、経過時間、
採否を保存している。
