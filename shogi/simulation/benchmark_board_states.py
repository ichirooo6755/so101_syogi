#!/usr/bin/env python3
"""Compare baseline and candidate search on fresh legal shogi board states.

No motor or camera is used. Other pieces are static; moving-piece coordinates
are known exactly. Results cannot be interpreted as real-world success rates.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import shogi

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from board_map import sim_square, simulation_obstacles
from adaptive_pick_place import plan
from pick_place import run


def build_cases(count,seed,noise_mm):
    rng=random.Random(seed);cases=[];seen=set()
    while len(cases)<count:
        board=shogi.Board()
        for _ in range(rng.randrange(6,25)):
            moves=list(board.legal_moves)
            if not moves:break
            board.push(rng.choice(moves))
        moves=[m for m in board.legal_moves if m.from_square is not None and not m.promotion and board.piece_at(m.to_square) is None]
        if not moves:continue
        move=rng.choice(moves);key=(board.sfen(),move.usi())
        if key in seen:continue
        seen.add(key)
        side='black' if board.turn==shogi.BLACK else 'white'
        src=shogi.SQUARE_NAMES[move.from_square];dst=shogi.SQUARE_NAMES[move.to_square]
        sx,sy=sim_square(src,side)
        dx=rng.uniform(-noise_mm,noise_mm)/1000;dy=rng.uniform(-noise_mm,noise_mm)/1000
        cases.append({'sfen':board.sfen(),'move':move.usi(),'robot_side':side,
                      'source_m':[sx+dx,sy+dy],'source_offset_mm':[dx*1000,dy*1000],
                      'target_m':sim_square(dst,side),
                      'obstacles':simulation_obstacles(board,src,board.turn)})
    return cases


def compact(report):
    return {k:v for k,v in report.items() if k!='trace'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--cases',type=int,default=24)
    p.add_argument('--seed',type=int,default=20261101)
    p.add_argument('--noise-mm',type=float,default=2.)
    p.add_argument('--friction',type=float,default=.7)
    p.add_argument('--out',type=Path,default=ROOT/'simulation/runs/fresh_board_benchmark.json')
    a=p.parse_args()
    if not 1<=a.cases<=1000 or not 0<=a.noise_mm<=5:raise ValueError('Invalid benchmark size or offset')
    cases=build_cases(a.cases,a.seed,a.noise_mm);rows=[]
    for i,case in enumerate(cases):
        args=(case['source_m'],case['target_m']);opts={'obstacles':case['obstacles'],'jaw_friction':a.friction}
        baseline=compact(run(*args,**opts))
        adaptive=compact(plan(*args,**opts))
        rows.append({'sfen':case['sfen'],'move':case['move'],'robot_side':case['robot_side'],
                     'source_offset_mm':case['source_offset_mm'],'baseline':baseline,'adaptive':adaptive})
        print(f"{i+1}/{len(cases)} {case['move']} baseline={baseline['success']} adaptive={adaptive['success']}",flush=True)
    report={'sim_only':True,'seed':a.seed,'cases':a.cases,'source_offset_max_mm_per_axis':a.noise_mm,
            'jaw_friction':a.friction,'scope':'fresh legal positions, quiet non-capture non-promotion moves; known coordinates; static obstacles',
            'baseline_successes':sum(r['baseline']['success'] for r in rows),
            'adaptive_successes':sum(r['adaptive']['success'] for r in rows),'results':rows}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2),flush=True)


if __name__=='__main__':main()
