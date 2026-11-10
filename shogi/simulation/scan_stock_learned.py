"""Evaluate an existing learned policy on selected stock-arm board squares.

Only offline MuJoCo is used. These are assumed positions and synthetic nearby
pieces; they are not measurements of reach or proof of real-world grasping.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from board_map import BOARD_X, piece_yaw_deg, sim_square
from teaching_tasks import from_simulation, simulation_fingerprints
from pick_place import run
from train_waypoints import WaypointNet, WaypointPolicy


def load_policy(path):
    checkpoint=torch.load(path,map_location='cpu',weights_only=True)
    net=WaypointNet();net.load_state_dict(checkpoint['model'])
    return WaypointPolicy(net,*(checkpoint[k].numpy() for k in ('xmean','xstd','ymean','ystd')))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--checkpoint',type=Path,default=ROOT/'simulation/runs/waypoint_id5/policy.pt')
    p.add_argument('--squares',nargs='+',default=['9c','3f','3c'])
    p.add_argument('--side',choices=('black','white'),default='white')
    p.add_argument('--center-x',type=float,default=BOARD_X)
    p.add_argument('--out',type=Path,default=ROOT/'simulation/runs/stock_learned_samples.json')
    a=p.parse_args()
    if not np.isfinite(a.center_x) or not .15<=a.center_x<=.40: raise ValueError('Invalid board center')
    torch.set_num_threads(2)
    checkpoint_sha=hashlib.sha256(a.checkpoint.read_bytes()).hexdigest()
    inputs=simulation_fingerprints(ROOT)
    policy=load_policy(a.checkpoint);rows=[]
    for source in a.squares:
        # sim_square validates the square. The test move is a single rank step;
        # it is a grasp experiment, not a claim that this is a legal shogi move.
        src=sim_square(source,a.side,a.center_x)
        rank=ord(source[1])-ord('a');destination=source[0]+chr(ord('a')+(rank-1 if rank else 1))
        target=sim_square(destination,a.side,a.center_x)
        result=run(src,target,board_x=a.center_x,neighbors=True,
                   piece_yaw_deg=piece_yaw_deg(a.side),policy=policy)
        result.pop('trace',None)
        move={'source':source,'destination':destination,'drop':False,'capture':False}
        suggestions=from_simulation(move,result)
        rows.append({'source_square':source,'destination_square':destination,
                     'result':result,'teaching_candidates':suggestions})
        print(source,'->',destination,'success',result['success'],'candidates',suggestions,flush=True)
    if hashlib.sha256(a.checkpoint.read_bytes()).hexdigest()!=checkpoint_sha:
        raise RuntimeError('The checkpoint changed during evaluation; rerun the experiment')
    if simulation_fingerprints(ROOT)!=inputs:
        raise RuntimeError('The simulator changed during evaluation; rerun the experiment')
    report={'scope':'Stock SO-101, learned policy only, simulated square-to-neighbor grasps; '
                    'synthetic nearby pieces, guessed dimensions/friction; no real hardware or board validation.',
            'stock_arm':True,'board_mm':[330,360,12],'board_y_m':0.,'board_yaw_deg':0.,
            'board_center_x_m':a.center_x,'board_side':a.side,
            'checkpoint_sha256':checkpoint_sha,'input_fingerprints':inputs,
            'cases':rows}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
