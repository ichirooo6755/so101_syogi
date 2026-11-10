# 筆傾斜アタッチメント過去最高回復 結果（2026-08-27）

## 結論

Task 1〜6の実装と自動検証、およびGate 1〜3の診断実行は完了した。Gate 1を
通過しなかったため、Gate 2/3の結果は診断記録として保存し、Windows CUDA再学習と
12,816ケース最終評価は起動していない。既存bestおよび既存runは変更していない。

## 実装

- schema v1の純粋JSON圧力逆モデル、重み付きPAVA、厳密カテゴリlookupを実装した。
  カテゴリキーは`layout_class/angle_deg/phase`。未観測カテゴリはoffset 0の明示fallbackで、
  角度の最近傍補間は行わない。
- `CalligraphyEnv`へfeedforwardと残差積分を統合し、clip/fallback、接触喪失リーク、
  再接地soft-start、較正サンプルを記録するようにした。
- fitterは失敗・衝突・過渡・失接触・過大XY誤差・非有限値を除外し、設定fingerprint、
  元診断SHA-256、git SHA、leave-one-character/layout誤差をprovenanceへ保存する。
- Gate 1（18件）、Gate 2（60件）、Gate 3（768件）を別schemaで厳格化し、Gate 1からは
  `ready_for_cuda=true`を生成できないようにした。
- 6配置評価へunique文字数、layout別mean/p10、較正provenance、clip/fallback集計を追加した。
  128字は768行、全常用漢字は12,816行でなければmergeを失敗させる。
- Windows launcherはGate 2/schema/60件/較正SHA、親ZIP、CUDA、空き容量をpreflightし、
  r1前に親モデル128字×6配置・完筆100%を要求する。最終採択は12,816行、2,136字、
  6配置、全Cゲート、滴下・衝突0、meanとp10の過去最高閾値をすべて必須とした。

## 検証

- `PYTHONPATH=src .venv/bin/python -m pytest -q`: **208/208 PASS**。
- `.vscode/extensions.json`はユーザー変更のまま触れていない。
- 実測出力: `runs/brush-tilt-best-recovery-20260827-task-completion/`。

## Gate 1実測

固定45°（layout 0のみ30°）、`tip_pressure_scale=0.45`、一・三・十×6配置で測定した。

| 候補 | 完筆 | beauty mean | clip率 | fallback率 | 端点改善 | 判定 |
|---|---:|---:|---:|---:|---:|---|
| 未較正 | 18/18 | 69.7739 | 0% | 0% | +10.4876 | FAIL |
| 較正v4（接触回復あり） | 18/18 | 65.3040 | 13.1360% | 34.5220% | -1.9828 | FAIL |
| 較正v5（残差倍率4） | 17/18 | 68.3915 | 14.2604% | 28.9962% | -3.7204 | FAIL |

未較正候補は完筆、衝突・hard-limit 0、消失布白0、端点改善を通過したが、全ケースの
圧力追従、幅比0.90〜1.10、beauty > 69.8を満たさなかった。beautyは丸め前で
69.77388023324927のため厳密に不合格である。

較正元10,130サンプルのうち定常接触1,885件から8曲線を生成した。fitter内検証の
clip/fallbackは0%だったが、実行時には未観測の110mm/45°/entry等が明示fallbackとなり、
過渡圧がノット範囲外となった。閾値を下げず、Gate 1失敗時停止の規則を適用した。

## Gate 2実測（60件）

Gate 1と同じ未較正設定（固定45°、layout 0のみ30°、`tip_pressure_scale=0.45`）で
一・三・十・目・書・飛・龍・鬱・誠・砕を6配置ずつ測定した。

| 指標 | 実測 | 厳格判定 |
|---|---:|---|
| 評価数 | 60/60 | ✅ |
| 完筆 | 60/60 | ✅ |
| 衝突・hard-limit | 0 | ✅ |
| 消失布白 | 41 | ❌（≤14） |
| beauty平均 | 73.5123 | ❌（≥85） |
| 圧力・幅追従 | 未達 | ❌ |
| `ready_for_cuda` | false | — |

成果物: `runs/brush-tilt-best-recovery-20260827-task-completion/gate2-diagnostic-uncalibrated.json`

## Gate 3実測（128字×6配置=768件）

Gate 2と同じ設定で、代表128字を8シャード（各16字×6配置）に分割して並列測定し、
1つのJSONへ統合した。角度の最近傍補間や閾値緩和は行っていない。

| 指標 | 実測 | 厳格判定 |
|---|---:|---|
| 評価数 | 768/768 | ✅ |
| 完筆 | 754/768 | ❌（100%） |
| 衝突・hard-limit | 衝突14、hard-limit 0 | ❌ |
| 消失布白 | 473 | ❌（≤14） |
| beauty平均 | 74.5895 | 診断値 |
| 圧力・幅追従 | 未達 | ❌ |
| `ready_for_cuda` | false | — |

成果物: `runs/brush-tilt-best-recovery-20260827-task-completion/gate3-diagnostic-uncalibrated.json`
（入力シャード8件も同じディレクトリに保存）。Gate 3は評価数条件を満たすが、
Gate 1/2の前提と物理品質を満たさないためCUDA権限は発行しない。

## Windows CUDA

2026-08-27の再確認でも`DESKTOP-NT5T7N1`はTailscale上でoffline
（last seen 2026-08-26 17:10 JST）。ただしオンライン状態に関係なく、Gate 1未通過のため
CUDA launcherは起動対象外である。canonical modelは置換していない。
