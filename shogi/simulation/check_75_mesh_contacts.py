"""Recheck screened 75 mm poses against triangle meshes, offline, with python-fcl.

This is a static triangle-surface check, not an exhaustive volume, swept-path,
clearance, strength, robot-calibration, or hardware test. python-fcl is optional.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import fcl
import mujoco
import numpy as np

from study_75_layouts import FOCUS, GRIP, PENETRATION, Study

ROOT=Path(__file__).resolve().parents[1]


class SurfaceAudit:
    def __init__(self,study):
        self.study=study
        self.meshes={}

    def geometry(self,geom):
        model=self.study.model
        if model.geom_type[geom]==mujoco.mjtGeom.mjGEOM_BOX:
            return fcl.Box(*map(float,2*model.geom_size[geom]))
        if model.geom_type[geom]!=mujoco.mjtGeom.mjGEOM_MESH:
            raise ValueError(f'Unsupported geom type: {model.geom_type[geom]}')
        mesh=int(model.geom_dataid[geom])
        if mesh not in self.meshes:
            va=int(model.mesh_vertadr[mesh]);vn=int(model.mesh_vertnum[mesh])
            fa=int(model.mesh_faceadr[mesh]);fn=int(model.mesh_facenum[mesh])
            vertices=np.array(model.mesh_vert[va:va+vn],dtype=np.float64)
            triangles=np.array(model.mesh_face[fa:fa+fn],dtype=np.int32)
            result=fcl.BVHModel();result.beginModel(vn,fn)
            result.addSubModel(vertices,triangles);result.endModel()
            self.meshes[mesh]=result
        return self.meshes[mesh]

    def obj(self,geom):
        data=self.study.data
        rotation=np.array(data.geom_xmat[geom]).reshape(3,3).copy()
        position=np.array(data.geom_xpos[geom]).copy()
        return fcl.CollisionObject(self.geometry(geom),fcl.Transform(rotation,position))

    def surface_contact(self,a,b):
        first,second=self.obj(a),self.obj(b)
        hit=bool(fcl.collide(first,second,fcl.CollisionRequest(num_max_contacts=1),fcl.CollisionResult()))
        if hit: return {'triangle_intersection':True,'surface_distance_mm':None}
        distance=fcl.distance(first,second,fcl.DistanceRequest(),fcl.DistanceResult())
        return {'triangle_intersection':False,'surface_distance_mm':round(float(distance)*1000,2)}

    def candidates(self):
        s=self.study;data=s.data;pairs={}
        for contact in data.contact[:data.ncon]:
            a,b=int(contact.geom1),int(contact.geom2)
            if contact.dist < PENETRATION and ((a==s.board and b in s.arm) or
                    (b==s.board and a in s.arm) or (a in s.arm and b in s.arm)):
                pairs[(a,b)]=min(pairs.get((a,b),0.),float(contact.dist))
        for a in s.base_geoms:
            for b in s.distal:
                distance=s.pair_distance(a,b)
                if distance<PENETRATION: pairs[(a,b)]=distance
        return pairs

    def label(self,geom):
        s=self.study;m=s.model
        body=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[geom]))
        return {'body':body,'part':s.label(geom),'geom_id':geom}


def run(source):
    study=Study();audit=SurfaceAudit(study)
    try:
        layouts=[]
        for layout in source['full_board']:
            cx,cy=[x/1000 for x in layout['center_mm']]
            yaw=np.deg2rad(layout['yaw_deg']);bottom=layout['board_bottom_mm']/1000
            study.configure(cx,cy,yaw,bottom)
            base=[{'part':audit.label(i),**audit.surface_contact(i,study.board)} for i in study.base_geoms]
            cases=[]
            for row in layout['squares']:
                if row['square'] not in FOCUS[:6] or row['clear'] or not row['ik']: continue
                study.data.qpos[:5]=row['q_rad'];study.data.qpos[5]=GRIP
                mujoco.mj_forward(study.model,study.data)
                pairs=[]
                for (a,b),dist in audit.candidates().items():
                    pairs.append({'geoms':[audit.label(a),audit.label(b)],
                                  'convex_depth_mm':round(-dist*1000,2),**audit.surface_contact(a,b)})
                cases.append({'square':row['square'],'q_rad':row['q_rad'],
                              'triangle_intersections':sum(pair['triangle_intersection'] for pair in pairs),
                              'pairs':pairs})
            layouts.append({'center_mm':layout['center_mm'],'yaw_deg':layout['yaw_deg'],
                            'board_bottom_mm':layout['board_bottom_mm'],
                            'base_board':base,'near_conflicting_poses':cases})
            print('mesh',layout['center_mm'],'base_hits',sum(p['triangle_intersection'] for p in base),
                  'near_cases',[(c['square'],c['triangle_intersections']) for c in cases],flush=True)
        return {'scope':'Triangle-surface recheck of convex candidate pairs at recorded static poses. '
                        'Not an exhaustive posture search, solid containment, swept path, clearance, '
                        'surrounding pieces, actual camera/wires, force or hardware test.',
                'fcl_version':getattr(fcl,'__version__','unknown'),'layouts':layouts}
    finally: study.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,default=ROOT/'output/upper_arm_extension/layout_study_75_base.json')
    parser.add_argument('--out',type=Path,default=ROOT/'output/upper_arm_extension/layout_study_75_mesh.json')
    args=parser.parse_args()
    result=run(json.loads(args.input.read_text()))
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__': main()
