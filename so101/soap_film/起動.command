#!/bin/zsh
cd "${0:A:h}"
PYTHON=".venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Python環境がありません。README.md のセットアップ手順をご確認ください。"
  read '?Enter で終了'
  exit 1
fi
export OPENBLAS_NUM_THREADS=1
"$PYTHON" app.py
