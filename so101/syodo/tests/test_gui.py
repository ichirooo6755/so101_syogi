"""Local GUI boundaries: no implicit motion, stale plans, serialization and stop."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("syodo_gui", ROOT / "scripts/syodo_gui.py")
gui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gui)


@pytest.fixture
def app(tmp_path):
    root = tmp_path / "syodo"
    (root / "data/hardware").mkdir(parents=True)
    original = json.loads((ROOT / "tests/fixtures/hardware-desk.json").read_text())
    original["poses"]["suzuri_pull"] = deepcopy(original["poses"]["suzuri_pool"])
    original["suzuri_pull_deg"] = original["poses"]["suzuri_pull"]
    gui.write_json(root / "data/hardware/desk.json", original)
    console = gui.Console(root)
    console.save({"sim_python": sys.executable, "hw_python": sys.executable})
    return console


def calibrated(app):
    port = app.root / "fake-follower-usb"
    port.touch()
    leader = app.root / "fake-leader-usb"
    leader.touch()
    app.save({"reach_mm": 180, "paper_depth_mm": 200, "paper_width_mm": 150, "follower_port": str(port), "leader_port": str(leader)})
    desk = gui.read_json(app.desk_path)
    desk.update(ready=True, stale_poses=[], follower_usb_serial="TEST", joint_ranges_rad=[[-3, 3]] * 6, pressure_calibration_v1={"test": True})
    gui.write_json(app.desk_path, desk)
    # Stub the native validation report for API-routing unit tests only.
    # test_gui_workflow.py runs the actual native checks and FK planner.
    gui.write_json(app.data / "validation.json", {"desk_sha256": hashlib.sha256(app.desk_path.read_bytes()).hexdigest(), "geometry_ok": True, "pressure_ok": True, "errors": []})
    assert app.status()["ready"]


def wait_for(predicate, seconds=5):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    pytest.fail("worker timed out")


def test_first_launch_preserves_original_and_invalidates_old_brush(app):
    original = gui.read_json(app.root / "data/hardware/desk.json")
    desk = gui.read_json(app.desk_path)
    assert original["ready"] is True
    assert original["brush_total_cm"] == 12
    assert desk["ready"] is False
    assert desk["pressure_calibration_v1"] is None
    assert set(desk["stale_poses"]) == set(gui.REQUIRED)
    assert desk["suzuri_pull_deg"] is None
    assert "suzuri_pull" not in desk["poses"]
    assert app.settings["brush_length_mm"] == 240
    assert app.settings["tuft_mm"] == 42
    assert app.settings["reach_mm"] is None


def test_brush_length_uses_measured_reach_and_reteaches(app):
    original = (app.root / "data/hardware/desk.json").read_bytes()
    app.save({"reach_mm": 180})
    desk = gui.read_json(app.desk_path)
    assert desk["brush_total_cm"] == 18
    assert desk["brush_rigid_cm"] == pytest.approx(13.8)
    assert desk["brush_tuft_cm"] == 4.2
    assert desk["brush_tip_length_scale"] == pytest.approx(180 / 38)
    assert (app.root / "data/hardware/desk.json").read_bytes() == original
    calibrated(app)
    app.save({"reach_mm": 190})
    assert not app.status()["ready"]
    assert gui.read_json(app.desk_path)["pressure_calibration_v1"] is None


@pytest.mark.parametrize("change", [
    {"reach_mm": 241}, {"reach_mm": 42}, {"reach_mm": float("nan")},
    {"tuft_mm": float("inf")}, {"word": "春夏秋冬春"}, {"word": " "},
    {"word": "春 夏"}, {"speed": 0}, {"camera_enabled": "true"},
    {"camera_url": "file:///etc/passwd"}, {"camera_roi": [0.9, 0, 0.1, 1]},
    {"not_a_setting": "value"},
])
def test_invalid_settings_do_not_write(app, change):
    settings = app.settings_path.read_bytes()
    desk = app.desk_path.read_bytes()
    with pytest.raises(gui.UserError):
        app.save(change)
    assert app.settings_path.read_bytes() == settings
    assert app.desk_path.read_bytes() == desk


def test_camera_changes_preserve_calibration_but_invalidate_prepared_path(app):
    calibrated(app)
    app.prepared = {"key": app.key(), "directory": Path("unused")}
    desk = app.desk_path.read_bytes()
    app.save({"camera_enabled": True})
    assert app.desk_path.read_bytes() == desk
    assert app.status()["ready"]
    assert not app.status()["prepared"]


@pytest.mark.parametrize("action", ["prepare", "write", "bilateral", "snap", "solve", "pressure-calibrate"])
def test_motion_and_preparation_are_blocked_until_calibration(app, action):
    with pytest.raises(gui.UserError):
        app.action(action, {"pose": "upright"})
    assert not app.jobs.active


def capture_jobs(app, monkeypatch):
    captured = []
    monkeypatch.setattr(app.jobs, "start", lambda *args, **kwargs: captured.append((args, kwargs)))
    return captured


def test_bilateral_aligns_first_and_keeps_gui_desk(app, monkeypatch):
    calibrated(app)
    captured = capture_jobs(app, monkeypatch)
    app.action("bilateral", {})
    commands = captured[0][0][2]
    assert [c[1][3] for c in commands] == ["match-leader", "bilateral"]
    for _, cmd in commands:
        assert cmd[cmd.index("--desk") + 1] == str(app.desk_path)
        assert cmd[cmd.index("--port") + 1] == app.settings["follower_port"]
        assert "--leader-port" in cmd


def test_prepare_reads_position_then_checks_all_motion_without_play(app, monkeypatch):
    calibrated(app)
    cache = app.root / "data/kanjivg"
    cache.mkdir(parents=True)
    for char in app.settings["word"]:
        (cache / f"{ord(char):05x}.svg").write_text("<svg/>")
    captured = capture_jobs(app, monkeypatch)
    app.action("prepare", {})
    commands = captured[0][0][2]
    assert [Path(command[2]).name for _, command in commands] == [
        "gui_workflow.py", "hardware_write.py", "audit_hardware_trace.py", "gui_workflow.py",
    ]
    for _, command in commands:
        assert command[0] == sys.executable
        assert command[command.index("--desk") + 1] == str(app.desk_path)
        assert "play" not in command
    assert "snapshot" in commands[0][1]
    assert "--calibrated-heights" in commands[1][1]
    assert "--glyph-mm" in commands[1][1]
    assert not app.status()["prepared"]
    directory = Path(commands[-1][1][-1]).parent
    directory.mkdir(parents=True)
    for name in ("motion.npz", "start.json", "trace.npz"):
        (directory / name).write_bytes(b"fake artifact")
    gui.write_json(directory / "preflight.json", {"passed": True})
    captured[0][1]["success"]()
    assert app.status()["prepared"]
    app.save({"speed": 0.5})
    assert not app.status()["prepared"]


@pytest.mark.parametrize("enabled", [False, True])
def test_write_consumes_matching_preparation_and_uses_saved_settings(app, monkeypatch, enabled):
    calibrated(app)
    app.save({"camera_enabled": enabled})
    captured = capture_jobs(app, monkeypatch)
    directory = app.root / "runs/test"
    directory.mkdir(parents=True)
    (directory / "motion.npz").write_bytes(b"fake artifact")
    app.prepared = {"key": app.key(), "directory": directory, "hashes": {"motion.npz": hashlib.sha256(b"fake artifact").hexdigest()}}
    app.air_verified_key = app.key()  # The preceding physical air test was reviewed.
    app.action("write", {})
    cmd = captured[0][0][2][0][1]
    assert cmd[cmd.index("--settings") + 1] == str(app.settings_path)
    assert cmd[cmd.index("--motion") + 1] == str(directory / "motion.npz")
    assert gui.read_json(app.settings_path)["camera_enabled"] is enabled
    assert Path(cmd[2]).name == "gui_workflow.py"
    assert app.prepared is None
    with pytest.raises(gui.UserError):
        app.action("write", {})


def test_changed_desk_blocks_write_even_when_json_still_says_ready(app):
    calibrated(app)
    app.prepared = {"key": app.key(), "directory": Path("unused")}
    desk = gui.read_json(app.desk_path)
    desk["paper"]["surface_z"] += 0.001
    gui.write_json(app.desk_path, desk)
    with pytest.raises(gui.UserError, match="軌道"):
        app.action("write", {})


def test_pressure_plan_is_required_and_interactive_prompts_are_enabled(app, monkeypatch):
    calibrated(app)
    with pytest.raises(gui.UserError, match="試験軌道"):
        app.action("pressure-calibrate", {})
    captured = capture_jobs(app, monkeypatch)
    app.pressure_plan = {"key": app.key(), "directory": app.root / "runs/test"}
    app.action("pressure-calibrate", {})
    assert captured[0][1]["interactive"] is True
    assert [Path(command[1][2]).name for command in captured[0][0][2]] == ["gui_workflow.py", "gui_workflow.py", "gui_task.py", "gui_workflow.py"]
    assert app.pressure_plan is None


def test_failed_prepare_step_never_advances_to_next_process(tmp_path):
    jobs = gui.Jobs(tmp_path)
    sentinel = tmp_path / "should-not-exist"
    jobs.start("test", "prepare", [
        ("fail", [sys.executable, "-c", "raise SystemExit(7)"]),
        ("next", [sys.executable, "-c", "import sys; open(sys.argv[1], 'w').close()", str(sentinel)]),
    ])
    wait_for(lambda: not jobs.active)
    assert jobs.snapshot()["state"] == "error"
    assert jobs.snapshot()["returncode"] == 7
    assert not sentinel.exists()


def test_only_one_job_can_own_arm_and_stop_prevents_next_command(tmp_path):
    jobs = gui.Jobs(tmp_path)
    sentinel = tmp_path / "should-not-exist"
    jobs.start("test", "bilateral", [
        ("running", [sys.executable, "-u", "-c", "import time; print('started',flush=True); time.sleep(30)"]),
        ("next", [sys.executable, "-c", "import sys; open(sys.argv[1], 'w').close()", str(sentinel)]),
    ])
    wait_for(lambda: any(l["text"] == "started" for l in jobs.snapshot()["lines"]))
    with pytest.raises(gui.UserError):
        jobs.start("other", "write", [])
    jobs.stop()
    wait_for(lambda: not jobs.active)
    assert jobs.snapshot()["state"] == "stopped"
    assert not sentinel.exists()


def test_prompt_requires_current_id_and_explicit_valid_answer(tmp_path):
    jobs = gui.Jobs(tmp_path)
    script = "import json; print('SYODO_GUI_PROMPT:'+json.dumps({'kind':'line','text':'奥側の良い線番号'}),flush=True); print('answer='+input(),flush=True)"
    jobs.start("test", "pressure-calibrate", [("prompt", [sys.executable, "-u", "-c", script])], interactive=True)
    wait_for(lambda: jobs.snapshot()["prompt"] is not None)
    prompt = jobs.snapshot()["prompt"]
    with pytest.raises(gui.UserError):
        jobs.respond("old-id", "1")
    with pytest.raises(gui.UserError):
        jobs.respond(prompt["id"], "9")
    assert jobs.active
    jobs.respond(prompt["id"], "3")
    wait_for(lambda: not jobs.active)
    assert jobs.snapshot()["state"] == "done"
    assert any(l["text"] == "answer=3" for l in jobs.snapshot()["lines"])


def test_http_rejects_cross_origin_commands_and_path_traversal(app):
    server = gui.ThreadingHTTPServer(("127.0.0.1", 0), gui.Handler)
    server.console = app
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert json.load(urlopen(base + "/api/state"))["settings"]["tuft_mm"] == 42
        for headers in [{}, {"X-Syodo-Token": app.token, "Origin": "http://unrelated.invalid"}]:
            request = Request(base + "/api/action", data=b'{"action":"bilateral"}', headers=headers)
            with pytest.raises(HTTPError) as exc:
                urlopen(request)
            assert exc.value.code == 403
        with pytest.raises(HTTPError) as exc:
            urlopen(base + "/../../data/hardware/desk.json")
        assert exc.value.code == 404
        assert not app.jobs.active
    finally:
        server.shutdown()
        server.server_close()


def test_24cm_reach_is_accepted_by_native_geometry():
    from so101_calligraphy.hardware_desk import brush_geometry
    scale, rigid, tuft = brush_geometry(24.0, 4.2)
    assert scale == pytest.approx(0.24 / 0.038)
    assert rigid == pytest.approx(0.198)
    assert tuft == pytest.approx(0.042)


def test_flash_rejects_missing_xiao_port_before_launch(app, monkeypatch):
    captured = capture_jobs(app, monkeypatch)
    with pytest.raises(gui.UserError, match='XIAO'):
        app.action('esp-flash', {'port': '/dev/cu.does-not-exist'})
    assert not captured
