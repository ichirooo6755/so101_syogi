"""Validate and apply an explicitly reviewed follower calibration capture."""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

CAL = Path.home() / '.cache/huggingface/lerobot/calibration/robots/so_follower/syodo_follower.json'
EDITABLE = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper')
WRIST_MARKER = Path(__file__).resolve().parents[1] / 'data/hardware/follower-controller-wrist-range.json'


def wrist_range_is_taught(calibration):
    try:
        saved = json.loads(WRIST_MARKER.read_text())
        c = calibration['wrist_roll']
        return saved == {'id': c.id, 'homing_offset': c.homing_offset,
                         'range_min': c.range_min, 'range_max': c.range_max}
    except (OSError, ValueError, KeyError, AttributeError):
        return False


def remember_wrist_range():
    c = json.loads(CAL.read_text())['wrist_roll']
    value = {k: c[k] for k in ('id', 'homing_offset', 'range_min', 'range_max')}
    WRIST_MARKER.parent.mkdir(parents=True, exist_ok=True)
    temp = WRIST_MARKER.with_name(WRIST_MARKER.name + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temp, WRIST_MARKER)


def candidate_from_capture(capture, preserve_wrapped_wrist=False):
    result = {}
    retained_wrist = False
    for name in EDITABLE:
        row = capture[name]
        lo, hi, last = row['min'], row['max'], row['last']
        if not (0 <= lo <= last <= hi <= 4095):
            raise ValueError(f'{name}: 記録値が不正です')
        if name == 'wrist_roll' and row.get('wrapped'):
            if not preserve_wrapped_wrist:
                raise ValueError('ID5 の境界またぎは、この較正では保存できません')
            span = row.get('unwrapped_max', 0) - row.get('unwrapped_min', 0)
            if not 200 <= span <= 4095:
                raise ValueError('ID5 は安全な範囲をゆっくり動かしてください（1回転以内）')
            retained_wrist = True
            continue
        if hi - lo >= 200:
            result[name] = (lo, hi)
    if not result and not retained_wrist:
        raise ValueError('十分な範囲を動かした関節がありません。もう一度記録してください')
    return result


def apply_capture(bus, candidate, expected_hash, calibration_path=None):
    path = Path(calibration_path) if calibration_path is not None else CAL
    original = path.read_bytes()
    if hashlib.sha256(original).hexdigest() != expected_hash:
        raise ValueError('記録後に較正ファイルが変更されました。記録し直してください')
    old = json.loads(original)
    if not bus.is_calibrated:
        raise ValueError('モーターと較正ファイルが一致しません')
    for name, c in bus.calibration.items():
        if bus._read(c.id, 40, 1) != 0:
            raise ValueError(f'{name}: トルク OFF を確認できません')
        if name in candidate:
            pos = bus._read(c.id, 56, 2)
            lo, hi = candidate[name]
            if not lo <= pos <= hi:
                raise ValueError(f'{name}: 現在位置が記録範囲外です')
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup = path.with_name(path.name + '.backup-controller-' + stamp)
    with backup.open('xb') as fp:
        fp.write(original)
        fp.flush()
        os.fsync(fp.fileno())
    new = json.loads(original)
    modified = []
    try:
        for name, (lo, hi) in candidate.items():
            c = bus.calibration[name]
            modified.append(name)
            bus._write(c.id, 55, 1, 0)
            bus._write(c.id, 9, 2, lo)
            bus._write(c.id, 11, 2, hi)
            if (bus._read(c.id, 9, 2), bus._read(c.id, 11, 2)) != (lo, hi):
                raise RuntimeError(f'{name}: 読み戻し不一致')
            bus._write(c.id, 55, 1, 1)
            new[name]['range_min'], new[name]['range_max'] = lo, hi
        temp = path.with_name(path.name + '.tmp-' + stamp)
        with temp.open('x') as fp:
            json.dump(new, fp, indent=4)
            fp.write('\n')
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(temp, path)
    except Exception as error:
        failed = []
        for name in reversed(modified):
            try:
                c = bus.calibration[name]
                bus._write(c.id, 55, 1, 0)
                bus._write(c.id, 9, 2, old[name]['range_min'])
                bus._write(c.id, 11, 2, old[name]['range_max'])
                bus._write(c.id, 55, 1, 1)
            except Exception:
                failed.append(name)
        if failed:
            raise RuntimeError('較正失敗。復旧を確認できない関節: ' + ', '.join(failed) + '。操作しないでください') from error
        raise RuntimeError('較正失敗。変更した範囲は元に戻しました: ' + str(error)) from error
    return backup
