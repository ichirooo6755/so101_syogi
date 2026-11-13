# 3ゲームのルールライブラリ

統合版の対局管理はTypeScriptから各ゲームの既存ライブラリを呼び出し、人とAIの着手を同じルールで判定する。

| ゲーム | 配布物 | ライセンス | 使用範囲 |
| --- | --- | --- | --- |
| 囲碁 | [`@sabaki/go-board` 1.4.3](vendor/sabaki-go-board-1.4.3.tgz) | MIT | 盤面、捕獲、自殺手、単純コウの判定。スーパーコウや終局・得点は採用ルールに従って対局管理で扱う。 |
| 将棋 | [`tsshogi` 2.3.4](vendor/tsshogi-2.3.4.tgz) | MIT | 着手・成り・持ち駒の検証、棋譜履歴からの千日手・連続王手の判定。 |
| チェス | [`chess.js` 1.4.0](vendor/chess.js-1.4.0.tgz) | BSD-2-Clause | 合法手の生成・検証、特殊手と詰みの判定。引き分けの確定条件は採用ルールに従って対局管理で扱う。 |

`vendor/` はnpmレジストリから取得した配布物を収録している。各アーカイブ内に上流のライセンスがあり、`package-lock.json` に整合性ハッシュを記録する。

```sh
cd rules
npm ci --offline --ignore-scripts
```

Windows の PowerShell で `npm` のスクリプト実行が制限されている場合は、`rules/` で `npm.cmd ci --offline --ignore-scripts` を実行する。

各ライブラリの上流資料は、[SabakiHQ/go-board](https://github.com/SabakiHQ/go-board)、[sunfish-shogi/tsshogi](https://github.com/sunfish-shogi/tsshogi)、[jhlywa/chess.js](https://github.com/jhlywa/chess.js) を参照。
