# 並列度の観測メモ（16GB M1 Pro）

本ドキュメントは本番 `kaisho-yohitsu-5x` の観測と、2026-08-17 の並列ベンチ結果を残す。

## 既知の制約

- `DummyVecEnv` では `n_envs` を増やしてもコアを使わない
- 学習は `SubprocVecEnv(spawn)`。軌跡が各 worker に複製されるため RAM が主制約
- BC は ProcessPool → デモ解放 → Dummy×1 bootstrap → Subproc×N の順が安全
- `--device auto` は未実装（明示的に `cpu` / `mps`）
- 8 以上の env は全数評価シャード向け。学習では OOM / silent death / BrokenProcessPool のリスクが高い

## 本番観測（`kaisho-yohitsu-5x`, n_envs=6, device=mps）

- BC workers 6 + PPO Subproc 6 で長時間稼働を確認（累積 ~1,577万 step）
- 学習木の RSS はおおよそ 1.2 GiB 前後でも、圧縮と約 1 GiB 級の swap が出ることがある
- ファン回転は負荷指標として弱い。判定は fps / CPU / RSS / swap / クラッシュ有無

## 失敗観測（`kaisho-yohitsu-5x-hard-hi`, n_envs=8）

- BC demo 収集で `BrokenProcessPool`（workers=8）
- 以後の学習並列は `bc-workers<=6` を上限とする

## 正式ベンチ結果（2026-08-17）

フル professional セル行列は、SSD 復旧プロセス共存下の 16GB メモリ逼迫で torch import が飢餓/jetsam され完走できなかった。代替として:

```bash
PYTHONPATH=src python scripts/benchmark_subproc_scaling.py \
  --output runs/parallel-benchmark \
  --envs 5,6,7 --seeds 31,37 --steps 40
```

- Gymnasium `AsyncVectorEnv` の process overhead は `n_envs=7` が最高スループット、swap Δ≈0
- 成果物: `runs/parallel-benchmark/benchmark.json` / `recommended.env` / `README.md`

### 推奨構成（学習）

- **既定**: `--n-envs 6 --bc-workers 6 --device mps`
- **監視下の上限**: `n_envs=7`（tiny-env では安定、MuJoCo本番は未再測）
- **禁止寄り**: 学習で `n_envs>=8`（BC BrokenProcessPool）
- **複数 seed 並走**: 現状の 16GB + IDE/復旧同居では非推奨（単一 run を優先）

`scripts/run_kaisho_5x.sh` と hard-mining 起動は上記既定に合わせる。
長時間ランチャー（`run_overnight_until.sh` / `run_kaisho_5x.sh` / `post_5x_pipeline.sh`）は `caffeinate -dims` でアイドル睡眠を抑止する。蓋を閉じると止まることがあるので、電源接続のまま開ける。すでに動いている学習へ後付けするなら `caffeinate -dims -w <pid>`。
メモリに余裕があるときだけ、追加で:

```bash
PYTHONPATH=src python scripts/benchmark_professional_parallelism.py \
  --model runs/kaisho-yohitsu-5x/final_model.zip \
  --output runs/parallel-benchmark-pro \
  --envs 5,6,7 --devices cpu,mps --seeds 31,37 \
  --timesteps 8192 --start-stage 8
```
