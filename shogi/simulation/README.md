# SO-101 将棋駒：MuJoCo 試行と模倣学習

これは物理シミュレーションの研究用プロトタイプです。GUI の実機経路は `--plan-only` の経由点だけを使い、物理ロールアウトは裏の確認用です。人とロボットが盤を挟んで座り、人は自分の手を指し、ロボットは AI の手を指す想定です。GUI の「コマを自動で動かす」は盤面の駒をすぐに進め、逆運動学の経由点を Follower へ渡します。経由点に届かないときは高さを下げます。隣の駒との接触はアームだけを失敗にし、静止中の駒同士は数えません。成りは ID5 を 180° 回して配線のため開始角度へ巻き戻します。5 軸では盤上で駒を裏向きのまま置けないので、成りは局面側に記録します。ID5 の可動は 365° です。駒取りは相手駒→駒台、自駒→移動先を続けて再生します。打ちは駒台スロットから置きます。シミュレーション側の駒取りプレビューは今も別試行です。

## 何を試すか

既存の [so101-manipulation-eval](https://github.com/FERBIN12/so101-manipulation-eval) の SO-101 ジョー・接触モデル、姿勢の逆運動学、接触監査を再利用しています。将棋駒は自由に動く五角形の剛体で、接近 → 両爪で閉じる → 浮かせる → 運ぶ → 置く → 離す、を関節の位置制御で行います。試行中に駒をグリッパーに固定したり座標を上書きしたりしません。GUI では局面にある他の駒を固定障害物として置きます。学習用データの試行では移動元の近傍に仮の固定障害物を置きます。

便宜上、盤は 330×360×12 mm、駒は 23×27×7 mm・4 g、爪のすべり摩擦係数は再利用元の仮値 2.0 とします。駒との接触は再利用元の近似パッドで計算し、爪メッシュそのものと駒の接触は除外されています。これらは使用者の実物を測った値ではありません。GUI では現在の局面から他の駒の位置と向きを置きますが、他の駒は動かない障害物で、大きさと形は共通の仮定です。盤面はロボットの正面から奥に +X とし、先手・後手の切り替えに応じて盤の向きを変え、ロボット側の駒は初期状態で +X を向きます。駒取りの試行では空の駒台を仮定します。カメラ・配線・駒台上の他の駒は含みません。

成功には、両爪で同時に挟みながら 20 mm 以上浮かせ、目標から 8 mm 以内に静かに置くことを求めます。成らない手は初期の表裏・向きを 15° 以内、成る手は表のまま ID5 が巻き戻っていることが条件です。動作中にアームが盤や隣の駒に触れた場合は失敗にします。これはシミュレーション内部の判定です。実物のグリッパー・摩擦・位置精度を保証しません。

## 動かし方

Mac では同梱の `.venv-sim` を使えます。別に作る場合は Python 3.12 を使用し、GUI の `.venv` とは分けてください。

```sh
python3.12 -m venv .venv-sim
.venv-sim/bin/pip install -r simulation/requirements.txt
.venv-sim/bin/python simulation/pick_place.py
.venv-sim/bin/python simulation/reachability.py
.venv-sim/bin/python -m unittest discover -s simulation -p 'test_*.py' -v
```

単一試行の JSON は `simulation/runs/latest.json` に記録されます。`--source X Y --target X Y` はモデル基準のメートル座標、`--yaw-deg 180` はロボットから見て反対向きの駒です。出力の `success` は上記の仮定下の判定であり、GUI の仮想盤から実盤への較正値ではありません。到達可能性マップは固定の初期姿勢による静的 IK のみで、干渉や動作を検査しません。

`--jaw-friction 0.3` のように、爪の摩擦の仮定を変えられます。`runs/friction_sensitivity.json` は以前の盤の向きで試した記録であり、現在の対面配置での検証結果ではありません。

## 学習と評価

`train_imitation.py` は、逆運動学で成功したシミュレーションだけから関節指令をまねる教師あり学習を行います。`train_waypoints.py` は、同じ教示から接近・把持・移動などの目標関節姿勢を学び、滑らかな時間経過に沿って動かします。学習モデルを試すときは逆運動学へのフォールバックを使いません。

両モデルは画像を見ません。シミュレーター内で与えられる駒の正確な位置と、外から決めた動作段階を入力します。学習は盤の一部の近傍で 1 マス動かす限定的な条件です。現状の学習結果をカメラベースの実機制御や盤全体への対応として扱えません。結果は各 `runs/*/report.json` に記録します。GUI の自動着手は学習モデルではなく逆運動学です。実機チェックは空撃ちが既定です。

学習の教示は成らない手だけを使います。成りは位相が増えて目標姿勢学習と混ざるためです。成りの ID5 回転は単体テストと GUI の逆運動学で確認します。GUI の自動着手は学習モデルではなく逆運動学です。教示の配置には最大 12 mm のずれを足しています。8 コア再学習（`runs/imitation_id5`、70 秒）の教示は 236/320、密な模倣の未見は 0/16（接近で盤に触れる）。同じ教示からの目標姿勢学習（`runs/waypoint_id5`）は未見 14/16 で、失敗 2 件は教示側も失敗しています。朝 7 時までの追加学習は 2026-11-01 7:00 JST に止まりました。`runs/overnight/` は 375 ラウンド、経由点まで残ったのは 366、未見の最良は 10/12 です。教示側も 10/12 なので、学習側が教示を超えたラウンドはありません。

GUI の盤は長辺配置です。人とロボットが 330 mm の筋方向で向かい合い、段は左右です。中心は X=0.19 m。24 cm だと 7一→6二が届かず、20 cm だと 8八への取りが届かない。19 cm ではどちらも浮く。9筋は届かない。中央筋では移動・取り・打ち・成りの物理が成功する。傾き IK は空振りするので使わない。学習用の教示座標は従来どおり数字の XY で、この向き変更の影響を受けません。

対面（短辺）配置の旧記録：仮条件の 160 配置を逆運動学で試し、成功した 100 件を目標姿勢の模倣学習に使用。未使用の 24 配置では、ロボットの駒の向きで学習モデル 17/24・逆運動学 19/24、反対向きで 18/24・20/24。教示の盤中心は X=0.245 m、評価は X=0.265 m。詳細は `runs/waypoint_opposing/both_sides_report.json`。短辺・中心 0.265 m では全体 52/81、歩 6/9。`runs/opposing_board_comparison.json` は短辺比較です。

```sh
.venv-sim/bin/python simulation/compare_board_placement.py
.venv-sim/bin/python simulation/evaluate_waypoints.py
```

上の評価コマンドは保存した対面配置のデータと学習済みモデルを読みます。教示とモデルを作り直す場合は次を実行します。

教示の物理試行は CPU コア数まで並列します。この Mac は 8 コアなので `--jobs 8` が上限です。PyTorch も同じコア数を使います。スリープさせないときは `caffeinate` を付けます。

```sh
caffeinate -dim .venv-sim/bin/python simulation/train_imitation.py --demos 320 --eval 16 --steps 2000 --board-x 0.265 --jobs 8 --out simulation/runs/imitation_id5
.venv-sim/bin/python simulation/train_waypoints.py --data simulation/runs/imitation_id5/demonstrations.npz --out simulation/runs/waypoint_id5 --steps 5000 --heldout-offset 3000 --eval-board-x 0.265
.venv-sim/bin/python simulation/train_imitation.py --demos 160 --eval 1 --steps 200 --board-x 0.245 --out simulation/runs/imitation_opposing
.venv-sim/bin/python simulation/train_waypoints.py --data simulation/runs/imitation_opposing/demonstrations.npz --out simulation/runs/waypoint_opposing --steps 5000 --heldout-offset 3000 --eval-board-x 0.265
.venv-sim/bin/python simulation/evaluate_waypoints.py
```

## 実機へ進むために

実盤・駒を計測し、盤と手首カメラの位置をロボット座標に較正します。駒が隠れた場合や把持に失敗した場合の検出・再撮影、盤上の他の駒やカメラ・配線の干渉、全マスと駒台の到達性を確認する必要があります。既存の Follower の安全制御と較正値に合わせ、軌道検査・空中動作・人の確認を経てから、実際の駒で段階的に検証します。現在のモデルと実機の関節位置・方向の対応も未検証です。

元の実装は `vendor/so101-manipulation-eval` のコミット `b02b8b2e300733dbe76cead4f3a57425c37955fe`、ライセンスは [UPSTREAM_LICENSE.txt](UPSTREAM_LICENSE.txt) および [SO_ARM100_APACHE-2.0.txt](SO_ARM100_APACHE-2.0.txt) を参照してください。
