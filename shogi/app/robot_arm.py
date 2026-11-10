"""Replay IK waypoints on the existing SO-101 Follower bus. Dry-run unless live."""
from __future__ import annotations
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

NAMES=('shoulder_pan','shoulder_lift','elbow_flex','wrist_flex','wrist_roll','gripper')
FOLLOWER_PORT='/dev/cu.usbmodem5B7B0140931'
SCRIPTS=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101/syodo/scripts')
CALIB_PATH=Path.home()/'.cache/huggingface/lerobot/calibration/robots/so_follower/syodo_follower.json'
OFFSETS_PATH=Path(__file__).with_name('follower_offsets.json')


def resolve_port(port=FOLLOWER_PORT):
    preferred=Path(port)
    if preferred.exists(): return str(preferred)
    raise ValueError('指定された Follower の USB が見つかりません。カメラのポートを代用しません')
OPEN_Q=.032; CLOSE_Q=.065
MAX_DEG_S=20.0
OBSERVE={'phase':'observe','joints_rad':[0.,-.55,.95,.82,0.],'gripper':OPEN_Q,'duration_s':1.2}


def with_observe(waypoints):
    return list(waypoints)+[dict(OBSERVE)]


def _calib():
    if not CALIB_PATH.is_file(): raise ValueError('Follower の較正ファイルがありません')
    return json.loads(CALIB_PATH.read_text())


def load_offsets():
    if not OFFSETS_PATH.is_file(): return {n:0.0 for n in NAMES[:-1]}
    data=json.loads(OFFSETS_PATH.read_text())
    return {n:float(data.get(n,0)) for n in NAMES[:-1]}


def offsets_from_present(present, joints_rad=None):
    q=np.asarray(OBSERVE['joints_rad'] if joints_rad is None else joints_rad,float)
    if q.shape!=(5,) or not np.isfinite(q).all(): raise ValueError('関節角が不正です')
    return {n:float(np.degrees(q[i])-float(present[n])) for i,n in enumerate(NAMES[:-1])}


def save_offsets(offsets):
    OFFSETS_PATH.write_text(json.dumps({n:float(offsets[n]) for n in NAMES[:-1]},indent=2)+'\n')
    return load_offsets()


def q_to_follower(joints_rad, gripper):
    q=np.asarray(joints_rad,float)
    if q.shape!=(5,) or not np.isfinite(q).all(): raise ValueError('関節角が不正です')
    if not np.isfinite(gripper): raise ValueError('グリッパー角が不正です')
    off=load_offsets()
    deg=[float(np.degrees(q[i])-off[n]) for i,n in enumerate(NAMES[:-1])]
    span=CLOSE_Q-OPEN_Q
    g=float(np.clip((gripper-OPEN_Q)/span*80.0,0,100)) if span else 20.0
    cmd=dict(zip(NAMES,[*deg,g]))
    calib=_calib()
    for name,value in cmd.items():
        c=calib[name]
        raw=c['range_min']+value*(c['range_max']-c['range_min'])/100 if name=='gripper' else value*4095/360+(c['range_min']+c['range_max'])/2
        if not c['range_min']-0.5<=raw<=c['range_max']+0.5:
            raise ValueError(f'{name} が Follower の較正範囲外です')
    return cmd


def interpolate(a,b,steps):
    a=np.array([a[n] for n in NAMES],float); b=np.array([b[n] for n in NAMES],float)
    for i in range(1,steps+1):
        t=i/steps; mix=t*t*(3-2*t)
        yield dict(zip(NAMES,(a+(b-a)*mix).tolist()))


class Arm:
    def __init__(self, port=FOLLOWER_PORT):
        self.port=port; self.bus=None; self.live=False

    def play(self, waypoints, live=False):
        if not waypoints: raise ValueError('再生する経由点がありません')
        log=[]; prev=None
        if live: self._connect()
        try:
            if live:
                prev=self.bus.sync_read('Present_Position', list(NAMES), num_retry=2)
            for wp in waypoints:
                cmd=q_to_follower(wp['joints_rad'][:5], wp['gripper'])
                duration=max(0.2,float(wp.get('duration_s',1)))
                start=prev or cmd
                delta=max(abs(cmd[n]-start[n]) for n in NAMES if n!='gripper')
                # smoothstep peaks at 1.5 times its average angular speed.
                duration=max(duration, 1.5*delta/MAX_DEG_S)
                steps=max(2,int(math.ceil(duration*20)))
                dt=duration/steps
                for sample in interpolate(start,cmd,steps):
                    if live:
                        self.bus.sync_write('Goal_Position', sample)
                        time.sleep(dt)
                log.append({'phase':wp.get('phase'),'follower':cmd,'sent':bool(live),'duration_s':duration})
                prev=cmd
        finally:
            if live: self._disconnect()
        return {'live':bool(live),'sim_only':not live,'commands':log,'count':len(log)}

    def _connect(self):
        # A single guessed observation pose does not calibrate joint signs,
        # gripper travel, camera extrinsics or collision-free motion. Do not
        # enable torque until an independently verified live path exists.
        raise ValueError('実機動作は未検証です。関節対応・盤座標・把持と停止の実機検証が必要です')

    def snap_observe(self):
        self._connect()
        try:
            present=self.bus.sync_read('Present_Position', list(NAMES), num_retry=2)
            return save_offsets(offsets_from_present(present))
        finally:
            self._disconnect()

    def _disconnect(self):
        if self.bus is not None:
            self.bus.disconnect(); self.bus=None; self.live=False
