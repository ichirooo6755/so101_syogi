"""Bounded position-position bilateral control for two calibrated SO-101 arms.

This is position feedback, not a calibrated force sensor. Hardware validation
is required before using it near people, tools, paper, or obstacles.
"""
import math
import os
import subprocess
from pathlib import Path

from follower_pad_bus import Follower, NAMES

LEADER_PORT = '/dev/cu.usbmodem5B7B0136431'
LEADER_CAL = Path.home() / '.cache/huggingface/lerobot/calibration/teleoperators/so_leader/syodo_leader.json'
STEP = 0.7
ERROR_LIMIT = 15.0
LEADER_TORQUE_LIMIT = 200  # RAM torque limit, 0..1000; never increase an existing limit.


def assert_no_other_owner(port):
    result = subprocess.run(['lsof', '-t', port], capture_output=True, text=True, timeout=3)
    if result.returncode not in (0, 1):
        raise ValueError(f'USB ポートの使用状況を確認できません: {port}')
    owners = {int(p) for p in result.stdout.split() if p.isdigit()}
    if owners - {os.getpid()}:
        raise ValueError(f'別のプログラムが USB ポートを使用中です: {port}')


def make_limits(calibration, initial):
    limits = {}
    for n in NAMES:
        c = calibration[n]
        if c.range_min >= c.range_max:
            raise ValueError(f'{n}: 較正範囲が不正です')
        span = (c.range_max - c.range_min) * 360 / 4095 / 2
        lo, hi = (0, 100) if n == 'gripper' else (-span, span)
        if n == 'wrist_roll':
            lo, hi = max(lo, initial[n] - 15), min(hi, initial[n] + 15)
        if not math.isfinite(initial[n]) or not lo <= initial[n] <= hi:
            raise ValueError(f'{n}: 現在位置が較正範囲外です')
        limits[n] = (lo, hi)
    return limits


def calculate_goals(master, follower, offsets, master_limits, follower_limits):
    goals_m, goals_f = {}, {}
    for n in NAMES:
        m, f = float(master[n]), float(follower[n])
        if not math.isfinite(m) or not math.isfinite(f):
            raise ValueError(f'{n}: 位置値が不正です')
        if not master_limits[n][0] <= m <= master_limits[n][1] or not follower_limits[n][0] <= f <= follower_limits[n][1]:
            raise ValueError(f'{n}: 安全範囲外です')
        error = m + offsets[n] - f
        if abs(error) > ERROR_LIMIT:
            raise ValueError(f'{n}: 両腕の位置差が大きすぎます')
        m_goal = max(master_limits[n][0], min(master_limits[n][1], m - max(-STEP, min(STEP, error))))
        f_goal = max(follower_limits[n][0], min(follower_limits[n][1], f + max(-STEP, min(STEP, error))))
        goals_m[n], goals_f[n] = m_goal, f_goal
    return goals_m, goals_f


class BilateralPair:
    def __init__(self, follower_port, leader_port=LEADER_PORT):
        if os.path.realpath(follower_port) == os.path.realpath(leader_port):
            raise ValueError('Leader と Follower は別の USB ポートにしてください')
        self.follower_port, self.leader_port = follower_port, leader_port
        self.master = Follower(leader_port, calibration_path=LEADER_CAL)
        self.follower = Follower(follower_port)
        self.names = list(NAMES)
        self.armed = False
        self.limit_backup = {}

    def connect(self):
        for port in (self.leader_port, self.follower_port):
            assert_no_other_owner(port)
        try:
            for label, arm in (('Leader', self.master), ('Follower', self.follower)):
                try:
                    arm.connect()
                    if not arm.is_calibrated:
                        raise ValueError('較正情報が一致しません。接続先と較正を確認してください')
                    for n in NAMES:
                        if arm.read('Operating_Mode', n, normalize=False) != 0:
                            raise ValueError(f'{n}: 位置制御モードではありません')
                    arm.sync_read('Present_Position', self.names)
                except Exception as exc:
                    raise ValueError(f'{label}: {exc}') from exc
        except Exception:
            self.close(hold=False)
            raise

    def start(self, guard=lambda: True):
        for port in (self.leader_port, self.follower_port):
            assert_no_other_owner(port)
        m_before = self.master.sync_read('Present_Position', self.names)
        f_before = self.follower.sync_read('Present_Position', self.names)
        make_limits(self.master.calibration, m_before)
        make_limits(self.follower.calibration, f_before)
        # Cleanup must hold both if any later operation fails, including a
        # partially applied temporary torque cap.
        self.armed = True
        for n in NAMES:
            if not guard():
                raise ValueError('画面が非表示か停止されたため開始を中止しました')
            i = self.master.calibration[n].id
            previous = self.master._read(i, 48, 2)
            if not 1 <= previous <= 1000:
                raise ValueError(f'Leader {n}: トルク上限を確認できません')
            self.limit_backup.setdefault(n, previous)
            if previous > LEADER_TORQUE_LIMIT:
                self.master._write(i, 48, 2, LEADER_TORQUE_LIMIT)
        m = self.master.sync_read('Present_Position', self.names)
        f = self.follower.sync_read('Present_Position', self.names)
        if any(abs(m[n] - m_before[n]) > 2 or abs(f[n] - f_before[n]) > 2 for n in NAMES):
            raise ValueError('開始準備中に姿勢が変化しました')
        make_limits(self.master.calibration, m)
        make_limits(self.follower.calibration, f)
        for label, arm, initial in (('Leader', self.master, m), ('Follower', self.follower, f)):
            for name in NAMES:
                if not guard():
                    raise ValueError('画面が非表示か停止されたため開始を中止しました')
                now = arm.sync_read('Present_Position', [name])[name]
                if abs(now - initial[name]) > 2:
                    raise ValueError(f'{label} {name}: 開始準備中に姿勢が変化しました')
                # A motor's goal is the latest measured position, not a stored pose.
                arm.sync_write('Goal_Position', {name: now})
                arm.enable_torque([name])
        if not guard():
            raise ValueError('画面が非表示か停止されたため開始を中止しました')
        m_final = self.master.sync_read('Present_Position', self.names)
        f_final = self.follower.sync_read('Present_Position', self.names)
        if any(abs(m_final[n] - m[n]) > 2 or abs(f_final[n] - f[n]) > 2 for n in NAMES):
            raise ValueError('開始準備中に姿勢が変化しました')
        self.master_limits = make_limits(self.master.calibration, m_final)
        self.follower_limits = make_limits(self.follower.calibration, f_final)
        self.offsets = {n: f_final[n] - m_final[n] for n in NAMES}

    def step(self):
        m = self.master.sync_read('Present_Position', self.names)
        f = self.follower.sync_read('Present_Position', self.names)
        gm, gf = calculate_goals(m, f, self.offsets, self.master_limits, self.follower_limits)
        self.follower.sync_write('Goal_Position', gf)
        self.master.sync_write('Goal_Position', gm)

    def hold(self):
        errors = []
        for label, arm in (('Leader', self.master), ('Follower', self.follower)):
            if arm.is_connected:
                try:
                    pos = arm.sync_read('Present_Position', self.names)
                    arm.sync_write('Goal_Position', pos)
                except Exception as exc:
                    errors.append(f'{label}: {exc}')
        self.armed = False
        if errors:
            raise RuntimeError('停止位置を確認できません: ' + '; '.join(errors))

    def torque_off(self):
        self.armed = False
        errors = []
        for label, arm in (('Leader', self.master), ('Follower', self.follower)):
            for n in NAMES:
                try:
                    arm._write(arm.calibration[n].id, 40, 1, 0)
                except Exception as exc:
                    errors.append(f'{label} {n}: {exc}')
        # Restore only on joints whose torque OFF is verified.
        for n, value in self.limit_backup.items():
            try:
                i = self.master.calibration[n].id
                if self.master._read(i, 40, 1) == 0:
                    self.master._write(i, 48, 2, value)
            except Exception as exc:
                errors.append(f'Leader {n} 上限復元: {exc}')
        if errors:
            raise RuntimeError('トルク OFF を確認できない関節があります: ' + '; '.join(errors))

    def close(self, hold=True):
        error = None
        if hold and self.armed:
            try:
                self.hold()
            except Exception as exc:
                error = exc
        for arm in (self.master, self.follower):
            try:
                if arm.is_connected:
                    arm.disconnect(disable_torque=False)
            except Exception as exc:
                error = error or exc
        if error:
            raise error
