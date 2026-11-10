#!/usr/bin/env python3
"""Adapt the existing pressure calibration's input prompts for the local GUI.

Keep calibration logic, checks and motor cleanup in hardware_write.py. A prompt
is emitted as a complete JSON line; no stdin data is sent until the user answers.
"""
from __future__ import annotations

import builtins
import json
from pathlib import Path
import runpy
import sys


def ask(prompt=""):
    kind = "line" if "良い線番号" in prompt else "continue"
    print("SYODO_GUI_PROMPT:" + json.dumps({"kind": kind, "text": prompt}, ensure_ascii=False), flush=True)
    value = sys.stdin.readline()
    if not value:
        raise EOFError("GUIとの接続が終了しました。")
    if kind == "line" and value.strip() == "none":
        raise SystemExit("良い線がないため筆圧を保存せず終了しました。紙の接触と筆の取り付けを確認してください。")
    return value.rstrip("\r\n")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "pressure-calibrate":
        raise SystemExit("GUIで使えるのは pressure-calibrate です。")
    builtins.input = ask
    target = Path(__file__).with_name("hardware_write.py")
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
