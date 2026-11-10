#!/usr/bin/env python3
"""Try a small, fixed set of contact-checked motions in MuJoCo only.

Every candidate is a fresh offline simulation. A successful result is NOT a
hardware command, and can only support planning under the assumed scene.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pick_place import run

ROOT=Path(__file__).resolve().parents[1]

# Ordered before evaluation. The first choice was tuned on the initial-pawn
# examples; evaluation must use separate board states and label its scope.
CANDIDATES=(
    {'preclear_height':.045,'transit_h':.045,'grip_margin_m':.005,'grasp_height':.010},
    {'preclear_height':.035,'transit_h':.035,'grip_margin_m':.005,'grasp_height':.010},
    {'preclear_height':.028,'transit_h':.028,'grip_margin_m':.005,'grasp_height':.010},
    {'preclear_height':.055,'transit_h':.045,'grip_margin_m':.005,'grasp_height':.010},
    {'preclear_height':.045,'transit_h':.035,'grip_margin_m':.004,'grasp_height':.011},
    {'preclear_height':None,'transit_h':.045,'grip_margin_m':.005,'grasp_height':.010},
)


def plan(source,target,*,obstacles=None,piece_yaw_deg=0.,board_x=.24,with_stand=False,
         jaw_friction=2.,candidates=CANDIDATES,promote=False):
    if not candidates: raise ValueError('At least one candidate is required')
    attempts=[]
    last=None
    for index,parameters in enumerate(candidates):
        result=run(source,target,obstacles=obstacles,piece_yaw_deg=piece_yaw_deg,
                   board_x=board_x,with_stand=with_stand,jaw_friction=jaw_friction,promote=promote,**parameters)
        record={k:v for k,v in result.items() if k!='trace'}
        attempts.append({'parameters':dict(parameters),'result':record})
        last=result
        if result['success']:
            result['selected_candidate']=index
            break
    else:
        last['selected_candidate']=None
    last['planner']='offline_contact_checked_candidates'
    last['candidate_attempts']=attempts
    return last


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',nargs=2,type=float,required=True)
    p.add_argument('--target',nargs=2,type=float,required=True)
    p.add_argument('--yaw-deg',type=float,default=0.)
    p.add_argument('--board-x',type=float,default=.24)
    p.add_argument('--obstacles-json')
    p.add_argument('--promote',action='store_true')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    obstacles=json.loads(a.obstacles_json) if a.obstacles_json is not None else None
    result=plan(a.source,a.target,obstacles=obstacles,piece_yaw_deg=a.yaw_deg,board_x=a.board_x,promote=a.promote)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'sim_only':True,'success':result['success'],
                      'selected_candidate':result['selected_candidate'],
                      'trials':len(result['candidate_attempts'])},indent=2))
    return 0 if result['success'] else 2


if __name__=='__main__':raise SystemExit(main())
