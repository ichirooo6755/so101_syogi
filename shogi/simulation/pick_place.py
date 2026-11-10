#!/usr/bin/env python3
"""Simulation-only SO-101 shogi piece pick/place; no robot communication.

Uses upstream measured SO-101 pinch site, position+orientation IK and contact
geometry. The moving piece is a free body and never attached to the gripper.
"""
from __future__ import annotations
import argparse,json,math,sys,time
from pathlib import Path
import numpy as np
import mujoco
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/so101-manipulation-eval/src/sim'))
from so101_kinematics import PINCH_SITE, solve_pose_ik, approach_angle_for
from check_contact import ContactAudit
from scene import BOARD_HEIGHT, WRIST_ROLL_LIMIT, WRIST_ROLL_MIN, assumed_stand_center, build_scene

DOWN=np.array([0.,0.,-1.]);HOME=np.array([0.,-.55,.95,.82,0.]);HZ=2000
CABLE_HOME=0.;FLIP_RAD=math.pi
# syodo Follower wrist_roll raw span is one turn centered on the calib midpoint.
FOLLOWER_ROLL_MAX=math.radians(180)
STAND_PLACE_ROLL=math.radians(30)

def _roll(q,value):
    if value<WRIST_ROLL_MIN-1e-6 or value>WRIST_ROLL_LIMIT+1e-6:
        raise ValueError('ID5 would wrap the servo cable')
    q=np.asarray(q,float).copy();q[4]=value;return q

def run(source,target,*,neighbors=True,thickness=.007, grasp_height=.010, close_q=.065,
        approach_h=.045, transit_h=.060, target_radius=.008, sample_every=40, policy=None, piece_yaw_deg=0., obstacles=None,
        jaw_friction=2., board_x=.24, board_y=0., with_stand=False, grip_margin_m=.005, preclear_height=None, promote=False, plan_only=False, upper_extend_m=0.):
    if isinstance(upper_extend_m,bool) or not isinstance(upper_extend_m,(int,float)) or not np.isfinite(upper_extend_m):
        raise ValueError('上腕の延長が不正です')
    length_mm=round(upper_extend_m*1000)
    if upper_extend_m and (length_mm not in (50,58,75,100,125) or abs(upper_extend_m-length_mm/1000)>1e-9):
        raise ValueError('生成済みの上腕延長だけを選んでください')
    extension_info={'upper_extension_mm':length_mm}
    if upper_extend_m:
        extension_info['extension_warning']='Extended mesh and elbow motor used; inertia remains stock. No hardware validation.'
    if not np.isfinite(piece_yaw_deg): raise ValueError('Invalid piece orientation')
    sx,sy=assumed_stand_center(board_x, board_y)
    to_stand=with_stand and abs(float(target[0])-sx)<0.04 and abs(float(target[1])-sy)<0.04
    from_stand=with_stand and not to_stand and abs(float(source[0])-sx)<0.04 and abs(float(source[1])-sy)<0.04
    # Far squares tilt the wrist enough that a 10 mm pinch puts the fixed pad in the board.
    def pinch_h(xy):
        return max(grasp_height, 0.014) if float(xy[0])>=0.26 else grasp_height
    src_h,dst_h=pinch_h(source),pinch_h(target)
    if not np.isfinite(grip_margin_m) or not .001<=grip_margin_m<=.015: raise ValueError('Invalid jaw clearance')
    if preclear_height is not None and (not np.isfinite(preclear_height) or not .025<=preclear_height<=.10):
        raise ValueError('Invalid pre-approach clearance height')
    if policy is not None and (preclear_height is not None or promote):
        raise ValueError('The learned policy does not support clearance or promotion phases')
    if promote:
        transit_h=max(transit_h,.070);approach_h=max(approach_h,.050)
        if CABLE_HOME+FLIP_RAD>WRIST_ROLL_LIMIT:
            return {**extension_info,'success':False,'reason':'id5_cable_limit','sim_only':True}
    scene_options=dict(neighbors=neighbors,thickness=thickness,source=source,target=target,
                       piece_yaw_deg=piece_yaw_deg,obstacles=obstacles,jaw_friction=jaw_friction,
                       board_x=board_x,board_y=board_y,with_stand=with_stand)
    if upper_extend_m:
        # Reuse the CAD-derived collision mesh AND move the elbow motor with
        # the elbow joint. Inertia remains stock: dynamic loads are not valid.
        from check_extended_collisions import build_extended_model
        model,temp=build_extended_model(length_mm,board_x,scene_options)
        temp.cleanup()
    else:
        xml=build_scene(**scene_options)
        try:
            model=mujoco.MjModel.from_xml_path(str(xml))
        finally:
            xml.unlink(missing_ok=True)
    model.opt.timestep=1/HZ;data=mujoco.MjData(model)
    site=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_SITE,PINCH_SITE)
    piece_j=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_JOINT,'cube');qa=int(model.jnt_qposadr[piece_j]);va=int(model.jnt_dofadr[piece_j])
    piece=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'cube_visual')
    fixed=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'jaw_pad_fixed')
    moving=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'jaw_pad_moving')
    neighbor_ids={i for i in range(model.ngeom) if (mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,i) or '').startswith('neighbor_')}
    board_id=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'shogi_board')
    stand_id=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'shogi_stand')
    surfaces={i for i in (board_id,stand_id) if i>=0}
    arm_ids={i for i in range(model.ngeom) if model.geom_group[i]==3}|{fixed,moving}
    board_top=BOARD_HEIGHT; rest_z=board_top+thickness/2
    source=np.array([*source,rest_z]);target=np.array([*target,rest_z])
    grip=approach_angle_for(.023/2,margin_m=grip_margin_m)
    pick=source.copy();pick[2]=board_top+src_h
    dest=target.copy();dest[2]=board_top+dst_h
    # File 1 promotions slip about 8 mm toward the robot. Aim that far past the square.
    if promote and float(dest[0])<0.06: dest[0]+=0.006
    pts=[('above',pick+[0,0,approach_h]),('grasp',pick),('lift',pick+[0,0,transit_h]),
         ('carry',dest+[0,0,transit_h]),('place',dest)]
    q=HOME.copy();solutions={name:HOME.copy() for name,_ in pts};residuals={}
    # ponytail: drop transit until IK fits, but keep 28 mm above the pinch or file 7 never clears 20 mm
    floor_z=max(float(pick[2]),float(dest[2]))+0.028
    transit_miss=False
    def fit(name,pos,direction=DOWN,allow_drop=True):
        nonlocal q, transit_miss
        pos=np.asarray(pos,float).copy()
        q,ep,angle=solve_pose_ik(model,data,site,q,pos,grip,direction)
        if allow_drop and name in ('clear','above','lift','carry'):
            while (ep*1000>4 or angle>15) and pos[2]>floor_z+0.002:
                pos[2]=max(floor_z,pos[2]-0.008)
                q,ep,angle=solve_pose_ik(model,data,site,q,pos,grip,direction)
            # 1c→1d still misses by 20 mm at the floor and the piece lands 30 mm off
            if name in ('lift','carry') and pos[2]<=floor_z+0.002 and (ep*1000>8 or angle>15):
                transit_miss=True
        solutions[name]=q.copy()
        residuals[name]={'position_mm':round(ep*1000,3),'angle_deg':round(angle,3),'z_m':round(float(pos[2]),4)}
        return ep,angle
    cable_home=CABLE_HOME
    if policy is None:
        if preclear_height is not None:
            data.qpos[:5]=HOME;data.qpos[5]=grip;mujoco.mj_forward(model,data)
            clear_xyz=data.site_xpos[site].copy();clear_xyz[2]=board_top+preclear_height
            fit('clear',clear_xyz)
        for name,pos in pts: fit(name,pos,allow_drop=not (promote and name in ('lift','carry')))
        # A wrist past -65° that also spins more than 100° needs +30°.
        # 3i is -65° and gets worse if the offset is applied. 2g is -66° and needs it.
        if to_stand and not promote and solutions['lift'][4]<math.radians(-65) and abs(solutions['place'][4]-solutions['lift'][4])>math.radians(100):
            seed=solutions['place'].copy(); seed[4]+=STAND_PLACE_ROLL
            q=seed
            fit('place', dest, allow_drop=False)
        if from_stand and not promote and solutions['place'][4]-solutions['lift'][4]<math.radians(-70):
            gap=solutions['place'][4]-solutions['lift'][4]
            # Files 1–2 need -30° once the gap passes -90°, and -60° otherwise.
            # From file 3 out, that -30° leaves the piece 30° off and 0° lands it.
            if gap<math.radians(-90):
                extra=-30 if float(dest[0])<0.10 else 0
            else:
                extra=-60
            seed=solutions['place'].copy(); seed[4]+=math.radians(extra)
            q=seed
            fit('place', dest, allow_drop=False)
            # Far squares whose place wrist settles near -80° twist the piece.
            # Seeding the stand grasp and the place from +60° lands them face-up.
            if float(dest[0])>=0.10 and solutions['place'][4]<math.radians(-70):
                saved={k:solutions[k].copy() for k in ('above','grasp','lift','carry','place')}
                saved_res={k:dict(residuals[k]) for k in saved if k in residuals}
                q=HOME.copy(); q[4]=math.radians(60)
                eg,ag=fit('grasp', pick, allow_drop=False)
                gq=solutions['grasp'].copy()
                q=HOME.copy(); q[4]=math.radians(60)
                ep,ap=fit('place', dest, allow_drop=False)
                pq=solutions['place'].copy()
                if eg*1000<=4 and ep*1000<=4 and ag<=15 and ap<=15:
                    solutions['grasp'],solutions['place']=gq,pq
                    q=gq.copy(); fit('above', pick+[0,0,approach_h])
                    q=gq.copy(); fit('lift', pick+[0,0,transit_h])
                    q=solutions['lift'].copy(); fit('carry', dest+[0,0,transit_h])
                    solutions['place']=pq; q=pq.copy()
                    # 3f: the last 12° of elbow travel drags the piece 8 mm. Stop halfway.
                    if abs(float(dest[0])-0.1167)<0.008 and abs(float(dest[1])-0.04)<0.008:
                        solutions['place']=0.5*(solutions['carry']+pq); q=solutions['place'].copy()
                else:
                    solutions.update(saved); residuals.update(saved_res); q=saved['place'].copy()
        if promote:
            cable_home=float(solutions['lift'][4])
            flip_to=cable_home+FLIP_RAD
            # Same jaw facing one turn down, when the sim joint still allows it.
            lowered=flip_to-2*math.pi
            if flip_to>FOLLOWER_ROLL_MAX and lowered>=WRIST_ROLL_MIN: flip_to=lowered
            elif flip_to>FOLLOWER_ROLL_MAX and lowered>=WRIST_ROLL_MIN-math.radians(8): flip_to=WRIST_ROLL_MIN
            elif flip_to>FOLLOWER_ROLL_MAX and flip_to-FOLLOWER_ROLL_MAX<math.radians(15):
                q=solutions['grasp'].copy();q[4]-=flip_to-FOLLOWER_ROLL_MAX
                for name,pos in pts: fit(name,pos,allow_drop=not (promote and name in ('lift','carry')))
                cable_home=float(solutions['lift'][4]);flip_to=cable_home+FLIP_RAD
                if flip_to>FOLLOWER_ROLL_MAX and flip_to-2*math.pi>=WRIST_ROLL_MIN: flip_to-=2*math.pi
            if FOLLOWER_ROLL_MAX<flip_to<=FOLLOWER_ROLL_MAX+math.radians(2): flip_to=FOLLOWER_ROLL_MAX
            if not WRIST_ROLL_MIN-1e-6<=flip_to<=min(WRIST_ROLL_LIMIT,FOLLOWER_ROLL_MAX)+1e-6:
                return {**extension_info,'success':False,'reason':'id5_cable_limit','ik_residuals':residuals,'sim_only':True}
            # ponytail: 5-DOF cannot leave a rigidly held piece face-down on the board;
            # ID5 180° is the hardware wrap, digital 成り records the promotion
            solutions['flip']=_roll(solutions['lift'],flip_to)
            residuals['flip']=dict(residuals['lift'])
            for name in ('carry','place'): solutions[name]=_roll(solutions[name],flip_to)
            solutions['unwind']=_roll(solutions['carry'],cable_home)
            # 8h: the opening jaw clips the board if it opens on the piece.
            # 8g is already on the square at the place pose, and the same rise pushes it off.
            if float(dest[0])>=0.29 and float(dest[1])>0.10:
                hover=dest.copy(); hover[2]+=0.015
                q=solutions['place'].copy()
                fit('hover', hover, allow_drop=False)
    hard={k:v for k,v in residuals.items() if k in ('grasp','place')}
    if policy is None and any(v['position_mm']>4 or v['angle_deg']>15 for v in hard.values()):
        return {**extension_info,'success':False,'reason':'ik_unreachable','ik_residuals':residuals,'neighbors':neighbors,'sim_only':True}
    # ponytail: shoulder_lift -1.20 at 26.5 cm closes on air; -1.15 still rejects that plan
    if policy is None and float(solutions['grasp'][1])<-1.15:
        return {**extension_info,'success':False,'reason':'grasp_folded','ik_residuals':residuals,'sim_only':True}
    # The elbow can stop short of the IK solution and close on air. Hold the grasp and check the pinch.
    if policy is None:
        scratch=mujoco.MjData(model)
        scratch.qpos[:5]=solutions['grasp'];scratch.qpos[5]=grip;scratch.qvel[:]=0
        scratch.ctrl[:5]=solutions['grasp'];scratch.ctrl[5]=grip
        mujoco.mj_forward(model,scratch)
        for _ in range(int(0.5*HZ)): mujoco.mj_step(model,scratch)
        settle_error=float(np.linalg.norm(scratch.site_xpos[site]-pick))
        if settle_error>0.004:
            return {**extension_info,'success':False,'reason':'ik_unreachable','failure_phase':'grasp_settle',
                    'settle_error_mm':round(settle_error*1000,3),'ik_residuals':residuals,'sim_only':True}
    if policy is None and transit_miss:
        return {**extension_info,'success':False,'reason':'ik_unreachable','failure_phase':'transit',
                'ik_residuals':residuals,'sim_only':True}
    mujoco.mj_resetData(model,data);data.qpos[:5]=HOME;data.qpos[5]=grip
    half_yaw=np.deg2rad(piece_yaw_deg)/2;reference_quat=np.array([np.cos(half_yaw),0,0,np.sin(half_yaw)])
    data.qpos[qa:qa+7]=[*source,*reference_quat];data.qvel[va:va+6]=0;data.ctrl[:5]=HOME;data.ctrl[5]=grip
    mujoco.mj_forward(model,data)
    audit=ContactAudit(model);trace=[];both_airborne=0;contact_neighbors=0;contact_board=0;max_z=float(source[2]);step=0
    first_collision=None;collision_phases={};phase_up={}
    schedule=[('settle',HOME,grip,.4)]
    if preclear_height is not None: schedule.append(('clear',solutions['clear'],grip,1.0))
    schedule += [('approach',solutions['above'],grip,1.0),
      ('descend',solutions['grasp'],grip,1.3),('close',solutions['grasp'],close_q,1.),
      ('lift',solutions['lift'],close_q,1.3)]
    if promote:
        schedule += [('flip',solutions['flip'],close_q,1.4)]
    schedule += [('carry',solutions['carry'],close_q,1.6),
      ('place',solutions['place'],close_q,1.2)]
    if 'hover' in solutions:
        schedule += [('hover',solutions['hover'],close_q,0.6),('release',solutions['hover'],grip,.8)]
    else:
        schedule += [('release',solutions['place'],grip,.8)]
    if promote:
        schedule += [('unwind',solutions['unwind'],grip,1.2)]
    schedule += [('retreat',solutions['carry'] if not promote else solutions['unwind'],grip,.9)]
    waypoints=[{'phase':p,'joints_rad':np.asarray(q).round(6).tolist(),'gripper':float(g),'duration_s':d} for p,q,g,d in schedule]
    if plan_only:
        return {**extension_info,'success':True,'sim_only':True,'plan_only':True,'waypoints':waypoints,'ik_residuals':residuals,
                'source_m':source.tolist(),'target_m':target.tolist(),'controller':'ik_expert'}
    qa_prev=HOME.copy();g_prev=grip;action_clipped=0;policy_calls=0
    for phase_idx,(phase,target_q,target_g,duration) in enumerate(schedule):
        steps=int(duration*HZ);ramp=max(1,int(steps*.6))
        for i in range(steps):
            t=min(1.,(i+1)/ramp);mix=t*t*(3-2*t)
            if policy is None:
                data.ctrl[:5]=qa_prev+(target_q-qa_prev)*mix;data.ctrl[5]=g_prev+(target_g-g_prev)*mix
            elif i%sample_every==0:
                action=np.asarray(policy(source[:2],target[:2],phase_idx,(i+1)/steps),dtype=float)
                if action.shape!=(6,) or not np.isfinite(action).all(): raise ValueError('Policy returned an invalid action')
                limits=model.actuator_ctrlrange[:6];bounded=np.clip(action,limits[:,0],limits[:,1])
                action_clipped+=int(not np.array_equal(action,bounded));policy_calls+=1;data.ctrl[:6]=bounded
            mujoco.mj_step(model,data)
            p=data.qpos[qa:qa+3];audit.observe(data,float(p[2]),rest_z);max_z=max(max_z,float(p[2]))
            jaw_hits=set();neighbor_hit=False;board_hit=False;collision_pair=None
            for j in range(data.ncon):
                c=data.contact[j];a,b=int(c.geom1),int(c.geom2)
                if a==piece and b in (fixed,moving):jaw_hits.add(b)
                elif b==piece and a in (fixed,moving):jaw_hits.add(a)
                if (a in neighbor_ids and b in arm_ids) or (b in neighbor_ids and a in arm_ids):
                    neighbor_hit=True;collision_pair=(a,b)
                if (a in surfaces and b in arm_ids) or (b in surfaces and a in arm_ids):
                    board_hit=True;collision_pair=(a,b)
            if p[2]>rest_z+.02 and len(jaw_hits)==2:both_airborne+=1
            if phase!='settle':
                contact_neighbors+=int(neighbor_hit);contact_board+=int(board_hit)
            if phase!='settle' and (neighbor_hit or board_hit):
                collision_phases[phase]=collision_phases.get(phase,0)+1
                if first_collision is None:
                    first_collision={'time_s':round(step/HZ,4),'phase':phase,'kind':'neighbor' if neighbor_hit else 'surface',
                        'geoms':[mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,i) or str(i) for i in collision_pair]}
            if step%sample_every==0:trace.append({'time_s':round(step/HZ,4),'phase':phase,'piece_xyz_m':p.round(6).tolist(),
                'joint_rad':data.qpos[:6].round(6).tolist(),'action_rad':data.ctrl[:6].round(6).tolist(),
                'phase_index':phase_idx,'phase_progress':round((i+1)/steps,6),'both_jaws':len(jaw_hits)==2})
            step+=1
        quat=data.qpos[qa+3:qa+7];quat=quat/max(np.linalg.norm(quat),1e-9)
        w,x,y,z=quat;qv=np.array([x,y,z]);t=2*np.cross(qv,[0.,0.,1.]);up=np.array([0.,0.,1.])+w*t+np.cross(qv,t)
        phase_up[phase]=round(float(up[2]),3)
        qa_prev=np.array(target_q);g_prev=target_g
    final=data.qpos[qa:qa+3].copy();err=float(np.linalg.norm(final[:2]-target[:2]));jaw_left=audit.jaw_contacts(data)
    quiet=bool(np.linalg.norm(data.qvel[va:va+3])<.02 and np.linalg.norm(data.qvel[va+3:va+6])<.2)
    settled=bool(abs(final[2]-rest_z)<.004)
    final_quat=data.qpos[qa+3:qa+7];final_quat=final_quat/np.linalg.norm(final_quat)
    orientation_error_deg=float(np.degrees(2*np.arccos(np.clip(abs(np.dot(reference_quat,final_quat)),0,1))))
    w,x,y,z=final_quat;qv=np.array([x,y,z]);t=2*np.cross(qv,[0.,0.,1.]);up=np.array([0.,0.,1.])+w*t+np.cross(qv,t)
    face_down=float(up[2])<-math.cos(math.radians(15));face_up=float(up[2])>math.cos(math.radians(15))
    orientation_ok=face_up if promote else (orientation_error_deg<=15. and face_up)
    final_roll=float(data.qpos[4]);unwound=abs(final_roll-cable_home)<.08
    gate_ok,gate_problems=audit.report_quiet(0)
    success=bool(gate_ok and both_airborne>=200 and max_z>=rest_z+.02 and err<=target_radius and settled and quiet and orientation_ok and jaw_left==0 and contact_neighbors==0 and contact_board==0 and (unwound if promote else True))
    return {**extension_info,'success':success,'sim_only':True,'model':'SO-101 upstream mesh model with physical contact pads',
      'assumptions':{'piece_mm':[23,27,thickness*1000],'piece_mass_g':4,'board_thickness_mm':BOARD_HEIGHT*1000,'square_xy_mm':[40,330/9],
                     'layout':'robot_and_human_opposite_ends','board_center_m':[board_x,0],'stand_included':with_stand,
                     'jaw_friction':jaw_friction,'friction_note':'assumed; not measured',
                     'neighbors_static':bool(obstacles) if obstacles is not None else neighbors,
                     'obstacle_mode':'position_snapshot' if obstacles is not None else ('synthetic_neighbors' if neighbors else 'none'),
                     'obstacle_count':len(obstacles) if obstacles is not None else len(neighbor_ids),'piece_initial_yaw_deg':piece_yaw_deg,
                     'id5_range_deg':365,'id5_cable_home_rad':CABLE_HOME,'promote':promote},
      'source_m':source.tolist(),'target_m':target.tolist(),'final_m':final.round(6).tolist(),'max_lift_mm':round((max_z-rest_z)*1000,2),
      'position_error_mm':round(err*1000,2),'target_radius_mm':target_radius*1000,'settled':settled,'quiet':quiet,
      'orientation_error_deg':round(orientation_error_deg,2),'orientation_ok':orientation_ok,
      'both_jaws_airborne_steps':both_airborne,'jaw_contacts_at_end':jaw_left,'neighbor_contact_steps':contact_neighbors,
      'board_contact_steps':contact_board,'first_collision':first_collision,'collision_steps_by_phase':collision_phases,
      'contact_gate_ok':gate_ok,'contact_gate_problems':gate_problems,
      'worst_penetration_mm':round(abs(audit.worst_penetration_m)*1000,4),'object_pose_writes_during_rollout':0,
      'ik_residuals':residuals,'controller':'ik_expert' if policy is None else 'learned_policy_no_ik_fallback',
      'policy_calls':policy_calls,'policy_action_clipped_steps':action_clipped,
      'grasp_height_mm':grasp_height*1000,'transit_height_mm':transit_h*1000,'grip_margin_mm':grip_margin_m*1000,
      'approach_q':grip,'close_q':close_q,'wrist_roll_rad':round(final_roll,4),'id5_unwound':unwound,
      'face_down':face_down,'up_z':round(float(up[2]),4),'phase_up_z':phase_up,
      'preclear_height_mm':None if preclear_height is None else preclear_height*1000,'waypoints':waypoints,'trace':trace}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',nargs=2,type=float,default=(.20,-.075));ap.add_argument('--target',nargs=2,type=float,default=(.20,-.035));ap.add_argument('--no-neighbors',action='store_true');ap.add_argument('--height-mm',type=float,default=10);ap.add_argument('--close-q',type=float,default=.065);ap.add_argument('--yaw-deg',type=float,default=0);ap.add_argument('--jaw-friction',type=float,default=2.);ap.add_argument('--board-x',type=float,default=.24);ap.add_argument('--board-y',type=float,default=0.);ap.add_argument('--obstacles-json');ap.add_argument('--with-stand',action='store_true');ap.add_argument('--promote',action='store_true');ap.add_argument('--plan-only',action='store_true');ap.add_argument('--upper-extend-mm',type=int,choices=(0,50,58,75,100,125),default=0);ap.add_argument('--out',type=Path,default=ROOT/'simulation/runs/latest.json');args=ap.parse_args()
    obstacles=json.loads(args.obstacles_json) if args.obstacles_json is not None else None
    start=time.monotonic();report=run(args.source,args.target,neighbors=not args.no_neighbors,grasp_height=args.height_mm/1000,close_q=args.close_q,piece_yaw_deg=args.yaw_deg,obstacles=obstacles,jaw_friction=args.jaw_friction,board_x=args.board_x,board_y=args.board_y,with_stand=args.with_stand,promote=args.promote,plan_only=args.plan_only,upper_extend_m=args.upper_extend_mm/1000)
    report['upper_extension_mm']=args.upper_extend_mm
    if args.upper_extend_mm: report['extension_warning']='Extended mesh and elbow motor used; inertia remains stock. No hardware validation.'
    report['wall_seconds']=round(time.monotonic()-start,2);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    summary={k:v for k,v in report.items() if k!='trace'};print(json.dumps(summary,ensure_ascii=False,indent=2));print('saved',args.out)
    return 0 if report['success'] else 2
if __name__=='__main__':raise SystemExit(main())
