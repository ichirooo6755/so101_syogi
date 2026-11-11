"""Tests only use temporary repositories; no robot or network access."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

SCRIPT = Path(__file__).with_name("show.py")
REPO = SCRIPT.resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("architecture_show", SCRIPT)
show = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(show)


class DiagramTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".diagram-test-", dir=REPO)
        self.root = Path(self.temp.name)
        self.assertEqual(self.root.resolve().parent, REPO.resolve())
        self.previous_root = show.ROOT
        show.ROOT = self.root
        for relative in (show.SOURCE, show.CONFIG, show.PLAN):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / relative, target)
        self.data, self.config = show.load()
        show.sync(self.data, self.config)

    def tearDown(self):
        show.ROOT = self.previous_root
        self.temp.cleanup()

    def contents(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def run_main(self, arguments):
        output, error = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = show.main(arguments)
        return code, output.getvalue(), error.getvalue()

    def test_show_is_read_only_and_sync_is_idempotent(self):
        before = self.contents()
        code, output, error = self.run_main(["show"])
        self.assertEqual((code, error), (0, ""))
        self.assertTrue(output.startswith("```mermaid\nflowchart TB"))
        self.assertEqual(before, self.contents())
        self.assertEqual(show.sync(*show.load()), [])
        self.assertEqual(self.run_main(["check"])[0], 0)

    def test_status_changes_update_all_views_and_keep_history(self):
        for status in ("in_progress", "software_verified", "hardware_verified", "blocked"):
            code, _, error = self.run_main(["set-status", "go_vision", status, "--evidence", "テスト専用の確認条件と結果"])
            self.assertEqual((code, error), (0, ""))
            data, config = show.load()
            module = next(item for item in data["modules"] if item["id"] == "go_vision")
            self.assertEqual(module["status"], status)
            self.assertEqual(module["progress"]["history"][-1]["to"], status)
            self.assertIn("+09:00", module["progress"]["history"][-1]["updated_at"])
            diagram = (self.root / "構成図/構成図.mmd").read_text(encoding="utf-8")
            self.assertRegex(diagram, rf"class [^;\n]*\bgo_vision\b[^;\n]* {status};")
            self.assertIn(diagram.strip(), (self.root / show.PLAN).read_text(encoding="utf-8"))
            self.assertEqual(data["target_architecture"]["diagram"]["source"], diagram.strip())
            self.assertEqual((self.root / show.SOURCE).read_bytes(), (self.root / "docs/shogi-go-architecture-plan.json").read_bytes())
            svg = ET.parse(self.root / "構成図/構成図.svg").getroot()
            node = svg.find(".//{http://www.w3.org/2000/svg}g[@data-module='go_vision']")
            self.assertEqual(node.attrib["data-status"], status)
            self.assertEqual(node.find("{http://www.w3.org/2000/svg}rect").attrib["fill"], data["status_definitions"][status]["style"]["fill"])
            self.assertFalse(data["execution_policy"]["live_motor_commands_enabled"])
            self.assertEqual(self.run_main(["check"])[0], 0)
        self.assertEqual(len(module["progress"]["history"]), 4)

    def test_status_palette_is_read_from_json(self):
        self.data["status_definitions"]["planned"]["style"]["fill"] = "#123abc"
        show.sync(self.data, self.config)
        self.assertIn("classDef planned fill:#123abc", (self.root / "構成図/構成図.mmd").read_text(encoding="utf-8"))
        svg = ET.parse(self.root / "構成図/構成図.svg").getroot()
        node = svg.find(".//{http://www.w3.org/2000/svg}g[@data-module='go_vision']")
        self.assertEqual(node.find("{http://www.w3.org/2000/svg}rect").attrib["fill"], "#123abc")

    def test_open_regenerates_latest_status_and_opens_offline_svg(self):
        show.set_status(self.data, "go_vision", "in_progress", "テスト用の変更")
        (self.root / show.SOURCE).write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        with patch.object(show.webbrowser, "open", return_value=True) as browser:
            code, _, error = self.run_main(["open"])
        self.assertEqual((code, error), (0, ""))
        browser.assert_called_once_with((self.root / "構成図/構成図.svg").as_uri())
        svg = ET.parse(self.root / "構成図/構成図.svg").getroot()
        node = svg.find(".//{http://www.w3.org/2000/svg}g[@data-module='go_vision']")
        self.assertEqual(node.attrib["data-status"], "in_progress")
        self.assertEqual(self.run_main(["check"])[0], 0)

    def test_invalid_updates_do_not_write_any_files(self):
        before = self.contents()
        for arguments in (["set-status", "missing", "planned", "--evidence", "根拠"],
                          ["set-status", "go_vision", "invalid", "--evidence", "根拠"],
                          ["set-status", "go_vision", "implemented", "--evidence", "   "]):
            self.assertEqual(self.run_main(arguments)[0], 2)
            self.assertEqual(before, self.contents())

    def test_invalid_graph_and_missing_plan_marker_do_not_write_outputs(self):
        before = self.contents()
        self.data["target_architecture"]["edges"][0]["to"] = "missing"
        with self.assertRaises(ValueError):
            show.sync(self.data, self.config)
        self.assertEqual(before, self.contents())
        self.data, self.config = show.load()
        path = self.root / show.PLAN
        path.write_text(path.read_text(encoding="utf-8").replace(show.END, ""), encoding="utf-8")
        before = self.contents()
        with self.assertRaises(ValueError):
            show.sync(self.data, self.config)
        self.assertEqual(before, self.contents())

    def test_check_detects_manual_status_change_without_mutating_files(self):
        show.set_status(self.data, "go_vision", "in_progress", "テスト用の変更")
        (self.root / show.SOURCE).write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        before = self.contents()
        self.assertEqual(self.run_main(["check"])[0], 2)
        self.assertEqual(before, self.contents())
        self.assertEqual(self.run_main(["sync"])[0], 0)
        self.assertEqual(self.run_main(["check"])[0], 0)

    def test_plan_text_outside_generated_markers_is_preserved(self):
        path = self.root / show.PLAN
        original = path.read_text(encoding="utf-8")
        before, _, after = original.partition(show.START)
        suffix = after.partition(show.END)[2]
        show.set_status(self.data, "go_ai", "in_progress", "テスト用の変更")
        show.sync(self.data, self.config)
        updated = path.read_text(encoding="utf-8")
        self.assertEqual(updated.partition(show.START)[0], before)
        self.assertEqual(updated.partition(show.END)[2], suffix)

    def test_command_resolves_files_from_any_working_directory(self):
        target = self.root / "構成図/show.py"
        shutil.copyfile(SCRIPT, target)
        result = subprocess.run([sys.executable, str(target), "show", "--format", "mermaid"], cwd=self.temp.name, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("flowchart TB"))

    def test_svg_is_self_contained_and_nodes_and_connectors_do_not_cross(self):
        svg = ET.parse(self.root / "構成図/構成図.svg").getroot()
        ns = "{http://www.w3.org/2000/svg}"
        self.assertFalse(svg.findall(".//" + ns + "script"))
        boxes = {}
        for node in svg.findall(".//" + ns + "g[@data-module]"):
            rectangle = node.find(ns + "rect")
            x, y, w, h = (float(rectangle.attrib[key]) for key in ("x", "y", "width", "height"))
            boxes[node.attrib["data-module"]] = (x, y, x + w, y + h)
        self.assertEqual(len(boxes), 29)
        for ident, (left, top, right, bottom) in boxes.items():
            for other, (x1, y1, x2, y2) in boxes.items():
                if ident != other:
                    self.assertFalse(left < x2 and right > x1 and top < y2 and bottom > y1, f"重なるノード: {ident}, {other}")
        for path in svg.findall(".//" + ns + "path[@data-from]"):
            tokens = re.findall(r"[MVH]|-?\d+(?:\.\d+)?", path.attrib["d"])
            self.assertEqual(tokens.pop(0), "M")
            x, y = float(tokens.pop(0)), float(tokens.pop(0))
            while tokens:
                command, value = tokens.pop(0), float(tokens.pop(0))
                tx, ty = (value, y) if command == "H" else (x, value)
                for ident, (left, top, right, bottom) in boxes.items():
                    if ident in (path.attrib["data-from"], path.attrib["data-to"]):
                        continue
                    crosses = (top < y < bottom and min(x, tx) < right and max(x, tx) > left) if command == "H" else (left < x < right and min(y, ty) < bottom and max(y, ty) > top)
                    self.assertFalse(crosses, f"線がノードを通過: {path.attrib['data-from']} -> {path.attrib['data-to']}: {ident}")
                x, y = tx, ty


if __name__ == "__main__":
    unittest.main()
