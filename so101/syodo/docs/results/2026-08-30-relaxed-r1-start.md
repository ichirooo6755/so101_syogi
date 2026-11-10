# relaxed-r1 GateとWindows CUDA r1開始結果（2026-08-30）

## 結論

既存の`strict`と診断専用`relaxed-recovery`を変更せず、新しい`relaxed-r1`だけに
非canonical r1の起動権限を与えた。既存Gate 3の768件を再採点したportable evidenceは
`ready_for_r1=true`、launcher preflightはmodel/config/profile/SHAとCUDAを検証してPASSした。

Windows RTX 4060 Tiで2026-08-30 04:21:39 JSTにchunk 1/10を開始した。r1は実行中で、
48時間上限または2 checkpoint連続非改善のどちらか早い方で停止する。canonicalモデルは
自動置換しない。

## Gate

| 項目 | 値 |
|---|---:|
| profile | `relaxed-r1` |
| Gate 3評価数 | 768 |
| 完筆 | 675/768 |
| 衝突/hard-limit | 0 |
| 消失布白 | 629 |
| beauty mean | 74.843201 |
| pressure p90上限 | 0.78 |
| width ratio範囲 | 0.64〜4.0 |
| calibration | `null` |
| ready_for_r1 | `true` |
| canonical_eligible | `false` |

元shardは
`runs/brush-tilt-gate-recovery-relaxed-20260829/gate3-retest/shard-0..7.json`。
再集約は次のcommandで行い、再シミュレーションはしていない。

```bash
PYTHONPATH=src:. MPLBACKEND=Agg .venv/bin/python -u scripts/run_gate3_recovery.py \
  --gate2-evidence runs/brush-tilt-gate-recovery-relaxed-r1-20260830/gate2-evidence.json \
  --reuse-shards runs/brush-tilt-gate-recovery-relaxed-20260829/gate3-retest \
  --output runs/brush-tilt-gate-recovery-relaxed-r1-20260830/gate3 \
  --workers 1 --threshold-profile relaxed-r1
```

Gate 3再集約は104.18秒。evidenceはrepo内のmodel、Gate 2、upright baselineを相対パスで
記録し、MacからWindowsへ移送後も同じSHA検証を通る。

## 実装とテスト

- 設計: commit `8341153`
- `relaxed-r1`権限、未較正command、portable evidence、隔離run: commit `b941b3b`
- detached workerの`PYTHONPATH`修正: commit `404a08b`
- Windows 32 GiB RAMに合わせたrelaxed BC worker 4: commit `b6b4135`
- focusedテスト: PASS
- 全pytest: **268/268 PASS**
- `.vscode/extensions.json`の既存未コミット変更は含めていない

`relaxed-recovery`は引き続き`ready_for_cuda=false` / `ready_for_r1=false`。
strictは較正schema/fingerprint/SHAと全gate PASSを引き続き必須にする。

## Windows起動

既存のdirtyな`C:\syodo`を変更せず、commit `b6b4135`の独立worktree
`C:\syodo-relaxed-r1`を作成した。GitHub credentialが無人SSHでは利用できなかったため、
Macで作成したGit bundleを転送してcheckoutした。

起動command:

```powershell
cd C:\syodo-relaxed-r1
$env:PYTHONPATH = "C:\syodo-relaxed-r1\src;C:\syodo-relaxed-r1"
C:\syodo\.venv\Scripts\python.exe -u scripts\spawn_windows_recovery.py `
  --physical-gate runs\brush-tilt-gate-recovery-relaxed-r1-20260830\gate3\gate3-evidence.json `
  --deadline "2026-09-01 04:15:00"
```

起動証跡:

- GPU: NVIDIA GeForce RTX 4060 Ti、8,188 MiB
- PyTorch: 2.13.0+cu130、`torch.cuda.is_available() == true`
- launcher PID: 41564
- worker PID: 42808
- chunk 1 child PID: 21736
- phase: `r1 CUDA chunk 1/10`
- 開始: 2026-08-30 04:21:39 JST
- deadline: 2026-09-01 04:15:00 JST
- 出力: `C:\syodo-relaxed-r1\runs\kaisho-yohitsu-brush-tilt-a4-tip-relaxed-r1\chunk-01`
- `run.json`: device `cuda`、`n_envs=8`、timesteps 250,000、BC 180,000・worker 4、
  `pressure_calibration=null`、`require_pressure_calibration=false`
- Mac側開始スナップショット:
  `runs/brush-tilt-gate-recovery-relaxed-r1-20260830/windows-start/`

最初の起動PID 42604は、detached環境の`PYTHONPATH`にrepo rootがなく`import scripts`で
停止した。commit `404a08b`でテスト追加して修正した後のPID 43856は、8 BC workerで
demo収集中にWindowsのcommit memoryを使い切って停止した。32 GiB RAM・空きvirtual
15.29 GiBの実測からrelaxedだけを4 BC workerへ下げ、未完了chunkを
`chunk-01-failed-bcw8-20260830-0417`へ保存してから、commit `b6b4135`で上記PIDを再起動した。
失敗ログは同じrecovery logに保存している。

## 採否

このrunは緩和ゲートによる実験であり、完了しても自動採択しない。checkpointは各250k後の
Gate 1順位で選ぶが、canonical昇格には別途strict Gate 1〜3の全通過が必要となる。
