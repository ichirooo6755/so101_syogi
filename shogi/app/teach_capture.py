"""Read one stable six-motor snapshot. Never writes registers or moves motors."""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import subprocess
import sys
import termios
import time
from pathlib import Path
from types import SimpleNamespace

SCRIPTS = Path.home()/'Documents/ChatGPT/so101/syodo/scripts'
CALIB = Path.home()/'.cache/huggingface/lerobot/calibration/robots/so_follower/syodo_follower.json'
LEADER_CALIB = Path.home()/'.cache/huggingface/lerobot/calibration/teleoperators/so_leader/syodo_leader.json'
NAMES = ('shoulder_pan','shoulder_lift','elbow_flex','wrist_flex','wrist_roll','gripper')


def port_holders(port):
    result=subprocess.run(['/usr/sbin/lsof','-t','--',port],capture_output=True,text=True,timeout=5)
    if result.returncode not in (0,1) or result.stderr.strip():
        raise ValueError('USB の使用状況を確認できません')
    try:
        return {int(line) for line in result.stdout.splitlines() if line.strip()}
    except ValueError as exc:
        raise ValueError('USB の使用状況を確認できません') from exc


def validate_ports(ports):
    from serial.tools import list_ports
    available={p.device:p for p in list_ports.comports() if p.device.startswith('/dev/cu.')}
    if any(port not in available for port in ports):
        raise ValueError('選択したアームの USB が見つかりません。再検索してください')
    identities=[]
    for port in ports:
        p=available[port]
        identity=('serial',p.vid,p.pid,p.serial_number) if p.serial_number else ('location',p.location)
        if identity[-1] is None:
            raise ValueError('アームの USB 識別情報を確認できません')
        identities.append(identity)
    if len(set(identities))!=len(identities):
        raise ValueError('Leader と Follower に同じ USB を選べません')
    return [hashlib.sha256(json.dumps(identity).encode()).hexdigest() for identity in identities]


def read_snapshot(port, leader_port=None):
    ports=[port]+([leader_port] if leader_port else [])
    identities=validate_ports(ports)
    for p in ports:
        if port_holders(p):
            raise ValueError('アームを操作する他の画面で「切断」してから記録してください')
    if not hasattr(termios,'TIOCEXCL'):
        raise ValueError('USB を排他的に開けないため記録できません')
    files=[CALIB]+([LEADER_CALIB] if leader_port else [])
    calibration_bytes=[path.read_bytes() for path in files]
    hashes=[hashlib.sha256(blob).hexdigest() for blob in calibration_bytes]
    sys.path.insert(0,str(SCRIPTS))
    from follower_pad_bus import Follower
    readers=[]
    try:
        for index,p in enumerate(ports):
            reader=Follower(p);readers.append(reader)
            if index:
                calibration=json.loads(calibration_bytes[index])
                if set(calibration)!=set(NAMES): raise ValueError('Leader の較正ファイルが不正です')
                reader.calibration={n:SimpleNamespace(**calibration[n]) for n in NAMES}
                if any(reader.calibration[n].id!=i for i,n in enumerate(NAMES,1)):
                    raise ValueError('Leader のモーター ID が不正です')
            if any(getattr(reader.calibration[n],'drive_mode',0)!=0 for n in NAMES):
                raise ValueError('反転設定されたモーターの読み取り方式は未対応です')
            reader.connect()
            fcntl.ioctl(reader.port.ser.fileno(),termios.TIOCEXCL)
            if port_holders(p)-{os.getpid()}:
                raise ValueError('アームの USB を他のアプリが使用しています')
            if not reader.is_calibrated:
                raise ValueError(('Follower' if index==0 else 'Leader')+' の較正とモーターが一致しません')
            for name in NAMES:
                if reader.read('Operating_Mode',name,normalize=False)!=0:
                    raise ValueError(f'{name} が位置制御モードではありません')
        torque={name:bool(readers[0]._read(readers[0].calibration[name].id,40,1)) for name in NAMES}
        readings=[[] for _ in readers]
        started=time.monotonic()
        for _ in range(3):
            for index,reader in enumerate(readers):
                readings[index].append(reader.sync_read('Present_Position',NAMES,num_retry=2))
            time.sleep(.1)
        span_ms=round((time.monotonic()-started)*1000)
        all_positions=[]
        for group in readings:
            positions={}
            for name in NAMES:
                values=[float(reading[name]) for reading in group]
                if not all(math.isfinite(value) for value in values):
                    raise ValueError(f'{name} の読み取り値が不正です')
                if max(values)-min(values) > (2.0 if name=='gripper' else 1.0):
                    raise ValueError('アームが動いています。静止させてから記録してください')
                positions[name]=sum(values)/len(values)
            all_positions.append(positions)
        if [hashlib.sha256(path.read_bytes()).hexdigest() for path in files]!=hashes:
            raise ValueError('較正が読み取り中に変更されました')
        result={'positions':all_positions[0],'calibration_sha256':hashes[0],'calibration_verified':True,
                'follower_usb_id':identities[0], 'torque_enabled':torque,'sample_span_ms':span_ms}
        if leader_port:
            result.update(leader_positions=all_positions[1],leader_calibration_sha256=hashes[1],
                          leader_calibration_verified=True,leader_usb_id=identities[1])
        return result
    finally:
        for reader in reversed(readers):
            if reader.is_connected:
                reader.disconnect()


def main():
    try:
        if len(sys.argv) not in (2,3): raise ValueError('アームの USB を指定してください')
        print(json.dumps(read_snapshot(sys.argv[1],sys.argv[2] if len(sys.argv)==3 else None),
                         ensure_ascii=False,allow_nan=False))
    except Exception as exc:
        print(json.dumps({'error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
