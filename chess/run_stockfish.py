"""Start the installed Stockfish UCI engine on stdin/stdout."""

import argparse
import os
from pathlib import Path
import subprocess


ENGINE = Path(__file__).resolve().parent / "vendor" / "Stockfish" / "engine"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    binary = ENGINE / ("stockfish.exe" if os.name == "nt" else "stockfish")
    if not binary.is_file():
        parser.error(f"Missing {binary}. Run install_game_engine.py chess from the repository root.")
    try:
        return subprocess.call([str(binary)], cwd=ENGINE)
    except OSError as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
