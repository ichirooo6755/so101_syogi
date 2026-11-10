#!/usr/bin/env python3
"""Evaluate a saved simulator-only waypoint model on fresh layouts and both piece orientations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from pick_place import run
from train_imitation import clean, layouts
from train_waypoints import WaypointNet, WaypointPolicy, load_waypoints

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, default=HERE/'runs/waypoint_opposing/policy.pt')
    parser.add_argument('--data', type=Path, default=HERE/'runs/imitation_opposing/demonstrations.npz')
    parser.add_argument('--out', type=Path, default=HERE/'runs/waypoint_opposing/both_sides_report.json')
    parser.add_argument('--seed', type=int, default=20265031)
    parser.add_argument('--layouts', type=int, default=24)
    parser.add_argument('--board-x', type=float, default=.265)
    args = parser.parse_args()
    if args.layouts < 1: raise ValueError('At least one layout is required')
    torch.set_num_threads(2)
    ck=torch.load(args.model,map_location='cpu',weights_only=True)
    net=WaypointNet();net.load_state_dict(ck['model'])
    policy=WaypointPolicy(net,*(ck[k].numpy() for k in ('xmean','xstd','ymean','ystd')))
    train,_=load_waypoints(args.data)
    train_keys={tuple(np.round(row,6)) for row in train}
    cases=layouts(args.seed,args.layouts)
    test_keys={tuple(np.round(np.r_[s,t],6)) for s,t in cases}
    if train_keys & test_keys: raise RuntimeError('Train/evaluation layouts overlap')
    evaluations=[]
    for yaw in (0,180):
        for i,(source,target) in enumerate(cases):
            expert=clean(run(source,target,neighbors=True,piece_yaw_deg=yaw,board_x=args.board_x))
            learned=clean(run(source,target,neighbors=True,piece_yaw_deg=yaw,policy=policy,board_x=args.board_x))
            evaluations.append({'yaw_deg':yaw,'layout':i,'expert':expert,'learned':learned})
            print(f"yaw={yaw} layout {i+1}/{args.layouts}: expert={expert['success']} learned={learned['success']}",flush=True)
    sides={}
    for yaw in (0,180):
        rows=[r for r in evaluations if r['yaw_deg']==yaw]
        sides[str(yaw)]={'cases':len(rows),'expert_successes':sum(r['expert']['success'] for r in rows),
                         'learned_successes':sum(r['learned']['success'] for r in rows)}
    report={'sim_only':True,'seed':args.seed,'board_center_x_m':args.board_x,'layouts_per_orientation':args.layouts,'training_yaw_deg':0,
            'train_eval_layout_overlap':len(train_keys&test_keys),'orientations':sides,
            'no_expert_fallback':all(r['learned'].get('controller')=='learned_policy_no_ik_fallback'
                                     and r['learned'].get('policy_calls',0)>0 for r in evaluations),
            'evaluation':evaluations}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='evaluation'},indent=2),flush=True)


if __name__=='__main__':main()
