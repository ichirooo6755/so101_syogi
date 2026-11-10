# relaxed-r1 Gate 設計

## 目的

`relaxed-recovery`で得た実測範囲を、Windows CUDA r1を開始できる明示的な
非canonical実験ゲートとして再利用する。既存の`strict`と診断専用
`relaxed-recovery`の意味、閾値、canonicalモデルは変更しない。

## 選択した方式

新しい`relaxed-r1`プロファイルを追加する。数値閾値は
`relaxed-recovery`と同じにし、違いはGate 2のCUDA権限とGate 3のr1権限だけとする。
証跡と学習の設定を一致させるため、現在のGate 1〜3と同じく圧力較正なしで実行する。

既存プロファイルを直接変更する方式は、診断PASSと学習権限の意味を混ぜるため採用しない。
strict閾値を下げる方式も、release判定を壊すため採用しない。

## 境界

- `strict`: 従来どおり較正JSONと全fingerprint/SHAを必須にする。
- `relaxed-recovery`: 従来どおり診断専用で、CUDA/r1権限を与えない。
- `relaxed-r1`: 未較正を明示し、Gate 3のmodel/config/profile/SHAと全gate PASSを検証して
  r1を許可する。
- relaxed r1の出力、PID、log、status、selectionは`*-relaxed-r1`系へ隔離する。
- relaxed r1はcanonicalへ自動採択しない。strict再評価を通らない限り採択候補にも昇格しない。

## 学習と停止

stage 8、CUDA、8環境、最大2.5M stepを250kずつ実行する。最初のchunkだけpolicy-only
warm startとBCを行い、以降は選択中のbest checkpointから継続する。各chunk後に同じ
`relaxed-r1`・未較正条件のGate 1 screenを行い、完筆と衝突条件を満たしたうえで順位が
改善したcheckpointだけを次の親にする。2 checkpoint連続で改善しなければ停止する。

## 証跡と移送

Gate 3 evidence内のrepo配下パスは相対パスで保存し、Macで再採点した証跡をWindowsの
`C:\syodo`で同じ相対位置へ配置できるようにする。Windows起動時にCUDA、空き容量、
model SHA、config SHA、profile一致を検証し、PID、GPUスナップショット、progressを保存する。

## テスト

- `relaxed-recovery`が引き続き権限を持たないこと。
- `relaxed-r1`だけが緩和閾値PASS時にGate 2/Gate 3権限を持つこと。
- strictは較正必須、`relaxed-r1`は`calibration=null`のみ許容すること。
- 未較正r1 commandに較正引数がなく、CUDA・8環境・250k chunkを維持すること。
- relaxed runの出力がstrict runと分離されること。

