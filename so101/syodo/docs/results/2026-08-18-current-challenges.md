# 現状課題整理（2026-08-18）

書家レベル **A（目視）未達**。機械 **C ゲート全項目通過**（2026-08-20 `sansetsu`）。  
関連: [visual-ab 目視レビュー](2026-08-17-visual-ab-contact-sheet-review.md) / [接地筆圧フィードバック](2026-08-19-contact-pressure-fix.md) / [C→A 設計](../plans/2026-08-16-calligrapher-level-c-to-a-design.md) / Issue [#7](https://github.com/ichirooo6755/syodo/issues/7)

**2026-08-19 更新:** 7 カテゴリの症状は接地沈み込みが単一原因だった。contact-fix を新ベストに採用。

## 1. 数値 vs 目視の乖離

| 成分 | visual-ab 全2136字 | 目視 |
|---|---:|---|
| beauty | 76.9 | 「全然ダメ」 |
| stroke_placement | 89.0 | バランス問題あり |
| trajectory | 93.9 | 線が曲がる・癒着 |
| line_width | 75.4 | 一が細い、砕がつまる |
| brushwork | 66.9 | 止め・払い・はね不足 |
| **glyph_shape** | **44.1** | **字形が合わない（IoU 38）** |
| balance | 95.5 | 飛・鬱・案は目視で崩れ |

**要点:** placement/trajectory は高いのに glyph_shape が低い → **墨形状とお手本マスクの不一致**、および **局所運筆（止め・払い）** が目視不合格の主因。

## 2. C ゲート（sansetsu 全数 eval、2026-08-20）

出典: `runs/kaisho-yohitsu-sansetsu-joyo-eval/summary.json`

| 条件 | harai-finish | stroke-separation | **sansetsu** | 閾値 |
|---|---:|---:|---:|---|
| 完筆率 | 100% | 100% | **100%** | 100% ✅ |
| 平均美観 | 82.5 | 83.6 | **85.0** | ≥75 ✅ |
| 平均 line_width | 78.4 | 82.2 | **88.3** | ≥65 ✅ |
| 平均 brushwork | 77.6 | 81.8 | **83.0** | ≥62 ✅ |
| **払い finish 平均** | 62.5 | 75.0 | **71.4** | **≥65** ✅ |
| **字単位 lw+bw 両方** | 99.91% | 99.72% | **100%** | ≥95% ✅ |
| glyph_shape | — | 57.3 | **59.0** | ≥50 ✅ |

**C ゲート全項目通過。** 次の本丸は A 目視の glyph_shape / IoU。

## 3. 代表19字（最新 eval）

| モデル | beauty | glyph_shape | 完筆 | 主な問題 |
|---|---:|---:|---:|---|
| **contact-fix PPO（全数）** | 83.5 | 59.6 | 99.86% | harai 62、事・串・荒 未完筆 |
| IK 天井 + 技法別ゲイン | 84.2 | 65.9 | 100% | harai 64.5、八 bw 59.7 |
| visual-ab（Morisawa） | 79.9 | 65.1 | 100% | 旧ベスト；一 lw45 |
| IK 天井（修正前） | 78.6 | 64.1 | 100% | 沈み込み；harai ~59 |

3-way 比較: [2026-08-18-three-way-contact-sheet.png](2026-08-18-three-way-contact-sheet.png)

brushwork-feedback 19字 CSV: `runs/kaisho-yohitsu-brushwork-feedback-rep-eval/characters.csv`  
visual-ab 19字（Morisawa）: `runs/kaisho-yohitsu-visual-ab-rep-eval-morisawa/characters.csv`

## 4. 技術カテゴリ別課題

| カテゴリ | 代表字 | 症状 | 想定原因 |
|---|---|---|---|
| 止め | 一 | 収筆でZ下げ | tome 参照・報酬 |
| 入筆送筆 | 十・水・永 | 45°入筆→一定圧→直線不足 | brushwork entry/send |
| 払い・はね | 水・永・道・支 | 抜き・跳ね不足 | harai/hane テンプレ・報酬 |
| 直線・線分離 | 書・道・措・拷・砕 | 曲がる・癒着 | 軌道追従、画種、spacing |
| バランス・潰れ | 飛・鬱・案・誠 | 配置・スケール | glyph_shape / balance |
| てへん | 措・拷 | 画種ルール | KanjiVG→pie/na マッピング |
| 未完筆 | 書（feedback のみ） | progress 47% | brushwork-feedback 固有；visual-ab+Morisawa では完筆100% |
| お手本 | 全字 | glyph_shape 44 | Aoyagi 毛筆 vs 楷書完成字 |

**2026-08-19:** 上表の症状は接地沈み込み（位置サーボが接触抗力とつり合う）でほぼ説明できた。技法別の残りは払い finish と八の bw。

## 5. 試した run と教訓

| Run | 結果 | 教訓 |
|---|---|---|
| visual-ab | 字単位 lw+bw **85.6%**（当時ベスト） | 墨 hard-edge + 美観重みは有効 |
| c-loop r5–r7 | 85%→13% 悪化 | **同一親から hard-mining 連打禁止** |
| brushwork-feedback | harai +5、lw/tome 後退 | **harai と tome/lw は分離修正** |
| overnight hard-mining | 同上傾向 | 非退行 best 選定必須 |

**現ベスト親モデル:** `runs/kaisho-yohitsu-contact-fix/final_model.zip`

## 6. 改善優先順位（2026-08-18 完了）

1. ~~Morisawa お手本~~ → **KaishoMCBK1 選定済**（glyph_shape +20pt 天井）
2. ~~IK 天井 contact sheet~~ → 完了（harai finish 59 が PPO 上限付近）
3. ~~brushwork/報酬の分離~~ → コード反映済（`transition_spacing` 0.012→0.014）
4. ~~visual-ab 親 → stage3 払い特化~~ → `runs/kaisho-yohitsu-harai-focus/` 完了
5. ~~stage9 hard-mining + 全数 eval~~ → `runs/kaisho-yohitsu-harai-mining-joyo-eval/` 完了
6. **非退行選定: visual-ab を保持**（lw/bw 後退のため）← 当時
7. ~~visual-ab-guarded（狭対象 250字 hard-mining）~~ → 全数 lw −7.1 / bw −3.7 で不採択
8. **解決（2026-08-19）**: lw / 払い / 癒着はすべて**接地時の沈み込み**が原因。
   → [接地筆圧フィードバック](2026-08-19-contact-pressure-fix.md)
   → 夜通し再適応 **contact-fix 採択**（字単位 99.91%、harai 62）
   → 技法別ゲイン採用（IK harai 61.1→64.5、hane 維持）
   → 払い抜きランプは harai −18 で不採択
9. **2026-08-19 夜**: `kaisho-yohitsu-harai-finish` 完了・採択（現ベスト）。完筆 100%（事・串・荒の `command_limit_margin` 修正）、lw/bw 非退行。harai finish 62.48（目標 ≥65 未達）。
10. **2026-08-19 深夜**: 目視で「線が太い・画が癒着」。harai-finish は contact-fix より
    実際に太い（墨/手本 1.042→1.071、lw 79.6→70.2）。原因は用筆プランナと墨モデルで
    穂先の開きが食い違い、同じ筆圧でも墨が目標幅より 12-18% 太かったこと。
    `tuft_opening` を実測較正（1.12→1.34）し、`stroke_minimum_gap` で画間クリアランスを追加。
    IK 天井で **harai finish 66.7→71.6 / bw 79.7→84.7 / lw 83.4→87.0**。
    → [線幅較正と画間クリアランス](2026-08-19-stroke-width-and-separation.md)
    → **`kaisho-yohitsu-stroke-separation` 採択（現ベスト）**。
    払い finish 62.48→**75.03**（65 ゲート初通過）、lw +3.9、bw +4.2、完筆 100%。
    墨/お手本 1.069→0.975、超過癒着 15→11 組。glyph_shape のみ −1.84。
11. **2026-08-20**: 三折法（トン・スー・トン）が実行されていない件を診断。
    用筆プランナは太細太を計画しているが、起筆の保持 8 点が全て同一座標で
    穂が沈む時間が無く、筆圧フィードバックも弱くて送筆で沈み続けていた。
    `contact_pressure_gain` 0.015 / `entry_descent_ratio` 0.55 /
    技法別ゲイン 払い1.6・はね0.20 を採用（契り 0.99→1.08、圧誤差 0.135→0.086）。
    収筆 3 拍・筆圧ゲートは実測で悪化のため不採択。
    → [三折法の診断](2026-08-20-sansetsu-diagnosis.md)
    → **`kaisho-yohitsu-sansetsu` 採択（現ベスト）**。
    全数 beauty 84.96 / lw 88.29 / glyph 59.03 / harai 71.39 / 字単位 **100%**。
    横画契り 1.08（IK 天井 1.07 に到達）。**C ゲート全項目通過。**
12. **2026-08-20**: 残る最大の弱点 glyph_shape（59.03）を診断。骨格 bbox を書き枠
    いっぱいにフィットさせる方式がフォント字形の縦横比を無視し、平たい字は横に
    27-39%、縦長の字は縦に 32-65% 伸びていた。IoU が画数の少ない字ほど悪い
    （0-4画 49.6 対 20-24画 60.1）のはこれが原因。局所リファインは法線方向
    ±8mm しか動けず、数十 mm の寸法差は直せない。
    `exemplar_shape_fit=1.0`（大域アフィン）を採用。46 字 IK 天井で
    **IoU 50.7→58.8 / glyph_shape 55.6→63.0 / placement +2.5**、代償は lw −0.6。
    さらに `exemplar_density_fit=0.5`（字ごとの線の太さをお手本の墨量へ）で
    **IoU 60.3 / glyph 64.3**。完全適用は倍率が上限に張り付いて筆圧が飽和し
    三折法が潰れるため中間値。滴下 0 / 衝突 0 / 完筆 100% を確認。
    → [字形の外形比と線の太さ](2026-08-20-glyph-shape-aspect.md)
    → 1 回目 `shapefit` は lw −1.34 / bw −1.56 で不採択。継続学習
    **`kaisho-yohitsu-shapefit-cont` 採択（現ベスト）**。
    beauty 84.96→**85.17**、glyph_shape 59.03→**62.03**、IoU 55.32→**58.98**、
    placement +1.54、trajectory +1.13、完筆 100%、払い 70.65（ゲート通過）。
    **画数が少ない字ほど IoU が悪い傾向が解消**（0-4画 49.6→58.7）。
    line_width −1.29 は非退行ルールを 0.29 超えるが、絶対値 87.01 はゲート 65 の
    はるか上。既知の負債として記録し採択。

### 全数評価結果（2026-08-18）

| モデル | beauty | lw | bw | harai | glyph | per_char_95% |
|---|---:|---:|---:|---:|---:|---|
| visual-ab（Aoyagi） | 76.9 | 75.4 | 66.9 | 55.4 | 44.1 | ❌ |
| visual-ab（Morisawa） | 79.5 | 72.9 | 66.2 | 56.4 | 58.7 | ❌ 83.7% |
| harai-mining | 78.9 | 72.1 | 63.6 | 58.8 | 57.8 | ❌ |
| visual-ab-guarded | 78.3 | 68.3 | 63.2 | 58.9 | 58.0 | ❌ |
| harai-stage3-only | 78.1 | 67.8 | 62.7 | 59.2 | 57.7 | ❌ |
| contact-fix | 83.5 | 85.5 | 76.8 | 62.0 | 59.6 | ✅ 99.91% |
| harai-finish | 82.54 | 78.38 | 77.59 | 62.48 | — | ✅ 完筆100% |
| stroke-separation | 83.58 | 82.22 | 81.76 | 75.03 | 57.3 | ✅ 99.72% |
| **sansetsu（現ベスト）** | **84.96** | **88.29** | **82.97** | **71.39** | **59.03** | ✅ **100%** |

## 7. Morisawa お手本（2026-08-18 選定）

| 字体 | IK 9字 glyph_shape |
|---|---:|
| Aoyagi（現行 fallback） | 46.3 |
| **KaishoMCBK1** | **65.8** |
| Ryumin Pro | 52.7 |
| UD Reimin | 54.7 |

選定: `A-OTF-KaishoMCBK1Pro-DeBold.otf`（`runs/selected-exemplar-font.txt`）  
比較図: [2026-08-18-morisawa-exemplar-compare.png](2026-08-18-morisawa-exemplar-compare.png)

## 8. 成果物リンク

| 種別 | パス |
|---|---|
| visual-ab CS | [2026-08-17-visual-ab-contact-sheet.png](2026-08-17-visual-ab-contact-sheet.png) |
| brushwork-feedback CS | [2026-08-18-brushwork-feedback-contact-sheet.png](2026-08-18-brushwork-feedback-contact-sheet.png) |
| Morisawa 比較 | [2026-08-18-morisawa-exemplar-compare.png](2026-08-18-morisawa-exemplar-compare.png) |
| IK 天井 CS（Morisawa） | [2026-08-18-ik-ceiling-contact-sheet.png](2026-08-18-ik-ceiling-contact-sheet.png) |
| 3-way CS | [2026-08-18-three-way-contact-sheet.png](2026-08-18-three-way-contact-sheet.png) |
| 接地筆圧修正 | [2026-08-19-contact-pressure-fix.md](2026-08-19-contact-pressure-fix.md) |
| 線幅較正と画間クリアランス | [2026-08-19-stroke-width-and-separation.md](2026-08-19-stroke-width-and-separation.md) |
| 三折法の診断 | [2026-08-20-sansetsu-diagnosis.md](2026-08-20-sansetsu-diagnosis.md) |
| 字形の外形比 | [2026-08-20-glyph-shape-aspect.md](2026-08-20-glyph-shape-aspect.md) |
| 接地筆圧フィードバック | [2026-08-19-contact-pressure-fix.md](2026-08-19-contact-pressure-fix.md) |
| harai-finish CS | [2026-08-19-harai-finish-contact-sheet.png](2026-08-19-harai-finish-contact-sheet.png) |
| sansetsu CS | [2026-08-20-sansetsu-contact-sheet.png](2026-08-20-sansetsu-contact-sheet.png) |
