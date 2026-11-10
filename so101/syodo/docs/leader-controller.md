# Xbox コントローラーで Leader を操作

`Leaderコントローラー.command` をダブルクリックして起動します。LeRobot 実機環境 `~/Documents/lerobot-hw/.venv` と、較正済みの `syodo_leader` が必要です。Xbox コントローラーを macOS に接続し、Chrome または Gamepad API 対応ブラウザーでボタンを一度押してください。腕の周囲を空け、腕を支えられる状態で「Leader に接続」→ RB を離して「操作開始」→ RB を押しながら少しずつ操作します。画面に各操作を表示します。

接続先は、実機の 6 個の較正情報と `syodo_leader` の一致を確認した `/dev/cu.usbmodem5B7B0136431` に限定します。このポート名は以前 Follower に使われていたため、接続する腕を入れ替えた際は確認が必要です。較正とモーターの一致、位置制御モード、開始位置を確認し、較正範囲の内側で低速の小さな相対指令を出します。ID5（手首回転）は指令もトルク設定も変更しません。Follower は操作しません。

RB を放すと現在位置を保持します。画面を隠したとき、入力通信が 0.3 秒途絶えたとき、コントローラーが外れたときは再度「操作開始」が必要です。「停止」は保持、「切断」は保持設定のまま通信を切ります。電源断や通信障害では保持できない場合があり、ソフトウェア停止は物理的な非常停止ではありません。腕が落下しないよう支えてから作業してください。ほかのプログラムと同時に Leader ポートを使わないでください。

ブラウザーの [Gamepad API](https://www.w3.org/TR/gamepad/) の標準配置を使い、モーター通信には OSS の [LeRobot](https://github.com/huggingface/lerobot) を使用しています。Xbox 操作例の参考: [XLeRobot](https://github.com/Vector-Wangel/XLeRobot/blob/main/software/examples/5_xlerobot_teleop_xbox.py)。入力・較正・実機の向きは環境ごとに異なるため、最初は空中で各関節を短く動かして確認してください。
