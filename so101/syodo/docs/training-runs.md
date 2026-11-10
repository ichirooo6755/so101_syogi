# 学習実行台帳

いまの作業本体は実機書字（[`docs/hardware-open.md`](hardware-open.md)）。ここはシミュ PPO の台帳。
用語と全体フローは [glossary-and-training-process.md](glossary-and-training-process.md)。
機械可読な全引数は各出力先の `run.json`、段階計画は `schedule.json`、進捗は `progress.json`。

## `hardware-12-8-4`（再設計・未起動、2026-09-08）

- 目的: 把持→毛先12 cm＝筆軸8 cm＋穂4 cmと傾斜アタッチメントに合わせる。旧`hardware-12cm`の「穂12 cm」前提は破棄
- CLI候補: `so101-train-professional --desk data/hardware/desk.json`（全長と穂長を別々に載せる。半紙FKは未使用）
- desk は `ready=true`（2026-09-01）。四隅 z 幅 1.2 mm、定規の実測 155 mm に対し FK 153.9 mm。詳細 [`docs/hardware-open.md`](hardware-open.md)
- 未起動の理由: 実機12/8/4 cm構成での試し書きと物性同定を先に行う
- シーン: 半紙 縦置き 333×242 mm、土台と紙は同じ机（学習用 A4 の 150 mm 台座は使わない）
- Cゲートは3.8 cm穂の採択モデルのまま。実機の穂4 cmは近いが、8 cm剛体軸と物性同定を含む評価が終わるまでcanonicalにしない
- 親候補: `runs/kaisho-yohitsu-sansetsu/final_model.zip`（起動時に SHA を書く）
- 追跡: [#14](https://github.com/ichirooo6755/syodo/issues/14)

## `kaisho-yohitsu-brush-tilt-a4-tip-relaxed-r1`（期限切れ・非canonical、2026-08-30）

- 目的: strictと診断専用`relaxed-recovery`を変更せず、同じ実測閾値にr1権限だけを与えた
  `relaxed-r1`でWindows CUDA再学習を実行する
- 親: `runs/kaisho-yohitsu-brushmark-joyo/08-joyo/model.zip`、SHA-256
  `afaf3ae1e747c2138ed40de497872b5fb3036656210c691574c12c1589119f14`
- Gate 3: 128字×6配置=768件、完筆675、衝突0、穴629、beauty 74.843201。
  `ready_for_r1=true` / `canonical_eligible=false`
- 較正: `calibration=null`。Gate証跡と学習commandを同じ未較正条件に固定
- 実装: `b941b3b`、detached workerのimport修正: `404a08b`、実行SHA: `b6b4135`
- テスト: focused PASS、全pytest **268/268 PASS**
- Windows: RTX 4060 Ti 8 GiB、PyTorch 2.13.0+cu130、CUDA利用可能、24 CPU。
  2026-08-30 04:21 JST開始、launcher PID 41564、worker PID 42808、chunk 1 child PID 21736
- 学習: stage 8、`n_envs=8`、BC 180k（worker 4）、PPO 250k×最大10 chunk、lr 1e-4、clip 0.1、
  target KL 0.03。各chunk後Gate 1 screen、2 checkpoint連続非改善で停止
- deadline: 2026-09-01 04:15 JST（48時間上限）
- Windows出力: `C:\syodo-relaxed-r1\runs\kaisho-yohitsu-brush-tilt-a4-tip-relaxed-r1\`
- Gate証跡: `runs/brush-tilt-gate-recovery-relaxed-r1-20260830/gate3/gate3-evidence.json`
- Windows開始スナップショット: `runs/brush-tilt-gate-recovery-relaxed-r1-20260830/windows-start/`
- 完全結果: [`docs/results/2026-08-30-relaxed-r1-start.md`](results/2026-08-30-relaxed-r1-start.md)
- canonicalモデル、既存strict run、12,816件canonical評価は変更・起動しない

## `brush-tilt-gate-recovery-v2-20260829`（完了・Gate 1未達で停止）

- 目的: 既存閾値を固定したまま、圧力schema v2・安全制御・Gate 1〜3回復とWindows r1の
  起動条件を実装し、最良候補を採択判定する
- 親: canonical `runs/kaisho-yohitsu-sansetsu/final_model.zip`（変更なし）
- 較正: 7点open-loop probe 420評価（一三十目書飛×6 fit、鬱誠砕案×6 held-out）から
  schema v2の12曲線を生成。calibration SHA-256
  `73ecc23f8c7af57d7b1097df368551185b6f484a1322408cca8f33313d244769`
- 探索: gap `1.5/2.0/2.5 mm` × floor `0.35/0.45` × motion `0.72/0.85/1.00` の
  18候補を6 workerでscreen。全候補がGate 1未達で `selected=null`、`rl_candidate=null`
- 最良候補再評価（最新DLS修正）: 一三十×6、完筆 **17/18**、衝突/hard-limit **0**、
  穴 **0**、beauty **70.957650**、endpoint改善 **+6.612542**、runtime clip/fallback
  **0%/0%**。圧力・幅・完筆・endpoint条件未達で `passed=false` / `ready_for_cuda=false`
- 実行環境: Apple M1 Pro、8 CPU、16 GiB RAM、macOS、CPU。主要証跡JSONの `run` に完全CLI、
  git SHA、dirty状態、較正SHA、経過時間、採否を保存
- 起動停止: Gate 1未達のためGate 2/3、限定RL、Windows CUDA r1、12,816件canonical評価は
  起動しない。既存Gate 2/3診断とTask 7 smokeは履歴として保持
- 完全な結果: [`docs/results/2026-08-29-gate1-3-recovery-r1.md`](results/2026-08-29-gate1-3-recovery-r1.md)
- 成果物: `runs/brush-tilt-gate-recovery-v2-20260829/`
- screen CLI:

  ```bash
  env PYTHONPATH=src MPLBACKEND=Agg .venv/bin/python -u scripts/search_gate_recovery.py \
    --output runs/brush-tilt-gate-recovery-v2-20260829/search \
    --pressure-calibration runs/brush-tilt-gate-recovery-v2-20260829/pressure-calibration-v2.json \
    --workers 6 --hours 48
  ```

## `brush-tilt-gate-recovery-relaxed-20260829`（完了・診断上のGate 1〜3到達）

- 目的: strict閾値で回復不能だったため、ユーザー指定に従いstrictを変更せず明示的な
  `relaxed-recovery`プロファイルで同一候補をGate 1〜3まで連続診断する
- 親: `runs/kaisho-yohitsu-brushmark-joyo/08-joyo/model.zip`（canonical採択モデルは変更なし）
- 候補: `minimum_gap=0.0015`、`clearance_floor=0.35`、`exemplar_motion_strength=0.72`
- Gate 1: 18件、完筆17、衝突0、穴0、beauty 69.916535、endpoint改善+1.324365、relaxed PASS
- Gate 2: 60件、完筆56、衝突0、穴56、beauty 73.731144、relaxed PASS
- Gate 3: 768件（128字×6配置、8 shard）、完筆675、衝突0、穴629、beauty 74.843201、relaxed PASS
- 圧力/幅の実測範囲: 圧力p90最大0.775343、幅比中央値0.642834〜3.988472。Gate 3再採点は
  `--reuse-shards`で原本を再利用し、再シミュレーションを行っていない
- 較正: `calibration=null`（clip/fallbackは0%/0%）。較正原本は別runに保持し採択していない
- `ready_for_cuda=false` / `ready_for_r1=false`。安全負債を含む診断結果であり、Windows r1、
  限定RL、12,816件canonical評価は未起動
- 完全結果: [`docs/results/2026-08-29-gate1-3-relaxed-recovery.md`](results/2026-08-29-gate1-3-relaxed-recovery.md)
- 成果物: `runs/brush-tilt-gate-recovery-relaxed-20260829/`


## `a4-tip-cuda-recovery`（PLAN.md、2026-08-25）

- 計画: [`docs/plans/2026-08-22-a4-tip-cuda-recovery-design.md`](plans/2026-08-22-a4-tip-cuda-recovery-design.md) / 固定45°: [`docs/plans/2026-08-27-fixed-45-pressure-recovery.md`](plans/2026-08-27-fixed-45-pressure-recovery.md)
- 親: `runs/kaisho-yohitsu-brushmark-joyo/08-joyo/model.zip`（Mac/Windows 配置済み）
- 起動条件: `runs/kaisho-yohitsu-brush-tilt-a4-tip-calibration/selected.json` の `ready_for_cuda`
- 既存 `kaisho-yohitsu-brush-tilt-a4-tip-r1` は上書きしない（完了・不採択）
- 較正 2026-08-26: 完筆 60/60。未達は圧・幅・布白 76>14・端点 +1.0（要 +10）。`ready_for_cuda=false` → **CUDA 未起動**
- 再測: `runs/kaisho-yohitsu-brush-tilt-a4-tip-calibration-20260826/selected-diagnostic.json`
- 2026-08-27 夕: 6 軸 expert は完筆 **60/60**・衝突 0・beauty **72.96**・穴 41。サーボ固定互換は 45/60 で CUDA 教師にしない。Windows Tailscale 無応答のため **CUDA 未起動**。JSON: `runs/kaisho-yohitsu-brush-tilt-a4-tip-calibration/dynamic-actual-tip-10x6.json`。Issue [#13](https://github.com/ichirooo6755/syodo/issues/13)
- 2026-08-27: 穂先が遠いときは 30° 起筆を要求しない（live のみ）。完筆 **60/60**、beauty **72.96**。直立 60 の端点平均 20.11、動的は 19.90（**+0.3**、要 +10）。未達は圧・幅・布白 41>14。layout 圧・停滞 Z・送筆滞留のいじりは完筆か布白を壊して不採用。CUDA 未起動。`--upright` は `large_frame_entry_lean` と `airborne_lean` も 0。Issue [#13](https://github.com/ichirooo6755/syodo/issues/13)
- 2026-08-27 夜 **固定45°スクリーン**: 一三十×6 で完筆 **18/18**・衝突 0・穴 0・端点 **+10.49**（直立比、PASS）。未達は圧・幅のみ。layout 0 は固定30°（45°は arm-floor）。`tip_pressure_scale=0.45`。beauty 平均 69.8。全60・CUDA 未起動。JSON: `runs/kaisho-yohitsu-brush-tilt-a4-tip-calibration-20260827-fastfix/screen-fixed45-L0-30-20260827e.json` / `selected-fixed45-screen.json`。Issue [#13](https://github.com/ichirooo6755/syodo/issues/13)
- 2026-08-27 深夜 **単調圧力逆モデル＋feedforward統合**: versioned 較正 JSON/schema、PAVA 単調化、CalligraphyEnv feedforward 統合、fit CLI を実装・単体テスト全通過。Gate 1 (18ケース) 評価で完筆 18/18 (100%)・衝突0・穴0・端点 +10.49。一部配置の圧/幅残差のため `ready_for_cuda=false`、Windows Tailscale offline のため **CUDA 未起動**。報告書: [`docs/results/2026-08-27-brush-tilt-best-recovery.md`](results/2026-08-27-brush-tilt-best-recovery.md)
- 2026-08-27 完了監査 **厳格Gate再実行**: Task 1〜6と208テストを完了。未較正Gate 1は18/18、衝突0、穴0、端点+10.4876だが、圧・幅および丸め前beauty **69.77388023324927 <= 69.8**でFAIL。明示依頼によりGate 2（60件）とGate 3（768件）の診断も実施したが、いずれもFAIL。CUDA・12,816件評価は未起動。出力: `runs/brush-tilt-best-recovery-20260827-task-completion/`。

## `calligrapher-prep`（A/B、2026-08-25）

- 目的: 書家レベル（sansetsu 84.96 / 完筆 100%）へ戻す次の学習条件を、Codex 流の 9×60 総当たりなしで決める
- 方法: Mac 上の `scripts/diagnose_stroke_merge.py` expert-only。Windows 全数評価は触っていない
- 結果: layout-0 は 10/10 完筆だが beauty 約 72。ホバー修正後は代表 10 字×6 枠が **完筆 60/60**。圧・幅・布白・端点は未達。60 mm へ戻すと現行圧では悪化。台座 x 変更は枠同士がトレードオフ
- 出力: `runs/calligrapher-prep-2026-08-25/summary.json`
- 次の CUDA: 物理ゲート通過まで起動しない。未完筆 hard-mining も起動しない
- Issue: [#13](https://github.com/ichirooo6755/syodo/issues/13)

## `brush-tilt-a4-tip`（学習中、2026-08-25〜、打ち切りなし）

- 目的: 実機傾斜アタッチメント＋A4 85/110 mm 枠で、過去最高に近い beauty を回復する
- 親モデル: `runs/kaisho-yohitsu-shapefit-cont/final_model.zip`（Windows 上。sansetsu は採択のまま保護）
- 変更: CUDA PPO、`n_envs=8`、`require-subproc`、stage 8 から再適応。物理ゲート未達のため A4 較正 JSON は起動条件にしない
- 開始: 2026-08-25 未明 JST、Windows RTX 4060 Ti。2026-08-25 04:20 JST に締切を外して再開（r1 `final_model.zip` から全数 12,816 行 eval）
- 進捗: 2026-08-25 13:14 JST 時点で 8 シャードとも 900/1602（56%）。ETA 今夜 20–21 時、遅ければ 22–23 時
- 出力: `runs/kaisho-yohitsu-brush-tilt-a4-tip-r1`。評価後の自動 r2 はウォッチャで停止（採択しない）
- 起動: `scripts/spawn_windows_recovery.py`（`--deadline` 省略）
- Issue: [#13](https://github.com/ichirooo6755/syodo/issues/13)

## `brush-tilt-physical-r1`（完了・不採択、2026-08-23）

- 全数: beauty 82.80 / 完筆 97.3% / C ゲート未達。canonical は置換していない

## `brush-tilt`（完了・不採択、2026-08-22）

- 目的: 傾斜 EE + 起筆 `entry_lean=1.0` を sansetsu に載せる。C ゲート非退行
- 親モデル: `runs/kaisho-yohitsu-sansetsu/final_model.zip`
- 128字: beauty 68.89、完筆 54.7%。以降 r2/r3 も退行
- 起動: `scripts/spawn_windows_train.py`
- Issue: [#13](https://github.com/ichirooo6755/syodo/issues/13)

## `sansetsu`（完了・採択・現ベスト、2026-08-20）

- 目的: 三折法（トン・スー・トン）を方策に載せる。筆圧追従強化 + 起筆沈み込み
- 親モデル: `runs/kaisho-yohitsu-stroke-separation/final_model.zip`
- 非退行基準: `runs/kaisho-yohitsu-stroke-separation-joyo-eval/`
- 変更: `contact_pressure_gain=0.015` / `limit=0.0040`、`entry_descent_ratio=0.55`、技法別ゲイン 払い×1.6 / はね×0.20
- 開始: 2026-08-20 02:04 JST、stage 5–8、1.3M/stage、hard-mining なし
- 全数 eval: 2026-08-20 06:08 JST 完了（2136字）
- 結果（全2136字）: beauty **84.96** / lw **88.29** / bw **82.97** / harai **71.39** / glyph **59.03** / 字単位 **100%**
- 非退行（stroke-separation 比）: beauty +1.38 / lw +6.07 / glyph +1.72 / 字単位 99.72→100% → **採択**
- **C ゲート全項目通過**（harai ≥65、完筆 100%、字単位 100%）
- 出力: `runs/kaisho-yohitsu-sansetsu` / 全数 `runs/kaisho-yohitsu-sansetsu-joyo-eval`
- 起動: `scripts/run_sansetsu_overnight.sh`
- 診断: [`docs/results/2026-08-20-sansetsu-diagnosis.md`](../docs/results/2026-08-20-sansetsu-diagnosis.md)
- CS: [`docs/results/2026-08-20-sansetsu-contact-sheet.png`](../docs/results/2026-08-20-sansetsu-contact-sheet.png)
- Issue: [#7](https://github.com/ichirooo6755/syodo/issues/7)

## `stroke-separation`（完了・採択、2026-08-20）

- 目的: 線幅較正（`tuft_opening=1.34`）と画間クリアランスで太さ・癒着を改善
- 親モデル: `runs/kaisho-yohitsu-harai-finish/final_model.zip`
- 非退行基準: `runs/kaisho-yohitsu-harai-finish-joyo-eval/`
- 変更: `BrushConfig.tuft_opening=1.34`、`stroke_minimum_gap=0.0015`、`stroke_clearance_floor=0.45`
- 開始: 2026-08-19 22:30 JST、stage 5–8、1.3M/stage、hard-mining なし
- 全数 eval: 2026-08-20 02:01 JST 完了（2136字）
- 結果（全2136字）: beauty **83.58** / lw **82.22** / bw **81.76** / harai **75.03** / glyph 57.31 / 字単位 99.72%
- 非退行（harai-finish 比）: lw +3.85 / bw +4.17 / harai +12.55 / 完筆 100% → **採択**（harai finish 65 ゲート初通過）
- 出力: `runs/kaisho-yohitsu-stroke-separation` / 全数 `runs/kaisho-yohitsu-stroke-separation-joyo-eval`
- 起動: `scripts/run_stroke_separation_overnight.sh`
- 記録: [`docs/results/2026-08-19-stroke-width-and-separation.md`](../docs/results/2026-08-19-stroke-width-and-separation.md)
- Issue: [#7](https://github.com/ichirooo6755/syodo/issues/7)

## `harai-finish`（完了・採択、2026-08-19）

- 目的: 払い finish ≥65 と完筆 100%。報酬を評価指標に揃え、持ち上げ余力を IK A/B で拡大
- 親モデル: `runs/kaisho-yohitsu-contact-fix/final_model.zip`
- 非退行基準: `runs/kaisho-yohitsu-contact-fix-joyo-eval/`
- 変更: `command_limit_margin=0.005`、`harai_finish_release`（幅/圧/速、許容 0.065）、`contact_pressure_limit=0.0035`
- 開始: 2026-08-19 11:31 JST、stage 5–8、2.2M/stage、hard-mining なし
- PPO 完了: 2026-08-19 18:53 JST（7h 21m）
- 全数 eval: 2026-08-19 21:00 JST 完了（2136字）
- 結果（全2136字）: beauty **82.54** / lw **78.38** / bw **77.59** / harai **62.48** / 完筆 **✅ all_complete**
- 非退行（contact-fix 比）: lw +12.3 / bw +10.1 / 完筆 ❌→✅ → **採択**
- harai finish: 62.0→62.48（目標 ≥65 は未達。PPO が IK 天井 65.5 に追いつかず）
- 出力: `runs/kaisho-yohitsu-harai-finish` / 全数 `runs/kaisho-yohitsu-harai-finish-joyo-eval`
- 起動: `scripts/run_harai_finish_overnight.sh`
- IK A/B: `runs/ab-harai-ik-ceiling.json`（plimit0035 採択、clearance は hane 低下で不採択）
- CS: [`docs/results/2026-08-19-harai-finish-contact-sheet.png`](../docs/results/2026-08-19-harai-finish-contact-sheet.png)
- Issue: [#7](https://github.com/ichirooo6755/syodo/issues/7)

## `contact-fix`（完了・現ベスト、2026-08-19）

- 目的: 接地筆圧フィードバック導入後の広い再適応（hard-mining なし）
- 親モデル: `runs/kaisho-yohitsu-visual-ab/final_model.zip`
- お手本: Morisawa KaishoMCBK1
- 開始: 2026-08-18 23:57 JST、PPO 完了 05:09、全数 eval 05:37
- 変更: `EnvConfig.contact_pressure_gain=0.0050` / `limit=0.0015`、stage 5–8
- 結果（全2136字）: beauty **83.5** / lw **85.5** / bw **76.8** / harai **62.0** / 字単位 **99.91%**
- 非退行: visual-ab Morisawa 比で lw +12.6 / bw +10.6 / 字単位 +16.3 → **採択**
- 出力: `runs/kaisho-yohitsu-contact-fix` / `runs/kaisho-yohitsu-contact-fix-joyo-eval`
- 記録: [`docs/results/2026-08-19-contact-pressure-fix.md`](results/2026-08-19-contact-pressure-fix.md)
- コード後追記: 技法別ゲイン（harai×1.4、hane蓄力×0.35）。抜きランプは不採択
- Issue: [#7](https://github.com/ichirooo6755/syodo/issues/7)

## `visual-ab`（完了・見た目A/B本番）

- 目的: 実験A（墨 hard-edge）+ 実験B（美観重み・IoUログ）を本番に入れ、C-r1 から短い再学習
- 親モデル: `runs/kaisho-yohitsu-c-r1/final_model.zip`
- 完了: 2026-08-17 ~17:01 JST（PPO 40万、約23分）
- 結果（全2136字）: beauty **76.9** / lw **75.4** / bw **66.9** / 払い **55.4** / 字単位 lw+bw 両方 **85.6%**（要95%）→ C未達
- IoU 平均 **38.2**（ログ用）
- 出力: `runs/kaisho-yohitsu-visual-ab` / `runs/kaisho-yohitsu-visual-ab-joyo-eval`
- contact sheet: `docs/results/2026-08-17-visual-ab-contact-sheet.png`
- 比較: `docs/results/2026-08-17-ink-stamp-edge-compare.png`, `docs/results/2026-08-17-beauty-weights-compare.png`
- Issue: [#7](https://github.com/ichirooo6755/syodo/issues/7)

## `overnight`（実行中・2026-08-18 08:00 まで）

- 目的: c-loop r4 終了後も hard-mining を夜通し（r5, r6, …）
- 親モデル: 各ラウンド開始時に **字単位 lw+bw 合格率が最高** の eval から自動選択（visual-ab 85.6% 等）
- 締切: `2026-08-18 08:00 JST`（残り時間が ~2.5h 未満なら新ラウンドを開始しない）
- ログ: `runs/overnight-train.log` / PID `runs/overnight.pid`
- 起動: `scripts/run_overnight_until.sh`（`caffeinate -dims`。蓋閉じは不可）

## `c-loop`（r4 実行中 → 夜通しに引継ぎ）

- 経路: **C（機械）→ A（目視）**。B（書家レビュー）は後段オプション
- 目的: 字単位 lw/bw≥95% と払い収筆≥65 を満たすまで hard-mining を最大4ラウンド
- 開始: 2026-08-17 14:22 JST
- 親モデル: `runs/kaisho-yohitsu-5x-hard-max/final_model.zip`
- 入力CSV: `runs/kaisho-yohitsu-5x-joyo-eval-max/characters.csv`（未達802字＋回帰セット）
- 各ラウンド: PPO 250万 / BC 18万×5 / `n_envs=7` / `mps`
- 出力: `runs/kaisho-yohitsu-c-rN` → `runs/kaisho-yohitsu-c-rN-joyo-eval`
- ログ: `runs/c-loop-train.log` / PID `runs/c-loop.pid`

## `kaisho-yohitsu-5x-hard-max`（完了・高負荷）

- 目的: 常用未達字を **n_envs=7 / n_steps=4096 / PPO 200万** で叩き、Cへ寄せる
- 結果（全2136字）: 美観79.9 / lw69.8 / bw63.5。字単位両方合格62.5%（要95%）、払い56.9（要65）→ C未達
- 出力: `runs/kaisho-yohitsu-5x-hard-max` / `runs/kaisho-yohitsu-5x-joyo-eval-max`

## `parallel-benchmark`（完了・2026-08-17）

- 目的: 16GB Mac で安定する学習並列度を決める
- 結果: 学習既定 `n_envs=6` / `device=mps` / `bc-workers<=6`。監視上限7。学習で8以上は不可（BC BrokenProcessPool）
- 成果物: `runs/parallel-benchmark/benchmark.json`、`recommended.env`、`README.md`
- メモ: [docs/parallelism-notes.md](parallelism-notes.md)
- 補足: フル professional セルはメモリ逼迫で未完走。`benchmark_subproc_scaling.py` + 本番観測で確定

## `kaisho-yohitsu-5x-hard-hi`（待機/実行中・書家レベル C）

- 目的: 全数評価で lw/bw/払い未達の字を hard-mining し、機械合格（C）へ近づける。最終の書家レベル宣言はユーザー目視（A）
- 設計: `docs/plans/2026-08-16-calligrapher-level-c-to-a-design.md`
- 並列: ベンチ推奨どおり `n_envs=6` / `mps` / `bc-workers=6`（メモリ空き待ち後に起動）
- 親モデル: `runs/kaisho-yohitsu-5x/final_model.zip`
- hard CSV: `runs/kaisho-yohitsu-5x-joyo-eval/characters.csv`
- 出力: `runs/kaisho-yohitsu-5x-hard-hi` → 再評価 `runs/kaisho-yohitsu-5x-joyo-eval-r2`
- ログ: `runs/kaisho-yohitsu-5x-hard-hi-train.log`

## `kaisho-yohitsu-5x-hard`（中断・n_envs=6 初回）

- 開始: 2026-08-16 17:32 JST。ディスク逼迫で途中停止。`hard-hi` へ移行

## `post-5x-continue`（一部完了・方針修正）

- 全数評価は完了（2,136字）。旧 acceptance が美観だけで通したため hard-mining を誤スキップ → 厳格ゲートへ修正し本項の hard ランへ切替
- 出力: `runs/kaisho-yohitsu-5x-joyo-eval/`

## `kaisho-yohitsu-5x`（完了）

- 目的: 線幅目標修正版の最終モデルから、払い収筆・運筆を強化して常用漢字まで5倍規模で継続学習
- 開始: 2026-08-16 08:33 JST（途中 Cursor 再起動で elementary から再開、13:24 JST）
- 完了: 2026-08-16 16:06 JST 前後（最終評価）
- 親モデル: 当初 `runs/kaisho-yohitsu-5h/final_model.zip`／再開時 `runs/kaisho-yohitsu-5x/resume_elementary.zip`
- 出力: `runs/kaisho-yohitsu-5x`
- ログ: `runs/kaisho-yohitsu-5x-train.log` / `runs/kaisho-yohitsu-5x-detached.log`
- 並列: BC 6 process、PPO `SubprocVecEnv` 6 process
- 規模: 部首/教育/常用 各2,250,000 PPO step、仮名4,500,000 PPO step
- 最終96字: 美観78.27、line_width 62.44、brushwork 59.84、完筆96/96、滴下0、衝突0、ゲート2未達
- Issue: [#2 コメント](https://github.com/ichirooo6755/syodo/issues/2#issuecomment-5306393747)

```bash
source .venv/bin/activate
export PYTHONPATH=src PYTHONUNBUFFERED=1
so101-train-professional \
  --ablation all \
  --initial-model runs/kaisho-yohitsu-5h/final_model.zip \
  --start-stage 5 \
  --timesteps 2250000 --kana-timesteps 4500000 \
  --bc-steps 200000 --kana-bc-steps 400000 --bc-epochs 5 \
  --n-envs 6 --bc-workers 6 --n-steps 2048 --batch-size 768 \
  --device mps --allow-gate-failure \
  --stage-eval-size 48 --eval-limit 96 \
  --output runs/kaisho-yohitsu-5x \
  --seed 23 \
  2>&1 | tee runs/kaisho-yohitsu-5x-train.log
```

## `kaisho-yohitsu-5h`（完了）

- 目的: 修正した用筆目標幅で、部首・仮名・教育漢字・常用漢字へ継続学習
- 親モデル: `runs/kaisho-yohitsu-all-long/final_model.zip`
- 出力: `runs/kaisho-yohitsu-5h`
- 結果: 96/96完筆、美観78.98、線幅68.45、運筆57.67、滴下0、衝突0

```bash
PYTHONPATH=src so101-train-professional \
  --ablation all \
  --initial-model runs/kaisho-yohitsu-all-long/final_model.zip \
  --start-stage 5 \
  --timesteps 450000 --kana-timesteps 900000 \
  --bc-steps 40000 --kana-bc-steps 80000 --bc-epochs 5 \
  --n-envs 10 --n-steps 1024 --batch-size 512 \
  --device mps --allow-gate-failure \
  --stage-eval-size 48 --eval-limit 96 \
  --output runs/kaisho-yohitsu-5h \
  --seed 17
```

## `kaisho-yohitsu-all-long`（完了・線幅不整合版）

- 目的: 画像教師・仮名を含む長時間カリキュラムの初回検証
- 結果: 96/96完筆だが、目標幅が実墨フットプリントの約半分で `line_width≈0.9` に崩壊
- 判断: モデルは `kaisho-yohitsu-5h` のwarm-startにのみ使用し、品質基準モデルにはしない

## 2026-08-27 brush-tilt-best-recovery Gate 1〜3診断

- 親モデル: `runs/kaisho-yohitsu-sansetsu/final_model.zip`（canonical bestを保持）
- 設定: 未較正、固定45°（layout 0のみ30°）、`tip_pressure_scale=0.45`、6配置
- Gate 1: 18/18完筆、消失布白0、端点改善+10.4876、beauty 69.77388023324927。圧力・幅・厳密beauty未達でFAIL。
- Gate 2: 60/60完筆、消失布白41、beauty 73.51234259823465。負空間・圧力・幅・beauty未達でFAIL。
- Gate 3: 768/768評価、754/768完筆、消失布白473、beauty 74.58946245601119。完筆・安全性・負空間・圧力・幅未達でFAIL。
- 出力: `runs/brush-tilt-best-recovery-20260827-task-completion/gate{1,2,3}-*`（Gate 3は8シャードを統合）
- 判定: すべて `ready_for_cuda=false`。CUDA再学習・12,816件評価は未起動。Gate 3の診断継続は明示依頼による。

## 2026-08-28 Windows 非採択 Gate 1 smoke（Task 7 step 7）

- 実行環境: `DESKTOP-NT5T7N1` / RTX 4060 Ti 8GB / 24 logical CPU、隔離worktree `C:\syodo-codex-smoke-2bb46c0`、commit `2bb46c0`。
- 内容: stage 8 joyo、親 `kaisho-yohitsu-brushmark-joyo/08-joyo/model.zip`、BC 20,000 step + PPO 200,000 step、`n_envs=8`、`--device cuda`、seed 121。Gate失敗を許容する非採択実験。
- 結果: Gate 1 18件、完筆17/18、消失布白0、beauty **63.704647**、endpoint改善 **+5.863549**、衝突/ハードリミットゲートFAIL、圧力/幅FAIL、calibration clip **12.03%**・fallback **30.59%**。`passed=false` / `ready_for_cuda=false`。
- 比較: 同一smokeモデルのupright基準は17/18、beauty **64.326149**、endpoint基準。従来未較正Gate 1（18/18、beauty 69.773880、endpoint +10.487598）を下回ったため、継続学習・本番採択は停止。
- 成果物: `runs/brush-tilt-best-recovery-20260827-task-completion/gate1-smoke-200k-r1.json`、`gate1-smoke-200k-r1-upright.json`。Windows側の学習モデルは `runs/kaisho-yohitsu-brush-tilt-a4-tip-smoke-200k-r1/08-joyo/model.zip`。

## 記録規約

今後の全runは次を必須とします。

1. 作業目的と仮説
2. 完全なCLI
3. 親モデル・seed・git commit・dirty状態
4. CPU/RAM/OSと並列設定
5. 出力先、ログ、開始/終了時刻
6. 全体・最低・p10と線幅/運筆/安全性
7. 採用・不採用理由と次の作業
