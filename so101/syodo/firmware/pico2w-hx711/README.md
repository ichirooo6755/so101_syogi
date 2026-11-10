# Pico 2 W / SC616C-1kg × 4 / HX711 × 4

200 × 300 × 2 mmアルミ板の四隅を独立計測する。上=奥。①右下=GP2/6、②左下=GP3/7、③右上=GP4/8、④左上=GP5/9。JSONの順番は②④③①（手前左、奥左、奥右、手前右）。

配線と励起電圧の確認は[詳細手順](../../docs/hardware/force-plate.md)。VDDはまず3V3 OUT（Pin 36）、GND共通。SC616CのAVDD実測が3 V未満なら励起仕様外。5 V給電の場合は信号のレベル変換と投入時条件を確認する。

MicroPythonのPico 2 W版が動作するボードへ、プロジェクトルートから実行する。

```bash
.venv/bin/python scripts/pico_put.py --port /dev/cu.usbmodem1101 firmware/pico2w-hx711/hx711.py hx711.py
.venv/bin/python scripts/pico_put.py --port /dev/cu.usbmodem1101 --reset firmware/pico2w-hx711/main.py main.py
./scripts/force-plate live --port /dev/cu.usbmodem1101
```

アップロードは一時ファイルへ書いて置換し、ボード上のSHA-256を検証する。`--reset`がないとREPLのまま止まるので、最後のmain.py転送に付ける。既存main.py・hx711.py・cal.jsonは更新前にバックアップする。UF2が必要な場合は[MicroPython公式Pico 2 Wダウンロード](https://micropython.org/download/RPI_PICO2_W/)から適切な版を選ぶ。

ファームはA入力・gain 128の25クロック。各HIGH区間を割り込み禁止にし、GCは読取中だけ禁止、シフト演算はLOWで行う。HIGH/LOWには1 µs待ちを入れる。HX711のHIGH最大50 µs・60 µs超でパワーダウンという条件を守るための実装。実ピン波形の最終確認はロジックアナライザで行う。

全4チャンネルまたは250 msのタイムアウトで1フレームを出力する。欠測rawの0はダミーで、`hx711_ready=false`を必ず確認する。`sequence`、`boot_id`、各DOUT-ready観測時刻、観測間隔由来の不確かさを保存する。独立ADCの同時変換は保証しない。`RATE_HZ=10`は実基板ジャンパの記録であり、変換速度を変更する命令ではない。

USBコマンド:

- `sync TOKEN`: 同じtoken、起動ID、現在の端末時刻を返信。計測待ち中も受け付ける。
- `show`: zero/gainと識別情報。
- `tare` / `tare 0`: 全体または内部1チャンネルを16個の有効値で風袋引き。欠測・飽和で更新しない。
- `cal 0 0.980665`: **単体セルへ直接**既知荷重を加えたベンチ試験用。板を組んだ状態の隅の重りをこのコマンドで1セルに割り当てない。板はホストの`force-plate calibrate`を使う。

ホストで保存した較正が分析の基準。ファームのforce_nは参考表示で、rawを消さない。起動時に勝手な風袋引きはしない。
