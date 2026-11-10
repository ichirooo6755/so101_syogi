# SO-101 で将棋と囲碁をやる

SO-101（SO-ARM101 系 6 軸アーム）で、実物の将棋と囲碁を人と対局できるようにするプロジェクトです。
**現状は将棋の開発途中で、実機対局はまだ成立していません。囲碁は未着手です。**

- 対象リポジトリ: https://github.com/ichirooo6755/so101_syogi
- 作業元（ローカル）: `~/Documents/ChatGPT/syogi` が将棋の本体、`~/Documents/ChatGPT/so101` が SO-101 本体まわり（カメラ／ロードセル台座・書道）。どちらも本リポジトリに入れました。`nnw`、`kobelco` は別プロジェクトなので入れていません（理由は [docs/repo-map.md](docs/repo-map.md)）。

## 現在地（2026-11-10 時点・引き継ぎ用）

| 項目 | 状態 |
| --- | --- |
| 将棋 GUI・対局ループ（Mac 上） | 実装あり。人の手を画像差分＋合法手で候補化し、Fairy-Stockfish が応手を選ぶ |
| 盤の認識 | ArUco マーカー 4 枚で盤四隅を検出し正面化する試作あり。実盤・実照明での精度は未測定 |
| アーム動作計画 | シミュレーション（MuJoCo）で移動・取り・打ち・成りの計画と到達可否を評価済み。実機送信は停止中 |
| 実機（Follower） | USB 未接続の記録が最新。`shogi/app/robot_arm.py` はトルク有効化を拒否する。実機で駒をつかむ／取る／打つ／成るは未検証 |
| 上腕延長部品 | +50 / +58 / +75 / +100 / +125 mm の比較試作（STEP/STL・試算 JSON）。最終寸法は未決定、未印刷のものを含む |
| 手首カメラ | XIAO ESP32S3 Sense 用ファーム（`shogi/firmware/ShogiCamera/`）とマウント試作あり。実機撮影は未試験 |
| 囲碁 | **未着手。** 設計メモだけ [go/README.md](go/README.md) に置いた |

詳しい現状・次にやることは将棋側の正本 [shogi/README.md](shogi/README.md) と
[shogi/docs/shogi-implementation-plan.md](shogi/docs/shogi-implementation-plan.md) が優先です。
本 README と食い違う場合はそちらを正としてください。

## フォルダ構成（ファイルの位置関係）

```
.
├── README.md                  # このファイル（全体の引き継ぎ）
├── docs/
│   ├── organization-2026-11-10.md  # 2026-11-10 の整理の経緯・選別判断・検証結果
│   ├── repo-map.md            # 元フォルダとの対応・上げなかったものと理由
│   └── board-geometry.md      # 盤面のマス／交点の位置関係（将棋9×9・囲碁19路）
├── shogi/                     # 将棋本体（元 ~/Documents/ChatGPT/syogi）
│   ├── README.md              # 将棋の現状・起動・検証の正本
│   ├── app/                   # GUI・認識・動作計画・実機ゲート
│   ├── cad/                   # 上腕延長・カメラマウントの生成コードと上流 STEP
│   ├── docs/                  # 設計計画・Leader 教示・STEP 検査
│   ├── firmware/ShogiCamera/  # XIAO ESP32S3 Sense 手首カメラ
│   ├── simulation/            # MuJoCo 到達・接触・経路評価（runs/ は含めない）
│   ├── tests/                 # 単体テスト
│   ├── scripts/fetch_upstream.sh  # vendor/ の再取得（Fairy-Stockfish 等）
│   └── output/                # 延長部品 STEP/STL と試算 JSON、マウント試作
├── go/                        # 囲碁（未着手、設計メモのみ）
│   └── README.md
└── so101/                     # SO-101 本体まわり（元 ~/Documents/ChatGPT/so101）
    ├── README.md              # 本体側の進捗の索引
    ├── output/                # 手首カメラ＋HX711台座 V1–V8、筆保持 V2–V8
    ├── scripts/               # 上記CADの生成・検査スクリプト
    ├── reference/             # 変更前スナップショットと資料
    ├── syodo/                 # 書道（別リポジトリ syodo と同内容の取り込み）
    └── soap_film/             # 薄膜シミュ（履歴として取り込み、代表出力のみ）
```

将棋・囲碁で共有する盤座標の考え方は [docs/board-geometry.md](docs/board-geometry.md) にまとめました。
将棋のマス中心の計算は `shogi/app/board_map.py` が正本です。

## 動かし方（将棋）

```sh
cd shogi
./scripts/fetch_upstream.sh          # vendor/ を取得（既存は変更しない）
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make -C vendor/Fairy-Stockfish/src -j4 build ARCH=apple-silicon largeboards=yes
# 既存環境がある Mac では 将棋GUI.command を開く
```

シミュレーションは Python 3.12 の `.venv-sim` と `shogi/simulation/requirements.txt` が別途必要です。
検証: `shogi/README.md` の「検証と参考資料」を参照。

## GitHub に上げていないもの

- `kobelco/` — 明示的に対象外。別プロジェクト。
- `nnw/` — NW-E507 型 DAP の基板・ファーム。将棋・囲碁と無関係。
- 大容量の再生成できる中間ファイル（書道・将棋の学習 run、FEM の `.vtu/.msh`、薄膜の `state_*.npz`、`.f3d` 中間バックアップ、仮想環境、`vendor/`、`build/`、Wi-Fi 設定、実機較正値）は実ファイルを入れず、生成元と一覧で辿れるようにしています。一覧は [docs/large-artifacts.md](docs/large-artifacts.md)。
- SO-101 本体まわり（台座・書道・薄膜）は 2026-11-10 の追加整理で `so101/` に入れました。経緯は [docs/organization-2026-11-10.md](docs/organization-2026-11-10.md)。

## 課題管理（GitHub Issues）

作業は Issue で追います。引き継ぐ人はまず open Issue と本 README を見てください。

- [#1 実機対局の成立（関節制御・較正・単駒把持）](https://github.com/ichirooo6755/so101_syogi/issues/1)
- [#2 上腕の延長寸法の決定（+58/+75/+100/+125 の比較を実測で決める）](https://github.com/ichirooo6755/so101_syogi/issues/2)
- [#3 盤面の位置関係の実測（盤寸法・マス間隔・駒台スロット・裏返し台）](https://github.com/ichirooo6755/so101_syogi/issues/3)
- [#4 駒台の在庫管理（持ち駒の駒種・空き場所）](https://github.com/ichirooo6755/so101_syogi/issues/4)
- [#5 囲碁の着手（19 路盤の交点座標・石の把持・ルールエンジン選定）](https://github.com/ichirooo6755/so101_syogi/issues/5)

## 注意

- 実機が未準備な状態で成功を保証する記述を増やさないこと。「シミュレーションで浮いた＝実機でできる」ではありません。
- 鍵・Wi-Fi 情報・個人の接続情報をコミットしないこと。
- 大きな学習データ・動画・重みは本リポジトリに入れず、別管理にして参照だけ書くこと。
