# visual-ab Aoyagi vs Morisawa 全数比較（2026-08-18）

前回の mining / guarded 不採択は、**お手本が違う物差し同士**を比べていた。
visual-ab を KaishoMCBK1 で全数再評価すると、glyph 改善の大半は学習ではなく教師変更だった。

| モデル | お手本 | beauty | lw | bw | harai | glyph |
|---|---|---:|---:|---:|---:|---:|
| **visual-ab** | Aoyagi | 76.9 | 75.4 | 66.9 | 55.4 | 44.1 |
| **visual-ab（現ベスト）** | **Morisawa MCBK1** | **79.5** | **72.9** | **66.2** | 56.4 | **58.7** |
| harai-mining | Morisawa | 78.9 | 72.1 | 63.6 | **58.8** | 57.8 |
| visual-ab-guarded | Morisawa | 78.3 | 68.3 | 63.2 | 58.9 | 58.0 |

同一教師での非退行選定: **visual-ab + Morisawa を保持**。
mining は brushwork 退行、guarded は lw/bw と最低美観も退行。

次: stage 3（永水小木火人子心手）だけを短く学習。stages 4–8 は回さない。
