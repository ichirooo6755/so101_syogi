#!/bin/zsh
# Cursor の子プロセスとして起動するとチャット終了で殺されるため、
# この .command を open して独立セッションで回す。
cd /Users/sugawaraichirou/Documents/syodo
source .venv/bin/activate
export PYTHONPATH=src PYTHONUNBUFFERED=1
export MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mplconfig-syodo
export PYTHONPYCACHEPREFIX=/tmp/pycache-syodo
mkdir -p "$MPLCONFIGDIR" "$PYTHONPYCACHEPREFIX" docs/results runs
echo $$ > runs/overnight.pid
exec /usr/bin/caffeinate -dims zsh scripts/run_overnight_until.sh
