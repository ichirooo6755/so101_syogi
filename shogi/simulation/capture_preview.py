#!/usr/bin/env python3
"""Independently preview the two transfers of a capture, simulation only.

Each transfer starts in HOME with a freshly initialized simulator. This is not
a continuous capture, does not turn over a promoted piece, and must never be
used as an executable robot trajectory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from adaptive_pick_place import plan
from scene import assumed_stand_center

ROOT=Path(__file__).resolve().parents[1]


def preview(source, destination, obstacles, board_x=.24, promote_captured=False, promote_own=False):
    stand=assumed_stand_center(board_x)
    # The other pieces remain obstacles throughout each independent trial.
    # The attacked piece points at the robot; the attacker's piece points away.
    # Each transfer starts at ID5 cable home and unwinds after a flip.
    first=plan(destination,stand,obstacles=[*obstacles,{'position_m':source,'yaw_deg':0}],
               piece_yaw_deg=180,board_x=board_x,with_stand=True,promote=promote_captured)
    second=plan(source,destination,obstacles=[*obstacles,{'position_m':stand,'yaw_deg':180}],
                piece_yaw_deg=0,board_x=board_x,with_stand=True,promote=promote_own)
    return {'success':False,'sim_only':True,'reason':'capture_preview_only',
            'preview_scope':'two independently initialized transfers; no continuity, stand pile, piece turning, or promotion',
            'stand_xy_m':stand,'captured_to_stand':first,'own_piece_to_board':second}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',nargs=2,type=float,required=True)
    p.add_argument('--target',nargs=2,type=float,required=True)
    p.add_argument('--obstacles-json',required=True)
    p.add_argument('--board-x',type=float,default=.24)
    p.add_argument('--promote-captured',action='store_true')
    p.add_argument('--promote-own',action='store_true')
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    result=preview(args.source,args.target,json.loads(args.obstacles_json),args.board_x,
                   promote_captured=args.promote_captured,promote_own=args.promote_own)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'sim_only':True,'reason':result['reason'],
                      'captured_to_stand':result['captured_to_stand']['success'],
                      'own_piece_to_board':result['own_piece_to_board']['success']},indent=2))


if __name__=='__main__':main()
