# relaxed-r1 Gate 実装計画

1. `diagnose_stroke_merge.py`へ`relaxed-r1`を追加し、テストでstrict、診断専用relaxed、
   r1許可relaxedの権限を固定する。
2. `run_gate3_recovery.py`で`relaxed-r1`をr1許可プロファイルとしてmergeし、
   canonical可否と診断専用フラグを分け、repo内パスを相対化する。
3. `search_gate_recovery.py`の診断commandを較正任意にし、学習後screenで証跡と同じ
   未較正設定を使用できるようにする。
4. `spawn_windows_recovery.py`でstrictの較正検証を保持しつつ、`relaxed-r1`の
   `calibration=null`を許可する。未較正chunk command、profile伝播、隔離run名を追加する。
5. focused pytest、全pytestを実行する。
6. 既存relaxed shardを`relaxed-r1`として再採点し、portable Gate 3 evidenceを生成する。
7. commit/push後、Windowsへbranchとignored evidenceを同期し、preflightを通して
   detached CUDA r1を起動する。PID、CUDA名、status、最初のprogressを確認する。
8. README、結果報告、training台帳へ実装SHA、完全CLI、Gate証跡、Windows起動証跡を残す。

