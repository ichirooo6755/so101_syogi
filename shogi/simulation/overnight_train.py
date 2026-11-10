#!/usr/bin/env python3
"""Keep training waypoint policies with board jitter until a local morning cutoff."""
from __future__ import annotations
import json, os, subprocess, sys, time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PYTHON=ROOT/'.venv-sim/bin/python'
TZ=ZoneInfo('Asia/Tokyo')
CUTOFF=datetime(2026,11,1,7,0,tzinfo=TZ)
JOBS=os.cpu_count() or 8


def main():
    if datetime.now(TZ)>=CUTOFF:
        CUTOFF_USE=datetime(2026,11,2,7,0,tzinfo=TZ)
    else:
        CUTOFF_USE=CUTOFF
    out_root=HERE/'runs'/'overnight'
    out_root.mkdir(parents=True,exist_ok=True)
    best={'heldout_learned_successes':-1}
    seed=20261101
    round_id=0
    while datetime.now(TZ)<CUTOFF_USE:
        round_id+=1
        dest=out_root/f'round_{round_id}'
        demo=dest/'imitation'
        way=dest/'waypoint'
        demo.mkdir(parents=True,exist_ok=True)
        board=0.250+0.005*((round_id-1)%7)
        cmd_i=[str(PYTHON),str(HERE/'train_imitation.py'),'--demos','160','--eval','12','--steps','1500',
               '--board-x',str(board),'--jobs',str(JOBS),'--seed',str(seed+round_id),'--out',str(demo)]
        cmd_w=[str(PYTHON),str(HERE/'train_waypoints.py'),'--data',str(demo/'demonstrations.npz'),
               '--out',str(way),'--steps','4000','--eval','12','--heldout-offset','3000','--eval-board-x',str(board)]
        print(f'round {round_id} board_x={board} until {CUTOFF_USE.isoformat()}',flush=True)
        r=subprocess.run(cmd_i)
        if r.returncode!=0 or not (demo/'demonstrations.npz').is_file():
            print('imitation failed',r.returncode,flush=True); continue
        r=subprocess.run(cmd_w)
        report_path=way/'report.json'
        if r.returncode!=0 or not report_path.is_file():
            print('waypoint failed',r.returncode,flush=True); continue
        report=json.loads(report_path.read_text())
        print('learned',report.get('heldout_learned_successes'),'/',report.get('heldout_count'),flush=True)
        if report.get('heldout_learned_successes',-1)>=best['heldout_learned_successes']:
            best=report; (out_root/'best.json').write_text(json.dumps({k:v for k,v in report.items() if k!='evaluation'},indent=2)+'\n')
    print('stopped',datetime.now(TZ).isoformat(),'best',best.get('heldout_learned_successes'),flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
