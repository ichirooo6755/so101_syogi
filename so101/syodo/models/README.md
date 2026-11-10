# 学習済みPPOモデル

## 画像お手本付き常用漢字モデル

`professional-image-v3-ppo.zip`は371次元の画像・筆・墨観測を使う現行モデルです。
検証済みAoyagi Kouzan画像、KanjiVGの筆順・画種、AnimCJKの日本語中心線と線幅を
教師に、硯から始まる7段階で学習しました。

```bash
source .venv/bin/activate
mjpython -m so101_calligraphy.training.replay \
  models/professional-image-v3-ppo.zip --kanji 書 --professional \
  --save-ink outputs/sho.png
```

検証値:

- 累積PPO step: 31,744（前段の画像条件付きsmoke warm-startを含む）
- 常用漢字全数: 2,136 / 2,136完筆、平均beauty score 76.57、最低71.00
- 10パーセンタイル: 74.58
- 滴下: 0 / 2,136、衝突: 0 / 2,136
- SHA-256: `8114801053271982fadaec5aaf2bd3c2f2a1aefb2582bb9781ad4e93d07d9d13`
- 詳細: `docs/results/2026-08-15-image-exemplar-ppo.md`

モデルはDLS基準制御への6関節残差を出力します。`--professional`が含墨・墨落とし・
画像観測・筆物理をまとめて有効にするため、再生時に必ず指定してください。

## 線質・基本筆法モデル（現行環境）

`beauty-techniques-ppo.zip`は、42次元観測の現行環境で、とめ・はね・はらい、折れ、横画、縦画、点を学習したStable-Baselines3 PPOモデルです。KanjiVGの中心線・筆順・画種と、AnimCJKの日本語楷書アウトラインから得た線幅を教師にしています。

```bash
source .venv/bin/activate
mjpython -m so101_calligraphy.training.replay \
  models/beauty-techniques-ppo.zip --kanji 書 --ik-assist \
  --save-ink outputs/sho.png
```

検証値:

- 累積PPO step: 115,200
- 基本筆法: 7 / 7完筆、平均beauty score 75.13、最低67.63
- 未学習10字: 10 / 10完筆、平均64.53、最低53.38
- 教育漢字: 1,026 / 1,026完筆、平均65.83、最低44.40、衝突0
- ドメインランダム化評価: 70 / 70完筆、平均74.90、最低66.34
- SHA-256: `584d211f2a5cb0d1881e58b880e304413a75fb0a52cd03fef47d6df0ae373132`
- 報酬推移: `beauty-techniques-reward-curve.png`
- 評価値: `beauty-techniques-evaluation.json`

このモデルはDLS基準制御への6関節残差を出力するため、再生時は`--ik-assist`を指定してください。beauty scoreは形状、線幅、筆圧、速度、収筆、配置を合わせた工学的評価で、人間の審美評価ではありません。

## 教育漢字モデル（旧点接触環境）

`education-kanji-ppo.zip`は旧20次元・点接触環境で、小学校1〜6年の教育漢字1,026字を完筆した履歴モデルです。現行の42次元環境とは互換性がありません。再現にはcommit `216ebdb`を別worktreeへ展開してください。

```bash
git worktree add ../syodo-v01 216ebdb
cd ../syodo-v01
source .venv/bin/activate
mjpython -m so101_calligraphy.training.replay \
  models/education-kanji-ppo.zip --kanji 書 --ik-assist
```

旧モデルの検証値:

- 累積PPO step: 5,433,344
- 完筆: 1,026 / 1,026
- 衝突: 0 / 1,026
- SHA-256: `f3a2dde52b81e7ab2e3eea14feca93e5f6e06bf0b4ad091c363535038fc0b736`

各モデルの学習データに関する帰属・配布条件は[THIRD_PARTY.md](../THIRD_PARTY.md)を参照してください。
