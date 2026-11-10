#!/usr/bin/env python3
"""Local, dead-man controlled SO-101 follower console."""
import json
import hashlib
import math
import os
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Verified against the connected follower's six saved calibration records.
PORT = '/dev/cu.usbmodem5B7B0140931'
JOINTS = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper')
LABELS = {'shoulder_pan': '肩の回転', 'shoulder_lift': '肩の上下', 'elbow_flex': 'ひじ',
          'wrist_flex': '手首の曲げ', 'wrist_roll': '手首の回転', 'gripper': 'グリッパー'}
TOKEN = secrets.token_urlsafe(32)
PAGE = Path(__file__).with_name('follower_pad') / 'index.html'
TIMEOUT = 0.30
PREFERENCES = Path.home() / '.cache/huggingface/lerobot/follower_pad_preferences.json'

def load_preferences():
    try:
        data = json.loads(PREFERENCES.read_text())
        speed, mirror = float(data['speed']), data['mirror']
        if not math.isfinite(speed) or not 5 <= speed <= 30 or type(mirror) is not bool:
            raise ValueError('invalid preferences')
        return {'speed': speed, 'mirror': mirror}
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return {'speed': 20, 'mirror': False}

def save_preferences(prefs):
    PREFERENCES.parent.mkdir(parents=True, exist_ok=True)
    tmp = PREFERENCES.with_suffix('.tmp')
    tmp.write_text(json.dumps(prefs))
    tmp.replace(PREFERENCES)


def check_motor_status(port, allow_gripper_overload=False):
    """Read Feetech status packets before loading LeRobot or enabling torque."""
    import serial
    with serial.Serial(port, 1_000_000, timeout=0.3) as device:
        overloaded = set()
        for motor_id in range(1, 7):
            body = [motor_id, 4, 2, 62, 1]
            device.reset_input_buffer()
            device.write(bytes([255, 255, *body, (~sum(body)) & 255]))
            packet = device.read(7)
            if (len(packet) != 7 or packet[:4] != bytes([255, 255, motor_id, 3])
                    or sum(packet[2:]) & 255 != 255):
                raise ValueError(f'モーター ID{motor_id} の応答を確認できません')
            error = packet[4]
            if error == 32 and motor_id == 6 and allow_gripper_overload:
                overloaded.add(motor_id)
                continue
            if error:
                from follower_motor_errors import describe_status
                detail = describe_status(error)
                raise ValueError(f'モーター ID{motor_id}: {detail}（status=0x{error:02x}、測定 {packet[5] / 10:.1f} V）。負荷・配線・電源を確認してください')
        return overloaded


def next_goals(present, inputs, limits, dt, previous=None, speed=20):
    """Integrate slowly, limiting accumulated lag behind the measured position."""
    previous = previous or present
    result = {}
    for name, value in zip(JOINTS, inputs):
        if name not in present:
            continue
        value = float(value)
        if not math.isfinite(value) or abs(value) > 1:
            raise ValueError('不正な入力')
        if abs(value) < 0.18:
            continue
        lo, hi = limits[name]
        now = float(present[name])
        if not math.isfinite(now) or not lo <= now <= hi:
            raise ValueError(f'{name} が安全範囲外です')
        joint_speed = speed if name != 'gripper' else speed * 0.8
        target = float(previous.get(name, now)) + value * joint_speed * min(max(dt, 0), 0.05)
        target = max(now - 5, min(now + 5, target))
        result[name] = max(lo, min(hi, target))
    return result


def record_position(row, value, allow_full_turn=False):
    """Track one-turn Leader ID5 crossings without treating them as broken data."""
    previous = row['last']
    delta = value - previous
    if abs(delta) > 2048:
        boundary_crossing = ((previous >= 3840 and value <= 255) or
                             (previous <= 255 and value >= 3840))
        if not allow_full_turn or not boundary_crossing:
            raise ValueError('位置が不連続です。記録を中止しました')
        delta += -4096 if delta > 0 else 4096
        row['wrapped'] = True
    if allow_full_turn:
        unwrapped = row.get('unwrapped', previous) + delta
        row['unwrapped'] = unwrapped
        row['unwrapped_min'] = min(row.get('unwrapped_min', previous), unwrapped)
        row['unwrapped_max'] = max(row.get('unwrapped_max', previous), unwrapped)
        if row['unwrapped_max'] - row['unwrapped_min'] > 4095:
            raise ValueError('ID5 の記録が1回転を超えました。記録を中止しました')
    row['min'] = min(row['min'], value)
    row['max'] = max(row['max'], value)
    row['last'] = value


def saved_calibration_ranges(target):
    if target == 'Leader':
        from follower_bilateral import LEADER_CAL
        path = LEADER_CAL
    else:
        from follower_calibration import CAL
        path = CAL
    try:
        data = json.loads(path.read_text())
        result = {}
        for name in JOINTS:
            lo, hi = data[name]['range_min'], data[name]['range_max']
            if type(lo) is not int or type(hi) is not int or not 0 <= lo < hi <= 4095:
                return None
            result[name] = {'min': lo, 'max': hi}
        return result
    except (OSError, ValueError, KeyError, TypeError):
        return None


class Controller:
    def __init__(self):
        self.lock = threading.Lock()
        self.command = None
        self.input = None
        self.neutral = False
        self.last = 0.0
        self.preferences = load_preferences()
        self.speed = self.preferences['speed']
        self.state = '未接続'
        self.armed = False
        self.ui_last = time.monotonic()
        self.calibration_state = 'idle'
        self.calibration_ranges = {}
        self.calibration_samples = 0
        self.calibration_hash = ''
        self.wrist_taught = False
        self.mode = 'controller'
        self.calibration_target = 'Follower'
        self.calibration_connected = False
        self.worker = threading.Thread(target=self.run, daemon=True)
        self.worker.start()

    def post(self, body):
        kind = body.get('kind')
        with self.lock:
            if kind in ('connect', 'arm', 'bilateral_connect', 'bilateral_start', 'leader_cal_connect', 'stop', 'disconnect', 'torque_off', 'cal_start', 'cal_finish', 'cal_apply', 'cal_cancel'):
                if self.command is not None:
                    raise ValueError('処理中です')
                self.command = kind
                if kind in ('stop', 'disconnect', 'torque_off', 'cal_start', 'cal_cancel', 'bilateral_connect', 'leader_cal_connect'):
                    self.input = None
                    self.armed = False
            elif kind == 'preferences':
                speed, mirror = float(body.get('speed')), body.get('mirror')
                if not math.isfinite(speed) or not 5 <= speed <= 30 or type(mirror) is not bool:
                    raise ValueError('設定値が不正です')
                if self.armed and mirror != self.preferences['mirror']:
                    raise ValueError('反転モードは停止してから変更してください')
                prefs = {'speed': speed, 'mirror': mirror}
                save_preferences(prefs)
                self.preferences = prefs
            elif kind == 'input':
                values = body.get('axes')
                if not isinstance(values, list) or len(values) != 6:
                    raise ValueError('入力形式エラー')
                values = [float(x) for x in values]
                if any(not math.isfinite(x) or abs(x) > 1 for x in values):
                    raise ValueError('入力範囲エラー')
                speed = float(body.get('speed', 20))
                if not math.isfinite(speed) or not 5 <= speed <= 30:
                    raise ValueError('速度の範囲エラー')
                self.speed = speed
                self.input = values
                self.neutral = all(abs(x) < 0.18 for x in values) and body.get('neutral_extra', True) is True
                self.last = time.monotonic()
            else:
                raise ValueError('不明な操作')

    def run(self):
        leader = None
        leader_cal = None
        pair = None
        limits = {}
        active = []
        blocked = []
        gripper_overloaded = False
        holding = False
        targets = {}
        last_cycle = time.monotonic()
        while True:
            try:
                with self.lock:
                    cmd, self.command = self.command, None
                    inputs, stamp, armed, speed = self.input, self.last, self.armed, self.speed
                if cmd == 'connect' and pair is not None:
                    self.state = '先に両腕をトルク OFF にしてから切断してください'
                elif cmd == 'connect' and leader_cal is not None:
                    self.state = '先に Leader の較正を終了して切断してください'
                elif cmd == 'connect' and leader is None:
                    self.mode = 'controller'
                    self.calibration_target = 'Follower'
                    self.state = '接続確認中…'
                    gripper_overloaded = 6 in (check_motor_status(PORT, allow_gripper_overload=True) or set())
                    from follower_pad_bus import Follower
                    leader = Follower(PORT)
                    if not leader.calibration or any(n not in leader.calibration for n in JOINTS):
                        raise ValueError('Follower の較正ファイルがありません')
                    leader.bus.connect()
                    if not (leader.calibration_matches(allow_gripper_overload=True) if gripper_overloaded else leader.is_calibrated):
                        raise ValueError('Follower の較正がモーターと一致しません')
                    for n in JOINTS:
                        if (leader.bus._read(6, 33, 1, allow_gripper_overload=True) if n == 'gripper' and gripper_overloaded else leader.bus.read('Operating_Mode', n, normalize=False)) != 0:
                            raise ValueError(f'{n} が位置制御モードではありません')
                        c = leader.calibration[n]
                        span = (c.range_max - c.range_min) * 360 / 4095 / 2
                        limits[n] = (0, 100) if n == 'gripper' else (-span, span)
                        if limits[n][0] >= limits[n][1]:
                            raise ValueError(f'{n} の較正範囲が狭すぎます')
                    # Identify joints safely within their calibrated travel, without
                    # commanding the joints that are already beyond its bounds.
                    active, blocked = [], []
                    for n in JOINTS:
                        if n == 'gripper' and gripper_overloaded:
                            blocked.append(n)
                            continue
                        c = leader.calibration[n]
                        raw = leader.bus._read(c.id, 56, 2)
                        position = ((raw - c.range_min) * 100 / (c.range_max - c.range_min)
                                    if n == 'gripper' else
                                    (raw - (c.range_min + c.range_max) / 2) * 360 / 4095)
                        if limits[n][0] <= position <= limits[n][1]:
                            active.append(n)
                        else:
                            blocked.append(n)
                    if not active:
                        raise ValueError('操作できる較正範囲内の関節がありません')
                    pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                    # A generic full-turn calibration is not a taught physical travel range.
                    from follower_calibration import wrist_range_is_taught
                    self.wrist_taught = wrist_range_is_taught(leader.calibration)
                    lo, hi = limits['wrist_roll']
                    if 'wrist_roll' in pos and not self.wrist_taught:
                        limits['wrist_roll'] = (max(lo, pos['wrist_roll'] - 15), min(hi, pos['wrist_roll'] + 15))
                    self.state = '接続済み・操作待ち' + (' / 範囲の端または外のため停止: ' + '、'.join(LABELS[n] for n in blocked) if blocked else '')
                    if gripper_overloaded:
                        self.state += ' / ID6 過負荷のため操作対象から除外。把持物が落ちる場合があります'
                    self.calibration_connected = True
                elif cmd == 'leader_cal_connect':
                    if pair is not None:
                        self.state = '両腕を停止して切断してから Leader の較正を選んでください'
                    elif self.calibration_state != 'idle':
                        self.state = '現在の較正を終了または中止してください'
                    elif leader_cal is not None:
                        self.state = 'Leader は較正用に接続済みです'
                    else:
                        if leader is not None:
                            if holding:
                                pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                                leader.bus.sync_write('Goal_Position', pos)
                            leader.bus.disconnect(disable_torque=False)
                            leader = None
                            holding = False
                            self.calibration_connected = False
                        self.state = 'Leader の通信・較正を確認中…'
                        from follower_bilateral import LEADER_PORT, LEADER_CAL, assert_no_other_owner
                        from follower_pad_bus import Follower
                        assert_no_other_owner(LEADER_PORT)
                        check_motor_status(LEADER_PORT)
                        leader_cal = Follower(LEADER_PORT, calibration_path=LEADER_CAL)
                        leader_cal.bus.connect()
                        if not leader_cal.is_calibrated:
                            raise ValueError('Leader のモーターと保存済み較正が一致しません。接続先と較正を確認してください')
                        for n in JOINTS:
                            if leader_cal.bus.read('Operating_Mode', n, normalize=False) != 0:
                                raise ValueError(f'Leader {n}: 位置制御モードではありません')
                        self.mode = 'leader_calibration'
                        self.calibration_target = 'Leader'
                        self.calibration_connected = True
                        self.state = 'Leader の較正用に接続済み・記録待ち'
                elif cmd == 'bilateral_connect' and leader_cal is not None:
                    self.state = 'Leader の較正を終了して切断してください'
                elif cmd == 'bilateral_connect':
                    if pair is not None:
                        self.state = '両腕は接続済みです'
                    else:
                        if self.calibration_state != 'idle':
                            raise ValueError('較正を終了または中止してください')
                        if leader is not None:
                            if holding:
                                pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                                leader.bus.sync_write('Goal_Position', pos)
                            leader.bus.disconnect(disable_torque=False)
                            leader = None
                            holding = False
                            self.calibration_connected = False
                        self.state = '両腕の接続と較正を確認中…'
                        from follower_bilateral import BilateralPair
                        pair = BilateralPair(PORT)
                        pair.connect()
                        self.mode = 'bilateral'
                        self.state = '両腕接続済み・開始待ち。開始位置の差を維持します'
                elif cmd == 'bilateral_start':
                    if pair is None or self.mode != 'bilateral':
                        raise ValueError('先に両腕を接続してください')
                    if time.monotonic() - self.ui_last > 0.5:
                        raise ValueError('操作画面を前面にしてください')
                    self.state = '開始準備中・両腕を支えてください'
                    def start_allowed():
                        with self.lock:
                            return self.command is None and time.monotonic() - self.ui_last <= 0.5
                    pair.start(start_allowed)
                    with self.lock:
                        self.armed = True
                    self.state = 'バイラテラル動作中・ID5 は開始位置から ±15°'
                elif cmd == 'arm' and pair is not None:
                    self.state = 'バイラテラルは専用の開始ボタンを使用してください'
                elif cmd == 'arm' and leader is not None:
                    if self.calibration_state != 'idle':
                        raise ValueError('較正を終了または中止してください')
                    if not self.neutral or time.monotonic() - stamp > TIMEOUT:
                        raise ValueError('スティック、LT・RT、A・B ボタンを離してから操作開始してください')
                    pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                    for n in active:
                        if not math.isfinite(float(pos[n])) or not limits[n][0] <= pos[n] <= limits[n][1]:
                            raise ValueError(f'{n} が較正範囲の端にあります。安全な範囲に置いてください')
                    leader.bus.sync_write('Goal_Position', pos)
                    leader.bus.enable_torque(active)
                    targets = dict(pos)
                    holding = True
                    with self.lock:
                        self.armed = True
                    self.state = '操作可能・スティックで動かす' + (' / 操作対象外: ' + '、'.join(LABELS[n] for n in blocked) if blocked else '') + (' / ID6 過負荷・把持物に注意' if gripper_overloaded else '')
                elif cmd == 'torque_off':
                    if pair is not None:
                        self.state = '両腕のトルクを OFF にしています・腕を支えてください'
                        pair.torque_off()
                        self.state = '両腕の全関節のトルク OFF を確認しました'
                        continue
                    target = leader_cal if leader_cal is not None else leader
                    if target is None:
                        raise ValueError('トルク OFF の前に Follower に接続してください')
                    self.calibration_state = 'idle'
                    self.calibration_ranges = {}
                    holding = False
                    self.state = 'トルクを OFF にしています・腕を支えてください'
                    for n in JOINTS:
                        c = target.calibration[n]
                        allow = leader_cal is None and gripper_overloaded and n == 'gripper'
                        if allow:
                            if target.bus._read(c.id, 40, 1, allow_gripper_overload=True) != 0:
                                target.bus._write(c.id, 40, 1, 0, allow_gripper_overload=True)
                        elif target.bus._read(c.id, 40, 1) != 0:
                            target.bus._write(c.id, 40, 1, 0)
                    self.state = f'{self.calibration_target} の全関節のトルク OFF を確認しました'
                elif cmd == 'cal_start':
                    if gripper_overloaded and leader_cal is None:
                        self.state = 'ID6 の過負荷を解消して再接続してから較正してください'
                        continue
                    if pair is not None:
                        self.state = '較正前に両腕をトルク OFF にして切断してください'
                        continue
                    target = leader_cal if leader_cal is not None else leader
                    if target is None:
                        raise ValueError('先に較正する腕に接続してください')
                    from follower_calibration import CAL, EDITABLE
                    from follower_bilateral import LEADER_CAL
                    calibration_path = LEADER_CAL if leader_cal is not None else CAL
                    self.calibration_state = 'starting'
                    self.state = '較正の準備中・腕を支えてください'
                    holding = False
                    for n in JOINTS:
                        c = target.calibration[n]
                        if target.bus._read(c.id, 40, 1) != 0:
                            target.bus._write(c.id, 40, 1, 0)
                    self.calibration_hash = hashlib.sha256(calibration_path.read_bytes()).hexdigest()
                    self.calibration_ranges = {}
                    for n in EDITABLE:
                        value = target.bus._read(target.calibration[n].id, 56, 2)
                        self.calibration_ranges[n] = {'min': value, 'max': value, 'last': value}
                    self.calibration_samples = 0
                    self.calibration_state = 'recording'
                    self.state = f'{self.calibration_target} の較正記録中・腕を支えて安全な範囲を教示してください'
                elif cmd == 'cal_finish' and (leader is not None or leader_cal is not None) and self.calibration_state == 'recording':
                    from follower_calibration import candidate_from_capture
                    if self.calibration_samples < 10:
                        raise ValueError('記録時間が短すぎます')
                    full_turn = (leader_cal is not None and
                                 leader_cal.calibration['wrist_roll'].range_min == 0 and
                                 leader_cal.calibration['wrist_roll'].range_max == 4095)
                    candidate_from_capture(self.calibration_ranges, preserve_wrapped_wrist=full_turn)
                    self.calibration_state = 'review'
                    self.state = '記録終了・範囲を確認し「較正を保存」を押してください'
                elif cmd == 'cal_apply' and (leader is not None or leader_cal is not None) and self.calibration_state == 'review':
                    from follower_calibration import apply_capture, candidate_from_capture, remember_wrist_range
                    from follower_bilateral import LEADER_CAL
                    target = leader_cal if leader_cal is not None else leader
                    self.calibration_state = 'applying'
                    self.state = '較正を書込み・読み戻し中…'
                    full_turn = (leader_cal is not None and
                                 leader_cal.calibration['wrist_roll'].range_min == 0 and
                                 leader_cal.calibration['wrist_roll'].range_max == 4095)
                    candidate = candidate_from_capture(self.calibration_ranges, preserve_wrapped_wrist=full_turn)
                    retained_wrist = bool(full_turn and self.calibration_ranges['wrist_roll'].get('wrapped'))
                    if candidate:
                        backup = apply_capture(target.bus, candidate, self.calibration_hash,
                                               calibration_path=LEADER_CAL if leader_cal is not None else None)
                    else:
                        if hashlib.sha256(LEADER_CAL.read_bytes()).hexdigest() != self.calibration_hash or not target.is_calibrated:
                            raise ValueError('Leader の較正が記録後に変わりました。記録し直してください')
                        for n in JOINTS:
                            if target.bus._read(target.calibration[n].id, 40, 1) != 0:
                                raise ValueError(f'{LABELS[n]}: トルク OFF を確認できません')
                    wrist_warning = ''
                    if 'wrist_roll' in candidate and leader_cal is None:
                        try:
                            remember_wrist_range()
                        except (OSError, ValueError, KeyError) as exc:
                            wrist_warning = ' ID5 の範囲認識に失敗したため、次回も ±15° 制限です: ' + str(exc)
                    target.bus.disconnect(disable_torque=False)
                    leader = None
                    leader_cal = None
                    holding = False
                    self.wrist_taught = False
                    self.calibration_state = 'idle'
                    self.mode = 'controller'
                    self.calibration_connected = False
                    target_label = self.calibration_target
                    self.calibration_target = 'Follower'
                    if retained_wrist and not candidate:
                        self.state = 'Leader ID5 は既存の全回転較正を維持しました（較正値の変更なし）。再接続してください'
                    else:
                        self.state = f'{target_label} の較正を保存しました。再接続してください。教示済みデータは再確認が必要です' + wrist_warning
                        if retained_wrist:
                            self.state += ' / ID5 は既存の全回転較正を維持しました'
                elif cmd == 'cal_cancel':
                    self.calibration_state = 'idle'
                    self.calibration_ranges = {}
                    self.state = '較正を中止しました・トルクは OFF のままです'
                elif cmd in ('stop', 'disconnect') and leader_cal is not None:
                    if self.calibration_state in ('starting', 'recording', 'review'):
                        self.calibration_state = 'idle'
                        self.calibration_ranges = {}
                    self.state = 'Leader 較正を停止しました。トルク状態を確認してください'
                    if cmd == 'disconnect':
                        leader_cal.bus.disconnect(disable_torque=False)
                        leader_cal = None
                        self.mode = 'controller'
                        self.calibration_target = 'Follower'
                        self.calibration_connected = False
                        self.state = 'Leader を切断しました。トルク設定は維持されます'
                elif cmd in ('stop', 'disconnect') and pair is not None:
                    if pair.armed:
                        pair.hold()
                        self.state = '両腕を停止・現在位置を保持中'
                    else:
                        self.state = '両腕を停止中'
                    if cmd == 'disconnect':
                        pair.close(hold=False)
                        pair = None
                        self.mode = 'controller'
                        self.state = '両腕を切断しました。トルク設定は維持されます'
                elif cmd in ('stop', 'disconnect') and leader is not None:
                    if self.calibration_state in ('starting', 'recording', 'review'):
                        self.calibration_state = 'idle'
                        self.calibration_ranges = {}
                    if holding:
                        pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                        leader.bus.sync_write('Goal_Position', pos)
                    self.state = '停止・現在位置を保持中' if holding else '停止'
                    if cmd == 'disconnect':
                        leader.bus.disconnect(disable_torque=False)
                        leader = None
                        holding = False
                        self.wrist_taught = False
                        self.calibration_connected = False
                        self.state = '切断・トルクは保持設定のまま'
                now = time.monotonic()
                if pair is not None and pair.armed and armed and cmd is None:
                    if now - self.ui_last > 0.5:
                        with self.lock:
                            self.armed = False
                        pair.hold()
                        self.state = '画面との通信が途絶・両腕を停止し現在位置を保持中'
                    else:
                        pair.step()
                if (leader is not None or leader_cal is not None) and self.calibration_state == 'recording' and cmd is None:
                    if now - self.ui_last > 2:
                        self.calibration_state = 'idle'
                        self.state = '画面との通信が途切れ、較正記録を中止しました・トルク OFF'
                    else:
                        target = leader_cal if leader_cal is not None else leader
                        for n, row in self.calibration_ranges.items():
                            value = target.bus._read(target.calibration[n].id, 56, 2)
                            c = target.calibration[n]
                            allow_wrap = (leader_cal is not None and n == 'wrist_roll' and
                                          c.range_min == 0 and c.range_max == 4095)
                            try:
                                record_position(row, value, allow_full_turn=allow_wrap)
                            except ValueError as exc:
                                raise ValueError(f'{LABELS[n]}: {exc}') from exc
                        self.calibration_samples += 1
                if leader is not None and armed and cmd is None:
                    if now - stamp > TIMEOUT:
                        with self.lock:
                            self.armed = False
                            self.input = None
                        if holding:
                            pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                            leader.bus.sync_write('Goal_Position', pos)
                        self.state = '通信停止・現在位置を保持中。再度操作開始してください'
                    elif inputs is not None:
                        pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                        goals = next_goals(pos, inputs, limits, now - last_cycle, targets, speed)
                        if holding:
                            targets = {**pos, **goals}
                            leader.bus.sync_write('Goal_Position', targets)
                    elif holding:
                        # Releasing RB cancels the last small in-flight command.
                        pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                        leader.bus.sync_write('Goal_Position', pos)
                last_cycle = now
            except Exception as exc:
                from follower_motor_errors import MotorReadError, MotorRangeError
                if (isinstance(exc, MotorRangeError) and leader is not None and
                        leader_cal is None and pair is None and exc.name in active and
                        self.calibration_state == 'idle'):
                    active.remove(exc.name)
                    if exc.name not in blocked:
                        blocked.append(exc.name)
                    with self.lock:
                        self.armed = False
                        self.input = None
                    try:
                        if holding:
                            safe_pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                            leader.bus.sync_write('Goal_Position', safe_pos)
                        self.state = (f'{LABELS[exc.name]}が較正範囲外（現在 {exc.raw}、範囲 '
                                      f'{exc.minimum}〜{exc.maximum}）。当該関節を除外して停止。'
                                      + ('他の関節は保持中。' if holding else '')
                                      + '腕を支えて原因を確認してください')
                        time.sleep(0.05)
                        continue
                    except Exception as hold_exc:
                        exc = ValueError(f'{exc} / 他の関節の保持を確認できません: {hold_exc}')
                if (isinstance(exc, MotorReadError) and exc.gripper_overload and
                        leader is not None and leader_cal is None and pair is None and
                        'gripper' in active and self.calibration_state == 'idle'):
                    active.remove('gripper')
                    blocked.append('gripper')
                    gripper_overloaded = True
                    with self.lock:
                        self.armed = False
                        self.input = None
                    try:
                        if holding:
                            safe_pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                            leader.bus.sync_write('Goal_Position', safe_pos)
                        self.state = 'ID6 過負荷・グリッパーを除外して停止。把持物に注意し、操作開始で他の関節を再開できます'
                        time.sleep(0.05)
                        continue
                    except Exception as hold_exc:
                        exc = ValueError(f'ID6 過負荷後、他の関節を保持できません: {hold_exc}')
                with self.lock:
                    self.armed = False
                    self.input = None
                self.state = 'エラー・操作停止: ' + str(exc)
                if self.calibration_state in ('starting', 'recording', 'review'):
                    self.calibration_ranges = {}
                    self.state += ' / 記録は保存されていません'
                self.calibration_state = 'idle'
                self.calibration_connected = False
                self.wrist_taught = False
                if leader_cal is not None:
                    try:
                        if leader_cal.bus.is_connected:
                            leader_cal.bus.disconnect(disable_torque=False)
                    except Exception as cleanup:
                        self.state += ' / Leader の切断を確認できません: ' + str(cleanup)
                    leader_cal = None
                    self.mode = 'controller'
                    self.calibration_target = 'Follower'
                if pair is not None:
                    temporary_limit = bool(pair.limit_backup)
                    try:
                        pair.close(hold=True)
                    except Exception as cleanup:
                        self.state += ' / 保持を確認できません: ' + str(cleanup)
                    if temporary_limit:
                        self.state += ' / Leader のトルク上限は低い設定のままの場合があります'
                    pair = None
                    self.mode = 'controller'
                if leader is not None:
                    try:
                        if holding:
                            pos = leader.bus.sync_read('Present_Position', active, num_retry=2)
                            leader.bus.sync_write('Goal_Position', pos)
                    except Exception as cleanup:
                        self.state += ' / 保持を確認できません: ' + str(cleanup)
                    try:
                        if leader.bus.is_connected:
                            leader.bus.disconnect(disable_torque=False)
                    except Exception as cleanup:
                        self.state += ' / 切断を確認できません: ' + str(cleanup)
                    leader = None
                    holding = False
            time.sleep(0.05)


control = Controller()


class Handler(BaseHTTPRequestHandler):
    def valid(self):
        return (self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}' and
                self.headers.get('Origin') == f'http://127.0.0.1:{self.server.server_port}' and
                secrets.compare_digest(self.headers.get('X-Token', ''), TOKEN))

    def do_GET(self):
        if self.path != '/' + TOKEN or self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
            self.send_error(404); return
        data = PAGE.read_bytes().replace(b'__TOKEN__', TOKEN.encode())
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != '/api' or not self.valid():
            self.send_error(403); return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 2048:
                raise ValueError('サイズエラー')
            body = json.loads(self.rfile.read(size))
            if body.get('visible') is True:
                control.ui_last = time.monotonic()
            if body.get('kind') != 'status':
                control.post(body)
            data = json.dumps({'state': control.state, 'armed': control.armed, 'preferences': control.preferences,
                               'calibration_state': control.calibration_state,
                               'calibration_ranges': control.calibration_ranges,
                               'saved_ranges': saved_calibration_ranges(control.calibration_target),
                               'calibration_samples': control.calibration_samples,
                               'calibration_target': control.calibration_target,
                               'calibration_connected': control.calibration_connected,
                               'wrist_taught': control.wrist_taught,
                               'mode': control.mode,
                               'usb': os.path.exists(PORT)}, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            self.send_error(400)

    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    url = f'http://127.0.0.1:{server.server_port}/{TOKEN}'
    print('Follower 操作画面:', url, flush=True)
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        with control.lock:
            control.armed = False
            control.input = None
            control.command = 'disconnect'
        time.sleep(0.5)
        server.server_close()


if __name__ == '__main__':
    main()
