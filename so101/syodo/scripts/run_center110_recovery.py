"""Run the restartable centered-110mm CUDA recovery curriculum on Windows."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
CHUNK_STEPS = 250_000
MAX_CHUNKS = 8
SEED = 217
CENTER110_PROFILE = "p10-80-v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_train_command(
    *,
    python: Path,
    parent: Path,
    hard_csv: Path,
    output: Path,
    font: Path,
    first_chunk: bool,
    learning_rate: float,
    n_envs: int = 4,
) -> list[str]:
    """Build one exact 250k CUDA/Subproc center-recovery command."""

    command = [
        str(python),
        "-u",
        "-m",
        "so101_calligraphy.training.professional",
        "--ablation",
        "all",
        "--run-purpose",
        "center110 dynamic-brush p10-80 recovery",
        "--initial-model",
        str(parent),
        "--hard-csv",
        str(hard_csv),
        "--hard-beauty-threshold",
        "80",
        "--brushmark-layout",
        "--center110-profile",
        CENTER110_PROFILE,
        "--training-layouts",
        "0",
        "--start-stage",
        "9",
        "--end-stage",
        "9",
        "--timesteps",
        str(CHUNK_STEPS),
        "--bc-steps",
        "100000",
        "--bc-epochs",
        "3",
        "--n-envs",
        str(n_envs),
        "--require-subproc",
        "--bc-workers",
        str(n_envs),
        "--n-steps",
        "2048",
        "--batch-size",
        "1024",
        "--learning-rate",
        str(learning_rate),
        "--clip-range",
        "0.1",
        "--target-kl",
        "0.03",
        "--device",
        "cuda",
        "--train-only",
        "--allow-gate-failure",
        # The driver performs the required fixed-seed 128-glyph audit after
        # every chunk. Keep the curriculum's internal gate sample small so it
        # does not duplicate that expensive audit before the checkpoint can be
        # selected.
        "--stage-eval-size",
        "8",
        "--exemplar-font",
        str(font),
        "--seed",
        str(SEED),
        "--output",
        str(output),
    ]
    command.append("--policy-only-warm-start" if first_chunk else "--skip-bc")
    return command


def build_eval_command(
    *,
    python: Path,
    model: Path | None,
    output: Path,
    font: Path,
    limit: int,
) -> list[str]:
    """Build the fixed-seed four-shard center evaluation command."""

    command = [
        str(python),
        str(ROOT / "scripts" / "evaluate_joyo_shards.py"),
        "--output",
        str(output),
        "--shards",
        "4",
        "--device",
        "cpu",
        "--seed",
        str(SEED),
        "--eval-limit",
        str(limit),
        "--brushmark-layout",
        "--center110-profile",
        CENTER110_PROFILE,
        "--eval-layouts",
        "0",
        "--exemplar-font",
        str(font),
    ]
    if model is not None:
        command.extend(["--model", str(model)])
    return command


def candidate_rank(evaluation: Mapping[str, Any]) -> tuple[float, ...]:
    """Rank safety, completion, p10, mean, then minimum exactly in that order."""

    safe = int(
        int(evaluation["total_drips"]) == 0
        and int(evaluation["collision_count"]) == 0
    )
    return (
        float(safe),
        float(evaluation["success_rate"]),
        float(evaluation["p10_beauty_score"]),
        float(evaluation["mean_beauty_score"]),
        float(evaluation["minimum_beauty_score"]),
    )


def accepted_full(summary: Mapping[str, Any]) -> bool:
    """Apply the exact 2,136-row center acceptance contract."""

    evaluation = summary["evaluation"]
    acceptance = summary.get("acceptance", {})
    return bool(
        summary.get("all_joyo_evaluated") is True
        and summary.get("eval_layouts") == [0]
        and summary.get("brushmark_layout") is True
        and summary.get("center110_profile") == CENTER110_PROFILE
        and int(evaluation["count"]) == 2_136
        and int(evaluation["unique_character_count"]) == 2_136
        and int(evaluation["layout_count"]) == 1
        and float(evaluation["success_rate"]) == 1.0
        and float(evaluation["mean_beauty_score"]) >= 80.0
        and float(evaluation["p10_beauty_score"]) >= 80.0
        and float(evaluation["minimum_beauty_score"]) >= 60.0
        and int(evaluation["total_drips"]) == 0
        and int(evaluation["collision_count"]) == 0
        and acceptance
        and all(bool(value) for value in acceptance.values())
    )


def _load_summary(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("evaluation"), dict):
        raise ValueError(f"Invalid evaluation summary: {path}")
    return value


def _validate_center_csv(path: Path, expected_rows: int) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    keys = [(row.get("character", ""), row.get("layout_index", "")) for row in rows]
    if (
        len(rows) != expected_rows
        or len(set(keys)) != expected_rows
        or any(len(character) != 1 or layout != "0" for character, layout in keys)
    ):
        raise ValueError(
            f"Center CSV must have {expected_rows:,} unique character/layout-0 rows: {path}"
        )


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _append_command(path: Path, *, phase: str, command: Sequence[str]) -> None:
    record = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "phase": phase,
        "commit": _git_commit(),
        "argv": list(command),
        "display": subprocess.list2cmdline(list(command)),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _run(
    command: Sequence[str], *, phase: str, output: Path, commands_path: Path
) -> Path:
    _append_command(commands_path, phase=phase, command=command)
    log_path = output / "logs" / f"{phase}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log:
        result = subprocess.run(
            list(command), cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, text=True
        )
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command)
    return log_path


def _clean_windows_state() -> bool:
    """Require >=8 GiB free RAM and no other python.exe before 4->2 fallback."""

    if os.name != "nt":
        return False
    memory = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    free_bytes = int(memory.stdout.strip()) * 1024
    tasks = subprocess.run(
        ["tasklist.exe", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
        check=True,
        capture_output=True,
        text=True,
    )
    other_python = [
        row
        for row in csv.reader(tasks.stdout.splitlines())
        if len(row) >= 2 and row[1].isdigit() and int(row[1]) != os.getpid()
    ]
    return free_bytes >= 8 * 1024**3 and not other_python


def _run_train_with_1455_fallback(
    *,
    python: Path,
    parent: Path,
    hard_csv: Path,
    chunk: Path,
    font: Path,
    first_chunk: bool,
    learning_rate: float,
    run_output: Path,
    commands_path: Path,
) -> tuple[int, Path]:
    command = build_train_command(
        python=python,
        parent=parent,
        hard_csv=hard_csv,
        output=chunk,
        font=font,
        first_chunk=first_chunk,
        learning_rate=learning_rate,
    )
    phase = f"chunk-{int(chunk.name.split('-')[-1]):02d}-train-n4"
    try:
        return 4, _run(
            command, phase=phase, output=run_output, commands_path=commands_path
        )
    except subprocess.CalledProcessError:
        log_path = run_output / "logs" / f"{phase}.log"
        text = log_path.read_text(encoding="utf-8", errors="replace")
        if "WinError 1455" not in text or not _clean_windows_state():
            raise
        post_bc = chunk / "09-hard-mining" / "post_bc_model.zip"
        retry_parent = post_bc if post_bc.is_file() else parent
        retry = build_train_command(
            python=python,
            parent=retry_parent,
            hard_csv=hard_csv,
            output=chunk,
            font=font,
            first_chunk=first_chunk and not post_bc.is_file(),
            learning_rate=learning_rate,
            n_envs=2,
        )
        return 2, _run(
            retry,
            phase=f"chunk-{int(chunk.name.split('-')[-1]):02d}-train-n2",
            output=run_output,
            commands_path=commands_path,
        )


def _materialize_chunk_model(chunk: Path) -> Path:
    """Normalize professional.py's stage model to the driver checkpoint name."""

    expected = chunk / "final_model.zip"
    if expected.is_file():
        return expected
    stage_model = chunk / "09-hard-mining" / "model.zip"
    if stage_model.is_file():
        # Preserve the stage artifact while providing the stable driver name.
        shutil.copy2(stage_model, expected)
    return expected


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--baseline-summary", type=Path, required=True)
    parser.add_argument("--baseline-csv", type=Path, required=True)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.dry_run:
        for name in ("parent", "baseline_summary", "baseline_csv", "font", "python"):
            if not getattr(args, name).expanduser().is_file():
                parser.error(f"--{name.replace('_', '-')} does not exist")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    parent = args.parent.expanduser().resolve()
    baseline_summary = args.baseline_summary.expanduser().resolve()
    baseline_csv = args.baseline_csv.expanduser().resolve()
    font = args.font.expanduser().resolve()
    # Keep a virtualenv launcher intact; Path.resolve() follows its interpreter symlink.
    python = Path(os.path.abspath(args.python.expanduser()))
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    commands_path = output / "commands.jsonl"

    if args.dry_run:
        train = build_train_command(
            python=python,
            parent=parent,
            hard_csv=baseline_csv,
            output=output / "chunks" / "chunk-01",
            font=font,
            first_chunk=True,
            learning_rate=5e-5,
        )
        evaluation = build_eval_command(
            python=python,
            model=output / "chunks" / "chunk-01" / "final_model.zip",
            output=output / "evaluations" / "chunk-01-128",
            font=font,
            limit=128,
        )
        print(subprocess.list2cmdline(train))
        print(subprocess.list2cmdline(evaluation))
        return 0

    _validate_center_csv(baseline_csv, 2_136)
    baseline = _load_summary(baseline_summary)
    if not (
        baseline.get("all_joyo_evaluated") is True
        and baseline.get("eval_layouts") == [0]
        and baseline.get("brushmark_layout") is True
        and baseline.get("center110_profile") == CENTER110_PROFILE
        and int(baseline["evaluation"]["count"]) == 2_136
        and int(baseline["evaluation"]["unique_character_count"]) == 2_136
        and int(baseline["evaluation"]["layout_count"]) == 1
    ):
        raise ValueError("Baseline must be the full 2,136-row center evaluation.")

    status_path = output / "status.json"
    status = (
        json.loads(status_path.read_text(encoding="utf-8"))
        if status_path.is_file()
        else {
            "schema_version": 1,
            "center110_profile": CENTER110_PROFILE,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "commit": _git_commit(),
            "parent_model": str(parent),
            "parent_model_sha256": _sha256(parent),
            "baseline_summary": str(baseline_summary),
            "baseline_summary_sha256": _sha256(baseline_summary),
            "baseline_csv": str(baseline_csv),
            "baseline_csv_sha256": _sha256(baseline_csv),
            "chunks": [],
            "selected_model": str(parent),
            "learning_rate": 5e-5,
            "learning_rate_reduced": False,
            "full_non_improvements": 0,
            "best_full_rank": list(candidate_rank(baseline["evaluation"])),
            "stop_reason": "",
        }
    )
    if status.get("center110_profile") != CENTER110_PROFILE:
        raise ValueError(
            "Existing status uses a missing or different center110 profile."
        )
    _write_json(status_path, status)
    if status.get("stop_reason"):
        print(status_path)
        return 0
    selected = Path(status["selected_model"])
    hard_csv = Path(status.get("latest_hard_csv", baseline_csv))
    best_checkpoint_rank = tuple(status.get("best_checkpoint_rank", ()))
    best_full_rank = tuple(status["best_full_rank"])

    for chunk_number in range(len(status["chunks"]) + 1, MAX_CHUNKS + 1):
        chunk = output / "chunks" / f"chunk-{chunk_number:02d}"
        model = chunk / "final_model.zip"
        previous_selected = selected
        previous_checkpoint_rank = best_checkpoint_rank
        status.update(
            phase="training",
            current_chunk=chunk_number,
            completed_timesteps=(chunk_number - 1) * CHUNK_STEPS,
            updated_at=datetime.now().isoformat(timespec="seconds"),
        )
        _write_json(status_path, status)
        if model.is_file():
            n_envs = 4
        else:
            n_envs, _ = _run_train_with_1455_fallback(
                python=python,
                parent=selected,
                hard_csv=hard_csv,
                chunk=chunk,
                font=font,
                first_chunk=chunk_number == 1,
                learning_rate=float(status["learning_rate"]),
                run_output=output,
                commands_path=commands_path,
            )
        model = _materialize_chunk_model(chunk)
        if not model.is_file():
            raise FileNotFoundError(f"Training did not create {model}")

        eval_128 = output / "evaluations" / f"chunk-{chunk_number:02d}-128"
        status.update(
            phase="eval-128",
            updated_at=datetime.now().isoformat(timespec="seconds"),
        )
        _write_json(status_path, status)
        if not (eval_128 / "summary.json").is_file():
            _run(
                build_eval_command(
                    python=python, model=model, output=eval_128, font=font, limit=128
                ),
                phase=f"chunk-{chunk_number:02d}-eval-128",
                output=output,
                commands_path=commands_path,
            )
        summary_128 = _load_summary(eval_128 / "summary.json")
        _validate_center_csv(eval_128 / "characters.csv", 128)
        rank_128 = candidate_rank(summary_128["evaluation"])
        safe = bool(rank_128[0])
        selected_reason = "kept previous safe checkpoint"
        if safe and (not best_checkpoint_rank or rank_128 > best_checkpoint_rank):
            selected = model
            best_checkpoint_rank = rank_128
            selected_reason = "best safe 128 rank"
        elif not safe and not status["learning_rate_reduced"]:
            status["learning_rate"] = 2.5e-5
            status["learning_rate_reduced"] = True
            selected_reason = "safety regression; reverted and reduced learning rate"

        record: dict[str, Any] = {
            "chunk": chunk_number,
            "timesteps_total": chunk_number * CHUNK_STEPS,
            "n_envs": n_envs,
            "model": str(model),
            "model_sha256": _sha256(model),
            "post_bc_model": None,
            "eval_128": str(eval_128 / "summary.json"),
            "rank_128": list(rank_128),
            "selected": str(selected),
            "selection_reason": selected_reason,
        }
        post_bc = chunk / "09-hard-mining" / "post_bc_model.zip"
        if post_bc.is_file():
            record["post_bc_model"] = {
                "path": str(post_bc),
                "sha256": _sha256(post_bc),
            }

        acceptance_128 = summary_128.get("acceptance", {})
        full_needed = chunk_number % 2 == 0 or bool(
            acceptance_128
            and all(bool(value) for value in acceptance_128.values())
        )
        if full_needed:
            full = output / "evaluations" / f"chunk-{chunk_number:02d}-full"
            status.update(
                phase="eval-full",
                updated_at=datetime.now().isoformat(timespec="seconds"),
            )
            _write_json(status_path, status)
            if not (full / "summary.json").is_file():
                _run(
                    build_eval_command(
                        python=python, model=model, output=full, font=font, limit=0
                    ),
                    phase=f"chunk-{chunk_number:02d}-eval-full",
                    output=output,
                    commands_path=commands_path,
                )
            summary_full = _load_summary(full / "summary.json")
            _validate_center_csv(full / "characters.csv", 2_136)
            full_rank = candidate_rank(summary_full["evaluation"])
            if not bool(full_rank[0]):
                selected = previous_selected
                best_checkpoint_rank = previous_checkpoint_rank
                record["selection_reason"] = "full safety regression; reverted"
                if not status["learning_rate_reduced"]:
                    status["learning_rate"] = 2.5e-5
                    status["learning_rate_reduced"] = True
                    record["selection_reason"] += " and reduced learning rate"
            improved = full_rank > best_full_rank
            status["full_non_improvements"] = (
                0 if improved else int(status["full_non_improvements"]) + 1
            )
            if improved:
                best_full_rank = full_rank
                status["best_full_rank"] = list(full_rank)
            hard_csv = full / "characters.csv"
            status["latest_hard_csv"] = str(hard_csv)
            record.update(
                full_summary=str(full / "summary.json"),
                full_csv_sha256=_sha256(full / "characters.csv"),
                full_rank=list(full_rank),
                full_improved=improved,
            )
            if accepted_full(summary_full):
                status["stop_reason"] = "accepted"

        record["selected"] = str(selected)
        status["chunks"].append(record)
        status["selected_model"] = str(selected)
        status["selected_model_sha256"] = _sha256(selected)
        status["best_checkpoint_rank"] = list(best_checkpoint_rank)
        status["phase"] = "chunk-complete"
        status["completed_timesteps"] = chunk_number * CHUNK_STEPS
        status["updated_at"] = datetime.now().isoformat(timespec="seconds")
        _write_json(status_path, status)
        if status["stop_reason"] == "accepted":
            break
        if int(status["full_non_improvements"]) >= 2:
            status["stop_reason"] = "two consecutive full evaluations without improvement"
            _write_json(status_path, status)
            break
    else:
        status["stop_reason"] = "2,000,000 timestep limit"
        _write_json(status_path, status)

    print(status_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
