# 教育漢字汎化学習の結果

## 結果

Apple Silicon MacのCPUだけで、SO-101書道環境の学習と全件評価を完了した。学習済み決定論方策は、学年別漢字配当表の1,026字すべてをKanjiVGの画順どおりに完筆した。

| 学年 | 対象 | 完筆 | 成功率 |
|---:|---:|---:|---:|
| 1 | 80 | 80 | 100% |
| 2 | 160 | 160 | 100% |
| 3 | 200 | 200 | 100% |
| 4 | 202 | 202 | 100% |
| 5 | 193 | 193 | 100% |
| 6 | 191 | 191 | 100% |
| 合計 | 1,026 | 1,026 | 100% |

- 完了基準: 80%以上
- 実測: 100%
- 衝突: 0件
- 全文字の最小進捗: 100%
- 1文字の最大step数: 1,850（上限2,200）
- 平均step数: 1,003.6
- 累積PPO step: 5,433,344
- 評価seed: 各文字について `7 + education-kanji index`
- 観測: 20次元
- 行動: SO-101の6関節残差指令

## 学習構成

基本筆画と実在部首14段階を3,526,656 step学習した後、36、80、240、440、642、835、1,026字の累積プールへ進めた。純粋な行動クローニングでは長い文字で局所誤差が累積したため、DLS関節制御を基準にPPOが小さな残差を学ぶ構成へ変更した。残差係数0.05では、6年生までの固定32字評価が32/32となり、全件評価も一度で通過した。

対象文字と学年はEDRDG KANJIDIC2、筆画・方向・筆順はKanjiVG `r20250816`を使用した。GPU、CUDA、Isaac Simは使用していない。

## 成果物

- 学習済みモデル: [`models/education-kanji-ppo.zip`](../../models/education-kanji-ppo.zip)
- 評価要約: [`models/education-kanji-evaluation.json`](../../models/education-kanji-evaluation.json)
- 報酬推移: [`models/education-kanji-reward-curve.png`](../../models/education-kanji-reward-curve.png)
- モデルSHA-256: `f3a2dde52b81e7ab2e3eea14feca93e5f6e06bf0b4ad091c363535038fc0b736`

この結果はMuJoCo上の軽量SO-101モデルに対するものであり、実機転送の検証結果ではない。実機にはサーボ較正、速度制限、筆圧、遅延、非常停止を追加する必要がある。
