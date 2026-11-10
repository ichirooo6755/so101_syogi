from __future__ import annotations

from pathlib import Path

import json

import scripts.collect_pressure_probe as collector


def test_probe_commands_cover_exact_offsets_characters_and_feedback_zero(
    tmp_path: Path,
) -> None:
    commands = collector.diagnostic_commands(tmp_path, python="python")

    assert len(commands) == 7
    assert all(command[:2] == ["python", "-u"] for command in commands)
    offsets = [float(command[command.index("--pressure-probe-offset-m") + 1]) for command in commands]
    assert offsets == list(collector.PROBE_OFFSETS_M)
    assert all(command[command.index("--chars") + 1] == "一三十目書飛鬱誠砕案" for command in commands)
    assert all(command[command.index("--layouts") + 1] == "0,1,2,3,4,5" for command in commands)
    assert all(command[command.index("--pressure-gain") + 1] == "0" for command in commands)


def test_probe_merge_only_preserves_source_configuration_fingerprints(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output = tmp_path / "probe.json"
    parts = tmp_path / "probe-parts"
    commands = collector.diagnostic_commands(parts, python="python")
    parts.mkdir()
    for index, command in enumerate(commands):
        part_path = Path(command[command.index("--output") + 1])
        part_path.write_text(
            json.dumps(
                {
                    "summary": {"configuration_fingerprint": f"config-{index}"},
                    "results": [
                        {
                            "character": "一",
                            "pressure_calibration_samples": [],
                            "worst_clearance": float("inf") if _ == 0 else 0.0,
                        }
                        for _ in range(60)
                    ],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(
        collector,
        "ThreadPoolExecutor",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    assert collector.main(["--output", str(output), "--merge-only"]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert summary["source_configuration_fingerprints"] == [
        f"config-{index}" for index in range(7)
    ]
    assert len(summary["configuration_fingerprint"]) == 64
    assert summary["run"]["status"] == "completed"
    assert summary["run"]["extra"]["device"] == "cpu"
    assert summary["run"]["extra"]["calibration_sha256"] is None
    assert "--merge-only" in summary["run"]["command"]
    assert payload["results"][0]["worst_clearance"] is None
