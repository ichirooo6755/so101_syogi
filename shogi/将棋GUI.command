#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
if [[ ! -x .venv/bin/python ]]; then
  echo '仮想環境がありません。README のセットアップを実行してください。'
  read -r
  exit 1
fi
exec .venv/bin/python app/server.py
