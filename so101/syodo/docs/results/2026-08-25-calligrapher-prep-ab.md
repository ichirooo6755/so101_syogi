# 書家レベル回復の下準備 A/B（2026-08-25）

Windows の `brush-tilt-a4-tip-r1` 全数評価は動かしたまま、Mac で expert-only だけ測った。9 条件×60 ケースの圧掃引はしていない。

数値の正本: [`runs/calligrapher-prep-2026-08-25/summary.json`](../../runs/calligrapher-prep-2026-08-25/summary.json)

ホバー修正後の再測: [`runs/calligrapher-prep-2026-08-25/gate-after-hover-fix.json`](../../runs/calligrapher-prep-2026-08-25/gate-after-hover-fix.json)

## 分かったこと

1. IK expert は A4 の layout-0 なら代表 10 字を完筆できる。いまの PPO が 40,000 step で落ちる主因は方策。
2. その expert でも beauty 平均は約 72。ここから hard-mining しても 85 には届かない。
3. 「一」layout-3 の beauty 0 は IK 不足ではなく、接地を失った送筆点が 4.5 mm ゲートの直前でホバーしていた。失接触後は姿勢タスクを外して位置 DLS に戻すと **60/60 完筆**。飛 L2/L3 も同じ修正で完筆。
4. 台座を前後に動かすと、直した枠の代わりに別枠が壊れる。既定 x=30 mm を維持。
5. 旧 60 mm 枠は、現行の穂先圧モデルでは layout-0 より幅・圧・布白が悪い。
6. 完筆ゲートは通過。残るのは圧・幅・布白・端点。

## 次の学習に入れる条件

- 親 ZIP `brushmark-joyo` が無い。sansetsu は触らない。
- `ready_for_cuda`（圧・幅・布白・端点）まで CUDA しない。
- 未完筆字の stage 9 hard-mining を次ラウンドに使わない。
