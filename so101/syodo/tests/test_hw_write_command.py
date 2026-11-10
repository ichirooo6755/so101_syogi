"""CLI contract for the one-command hardware writer."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "scripts/hw-write"


def _fake_python(tmp_path: Path) -> tuple[Path, Path]:
    capture = tmp_path / "calls.jsonl"
    executable = tmp_path / "python"
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['HW_WRITE_CAPTURE'], 'a', encoding='utf-8') as f:\n"
        "    f.write(json.dumps(sys.argv[1:], ensure_ascii=False) + '\\n')\n"
        "if len(sys.argv) > 3 and sys.argv[2:4] == ['trace', '🙂']:\n"
        "    raise SystemExit(3)\n"
        "if os.environ.get('HW_WRITE_AUDIT_FAIL') and sys.argv[1].endswith('audit_hardware_trace.py'):\n"
        "    raise SystemExit(5)\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable, capture


def _run(tmp_path: Path, *args: str) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    fake, capture = _fake_python(tmp_path)
    env = {
        **os.environ,
        "SYODO_PYTHON": str(fake),
        "LEROBOT_HW_PYTHON": str(fake),
        "SYODO_RUN_ROOT": str(tmp_path / "runs"),
        "HW_WRITE_CAPTURE": str(capture),
    }
    result = subprocess.run(
        [str(COMMAND), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    calls = (
        [json.loads(line) for line in capture.read_text(encoding="utf-8").splitlines()]
        if capture.exists()
        else []
    )
    return result, calls


def test_hw_write_requires_text(tmp_path: Path) -> None:
    result, calls = _run(tmp_path)
    assert result.returncode == 2
    assert "使い方" in result.stderr
    assert calls == []


def test_hw_write_rejects_empty_text(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "")
    assert result.returncode == 2
    assert "1〜4文字" in result.stderr
    assert calls == []


def test_hw_write_rejects_more_than_four_characters_before_commands(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "春夏秋冬春")
    assert result.returncode == 2
    assert "1〜4文字" in result.stderr
    assert calls == []


def test_hw_write_stops_before_hardware_when_trace_generation_fails(
    tmp_path: Path,
) -> None:
    result, calls = _run(tmp_path, "🙂")
    assert result.returncode == 3
    assert len(calls) == 1
    assert calls[0][1:3] == ["trace", "🙂"]


@pytest.mark.parametrize("word", ("文", "文字", "文字列", "春夏秋冬"))
def test_hw_write_generates_fresh_trace_and_forwards_play_options(
    tmp_path: Path, word: str
) -> None:
    result, calls = _run(tmp_path, word, "--camera-url", "http://camera")
    assert result.returncode == 0, result.stderr
    assert len(calls) == 5
    trace_call, audit_call, simulation_call, groom_call, play_call = calls
    assert trace_call[1:3] == ["trace", word]
    trace_path = Path(trace_call[trace_call.index("--out") + 1])
    assert trace_path.name == "trace.npz"
    assert trace_path.parent.parent == tmp_path / "runs"
    assert Path(audit_call[0]).name == "audit_hardware_trace.py"
    assert audit_call[1:] == [str(trace_path), "--output", str(trace_path.parent / "preflight.json")]
    assert Path(simulation_call[0]).name == "simulate_hardware_brush.py"
    assert simulation_call[1:] == [
        str(trace_path),
        "--out",
        str(trace_path.parent / "brush-simulation"),
        "--speed",
        "1.5",
    ]
    assert groom_call[1:] == ["prepare-groom"]
    assert play_call[1:3] == ["play", str(trace_path)]
    assert play_call[play_call.index("--speed") + 1] == "1.5"
    assert play_call[play_call.index("--stride") + 1] == "1"
    assert play_call[play_call.index("--hold-s") + 1] == "0"
    assert play_call[play_call.index("--approach-s") + 1] == "6"
    assert play_call[play_call.index("--log") + 1] == str(trace_path.parent / "write.csv")
    assert play_call[-2:] == ["--camera-url", "http://camera"]


def test_prepare_only_runs_no_play_command(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "文字", "--prepare-only")
    assert result.returncode == 0, result.stderr
    assert len(calls) == 4
    assert all("play" not in call for call in calls)
    assert "送信前検証" in result.stdout


def test_failed_fk_audit_prevents_motor_play(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HW_WRITE_AUDIT_FAIL", "1")
    result, calls = _run(tmp_path, "文字")
    assert result.returncode == 5
    assert len(calls) == 2
    assert all("play" not in call for call in calls)


def test_hw_write_uses_playback_speed_for_brush_simulation(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "文", "--speed", "0.75")
    assert result.returncode == 0, result.stderr
    simulation_call = next(call for call in calls if call[0].endswith("simulate_hardware_brush.py"))
    assert simulation_call[simulation_call.index("--speed") + 1] == "0.75"


def test_hw_write_without_play_options_is_valid_on_macos_bash(tmp_path: Path) -> None:
    result, calls = _run(tmp_path, "文")
    assert result.returncode == 0, result.stderr
    assert calls[-1][1] == "play"
