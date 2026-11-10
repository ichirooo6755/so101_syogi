"""Record manual demonstrations as evidence; never command or replay an arm."""
from __future__ import annotations

import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import tempfile
import uuid

NAMES = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper')
PHASES = (
    ('approach', '駒の上に近づく（爪を開く）'),
    ('align', '駒に爪を合わせる（まだ開く）'),
    ('grasp', '駒をつかむ（爪を閉じる）'),
    ('lift', '駒を持ち上げる'),
)
PLACE_PHASES = (
    ('approach_loaded', '駒を持ったままマスの上へ近づく'),
    ('align_loaded', '駒を置く位置まで下ろす'),
    ('release', '爪を開いて駒を離す'),
    ('retreat', '爪を駒から離す'),
)
DIRECTORY = Path.home()/'.cache'/'so101-shogi'/'teaching'


def begin(square, side, board_estimate, directory=DIRECTORY, mode='leader', operation='pick', issue=None):
    if not isinstance(square,str) or not re.fullmatch(r'[1-9][a-i]',square):
        raise ValueError('マスは 9e のように指定してください')
    if side not in ('black','white'):
        raise ValueError('ロボットの先手・後手を選んでください')
    if mode not in ('leader','manual'):
        raise ValueError('教え方を選んでください')
    if operation not in ('pick','place'):
        raise ValueError('駒を取る動きか置く動きを選んでください')
    if not isinstance(board_estimate,dict):
        raise ValueError('盤の設定が不正です')
    sample = {'version':1, 'id':uuid.uuid4().hex, 'square':square, 'side':side,
              'arm':'stock', 'mode':mode, 'operation':operation,
              'failure_context':dict(issue) if isinstance(issue,dict) else None,
              'board_estimate_simulation_only':dict(board_estimate),
              'physical_board_pose_verified':False, 'calibration_sha256':None,
              'leader_calibration_sha256':None, 'follower_usb_id':None, 'leader_usb_id':None,
              'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'status':'recording', 'samples':[]}
    _save(sample,directory)
    return sample


def _positions(values):
    if not isinstance(values,dict) or set(values)!=set(NAMES):
        raise ValueError('6 関節の位置を読み取れません')
    parsed = {}
    for name in NAMES:
        value = values[name]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError(f'{name} の位置が不正です')
        value=float(value)
        if not ((0 <= value <= 100) if name=='gripper' else (-360 <= value <= 360)):
            raise ValueError(f'{name} の位置が範囲外です')
        parsed[name]=value
    return parsed


def add_capture(session, capture, directory=DIRECTORY):
    phases=PLACE_PHASES if session.get('operation')=='place' else PHASES
    if session.get('status') != 'recording' or len(session.get('samples',[])) >= len(phases):
        raise ValueError('新しいマスの記録を始めてください')
    if not isinstance(capture,dict) or capture.get('calibration_verified') is not True:
        raise ValueError('Follower の較正を確認できません')
    sha = capture.get('calibration_sha256')
    if not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{64}',sha):
        raise ValueError('較正情報が不正です')
    if session.get('calibration_sha256') not in (None,sha):
        raise ValueError('較正が途中で変わりました。この記録を使わず最初からやり直してください')
    follower_usb=capture.get('follower_usb_id')
    if not isinstance(follower_usb,str) or not re.fullmatch(r'[0-9a-f]{64}',follower_usb):
        raise ValueError('Follower の USB 識別情報が不正です')
    if session.get('follower_usb_id') not in (None,follower_usb):
        raise ValueError('Follower の USB が途中で変わりました。最初からやり直してください')
    parsed = _positions(capture.get('positions'))
    leader_positions=None;leader_sha=None;leader_usb=None
    if session.get('mode')=='leader':
        if capture.get('leader_calibration_verified') is not True:
            raise ValueError('Leader の較正を確認できません')
        leader_sha=capture.get('leader_calibration_sha256')
        if not isinstance(leader_sha,str) or not re.fullmatch(r'[0-9a-f]{64}',leader_sha):
            raise ValueError('Leader の較正情報が不正です')
        if session.get('leader_calibration_sha256') not in (None,leader_sha):
            raise ValueError('Leader の較正が途中で変わりました。最初からやり直してください')
        leader_usb=capture.get('leader_usb_id')
        if not isinstance(leader_usb,str) or not re.fullmatch(r'[0-9a-f]{64}',leader_usb):
            raise ValueError('Leader の USB 識別情報が不正です')
        if session.get('leader_usb_id') not in (None,leader_usb):
            raise ValueError('Leader の USB が途中で変わりました。最初からやり直してください')
        leader_positions=_positions(capture.get('leader_positions'))
    result = dict(session)
    result['samples'] = [*session['samples'], {
        'phase':phases[len(session['samples'])][0],
        'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'positions':parsed, 'units':'degrees except gripper normalized 0-100',
        'leader_positions':leader_positions,
        'sample_span_ms':capture.get('sample_span_ms'),
        'torque_enabled':capture.get('torque_enabled'),
    }]
    result['calibration_sha256'] = sha
    result['leader_calibration_sha256'] = leader_sha
    result['follower_usb_id']=follower_usb
    result['leader_usb_id']=leader_usb
    if len(result['samples'])==len(phases):
        result['status']='recorded_unverified'
    _save(result,directory)
    return result


def public_state(session):
    if session is None:
        return {'status':'idle'}
    index=len(session['samples'])
    phases=PLACE_PHASES if session.get('operation')=='place' else PHASES
    return {'status':session['status'],'id':session['id'],'square':session['square'],
            'side':session['side'],'mode':session['mode'],'operation':session.get('operation','pick'),
            'recorded':index,'total':len(phases),
            'next':phases[index][1] if index<len(phases) else None}


def _save(session, directory):
    ident=session.get('id')
    if not isinstance(ident,str) or not re.fullmatch(r'[0-9a-f]{32}',ident):
        raise ValueError('記録 ID が不正です')
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,temp = tempfile.mkstemp(prefix='.teaching-',suffix='.tmp',dir=directory)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as fp:
            json.dump(session,fp,ensure_ascii=False,indent=2,allow_nan=False)
            fp.write('\n')
        os.replace(temp,directory/(ident+'.json'))
    finally:
        if os.path.exists(temp): os.unlink(temp)
