"""Kinematic-only map for the assumed board. Not a hardware reach guarantee."""
import argparse,json,sys
from pathlib import Path
import numpy as np
import mujoco
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'vendor/so101-manipulation-eval/src/sim')]
from board_map import BOARD_X, sim_square
from so101_kinematics import solve_pose_ik,PINCH_SITE,approach_angle_for
from scene import build_scene

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--side',choices=('black','white'),default='black')
    parser.add_argument('--center-x',type=float,default=BOARD_X)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if not np.isfinite(args.center_x) or not .15<=args.center_x<=.45:
        raise ValueError('Board center is outside this simulated scan range')
    xml=build_scene(neighbors=False)
    try:model=mujoco.MjModel.from_xml_path(str(xml))
    finally:xml.unlink(missing_ok=True)
    data=mujoco.MjData(model);site=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_SITE,PINCH_SITE)
    home=np.array([0.,-.55,.95,.82,0.]);grip=approach_angle_for(.023/2,margin_m=.005)
    result=[]
    for rank in 'abcdefghi':
        for file in range(9,0,-1):
            square=f'{file}{rank}';x,y=sim_square(square,args.side);x+=args.center_x-BOARD_X
            _,err,angle=solve_pose_ik(model,data,site,home,np.array([x,y,.022]),grip,np.array([0.,0.,-1.]))
            result.append({'square':square,'xy_m':[round(x,6),round(y,6)],'reachable':bool(err<=.004 and angle<=15),
                           'ik_error_mm':round(err*1000,2),'approach_error_deg':round(angle,2)})
    by_square={r['square']:r for r in result}
    back='i' if args.side=='black' else 'a';middle='h' if args.side=='black' else 'b'
    pawns='g' if args.side=='black' else 'c';pawn_targets='f' if args.side=='black' else 'd'
    own_start=[f'{i}{back}' for i in range(1,10)]+[f'2{middle}',f'8{middle}']+[f'{i}{pawns}' for i in range(1,10)]
    summary={'board_dimensions_mm':[330,360,12],'board_center_m':[args.center_x,0],
             'layout':'robot_and_human_opposite_ends','ai_side':args.side,
             'method':'static IK only, fixed seed and assumed geometry; no collision or robot calibration',
             'reachable_count':sum(r['reachable'] for r in result),'total_count':len(result),
             'own_start_reachable':sum(by_square[s]['reachable'] for s in own_start),'own_start_total':len(own_start),
             'initial_pawn_moves_with_both_poses':sum(by_square[f'{i}{pawns}']['reachable'] and by_square[f'{i}{pawn_targets}']['reachable'] for i in range(1,10)),
             'initial_pawn_moves_total':9,'squares':result}
    path=args.out or ROOT/'simulation/runs'/f'reachability_opposing_{args.side}.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(summary,indent=2)+'\n')
    print(f"own initial {summary['own_start_reachable']}/20, all {summary['reachable_count']}/81 (static IK only), saved {path}",flush=True)
if __name__=='__main__':main()
