# 整理記録（2026-11-10）

`~/Documents/ChatGPT/` に散らばっていたファイルから、SO-101 で将棋と囲碁をやるのに
関係するものだけを、このリポジトリ（https://github.com/ichirooo6755/so101_syogi）へ
移して整理したときの記録です。引き継ぐ人は、まずこのファイルとルート `README.md` を
読んでください。元フォルダとの対応表は [repo-map.md](repo-map.md) にあります。

## 何をしたか

| # | 作業 | 内容 |
| --- | --- | --- |
| 1 | 対象リポジトリの確認 | `ichirooo6755/so101_syogi` は README だけの初期状態（Initial commit のみ）だった |
| 2 | 元フォルダの棚卸し | `~/Documents/ChatGPT/` 直下は `kobelco` / `nnw` / `so101` / `syogi` の 4 つ |
| 3 | 将棋一式の移行 | `syogi/` の作業ツリー（未コミット変更を含む）を `shogi/` へコピー。176 ファイル・約 59 MB |
| 4 | 囲碁の置き場を新規作成 | ローカルに囲碁の実装が無かったため `go/README.md` に設計メモだけ置いた |
| 5 | 盤面位置関係の整理 | `docs/board-geometry.md` を新規作成（将棋 9×9 マス／囲碁 19 路交点） |
| 6 | 引き継ぎ README の作成 | ルート `README.md` に現状・構成・起動・注意を集約 |
| 7 | GitHub Issue の作成 | 残作業を Issue #1–#5 に切り、README からリンク |
| 8 | push | コミット `08eb4da`（本体）と `a7319da`（Issue リンク追加）を `main` へ push |

## 選別の判断

指示は「kobelco 以外全部」かつ「将棋と囲碁を SO-101 でやるのに関係ないものは上げない」
だったため、後者を優先して選別しました。

### 入れたもの

- `syogi/` 一式 → `shogi/`
  - アプリ（`app/`）、CAD（`cad/`）、設計ドキュメント（`docs/`）、手首カメラの
    ファーム（`firmware/ShogiCamera/`）、シミュレーション（`simulation/`）、
    テスト（`tests/`）、上腕延長部品と XIAO マウントの試作（`output/`）を含む
  - 元リポジトリで**未コミットだった変更も含む**:
    `app/lerobot_motion.py`、上腕 +100 / +125 mm 試作（STEP/STL・試算 JSON）、
    公式 URDF 生成（`simulation/build_official_urdf.py` ほか）、`tests/test_lerobot_motion.py`

### 入れなかったもの

| 対象 | 理由 |
| --- | --- |
| `kobelco/` | 指示で明示的に対象外 |
| `nnw/`（約 3 GB） | NW-E507 型 DAP の基板・ファーム。将棋・囲碁と無関係 |
| `so101/syodo/`（書道、検証データ含め大容量） | SO-101 は使うが将棋・囲碁用ではない。別リポジトリ（syodo）で管理済み |
| `so101/soap_film/` | 球面の薄膜シミュレーター。無関係 |
| `so101/output・scripts・reference`、`組立部品表.md`、`SC616C-1kg load cell.pdf` | 筆用カメラ／HX711 ロードセルマウント（V1–V8）。書道の筆圧計測用。将棋の手首カメラは将棋側に独自マウント（`shogi/output/camera_xiao/`、`shogi/camera_mount_*.step`）があるため対象外にした。迷った点として [repo-map.md](repo-map.md) にも明記 |

### 将棋フォルダ内でも除外したもの

元の `syogi/.gitignore` の方針を踏襲し、ルート `.gitignore` にも同じ除外を書きました。

- `.venv/`、`.venv-sim/` — 仮想環境（`requirements.txt` から再作成）
- `vendor/` — 上流（Fairy-Stockfish 等）。`shogi/scripts/fetch_upstream.sh` で再取得
- `build/` — ファームのビルド成果物
- `simulation/runs/` — 学習・試行の途中データ
- `app/follower_offsets.json` — 実機の較正値（個人の実測値）
- `firmware/ShogiCamera/wifi_config.h` — Wi-Fi 設定（秘密情報）。雛形は `wifi_config.example.h`
- `output/firmware_xiao/`、`output/*.zip`、スライサ出力（`slice/` 配下の gcode / 3mf 等）
- `__pycache__/`、`*.pyc`、`.DS_Store`、`*.log`

秘密情報の混入チェック: `wifi_config.h` 本体は含めていないこと、パスワード類が
コードに直書きされていないことをステージ時点で確認しました。

## 整理後のフォルダ構成

```
.
├── README.md                  # 全体の引き継ぎ（現状・構成・起動・課題リンク）
├── docs/
│   ├── organization-2026-11-10.md  # このファイル（整理の経緯）
│   ├── repo-map.md            # 元フォルダとの対応・除外理由
│   └── board-geometry.md      # 盤面のマス／交点の位置関係
├── shogi/                     # 将棋本体（元 ~/Documents/ChatGPT/syogi）
└── go/                        # 囲碁（未着手、設計メモのみ）
```

将棋・囲碁で共有する盤座標の考え方は `docs/board-geometry.md` に寄せ、
将棋のマス中心計算の正本は `shogi/app/board_map.py` のままにしました。
将棋側の内部リンク（`shogi/README.md` から `docs/` や `output/` への相対参照）は
`shogi/` 配下で完結するので壊れていません。

## 作った GitHub Issue

| Issue | 内容 |
| --- | --- |
| [#1](https://github.com/ichirooo6755/so101_syogi/issues/1) | 実機対局の成立: 公式 LeRobot で関節制御と単駒把持を確認する |
| [#2](https://github.com/ichirooo6755/so101_syogi/issues/2) | 上腕の延長寸法を決める（+58/+75/+100/+125 の比較を実測で確定） |
| [#3](https://github.com/ichirooo6755/so101_syogi/issues/3) | 盤面の位置関係を実測する（盤寸法・マス間隔・駒台・裏返し台） |
| [#4](https://github.com/ichirooo6755/so101_syogi/issues/4) | 駒台の在庫管理（持ち駒の駒種・空き場所・成駒の表戻し） |
| [#5](https://github.com/ichirooo6755/so101_syogi/issues/5) | 囲碁の着手（19 路盤の交点座標・石の把持・ルール選定） |

## 追加整理（2026-11-10 11:29 の指示で実施）

「`so101` と将棋・囲碁の進捗も全部入れて」という追加指示を受け、初回整理で外した
SO-101 本体まわりも取り込みました。

| 追加したもの | 置き場 | 備考 |
| --- | --- | --- |
| 手首カメラ＋HX711 台座 V1–V8、筆保持 V2–V8 の CAD・印刷パッケージ・検査記録 | `so101/output/`（元構成のまま） | 完成形の STEP/STL・印刷 zip・検査 JSON を収録。説明の正本は `so101/output/README.md` |
| 上記 CAD の生成・検査スクリプト群（約 250 ファイル） | `so101/scripts/` | 成果物の生成元 |
| 変更前スナップショット、データシート、XIAO 公式資料 | `so101/reference/` | `.f3d` 本体は中間複製を除き収録 |
| 組立部品表、ロードセル資料、結果ファイル | `so101/組立部品表.md`、`so101/SC616C-1kg load cell.pdf`、`so101/result.json`、`so101/tmp/` | - |
| 書道一式（コード・ドキュメント・モデル・ファーム） | `so101/syodo/` | 正本は別リポジトリ https://github.com/ichirooo6755/syodo 。これは同内容の取り込みで、二重管理に注意 |
| 薄膜シミュレーター | `so101/soap_film/` | コードと代表出力（preview・設定・比較結果）を収録 |
| 将棋の書き込み用ファーム bin、配布 zip、スライス結果 | `shogi/output/firmware_xiao/`、`shogi/output/*.zip`、`shogi/output/*/slice*/` | 初回整理で外した小さな出力も追加 |

### それでも実ファイルを入れていないもの

GitHub の上限（1 ファイル 100 MB、リポジトリは実質 1 GB 程度）を超えるため、
実ファイルではなく生成元・要約・一覧で辿れるようにしました。詳細は
[large-artifacts.md](large-artifacts.md) を参照。

- 書道の学習 run `syodo/runs/`（約 3.4 GB・約 19 万ファイル）→ 要約は `so101/syodo/docs/training-runs.md`
- 将棋の学習 run `shogi/simulation/runs/`（約 779 MB）→ 記録は `shogi/simulation/README.md`
- 薄膜の状態ファイル `state_*.npz` 群（約 3.9 GB）と連番フレーム
- FEM の場の結果 `*.vtu`・メッシュ `*.msh`（約 1.2 GB、生成元は `so101/scripts/`）
- `.f3d` の中間バックアップ複製（完成形は収録）
- 書道のデータセット `syodo/data/`（元リポジトリでも Git 対象外、実機較正を含む）
- 仮想環境・`vendor/`・`build/`

なお、元フォルダの多数のファイルがクラウドの未取得（dataless）状態だったため、
コピー時に取得を伴い時間がかかりました。取得できなかったファイルがあれば
`docs/large-artifacts.md` の手順で元フォルダから個別に追加してください。

## 検証したこと／できていないこと

- ✅ コピー漏れ: 元 `syogi/` の `app/`・`tests/`・`docs/` と移行先を `diff` で照合し、
  差分が `__pycache__` だけであることを確認
- ✅ リモート確認: push 後に GitHub API でツリー（`.gitignore`、`README.md`、`docs/`、
  `go/`、`shogi/`）と Issue #1–#5 の作成を確認
- ⚠️ テスト再実行は未完了: 移行先で元の `.venv` を使った `unittest` が、ライブラリ
  読み込み（dyld）で進まず時間内に終わらなかったため中断した。コードのエラーでは
  ありません。再実行は `shogi/` で次を行ってから:
  1. `./scripts/fetch_upstream.sh`
  2. `python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt`
  3. `.venv/bin/python -m unittest discover -s tests`
- 元フォルダ（`~/Documents/ChatGPT/syogi/` 等）は削除していません。今後の正本は
  本リポジトリとし、元フォルダ側で作業を続ける場合は二重管理に注意してください。
