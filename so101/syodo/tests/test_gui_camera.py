import argparse
import json
from pathlib import Path
import cv2
import numpy as np
import pytest
from scripts import gui_camera as camera


def image(path, points):
    im=np.full((1000,1200,3),255,dtype=np.uint8)
    dictionary=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    for i,(x,y) in enumerate(points):
        tag=cv2.aruco.generateImageMarker(dictionary,i,80)
        im[y-40:y+40,x-40:x+40]=cv2.cvtColor(tag,cv2.COLOR_GRAY2BGR)
    assert cv2.imwrite(str(path),im)


def test_real_aruco_detector_finds_all_printed_codes(tmp_path):
    points=[(200,200),(200,600),(700,600),(700,200),(850,200),(950,200),(450,400)]
    path=tmp_path/'frame.jpg'; image(path,points)
    result,_=camera.markers(path)
    assert set(result) == set(range(7))
    for i,point in enumerate(points): assert np.linalg.norm(result[i]-point)<2


def test_calibration_detects_scene_shift_and_rejects_moving_camera(tmp_path,monkeypatch):
    desk_path=tmp_path/'desk.json'; desk_path.write_text('{}')
    points=[(200,200),(200,600),(700,600),(700,200),(850,200),(950,200),(450,400)]
    points2=[(x+10,y+20) if i in (0,1,2,3,6) else (x+15,y+5) for i,(x,y) in enumerate(points)]
    initial=tmp_path/'first.jpg'; shifted=tmp_path/'next.jpg'; image(initial,points); image(shifted,points2)
    world={n:[v[0],v[1],0] for n,v in zip(camera.CORNERS,[(.1,-.08),(.1,.08),(.3,.08),(.3,-.08)])}
    world['paper_center_touch']=[.2,0,0]
    desk={'tips_m':world,'poses':{'suzuri_pull':{}}}
    monkeypatch.setattr(camera,'load_desk',lambda p: desk)
    monkeypatch.setattr(camera,'require_ready',lambda d:d)
    before=tmp_path/'before.json'; after=tmp_path/'after.json'
    snap={'desk_sha256':camera.sha(desk_path),'qpos':[0]*6}
    before.write_text(json.dumps(snap)); after.write_text(json.dumps(snap))
    args=argparse.Namespace(desk=desk_path,before=before,after=after,image=initial,calibration=tmp_path/'cal.json',proposal=tmp_path/'proposal.json',overlay=tmp_path/'overlay.jpg',url='http://camera')
    camera.calibrate(args)
    args.image=shifted; camera.detect(args)
    result=json.loads(args.proposal.read_text())
    assert result['paper_error_mm']<1 and result['centre_error_mm']<1
    assert result['physical_positions_verified'] is False
    assert np.linalg.norm(result['paper_translation_m'])>0
    snap['qpos'][0]=np.deg2rad(1); after.write_text(json.dumps(snap))
    with pytest.raises(ValueError,match='姿勢が変わりました'): camera.detect(args)


def test_incorrect_centre_rejects_without_writing_calibration(tmp_path,monkeypatch):
    desk_path=tmp_path/'desk.json'; desk_path.write_text('{}')
    points=[(200,200),(200,600),(700,600),(700,200),(850,200),(950,200),(490,400)]
    frame=tmp_path/'frame.jpg'; image(frame,points)
    world={n:[v[0],v[1],0] for n,v in zip(camera.CORNERS,[(.1,-.08),(.1,.08),(.3,.08),(.3,-.08)])};world['paper_center_touch']=[.2,0,0]
    monkeypatch.setattr(camera,'load_desk',lambda p:{'tips_m':world,'poses':{'suzuri_pull':{}}})
    monkeypatch.setattr(camera,'require_ready',lambda d:d)
    snap=tmp_path/'pose.json'; snap.write_text(json.dumps({'desk_sha256':camera.sha(desk_path),'qpos':[0]*6}))
    args=argparse.Namespace(desk=desk_path,before=snap,after=snap,image=frame,calibration=tmp_path/'cal.json',overlay=tmp_path/'overlay.jpg',url='http://camera')
    with pytest.raises(ValueError,match='中央'): camera.calibrate(args)
    assert not args.calibration.exists()


def test_apply_shifted_proposal_runs_ik_and_native_desk_solver(tmp_path):
    from so101_calligraphy.hardware_desk import load_desk
    source=Path(__file__).resolve().parents[1]/'tests/fixtures/hardware-desk.json'
    desk=load_desk(source)
    # Synthetic upright ink points exercise the successful path without hardware.
    from so101_calligraphy.hardware_desk import solve_desk
    limits=desk['joint_ranges_rad']
    desk['poses']['suzuri_pool']=desk['poses']['paper_center_touch'].copy()
    desk['poses']['suzuri_pull']=desk['poses']['paper_near_left'].copy()
    desk=solve_desk(desk)
    desk['joint_ranges_rad']=limits
    path=tmp_path/'desk.json'; path.write_text(json.dumps(desk))
    proposal={'desk_sha256':camera.sha(path),'paper_rotation':[[1,0],[0,1]],'paper_translation_m':[.002,.001],
        'ink_rotation':[[1,0],[0,1]],'ink_translation_m':[.002,.001],'paper_error_mm':0,'centre_error_mm':0}
    prop=tmp_path/'proposal.json'; prop.write_text(json.dumps(proposal))
    camera.apply(argparse.Namespace(desk=path,proposal=prop))
    result=json.loads(path.read_text())
    assert result['camera_derived_v1']['physical_positions_verified'] is False
    assert result['pressure_calibration_v1'] is None
    assert result['ready'] is True
    shift=np.asarray(result['tips_m']['paper_center_touch'])[:2]-np.asarray(desk['tips_m']['paper_center_touch'])[:2]
    assert np.linalg.norm(shift-np.array([.002,.001])) < .0015
    with pytest.raises(ValueError,match='検出後'): camera.apply(argparse.Namespace(desk=path,proposal=prop))
