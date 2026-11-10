"""Safe, standard-library-only provenance recording for training runs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import tempfile
from typing import Any


JsonMapping = Mapping[str, Any]


def current_argv() -> tuple[str, ...]:
    """Return the fullest command line Python exposes for this process."""

    original = getattr(sys, "orig_argv", None)
    argv = original if original else sys.argv
    return tuple(str(part) for part in argv)


def format_command(argv: Sequence[str] | None = None) -> str:
    """Render an argv sequence as a copy-pasteable POSIX shell command."""

    parts = current_argv() if argv is None else tuple(str(part) for part in argv)
    return shlex.join(parts)


def _safe_capture(
    command: Sequence[str],
    *,
    cwd: str | Path | None = None,
    timeout: float = 5.0,
) -> str | None:
    """Capture a short command without allowing its failure to escape."""

    try:
        completed = subprocess.run(
            tuple(str(part) for part in command),
            cwd=None if cwd is None else os.fspath(cwd),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def collect_git_metadata(cwd: str | Path | None = None) -> dict[str, Any]:
    """Collect commit and dirty state, returning unknown values on failure."""

    working_directory = Path.cwd() if cwd is None else Path(cwd)
    commit = _safe_capture(("git", "rev-parse", "HEAD"), cwd=working_directory)
    status = _safe_capture(
        ("git", "status", "--porcelain", "--untracked-files=normal"),
        cwd=working_directory,
    )
    return {
        "commit": commit,
        "dirty": None if status is None else bool(status),
    }


def parse_linux_cpu_model(cpuinfo: str) -> str | None:
    """Extract the first useful CPU model from Linux ``/proc/cpuinfo``."""

    preferred = ("model name", "hardware", "processor")
    fields: dict[str, str] = {}
    for line in cpuinfo.splitlines():
        key, separator, value = line.partition(":")
        if separator and value.strip():
            fields.setdefault(key.strip().lower(), value.strip())
    return next((fields[key] for key in preferred if key in fields), None)


def _cpu_model(system: str) -> str | None:
    if system == "Darwin":
        return _safe_capture(("sysctl", "-n", "machdep.cpu.brand_string")) or None
    if system == "Linux":
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            return platform.processor() or None
        return parse_linux_cpu_model(cpuinfo) or platform.processor() or None
    return platform.processor() or None


def _physical_memory_bytes(system: str) -> int | None:
    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        page_count = int(os.sysconf("SC_PHYS_PAGES"))
        if page_size > 0 and page_count > 0:
            return page_size * page_count
    except (AttributeError, OSError, TypeError, ValueError):
        pass

    if system == "Darwin":
        value = _safe_capture(("sysctl", "-n", "hw.memsize"))
        try:
            return int(value) if value is not None else None
        except ValueError:
            return None
    return None


def collect_system_metadata() -> dict[str, Any]:
    """Collect portable OS, CPU, and physical-memory details."""

    system = platform.system()
    return {
        "os": system or None,
        "os_release": platform.release() or None,
        "os_version": platform.version() or None,
        "architecture": platform.machine() or None,
        "cpu": _cpu_model(system),
        "cpu_count": os.cpu_count(),
        "ram_bytes": _physical_memory_bytes(system),
    }


def _iso_timestamp(started_at: datetime | None) -> str:
    value = started_at or datetime.now(timezone.utc).astimezone()
    if value.tzinfo is None:
        value = value.astimezone()
    return value.isoformat(timespec="seconds")


def collect_run_metadata(
    *,
    purpose: str,
    parent_model: str | Path | None = None,
    started_at: datetime | None = None,
    cwd: str | Path | None = None,
    argv: Sequence[str] | None = None,
    extra: JsonMapping | None = None,
) -> dict[str, Any]:
    """Build a JSON-ready run manifest from explicit inputs and safe probes."""

    working_directory = (Path.cwd() if cwd is None else Path(cwd)).resolve()
    model = (
        None
        if parent_model is None
        else str(Path(parent_model).expanduser().resolve(strict=False))
    )
    metadata: dict[str, Any] = {
        "purpose": str(purpose),
        "started_at": _iso_timestamp(started_at),
        "command": format_command(argv),
        "cwd": str(working_directory),
        "parent_model": model,
        "git": collect_git_metadata(working_directory),
        "system": collect_system_metadata(),
    }
    if extra is not None:
        metadata["extra"] = dict(extra)
    return metadata


def _atomic_write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except OSError:
                pass
        raise
    return path


def write_command_file(
    run_directory: str | Path,
    command: str | Sequence[str],
) -> Path:
    """Write ``command.txt`` with one shell-ready command."""

    rendered = command if isinstance(command, str) else format_command(command)
    return _atomic_write(Path(run_directory) / "command.txt", rendered.rstrip() + "\n")


def write_run_metadata(
    run_directory: str | Path,
    metadata: JsonMapping,
) -> Path:
    """Write a deterministic, human-readable ``run.json`` manifest."""

    content = json.dumps(
        dict(metadata),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str,
    )
    return _atomic_write(Path(run_directory) / "run.json", content + "\n")


def _markdown_value(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value).replace("\n", " ")


def write_status_markdown(
    run_directory: str | Path,
    metadata: JsonMapping,
    *,
    status: str = "running",
    summary: str | None = None,
    next_action: str | None = None,
) -> Path:
    """Write a concise ``status.md`` suitable for run hand-off."""

    git = metadata.get("git")
    git_info = git if isinstance(git, Mapping) else {}
    system = metadata.get("system")
    system_info = system if isinstance(system, Mapping) else {}
    lines = [
        "# Run status",
        "",
        f"- Status: {_markdown_value(status)}",
        f"- Purpose: {_markdown_value(metadata.get('purpose'))}",
        f"- Started: {_markdown_value(metadata.get('started_at'))}",
        f"- Working directory: `{_markdown_value(metadata.get('cwd'))}`",
        f"- Parent model: `{_markdown_value(metadata.get('parent_model'))}`",
        f"- Git commit: `{_markdown_value(git_info.get('commit'))}`",
        f"- Git dirty: {_markdown_value(git_info.get('dirty'))}",
        (
            "- System: "
            f"{_markdown_value(system_info.get('os'))} "
            f"{_markdown_value(system_info.get('os_release'))}; "
            f"{_markdown_value(system_info.get('cpu'))}; "
            f"{_markdown_value(system_info.get('ram_bytes'))} bytes RAM"
        ),
        "",
        "## Command",
        "",
        f"    {_markdown_value(metadata.get('command'))}",
    ]
    if summary is not None:
        lines.extend(("", "## Result", "", summary.strip()))
    if next_action is not None:
        lines.extend(("", "## Next action", "", next_action.strip()))
    return _atomic_write(Path(run_directory) / "status.md", "\n".join(lines) + "\n")


def record_run(
    run_directory: str | Path,
    *,
    purpose: str,
    parent_model: str | Path | None = None,
    started_at: datetime | None = None,
    cwd: str | Path | None = None,
    argv: Sequence[str] | None = None,
    extra: JsonMapping | None = None,
    status: str = "running",
) -> dict[str, Any]:
    """Collect and write command, metadata, and status artifacts."""

    metadata = collect_run_metadata(
        purpose=purpose,
        parent_model=parent_model,
        started_at=started_at,
        cwd=cwd,
        argv=argv,
        extra=extra,
    )
    write_command_file(run_directory, str(metadata["command"]))
    write_run_metadata(run_directory, metadata)
    write_status_markdown(run_directory, metadata, status=status)
    return metadata
