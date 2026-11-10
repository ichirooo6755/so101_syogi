#!/usr/bin/env python3
"""Compare simulated initial pawn moves for two assumed board placements.

The robot is black and sits opposite the human. This test covers only the nine
initial one-square pawn moves; dimensions, friction and the two distances are
assumptions, and other pieces are fixed obstacles.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from board_map import sim_square
from pick_place import run


def initial_pieces():
    result=[]
    for back,middle,pawn,yaw in [('i','h','g',0),('a','b','c',180)]:
        result.extend((f'{n}{back}',yaw) for n in range(1,10))
        result.extend((f'{n}{middle}',yaw) for n in (2,8))
        result.extend((f'{n}{pawn}',yaw) for n in range(1,10))
    return result


def main():
    entries=[]
    for center in (.245,.265):
        for file in range(1,10):
            source=f'{file}g';target=f'{file}f'
            obstacles=[{'position_m':sim_square(square,'black',center),'yaw_deg':yaw}
                       for square,yaw in initial_pieces() if square!=source]
            report=run(sim_square(source,'black',center),sim_square(target,'black',center),
                       obstacles=obstacles,board_x=center)
            report.pop('trace',None)
            entries.append({'center_x_m':center,'move':source+target,'result':report})
            print(center,source+target,report['success'],report.get('reason',''),flush=True)
    counts={str(c):sum(e['result']['success'] for e in entries if e['center_x_m']==c) for c in (.245,.265)}
    out=ROOT/'simulation/runs/opposing_board_comparison.json'
    out.write_text(json.dumps({'sim_only':True,'scope':'nine initial pawn moves, fixed assumed obstacles',
                               'successes_out_of_nine':counts,'results':entries},indent=2)+'\n')
    print(json.dumps(counts,indent=2),flush=True)


if __name__=='__main__':main()
