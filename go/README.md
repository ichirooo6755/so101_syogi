# SO-101 囲碁：KataGoLocalのソース取り込みと統合計画

更新日: 2026-11-11。

このリポジトリを、将棋・囲碁とSO-101制御の本体とします。KataGoLocalから囲碁の局面・棋譜・AI通信などの既存ソースを取り込み、将棋側のカメラ・較正・動作計画・実機制御と接続する計画です。

**現在は既存ソースを無変更でコピーした段階です。囲碁の対局機能としては未統合で、囲碁の実機操作は未検証です。** コピーしたコードは有効な実行経路へ接続していません。

予定・状態・依存関係・完了条件の正本は [project-plan.json](project-plan.json) です。全体の進捗は [../docs/progress.md](../docs/progress.md)、既存の囲碁課題は [Issue #5](https://github.com/ichirooo6755/so101_syogi/issues/5) を参照してください。

## 今回コピーしたもの

- 移植元: 個人用の非公開リポジトリ [notdaigo/KataGoLocal](https://github.com/notdaigo/KataGoLocal)。閲覧には移植元へのアクセス権が必要です。
- 固定した移植元コミット: `7232592822c350cfa2a5720102c8bb39bd942ac5`。
- コピー先: [imports/katago-local/](imports/katago-local/)。元のリポジトリ内パスを維持しています。
- 対象: 下表の既存ソースと、型定義・依存バージョン・設定・機能テストを確認するための関連ファイル、計31ファイル。
- **バイト列を変更せずコピーしています。** 各ファイルの移植元Git blob SHA・SHA-256・サイズ・対応パスを計画JSONの `source_import.files` に記録しています。

コピーは、リファクタリング・言語変換・API統合・依存整理の完了を意味しません。移植対象を再利用できる単位に抽出する作業は今後行います。KataGoLocal本体のファイル・履歴は変更しません。

## 移植対象とTODO

表のパスはすべて `imports/katago-local/` 以下です。コピー済みでも、適応・統合のTODOは未完了です。

| ID | 優先度 | 移植する機能 | 主なコピー元ファイル | 次に必要な作業 |
| --- | --- | --- | --- | --- |
| M01 | 必須 | 囲碁の局面・ルール | `desktop/src/game.ts` | 石配置・手番・取り上げ・自殺手・単純コウ・パス・座標を本体の局面管理へ接続する |
| M02 | 必須 | 棋譜・SGF | `desktop/src/record.ts`, `sgf.ts` | 履歴・初期配置・分岐・コメント・SGF読込保存・KataGo用履歴を抽出する |
| M03 | 必須 | KataGo通信 | `crates/katago-local/src/protocol.rs`, `engine.rs` | GTP/Analysis、応手・評価・中断・タイムアウト・プロセス回収を再利用する |
| M04 | 必須 | 共通データ定義 | `crates/katago-local/src/domain.rs`, `desktop/src/backend.ts` | 色・交点・局面・ルール・コミ・探索条件・解析結果を整理し、UIや旧アプリ固有の型を切り離す |
| M05 | 必須 | AI処理と着手確定 | `desktop/src/application.ts`, `computation.ts` | 古い結果の破棄・保留・中断を抽出し、実物の盤面確認後に確定する方式へ改める |
| M06 | 基本 | 設定保存・解析キャッシュ | `crates/katago-local/src/storage.rs` | 必要な設定・結果・原子的保存を抽出し、新しい保存形式を定義する |
| M07 | 後続 | 解析・検討 | `desktop/src/moveReview.ts`, `crates/katago-local/src/engine.rs` | 勝率・目差・候補手・読み筋・各手評価を任意機能として接続する |
| M08 | 任意 | 碁盤表示 | `desktop/src/GobanView.tsx`, `styles.css` | 既存HTML/JavaScriptへ合わせて書き換えるか、囲碁画面だけReactを使うか判断する |
| M09 | 必須 | 機能テスト | `desktop/tests/`, `crates/katago-local/tests/engine.rs`, `tools/test_desktop_engine.mjs` | ルール・SGF往復・中断・古い結果の拒否を新しい構成で検証する |

`transport.rs` と `compute.rs` は通信・実行方式選択の参照として、`package.json` / lockfile / `Cargo.toml` と型定義・ブラウザー用補助コードは依存関係の参照として同梱しています。これらの設定や依存を本体へ一括採用するという意味ではありません。

## 言語・構成の方針

既存の将棋本体は [Pythonサーバー](../shogi/app/server.py) と [HTML/JavaScript画面](../shogi/app/index.html) です。移植元はTypeScript / React / Rustですが、**元の言語や構成を維持することを条件にしません。**

- 対局管理・ロボットとの接続・囲碁ロジックは、既存本体と対応させやすいPythonへの移植や既存ライブラリへの置換も候補とします。
- KataGo通信はPythonから直接GTP/Analysisを扱う案と、既存Rust処理を独立した子プロセスとして残す案を比較します。KataGo自体を作り直す計画ではありません。
- TypeScriptの局面・SGF処理を残す場合は、Pythonとの境界と実行環境を明示します。ブラウザーとPythonで別々の正しい局面を持つ構成にはしません。
- UIは既存HTML/JavaScriptへの適応を候補とし、React / Node.js / Tauriの追加を前提にしません。
- 判断理由、必要な実行環境、依存版、機能の対応関係をJSONへ記録してから統合します。今回は原文コピーだけで、言語選定や言語変換は未実施です。

## 互換性と対象外

旧CLI/API名、旧DB・旧キャッシュ形式、旧アプリの画面仕様との互換は維持しません。ただし、囲碁ルールや棋譜保存、中断時に状態を壊さない性質は機能として検証します。

取り込んだ原文には、旧互換処理の分岐・参照・テストが一部残っています。これは無変更コピーのためで、互換維持を移植要件に戻すものではありません。`engine.rs` / `domain.rs` / `storage.rs` / `transport.rs` / エンジンテスト内の不要部分は、後続の抽出時に整理します。

次はコピーしていません。

- `legacy.rs`、旧CLI用Rust版 `board.rs` / `sgf.rs`、互換性比較用 `compatibility.rs` とfixture。
- アプリ全体の `App.tsx`、Tauriシェル、Windowsインストーラー、Windows専用GPU検出コード、Windows用取得処理。
- KataGo実行ファイル・DLL・学習モデル・ダウンロードZIP・DB・認証情報・実機較正値・ブラウザープロファイル・大容量の実験データ。

**このコピーだけでビルド・起動できるパッケージにはなっていません。** 参照先が未同梱のコードや、元アプリ前提の設定もあります。取り込み先でのビルド、機能テスト、実機試験はまだ行っていません。

## 将棋側から共通利用するもの

| 領域 | 既存の対応先 | 囲碁で必要な適応 |
| --- | --- | --- |
| カメラ・ファーム | `shogi/app/usb_camera.py`, `mac_camera.py`, `shogi/firmware/ShogiCamera/` | 同じ撮影経路から、囲碁用の盤認識へ画像を渡す |
| 四隅検出・較正 | `shogi/app/markers.py`, `board_tracking.py`, `board_pose.py` | 実測した囲碁盤と観測姿勢で検証する |
| 盤座標 | `shogi/app/board_map.py`, `docs/board-geometry.md` | 9×9のマス中心・将棋の筋段を、9/13/19路の交点座標へ一般化する |
| 動作計画・到達評価 | `shogi/app/motion.py`, `move_plan.py`, `shogi/simulation/` | 碁石形状・密集配置・供給位置・回収位置・連続経路を扱う |
| 実機制御・教示 | `shogi/app/robot_arm.py`, `lerobot_motion.py`, 教示モジュール | 共通の較正・停止・機体識別を使う。既存の実機ゲートは維持する |
| 対局ループ | `shogi/app/server.py` の予定手・リビジョン・再観測の考え方 | 将棋のSFEN/USIと囲碁の局面・着手をゲーム別アダプターで分ける |

既存資産は試作・未統合の部分を含みます。将棋側でコードが存在することを、囲碁での実機検証済みとは扱いません。駒台の在庫管理は石の供給・回収設計の参考ですが、そのまま碁笥の実装にはなりません。

## 新規実装のTODO

- [ ] N01: Pythonへの書き換えを含めて言語とプロセス構成を選び、依存関係・単位・色・座標・局面の正本を定義する。
- [ ] N02: 本体の対局ループと囲碁機能を接続するアダプターを作る。将棋用のSFEN/USIや固定9×9処理を囲碁に流用しない。
- [ ] N03: 9路盤から実寸・厚さ・交点間隔・盤の向き・石径・爪寸法・供給/回収位置を測り、ロボット座標へ変換する。13/19路は到達評価後に拡張する。
- [ ] N04: 黒石・白石・空交点を認識し、人の着手・取られた石・遮蔽・盤ずれを照合する。将棋の画像差分は9×9と駒の移動を前提にしており、そのままでは使えない。
- [ ] N05: 石の供給、把持、配置、複数石の回収を実装し、隣接石との干渉と取り出し可能性を評価する。
- [ ] N06: 「着手予定→配置→回収→再観測→局面確定」の途中状態を記録し、失敗・切断・再試行で同じ石を二度処理しない復旧を作る。パス・投了は物理動作と区別する。
- [ ] N07: 採用ルール、スーパーコウ、連続パス、投了、死活確認・地合い計算・結果確定を整備する。既存の単純コウ処理だけで全ルール対応とはしない。
- [ ] N08: [KataGo・モデル・設定の配置と起動手順](#katagoの準備と起動)を用意済み。Windows x64で9路の応手を確認。macOSでのビルド・応手と対局アプリからの中断は未検証。
- [ ] N09: 9路の模擬対局と全交点・供給/回収位置の連続経路をシミュレーションで評価し、成功条件・失敗記録を残す。
- [ ] N10: 将棋側の実機ゲートを通した機体で単石・複数石回収・連続対局を段階評価する。実測と未検証を分けて記録する。

## KataGoの準備と起動

リポジトリのルートでPython 3.11以降と `tar` を使います。Windows x64では公式のKataGo v1.17.1 CPU版を取得します。macOSではXcode Command Line ToolsとHomebrewの `cmake`、`eigen` を用意すると、同じバージョンをCPU向けにビルドできます。

```sh
python install_game_engine.py go
python go/run_katago.py gtp
```

Windowsで `python` が使えない場合は `py`、macOSでは `python3` で実行できます。再利用する配布ファイルの保存先は `--cache` で指定できます。取得した配布物はSHA-256を照合します。

- 実行ファイルは `go/vendor/KataGo/engine/katago`、Windowsでは同じ場所の `katago.exe`。Windows版に同梱されたDLLも隣に配置します。
- 学習済みモデルは `go/vendor/KataGo/models/b10c384h6nbttflrs.bin.gz`。
- 設定は `go/vendor/KataGo/config/`。GTP用の `default_gtp.cfg` と解析用の `analysis_example.cfg` を収録し、`python go/run_katago.py analysis` で解析モードを起動します。

[KataGo v1.17.1 公式配布](https://github.com/lightvector/KataGo/releases/tag/v1.17.1)

## 進める順序

1. 原文コピーと出典・計画の保存（今回）。
2. 言語・プロセス境界・局面の正本の決定。
3. 画面やアームに依存しない9路の局面・SGF・KataGo応手を成立させる。
4. 模擬アームと接続し、着手予定・石取り・中断・再試行・確定の流れを確認する。
5. 実寸の盤・石・アームでシミュレーションと到達・干渉評価を行う。
6. [Issue #1](https://github.com/ichirooo6755/so101_syogi/issues/1) の関節制御・較正を確認した後、9路で実機評価する。[Issue #2](https://github.com/ichirooo6755/so101_syogi/issues/2) の延長設計と [Issue #3](https://github.com/ichirooo6755/so101_syogi/issues/3) の実測も参照する。
7. 9路の結果を基に13/19路と任意の解析UIを拡張する。

実機の接続状況・寸法・言語選定が未確定なので、完了日は未設定です。実装・ソフトウェア検証・シミュレーション・実機検証を別々に更新します。
