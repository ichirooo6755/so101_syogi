# 大容量ファイルの一覧（実ファイルを入れていないもの）

2026-11-10 の取り込みで、GitHub の上限（1 ファイル 100 MB、リポジトリは実質 1 GB 程度が目安）を
超える／膨らむため実ファイルを入れなかったものの一覧です。**進捗が無いという意味ではありません。**
いずれも生成元スクリプト・要約・代表出力はリポジトリに入れてあります。元ファイルは
ローカルの `~/Documents/ChatGPT/` 側に残っています（削除していません）。

| 対象 | 規模（見かけ） | 入れなかった理由 | 代わりに辿れるもの |
| --- | --- | --- | --- |
| `so101/syodo/runs/`（書道の学習・評価 run） | 約 3.4 GB、約 19 万ファイル、279 項目 | リポジトリ上限を大きく超える | 要約台帳 `so101/syodo/docs/training-runs.md`、結果 `so101/syodo/docs/results/`、モデル `so101/syodo/models/`（PPO zip・評価 JSON） |
| `syogi/simulation/runs/`（将棋の学習 run） | 約 779 MB、2133 ファイル（`.pt` 741、`.npz` 371、`.json` 1021） | 同上。GUI はこの学習結果を使わず IK が正本 | 記録は `shogi/simulation/README.md` と `shogi/README.md` の学習節（最良は未見 10/12、round 375）。チェックポイントが必要なら元フォルダから個別に拾う |
| `so101/soap_film/output/` の `state_*.npz` と連番フレーム | `.npz` 260 個・約 3.9 GB、PNG 1072 枚・約 578 MB | 同上 | 代表出力（preview MP4/GIF、8K 代表画像、settings.json、comparison.json）を `so101/soap_film/output/` に収録。生成元は `so101/soap_film/*.py` |
| `so101/output/` の FEM 結果 `*.vtu`（81 個・約 1.1 GB）、`*.msh`（12 個・約 158 MB）、`*.npz` | 約 1.2 GB | 再生成できる中間結果 | 生成元 `so101/scripts/`（build/check/export 群）と、結論側の `*.json` 検査記録・STEP/STL は `so101/output/` に収録 |
| `.f3d` の中間バックアップ（`*_before_*`、`source_cad/` の重複、`*_backup.f3d` 等、112 個・約 360 MB の大半） | 各約 10 MB が多数重複 | 同じアセンブリの複製が多くリポジトリが膨らむ | 完成形は `so101/output/*.f3d`、`so101/output/camera_mount_v8/*.f3d`、印刷パッケージ zip 内の F3D/STEP、バージョンごとの STEP/STL を収録。変更前スナップショットの置き場は `so101/reference/`（STEP/STL・資料を収録） |
| `so101/syodo/data/`（KanjiVG・kanjidic2・animcjk 等と `hardware/desk.json`） | 約 76 MB、2326 ファイル | 元リポジトリ（syodo）でも Git 対象外のデータセットと実機較正値 | 取得元は `so101/syodo/THIRD_PARTY.md` と各 README。較正は実機で再作成する |
| 仮想環境（`so101/.analysis-venv/`、`so101/syodo/.venv/`、`syogi/.venv*/`）、`vendor/`、`build/` | 各数百 MB | 再作成・再取得できる | `requirements.txt`、`shogi/scripts/fetch_upstream.sh` |

## 必要になったら

1. まずこの表の「代わりに辿れるもの」で足りるか確認する。
2. 実ファイルが要る場合は元フォルダ（`~/Documents/ChatGPT/...`）から対象だけを拾い、
   恒常的に必要なら Git LFS 等の別管理を検討して、この表を更新する。
3. 大きなファイルを通常コミットで追加しないこと（100 MB 超は push できません）。
