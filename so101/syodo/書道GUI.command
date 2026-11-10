#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
# The server has no external dependencies. Simulation and hardware Python
# interpreters are configured separately in the connection screen.
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$ROOT/scripts/syodo_gui.py" "$@"
fi
echo "Python 3.11以降をインストールしてください。"
exit 1
