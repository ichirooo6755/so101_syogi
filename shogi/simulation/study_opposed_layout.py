"""Static layout screen for a longer SO-101 facing a human across a shogi board.

Uses the official SO-101-derived MuJoCo model and the generated extended link.
An arm riser is represented by lowering the board relative to the robot base;
the riser, neighboring pieces, cables, camera, swept paths and loads are NOT
modelled. Results are neither a motion plan nor evidence of physical reach.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
from study_75_layouts import BOARD_L, BOARD_W, FOCUS, SQUARES, Study

ROOT=Path(__file__).resolve().parents[1]
# Black robot starts on the i rank; both players face each other along ranks.
OPPOSED_FOCUS=('9a','5a','1a','9i','5i','1i','9h','5h','1h')


def square_xy_opposed(square, cx, cy, yaw):
    f=int(square[0]); rank=ord(square[1])-ord('a')
    dx=(4-rank)*BOARD_L/9
    dy=(f-5)*BOARD_W/9
    c,s=math.cos(yaw),math.sin(yaw)
    return cx+c*dx-s*dy,cy+s*dx+c*dy


class OpposedStudy(Study):
    square_xy=staticmethod(square_xy_opposed)

    def __init__(self,extension_mm):
        super().__init__(extension_mm)
        # Board is 360 mm front-to-back and 330 mm across the players.
        self.model.geom_size[self.board,:2]=[BOARD_L/2,BOARD_W/2]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--extensions-mm',type=int,nargs='+',default=[75])
    ap.add_argument('--centers-mm',type=float,nargs='+',default=[250,270,290])
    ap.add_argument('--risers-mm',type=float,nargs='+',default=[0,30,60])
    ap.add_argument('--detail',type=int,default=2,help='Full-board layouts per extension')
    ap.add_argument('--out',type=Path,default=ROOT/'output/upper_arm_extension/opposed_layout.json')
    args=ap.parse_args()
    if any(not 0<=x<=150 for x in args.risers_mm) or any(not 200<=x<=450 for x in args.centers_mm):
        raise ValueError('Invalid assumed board/riser layout')
    if args.detail<0 or args.detail>10: raise ValueError('Invalid full-board sample count')
    results=[]
    for length in args.extensions_mm:
        study=OpposedStudy(length)
        try:
            scans=[]
            for cx,riser in itertools.product(args.centers_mm,args.risers_mm):
                row=study.evaluate(cx/1000,0.,0.,-riser/1000,OPPOSED_FOCUS)
                row['arm_riser_mm']=riser
                scans.append(row)
                print(f"extension {length} riser {riser} center {cx}: "
                      f"base gap {row['base_board_distance_mm']} mm, "
                      f"{row['clear_count']}/{row['total']} focus poses",flush=True)
            ranked=sorted(scans,key=lambda r:(r['base_board_margin_5mm'],r['clear_count'],r['ik_count']),reverse=True)
            detailed=[]
            for row in ranked[:args.detail]:
                d=study.evaluate(row['center_mm'][0]/1000,0.,0.,row['board_bottom_mm']/1000,SQUARES)
                d['arm_riser_mm']=row['arm_riser_mm']
                d['focus_descent']=[study.descent(x,d['center_mm'][0]/1000,0.,0.,d['board_bottom_mm']/1000)
                                    for x in d['squares'] if x['square'] in OPPOSED_FOCUS]
                detailed.append(d)
                print(f"extension {length} full board center {d['center_mm']}: "
                      f"{d['clear_count']}/{d['total']} static poses",flush=True)
            results.append({'extension_mm':length,'focus_scan':scans,'full_board':detailed})
        finally: study.close()
    report={'scope':'Static IK and selected interpolated descents only using assumed dimensions, '
                    'upstream-derived convex meshes, three IK seeds and a fixed downward approach. '
                    'Arm riser/support, desk, neighboring pieces, cables, camera, remaining paths, '
                    'real motor limits, load and real arm are not verified.',
            'board_mm':[360,330,12], 'board_axes':'ranks along robot-to-human X, files across Y',
            'riser_definition':'base elevated above board bottom; riser geometry not modelled',
            'grasp_height_above_board_mm':10,'results':results}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
