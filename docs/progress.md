# 進捗の一覧（2026-11-10 時点）

`~/Documents/ChatGPT/` にあった SO-101・将棋・囲碁まわりの進捗を、本リポジトリに入れたあとの
**現状の正本**です。詳細は各 README を優先し、ここは全体の地図です。

| 領域 | 状態の一文 | 詳細の正本 |
| --- | --- | --- |
| 将棋 | 開発途中。Mac 上の対局ループとシミュレーションはあるが、実機対局は未成立 | [`shogi/README.md`](../shogi/README.md)、[`shogi/docs/shogi-implementation-plan.md`](../shogi/docs/shogi-implementation-plan.md) |
| 囲碁 | 未着手（設計メモのみ） | [`go/README.md`](../go/README.md) |
| SO-101 台座・CAD | 手首カメラ＋HX711 台座は V8（ねじ固定）まで試作。筆保持は V8 本体4点。実印刷・強度・通電は未検証 | [`so101/README.md`](../so101/README.md)、[`so101/output/README.md`](../so101/output/README.md) |
| SO-101 書道 | 実機で 1–4 文字を書く段階。正本は別リポジトリ [syodo](https://github.com/ichirooo6755/syodo)。本リポジトリの `so101/syodo/` は同内容の取り込み（学習 run・データセットは大容量のため未収録） | [`so101/syodo/README.md`](../so101/syodo/README.md)、[`so101/syodo/docs/hardware-open.md`](../so101/syodo/docs/hardware-open.md)、[`so101/syodo/docs/training-runs.md`](../so101/syodo/docs/training-runs.md) |
| 薄膜シミュ | 履歴として取り込み。コードと代表出力のみ（大きな状態ファイルは未収録） | [`so101/soap_film/README.md`](../so101/soap_film/README.md) |

## 将棋の進捗（要約）

- **できること**: GUI、「対局を始める」、ArUco 四隅で盤正面化の試作、画像差分＋合法手で人の手候補、Fairy-Stockfish の応手、MuJoCo での移動・取り・打ち・成り計画と到達評価。
- **できないこと／未検証**: 実機へのモーター送信（`shogi/app/robot_arm.py` が拒否）、実盤でのマーカー検出精度、実機での把持・取り・打ち・成り、駒台の本実装、上腕延長の最終寸法決定と印刷・組付け。
- **延長部品**: +50 / +58 / +75 / +100 / +125 mm の比較試作（STEP/STL・試算 JSON）が `shogi/output/upper_arm_extension/` にある。最終寸法は未決定。
- **手首カメラ**: XIAO ESP32S3 Sense 用ファームとマウント試作あり。実機撮影は未試験。
- **学習**: overnight 最良は未見 10/12（round 375）。GUI は IK が正本で、この学習結果は使わない。`simulation/runs/` の実ファイルは大容量のため未収録（[large-artifacts.md](large-artifacts.md)）。

## SO-101 本体まわりの進捗（要約）

- **カメラ＋HX711 台座**: V1（手首サドル）→ V8（ねじ固定スタック、2026-10-28）まで履歴あり。最新は `so101/output/print_camera_hx711_v8/`。実印刷・強度・通電は未検証。
- **筆保持本体**: V8 の本体・手首・キャリア・15 mm 筆カートリッジ 4 点を `so101/output/print_v8/` にまとめ。実物の印刷・荷重試験は未実施。部品表は `so101/組立部品表.md`。
- **生成元**: `so101/scripts/`（Fusion 用の build/check/export 群）。成果物だけ見て直さず、スクリプトから再生成する想定。
- **書道（syodo）**: `desk.ready=true` の記録あり。Follower／Leader で実機書字。学習採択モデルは `kaisho-yohitsu-sansetsu`（機械 C ゲート通過）。実機 12/8/4 cm 筆構成の採択評価は未実施。詳細は `so101/syodo/README.md` の「いま」節。

## 囲碁の進捗（要約）

- ローカルにも実装ファイルは無かった。`go/README.md` に将棋からの流用見込みと、交点座標・石の把持・碁笥・ルール選定の洗い出しだけ置いた。
- 盤座標の設計置き場は [`board-geometry.md`](board-geometry.md)。

## 対局エンジンとルールライブラリの収録状況（2026-11-13 確認）

今回の対象ブランチ3本に、実ファイルの収録に関する未コミットの変更はありません。囲碁と将棋・チェスはローカルでコミット済みで、GitHub への push が残っています。

| 対象 | ブランチ | ローカルでコミット済みの内容 | GitHub の状態 |
| --- | --- | --- | --- |
| 囲碁・KataGo | [`codex/go-integration`](https://github.com/ichirooo6755/so101_syogi/tree/codex/go-integration) | `5cc3e4c`、`b468399`、`56cf79b`、`b7d06d6`。 `go/vendor/KataGo/` の Windows x64 用 v1.17.1 と DLL、Apple Silicon・Intel Mac 用 v1.17.2 と共有ライブラリ、学習済みモデル、対応ソース、ライセンス、出典。設定と起動方法を更新し、取得スクリプトを削除。 | `deaf1b2` まで。左記4件の push 待ち。 |
| 将棋・やねうら王 | [`codex/chess-stockfish-yaneuraou`](https://github.com/ichirooo6755/so101_syogi/tree/codex/chess-stockfish-yaneuraou) | `6d713cf`。 `shogi/vendor/YaneuraOu/` の Windows x64・Apple Silicon・Intel Mac 用 V9.00、Háo 評価関数 `engine/eval/nn.bin`、対応ソースとライセンス、起動パスの更新。 | `edc9f68` まで。左記1件の push 待ち。 |
| チェス・Stockfish | [`codex/chess-stockfish-yaneuraou`](https://github.com/ichirooo6755/so101_syogi/tree/codex/chess-stockfish-yaneuraou) | 同じ `6d713cf`。 `chess/vendor/Stockfish/` の Stockfish 19 Windows x64 実行ファイル、macOS ユニバーサル版のアーカイブ、NNUE、対応ソースとライセンス、起動方法の更新と取得スクリプトの削除。 | 将棋と同じコミットで反映予定。 |
| 3ゲームのルールライブラリ | [`codex/game-rule-libraries`](https://github.com/ichirooo6755/so101_syogi/tree/codex/game-rule-libraries/rules/vendor) | `rules/vendor/` の `@sabaki/go-board` 1.4.3、`tsshogi` 2.3.4、`chess.js` 1.4.0 の配布ファイル。 | `bb82c00` で収録を確認済み。 |

- [ ] `codex/go-integration` と `codex/chess-stockfish-yaneuraou` のコミットを GitHub に反映する。通常の push は大容量転送中にタイムアウトまたは切断し、Git LFS はリポジトリの予算超過で拒否された。
- [ ] 反映後に両ブランチを新規にチェックアウトし、エンジンと評価ファイルが収録されていること、取得スクリプトを使わず起動できることを確認する。Windows では KataGo の応手・解析と Stockfish の応手を確認済み。やねうら王はこのPCのアプリケーション制御で起動が止まり、macOS での各エンジンの動作確認も残っている。

## 大容量で実ファイルを入れていない進捗データ

進捗が無いのではなく、GitHub 上限のため実ファイルを入れず、生成元と要約で辿れるようにしたものです。一覧は [large-artifacts.md](large-artifacts.md)。

主なもの: 書道 `syodo/runs/`（約 3.4 GB）、将棋 `simulation/runs/`、FEM の `.vtu/.msh`、薄膜の `state_*.npz`、`.f3d` 中間バックアップ、データセット、仮想環境、`vendor/`。

## 課題（Issue）

- [#1 実機対局の成立](https://github.com/ichirooo6755/so101_syogi/issues/1)
- [#2 上腕延長の寸法決定](https://github.com/ichirooo6755/so101_syogi/issues/2)
- [#3 盤面位置関係の実測](https://github.com/ichirooo6755/so101_syogi/issues/3)
- [#4 駒台の在庫管理](https://github.com/ichirooo6755/so101_syogi/issues/4)
- [#5 囲碁の着手](https://github.com/ichirooo6755/so101_syogi/issues/5)

## 元フォルダとの関係

- 元: `~/Documents/ChatGPT/syogi` → 本リポ `shogi/`
- 元: `~/Documents/ChatGPT/so101` → 本リポ `so101/`（学習 run 等の超大容量は除く）
- 入れていない: `kobelco/`、`nnw/`（対応表は [repo-map.md](repo-map.md)）
- 整理の経緯: [organization-2026-11-10.md](organization-2026-11-10.md)
