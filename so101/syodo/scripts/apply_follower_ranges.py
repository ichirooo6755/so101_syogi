#!/usr/bin/env python3
"""Apply a human-recorded follower range capture with backup and readback.

Use only with a supported arm, torque off, and an explicitly reviewed capture.
Changes the meaning of LeRobot joint values and invalidates old desk calibration.
"""
import json
import os
from pathlib import Path
import sys
from datetime import datetime

from follower_pad_bus import Follower

PORT = '/dev/cu.usbmodem5B7B0140931'
CAL = Path.home() / '.cache/huggingface/lerobot/calibration/robots/so_follower/syodo_follower.json'
CAPTURE = Path(__file__).resolve().parents[1] / 'data/hardware/follower-controller-range-capture-20261031.json'
CHANGED = ('shoulder_lift', 'elbow_flex', 'wrist_flex', 'gripper')


def main():
    original = CAL.read_bytes()
    old = json.loads(original)
    capture = json.loads(CAPTURE.read_text())
    new = json.loads(original)
    if capture['samples'] < 10:
        raise ValueError('記録サンプルが不足しています')
    for n in CHANGED:
        item = capture['joints'][n]
        lo, hi = int(item['min']), int(item['max'])
        if not (0 <= lo < hi <= 4095 and hi - lo >= 200 and lo <= item['last'] <= hi):
            raise ValueError(f'{n}: 記録範囲が不正です')
        new[n]['range_min'], new[n]['range_max'] = lo, hi
    f = Follower(PORT)
    modified = []
    try:
        f.connect()
        if not f.is_calibrated:
            raise ValueError('保存済み較正とモーターが一致しません')
        for n, c in f.calibration.items():
            if f._read(c.id, 40, 1) != 0:
                raise ValueError(f'{n}: トルクが OFF ではありません')
            if n in CHANGED:
                pos = f._read(c.id, 56, 2)
                if not new[n]['range_min'] <= pos <= new[n]['range_max']:
                    raise ValueError(f'{n}: 現在位置が教示範囲外です')
        backup = CAL.with_name(CAL.name + '.backup-controller-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
        with backup.open('xb') as file:
            file.write(original)
            file.flush()
            os.fsync(file.fileno())
        print('backup:', backup, flush=True)
        for n in CHANGED:
            c = f.calibration[n]
            modified.append(n)
            f._write(c.id, 55, 1, 0)
            f._write(c.id, 9, 2, new[n]['range_min'])
            f._write(c.id, 11, 2, new[n]['range_max'])
            if (f._read(c.id, 9, 2), f._read(c.id, 11, 2)) != (new[n]['range_min'], new[n]['range_max']):
                raise RuntimeError(f'{n}: 書込み後の照合に失敗しました')
            f._write(c.id, 55, 1, 1)
            print(n, new[n]['range_min'], new[n]['range_max'], 'verified', flush=True)
        temp = CAL.with_name(CAL.name + '.controller-tmp')
        with temp.open('w') as file:
            json.dump(new, file, indent=4)
            file.write('\n')
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, CAL)
        print('calibration saved; old desk and recordings require revalidation', flush=True)
    except Exception:
        for n in reversed(modified):
            try:
                c = f.calibration[n]
                f._write(c.id, 55, 1, 0)
                f._write(c.id, 9, 2, old[n]['range_min'])
                f._write(c.id, 11, 2, old[n]['range_max'])
                f._write(c.id, 55, 1, 1)
                print('restored:', n, flush=True)
            except Exception as exc:
                print('RESTORE FAILED:', n, exc, file=sys.stderr, flush=True)
        raise
    finally:
        if f.is_connected:
            f.disconnect()


if __name__ == '__main__':
    main()
