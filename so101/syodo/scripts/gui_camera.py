#!/usr/bin/env python3
"""Marker-based planar camera calibration and conservative scene relocation."""
import argparse, copy, json, sys
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from scripts.gui_workflow import sha, write_json
from so101_calligraphy.hardware_desk import (load_desk, require_ready, require_joint_ranges,
    env_config_from_desk, lerobot_to_qpos, qpos_to_lerobot, playback_offsets, desk_gripper_map,
    solve_tip_ik, _tip_and_axis, PAPER_CORNERS, REQUIRED_POSES, fit_paper,
    check_taught_plane, _validate_solved_desk, geometry_fingerprint)

CORNERS = ('paper_near_left', 'paper_near_right', 'paper_far_right', 'paper_far_left')

def capture(args):
    with urlopen(Request(args.url.rstrip('/') + '/capture', headers={'User-Agent':'syodo-gui/1'}), timeout=5) as r:
        frame = r.read(4_000_001)
    if len(frame)>4_000_000 or not frame.startswith(b'\xff\xd8') or not frame.endswith(b'\xff\xd9'):
        raise ValueError('カメラ画像がJPEGではありません')
    args.image.parent.mkdir(parents=True, exist_ok=True)
    args.image.write_bytes(frame)

def markers(image):
    try:
        import cv2
    except ImportError as exc:
        raise ValueError('カメラ検出には opencv-contrib-python-headless が必要です。docs/gui.md を参照してください') from exc
    im = cv2.imread(str(image))
    if im is None: raise ValueError('カメラ画像を読めません')
    detector = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50))
    corners, ids, _ = detector.detectMarkers(im)
    if ids is None: raise ValueError('目印を検出できません。全体が写るように明るさとピントを調整してください')
    ids = ids.flatten().tolist()
    if len(ids) != len(set(ids)): raise ValueError('同じ番号の目印が複数あります')
    found = {int(i): np.mean(c.reshape(4,2), axis=0) for i,c in zip(ids,corners)}
    missing = [i for i in range(7) if i not in found]
    if missing: raise ValueError('目印が見えません: ' + ', '.join(map(str, missing)))
    if any(np.linalg.norm(c.reshape(4,2)[0]-c.reshape(4,2)[1]) < 12 for c in corners):
        raise ValueError('目印が小さすぎます。カメラを近づけてください')
    cv2.aruco.drawDetectedMarkers(im,corners,np.array(ids,dtype=np.int32))
    return found, im

def pose_check(before, after, desk):
    a,b = (json.loads(Path(p).read_text()) for p in (before,after))
    if a['desk_sha256'] != sha(desk) or b['desk_sha256'] != sha(desk): raise ValueError('撮影中に較正が変わりました')
    qa,qb = np.asarray(a['qpos']),np.asarray(b['qpos'])
    if qa.shape != (6,) or qb.shape != (6,) or not np.isfinite(qa).all() or not np.isfinite(qb).all() or np.max(np.abs(qa-qb)) > np.deg2rad(.3):
        raise ValueError('撮影中に腕の姿勢が変わりました。静止して撮り直してください')
    return qa

def map_points(H, points):
    p=np.c_[np.asarray(points,dtype=float),np.ones(len(points))] @ np.asarray(H).T
    if np.any(np.abs(p[:,2]) < 1e-9): raise ValueError('画像から座標へ変換できません')
    return p[:,:2]/p[:,2,None]

def calibrate(args):
    import cv2
    desk=require_ready(load_desk(args.desk))
    pose=pose_check(args.before,args.after,args.desk)
    found,im=markers(args.image)
    src=np.array([found[i] for i in range(4)], dtype=np.float64)
    dst=np.array([desk['tips_m'][n][:2] for n in CORNERS],dtype=np.float64)
    H=cv2.getPerspectiveTransform(src.astype('float32'),dst.astype('float32'))
    center=map_points(H,[found[6]])[0]
    error=np.linalg.norm(center-np.asarray(desk['tips_m']['paper_center_touch'][:2]))*1000
    if error>5: raise ValueError(f'紙中央の独立確認が {error:.1f} mm ずれています。目印を実測点に置いて撮り直してください')
    ink=map_points(H,[found[4],found[5]])
    if np.linalg.norm(ink[1]-ink[0]) < .03: raise ValueError('硯の2枚の目印を30 mm以上離してください')
    if 'suzuri_pull' not in desk['poses']: raise ValueError('硯の墨池と引く端を先に記録してください')
    write_json(args.calibration,{'desk_sha256':sha(args.desk),'camera_url':args.url,'image_shape':list(im.shape[:2]),'pose':pose.tolist(),'H':H.tolist(),
        'ink_markers':ink.tolist(),'centre_error_mm':float(error)})
    cv2.imwrite(str(args.overlay),im)
    print(f'カメラ基準を記録しました。中央の確認誤差 {error:.1f} mm。目印は紙面と同じ高さで使ってください。',flush=True)

def detect(args):
    import cv2
    desk=require_ready(load_desk(args.desk))
    pose=pose_check(args.before,args.after,args.desk)
    cal=json.loads(args.calibration.read_text())
    if cal['desk_sha256'] != sha(args.desk): raise ValueError('机の較正が変わりました。カメラ基準から取り直してください')
    if cal.get('camera_url') != args.url: raise ValueError('カメラの接続先が変わりました。基準から取り直してください')
    if np.max(np.abs(pose-np.asarray(cal['pose'])))>np.deg2rad(.5): raise ValueError('カメラ基準の撮影姿勢に腕を戻してください')
    found,im=markers(args.image)
    if list(im.shape[:2]) != cal.get('image_shape'): raise ValueError('画像の解像度が変わりました。カメラ基準から取り直してください')
    pts=map_points(cal['H'],[found[i] for i in range(7)])
    old=np.array([desk['tips_m'][n][:2] for n in CORNERS])
    # A rigid paper transform preserves the measured rectangle and orientation.
    def rigid(a,b):
        ac=a.mean(axis=0); bc=b.mean(axis=0)
        u,_,vt=np.linalg.svd((a-ac).T @ (b-bc))
        rot=vt.T @ u.T
        if np.linalg.det(rot)<0: raise ValueError('目印の並びが反転しています')
        return rot,bc-rot@ac
    rot,trans=rigid(old,pts[:4]); pred=old @ rot.T + trans
    err=float(np.max(np.linalg.norm(pred-pts[:4],axis=1))*1000)
    center_old=np.asarray(desk['tips_m']['paper_center_touch'][:2])
    center_error=float(np.linalg.norm(rot@center_old+trans-pts[6])*1000)
    if err>5 or center_error>5: raise ValueError(f'紙の目印の整合誤差が大きすぎます（四隅 {err:.1f} mm、中央 {center_error:.1f} mm）')
    oldink=np.asarray(cal['ink_markers']); newink=pts[4:6]
    if abs(np.linalg.norm(oldink[1]-oldink[0])-np.linalg.norm(newink[1]-newink[0]))>.003:
        raise ValueError('硯の目印間隔が3 mm以上変わりました。貼り付けと高さを確認してください')
    oldvec=oldink[1]-oldink[0]; newvec=newink[1]-newink[0]
    angle=np.arctan2(oldvec[0]*newvec[1]-oldvec[1]*newvec[0], np.dot(oldvec,newvec))
    c,s=np.cos(angle),np.sin(angle); irot=np.array([[c,-s],[s,c]])
    itrans=newink.mean(axis=0)-irot@oldink.mean(axis=0)
    for label,R,t in [('紙',rot,trans),('硯',irot,itrans)]:
        if np.linalg.norm(t)> .3: raise ValueError(label+'の移動量が大きすぎます。再較正してください')
    proposal={'desk_sha256':sha(args.desk),'paper_rotation':rot.tolist(),'paper_translation_m':trans.tolist(),
      'ink_rotation':irot.tolist(),'ink_translation_m':itrans.tolist(),'paper_error_mm':err,'centre_error_mm':center_error,
      'physical_positions_verified':False}
    write_json(args.proposal,proposal); cv2.imwrite(str(args.overlay),im)
    print('紙と硯の目印を検出しました。画像を確認してから位置に反映してください。',flush=True)

def apply(args):
    desk=require_ready(load_desk(args.desk)); p=json.loads(args.proposal.read_text())
    if p['desk_sha256'] != sha(args.desk): raise ValueError('検出後に較正が変わりました。検出し直してください')
    from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
    env=CalligraphyEnv('line',config=env_config_from_desk(desk)); env.reset(seed=0)
    moved=copy.deepcopy(desk); lim=np.asarray(require_joint_ranges(desk))
    paper=list(CORNERS)+['paper_center_touch','hover_center']
    ink=['suzuri_pool','suzuri_pull']
    try:
        for name in paper+ink:
            old=lerobot_to_qpos(desk['poses'][name],tilt_sign=desk['tilt_sign'],offsets=playback_offsets(desk),gripper_map=desk_gripper_map(desk))
            target,axis=_tip_and_axis(env,old); target=target.copy()
            prefix='paper' if name in paper else 'ink'
            target[:2]=np.asarray(p[prefix+'_rotation'])@target[:2]+np.asarray(p[prefix+'_translation_m'])
            q=old.copy()
            start=_tip_and_axis(env,old)[0].copy()
            for a in np.linspace(0,1,max(2,int(np.ceil(np.linalg.norm(target-start)/.002))+1))[1:]:
                step=start+a*(target-start)
                q=solve_tip_ik(env,step,q,lim,limit_margin_rad=np.deg2rad(2),max_step_rad=np.deg2rad(5),continuity_weight=.002)
                actual,axis=_tip_and_axis(env,q)
                if np.linalg.norm(actual-step)>.001 or np.degrees(np.arccos(np.clip(-axis[2],-1,1)))>8:
                    raise ValueError(name+'への計算経路が届かないか筆が傾きます')
            moved['poses'][name]=qpos_to_lerobot(q,tilt_sign=desk['tilt_sign'],offsets=playback_offsets(desk),gripper_map=desk_gripper_map(desk))
        # Keep the calibrated motor mapping fixed: re-running solve_desk here
        # refits it from the moved paper points and can shift the targets.
        xyz={}
        for name in REQUIRED_POSES:
            q=lerobot_to_qpos(moved['poses'][name],tilt_sign=desk['tilt_sign'],
                offsets=playback_offsets(desk),gripper_map=desk_gripper_map(desk))
            xyz[name]=_tip_and_axis(env,q)[0].copy()
    finally: env.close()
    corners=np.stack([xyz[name] for name in PAPER_CORNERS])
    check_taught_plane(corners)
    moved['tips_m']={name:value.tolist() for name,value in xyz.items()}
    moved['paper']=fit_paper(corners,xyz['paper_center_touch'][2])
    moved['safe_height_m']=float(xyz['hover_center'][2]-moved['paper']['surface_z'])
    moved['inkstone_offset_m']=(np.asarray(desk['inkstone_offset_m']) + xyz['suzuri_pool'] - np.asarray(desk['tips_m']['suzuri_pool'])).tolist()
    moved['suzuri_pull_deg']=moved['poses']['suzuri_pull']
    moved['pressure_calibration_v1']=None
    _validate_solved_desk(moved)
    moved['geometry_fingerprint']=geometry_fingerprint(moved)
    moved['camera_derived_v1']={'source_desk_sha256':p['desk_sha256'],'physical_positions_verified':False,
       'paper_error_mm':p['paper_error_mm'],'centre_error_mm':p['centre_error_mm']}
    # Save only after every predicted pose and native geometry check succeeds.
    write_json(args.desk,moved)
    print('検出した位置を計算して反映しました。筆圧を較正し直し、空中確認を行ってください。',flush=True)

def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['capture','calibrate','detect','apply']);
    for x in ['desk','before','after','image','calibration','proposal','overlay']: p.add_argument('--'+x,type=Path)
    p.add_argument('--url'); args=p.parse_args()
    try: globals()[args.command](args)
    except (ValueError,KeyError,OSError,ImportError) as e: raise SystemExit(str(e)) from e
if __name__=='__main__': main()
