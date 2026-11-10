# SO-101 実機較正

書字再生の前に、トルク OFF で机上の幾何を教える。較正が `ready` になるまで
`hardware_write.py play` は動かない。学習済み関節をこの工程なしで送らない。

部品が折れた直接因は、筆の向き（tilt 符号）と穂先が何に当たるかが未測定のまま
関節指令を流したこと。先に半紙・硯・アタッチメント可動、把持位置から毛先までの全長、毛だけの穂長を取る。

## 較正の有効性（2026-09-08、#14）

`ready` は JSON の真偽値 `true` が必要。さらに全必須教示、sim_home、関節オフセット、
全長・筆軸長・穂長とスケールの一致、筆の下向き確認、紙・硯・傾斜範囲・搬送高さを検証する。
値の欠落、NaN/Infinity、紙面から 15 mm 未満の hover は拒否する。
`dump` / `play` はデータやロボットを読み込む前に較正を検証し、実関節範囲も必須にする。

新しい `solve` は `geometry_fingerprint` を保存する。以後、教示値や解いた幾何を
変更したら再 solve が必要。以前の schema 1 デスクは、全実測値が有効なら引き続き
読めるが、過去の編集検出はできない。次回 solve から fingerprint が付く。

`sync-limits` で既存のサーボ較正ハッシュが変わった場合、`ready=false` とし、
旧教示は保存したまま `stale_poses` に記録する。`teach` と `snap sim_home` で全姿勢を
取り直すまで solve できない。同じサーボ較正で USB 識別だけを確定する場合は失効しない。
`preview` が sim_home の基準を変更した場合は `snap sim_home` を取り直してから再 solve する。
solve で関節写像が変わったら可動域を破棄するので、`sync-limits` をもう一度実行する。
筆圧の較正・Leader 基準と軌道は、更新後の desk に合わせて取り直す。

オフライン検証と既知の限界は [issue 対応記録](results/2026-09-08-open-issues.md) を参照。

## サーボ（筆から）

半紙は字の上下が縦、左右が横。手前が下手、奥が上手。

| ID | 役割 |
| --- | --- |
| **6** 一番先端 | 筆を立てる・寝かす。実可動 159.1°（731–2541 tick）。教示では立つ側の端に近い |
| **5** その手前 | 筆が立っているとき、毛先を左右へ。寝たまま回しても立たない |
| **4** 手首曲げ | **実際に筆を立てているのはここ。** 下に曲げると立つ |

未解決の一覧: [`docs/hardware-open.md`](hardware-open.md)。

## 測るもの


| 項目        | 記録                   | やり方                                                                              |
| --------- | -------------------- | -------------------------------------------------------------------------------- |
| 把持位置→毛先 | `brush_total_cm` | ロボットが筆を把持する位置から毛先まで。現物は **12 cm** |
| 穂（毛だけ） | `brush_tuft_cm` | 毛の根元から毛先まで。現物は **4 cm**。`brush_rigid_cm` は全長との差から **8 cm** として保存 |
| 筆の向き      | `tilt_sign` / 直立・起筆  | ID6 で筆を立てる／寝かせる |
| アタッチメント可動 | `tilt_range`         | ID6 の両端。**書きで使う範囲を自分で決める**（突き当たりでなくてよい）。機械端は 731–2541 tick |
| 半紙        | `paper` 幅・高さ・中心・紙面高さ | 四隅（下手右・下手左・上手左・上手右）＋中央                                                           |
| 搬送高さ      | `safe_height_m`      | 半紙中央の真上。穂先は紙から十分離す                                                               |
| 硯         | `inkstone_offset_m`  | 墨池中心に穂先が触れたところ                                                                   |


半紙はロボットの XY に揃えて **縦置き**（字の上下＝手前〜奥）。土台と半紙は同じ机。
学習用シミュの A4 は横長・150 mm 台座なので、実機デスクは `overlay_desk_hardware` で上書きする。

## 手順

腕を手で支える。サーボへ目標位置は送らない。

```bash
# 既存deskの「穂12 cm」という誤った表記だけを安全に移行する。
# 全長が同じなら紙面・関節・筆圧較正は保持され、solveは再実行しない。
python scripts/hardware_calibrate.py brush 12 4

# 1. トルク OFF で教示（lerobot venv）
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_calibrate.py teach

# 2. 教示した関節から紙・硯・符号を解く（書道 venv）
python scripts/hardware_calibrate.py solve
python scripts/hardware_calibrate.py show
# Follower未接続でも、保存済み較正JSONから可動域とhashだけ先に同期できる
PYTHONPATH=src .venv/bin/python scripts/hardware_calibrate.py sync-limits --prepare-only
# 接続後はUSB識別を確定する。同じ較正JSONなら事前生成したtraceは無効にならない
PYTHONPATH=src .venv/bin/python scripts/hardware_calibrate.py sync-limits --usb-serial FOLLOWER_USB_SERIAL
```

既定の保存先は `data/hardware/desk.json`（`data/` は git 対象外）。

`solve` は筆が机向きになるよう `wrist_roll_offset_deg` を探す。できないときだけ取り付けか ID5 の教示を直す。
**肩・肘のゼロ点は `solve` が四隅から自動で詰める**（`refine_arm_offsets`）。`sim_home` の目視 L 字は
肘で 25° ずれうるので、出発点にしか使わない。四隅と中央は同じ机に接地しているという制約のほうが強い。
四隅を FK したとき高さが 10 mm 以上ばらつく場合は、詰めても直らないほど教示が矛盾している。
その状態では `ready` にならないので、シミュ dump の再生もできない。

**四隅は紙の角でなくてよい。** `fit_paper` は半紙の実寸と突き合わせず、教示した四角形を書字領域にする。
紙全面に書きたいときだけ紙の角で取り直す（そのとき FK が 333×242 mm を再現すれば較正の裏づけになる）。

四隅は筆を直立させてから取る。寝たまま ID5 は回さない。毛先が紙に跡を残すまで。
**筆を立てる主役は ID4（手首曲げ）。** ID6 は補助。毛先を紙につけたまま ID4 を下に曲げて垂直を作り、
ずれた分を肩・肘で座り直す。手首曲げは上限（3185 tick）が近いので、足りなくなったら肘か肩で座り直す。

**`0.00%` は張り付いた読み。** 実位置が較正レンジ外だと正規化値は 0/100% に丸められ、
端より先は区別できない。`peek` は生 tick も表示する。端に張り付いていたらそれで気づく。

MacのContinuity Cameraは権限上直接読めない。上カメラにはESP32-S3 Senseを使い、
`scripts/esp32_camera.py`でHTTP画像をrunへ保存する。

## 2026-09-01 この個体の実測（較正完了）

- 筆は把持位置→毛先12 cm、うち筆軸8 cm・穂4 cm。半紙は縦置き、土台と同じ机。学習用シミュ（A4 横長・150 mm 台）とは別シーン
- ID6 実可動 **731–2541 tick = 159.1°**。LeRobot 較正レンジも同値。ID3 肘は 1864–4071
- ID6 の % → 角はゲイン固定（−1.591°/%）＋ゼロ点当てはめ。`desk.gripper_map_rad`
- ゼロ点 肩 **−78.70°** / 肘 **+52.32°** / 手首回転 +108.79°。肩・肘は四隅から算出
- 四隅 z 幅 **1.2 mm**、実測紙面 267×154 mm、紙面 z **+14.4 mm**、搬送余裕 31 mm
- 検証: 較正に使っていない定規の実測 155 mm に対し FK 153.9 mm（差 1.1 mm）
- `desk.ready=true`。`data/hardware/desk.json` は git 対象外

`hardware_write.py` はこの紙面を高さの原点にする。現在の開ループ設定は奥 **+8 mm → 手前 −12 mm**（文字数は問わない）。
この深さ補正を毛先の目標位置に先に反映してから、前の姿勢に連続するIKを解く。
画間への上げ下げでは補正を徐々に減らし、水平移動は紙面から **+60 mm**、待機は **+100 mm**（切断後もトルク維持）。
最後の指令値で位置誤差1 mm以内・筆傾き8°以内・隣接点5°以内・関節端2°以上を確認する。
以前の一定zのIK後に関節を外挿する方式は、位置ずれと大きな姿勢変化が出るため廃止した。
設定値8/−12 mm自体は変更していないが、補正後の軌道での筆圧と線質は再び紙上で確認する必要がある。
各 trace の NPZ と `write.json` に紙面 z、相対高さ、全長12 cm・筆軸8 cm・穂4 cm、`lift_deg_per_mm` を保存する。
別の机面や古いシミュレータ z を混ぜた軌道は再生時に拒否する。

```bash
.venv/bin/python scripts/hardware_calibrate.py preview
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_calibrate.py snap sim_home
```

写真は `data/hardware/sim-home-side.png` と `sim-home-overview.png`。腕の折れ方をコピーする。穂は立てたまま。

`tilt_sign=-1` は先端サーボ符号の反転で、取り付け直しが不要な場合に使う。

## 試し書き（シミュ dump ではなく教示角）

`solve` で `ready` にしたあと、教えた手前左→手前右を関節補間できる。
安全版 `stroke` は `sync-limits` 済みのFollowerだけを受け付ける。
先端・肘は手前左で固定し、横画は土台の左右だけ。hover には上げない（肩を上げると筆が寝る）。
ID5・ID6 は開始時の値で固定する。接続直後はいまの姿勢から下手左へ。

```bash
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_calibrate.py peek
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py stroke
```

低速・手を離さない。途中で机に食い込んだら支えて止める。電源が落ちたら 12V を入れ直してから再接続する。

## 書字（較正後のみ）

硯は Leader で一度録り、`play` が書字の前に毎回再生する。保存先は `data/hardware/suzuri.npz`（git 対象外）。
追加センサーは使わず、Follower の STS3215 が返す荷重・電流を記録する（[Feetech公式資料](https://www.feetechrc.com/20210429-56091.html)）。

```bash
cd ~/Documents/syodo
./scripts/hw-write 文字
./scripts/hw-write 文字 --prepare-only  # 実機を動かさず軌道と送信前の検証結果を保存
./scripts/hw-write 文字 --camera-url http://ESP32_IP --log runs/hardware-two-character/write.csv

# バイラテの前に姿勢を合わせる。起動時の差が原点。ID5は指令しない
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py match-leader
PYTHONUNBUFFERED=1 ~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py bilateral
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py record-suzuri

# 閉ループ筆圧が要るときだけ。record-word は 文字・学習・菅原
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py teach-reference
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py record-word 文字 --out runs/hardware-two-character/taught-文字.npz
~/Documents/lerobot-hw/.venv/bin/python scripts/hardware_write.py play runs/hardware-two-character/taught-文字.npz --speed 0.25 --stride 1 --hold-s 5
```

Enter で録画開始、Enter か Ctrl+C で終了。Leader を動かすと Follower が追う（同符号）。録画が無いときは、いまの姿勢から硯へ直行し、墨池から手前 7 cm を自動2往復したあと、ID5を90°回して毛先を整える（ID5固定だと穂が左へ約13 cm飛ぶので、IKで硯位置に残す。最後の手前で待つ3秒は未実装）。`hw-write` が本書き。

`teach-reference`は上下段それぞれで空中、接触、良い筆圧を順に保存します。
`record-word`は`文字・学習・菅原`だけを受け付け、上段と下段を別々に記録します。
どちらもLeaderとFollowerの初期姿勢差が5°以内になるまでFollowerのトルクを入れません。
教示NPZの`play`は最初に全軌道を空中で往復し、Enterを押すまで本書きを開始しません。
Ctrl+C、USB・較正不一致、5°超の指令、関節端2°以内、教示上限を超える荷重では
Followerのトルクを切って停止します。

`hw-write` / `trace`は1〜4文字。1文字は中央、2文字は縦2段、3〜4文字は右上→右下→左上→左下の2×2配置。紙の余白内で最大の正方形枡を取り、字形比を保って長辺を枡いっぱいへ広げる（筆跡用に各辺2 mmを残す）。現deskの枡は順に約124/118/62 mm角。全寸法でIKが通らない場合は2%刻みで80%まで調べ、位置・傾き・関節余裕・連続性の条件を満たした最初の寸法を採用する。通らなければ送信しない。採用率をNPZの`glyph_scale`、枡と軌道を`trace.layout.svg`、寸法と充填率を`trace.layout.json`へ保存する。
3〜4文字では奥・手前の開ループ設定を左右列で共用する。2文字用Leader基準・閉ループ較正は別配置へ流用せず、開ループ較正がなければ停止する。左右差を実測したことにはならない。
`hw-write` は保存した指令を独立にFK検証し、結果を同じrunの `preflight.json` に残す。続いて8 cmの剛体軸と4 cm・3分節の穂をMuJoCoで連続再生し、`brush-simulation/` に接触点、たわみ、力、予測墨跡を保存してから実機へ進む。物性値は未実測なので、シミュレーション値だけで実機合格にはしない。
trace schema 5より古い軌道や、筆圧設定のhashが合わない軌道は再生成する。
`write.csv` には各関節の読み戻し位置・直前の指令・次の指令・追従誤差を保存する。途中で切断した場合も完了分と `write.json` の中断理由を残す。
`pressure-plan`の上下5本ずつを別紙に書き、各段の良い線番号を入力してください。信号が安定した場合だけ荷重を追従し、不安定なら選択線の深さへ固定します。
`--camera-url`を指定すると、書字開始前にESP32のJPEG取得を確認します。書字中は
映像断、カメラ移動、紙面の大きな遮蔽、書字領域外の大きな変化が3枚連続した時点で
hoverへ退避します。`camera/frames/`、`camera/metrics.jsonl`、`camera/camera.json`を
同じrunへ保存し、墨だまり・字形・線質は保存画像を目視判定します。
`dump`（シミュ PPO）は実機にまだ載せない。



## EnvConfig への入り方

`solve` の結果は `brush_tip_length_scale`（把持位置→毛先の実測 cm / 3.8）と紙・硯オフセットへ写る。穂だけの長さは `brush_tuft_cm` として別に保持する。
全長12 cmは scale ≈ 3.16 で、IK再生はその到達長で解く。変形・接触するのは末端の4 cmだけで、手前8 cmは剛体の筆軸である。
PPO は `--desk data/hardware/desk.json` で両方を読む。desk は `ready`。実機12/8/4 cm構成の追加学習は未起動。
PPO を実機に載せるならその穂での追加学習と C ゲート取り直しが要る。
