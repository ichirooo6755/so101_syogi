# 筆傾斜アタッチメント過去最高回復 実装計画

## 前提

- 設計: `docs/plans/2026-08-27-brush-tilt-best-recovery-design.md`
- 親モデル: `runs/kaisho-yohitsu-brushmark-joyo/08-joyo/model.zip`
- 最終条件: 2,136字×6配置、平均beauty > 86.27775324466442、
  p10 >= 83.78582694425683、完筆100%、Cゲート全通過、滴下・予定外接触0。
- ユーザーの未コミット変更 `.vscode/extensions.json`、既存run、採択済みモデルは
  変更しない。

## Task 1: versioned圧力逆モデル

**Files**

- Create: `src/so101_calligraphy/pressure_calibration.py`
- Create: `tests/test_pressure_calibration.py`

**Steps**

1. 失敗する単体テストを追加する。
   - schema version、CAD/brush fingerprint、layout class、角度、phase、圧力ノットを
     必須にする。
   - ノットの有限性、圧力昇順、Zオフセット単調性、同数配列、Z上限を検証する。
   - 区分線形補間、範囲外clip、未観測カテゴリの明示的fallbackを検証する。
   - JSONの保存・読込往復を検証する。
2. `PressureCalibration`, `PressureCurve`, `PressureLookup` を不変dataclassで実装する。
3. pool-adjacent-violatorsによる重み付き単調化を純粋関数で実装する。
4. `lookup()` は `offset`, `clipped`, `fallback` を返し、黙った最近傍カテゴリ補間を
   行わない。
5. 対象テストを実行する。

## Task 2: 環境へfeedforward＋残差積分を統合

**Files**

- Modify: `src/so101_calligraphy/config.py`
- Modify: `src/so101_calligraphy/envs/calligraphy_env.py`
- Modify: `src/so101_calligraphy/training/professional.py`
- Modify: `tests/test_a4_tip.py`
- Modify: `tests/test_env.py`

**Steps**

1. `EnvConfig`へ較正JSONパス、較正必須フラグ、残差積分倍率、clip率上限を追加する。
   既定値は無効とし、旧runを再現する。
2. 環境初期化時に較正を一度だけ読込み、CAD/brush fingerprintを検証する。必須指定で
   欠損・不一致なら即時エラーにする。
3. 現在のlayout class、`_desired_brush_axis()`から得た実角度、brushwork phase、
   補間済み目標圧をlookupへ渡す。
4. `_contact_pressure_offset` をfeedforward基準値と残差積分値に分離する。最終Z補正は
   両者の和を物理travelへclipした値とする。
5. 接触喪失中は残差をリークしてゼロへ戻す。再接地は既存`_touchdown_error_scale()`で
   soft-startする。旧モードでは従来式と同じ値を返す。
6. stroke recordとinfoへfeedforward、residual、clip、fallbackを追加する。
7. 固定角対象、第6軸無効化、停滞回復、到達判定の既存テストを維持する。
8. 対象テストを実行する。

## Task 3: 較正サンプルの記録と単調テーブル生成

**Files**

- Modify: `scripts/diagnose_stroke_merge.py`
- Create: `scripts/fit_pressure_calibration.py`
- Create: `tests/test_pressure_calibration_cli.py`

**Steps**

1. 診断JSONへ各サンプルのlayout class、実角度、phase、目標圧、実圧、Zオフセット、
   接触力、実幅、目標幅、opening、XY/Z誤差、dwell、接触有無を保存する。
2. fitting CLIのテストfixtureを作り、過渡、失接触、衝突、XY誤差過大、非有限値が
   除外されることを確認する。
3. layout class×角度×phase×圧力binで、目標圧到達に必要なZをロバスト中央値で
   集約する。サンプル数を重みにして単調化する。
4. leave-one-character、leave-one-layoutの検証誤差、clip率、fallback率をJSONへ保存する。
5. git SHA、生成CLI、元診断ファイルSHA-256、設定fingerprintをprovenanceへ保存する。
6. ソースや既存runを自動変更せず、指定出力にcandidate JSONだけを書く。
7. 対象テストを実行する。

## Task 4: 物理ゲート選定の厳格化

**Files**

- Modify: `scripts/calibrate_a4_tip.py`
- Modify: `scripts/diagnose_stroke_merge.py`
- Modify: `tests/test_a4_tip.py`
- Create or Modify: `tests/test_pressure_calibration_cli.py`

**Steps**

1. Gate 1を各ケース単位で判定する。
   - 18/18完筆、衝突・hard-limit 0、消失布白0。
   - 端点改善+10以上。
   - 全ケースで圧median<=0.08、p90<=0.18、幅比0.90..1.10。
   - beauty平均が69.8より高い。
2. Gate 2を60ケースで判定する。
   - 60/60完筆、衝突・hard-limit 0。
   - 全ケースで圧・幅合格、消失布白<=14、opening p90<=1.12。
   - expert beauty>=85。
3. `selected.json`へgate version、較正JSON、fallback/clip率、評価件数を保存する。
4. 18ケースのselectedを60ケースのCUDA許可として誤用できないよう、
   `ready_for_cuda`はGate 2だけが設定可能にする。
5. dry-runで完全CLIを検証する。

## Task 5: 768ケース事前評価と12,816ケース最終評価

**Files**

- Modify: `scripts/evaluate_joyo_shards.py`
- Modify: `src/so101_calligraphy/training/professional.py`
- Modify: `tests/test_sharded_evaluation.py`

**Steps**

1. 既存の6配置評価を維持し、summaryへunique character count、layout別mean/p10、
   calibration provenance、fallback/clip集計を追加する。
2. `--eval-limit 128`が128字×6配置=768行になることをテストする。
3. full evalが2,136字×6配置=12,816行でなければmergeを失敗させる。
4. 同一文字・同一layoutの重複、欠損、不正layoutを既存検証で拒否する。
5. 単一配置の旧best補助評価を別出力へ保存し、6配置summaryへ混ぜない。

## Task 6: Windows CUDA回復ランの停止条件と採択条件

**Files**

- Modify: `scripts/spawn_windows_recovery.py`
- Modify: `tests/test_windows_recovery.py`

**Steps**

1. `PHYSICAL_GATE`はGate 2、60ケース、gate schema一致、較正fingerprint一致を必須にする。
2. 親ZIP、較正JSON、CUDA、空き容量をpreflightで必須にし、CPU fallbackを禁止する。
3. r1はstage 8、2.5M、lr=1e-4。r2/r3はstage 9、lr=7.5e-5/5e-5とする。
4. r1前に128字×6配置の親/設定smokeを実行し、完筆100%でなければ停止する。
5. 候補順位は `(C通過数, 完筆率, mean, p10, lw+bw+字単位合格率,
   endpoint, harai)` を維持する。
6. 最終回復判定は厳密にmean>86.27775324466442、p10>=83.78582694425683、
   12,816行、2,136字、6配置、全Cゲート、滴下・衝突0とする。
7. 2ラウンド連続で候補順位が改善しない場合に停止し、閾値を下げない。

## Task 7: 検証と段階実行

**Files**

- Modify after measurements: `docs/training-runs.md`
- Create after measurements: `docs/results/2026-08-27-brush-tilt-best-recovery.md`

**Steps**

1. `pytest -q tests/test_pressure_calibration.py tests/test_pressure_calibration_cli.py`
2. `pytest -q tests/test_a4_tip.py tests/test_env.py tests/test_brush_tilt.py`
3. `pytest -q tests/test_sharded_evaluation.py tests/test_windows_recovery.py`
4. `pytest -q` で全回帰を実行する。
5. 新規出力先でGate 1を実行し、失敗時は結果を記録してGate 2へ進まない。
6. Gate 1通過時だけGate 2、Gate 2通過時だけGate 3を実行する（本監査では明示依頼により、停止条件を解除せず診断目的でGate 2/3を継続実行）。
7. Gate 3通過かつWindows/CUDA利用可能時だけr1を起動する。
8. 各runに完全CLI、git SHA、dirty状態、較正SHA、環境、結果、採否を保存する。
9. 最終条件を満たした場合だけcanonical採択案を提示する。未達なら到達したゲートと
   次のボトルネックを正確に報告する。
