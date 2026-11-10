"""Static IK comparison: stock versus lengthened ID2-ID3 link.

Only the elbow body origin is moved; mesh, inertia, torque, wiring and all
collisions are unchanged. This is NOT a physical or trajectory test.
"""
import argparse
import json
import sys
from pathlib import Path
import mujoco
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'vendor/so101-manipulation-eval/src/sim')]
from board_map import BOARD_X, sim_square
from so101_kinematics import solve_pose_ik, PINCH_SITE, approach_angle_for
from scene import build_scene


def run(extension, center):
    scene=build_scene(neighbors=False)
    try: model=mujoco.MjModel.from_xml_path(str(scene))
    finally: scene.unlink(missing_ok=True)
    body=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'lower_arm')
    model.body_pos[body,0]-=extension
    data=mujoco.MjData(model)
    site=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_SITE,PINCH_SITE)
    home=np.array([0.,-.55,.95,.82,0.])
    grip=approach_angle_for(.023/2,margin_m=.005)
    squares=[]
    for rank in 'abcdefghi':
        for file in range(9,0,-1):
            square=f'{file}{rank}'
            x,y=sim_square(square,'black'); x+=center-BOARD_X
            _,err,angle=solve_pose_ik(model,data,site,home,np.array([x,y,.022]),grip,np.array([0.,0.,-1.]))
            squares.append({'square':square,'reachable':bool(err<=.004 and angle<=15),
                            'ik_error_mm':round(err*1000,2),'angle_error_deg':round(angle,2)})
    count=sum(x['reachable'] for x in squares)
    print(f'extension={extension*1000:.0f} mm center={center*1000:.0f} mm: {count}/81',flush=True)
    return {'extension_mm':extension*1000,'board_center_mm':center*1000,
            'reachable_count':count,'total':81,'squares':squares}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--extensions-mm',nargs='+',type=float,default=[0,50])
    parser.add_argument('--centers-mm',nargs='+',type=float,default=[240,270,300])
    parser.add_argument('--out',type=Path,default=ROOT/'output/upper_arm_extension/kinematic_comparison.json')
    args=parser.parse_args()
    results=[run(ext/1000,center/1000) for ext in args.extensions_mm for center in args.centers_mm]
    out=args.out
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'scope':'static IK only; original link mesh and inertia; no collisions or hardware',
                               'results':results},indent=2)+'\n')
