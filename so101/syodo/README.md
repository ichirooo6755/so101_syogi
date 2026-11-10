# SO-101 書道学習環境

Apple Silicon Mac上で、SO-101に取り付けた弾性筆でA4紙へ墨を転写する強化学習環境です。MuJoCo、Gymnasium、Stable-Baselines3のPPOを使い、CUDAとIsaac Simには依存しません。中心線だけでなく、筆圧、線幅、濃淡、かすれ、にじみ、筆のしなりと「とめ・はね・はらい」を学習対象にします。

## 書道GUI

`書道GUI.command` をダブルクリックすると、ローカルの操作画面が開きます。
「書く」「準備」「接続」の3画面で、文字・速さ、筆と紙・硯の較正、筆圧試験、
ESP32-S3のカメラ・ロードセル、バイラテラルへの切り替えを操作できます。
GUIは1〜2文字の実寸に対応し、紙と硯の位置検出は全ての目印が1枚に写る場合に利用できます。

新しい筆の初期値は **全長240 mm・穂42 mm**。制御に必要な **取り付け位置から毛先まで** は
現物を測って入力してください。GUI専用の較正は `data/hardware/gui/` に保存し、
従来の `data/hardware/desk.json` は保持します。[起動・操作手順](docs/gui.md)

展示や動画向けの説明は、[書道アームのキャプション集](docs/書道アーム_キャプション.md)にまとめています。

## いま（2026-09-09）

作業の本体は **実機で KanjiVG の1〜4文字を書く**。3〜4文字は右上→右下→左上→左下の2×2配置。実機の筆は把持位置から毛先まで12 cmで、内訳は筆軸8 cm＋穂4 cm。学習の採択モデルは3.8 cm穂の `kaisho-yohitsu-sansetsu`（機械Cゲート通過）で、実機の12/8/4 cm構成は未採択。

| 見るもの | 場所 |
| --- | --- |
| 実機の今 | [`docs/hardware-open.md`](docs/hardware-open.md) |
| 較正手順 | [`docs/hardware-calibration.md`](docs/hardware-calibration.md) |
| 四隅ロードセル | SC616C-1kg×4 / HX711×4 / Pico 2 W、200×300×2 mmアルミ板。`./scripts/force-plate`で表示・組立状態の較正・同期記録・書字分析。[手順](docs/hardware/force-plate.md)。実測較正・筆跡改善は未完了。 |
| 学習 run 台帳 | [`docs/training-runs.md`](docs/training-runs.md) |
| 過去の評価メモ | [`docs/results/`](docs/results/) |

書家レベルは **C（機械）→ A（目視）**。[#4](https://github.com/ichirooo6755/syodo/issues/4)

### 実機 SO-101

`desk.ready=true`。`data/hardware/desk.json` は git 対象外。実機の残り [#14](https://github.com/ichirooo6755/syodo/issues/14)。即書き [#15](https://github.com/ichirooo6755/syodo/issues/15) は完了。

較正の裏づけ: 定規の実測（下手左→下手右 155 mm）に対し FK 153.9 mm。四隅の z 幅 1.2 mm。

| 項目 | 現状 |
| --- | --- |
| 腕 | Follower `syodo_follower` `/dev/cu.usbmodem5B7B0136431`。Leader `syodo_leader` `/dev/cu.usbmodem5B7B0140931` |
| venv | 書道は repo の `.venv`。実機バスは `~/Documents/lerobot-hw/.venv` |
| 筆 | 実機は **全長12 cm＝筆軸8 cm＋穂4 cm**（把持位置から測る）。採択モデルの穂は3.8 cm |
| 机 | 半紙縦置き。実測書字領域 **267×154 mm**。土台と紙面は同じ高さ |
| 1字の桝 | 紙の15 mm余白内で最大の正方形（この机では約124 mm角） |
| 2字の桝 | 奥→手前の縦2段。約118 mm角。従来の110 mm上限を廃止 |
| 3〜4字の桝 | 2×2、右列から縦書き。約62 mm角。3文字では左下を空ける |
| 書字高さ | 奥+8→手前−12 mmの補正を目標位置に反映してから連続するIKを解く。最終指令で位置1 mm以内・筆傾き8°以内・隣接点5°以内・関節端2°以上を検証 |
| 画間 / 待機 | 紙面+60 mm / 紙面+100 mm（切断後もトルク維持） |
| 硯 | 墨池へ直行、手前 7 cm を 2 往復、ID5 を 90° 回して毛先を整える（穂先は IK で硯に残す）。最後の手前で待つ 3 秒は未実装 |
| 本書き | `./scripts/hw-write 春夏秋冬`。毎回 trace。KanjiVG にある1〜4文字なら可。到達できる寸法を検証して採用 |
| Leader 教示 | `record-word` が受け付けるのは `文字・学習・菅原` だけ |
| バイラテ | 起動時の差を保つ。先に `match-leader`。ID5 は指令しない |
| PPO | `--desk` はある。実機12/8/4 cm構成の採択評価は未実施 |

```bash
cd ~/Documents/syodo
./scripts/hw-write 文字
./scripts/hw-write 春夏秋冬 --prepare-only  # 4文字の配置・FK・筆先接触を確認
./scripts/hw-write 文字 --prepare-only  # 実機を動かさずFK検証と4 cm穂の動的再生を保存
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py match-leader
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py bilateral
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py stroke
```

`hw-write` は repo 直下から。既定 `--speed 1.5`、空中リハーサルと開始待機なし。カメラは `./scripts/hw-write 文字 --camera-url http://ESP32_IP`。

保存した指令を検証した `preflight.json` と、4 cmの穂を連続時間で曲げて再生した `brush-simulation/` を各runに残す。動的再生の物性値と墨幅は未実測なので、結果は診断値として扱う。
書字中は指令と読み戻し位置の差を記録する。[2026-09-08の修正・検証結果](docs/results/2026-09-08-open-issues.md)では指令FKの最大誤差を0.11 mm以下に改善した。修正後の紙上の仕上がりは未検証。

通信が切れたら 12V を切って 10 秒待ち、基板→1→…→5→6 を見て入れ直す。ID5 が消えやすい。

### シミュ採択 — `kaisho-yohitsu-sansetsu`

| 指標 | sansetsu | 目標 |
|---|---:|---:|
| beauty | **84.96** | ≥75 ✅ |
| line_width | **88.29** | ≥65 ✅ |
| brushwork | **82.97** | ≥62 ✅ |
| glyph_shape | **59.03** | ≥50 ✅ |
| harai finish | **71.39** | ≥65 ✅ |
| 完筆 | **100%** | 100% ✅ |
| 字単位 lw+bw | **100%** | ≥95% ✅ |

**現ベスト:** `runs/kaisho-yohitsu-sansetsu/final_model.zip`\
お手本: Morisawa KaishoMCBK1。全数 eval: `runs/kaisho-yohitsu-sansetsu-joyo-eval/`\
contact sheet: [`docs/results/2026-08-20-sansetsu-contact-sheet.png`](docs/results/2026-08-20-sansetsu-contact-sheet.png)

残課題（A 目視）: glyph_shape 59 / IoU ~54。[#17](https://github.com/ichirooo6755/syodo/issues/17)。傾斜機構と筆軸8 cm＋穂4 cmの実機同定は [#13](https://github.com/ichirooo6755/syodo/issues/13)、実機の残り（閉ループ筆圧・紙上確認）は [#14](https://github.com/ichirooo6755/syodo/issues/14)。

## 実装内容

- SO-101公式URDFの関節順、可動域、主要リンク長を反映した軽量MJCF
- 5つのアーム関節とグリッパ関節、合計6関節への位置目標増分
- A4紙面、硯と墨池、実機用8 cm剛体筆軸、6受動自由度を持つ4 cm・3分節の穂先
- MuJoCo接触力と圧縮量から求める筆圧、紙面摩擦
- 筆圧、穂先の開き、筆速、墨量、含水率、吸い込みから生成する可変幅の墨跡
- AnimCJKの日本字形から取得する筆画別の運筆中心線と高品質な線幅プロファイル
- SVG要素・サブパスを筆順として保持する等弧長サンプリング
- KanjiVGの実在筆画、部首階層、任意漢字を使う追加カリキュラム
- 画間の `上昇 → 空中移動 → 下降` を明示した3D目標列
- 「とめ・はね・はらい」別の起筆・送筆・収筆プロファイル
- 楷書8画種（横・縦・撇・捺・点・挑・折・鉤）ごとの押し引き・逆入・回鋒・転折の時間則
- 距離、筆圧、筆速、線幅、姿勢、正順進捗、滑らかさ、不要運動、pen-up、関節制限、衝突を含む報酬
- Chamfer距離、離散Fréchet距離、線幅、終筆、重心、傾き、余白による0〜100の説明可能な美しさ評価
- サーボ遅延、関節速度制限、摩擦・ゲイン・穂先剛性・墨水分のドメインランダム化
- PPOのカリキュラム学習、Monitor CSV、評価結果、チェックポイント、報酬グラフ
- 学習済みモデルをネイティブMuJoCo Viewerで再生

高精度モードでは、硯への下降、含墨、両方向の墨落とし、滴下を抑えた
搬送、起筆・送筆・収筆、必要時だけの再含墨までを一つのエピソードとして
扱います。旧物理との比較用に、筆物理、墨モデル、運筆補正は
`ModuleConfig`で独立して無効化できます。

モデルの関節値は[TheRobotStudioのSO-101 calibrated URDF](https://github.com/TheRobotStudio/SO-ARM100/blob/main/Simulation/SO101/so101_new_calib.urdf)を参照しています。STLメッシュは同梱せず、学習速度のため外形と衝突形状をプリミティブへ置き換えています。

## macOSセットアップ

推奨環境はApple Silicon、macOS、Python 3.11または3.12です。Python 3.13以降はPyTorch等の対応状況が変わりやすいため、このプロジェクトでは3.12までに制限しています。

HomebrewのPython 3.12を使う場合:

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
chflags -R nohidden .venv
```

最後の`chflags`は、Documents配下のファイルへmacOSのhiddenフラグが継承され、Pythonがeditable installの`.pth`を読み飛ばす場合を防ぎます。依存関係はmacOS arm64用wheelから導入されます。NVIDIAドライバ、CUDA Toolkit、Isaac Simは不要です。PPOは既定でCPUを使い、高精度学習では`--device mps`も選べます。

インストール確認:

```bash
python -m pytest
so101-check-env --task line
```

## 家のMacからWindowsへ指示する

長時間学習は Tailscale 上の `desktop-nt5t7n1`（Windows）。OpenSSH は [#10](https://github.com/ichirooo6755/syodo/issues/10) で有効済み。公開鍵と Cursor Remote SSH は [#11](https://github.com/ichirooo6755/syodo/issues/11)。

macOS の OpenSSH はユーザー名 `電研` を拒否する。Windows 側で ASCII 管理者 `syodo` を作り、鍵を `C:\ProgramData\ssh\administrators_authorized_keys` へ入れる。

Windows（管理者 PowerShell）:

```powershell
cd $env:USERPROFILE\Documents\syodo
.\scripts\add-mac-ssh-key.ps1 -PublicKey "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJEbAcCQhiRbSQjLV5E4XpnIlE+4GwMV5AEG0PDQs3ZM macbook-pro"
```

リポジトリがまだ古い場合は、同じ公開鍵を引数にしてスクリプトを実行する。sshd が止まっているときだけ `.\scripts\enable-windows-ssh.ps1`。

Mac:

```bash
ssh syodo-windows
```

`~/.ssh/config` の `Host syodo-windows` が `desktop-nt5t7n1` / ユーザー `syodo` / 鍵 `~/.ssh/id_ed25519_syodo` を指す。

Cursor: Command Palette → **Remote-SSH: Connect to Host** → `syodo-windows`。フォルダは **`C:\syodo`**（junction。実体は `C:\Users\電研\Documents\syodo`）。

## 環境仕様

標準モードの観測は42次元、筆・墨物理だけの高精度モードは65次元、画像お手本を
使うprofessional version 3は371次元の`float32`ベクトルです。

| 要素 | 次元 |
|---|---:|
| SO-101関節角度 | 6 |
| SO-101関節速度 | 6 |
| 筆先ワールド位置 | 3 |
| 現在目標点までの相対位置 | 3 |
| 正規化した全体進捗 | 1 |
| pen-downフラグ | 1 |
| 筆先速度 | 3 |
| 筆軸方向 | 3 |
| 穂先変形 | 3 |
| 筆圧・墨量・含水率 | 3 |
| 目標接線 | 2 |
| 目標筆圧・速度・線幅・画内進捗 | 4 |
| とめ・はね・はらい one-hot | 3 |
| サーボ遅延 | 1 |

高精度モードはさらに、硯までの相対位置、芯墨・表面墨・余剰墨・滴下危険度、
6つの穂先曲げ速度、末端筆軸、目標ロール、工程one-hotを含みます。
version 3はさらに、16×16のお手本全体像、筆先の接線座標系で切り出した5×5の
お手本パッチと5×5の実墨パッチを含みます。画像はCPUで処理し、CNNやCUDAは不要です。

行動は`Box(-1, 1, shape=(6,))`です。各値を小さな関節位置目標の増分へ変換し、SO-101の可動域内へクリップします。第6関節はグリッパです。筆は固定されているため、グリッパを不要に動かすと減点されます。

報酬と、実機較正可能な筆・墨・遅延定数は[config.py](src/so101_calligraphy/config.py)で調整できます。目標点は許容半径に入ったときだけ一つずつ進み、離れた場所から後続点を通過しても筆順の進捗報酬は得られません。全画完了、過大筆圧、重大な衝突または関節制限到達でエピソードが終了します。時間切れによる`truncated`は常に`False`です。

Pythonから直接作る例:

```python
from so101_calligraphy import CalligraphyEnv

env = CalligraphyEnv(task="cross")
observation, info = env.reset(seed=7)
observation, reward, terminated, truncated, info = env.step(env.action_space.sample())
env.close()
```

Gymnasium登録名は`SO101Calligraphy-v0`です。

## PPOで学習する

直線、円、十字を順番に学習する標準実行:

```bash
source .venv/bin/activate
so101-train --curriculum all --timesteps 200000
```

`--timesteps`は各段階のステップ数です。上の例では合計60万ステップになります。配線確認だけなら各段階数千ステップでも実行できますが、滑らかな筆記方策にはより長い学習と報酬調整が必要です。

一段階だけ学習する場合:

```bash
so101-train --curriculum line --timesteps 200000
so101-train --curriculum circle --timesteps 200000
so101-train --curriculum cross --timesteps 300000
```

主なオプション:

```text
--output PATH          出力先
--seed N               乱数シード
--learning-rate FLOAT  PPO学習率
--n-steps N            rollout長
--batch-size N         minibatchサイズ（n-stepsの約数）
--eval-freq N          評価間隔
--checkpoint-freq N    チェックポイント間隔
```

カリキュラム実行時には前段階のネットワークを次段階へそのまま引き継ぎます。出力例:

```text
runs/20260815-143000/
├── run.json
├── final_model.zip
├── 01-line/
│   ├── train_logs/train.monitor.csv
│   ├── reward_curve.png
│   ├── checkpoints/
│   ├── best/best_model.zip
│   ├── evaluation/evaluations.npz
│   └── final_model.zip
├── 02-circle/
└── 03-cross/
```

## 美しい線質をPPOで学習する

実在の日本字形を使い、`とめ → はね → はらい → 混合`の順に同じPPO方策を引き継ぎます。KanjiVGから中心線・筆順・画種を、[AnimCJK](https://github.com/parsimonhi/animCJK)の日本語楷書アウトラインから画ごとの線幅時系列を取得します。AnimCJKの約22 MBの固定revisionデータは初回だけ`data/animcjk/`へ保存されます。

```bash
source .venv/bin/activate
so101-train-beauty --output runs/beauty-techniques --timesteps 50000
```

各段階はDLSの位置・筆軸基準制御に対する6関節残差をPPOで学習します。学習時には紙面摩擦、関節摩擦、アクチュエータゲイン、1〜数stepの遅延、穂先剛性、墨量、含水率をランダム化します。成果物には次が含まれます。

```text
runs/beauty-techniques/
├── run.json
├── summary.json
├── final_model.zip
├── baseline/evaluation.json
├── final/evaluation.json
├── final/ink/*.png
├── 01-tome/reward_curve.png
├── 02-hane/reward_curve.png
├── 03-harai/reward_curve.png
└── 04-mixed/reward_curve.png
```

ネットワークを含む最小動作確認では`--timesteps 256 --n-envs 1 --n-steps 64 --batch-size 64`を使えます。AnimCJKを使わず、自動生成した線幅だけで試す場合は`--no-animcjk`を指定します。

学習済みの基本筆法モデルは`models/beauty-techniques-ppo.zip`です。累積115,200 PPO stepの学習後、基本7課題、ドメインランダム化70 episode、教育漢字1,026字の全数評価をすべて完筆しました。数値と書跡は[弾性筆・墨転写・基本筆法PPOの学習結果](docs/results/2026-08-15-realistic-brush-beauty.md)を参照してください。

## 硯と画像お手本から始める高精度書道

高精度モードは、検証済みの[Aoyagi Kouzan毛筆フォント](https://opentype.jp/kouzanmouhitufont.htm)
を既定の完成書跡画像教師にします。画数・筆順・画種はKanjiVG、日本字形の中心線と
線幅はAnimCJKが担当し、お手本画像は全体・局所観測、逐次報酬、完成時評価へ使います。
各画は元の順番と点数を保ったまま、法線方向へ最大8 mmの低次曲線でのみ補正するため、
交差部で別画へ飛ぶ点単位の吸着は行いません。学習開始前に常用漢字2,136字の
データ被覆を検査します。

Aoyagiは初回だけ公式配布ZIPを取得し、ZIPとTTFのSHA-256を検証して
`data/professional/`へ保存します。任意で正規ライセンスの
[Sモトヤ正楷書5 ProN](https://www.motoyafont.jp/font-list/seikai.html)へ差し替えられます。
指定ファイルのname tableが該当製品でない場合は学習前に停止します。

Sモトヤを購入済みで教師を差し替える場合だけ指定します。

```bash
export SO101_MOTOYA_FONT="/absolute/path/to/S-Motoya-Seikaisho-5-ProN.otf"
# または各コマンドへ --motoya-font /absolute/path/to/font.otf
```

```bash
source .venv/bin/activate
so101-train-professional \
  --output runs/image-exemplar-joyo \
  --timesteps 50000 --bc-steps 12000 --n-envs 4 --device mps
```

`--device mps`はApple SiliconのGPUでPPO/behavior cloningのニューラルネットを
学習します。MuJoCo物理と並列環境はCPU上で動作し、CUDAやIsaac Simは使いません。

カリキュラムは、含墨・墨落とし・垂直搬送、起筆／送筆／収筆、とめ／はね／はらい、
曲がり／折れ、実在部首、教育漢字、常用漢字の順です。各段階で完筆、軌跡、線幅、
配置、角度、運筆、滑らかさ、無滴下、無衝突のゲートを通過しない限り先へ進みません。
DLSの速度・圧力則は、日本文教出版が公開している毛筆指導の
[「始筆・送筆・終筆」と筆圧](https://www.nichibun-g.co.jp/data/education/line/e-book/line10/HTML/index9.html)
の区分に対応させています。
DLS基準動作をbehavior cloningした後、PPOは6関節の小さな残差を学習します。
`--eval-limit 0`（既定）は最後に2,136字すべてを評価します。
短い配線確認だけなら、例えば次を使います。

```bash
so101-train-professional --output runs/image-exemplar-smoke \
  --timesteps 256 --bc-steps 256 --bc-epochs 1 \
  --n-envs 1 --n-steps 64 --batch-size 64 --stage-eval-size 2 --eval-limit 3
```

切り戻し比較は`--ablation legacy`、`brush`、`brush-ink`、`all`に加え、
`no-brush`、`no-ink`、`no-brushwork`、`no-exemplar`で一要素ずつ外せます。
どの構成もversion 3の371次元観測を使い、`no-exemplar`では画像部分をゼロにするため、
同じネットワーク形状で比較できます。画像による軌跡補正だけを切る場合は
`EnvConfig.exemplar_motion_strength=0`にします。
今回の連続穂掃引・圧力整合・収筆ゲートの実測値と書跡は
[連続穂掃引と収筆規則の評価](docs/results/2026-08-15-brushwork-refined.md)にあります。
楷書の押し引きそのものを直した比較は
[楷書用筆則への切り替え](docs/results/2026-08-15-kaisho-yohitsu.md)です。

### 楷書用筆則とデータ役割

`modules.brushwork=professional` のとき、局所の筆圧・速度・筆軸・XY微動は
`src/so101_calligraphy/brushwork.py` の画種家族ルールから生成します。

| 入力 | 使うもの | 使わないもの |
| --- | --- | --- |
| KanjiVG | 筆順、画数、CJK Strokes 画種 | 完成字形の美観 |
| AnimCJK | 日本字形の中心線、画の線幅スケール（中央値） | サンプルごとの線幅→Z |
| 用筆則 | 起筆押し、送筆提按、収筆押し／抜き、逆入、回鋒、転折 | 文字ごとのハードコード |

画種家族は `heng`（横）、`shu`（縦）、`pie`（左払い）、`na`（右払い）、
`dian`（点）、`ti`（挑）、`zhe`（折）、`gou`（鉤／はね）です。常用漢字は
この写像だけで運筆されるため、特定文字向けの分岐は持ちません。
評価の`final/characters.csv`と`final/summary.json`には総合点に加えて次の内訳が
必ず保存されます。

- `glyph_shape`、`stroke_placement`、`stroke_length`、`stroke_angle`
- `line_width`、`trajectory`、`stroke_order`
- `smoothness`、`brushwork`、`ink_quality`、`ink_loading`
- `drip_control`、`collision_safety`、`balance`

完成率、滴下数、衝突数、平均・10パーセンタイル・最低美観も別項目です。代表字の
実際の墨跡は`final/ink/`、画像教師と差分を含む3面PNGは
`final/comparisons/`へ保存されます。
人間の審美判断を置き換える点数ではなく、再現可能な工学評価として使用してください。

### 常用2,136字のシャード評価と hard-mining

学習中の96字サンプル合格だけでは全常用漢字の品質は保証しません。5x完了後は次の順で進めます。

```bash
# 1) 全常用漢字を N シャードで並列評価（5x実行中は避ける）
PYTHONPATH=src python scripts/evaluate_joyo_shards.py \
  --model runs/kaisho-yohitsu-5x/final_model.zip \
  --output runs/kaisho-yohitsu-5x-joyo-eval \
  --shards 8 --device cpu --seed 23

# 2) 失敗字を hard-mining 段階として再学習
so101-train-professional \
  --ablation all \
  --initial-model runs/kaisho-yohitsu-5x/final_model.zip \
  --start-stage 9 \
  --hard-csv runs/kaisho-yohitsu-5x-joyo-eval/characters.csv \
  --n-envs 6 --bc-workers 6 --device mps \
  --output runs/kaisho-yohitsu-5x-hard \
  --seed 23

# 3) best checkpoint 選定と PPO contact sheet
PYTHONPATH=src python scripts/select_best_model.py --run runs/kaisho-yohitsu-5x-hard
PYTHONPATH=src python scripts/render_ppo_contact_sheet.py \
  --model runs/kaisho-yohitsu-5x-hard/final_model.zip \
  --output docs/results/ppo-contact-sheet.png
```

`evaluate_joyo_shards.py` は各シャードの完全CLIを保存し、Unicodeの重複・欠落を検査したうえで CSV と summary を統合します。`--dry-run` で起動コマンドだけ確認できます。

高精度モデルをMuJoCo Viewerで再生する場合:

```bash
mjpython -m so101_calligraphy.training.replay \
  models/professional-image-v3-ppo.zip \
  --kanji 書 --professional \
  --save-ink outputs/sho.png
```

紫の目標点が含墨・墨落とし、緑が搬送、赤が筆記です。終了時に14成分、芯墨・
表面墨、滴下、衝突の内訳も端末へ表示します。

画像教師を外した比較は`--ablation no-exemplar`で実行できます。これは筆物理・含墨・
運筆だけを診断する切り戻し用で、画像美観学習ではありません。

## 実在の筆画と部首を学習する

[KanjiVG](https://github.com/KanjiVG/kanjivg) `r20250816`の筆順SVGを利用できます。必要な文字だけを初回に`data/kanjivg/`へ取得し、Gitには追加しません。`kvg:type`と`kvg:radical="general"`を直接使うため、手作りの似た形ではなくKanjiVG収録の筆画・部首です。

基本筆画:

| 段階 | KanjiVG筆画 | 取得元 |
|---|---|---|
| 横画 | `㇐` | 一 |
| 縦画 | `㇑` | 十 |
| 点 | `㇔` | 主 |
| 左払い | `㇒` | 人 |
| 右払い | `㇏` | 人 |
| 折れ | `㇕` | 口 |
| はね | `㇚` | 小 |

```bash
so101-train --kanjivg-curriculum techniques --timesteps 200000
```

部首カリキュラムは、実際の漢字から一般部首としてマークされた部分だけを抽出します。

| 段階 | 部首 | 取得元 |
|---|---|---|
| ninben | 亻 | 休 |
| sanzui | 氵 | 海 |
| risshinben | 忄 | 情 |
| tehen | 扌 | 持 |
| kusakanmuri | 艹 | 花 |
| shinnyou | ⻌ | 道 |
| gonben | 言 | 語 |

```bash
so101-train --kanjivg-curriculum radicals --timesteps 250000
```

筆画7段階の後に部首7段階を続ける場合:

```bash
so101-train --kanjivg-curriculum foundations --timesteps 250000
```

KanjiVGに収録された任意の一文字を全筆順で学習する場合:

```bash
so101-train --kanji 書 --timesteps 500000
```

取得済みデータの場所を変える場合は、学習と再生の両方へ`--kanjivg-cache PATH`を指定します。

## MuJoCo Viewerで再生する

macOSではGUIをメインスレッドで起動する必要があるため、MuJoCo付属の`mjpython`を使います。

```bash
source .venv/bin/activate
mjpython -m so101_calligraphy.training.replay \
  runs/20260815-143000/final_model.zip \
  --task cross
```

緑の点はpen-up区間の現在目標、赤い点はpen-down区間の現在目標、青い点列は文字の中心線です。黒い楕円群が、筆圧、速度、穂先変形、墨量と水分から逐次転写された実際の墨跡です。ウィンドウを閉じると再生を終了します。

MP4へ書き出す場合（Viewer不要、学習と並行可）:

```bash
python -m so101_calligraphy.training.replay \
  runs/kaisho-yohitsu-5x/05-radicals/model.zip \
  --kanji 一 --professional \
  --save-video runs/kaisho-yohitsu-5x/videos/ichi.mp4 \
  --video-fps 30 --video-stride 2
```

速度やエピソード数も指定できます。

```bash
mjpython -m so101_calligraphy.training.replay MODEL.zip \
  --task circle --episodes 3 --speed 1.5 --save-ink outputs/circle.png
```

KanjiVGカリキュラムの段階や一文字を再生する例:

```bash
mjpython -m so101_calligraphy.training.replay MODEL.zip --kanjivg-stage gonben
mjpython -m so101_calligraphy.training.replay MODEL.zip --kanji 書
```

## 任意のSVGを使う

SVGは線の中心軌跡として作成してください。フォントをアウトライン化した塗りつぶし輪郭は、筆の中心線ではなく輪郭線として解釈されます。書道用データでは、原則として1画を1つの`path`、`line`、`polyline`等にしてください。各要素へ`data-technique="tome"`、`"hane"`、`"harai"`のいずれかを付けると終筆を明示でき、未指定ならKanjiVG画種または安全な`とめ`へ分類します。

- XML内の描画要素順が筆順です。
- 一つの`path`に離れたサブパスがある場合、それぞれ別の画になります。
- `path`、`line`、`polyline`、`polygon`、`circle`、`ellipse`、`rect`に対応します。
- 親グループと要素の`transform`を適用します。
- 非表示要素と`defs`内の図形は無視します。
- 全体を縦横比を保ってA4の安全な筆記領域へ配置します。

付属例を学習する場合:

```bash
so101-train --svg examples/cross.svg --timesteps 300000
```

再生時にも同じSVGを渡します。

```bash
mjpython -m so101_calligraphy.training.replay \
  runs/20260815-150000/final_model.zip \
  --svg examples/cross.svg
```

## ファイル構成

```text
src/so101_calligraphy/
├── assets/so101_calligraphy.xml  軽量SO-101、A4紙面、筆
├── brush_physics.py              分節筆と旧筆の切替・状態計測
├── brushwork.py                  起筆・送筆・収筆の運筆計画
├── config.py                     物理・報酬・環境設定
├── hardware_desk.py              実機デスク較正（半紙・硯・穂長）
├── ink.py                        紙面転写とViewer墨跡
├── ink_model.py                  含墨・墨落とし・毛細管・滴下
├── metrics.py                    Fréchet、線幅、終筆、重心評価
├── trajectory/                   図形、SVG、3D waypoint生成
├── envs/                         Gymnasium/MuJoCo環境
└── training/                     PPO学習、グラフ、Viewer再生
scripts/hw-write                  実機の日常入口（1〜4文字）
scripts/hardware_write.py         実機 play / bilateral / 教示
scripts/hardware_calibrate.py     トルクOFF較正
docs/hardware-open.md             実機の今
docs/hardware-calibration.md      較正手順
docs/training-runs.md             学習 run 台帳
docs/results/                     過去の評価メモ（履歴。入口ではない）
docs/plans/                       承認済み設計（履歴）
examples/                         最小SVG例
tests/                            軌跡、環境、PPO統合テスト
```

## 注意点と拡張方針

このモデルは学習研究用です。穂先は多数の筆毛や流体を解くモデルではなく、MuJoCoの3分節・6受動曲げ自由度の接触と軽量な楕円転写モデルです。学習済み関節指令を実機へ直接送らず、先に[デスク較正](docs/hardware-calibration.md)で半紙・硯・アタッチメント可動・穂長・Follower実可動域を測ってください。`hardware_write.py` は `data/hardware/desk.json` が `ready` になり、`sync-limits`を済ませるまで再生しません。実機の日常入口は`./scripts/hw-write 文字`。`trace`は1〜4文字に対応し、3〜4文字は縦書き2×2配置。開ループ筆圧は奥→手前の線形。閉ループは`teach-reference`。字の中の縦画そのものはKanjiVG筆順どおりに書けます。用筆は教室指導のトン・スー・トン／約45°入筆／穂先上部通過を目標にしています（[松本松栄堂「一」](https://matsumotoshoeido-shodo.jp/blog/4571/)、[香墨・基本の線](https://www.kasumi-syodo.jp/activities/10642)）。

0〜100の`beauty_score`は軌跡、線幅、終筆、配置から計算する再現可能な工学指標であり、人間の審美眼そのものではありません。人間評価や学習済み美的モデルを加える場合も、この内訳を残して評価のブラックボックス化を避けてください。

KanjiVGデータはUlrich Apelおよびコントリビューターの著作物で、[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)です。本リポジトリのMITライセンスは、ダウンロードしたKanjiVGデータには適用されません。詳細は[THIRD_PARTY.md](THIRD_PARTY.md)を参照してください。

## 教育漢字1,026字を一つの方策で学習する

小学校1〜6年の学年別漢字配当表を対象に、文字ごとの別モデルではなく一つの汎化PPO方策を学習できます。対象文字と学年は[EDRDG KANJIDIC2](https://www.edrdg.org/kanjidic/kanjd2index_legacy.html)、筆順軌跡はKanjiVGから取得します。学年別件数が `80, 160, 200, 202, 193, 191`、合計1,026字に一致しない場合は開始しません。

```bash
source .venv/bin/activate
so101-train-education --output runs/education-kanji
```

先に線質を学習したモデルから始める場合:

```bash
so101-train-education \
  --initial-model models/beauty-techniques-ppo.zip \
  --output runs/education-kanji
```

学習順は、1年生の低画数文字、1年生全体、2年生まで、…、6年生までの累積7段階です。各resetでプールから文字を選ぶため、同じ42次元観測と6次元行動で、位置だけでなく画種、画内進捗、目標筆圧・速度・線幅を全字へ共有します。既定ではKanjiVGの筆順・画種にAnimCJKの日本語楷書アウトラインを重ねます。中心線だけで試す場合は`--no-animcjk`を指定します。

教育漢字モードは、MuJoCoヤコビアンの位置・筆軸DLS関節指令にPPOの6関節残差指令を加える residual RL です。解析制御が安全な基準筆記を担当し、PPOは距離、筆圧、線幅、終筆、姿勢、滑らかさと不要運動を最適化します。残差は`EnvConfig.residual_action_scale`で安全に縮小されます。純PPOの直接関節指令モードも利用できます。

既定では各段階の固定サンプル成功率75%以上まで追加学習し、最後に全1,026字を決定論評価します。全体成功率80%以上になるまで最終段階を続行します。停止回数を制限したい検証実行だけ `--max-rounds N` を指定してください。主な成果物:

```text
runs/education-kanji/
├── run.json
├── final_model.zip
├── final_evaluation.json
├── all-kanji-evaluation-1.csv
└── 01-grade-1-low-stroke/ ... 07-grade-6/
```

学習済み汎化方策で任意の教育漢字を再生する場合、学習時と同じ残差制御を有効にします。

```bash
mjpython -m so101_calligraphy.training.replay \
  runs/education-kanji/final_model.zip --kanji 書 --ik-assist
```

`models/education-kanji-ppo.zip`は旧20次元・点接触環境で固定seedの全1,026字を完筆した履歴モデルです。新しい42次元環境とは観測形状が異なるため、再現にはcommit `216ebdb`を使用してください。新環境では`beauty-techniques-ppo.zip`を起点に上記コマンドで教育漢字へ継続学習します。

```bash
git worktree add ../syodo-v01 216ebdb
cd ../syodo-v01
mjpython -m so101_calligraphy.training.replay \
  models/education-kanji-ppo.zip --kanji 書 --ik-assist
```

詳細は[教育漢字汎化学習の結果](docs/results/2026-08-15-education-kanji.md)を参照してください。

KANJIDIC2とKanjiVGのダウンロード物は`data/`へキャッシュされ、Gitには追加されません。ライセンスと帰属は[THIRD_PARTY.md](THIRD_PARTY.md)を参照してください。
KANJIDIC2の最新版へ更新するときは`--refresh-data`を付けて再実行してください。各runには使用ファイルのSHA-256が記録されます。

途中のstageモデルから再開するときは、対応する段階番号を指定します。例えば5年生段階のモデルから6年生段階だけを続ける場合:

```bash
so101-train-education \
  --initial-model runs/education-kanji/06-grade-5/latest_model.zip \
  --start-stage 7 --output runs/education-kanji-resumed
```
