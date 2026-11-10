"""Offline study of a 75 mm upper arm, including the normally uncollidable base.

The board, pieces and riser heights are assumptions. This deliberately uses the
upstream convex collision approximations; a negative result may be conservative.
No motors are read or controlled. See the generated report for limitations.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import mujoco
import numpy as np

import check_extended_collisions as extended
from so101_kinematics import PINCH_SITE, approach_angle_for, solve_pose_ik

ROOT = Path(__file__).resolve().parents[1]
BOARD_W, BOARD_L, BOARD_THICKNESS = .330, .360, .012
SQUARES = tuple(f'{n}{r}' for r in 'abcdefghi' for n in range(9, 0, -1))
FOCUS = ('9d', '8d', '9e', '8e', '9f', '8f', '1a', '1e', '1i')
DOWN = np.array([0., 0., -1.])
HOME = np.array([0., -.55, .95, .82, 0.])
GRIP = approach_angle_for(.023 / 2, margin_m=.005)
PENETRATION = -.0005


def square_xy(square, cx, cy, yaw):
    """Black-side orientation, as in app/board_map.py."""
    f = int(square[0]); r = ord(square[1]) - ord('a')
    dx = ((9-f)-4)*BOARD_W/9
    dy = (4-r)*BOARD_L/9
    c, s = math.cos(yaw), math.sin(yaw)
    return cx+c*dx-s*dy, cy+s*dx+c*dy


class Study:
    def __init__(self, extension_mm=75):
        self.model, self.temp = extended.build_extended_model(extension_mm, .210)
        self.data = mujoco.MjData(self.model)
        self.board = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, 'shogi_board')
        self.site = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, PINCH_SITE)
        self.base = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, 'base')
        self.base_geoms = [i for i in range(self.model.ngeom) if self.model.geom_bodyid[i] == self.base]
        self.arm = {i for i in range(self.model.ngeom) if self.model.geom_group[i] == 3}
        self.arm.update(mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, n)
                        for n in ('jaw_pad_fixed', 'jaw_pad_moving'))
        distal_bodies = {mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, n)
                         for n in ('lower_arm', 'wrist', 'gripper', 'moving_jaw_so101_v1')}
        self.distal = [i for i in self.arm if self.model.geom_bodyid[i] in distal_bodies]
        self.seeds = [HOME.copy() for _ in range(3)]
        self.seeds[1][4] = math.pi/2
        self.seeds[2][4] = -math.pi/2

    square_xy = staticmethod(square_xy)

    def close(self):
        self.temp.cleanup()

    def label(self, geom):
        m = self.model
        body = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[geom]))
        name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, geom)
        mesh = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, int(m.geom_dataid[geom]))
                if m.geom_type[geom] == mujoco.mjtGeom.mjGEOM_MESH else None)
        return name or mesh or f'{body}:{geom}'

    def configure(self, cx, cy, yaw, bottom):
        """Move board geometry and recompute MuJoCo's model constants."""
        self.model.geom_pos[self.board] = (cx, cy, bottom + BOARD_THICKNESS/2)
        self.model.geom_quat[self.board] = (math.cos(yaw/2), 0, 0, math.sin(yaw/2))
        mujoco.mj_setConst(self.model, self.data)
        mujoco.mj_forward(self.model, self.data)

    def pair_distance(self, a, b):
        return float(mujoco.mj_geomDistance(self.model, self.data, a, b, 1., None))

    def base_board(self):
        return min((self.pair_distance(i, self.board), self.label(i)) for i in self.base_geoms)

    def contacts(self):
        """Check automatic contacts plus explicitly omitted base/distal pairs."""
        found = []
        for c in self.data.contact[:self.data.ncon]:
            a, b = int(c.geom1), int(c.geom2)
            if c.dist < PENETRATION and ((a == self.board and b in self.arm) or
                                          (b == self.board and a in self.arm) or
                                          (a in self.arm and b in self.arm)):
                found.append((float(c.dist), self.label(a), self.label(b)))
        for a in self.base_geoms:
            for b in self.distal:
                dist = self.pair_distance(a, b)
                if dist < PENETRATION:
                    found.append((dist, self.label(a), self.label(b)))
        return sorted(found)

    def search(self, square, cx, cy, yaw, bottom):
        target = np.array([*self.square_xy(square, cx, cy, yaw), bottom + BOARD_THICKNESS + .010])
        best = None
        for seed in self.seeds:
            q, error, angle = solve_pose_ik(self.model, self.data, self.site, seed, target, GRIP, DOWN)
            if error > .004 or angle > 15:
                continue
            self.data.qpos[:5] = q; self.data.qpos[5] = GRIP
            mujoco.mj_forward(self.model, self.data)
            hits = self.contacts()
            item = {'square':square, 'ik':True, 'clear':not hits,
                    'position_error_mm':round(error*1000, 3), 'angle_error_deg':round(angle, 3),
                    'q_rad':np.round(q, 6).tolist(),
                    'worst_contact':None if not hits else {'depth_mm':round(-hits[0][0]*1000, 2),
                                                            'geoms':list(hits[0][1:])}}
            if not hits:
                return item
            if best is None or item['worst_contact']['depth_mm'] < best['worst_contact']['depth_mm']:
                best = item
        return best or {'square':square, 'ik':False, 'clear':False}

    def descent(self, row, cx, cy, yaw_deg, bottom):
        """Try a 25 mm descent, checking linear joint interpolation at <=2 degrees."""
        if not row['clear']:
            return {'square':row['square'], 'checked':False, 'reason':'grasp_pose_not_clear'}
        yaw=math.radians(yaw_deg)
        x,y=self.square_xy(row['square'],cx,cy,yaw)
        target=np.array([x,y,bottom+BOARD_THICKNESS+.035])
        q_grasp=np.array(row['q_rad'])
        q_above,err,angle=solve_pose_ik(self.model,self.data,self.site,q_grasp,target,GRIP,DOWN)
        if err>.004 or angle>15:
            return {'square':row['square'],'checked':False,'reason':'pregrasp_ik_missing',
                    'position_error_mm':round(err*1000,2),'angle_error_deg':round(angle,2)}
        steps=max(1,math.ceil(float(np.max(np.abs(q_grasp-q_above)))/math.radians(2)))
        worst=None; max_xy=0.
        for fraction in np.linspace(0.,1.,steps+1):
            self.data.qpos[:5]=(1-fraction)*q_above+fraction*q_grasp
            self.data.qpos[5]=GRIP
            mujoco.mj_forward(self.model,self.data)
            max_xy=max(max_xy,float(np.linalg.norm(self.data.site_xpos[self.site,:2]-[x,y])))
            hits=self.contacts()
            if hits and (worst is None or hits[0][0]<worst[0]): worst=hits[0]
        return {'square':row['square'],'checked':True,'sample_count':steps+1,
                'clear':worst is None,'max_xy_deviation_mm':round(max_xy*1000,2),
                'pregrasp_q_rad':np.round(q_above,6).tolist(),
                'worst_contact':None if worst is None else {'depth_mm':round(-worst[0]*1000,2),
                                                             'geoms':list(worst[1:])}}

    def evaluate(self, cx, cy, yaw_deg, bottom, squares):
        yaw = math.radians(yaw_deg)
        self.configure(cx, cy, yaw, bottom)
        distance, base_part = self.base_board()
        rows = [self.search(square, cx, cy, yaw, bottom) for square in squares]
        return {'center_mm':[round(cx*1000,1),round(cy*1000,1)], 'yaw_deg':yaw_deg,
                'board_bottom_mm':round(bottom*1000,1),
                'base_board_distance_mm':round(distance*1000,2), 'closest_base_mesh':base_part,
                'base_board_clear':distance >= PENETRATION,
                'base_board_margin_5mm':distance >= .005,
                'ik_count':sum(row['ik'] for row in rows), 'clear_count':sum(row['clear'] for row in rows),
                'total':len(rows), 'squares':rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT/'output/upper_arm_extension/layout_study_75_base.json')
    args = parser.parse_args()
    study = Study()
    try:
        initial = []
        # Board bottom is raised on a separate support; its thickness stays 12 mm.
        for cx, bottom, cy in itertools.product((.210, .230, .250), (0., .040, .080), (0., -.020, .020)):
            result = study.evaluate(cx, cy, 0., bottom, FOCUS)
            initial.append(result)
            print('focus',result['center_mm'],result['board_bottom_mm'],
                  'base',result['base_board_distance_mm'],'clear',result['clear_count'],flush=True)
        # Refine the transition between near-end interference and far-end reach.
        for cx, yaw in itertools.product((.220,.225,.230,.235,.240),(-5.,0.,5.)):
            result = study.evaluate(cx,0.,yaw,0.,FOCUS)
            initial.append(result)
            print('fine',result['center_mm'],yaw,'base',result['base_board_distance_mm'],
                  'clear',result['clear_count'],flush=True)
        # Always test 210/0/0 as a baseline and the narrow region in 5 mm steps.
        ranked = sorted(initial, key=lambda r:(r['base_board_margin_5mm'],r['clear_count'],
                                               r['ik_count'],r['base_board_distance_mm']), reverse=True)
        chosen = [initial[0]]
        for cx in (230.,235.,240.):
            chosen.append(next(r for r in initial if r['center_mm']==[cx,0.] and
                               r['yaw_deg']==0. and r['board_bottom_mm']==0.))
        for row in ranked:
            if row not in chosen:
                chosen.append(row)
            if len(chosen) == 6:
                break
        detailed = []
        for row in chosen:
            result = study.evaluate(row['center_mm'][0]/1000,row['center_mm'][1]/1000,
                                    row['yaw_deg'],row['board_bottom_mm']/1000,SQUARES)
            result['focus_descent']=[study.descent(r,row['center_mm'][0]/1000,row['center_mm'][1]/1000,
                                                   row['yaw_deg'],row['board_bottom_mm']/1000)
                                     for r in result['squares'] if r['square'] in FOCUS[:6]]
            detailed.append(result)
            print('all',result['center_mm'],result['board_bottom_mm'],'base',result['base_board_distance_mm'],
                  'IK',result['ik_count'],'clear',result['clear_count'],flush=True)
        report = {'scope':'Static poses and sampled short descents only, approximate convex collision meshes, 3 IK seeds. '
                          'Base-board and base-distal are checked explicitly; adjacent pieces, motion paths, '
                          'camera, wires, support, torque, calibration and hardware are not checked.',
                  'board_mm':[330,360,12], 'height_definition':'bottom of board above table',
                  'grasp_center_above_board_mm':10, 'extension_mm':75,
                  'focus_scan':initial, 'full_board':detailed}
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    finally:
        study.close()


if __name__ == '__main__':
    main()
