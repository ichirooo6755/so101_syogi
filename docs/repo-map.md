# 元フォルダとの対応（repo-map）

2026-11-10 に `~/Documents/ChatGPT/` から本リポジトリへ移したときの記録です。
「kobelco 以外全部」ではなく、**将棋と囲碁を SO-101 でやるのに関係するものだけ**を入れました。

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
| `output/firmware_xiao/`, `output/*.zip` | ビルド済みファームと配布 zip。ソースから再生成 |
| `output/camera_xiao/slice/`, `output/upper_arm_extension/slice_*/`（gcode/3mf 等） | スライサ出力。STEP/STL から再生成 |
| `__pycache__/`, `*.pyc`, `.DS_Store`, `*.log` | 生成物・OS ファイル |

## 入れなかったもの（プロジェクト単位で対象外）

| 元の場所 | 内容 | 入れない理由 |
| --- | --- | --- |
| `~/Documents/ChatGPT/kobelco/` | 別プロジェクト | ユーザー指示で明示的に対象外 |
| `~/Documents/ChatGPT/nnw/` | NW-E507 型 USB-C DAP の基板・ファーム（約 3 GB） | 将棋・囲碁と無関係 |
| `~/Documents/ChatGPT/so101/syodo/` | SO-101 書道（筆・ロードセル学習、約 3.4 GB の `runs/` を含む） | SO-101 は使うが将棋・囲碁用ではない。別リポジトリ（syodo）で管理済み |
| `~/Documents/ChatGPT/so101/soap_film/` | 球面の薄膜シミュレーター（約 88 MB の出力） | 無関係 |
| `~/Documents/ChatGPT/so101/output/`, `scripts/`, `reference/`, `組立部品表.md`, `SC616C-1kg load cell.pdf` | 筆用カメラ／HX711 ロードセルマウント（V1–V8）と生成スクリプト群 | 書道の筆圧計測用。将棋の手首カメラは `shogi/output/camera_xiao/` と `shogi/camera_mount_*.step` が別にあり、そちらを入れた |

迷ったもの: `so101/` のカメラマウントは「SO-101 の手首にカメラを付ける」点では将棋と近いが、
実体は筆＋ロードセルの計測治具で、将棋側は独自マウント（XIAO 用）を既に持っているため対象外にした。
将棋で力覚が必要になったら、その時点で必要な部品だけを `shogi/` 側へ取り込む。

## 囲碁について

ローカルに囲碁の実装ファイルは無かったため、`go/README.md` の設計メモだけ新規作成した。
実装が始まったら `go/` 配下にコードを置き、盤座標は `docs/board-geometry.md` を更新する。

## 元フォルダ側の注意

- 元の `~/Documents/ChatGPT/syogi/` は Git リポジトリで、未コミット変更があった。
  本リポジトリへのコピーはその作業ツリーの内容で行った（元は変更していない）。
- 移行後も元のフォルダは消していない。どちらを正本にするかは運用で決め、
  二重管理になる場合は片方へ寄せること（推奨: 本リポジトリを正本にする）。
