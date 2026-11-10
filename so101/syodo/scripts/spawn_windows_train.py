"""Detach professional PPO on Windows so SSH logout does not kill it."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = "kaisho-yohitsu-brush-tilt"
OUT = ROOT / "runs" / RUN
LOG = ROOT / "runs" / f"{RUN}-train.log"
PIDFILE = ROOT / "runs" / f"{RUN}.pid"
PARENT = ROOT / "runs" / "kaisho-yohitsu-sansetsu" / "final_model.zip"
FONT = ROOT / "fonts" / "A-OTF-KaishoMCBK1Pro-DeBold.otf"
EVAL_OUT = ROOT / "runs" / f"{RUN}-joyo-eval"
EVAL_LOG = ROOT / "runs" / f"{RUN}-joyo-eval.log"

CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000
CREATE_BREAKAWAY_FROM_JOB = 0x01000000
DETACH = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW | CREATE_BREAKAWAY_FROM_JOB


def _alive(pid: int) -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    return str(pid) in result.stdout


def wait_and_eval(train_pid: int) -> None:
    """After PPO exits, run C-gate full joyo eval if final_model exists."""
    EVAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    log = EVAL_LOG.open("a", encoding="utf-8")
    log.write(f"# wait-eval pid={train_pid} {datetime.now().isoformat()}\n")
    log.flush()
    while _alive(train_pid):
        time.sleep(30)
    final = OUT / "final_model.zip"
    if not final.is_file():
        log.write(f"no {final}; skip eval\n")
        return
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["MPLBACKEND"] = "Agg"
    cmd = [
        sys.executable,
        "-u",
        str(ROOT / "scripts" / "evaluate_joyo_shards.py"),
        "--model",
        str(final),
        "--output",
        str(EVAL_OUT),
        "--shards",
        "8",
        "--device",
        "cpu",
        "--seed",
        "91",
        "--exemplar-font",
        str(FONT),
    ]
    log.write("starting joyo eval\n")
    log.flush()
    subprocess.run(cmd, cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT)


def main() -> None:
    if not PARENT.is_file():
        raise SystemExit(f"missing parent {PARENT}")
    if not FONT.is_file():
        raise SystemExit(f"missing font {FONT}")
    OUT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["MPLBACKEND"] = "Agg"
    cmd = [
        sys.executable,
        "-u",
        "-m",
        "so101_calligraphy.training.professional",
        "--ablation",
        "all",
        "--run-purpose",
        "brush-tilt + entry_lean=1.0; kanji-heavy 4/6/11M, kana 1.5M from sansetsu",
        "--initial-model",
        str(PARENT),
        "--exemplar-font",
        str(FONT),
        "--start-stage",
        "5",
        "--end-stage",
        "8",
        "--timesteps",
        "4000000",
        "--kana-timesteps",
        "1500000",
        "--elementary-timesteps",
        "6000000",
        "--joyo-timesteps",
        "11000000",
        "--bc-steps",
        "120000",
        "--kana-bc-steps",
        "120000",
        "--bc-epochs",
        "5",
        "--n-envs",
        "8",
        "--bc-workers",
        "8",
        "--n-steps",
        "2048",
        "--batch-size",
        "1024",
        "--learning-rate",
        "2e-4",
        "--device",
        "cuda",
        "--allow-gate-failure",
        "--stage-eval-size",
        "64",
        "--eval-limit",
        "128",
        "--output",
        str(OUT),
        "--seed",
        "91",
    ]
    log = LOG.open("w", encoding="utf-8")
    log.write(
        f"# spawned {datetime.now().isoformat()} "
        "4/6/11M kanji, kana 1.5M cuda; eval after; deadline 2026-08-22 10:00 JST\n"
    )
    log.flush()
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        creationflags=DETACH,
    )
    PIDFILE.write_text(str(proc.pid), encoding="ascii")
    subprocess.Popen(
        [sys.executable, "-u", str(Path(__file__).resolve()), "--wait-eval", str(proc.pid)],
        cwd=str(ROOT),
        env=env,
        creationflags=DETACH,
    )
    print(f"spawned pid={proc.pid} log={LOG}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--wait-eval":
        wait_and_eval(int(sys.argv[2]))
    else:
        main()
