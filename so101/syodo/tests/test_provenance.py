from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess

from so101_calligraphy.training import provenance


def test_format_command_is_shell_escaped_and_round_trips() -> None:
    argv = (
        "/usr/bin/python3",
        "-m",
        "so101_calligraphy.training.professional",
        "--run-purpose",
        "quality pass; don't expand $HOME",
        "--output",
        "runs/path with spaces",
    )

    command = provenance.format_command(argv)

    assert shlex.split(command) == list(argv)
    assert "'quality pass; don'\"'\"'t expand $HOME'" in command
    assert "'runs/path with spaces'" in command


def test_current_argv_prefers_python_original_argv(monkeypatch) -> None:
    monkeypatch.setattr(provenance.sys, "argv", ["short.py"])
    monkeypatch.setattr(
        provenance.sys,
        "orig_argv",
        ["python3", "-X", "dev", "-m", "package.module", "--flag"],
    )

    assert provenance.current_argv() == (
        "python3",
        "-X",
        "dev",
        "-m",
        "package.module",
        "--flag",
    )


def test_git_metadata_reports_clean_dirty_and_command_failures(
    tmp_path: Path, monkeypatch
) -> None:
    status_output = ""

    def fake_run(command, **_kwargs):
        if command[1:3] == ("rev-parse", "HEAD"):
            return subprocess.CompletedProcess(command, 0, "abc123\n", "")
        if command[1] == "status":
            return subprocess.CompletedProcess(command, 0, status_output, "")
        raise AssertionError(command)

    monkeypatch.setattr(provenance.subprocess, "run", fake_run)
    assert provenance.collect_git_metadata(tmp_path) == {
        "commit": "abc123",
        "dirty": False,
    }

    status_output = " M tracked.py\n?? new.py\n"
    assert provenance.collect_git_metadata(tmp_path)["dirty"] is True

    def failed_run(*_args, **_kwargs):
        raise OSError("git is unavailable")

    monkeypatch.setattr(provenance.subprocess, "run", failed_run)
    assert provenance.collect_git_metadata(tmp_path) == {
        "commit": None,
        "dirty": None,
    }


def test_linux_cpu_parser_handles_common_cpuinfo_shapes() -> None:
    assert (
        provenance.parse_linux_cpu_model(
            "processor : 0\nvendor_id : GenuineIntel\nmodel name : Test CPU 9000\n"
        )
        == "Test CPU 9000"
    )
    assert provenance.parse_linux_cpu_model("Hardware : Example SoC\n") == "Example SoC"
    assert provenance.parse_linux_cpu_model("bogus input") is None


def test_record_run_writes_all_handoff_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        provenance,
        "collect_git_metadata",
        lambda _cwd: {"commit": "deadbeef", "dirty": True},
    )
    monkeypatch.setattr(
        provenance,
        "collect_system_metadata",
        lambda: {
            "os": "TestOS",
            "os_release": "1.0",
            "os_version": "build",
            "architecture": "test64",
            "cpu": "Test CPU",
            "cpu_count": 8,
            "ram_bytes": 16 * 1024**3,
        },
    )
    started_at = datetime(2026, 8, 16, 8, 30, tzinfo=timezone.utc)
    argv = ["python3", "train.py", "--purpose", "全常用漢字を改善"]
    output = tmp_path / "run"

    metadata = provenance.record_run(
        output,
        purpose="全常用漢字を改善",
        parent_model=tmp_path / "parent model.zip",
        started_at=started_at,
        cwd=tmp_path,
        argv=argv,
        extra={"seed": 17},
    )

    assert (output / "command.txt").read_text(encoding="utf-8") == (
        shlex.join(argv) + "\n"
    )
    saved = json.loads((output / "run.json").read_text(encoding="utf-8"))
    assert saved == metadata
    assert saved["purpose"] == "全常用漢字を改善"
    assert saved["started_at"] == "2026-08-16T08:30:00+00:00"
    assert saved["cwd"] == str(tmp_path.resolve())
    assert saved["parent_model"].endswith("parent model.zip")
    assert saved["git"] == {"commit": "deadbeef", "dirty": True}
    assert saved["system"]["ram_bytes"] == 16 * 1024**3
    assert saved["extra"] == {"seed": 17}

    status = (output / "status.md").read_text(encoding="utf-8")
    assert "Status: running" in status
    assert "Purpose: 全常用漢字を改善" in status
    assert "Git commit: `deadbeef`" in status
    assert f"    {shlex.join(argv)}" in status


def test_status_markdown_can_record_result_and_next_action(tmp_path: Path) -> None:
    metadata = {
        "purpose": "smoke test",
        "started_at": "2026-08-16T08:30:00+09:00",
        "command": "python train.py",
        "cwd": "/workspace",
        "parent_model": None,
        "git": {"commit": None, "dirty": None},
        "system": {"os": "Linux", "os_release": "6", "cpu": "CPU", "ram_bytes": 8},
    }

    path = provenance.write_status_markdown(
        tmp_path,
        metadata,
        status="completed",
        summary="All checks passed.",
        next_action="Promote the checkpoint.",
    )

    text = path.read_text(encoding="utf-8")
    assert "Status: completed" in text
    assert "## Result\n\nAll checks passed." in text
    assert "## Next action\n\nPromote the checkpoint." in text
