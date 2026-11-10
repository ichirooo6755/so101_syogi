# XIAO ESP32S3 Sense 将棋カメラ

Espressif Arduino-ESP32 3.3.10 の `CameraWebServer` サンプルを再利用し、XIAO ピン配置、USB CDC の静止画取得、Wi-Fi 任意化を追加しました。追加・変更箇所は `ShogiCamera.ino`、`board_config.h`、`wifi_config.h` です。`app_httpd.cpp` は Apache-2.0 のヘッダーを保持しています。上流のライセンスは同フォルダの LICENSE ファイルを参照してください。

## USB-C 接続（初期設定）

Wi-Fi の設定は不要です。XIAO と Mac を**データ通信対応 USB-C ケーブル**で接続し、Arduino IDE または CLI で次を指定して書き込みます。

初回だけ `wifi_config.example.h` を `wifi_config.h` にコピーします。`wifi_config.h` は接続情報を含み得るため Git には保存しません。

- ボード：`XIAO_ESP32S3`
- PSRAM：`OPI PSRAM`
- USB Mode：`USB-OTG (TinyUSB)`
- USB CDC On Boot：`Enabled`
- 書き込み先：`arduino-cli board list` または Arduino IDE で XIAO と確認したポート。Follower のポートは選ばない。

Arduino IDE なら `ShogiCamera.ino` を開き、上記を選択して書き込みます。CLI の例（`PORT` は XIAO の実際のポートに置換）：

```sh
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi --build-path build/firmware firmware/ShogiCamera
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3:PSRAM=opi --input-dir build/firmware --port PORT firmware/ShogiCamera
```

GUI を再起動し、XIAO の接続先を選んで対局を開始します。USB は要求ごとの JPEG 静止画を繰り返し取得します（フレームレートは未測定）。初期解像度は SVGA (800×600) に設定しています。初期化に失敗する場合、シリアルモニター 115200 baud でエラーを確認できますが、GUI の取得中はモニターを閉じてください。

本機では XIAO が接続されていないため、書き込み・USB 通信・映像の実機試験はしていません。シリアル番号やポート名は接続後に確認が必要です。GUI は XIAO の VID/PID を持つポートのみを候補にします。

## Wi-Fi（任意）

`wifi_config.h` の `SHOGI_WIFI_ENABLED` を 1 にし、`SHOGI_WIFI_SSID` と `SHOGI_WIFI_PASSWORD` を手元で設定し、再ビルド・書き込みします。`SHOGI_AP_MODE` を 0 にすると既存の 2.4 GHz Wi-Fi、1 にすると XIAO 自身のアクセスポイントです。パスワードは 8 文字以上。シリアルモニターに表示される `http://IP/capture` を将棋 GUI の Wi-Fi 欄に入力できます。ESP のウェブ画面は同一ネットワークから認証なしでアクセスできるので、信頼できるネットワークで使ってください。

USB と Wi-Fi の併用時、カメラバッファは共有です。取得失敗時は別のストリームを停止してから再試行してください。両方式とも実機未検証です。

## USB プロトコル

`SHOGI/1 PING\n` に `SHOGI/1 READY\n`、`SHOGI/1 CAPTURE\n` に `SHOGI/1 JPEG <バイト数>\n` と JPEG の生バイト列を返します。エラーは `SHOGI/1 ERROR ...\n`。GUI は長さ・JPEG 終端を確認し、途中で切れた画像を拒否します。
