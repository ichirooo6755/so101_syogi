"""Start the installed KataGo with the SO-101 model and config."""

import argparse
import os
from pathlib import Path
import subprocess


VENDOR = Path(__file__).resolve().parent / "vendor" / "KataGo"
MODEL = "b10c384h6nbttflrs.bin.gz"
CONFIGS = {"gtp": "default_gtp.cfg", "analysis": "analysis_example.cfg"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=CONFIGS, nargs="?", default="gtp")
    args = parser.parse_args()
    binary = VENDOR / "engine" / ("katago.exe" if os.name == "nt" else "katago")
    model = VENDOR / "models" / MODEL
    config = VENDOR / "config" / CONFIGS[args.mode]
    for path in (binary, model, config):
        if not path.is_file():
            parser.error(f"Missing {path}. Run install_game_engine.py go from the repository root.")
    try:
        return subprocess.call(
            [str(binary), args.mode, "-model", str(model), "-config", str(config)], cwd=VENDOR,
        )
    except OSError as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
