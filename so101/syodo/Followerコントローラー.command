#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$HOME/Documents/lerobot-hw/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "LeRobot 実機環境が見つかりません: $PYTHON"
  exit 1
fi
cd "$ROOT"
exec "$PYTHON" "$ROOT/scripts/follower_pad.py"
