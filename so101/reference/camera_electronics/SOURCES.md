# SO101 カメラ・筆圧電子部品の参照

確認日: 2026-10-27。購入や実機への通電は行っていない。

## XIAO ESP32S3 Sense

- Seeed公式仕様・CAD: https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/
- 公式STEP ZIP: https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/seeed-studio-xiao-esp32s3-sense-3d_model.zip
- 拡張基板上面DXF: https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_ExpBoard_v1.0_top.dxf
- 秋月取扱品: https://akizukidenshi.com/catalog/g/g118079/
- カメラ使用例: https://wiki.seeedstudio.com/xiao_esp32s3_camera_usage/

公式仕様の基板外形21 x 17.8 mm、Senseの実装高さ15 mm。
保存した2023年のSTEPでは基板20.955 x 17.78 mm、USBを含む長辺24.363 mm、
基板裏面からレンズまで13.96 mm。STEPは古いカメラの参照であり、現行品の
OV3660/OV5640レンズの実形状を保証しない。レンズ周りを囲わない設計とする。
基板厚はSTEPの1.25 mmを参照し、保持部は余裕を設ける。

## AE-HX711-SIP

- 秋月: https://akizukidenshi.com/catalog/g/g112370/
- 原本: `../datasheets/AE-HX711-SIP_web_20231219.pdf`
- PDF図面: 基板30 x 22 mm。5 V (4.5–5.5 V)、10 sps。
- CN1: VDD / DAT / CLK / INPB / INNB / GND。
- CN2: AVDD (励起+) / GND (励起-)。
- CN3: INNA (信号-) / INPA (信号+)。

この完成基板の回路ではHX711のDVDDとVSUPはVDDへ接続され、RATEはGND。
ESP32へDATを5 Vのまま直結しない。CLKも5 V側入力規格を満たすレベル変換を用いる。
基板を3.3 Vで動作保証すると扱わない。標準状態の10 spsを80 spsへソフトだけで
変更できるとは扱わない。サーボ電源を直接5 V入力へ接続しない。

## レベル変換の取付予約

- 千石 BOB-19626: https://www.sengoku.co.jp/mod/sgk_cart/detail.php?code=EEHD-5XTN
- SparkFun: https://www.sparkfun.com/sparkfun-level-shifter-8-channel-txs0108e.html
- 外形図: https://cdn.sparkfun.com/assets/e/9/f/d/2/TXS01018E-Dimensions.png
- 設計原本: https://github.com/sparkfun/8_channel_level_shifter_TXS0108E

外形1.10 x 0.50 inch = 27.94 x 12.70 mm。2チャンネルをDAT/CLKに使い、
VCCA=3.3 V、VCCB=5 V、GNDを共通にする。OEの起動処理・配線は製品回路も確認する。
短い配線を使う。カメラ・Wi-Fiと同時動作するファームウェアは別途実装・試験が必要。

## 取付元の由来

SO101のカメラ用六角ナット穴の元設計:
https://github.com/TheRobotStudio/SO-ARM100/blob/main/Optional/SO101_Wrist_Cam_Hex-Nut_Mount_32x32_UVC_Module/README.md

ただし、今回のV8筆ユニットと通常頭M3の組合せでは、ねじ頭が回転する部品１に
干渉することを一時BRepで確認した。元設計に穴があることだけを適合根拠にしない。
