"""Search tilted pinch poses for the three remaining near-base squares.

This is an offline static geometry experiment; a tilted pose is not proof that
the real gripper can grasp a shogi piece or clear its neighbours and cables.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import mujoco
import numpy as np

from check_75_mesh_contacts import SurfaceAudit
from study_75_layouts import BOARD_THICKNESS, GRIP, HOME, Study, square_xy
from so101_kinematics import solve_pose_ik

ROOT=Path(__file__).resolve().parents[1]


def search(study,audit,center,square):
    x,y=square_xy(square,center,0.,0.)
    target=np.array([x,y,BOARD_THICKNESS+.010])
    seeds=[HOME.copy() for _ in range(3)]
    seeds[1][4]=math.pi/2;seeds[2][4]=-math.pi/2
    best=[];tested=valid=0
    for tilt in (0.,10.,20.,30.):
        for azimuth in ((0.,) if tilt==0 else range(0,360,45)):
            t,a=math.radians(tilt),math.radians(azimuth)
            desired=np.array([math.sin(t)*math.cos(a),math.sin(t)*math.sin(a),-math.cos(t)])
            for seed in seeds:
                tested+=1
                q,error,angle=solve_pose_ik(study.model,study.data,study.site,seed,target,GRIP,desired)
                if error>.004 or angle>3.: continue
                valid+=1
                study.data.qpos[:5]=q;study.data.qpos[5]=GRIP;mujoco.mj_forward(study.model,study.data)
                hits=study.contacts()
                depth=round(-hits[0][0]*1000,3) if hits else 0.
                item={'q_rad':np.round(q,6).tolist(),'target_tilt_deg':tilt,'azimuth_deg':azimuth,
                      'position_error_mm':round(error*1000,3),'direction_error_deg':round(angle,3),
                      'convex_worst_depth_mm':depth,'convex_clear':not hits}
                if not any(np.linalg.norm(np.array(old['q_rad'])-q)<.01 for old in best):
                    best.append(item);best.sort(key=lambda row:row['convex_worst_depth_mm']);best=best[:6]
                if not hits: break
            if best and best[0]['convex_clear']: break
        if best and best[0]['convex_clear']: break
    for row in best:
        study.data.qpos[:5]=row['q_rad'];study.data.qpos[5]=GRIP;mujoco.mj_forward(study.model,study.data)
        pairs=audit.candidates()
        row['triangle_intersections']=sum(audit.surface_contact(a,b)['triangle_intersection'] for a,b in pairs)
    return {'square':square,'trials':tested,'ik_solutions':valid,'candidates':best}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,default=ROOT/'output/upper_arm_extension/near_pose_search_75.json')
    args=parser.parse_args()
    study=Study();audit=SurfaceAudit(study);layouts=[]
    try:
        for center in (.235,.240):
            study.configure(center,0.,0.,0.)
            rows=[]
            for square in ('9d','9e','9f'):
                row=search(study,audit,center,square);rows.append(row)
                print(center,square,'trials',row['trials'],'IK',row['ik_solutions'],
                      'best',row['candidates'][0] if row['candidates'] else None,flush=True)
            layouts.append({'center_mm':[center*1000,0], 'squares':rows})
        args.out.write_text(json.dumps({'scope':'Static tilted IK poses, 3 seeds and sampled directions. '
            'Triangle rechecks only convex-candidate pairs. No grasp, neighbor, path, cable, '
            'strength, measured calibration or hardware validation.',
            'board_mm':[330,360,12],'pinch_height_mm':10,'layouts':layouts},ensure_ascii=False,indent=2)+'\n')
    finally: study.close()


if __name__=='__main__': main()
