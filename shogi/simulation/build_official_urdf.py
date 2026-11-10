"""Generate a kinematic URDF for an extended SO-101 from the official model.

The original link endpoints are retained and the elbow motor travels with the
joint. The CAD-derived link is scaled from mm to metres. The original inertias
are NOT adjusted; the result is for kinematics/static geometry, not dynamics or
proof of real-world safety. This tool does not communicate with hardware.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=ROOT/'vendor/so101-manipulation-eval/assets/so101/so101_new_calib.urdf'
UPSTREAM_SHA256='3a65d2d35e68a8d2f0c2cc176d19b884506543c93ba72980145b80abe276022c'


def _translate_x(element, delta):
    origin=element.find('origin')
    if origin is None: raise ValueError('Expected origin in official model')
    xyz=[float(v) for v in origin.get('xyz','').split()]
    if len(xyz)!=3: raise ValueError('Expected three coordinates in official model')
    xyz[0]+=delta
    origin.set('xyz',' '.join(f'{x:.12g}' for x in xyz))


def build(length_mm, out, source=UPSTREAM):
    if length_mm not in (50,58,75,100,125): raise ValueError('Unsupported generated link length')
    source=Path(source);out=Path(out)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=UPSTREAM_SHA256:
        raise ValueError('Official source differs from the pinned verified SO-101 URDF')
    mesh=ROOT/f'output/upper_arm_extension/Upper_arm_SO101_plus{length_mm}.stl'
    if not mesh.is_file(): raise ValueError('Generate the corresponding STEP/STL link first')
    root=ET.parse(source).getroot()
    root.insert(0,ET.Comment(' KINEMATIC PROTOTYPE ONLY: upper arm extended; '
        'mass/inertia remain stock; no real-arm calibration or motion validation. '))
    upper=root.find("link[@name='upper_arm_link']")
    elbow=root.find("joint[@name='elbow_flex']")
    if upper is None or elbow is None: raise ValueError('Official SO-101 links not found')
    delta=-length_mm/1000
    counts={'upper_visual':0,'upper_collision':0,'motor_visual':0,'motor_collision':0}
    for kind in ('visual','collision'):
        for item in upper.findall(kind):
            elt=item.find('./geometry/mesh')
            if elt is None: continue
            name=elt.get('filename','')
            if name=='assets/upper_arm_so101_v1.stl':
                _translate_x(item,delta)
                elt.set('filename',os.path.relpath(mesh,out.parent))
                elt.set('scale','.001 .001 .001')
                counts['upper_'+kind]+=1
            elif name=='assets/sts3215_03a_v1.stl':
                _translate_x(item,delta)
                counts['motor_'+kind]+=1
    if any(count!=1 for count in counts.values()):
        raise ValueError('Official upper link did not have the expected meshes')
    _translate_x(elbow,delta)
    # The upstream gripper_frame is on one jaw. This additional frame matches
    # the simulation pinch site; actual jaw/piece contact requires calibration.
    link=ET.SubElement(root,'link',{'name':'shogi_pinch_centre_link'})
    joint=ET.SubElement(root,'joint',{'name':'shogi_pinch_centre_joint','type':'fixed'})
    ET.SubElement(joint,'origin',{'xyz':'0.0059 0 -0.1024','rpy':'0 1.5707963267948966 0'})
    ET.SubElement(joint,'parent',{'link':'gripper_link'})
    ET.SubElement(joint,'child',{'link':link.get('name')})
    # All unchanged official meshes resolve to the shared model assets.
    asset_dir=ROOT/'simulation/model/assets'
    for elt in root.findall('.//mesh'):
        name=elt.get('filename','')
        if name.startswith('assets/'):
            path=asset_dir/name.removeprefix('assets/')
            if not path.is_file(): raise ValueError('Official mesh missing: '+str(path))
            elt.set('filename',os.path.relpath(path,out.parent))
    out.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(root,space='  ')
    ET.ElementTree(root).write(out,encoding='utf-8',xml_declaration=True)
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--length-mm',type=int,choices=(50,58,75,100,125),required=True)
    p.add_argument('--out',type=Path,help='URDF destination')
    args=p.parse_args()
    out=args.out or ROOT/f'simulation/model/so101_plus{args.length_mm}_kinematic.urdf'
    print(build(args.length_mm,out))


if __name__=='__main__':main()
