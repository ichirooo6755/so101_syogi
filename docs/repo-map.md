# 元フォルダとの対応（repo-map）

2026-11-10 に `~/Documents/ChatGPT/` から本リポジトリへ移したときの記録です。
初回は将棋・囲碁に関係するものだけを入れ、その後「SO-101 の進捗も全部」という
追加指示で `so101/` も取り込みました。現在も入れていないのは `kobelco` と `nnw` だけです。

## 入れたもの

| 元の場所 | 移行先 | 備考 |
| --- | --- | --- |
| `~/Documents/ChatGPT/syogi/`（一式） | `shogi/` | 将棋本体。元の Git 管理対象ファイル＋未コミット変更（`app/lerobot_motion.py`、上腕 +100/+125 試作、公式 URDF 生成など）を含む |

将棋フォルダ内でも次は**含めていません**（元の `.gitignore` 方針を踏襲）。

| 除外 | 理由・再取得方法 |
| --- | --- |
| `.venv/`, `.venv-sim/` | 仮想環境。`requirements.txt` から作り直す |
| `vendor/`（Fairy-Stockfish、so101-manipulation-eval） | 上流リポジトリ。`shogi/scripts/fetch_upstream.sh` で取得 |
| `build/`（ファームのビルド成果物） | `shogi/firmware/ShogiCamera/` から再ビルド |
| `simulation/runs/` | 学習・試行の途中データ。重い |
| `simulation/model/shogi_scene_*.xml` | 生成物 |
| `app/follower_offsets.json` | 実機の較正値（個人の実測）。実機で再記録 |
| `firmware/ShogiCamera/wifi_config.h` | Wi-Fi 設定（秘密情報）。`wifi_config.example.h` から作る |
| `__pycache__/`, `*.pyc`, `.DS_Store`, `*.log` | 生成物・OS ファイル |

※ `output/firmware_xiao/`、`output/*.zip`、スライサ出力（slice フォルダ）は
追加整理で収録に切り替えました。

## 入れなかったもの（プロジェクト単位で対象外）

| 元の場所 | 内容 | 入れない理由 |
| --- | --- | --- |
| `~/Documents/ChatGPT/kobelco/` | 別プロジェクト | ユーザー指示で明示的に対象外（現在も入れていない） |
| `~/Documents/ChatGPT/nnw/` | NW-E507 型 USB-C DAP の基板・ファーム（約 3 GB） | 将棋・囲碁・SO-101 と無関係（現在も入れていない） |

## 追加で入れたもの（2026-11-10 11:29 の指示）

初回整理では対象外にした SO-101 本体まわりも、「進捗も全部入れて」という指示で追加しました。

| 元の場所 | 移行先 | 備考 |
| --- | --- | --- |
| `~/Documents/ChatGPT/so101/output/`, `scripts/`, `reference/`, `tmp/`, `組立部品表.md`, `SC616C-1kg load cell.pdf`, `result.json` | `so101/` 配下（元構成のまま） | 手首カメラ＋HX711 台座と筆保持の進捗。大容量の中間ファイルは [large-artifacts.md](large-artifacts.md) 参照 |
| `~/Documents/ChatGPT/so101/syodo/` | `so101/syodo/` | 書道。正本は別リポジトリ https://github.com/ichirooo6755/syodo 。`runs/` と `data/` は入れていない |
| `~/Documents/ChatGPT/so101/soap_film/` | `so101/soap_film/` | 薄膜シミュ。コードと代表出力のみ |

## 囲碁について

ローカルに囲碁の実装ファイルは無かったため、`go/README.md` の設計メモだけ新規作成した。
実装が始まったら `go/` 配下にコードを置き、盤座標は `docs/board-geometry.md` を更新する。

## 元フォルダ側の注意

- 元の `~/Documents/ChatGPT/syogi/` は Git リポジトリで、未コミット変更があった。
  本リポジトリへのコピーはその作業ツリーの内容で行った（元は変更していない）。
- 移行後も元のフォルダは消していない。どちらを正本にするかは運用で決め、
  二重管理になる場合は片方へ寄せること（推奨: 本リポジトリを正本にする）。
