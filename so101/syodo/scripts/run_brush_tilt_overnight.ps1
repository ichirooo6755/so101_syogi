# 筆傾斜 + 起筆 lean を Windows 最速設定で朝 10 時まで回す。
# 親: sansetsu。hard-mining なし。C ゲートは朝の全数評価。
$ErrorActionPreference = "Stop"
Set-Location C:\syodo

$deadline = [datetime]::ParseExact(
    "2026-08-22 10:00:00",
    "yyyy-MM-dd HH:mm:ss",
    [System.Globalization.CultureInfo]::InvariantCulture
)
$run = "kaisho-yohitsu-brush-tilt"
$out = "runs\$run"
$log = "runs\$run-train.log"
$master = "runs\$run-overnight.log"
$pidFile = "runs\$run.pid"
$parent = "runs\kaisho-yohitsu-sansetsu\final_model.zip"
$font = "C:\syodo\fonts\A-OTF-KaishoMCBK1Pro-DeBold.otf"

New-Item -ItemType Directory -Force -Path $out, "runs" | Out-Null
function Log($msg) {
    $line = "==== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg ===="
    Add-Content -Path $master -Value $line
    Write-Host $line
}

if (-not (Test-Path $parent)) { throw "missing parent $parent" }
if (-not (Test-Path $font)) { throw "missing font $font" }

# AC 接続時はスリープしない（権限が無ければ学習は続ける）
foreach ($args in @(
    @("/change", "standby-timeout-ac", "0"),
    @("/change", "monitor-timeout-ac", "0"),
    @("/change", "hibernate-timeout-ac", "0")
)) {
    & powercfg @args 2>$null
}

$env:PYTHONPATH = "src"
$env:PYTHONUNBUFFERED = "1"
$env:MPLBACKEND = "Agg"

$py = ".\.venv\Scripts\python.exe"
$args = @(
    "-u", "-m", "so101_calligraphy.training.professional",
    "--ablation", "all",
    "--run-purpose", "brush-tilt EE + entry_lean=1.0 re-adapt from sansetsu (stage 5-8)",
    "--initial-model", $parent,
    "--exemplar-font", $font,
    "--start-stage", "5", "--end-stage", "8",
    "--timesteps", "1300000", "--kana-timesteps", "1300000",
    "--bc-steps", "120000", "--kana-bc-steps", "120000", "--bc-epochs", "5",
    "--n-envs", "8", "--bc-workers", "8",
    "--n-steps", "2048", "--batch-size", "1024",
    "--learning-rate", "3e-4",
    "--device", "cpu", "--allow-gate-failure",
    "--stage-eval-size", "64", "--eval-limit", "128",
    "--output", $out,
    "--seed", "91"
)

$errLog = "runs\$run-train.err.log"
Log "training start deadline=$deadline n_envs=8"
$proc = Start-Process -FilePath $py -ArgumentList $args -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $log -RedirectStandardError $errLog
$proc.Id | Set-Content $pidFile
Log "pid=$($proc.Id)"

while (-not $proc.HasExited) {
    if ((Get-Date) -ge $deadline) {
        Log "deadline reached; stopping pid=$($proc.Id)"
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Get-CimInstance Win32_Process | Where-Object {
            $_.ParentProcessId -eq $proc.Id -or $_.CommandLine -match "so101_calligraphy.training.professional"
        } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        break
    }
    Start-Sleep -Seconds 30
}

if ($proc.HasExited) {
    Log "training exited code=$($proc.ExitCode)"
} else {
    Log "training stopped by deadline"
}

$model = "$out\final_model.zip"
$left = [int]($deadline - (Get-Date)).TotalSeconds
if ((Test-Path $model) -and $left -gt 3000) {
    $evalDir = "runs\$run-joyo-eval"
    Log "full joyo eval -> $evalDir ($left s left)"
    & $py -u scripts\evaluate_joyo_shards.py --model $model --output $evalDir --shards 8 --device cpu --seed 91 --exemplar-font $font *>> $log
    Log "eval done"
} else {
    Log "skip full eval (model exists=$(Test-Path $model) left=${left}s)"
}
Log "overnight wrapper done"
