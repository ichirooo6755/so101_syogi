"""Compare a few board offsets for the 75 mm upper arm, using static poses.

Only the experiment process changes the scene and square mapping. This does
not command hardware, check motion paths, or validate the assumed board.
"""
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import check_extended_collisions as check

ROOT=Path(__file__).resolve().parents[1]
CONFIGS=[(190,0,0),(200,0,0),(210,0,0),(220,0,0),
         (200,-10,0),(200,10,0),(200,0,-3),(200,0,3)]


def main():
    original_scene=check.build_scene
    original_square=check.sim_square
    results=[]
    for cx,cy,yaw in CONFIGS:
        angle=math.radians(yaw);c=math.cos(angle);s=math.sin(angle)
        def square(name,side):
            x,y=original_square(name,side);dx=x-check.BOARD_X
            return check.BOARD_X+c*dx-s*y, cy/1000+s*dx+c*y
        def scene(*args,**kwargs):
            kwargs['board_y']=cy/1000
            path=original_scene(*args,**kwargs)
            if yaw:
                tree=ET.parse(path)
                board=tree.getroot().find(".//geom[@name='shogi_board']")
                board.set('quat',f'{math.cos(angle/2)} 0 0 {math.sin(angle/2)}')
                tree.write(path,encoding='unicode')
            return path
        check.sim_square=square
        check.build_scene=scene
        try: result=check.run(75,cx/1000,True)
        finally:
            check.sim_square=original_square
            check.build_scene=original_scene
        result['center_y_mm']=cy
        result['board_yaw_deg']=yaw
        result['collision_squares']=[r['square'] for r in result['squares'] if r['ik_reachable'] and r['contacts']]
        result['ik_missing_squares']=[r['square'] for r in result['squares'] if not r['ik_reachable']]
        results.append(result)
        print(f'x={cx} y={cy} yaw={yaw}: IK {result["ik_reachable_count"]}/81; '
              f'no detected penetration {result["ik_reachable_without_detected_penetration"]}/81',flush=True)
    out=ROOT/'output/upper_arm_extension/layout_scan_75_corrected.json'
    out.write_text(json.dumps({'scope':'Static IK and simplified collision meshes only; no trajectory, '
                                      'neighboring pieces, payload, calibration or hardware validation.',
                               'elbow_motor_moved_with_joint':True,
                               'board_assumed_mm':[330,360,12],'results':results},indent=2)+'\n')


if __name__=='__main__': main()
