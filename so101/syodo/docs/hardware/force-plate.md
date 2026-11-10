# 200 × 300 × 2 mmアルミ板の4点荷重計測

2026-09-10。実物は幅200 mm、奥行300 mm、厚さ2 mmのアルミ板。四隅の下に秋月 **SC616C-1kg × 4**、各セルにHX711を1台、Pico 2 Wを1台使う。A4（210 × 297 mm）とは寸法が異なる。ソフトウェアの入口は `./scripts/force-plate`。

合計鉛直荷重（N・g相当）、各支持点の荷重、荷重中心（mm）を記録する。4点の反力から任意の圧力分布を復元することはできない。筆だけが触れる準静的な状態で荷重中心を接触位置の目安にする。手、文鎮の移動、机への接触、横方向の摩擦、取付部が伝えるモーメント、アルミ板のたわみ・振動は誤差になる。墨跡や毛先そのものはカメラで照合する。

## 配線と取り付け

番号は既存の配置を維持する。上は奥、下は手前。

| セル | 板上の位置 | DAT（DOUT） | CLK（PD_SCK） | 内部チャンネル |
| --- | --- | --- | --- | --- |
| ① | 右下 | GP2 / Pin 4 | GP6 / Pin 9 | 3 |
| ② | 左下 | GP3 / Pin 5 | GP7 / Pin 10 | 0 |
| ③ | 右上 | GP4 / Pin 6 | GP8 / Pin 11 | 2 |
| ④ | 左上 | GP5 / Pin 7 | GP9 / Pin 12 | 1 |

ロードセルの電源＋→AVDD、電源−→GND、信号＋→INPA、信号−→INNA。B入力は使わない。4基板とPicoのGNDは共通にする。秋月CN1は1=VDD、2=DAT、3=CLK、6=GND。

**電圧を確認する。** HX711基板VDDは2.7～5.5 Vに対応するので、3V3 OUT（Pin 36）で信号を3.3 V系に揃える。SC616Cの励起電圧は3～10 Vなので、接続した状態の **AVDD–GNDが3.0 V以上**あることをテスターで確認する。下回る場合はその給電では仕様を満たさない。5 V VBUSを使う構成ではDATとCLKの電圧変換を設計して使う。Pico 2のデジタル入力の通電時耐性だけを根拠に、電源投入・切断時を含めた5 V直結を承認しない。

SC616Cはビーム型で、片端をベースに固定し、反対側の荷重端を板に取り付ける。スペーサで変形部が板・ベースに接触しないようにする。両端を同じ板へ固定したり、下面全体を机に密着させたりしない。各セルの矢印と荷重方向を確認する。ロボットの土台は測定板に載せない。荷重経路は板→各セル→ベースだけにし、配線は余裕を持たせる。板・紙・下敷き・紙留めを載せてから風袋を取る。

1 kgは**各セル**の定格であり、四隅のどこへでも4 kgを載せてよいという意味ではない。板の自重も各セルの負荷になる。厚さ2 mmの板を完全な剛体と仮定して精度を保証せず、中央・隅・中間位置の重りで検証する。

根拠: [SC616C-1kg製品](https://akizukidenshi.com/catalog/g/g117084/)、[セルのデータシート](https://akizukidenshi.com/goodsaffix/SC616C-1kg%20load%20cell.pdf)、[秋月HX711説明書](https://akizukidenshi.com/goodsaffix/ae-hx711.pdf)、[HX711データシート](https://akizukidenshi.com/goodsaffix/hx711.pdf)、[Pico 2 Wデータシート](https://datasheets.raspberrypi.com/picow/pico-2-w-datasheet.pdf)。

## 1. 表示・動作確認

```bash
./scripts/force-plate live --demo                         # ハード不要、合成データ
./scripts/force-plate live --port /dev/cu.usbmodem1101      # 未較正は4個のraw値のみ
./scripts/force-plate live --port /dev/cu.usbmodem1101 --ascii --seconds 5
```

GUIには実寸比率の板と4支持点を表示する。較正後は点の位置と円の大きさで荷重中心・荷重を表示する。未応答・飽和・低荷重・時刻差超過では位置を作らない。通信が1秒以上途切れたら現在値を消す。表示の風袋ボタンは無荷重で16フレームを平均し、その画面だけ更新する。保存済みの較正や書字記録の風袋は変更しない。GUIと記録コマンドを同じポートで同時実行しない。

## 2. 支持点を実測して設定

```bash
./scripts/force-plate init
```

`data/hardware/force-plate-geometry.json`を作成する。板は200 × 300 mmで確定しているが、支持点はまだ未実測なので **各端から15 mm内側という仮値**（左15・右185・上15・下285 mm、支持間隔170 × 270 mm）を置いている。すでにファイルがあれば上書きせず停止する。

板の左上を原点、右へ+X、下へ+Yとする。ロードセルの**荷重端が板を支持する中心**を測り、`geometry.left_mm / right_mm / top_mm / bottom_mm`を書き換える。四つの荷重点が長方形を成す設置に対応する。ベース固定側やセンサー外形の端は計測位置ではない。板の外寸をそのまま支持点間隔にしない。

古い内部座標は手前左の支持点が原点、+X=奥・+Y=右。CSVには互換用の`reaction_centre_x_m/y_m`と、新しい板左上基準の`board_x_mm/y_mm`を両方残す。

## 3. 板を組んだまま較正

100 g等の質量が分かっている重りを使う。以下の`100`は重りの**実際の質量**へ置き換える。最初は小さな荷重から確認する。文字を書かせる前に板設置後の机較正を取り直し、そのdeskを指定すると較正が現在の机に結び付く。

```bash
./scripts/force-plate calibrate \
  --port /dev/cu.usbmodem1101 --mass-g 100 \
  --geometry data/hardware/force-plate-geometry.json \
  --desk data/hardware/desk.json \
  --out runs/force-plate/calibration-01
```

板だけを測る段階は`--desk`を省略できる。対話で無荷重、四隅と中央の5点、別の位置の3点、最後に再び無荷重を測る。各点4秒・最低16フレーム。失敗しても取得した測定データを出力に残す。再実行は新しい出力名を使う。

較正は `ΣFi=mg`、`Σxi Fi=mg x`、`Σyi Fi=mg y` を最小二乗で同時に解き、**4個それぞれの符号付き感度**を求める。隅に100 gを載せたからといって、その隅の1セルだけに100 gがかかるとは扱わない。4セルの配分を安易な理想分配へ固定しない。適合点から独立した位置で、荷重誤差・位置誤差・ノイズ・最後のゼロドリフトを検証する。

現行の初期判定は荷重誤差0.03 N以内、位置誤差5 mm以内、ノイズ6σが0.03 N以下。これは合格の保証値ではなく、較正を採用するための設定。感度差・結線・取り付けが不適切で残差が大きいと保存を拒否する。接触閾値は最大(0.02 N, 無荷重ノイズの6σ)、最大荷重はfit/validate両方で測定した最大荷重の小さい方×1.05。100 gだけで較正したものを、より大きい筆圧範囲へ外挿しない。複数質量のデータを追記したmanifestは`fit`で再計算できる。

```bash
./scripts/force-plate fit measurements.json --out measured-calibration.json
./scripts/force-plate live --port /dev/cu.usbmodem1101 \
  --calibration runs/force-plate/calibration-01/calibration.json
```

## 4. 記録とロボットとの連携

```bash
./scripts/force-plate record --port /dev/cu.usbmodem1101 --seconds 30 --out raw.jsonl
./scripts/force-plate analyze raw.jsonl \
  --calibration runs/force-plate/calibration-01/calibration.json --out result-01
```

書字は1コマンドでPicoの記録と既存`hw-write`を実行する。

```bash
./scripts/force-plate write 文字 \
  --port /dev/cu.usbmodem1101 \
  --calibration runs/force-plate/calibration-01/calibration.json \
  --out runs/force-plate/writing-01
```

**板設置で紙面が高くなるため、旧desk・旧traceは流用しない。** [机較正手順](../hardware-calibration.md)に従い、現物の紙面・搬送高さ・筆圧基準を取り直す。上のwriteは実測較正のdesk fingerprint一致、4台応答、非飽和、開始時ゼロ点、時刻精度を確認してから既存hw-writeを呼ぶ。既存の机・関節・硯・カメラ等の検証は維持される。`--speed`で書字速度を指定できる。

これは **測定と分析を追加する書字**。荷重からその場で関節を補正する閉ループや、ロードセル断線時の緊急停止器にはしていない。実行中の通信異常は記録され、終了時に失敗として報告する。サーボ制御の既存保護をセンサーの代わりに変更しない。

- `raw.jsonl`: 生値、実際にDOUT-readyを観測した各時刻、未応答、ADC飽和、sequence、boot ID、USB受信時刻、時計同期イベント。
- `write.csv` / `write.json` / `trace.npz`: 既存書字記録。指令区間の単調時刻、セッションID、指令上の毛先XYZを追加。
- `analysis/force-plate.csv`: 全荷重、各チャンネルN、g相当、板上mm、無効理由、対応する書字点、接触抜け・意図しない接触。
- `analysis/strokes.csv`: 画ごとの平均・標準偏差・ピーク荷重、変動係数、接触抜け件数。
- `analysis/force-plate.png`: 荷重時系列と板上の荷重中心。
- `analysis/summary.json`: 原本・較正・ロボットログのSHA-256、集計と制約。

Picoは`sync TOKEN`へ端末時刻を返す。Macは往復時間が短い応答で時計差を推定し、10秒ごとに更新。USB受信時刻を取得時刻へ置き換えない。往復時間の半分と、未測定のクロックドリフト用1000 ppm予算を不確かさとして記録する。旧ファーム診断用の`record --no-sync`もあるが、その記録はロボットとの時刻照合には使えない。同一セッション以外のログ・時計逆転・Pico再起動は拒否する。

4基板は独立クロックなので、同じループで読んでも厳密な同時AD変換にはならない。チャンネル時刻差は初期上限5 ms。HX711は実基板のRATE設定により10/80 SPS。速度を上げる場合は4枚のRATEを揃え、`main.py`のRATE_HZも合わせる。ファームの定数変更だけでは80 SPSにならない。DOUT観測の遅れも記録する。**ADCデジタルフィルタの遅延は未較正**で、接触開始・筆離れの時刻にはその誤差が残る。動的な制御や学習採用前にタップ・段荷重で遅延を測る。

## 5. 板座標とロボット座標

位置誤差の照合には、板上で実測した3点以上と、それと独立した検証点を使う。次の構造のJSONを作り、`register`を実行する。値を例から写さず現物で測定する。`robot_xy_m`は同じ新deskのロボット座標（m）。

```json
{"desk_fingerprint":"現在の新deskのfingerprint", "points":[
  {"role":"fit", "board_xy_mm":[0,0], "robot_xy_m":[0.30,-0.10]},
  {"role":"fit", "board_xy_mm":[200,0], "robot_xy_m":[0.30,0.10]},
  {"role":"fit", "board_xy_mm":[0,300], "robot_xy_m":[0.00,-0.10]},
  {"role":"validate", "board_xy_mm":[100,150], "robot_xy_m":[0.15,0.00]}
]}
```

```bash
./scripts/force-plate register measured-points.json --out measured-registration.json
# writeに --registration measured-registration.json を追加
```

変換はアフィン写像で、独立検証点を含め2 mm以内を要求する。指令毛先と反力中心の距離は`command_centre_error_mm`へ保存する。指令毛先と実際の曲がった毛先が一致するとは限らず、この値を筆跡精度とは扱わない。

## 書道改善への使い方と現在の検証範囲

まず横画の往復、縦画、止め・払いを複数速度で記録し、接触抜け・筆圧のばらつきと撮影した線を照合する。次に深さ対荷重・速度対荷重・方向による遅れを測り、既存の筆モデルの剛性・減衰や筆圧較正に使う。適合用とは別の運筆・文字で改善を測り、従来の包括評価・採用基準を通す。`target_pressure`は現行モデルの単位であり、Nへ読み替えない。実N目標があるCSVの`target_force_n`だけ、Nの誤差を計算する。

現段階の出力は`training_eligible=false`。実測・動的遅延・紙座標合わせ・独立した墨跡評価を伴わない合成データや計測だけで、学習済みモデルを更新しない。

```bash
./scripts/force-plate demo --out runs/force-plate/plate-demo-new
```

200 × 300 mm板、異なる符号・感度の4セル、既知位置の較正、独立検証、480フレームの模擬書字を実行する。故意に5フレームの接触抜けと1フレームの欠測を含める。実測ではないとJSONと図に明示する。
