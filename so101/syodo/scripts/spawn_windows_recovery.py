"""Detach and supervise A4/tip-only CUDA recovery training on Windows."""

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
import time
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
DEFAULT_BASE_RUN = "kaisho-yohitsu-brush-tilt-a4-tip"
BASE_RUN = DEFAULT_BASE_RUN
PARENT = RUNS / "kaisho-yohitsu-brushmark-joyo" / "08-joyo" / "model.zip"
FONT = ROOT / "fonts" / "A-OTF-KaishoMCBK1Pro-DeBold.otf"
PHYSICAL_GATE = RUNS / f"{BASE_RUN}-gate3" / "gate3-evidence.json"
MASTER_LOG = RUNS / f"{BASE_RUN}-recovery.log"
PIDFILE = RUNS / f"{BASE_RUN}-recovery.pid"
STATUS = RUNS / f"{BASE_RUN}-recovery-status.json"
SELECTION = RUNS / f"{BASE_RUN}-recovery-selection.json"

DETACH = 0x00000200 | 0x08000000 | 0x01000000
MIN_FREE_BYTES = 20 * 1024**3
POLL_SECONDS = 30
TARGET_MEAN = 85.0
RECOVERY_MEAN = 86.27775324466442
RECOVERY_P10 = 83.78582694425683
PHYSICAL_GATE_SCHEMA_VERSION = 2
R1_CHUNK_STEPS = 250_000
R1_CHUNKS = 10
R1_AUTHORITY_PROFILES = frozenset({"strict", "relaxed-r1"})


def _default_base_run(threshold_profile: str) -> str:
    return (
        f"{DEFAULT_BASE_RUN}-relaxed"
        if threshold_profile == "relaxed-r1"
        else DEFAULT_BASE_RUN
    )


def _configure_run_paths(base_run: str) -> None:
    if not base_run or Path(base_run).name != base_run:
        raise ValueError("base run must be a non-empty path-free name")
    global BASE_RUN, PHYSICAL_GATE, MASTER_LOG, PIDFILE, STATUS, SELECTION
    BASE_RUN = base_run
    PHYSICAL_GATE = RUNS / f"{base_run}-gate3" / "gate3-evidence.json"
    MASTER_LOG = RUNS / f"{base_run}-recovery.log"
    PIDFILE = RUNS / f"{base_run}-recovery.pid"
    STATUS = RUNS / f"{base_run}-recovery-status.json"
    SELECTION = RUNS / f"{base_run}-recovery-selection.json"


class DeadlineReached(RuntimeError):
    """Raised when the local deadline stops a child process."""


def parse_deadline(value: str) -> datetime | None:
    """Parse a local ISO deadline. none/off/empty means run until finished."""

    text = value.strip()
    if text.lower() in {"", "none", "off"}:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("deadline must be an ISO local datetime") from exc


def round_phase(output: Path, evaluation: Path) -> str:
    """Return train, eval, or done for an existing recovery round."""

    if (evaluation / "summary.json").is_file():
        return "done"
    if (output / "final_model.zip").is_file():
        return "eval"
    return "train"


def _run_paths(round_number: int) -> tuple[Path, Path]:
    output = RUNS / f"{BASE_RUN}-r{round_number}"
    return output, RUNS / f"{output.name}-joyo-eval"


def build_train_command(
    *,
    python: Path,
    round_number: int,
    parent: Path,
    output: Path,
    learning_rate: float,
    pressure_calibration: Path,
    hard_csv: Path | None = None,
) -> list[str]:
    start_stage = 8 if round_number == 1 else 9
    command = [
        str(python),
        "-u",
        "-m",
        "so101_calligraphy.training.professional",
        "--ablation",
        "all",
        "--run-purpose",
        f"A4 38mm tip-only CUDA recovery r{round_number}",
        "--initial-model",
        str(parent),
        "--exemplar-font",
        str(FONT),
        "--start-stage",
        str(start_stage),
        "--end-stage",
        str(start_stage),
        "--timesteps",
        "2500000",
        "--bc-steps",
        "180000",
        "--bc-epochs",
        "5",
        "--n-envs",
        "8",
        "--require-subproc",
        "--bc-workers",
        "8",
        "--n-steps",
        "2048",
        "--batch-size",
        "1024",
        "--learning-rate",
        str(learning_rate),
        "--device",
        "cuda",
        "--allow-gate-failure",
        "--pressure-calibration",
        str(pressure_calibration),
        "--require-pressure-calibration",
        "--stage-eval-size",
        "64",
        "--eval-limit",
        "128",
        "--output",
        str(output),
        "--seed",
        str(120 + round_number),
    ]
    if start_stage == 9:
        if hard_csv is None:
            raise ValueError("hard_csv is required after r1")
        command.extend(("--hard-csv", str(hard_csv)))
    return command


def build_r1_chunk_command(
    *,
    python: Path,
    parent: Path,
    output: Path,
    pressure_calibration: Path | None,
    config: dict[str, float],
    first_chunk: bool,
    threshold_profile: str = "strict",
) -> list[str]:
    bc_workers = 4 if threshold_profile == "relaxed-r1" else 8
    command = [
        str(python),
        "-u",
        "-m",
        "so101_calligraphy.training.professional",
        "--ablation",
        "all",
        "--run-purpose",
        f"{threshold_profile} Gate3-approved Windows CUDA r1 safety-screened chunk",
        "--initial-model",
        str(parent),
        "--exemplar-font",
        str(FONT),
        "--start-stage",
        "8",
        "--end-stage",
        "8",
        "--timesteps",
        str(R1_CHUNK_STEPS),
        "--bc-steps",
        "180000",
        "--bc-epochs",
        "5",
        "--n-envs",
        "8",
        "--require-subproc",
        "--bc-workers",
        str(bc_workers),
        "--n-steps",
        "2048",
        "--batch-size",
        "1024",
        "--learning-rate",
        "0.0001",
        "--clip-range",
        "0.1",
        "--target-kl",
        "0.03",
        "--device",
        "cuda",
        "--minimum-gap",
        str(config["minimum_gap_m"]),
        "--clearance-floor",
        str(config["clearance_floor"]),
        "--exemplar-motion-strength",
        str(config["exemplar_motion_strength"]),
        "--train-only",
        "--allow-gate-failure",
        "--output",
        str(output),
    ]
    if pressure_calibration is not None:
        command[command.index("--minimum-gap"):command.index("--minimum-gap")] = [
            "--pressure-calibration",
            str(pressure_calibration),
            "--require-pressure-calibration",
            "--pressure-calibration-clip-rate-limit",
            "0.05",
        ]
    command.append("--policy-only-warm-start" if first_chunk else "--skip-bc")
    return command


def build_eval_command(
    *,
    python: Path,
    model: Path,
    output: Path,
    seed: int,
    pressure_calibration: Path,
    eval_limit: int = 0,
) -> list[str]:
    return [
        str(python),
        "-u",
        str(ROOT / "scripts" / "evaluate_joyo_shards.py"),
        "--model",
        str(model),
        "--output",
        str(output),
        "--shards",
        "8",
        "--device",
        "cpu",
        "--seed",
        str(seed),
        "--eval-limit",
        str(eval_limit),
        "--exemplar-font",
        str(FONT),
        "--pressure-calibration",
        str(pressure_calibration),
    ]


def candidate_rank(
    summary: dict[str, Any], rows: Sequence[dict[str, str]]
) -> tuple[float, ...]:
    acceptance = summary.get("acceptance") or {}
    evaluation = summary.get("evaluation") or {}
    components = evaluation.get("component_means") or {}
    techniques = evaluation.get("technique_means") or {}
    endpoint = evaluation.get("endpoint_triangle") or {}
    harai = techniques.get("harai") or {}
    per_row_lw_bw = sum(
        float(row["line_width"]) >= 65.0 and float(row["brushwork"]) >= 62.0
        for row in rows
    ) / max(1, len(rows))
    return (
        float(sum(bool(value) for value in acceptance.values())),
        float(evaluation.get("success_rate") or 0.0),
        float(evaluation.get("mean_beauty_score") or 0.0),
        float(evaluation.get("p10_beauty_score") or 0.0),
        float(components.get("line_width") or 0.0)
        + float(components.get("brushwork") or 0.0)
        + per_row_lw_bw,
        float(endpoint.get("mean") or 0.0),
        float(harai.get("finish") or 0.0),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _read_candidate(round_number: int, model: Path, evaluation: Path) -> dict[str, Any]:
    summary = json.loads((evaluation / "summary.json").read_text(encoding="utf-8"))
    with (evaluation / "characters.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    values = summary["evaluation"]
    acceptance = summary["acceptance"]
    rank = candidate_rank(summary, rows)
    minimum_gate = bool(
        all(bool(value) for value in acceptance.values())
        and float(values["success_rate"]) == 1.0
        and float(values["mean_beauty_score"]) >= TARGET_MEAN
    )
    full_safe_shape = bool(
        len(rows) == 12_816
        and int(values.get("count", 0)) == 12_816
        and len({row.get("character", "") for row in rows}) == 2_136
        and int(values.get("unique_character_count", 0)) == 2_136
        and int(values.get("layout_count", 0)) == 6
        and int(values.get("total_drips", -1)) == 0
        and int(values.get("collision_count", -1)) == 0
    )
    recovered = bool(
        minimum_gate
        and full_safe_shape
        and float(values["mean_beauty_score"]) > RECOVERY_MEAN
        and float(values["p10_beauty_score"]) >= RECOVERY_P10
    )
    return {
        "round": round_number,
        "model": str(model),
        "model_sha256": _sha256(model),
        "evaluation": str(evaluation),
        "evaluation_rows": len(rows),
        "rank": list(rank),
        "minimum_gate": minimum_gate,
        "full_safe_shape": full_safe_shape,
        "past_best_recovered": recovered,
    }


def _environment() -> dict[str, str]:
    return os.environ | {
        "PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT))),
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "MPLBACKEND": "Agg",
    }


def _alive(pid: int) -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    return any(
        len(row) > 1 and row[1] == str(pid)
        for row in csv.reader(result.stdout.splitlines())
    )


def _log(message: str) -> None:
    line = f"==== {datetime.now():%Y-%m-%d %H:%M:%S} {message} ===="
    with MASTER_LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def _write_status(**values: object) -> None:
    STATUS.write_text(
        json.dumps({"updated_at": datetime.now().isoformat(), **values}, indent=2),
        encoding="utf-8",
    )


def _physical_gate_passed(path: Path) -> bool:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(value, dict):
        return False
    summary = value.get("summary")
    if not isinstance(summary, dict):
        return False
    gates = summary.get("gates")
    threshold_profile = value.get(
        "threshold_profile", summary.get("threshold_profile", "strict")
    )
    model_raw = value.get("model")
    calibration_raw = value.get("calibration")
    config = value.get("config")
    if (
        not isinstance(model_raw, str)
        or not model_raw
        or not isinstance(config, dict)
        or threshold_profile not in R1_AUTHORITY_PROFILES
        or threshold_profile != summary.get("threshold_profile", threshold_profile)
    ):
        return False
    model = Path(model_raw)
    if not model.is_absolute():
        model = ROOT / model
    try:
        model_matches = _sha256(model) == value.get("model_sha256")
        if isinstance(calibration_raw, str) and calibration_raw:
            calibration = Path(calibration_raw)
            if not calibration.is_absolute():
                calibration = ROOT / calibration
            calibration_matches = _sha256(calibration) == value.get(
                "calibration_sha256"
            )
            from so101_calligraphy.pressure_calibration import PressureCalibration

            calibration_model = PressureCalibration.load(calibration)
            calibration_metadata_matches = bool(
                calibration_model.schema_version
                == value.get("calibration_schema_version")
                and calibration_model.cad_fingerprint == value.get("cad_fingerprint")
                and calibration_model.brush_fingerprint
                == value.get("brush_fingerprint")
            )
        else:
            calibration_matches = bool(
                threshold_profile == "relaxed-r1"
                and all(
                    value.get(name) is None
                    for name in (
                        "calibration",
                        "calibration_sha256",
                        "calibration_schema_version",
                        "cad_fingerprint",
                        "brush_fingerprint",
                    )
                )
            )
            calibration_metadata_matches = calibration_matches
    except OSError:
        calibration_matches = False
        model_matches = False
        calibration_metadata_matches = False
    except (ValueError, json.JSONDecodeError):
        calibration_matches = False
        model_matches = False
        calibration_metadata_matches = False
    return bool(
        value.get("ready_for_r1") is True
        and value.get("gate_schema_version") == PHYSICAL_GATE_SCHEMA_VERSION
        and value.get("gate_level") == 3
        and value.get("evaluation_count") == 768
        and calibration_matches
        and calibration_metadata_matches
        and model_matches
        and _json_sha256(config) == value.get("config_sha256")
        and isinstance(value.get("configuration_fingerprint"), str)
        and value.get("configuration_fingerprint")
        == summary.get("configuration_fingerprint")
        and summary.get("ready_for_r1") is True
        and summary.get("passed") is True
        and summary.get("gate_schema_version") == PHYSICAL_GATE_SCHEMA_VERSION
        and summary.get("gate_level") == 3
        and summary.get("evaluations") == 768
        and isinstance(gates, dict)
        and gates
        and all(gate is True for gate in gates.values())
    )


def _physical_gate_calibration(path: Path) -> Path | None:
    value = json.loads(path.read_text(encoding="utf-8"))
    raw = value.get("calibration")
    if raw in (None, ""):
        return None
    calibration = Path(str(raw))
    return calibration if calibration.is_absolute() else ROOT / calibration


def _physical_gate_model(path: Path) -> Path:
    value = json.loads(path.read_text(encoding="utf-8"))
    model = Path(str(value["model"]))
    return model if model.is_absolute() else ROOT / model


def _physical_gate_config(path: Path) -> dict[str, float]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return {name: float(raw) for name, raw in value["config"].items()}


def parent_smoke_passed(summary: dict[str, Any]) -> bool:
    evaluation = summary.get("evaluation")
    return bool(
        isinstance(evaluation, dict)
        and evaluation.get("count") == 768
        and evaluation.get("unique_character_count") == 128
        and evaluation.get("layout_count") == 6
        and evaluation.get("success_rate") == 1.0
    )


def _deadline_reached(deadline: datetime | None) -> bool:
    return deadline is not None and datetime.now() >= deadline


def _stop_tree(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)


def _preflight(physical_gate: Path, *, check_duplicate: bool = True) -> str:
    if sys.platform != "win32":
        raise SystemExit("this launcher must run on Windows")
    for label, path in (
        ("exemplar font", FONT),
        ("joyo evaluator", ROOT / "scripts" / "evaluate_joyo_shards.py"),
    ):
        if not path.is_file():
            raise SystemExit(f"missing {label}: {path}")
    if not _physical_gate_passed(physical_gate):
        raise SystemExit(f"physical gate not passed: {physical_gate}")
    calibration = _physical_gate_calibration(physical_gate)
    if calibration is not None and not calibration.is_file():
        raise SystemExit(f"missing pressure calibration: {calibration}")
    if shutil.disk_usage(ROOT).free < MIN_FREE_BYTES:
        raise SystemExit("less than 20 GiB free on the Windows drive")
    if check_duplicate and PIDFILE.is_file():
        try:
            pid = int(PIDFILE.read_text(encoding="ascii").strip())
        except ValueError:
            pid = 0
        if pid and _alive(pid):
            raise SystemExit(f"recovery launcher is already running: pid={pid}")
    cuda = subprocess.run(
        [
            sys.executable,
            "-c",
            "import torch; print(torch.__version__); "
            "assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if cuda.returncode != 0:
        raise SystemExit("CUDA preflight failed:\n" + cuda.stdout + cuda.stderr)
    from stable_baselines3 import PPO

    parent_model = PPO.load(_physical_gate_model(physical_gate), device="cpu")
    if parent_model.observation_space.shape != (371,):
        raise SystemExit(
            f"parent model observation shape is {parent_model.observation_space.shape}, expected (371,)"
        )
    if parent_model.action_space.shape != (6,):
        raise SystemExit(
            f"parent model action shape is {parent_model.action_space.shape}, expected (6,)"
        )
    return cuda.stdout.strip()


def _gpu_snapshot() -> str:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,utilization.gpu,memory.used,memory.total",
            "--format=csv,noheader",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout + result.stderr).strip()


def _output_progress_path(command: Sequence[str]) -> Path | None:
    try:
        return Path(command[command.index("--output") + 1]) / "progress.json"
    except (ValueError, IndexError):
        return None


def _run_command(
    command: Sequence[str], *, log_path: Path, phase: str, deadline: datetime | None
) -> None:
    _log(f"{phase} start: {subprocess.list2cmdline(command)}")
    with log_path.open("wb") as log:
        if "--device" in command and command[command.index("--device") + 1] == "cuda":
            log.write(b"Using cuda device (launcher preflight verified)\n")
            log.flush()
        process = subprocess.Popen(
            list(command), cwd=ROOT, env=_environment(), stdout=log, stderr=subprocess.STDOUT
        )
        progress_path = _output_progress_path(command)
        while process.poll() is None:
            if _deadline_reached(deadline):
                _stop_tree(process.pid)
                try:
                    process.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    pass
                raise DeadlineReached(phase)
            progress: object = None
            if progress_path is not None and progress_path.is_file():
                try:
                    progress = json.loads(progress_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    progress = None
            _write_status(
                state="running",
                phase=phase,
                child_pid=process.pid,
                deadline=None if deadline is None else deadline.isoformat(),
                progress=progress,
                gpu=_gpu_snapshot(),
            )
            time.sleep(POLL_SECONDS)
        if process.returncode:
            raise RuntimeError(
                f"{phase} exited with code {process.returncode}; see {log_path}"
            )
    _log(f"{phase} complete")


def _disable_sleep() -> None:
    for setting in ("standby-timeout-ac", "monitor-timeout-ac", "hibernate-timeout-ac"):
        subprocess.run(
            ["powercfg", "/change", setting, "0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def _finish(candidates: list[dict[str, Any]], *, physical_gate: Path, deadline: datetime | None, state: str) -> int:
    if not candidates:
        _write_status(
            state=state,
            deadline=None if deadline is None else deadline.isoformat(),
            physical_gate=str(physical_gate),
            candidates=candidates,
            note="Stopped before a completed round; no canonical model replacement.",
        )
        _log(f"recovery worker {state} with no completed candidate")
        return 0 if state == "stopped_deadline" else 1
    selected = max(candidates, key=lambda item: tuple(item["rank"]))
    result = {
        "selected": selected,
        "candidates": candidates,
        "physical_gate": str(physical_gate),
        "deadline": None if deadline is None else deadline.isoformat(),
        "note": "No canonical model replacement.",
    }
    SELECTION.write_text(json.dumps(result, indent=2), encoding="utf-8")
    _write_status(state=state, **result)
    _log(f"recovery worker {state} selected={selected['model']}")
    return 0


def _worker(physical_gate: Path, deadline: datetime | None) -> int:
    candidates: list[dict[str, Any]] = []
    try:
        cuda = _preflight(physical_gate, check_duplicate=False)
        pressure_calibration = _physical_gate_calibration(physical_gate)
        initial_model = _physical_gate_model(physical_gate)
        config = _physical_gate_config(physical_gate)
        evidence = json.loads(physical_gate.read_text(encoding="utf-8"))
        threshold_profile = str(evidence["threshold_profile"])
        baseline_raw = evidence.get("upright_baseline")
        if not isinstance(baseline_raw, str) or not baseline_raw:
            raise RuntimeError("Gate 3 evidence is missing the Gate 1 upright baseline")
        upright_baseline = Path(baseline_raw)
        if not upright_baseline.is_absolute():
            upright_baseline = ROOT / upright_baseline
        if not upright_baseline.is_file():
            raise RuntimeError(f"missing upright baseline: {upright_baseline}")
        from scripts.search_gate_recovery import (
            ALL_LAYOUTS,
            GATE1_CHARACTERS,
            GATE2_CHARACTERS,
            Candidate,
            candidate_rank as physical_rank,
            diagnostic_command,
            screen_rows,
        )

        candidate_config = Candidate(
            config["minimum_gap_m"],
            config["clearance_floor"],
            config["exemplar_motion_strength"],
        )
        gate2_evidence = Path(str(evidence["gate2_evidence"]))
        if not gate2_evidence.is_absolute():
            gate2_evidence = ROOT / gate2_evidence
        gate2_value = json.loads(gate2_evidence.read_text(encoding="utf-8"))
        gate1_path = Path(str(gate2_value["gate1_diagnostic"]))
        if not gate1_path.is_absolute():
            gate1_path = ROOT / gate1_path
        baseline_gate1 = json.loads(gate1_path.read_text(encoding="utf-8"))
        best_rank = physical_rank(baseline_gate1["results"])
        best_model = initial_model
        no_improvement = 0
        _disable_sleep()
        _log(
            f"recovery worker pid={os.getpid()} "
            f"deadline={None if deadline is None else deadline.isoformat()} CUDA={cuda!r}"
        )
        r1_output = RUNS / f"{BASE_RUN}-r1"
        r1_output.mkdir(parents=True, exist_ok=True)
        for chunk_number in range(1, R1_CHUNKS + 1):
            if _deadline_reached(deadline):
                raise DeadlineReached("before next r1 chunk")
            chunk = r1_output / f"chunk-{chunk_number:02d}"
            model = chunk / "final_model.zip"
            if not model.is_file():
                if chunk.exists():
                    raise RuntimeError(f"incomplete r1 chunk without a model: {chunk}")
                _run_command(
                    build_r1_chunk_command(
                        python=Path(sys.executable),
                        parent=best_model,
                        output=chunk,
                        pressure_calibration=pressure_calibration,
                        config=config,
                        first_chunk=best_model == initial_model,
                        threshold_profile=threshold_profile,
                    ),
                    log_path=RUNS / f"{BASE_RUN}-r1-chunk-{chunk_number:02d}.log",
                    phase=f"r1 CUDA chunk {chunk_number}/{R1_CHUNKS}",
                    deadline=deadline,
                )
            if not model.is_file():
                raise RuntimeError(f"missing r1 chunk model: {model}")
            safety_path = chunk / "gate1-safety.json"
            if not safety_path.is_file():
                _run_command(
                    diagnostic_command(
                        safety_path,
                        calibration=pressure_calibration,
                        candidate=candidate_config,
                        characters=GATE1_CHARACTERS,
                        layouts=ALL_LAYOUTS,
                        gate_level=1,
                        model=model,
                        upright_baseline=upright_baseline,
                        threshold_profile=threshold_profile,
                    ),
                    log_path=RUNS / f"{BASE_RUN}-r1-chunk-{chunk_number:02d}-safety.log",
                    phase=f"r1 250k safety screen {chunk_number}/{R1_CHUNKS}",
                    deadline=deadline,
                )
            safety_report = json.loads(safety_path.read_text(encoding="utf-8"))
            safety = screen_rows(
                safety_report["results"], threshold_profile=threshold_profile
            )
            rank = physical_rank(safety_report["results"])
            improved = bool(safety["complete"] and safety["safe"] and rank > best_rank)
            record = {
                "chunk": chunk_number,
                "model": str(model),
                "model_sha256": _sha256(model),
                "safety": safety,
                "gate1": safety_report["summary"],
                "rank": list(rank),
                "accepted": improved,
            }
            candidates.append(record)
            if improved:
                best_rank = rank
                best_model = model
                no_improvement = 0
            else:
                no_improvement += 1
            if no_improvement >= 2:
                _log("two consecutive 250k checkpoints did not improve candidate rank; stop")
                break

        post = r1_output / "post-gates"
        post.mkdir(exist_ok=True)
        gate1_post = post / "gate1.json"
        gate2_post = post / "gate2.json"
        for level, destination, characters in (
            (1, gate1_post, GATE1_CHARACTERS),
            (2, gate2_post, GATE2_CHARACTERS),
        ):
            if not destination.is_file():
                _run_command(
                    diagnostic_command(
                        destination,
                        calibration=pressure_calibration,
                        candidate=candidate_config,
                        characters=characters,
                        layouts=ALL_LAYOUTS,
                        gate_level=level,
                        model=best_model,
                        upright_baseline=upright_baseline if level == 1 else None,
                        threshold_profile=threshold_profile,
                    ),
                    log_path=RUNS / f"{BASE_RUN}-r1-post-gate{level}.log",
                    phase=f"r1 post Gate {level}",
                    deadline=deadline,
                )
        gate1_report = json.loads(gate1_post.read_text(encoding="utf-8"))
        gate2_report = json.loads(gate2_post.read_text(encoding="utf-8"))
        post_gate2_evidence = post / "gate2-evidence.json"
        post_gate2_evidence.write_text(
            json.dumps(
                {
                    "summary": gate2_report["summary"],
                    "config": config,
                    "calibration": (
                        None
                        if pressure_calibration is None
                        else str(pressure_calibration)
                    ),
                    "threshold_profile": threshold_profile,
                    "upright_baseline": str(upright_baseline),
                    "gate1_diagnostic": str(gate1_post),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        gate3_post = post / "gate3"
        gate3_command = [
            sys.executable,
            "-u",
            str(ROOT / "scripts" / "run_gate3_recovery.py"),
            "--gate2-evidence",
            str(post_gate2_evidence),
            "--model",
            str(best_model),
            "--output",
            str(gate3_post),
            "--workers",
            "8",
            "--threshold-profile",
            threshold_profile,
        ]
        gate3_error: str | None = None
        try:
            if not (gate3_post / "gate3-evidence.json").is_file():
                _run_command(
                    gate3_command,
                    log_path=RUNS / f"{BASE_RUN}-r1-post-gate3.log",
                    phase="r1 post Gate 3",
                    deadline=deadline,
                )
        except RuntimeError as exc:
            gate3_error = str(exc)
        gate3_value = (
            json.loads((gate3_post / "gate3-evidence.json").read_text(encoding="utf-8"))
            if (gate3_post / "gate3-evidence.json").is_file()
            else {}
        )
        experiment_selected = bool(
            best_model != initial_model
            and gate1_report["summary"].get("passed") is True
            and gate2_report["summary"].get("passed") is True
            and gate3_value.get("ready_for_r1") is True
        )
        result = {
            "selected_model": str(best_model),
            "selected_model_sha256": _sha256(best_model),
            "initial_model": str(initial_model),
            "chunks": candidates,
            "total_trained_steps": len(candidates) * R1_CHUNK_STEPS,
            "gate1": gate1_report["summary"],
            "gate2": gate2_report["summary"],
            "gate3": gate3_value.get("summary"),
            "gate3_error": gate3_error,
            "experiment_selected": experiment_selected,
            "r1_adopted": experiment_selected and threshold_profile == "strict",
            "canonical_replaced": False,
            "full_12816_evaluation_run": False,
        }
        SELECTION.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_status(state="completed", **result)
        return 0
    except DeadlineReached as exc:
        _log(f"deadline reached during {exc}")
        return _finish(
            candidates, physical_gate=physical_gate, deadline=deadline, state="stopped_deadline"
        )
    except Exception as exc:  # noqa: BLE001 - persist detached worker failure
        _write_status(state="failed", error=repr(exc), candidates=candidates)
        _log(f"recovery failed: {exc!r}")
        return 1

    return 0


def _print_dry_run(physical_gate: Path) -> None:
    print(_preflight(physical_gate))
    pressure_calibration = _physical_gate_calibration(physical_gate)
    parent = _physical_gate_model(physical_gate)
    config = _physical_gate_config(physical_gate)
    for chunk_number in range(1, R1_CHUNKS + 1):
        output = RUNS / f"{BASE_RUN}-r1" / f"chunk-{chunk_number:02d}"
        print(
            subprocess.list2cmdline(
                build_r1_chunk_command(
                    python=Path(sys.executable),
                    parent=parent,
                    output=output,
                    pressure_calibration=pressure_calibration,
                    config=config,
                    first_chunk=chunk_number == 1,
                    threshold_profile=str(
                        json.loads(physical_gate.read_text(encoding="utf-8"))[
                            "threshold_profile"
                        ]
                    ),
                )
            )
        )
        parent = output / "final_model.zip"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--physical-gate", type=Path, default=PHYSICAL_GATE)
    parser.add_argument("--base-run")
    parser.add_argument(
        "--deadline",
        type=parse_deadline,
        default=None,
        help="Local datetime to stop children. Omit or pass none to run until finished.",
    )
    args = parser.parse_args(argv)
    physical_gate = args.physical_gate.resolve()
    try:
        gate_profile = str(
            json.loads(physical_gate.read_text(encoding="utf-8")).get(
                "threshold_profile", "strict"
            )
        )
    except (OSError, json.JSONDecodeError):
        gate_profile = "strict"
    base_run = args.base_run or _default_base_run(gate_profile)
    _configure_run_paths(base_run)
    RUNS.mkdir(parents=True, exist_ok=True)
    deadline_text = "none" if args.deadline is None else args.deadline.isoformat()
    if args.dry_run:
        _print_dry_run(physical_gate)
        print(f"deadline={deadline_text}")
        print(f"parent={PARENT}")
        return 0
    if args.worker:
        return _worker(physical_gate, args.deadline)

    cuda = _preflight(physical_gate)
    command = [
        sys.executable,
        "-u",
        str(Path(__file__).resolve()),
        "--worker",
        "--physical-gate",
        str(physical_gate),
        "--base-run",
        base_run,
    ]
    if args.deadline is not None:
        command.extend(("--deadline", args.deadline.isoformat(sep=" ")))
    with MASTER_LOG.open("ab") as log:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=_environment(),
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=DETACH,
        )
    PIDFILE.write_text(str(process.pid), encoding="ascii")
    print(
        f"spawned recovery pid={process.pid} CUDA={cuda!r} "
        f"deadline={deadline_text} log={MASTER_LOG}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
