"""Inspect contacts at IK poses for a CAD-derived extended upper-arm mesh.

This is static collision screening, not a trajectory, load, or grasp test.
The upstream inertias and other simplified collision meshes are unchanged.
"""
import argparse
import json
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import mujoco
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'vendor/so101-manipulation-eval/src/sim')]
from board_map import BOARD_X, sim_square
from so101_kinematics import solve_pose_ik, PINCH_SITE, approach_angle_for
from scene import build_scene


def build_extended_model(length_mm,center,scene_options=None):
    tmp=tempfile.TemporaryDirectory(prefix='syogi-extended-')
    path=Path(tmp.name); assets=path/'assets';assets.mkdir()
    original=ROOT/'simulation/model/assets'
    for item in original.iterdir():
        if item.name!='upper_arm_so101_v1.stl': (assets/item.name).symlink_to(item.resolve())
    raw=bytearray((ROOT/f'output/upper_arm_extension/Upper_arm_SO101_plus{length_mm}.stl').read_bytes())
    n=struct.unpack_from('<I',raw,80)[0]
    if len(raw)!=84+n*50: raise ValueError('Unexpected binary STL')
    for i in range(n):
        for j in range(3):
            offset=84+i*50+12+j*12
            x,y,z=struct.unpack_from('<3f',raw,offset)
            struct.pack_into('<3f',raw,offset,(x-length_mm)/1000,y/1000,z/1000)
    (assets/'upper_arm_so101_v1.stl').write_bytes(raw)
    arm=ET.parse(ROOT/'simulation/model/so101_new_calib.xml')
    upper=arm.getroot().find(".//body[@name='upper_arm']")
    if upper is None: raise ValueError('Upper arm body is missing')
    # The elbow motor is modelled as two geoms on upper_arm, not on the
    # lower_arm body. Move both with the elbow joint when lengthening the link.
    motor_geoms=[geom for geom in upper.findall('geom') if geom.get('mesh')=='sts3215_03a_v1']
    if len(motor_geoms)!=2: raise ValueError('Expected visual and collision elbow motor geoms')
    for geom in motor_geoms:
        motor_position=[float(x) for x in geom.get('pos').split()]
        motor_position[0]-=length_mm/1000
        geom.set('pos',' '.join(map(str,motor_position)))
    elbow=arm.getroot().find(".//body[@name='lower_arm']")
    position=[float(x) for x in elbow.get('pos').split()];position[0]-=length_mm/1000
    elbow.set('pos',' '.join(map(str,position)))
    arm.write(path/'extended_arm.xml',encoding='unicode')
    options={'neighbors':False,'board_x':center}
    if scene_options:
        options.update(scene_options)
    scene=build_scene(**options)
    try: root=ET.parse(scene)
    finally: scene.unlink(missing_ok=True)
    root.getroot().find('include').set('file','extended_arm.xml')
    root.write(path/'scene.xml',encoding='unicode')
    model=mujoco.MjModel.from_xml_path(str(path/'scene.xml'))
    return model,tmp


def run(length_mm,center,alternatives=False):
    model,tmp=build_extended_model(length_mm,center)
    try:
        data=mujoco.MjData(model)
        site=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_SITE,PINCH_SITE)
        board=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'shogi_board')
        arm={i for i in range(model.ngeom) if model.geom_group[i]==3}
        arm.update(mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,n) for n in ('jaw_pad_fixed','jaw_pad_moving'))
        def label(geom):
            body=int(model.geom_bodyid[geom])
            return {'geom':mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,geom) or f'geom_{geom}',
                    'body':mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,body) or f'body_{body}'}
        home=np.array([0.,-.55,.95,.82,0.]);grip=approach_angle_for(.023/2,margin_m=.005)
        seeds=[home]
        if alternatives:
            seeds.extend(np.array(x,dtype=float) for x in [
                [0.,-.2,.4,1.2,0.],[0.,.1,-.8,1.,0.],[0.,-1.2,1.4,.5,0.],
                [0.,.8,-1.3,1.4,0.],[0.,-.1,0.,1.,0.],[0.,.7,.4,-.3,0.],
                [0.,-1.,.1,1.7,0.],[0.,.5,1.1,-.4,0.]])
        rows=[]
        for rank in 'abcdefghi':
            for file in range(9,0,-1):
                name=f'{file}{rank}';x,y=sim_square(name,'black');x+=center-BOARD_X
                reachable=False;best_contacts=[];attempts=0
                for seed in seeds:
                    attempts+=1
                    q,err,angle=solve_pose_ik(model,data,site,seed,np.array([x,y,.022]),grip,np.array([0.,0.,-1.]))
                    if err>.004 or angle>15: continue
                    reachable=True;contacts=[]
                    data.qpos[:5]=q;data.qpos[5]=grip;mujoco.mj_forward(model,data)
                    for contact in data.contact[:data.ncon]:
                        a,b=int(contact.geom1),int(contact.geom2)
                        if contact.dist >= -.0005: continue
                        if (a==board and b in arm) or (b==board and a in arm) or (a in arm and b in arm):
                            contacts.append({'geoms':[label(a),label(b)],
                                             'depth_mm':round(float(-contact.dist)*1000,2)})
                    if not contacts:
                        best_contacts=[];break
                    if not best_contacts or len(contacts)<len(best_contacts): best_contacts=contacts
                rows.append({'square':name,'ik_reachable':reachable,'contacts':best_contacts,'attempts':attempts})
        return {'extension_mm':length_mm,'center_mm':center*1000,
                'ik_reachable_count':sum(x['ik_reachable'] for x in rows),
                'ik_reachable_without_detected_penetration':sum(x['ik_reachable'] and not x['contacts'] for x in rows),
                'squares':rows}
    finally: tmp.cleanup()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--length-mm',type=int,choices=(58,75),default=58)
    parser.add_argument('--center-mm',type=float,default=190);parser.add_argument('--alternatives',action='store_true')
    parser.add_argument('--out',type=Path,help='Write results to a specified file')
    args=parser.parse_args()
    result=run(args.length_mm,args.center_mm/1000,args.alternatives)
    result['scope']='Static IK poses, board and model collision meshes only; no path, load, neighbor, grasp or hardware validation.'
    suffix='_alternatives' if args.alternatives else ''
    out=args.out or ROOT/f'output/upper_arm_extension/static_contacts_{args.length_mm}_{int(args.center_mm)}{suffix}.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(f"{result['ik_reachable_without_detected_penetration']}/{result['ik_reachable_count']} reachable poses without detected penetration",flush=True)
