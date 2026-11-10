"""Build a physical SO-101/shogi-piece scene from the upstream MuJoCo model.

All dimensions are initial assumptions, not measurements of the user's board.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import tempfile
import os
import math

MODEL=Path(__file__).resolve().parent/'model'
# Stock lower stop, plus 365° of travel. ID5 can flip once; the cable then
# needs a rewind toward the pose that started the wrap.
WRIST_ROLL_MIN=-2.7438472969992493
WRIST_ROLL_LIMIT=WRIST_ROLL_MIN+math.radians(365)
# Assumed thin board on the table. Z=0 is the bench top under the robot.
BOARD_HEIGHT=.012

def assumed_stand_center(board_x, board_y=0.0):
    """A guessed, single-slot stand location used only for simulation."""
    return (board_x-.04, board_y-.20)

def build_scene(*, width=0.023, length=0.027, thickness=0.007, mass=0.004,
                board_width=0.33, board_length=0.36, board_height=BOARD_HEIGHT,
                board_x=0.24, board_y=0.0, neighbors=True, source=(.20,-.075), target=(.20,-.035), piece_yaw_deg=0.,
                obstacles=None, jaw_friction=2., with_stand=False):
    vals=[width,length,thickness,mass,board_width,board_length,board_height]
    if any(not (0 < x < 1) for x in vals): raise ValueError('Scene dimensions must be positive and less than one metre/kg')
    if not (0.005<=width<=.04 and .008<=length<=.05 and .002<=thickness<=.02):
        raise ValueError('Piece dimensions outside the supported test range')
    root=ET.parse(MODEL/'upstream_scene.xml').getroot()
    if not math.isfinite(jaw_friction) or not .05<=jaw_friction<=3.:
        raise ValueError('Unsupported simulated jaw friction')
    for joint in root.iter('joint'):
        if joint.get('name')=='wrist_roll':
            joint.set('range',f'{WRIST_ROLL_MIN:.8f} {WRIST_ROLL_LIMIT:.8f}')
    for act in root.iter('position'):
        if act.get('joint')=='wrist_roll':
            act.set('ctrlrange',f'{WRIST_ROLL_MIN:.8f} {WRIST_ROLL_LIMIT:.8f}')
    # The upstream model has explicit jaw-pad contacts. Override their sliding
    # friction for sensitivity checks while retaining all other parameters.
    for pair in root.findall('./contact/pair'):
        if pair.get('geom1')=='cube_visual' and pair.get('geom2') in ('jaw_pad_fixed','jaw_pad_moving'):
            pair.set('friction',f'{jaw_friction} {jaw_friction} 0.02 0.002 0.002')
    asset=root.find('asset');world=root.find('worldbody');assert asset is not None and world is not None
    # A convex five-sided slab. Shape, mass and friction are assumed, not measured.
    # The robot's pieces point away from the near edge, along +X.
    points=[(-length/2,-width/2),(-length/2,width/2),(length*.18,width/2),(length/2,0),(length*.18,-width/2)]
    vertices=' '.join(f'{x:.8f} {y:.8f} {z:.8f}' for z in (-thickness/2,thickness/2) for x,y in points)
    ET.SubElement(asset,'mesh',{'name':'shogi_piece_assumed','vertex':vertices})
    # A rigid board on top of the upstream bench. Its footprint is an assumption.
    ET.SubElement(world,'geom',{'name':'shogi_board','type':'box', 'pos':f'{board_x} {board_y} {board_height/2}',
        'size':f'{board_width/2} {board_length/2} {board_height/2}', 'rgba':'.68 .44 .19 1',
        'contype':'1','conaffinity':'3','friction':'.9 .005 .0001','condim':'3'})
    if with_stand:
        # One assumed empty stand; its real location and geometry are unknown.
        stand_x,stand_y=assumed_stand_center(board_x, board_y)
        ET.SubElement(world,'geom',{'name':'shogi_stand','type':'box','pos':f'{stand_x} {stand_y} {board_height/2}',
            'size':f'.050 .045 {board_height/2}','rgba':'.68 .44 .19 1',
            'contype':'1','conaffinity':'3','friction':'.9 .005 .0001','condim':'3'})
    cube=world.find("body[@name='cube']");assert cube is not None
    z=board_height+thickness/2
    cube.set('pos',f'{source[0]} {source[1]} {z}')
    half_yaw=math.radians(piece_yaw_deg)/2
    quat=f'{math.cos(half_yaw):.8f} 0 0 {math.sin(half_yaw):.8f}'
    cube.set('quat',quat)
    geom=cube.find("geom[@name='cube_visual']");assert geom is not None
    geom.set('type','mesh');geom.set('mesh','shogi_piece_assumed');geom.set('mass',str(mass));geom.attrib.pop('size',None)
    # Static neighboring pieces represent collision obstacles, not grasp targets.
    if obstacles is not None:
        if not isinstance(obstacles,list) or len(obstacles)>80:
            raise ValueError('Invalid simulated board obstacles')
        for i,ob in enumerate(obstacles):
            x,y=ob['position_m'];angle=float(ob['yaw_deg']);x=float(x);y=float(y)
            if not all(math.isfinite(v) for v in (x,y,angle)):
                raise ValueError('Non-finite obstacle position')
            half=math.radians(angle)/2
            obstacle_quat=f'{math.cos(half):.8f} 0 0 {math.sin(half):.8f}'
            ET.SubElement(world,'geom',{'name':f'neighbor_{i}','type':'mesh','mesh':'shogi_piece_assumed',
                'pos':f'{x:.6f} {y:.6f} {z:.6f}','quat':obstacle_quat,'rgba':'.89 .70 .38 1',
                'contype':'1','conaffinity':'3','friction':'.9 .005 .0001'})
    elif neighbors:
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx==0 and dy==0: continue
                x=source[0]+dx*board_length/9;y=source[1]+dy*board_width/9
                if abs(x-target[0])<.005 and abs(y-target[1])<.005:continue
                ET.SubElement(world,'geom',{'name':f'neighbor_{dx+1}_{dy+1}','type':'mesh','mesh':'shogi_piece_assumed',
                    'pos':f'{x:.6f} {y:.6f} {z:.6f}','rgba':'.89 .70 .38 1','contype':'1','conaffinity':'3',
                    'friction':'.9 .005 .0001','quat':quat})
    fd,name=tempfile.mkstemp(prefix='shogi_scene_',suffix='.xml',dir=MODEL)
    with os.fdopen(fd,'w',encoding='utf8') as fp:
        ET.ElementTree(root).write(fp,encoding='unicode')
    return Path(name)
