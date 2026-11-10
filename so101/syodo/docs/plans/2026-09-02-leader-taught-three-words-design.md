# Leader教示による3語実機テンプレート

## 目的

`文字・学習・菅原`だけを、SO-101 Leaderで教えた字形とFollower実測の筆圧で再生する。
汎用の教示学習やPPOは追加せず、既存の実機安全ゲートとdesk fingerprintを使う。

## CLI

- `hardware_write.py teach-reference`: 上下段ごとに`hover/contact/good`をLeaderで教示し、Followerの実関節、荷重、電流を保存する。
- `hardware_write.py record-word 文字|学習|菅原`: 上段、下段を順にLeaderで実書し、Followerの実関節と荷重・電流をテンプレートNPZへ保存する。
- 既存の`hardware_write.py play`は教示NPZも受け付ける。墨なしの空中再生後に止まり、ユーザーが準備してから本書きする。

## データ

基準JSONは上下段の3姿勢、選択した荷重または電流信号、無荷重中央値、MAD、良い圧、過負荷閾値、Leader/Follower USB識別、両較正hash、desk fingerprintを持つ。

教示NPZは`qpos`、空中用`air_qpos`、`pen_down`、`cell_index`、記録信号、文字列、dt、基準・desk fingerprintを持つ。字形は3語以外を拒否する。

## 実機フロー

Followerのトルクを切ったままLeaderとの差を表示し、全関節が近いことを確認してからEnterで追従を開始する。基準教示では直近の安定サンプルの中央値を保存する。文字教示は上段と下段を別々に記録し、間を安全な空中補間でつなぐ。

再生は記録軌道をそのまま字形に使い、教示時の良い圧から外れた分だけ接触→良い圧の関節方向へ小さく補正する。補正量、関節範囲、隣接変化、過負荷を毎点検査する。

## 安全

- USBシリアル、Leader/Follower ID、較正hash、desk fingerprintを照合する。
- 接続直後はFollowerの現在位置を目標にしてからトルクONする。
- 初期姿勢差、5°を超える隣接指令、関節端2°以内、通信失敗、過負荷で中断する。
- Ctrl+Cや教示失敗ではFollowerをトルクOFFにする。
- 本書き前に空中軌道を再生し、ユーザーのEnterなしでは紙へ下ろさない。
- ESP32カメラは未接続なら使わない。接続時の監視は既存`play`と同じ扱いにする。

## テスト

信号選択、pen-down判定、姿勢合わせ拒否、3語制限、fingerprint不一致、空中軌道の範囲・滑らかさ、過負荷退避、中断時トルクOFFを単体テストする。全pytestを通し、実機では基準教示→空中再生→各語2回の順で確認する。
