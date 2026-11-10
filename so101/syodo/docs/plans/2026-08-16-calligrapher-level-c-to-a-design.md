# 書家レベル担保（C → A）

Date: 2026-08-16  
Issue: [#4](https://github.com/ichirooo6755/syodo/issues/4)（親 [#2](https://github.com/ichirooo6755/syodo/issues/2)）

## Goal

常用漢字の学習結果を「数値ゲート通過」だけで書家レベルと書かない。  
**機械の厳しい合格（C）のあと、ユーザー目視（A）で初めて書家レベルと宣言する。**

## Decision (approved)

- 判定経路: **C → A**（書家レビュー B は後段オプション）
- 実装アプローチ: ゲート強化 →（必要なら）墨キレ改善 → hard-mining 必須 → contact sheet 目視

## Two-stage acceptance

### C — 機械合格（自動）

全 2,136 字評価の `acceptance` がすべて true のときのみ「機械合格」。

必須:

| 条件 | 閾値 |
| --- | --- |
| 完筆率 | 1.0 |
| 滴下 / 衝突 | 0 |
| 平均美観 | ≥ 75 |
| 最低美観 | ≥ 60 |
| 平均 `line_width` | ≥ 65 |
| 平均 `brushwork` | ≥ 62 |
| 払い収筆平均（`harai.finish` がある場合） | ≥ 65 |
| 字単位で lw≥65 かつ bw≥62 を満たす割合 | ≥ 95% |

どれか一つでも false なら **hard-mining をスキップしてはならない**  
（旧 acceptance は美観＋安全だけで通してしまい、運筆未達 1544 字でも mining を飛ばした）。

### A — 書家レベル宣言（ユーザー）

機械合格後にのみ実施。次を目視し、ユーザーが合格と宣言したときだけ README / Issue に「書家レベル」と記す。

代表字: `一・十・永・水・小・語・教・鬱`  
＋ 学年別ランダム各数文字の PPO contact sheet（IK 比較表と混同しない）。

機械だけの状態では「書家レベル合格」と書かない。

## Pipeline changes

1. `scripts/evaluate_joyo_shards.py` の `acceptance` を上記に拡張
2. `scripts/post_5x_pipeline.sh` / 続行スクリプトは `all(acceptance.values())` のみで判定し、未達なら必ず `--hard-csv` / `--start-stage 9`
3. 既存 `runs/kaisho-yohitsu-5x-joyo-eval/characters.csv` から即 hard-mining 再開（冗長な同一モデル再評価は止める）
4. 再評価 → best 選定 → `docs/results/2026-08-16-ppo-contact-sheet.png`
5. ユーザー目視待ちコメントを Issue #4 / #2 に残す

## Follow-ups (after first C loop)

- 墨スタンプ縁のキレ改善（ぼやけ低減）の短い実験 → 再学習
- glyph_shape と brushwork の報酬競合の再調整
- 任意: 書家レビュー（B）を A の上位に追加

## Non-goals (this slice)

- 実機 SO-101 での書家品質保証（sim2real 較正は別トラック）
- フォント配布やお手本ライセンス変更
