import importlib.util
import json
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import follower_calibration as cal
import follower_bilateral as bilateral

spec = importlib.util.spec_from_file_location('follower_pad_test', SCRIPTS / 'follower_pad.py')
pad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pad)


class FakeBus:
    is_calibrated = True

    def __init__(self):
        self.calibration = {n: types.SimpleNamespace(id=i + 1) for i, n in enumerate(pad.JOINTS)}
        self.registers = {(i, a): value for i in range(1, 7)
                          for a, value in ((9, 100), (11, 3000), (40, 0), (55, 1), (56, 500))}
        self.fail_once = None

    def _read(self, i, a, length):
        return self.registers[i, a]

    def _write(self, i, a, length, value):
        if self.fail_once == (i, a):
            self.fail_once = None
            raise OSError('injected write failure')
        self.registers[i, a] = value


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_path = cal.CAL
        self.original_marker = cal.WRIST_MARKER
        cal.CAL = Path(self.tmp.name) / 'follower.json'
        cal.WRIST_MARKER = Path(self.tmp.name) / 'wrist.json'
        self.old = {n: {'id': i + 1, 'range_min': 100, 'range_max': 3000}
                    for i, n in enumerate(pad.JOINTS)}
        cal.CAL.write_text(json.dumps(self.old))
        import hashlib
        self.digest = hashlib.sha256(cal.CAL.read_bytes()).hexdigest()
        self.bus = FakeBus()

    def tearDown(self):
        cal.CAL = self.original_path
        cal.WRIST_MARKER = self.original_marker
        self.tmp.cleanup()

    def test_capture_selects_only_moved_joints(self):
        rows = {n: {'min': 400, 'max': 410, 'last': 405} for n in cal.EDITABLE}
        rows['shoulder_lift'] = {'min': 250, 'max': 1800, 'last': 500}
        self.assertEqual(cal.candidate_from_capture(rows), {'shoulder_lift': (250, 1800)})

    def test_id5_must_be_explicitly_taught_and_match_current_calibration(self):
        data = json.loads(cal.CAL.read_text())
        data['wrist_roll'].update(homing_offset=17, range_min=500, range_max=2000)
        cal.CAL.write_text(json.dumps(data))
        wrist = types.SimpleNamespace(**data['wrist_roll'])
        self.assertFalse(cal.wrist_range_is_taught({'wrist_roll': wrist}))
        cal.remember_wrist_range()
        self.assertTrue(cal.wrist_range_is_taught({'wrist_roll': wrist}))
        wrist.range_max += 1
        self.assertFalse(cal.wrist_range_is_taught({'wrist_roll': wrist}))
        rows = {n: {'min': 400, 'max': 410, 'last': 405} for n in cal.EDITABLE}
        rows['wrist_roll'] = {'min': 500, 'max': 2000, 'last': 1000}
        self.assertEqual(cal.candidate_from_capture(rows), {'wrist_roll': (500, 2000)})

    def test_leader_id5_wrap_preserves_existing_full_turn(self):
        rows = {n: {'min': 1000, 'max': 1000, 'last': 1000} for n in cal.EDITABLE}
        row = rows['wrist_roll'] = {'min': 3200, 'max': 3200, 'last': 3200}
        for value in (3900, 4090, 5, 200, 5, 4090, 3200):
            pad.record_position(row, value, allow_full_turn=True)
        self.assertTrue(row['wrapped'])
        self.assertGreaterEqual(row['unwrapped_max'] - row['unwrapped_min'], 200)
        self.assertEqual(cal.candidate_from_capture(rows, preserve_wrapped_wrist=True), {})
        with self.assertRaisesRegex(ValueError, '境界またぎ'):
            cal.candidate_from_capture(rows)

    def test_full_turn_rejects_unexplained_jump_or_over_rotation(self):
        row = {'min': 1000, 'max': 1000, 'last': 1000}
        with self.assertRaisesRegex(ValueError, '不連続'):
            pad.record_position(row, 3500, allow_full_turn=True)
        row = {'min': 4090, 'max': 4090, 'last': 4090}
        with self.assertRaisesRegex(ValueError, '不連続'):
            pad.record_position(row, 5, allow_full_turn=False)
        row = {'min': 100, 'max': 4090, 'last': 4090,
               'unwrapped': 8190, 'unwrapped_min': 4000, 'unwrapped_max': 8190}
        with self.assertRaisesRegex(ValueError, '1回転'):
            pad.record_position(row, 5, allow_full_turn=True)

    def test_apply_backs_up_and_reads_back(self):
        backup = cal.apply_capture(self.bus, {'shoulder_lift': (250, 1800)}, self.digest)
        self.assertEqual(json.loads(backup.read_text()), self.old)
        self.assertEqual(json.loads(cal.CAL.read_text())['shoulder_lift']['range_min'], 250)
        self.assertEqual(self.bus._read(2, 55, 1), 1)
        self.assertEqual(self.bus._read(2, 11, 2), 1800)

    def test_failed_write_restores_motor_and_file(self):
        self.bus.fail_once = (2, 11)
        with self.assertRaisesRegex(RuntimeError, '元に戻しました'):
            cal.apply_capture(self.bus, {'shoulder_lift': (250, 1800)}, self.digest)
        self.assertEqual(json.loads(cal.CAL.read_text()), self.old)
        self.assertEqual((self.bus._read(2, 9, 2), self.bus._read(2, 11, 2), self.bus._read(2, 55, 1)), (100, 3000, 1))

    def test_torque_on_refuses_writes(self):
        self.bus.registers[2, 40] = 1
        with self.assertRaisesRegex(ValueError, 'トルク'):
            cal.apply_capture(self.bus, {'shoulder_lift': (250, 1800)}, self.digest)
        self.assertEqual(json.loads(cal.CAL.read_text()), self.old)
        self.assertEqual(self.bus._read(2, 9, 2), 100)

    def test_speed_accumulates_but_lag_is_bounded(self):
        pos, limits, target = {'shoulder_pan': 0}, {'shoulder_pan': (-90, 90)}, {}
        for _ in range(20):
            target = pad.next_goals(pos, [1, 0, 0, 0, 0, 0], limits, .05, target, 20)
        self.assertEqual(target['shoulder_pan'], 5)
        self.assertEqual(pad.next_goals(pos, [0] * 6, limits, .05, target, 20), {})

    def test_worker_records_and_torque_off_without_motion(self):
        bus = self.bus
        bus.calibration = {n: types.SimpleNamespace(id=i + 1, range_min=100, range_max=3000)
                           for i, n in enumerate(pad.JOINTS)}
        bus.bus = bus
        bus.is_connected = False
        bus.connect = lambda: setattr(bus, 'is_connected', True)
        bus.disconnect = lambda disable_torque=False: setattr(bus, 'is_connected', False)
        bus.read = lambda *args, **kwargs: 0
        bus.sync_read = lambda key, names, **kwargs: {n: 14 if n == 'gripper' else -83 for n in names}
        bus.sync_write = lambda *args: self.fail('recording must not send motion commands')
        for i in range(1, 7):
            bus.registers[i, 40] = 1
        previous = sys.modules.get('follower_pad_bus')
        fake_module = types.ModuleType('follower_pad_bus')
        fake_module.Follower = lambda port: bus
        sys.modules['follower_pad_bus'] = fake_module
        old_check = pad.check_motor_status
        pad.check_motor_status = lambda port, **kwargs: None
        try:
            controller = pad.Controller()
            def wait_for(predicate):
                end = time.monotonic() + 3
                while time.monotonic() < end:
                    if predicate():
                        return
                    time.sleep(.01)
                self.fail(controller.state)
            controller.post({'kind': 'connect'})
            wait_for(lambda: '接続済み' in controller.state)
            controller.post({'kind': 'cal_start'})
            wait_for(lambda: controller.calibration_state == 'recording')
            self.assertTrue(all(bus._read(i, 40, 1) == 0 for i in range(1, 7)))
            bus.registers[2, 56] = 1000
            wait_for(lambda: controller.calibration_samples >= 10)
            controller.post({'kind': 'cal_finish'})
            wait_for(lambda: controller.calibration_state == 'review')
            self.assertEqual(cal.candidate_from_capture(controller.calibration_ranges)['shoulder_lift'], (500, 1000))
            controller.post({'kind': 'cal_cancel'})
            wait_for(lambda: controller.calibration_state == 'idle')
            controller.post({'kind': 'torque_off'})
            wait_for(lambda: '全関節のトルク OFF' in controller.state)
        finally:
            pad.check_motor_status = old_check
            if previous is None:
                sys.modules.pop('follower_pad_bus', None)
            else:
                sys.modules['follower_pad_bus'] = previous

    def test_leader_calibration_records_and_updates_only_leader_file(self):
        leader_file = Path(self.tmp.name) / 'leader.json'
        leader_file.write_text(json.dumps(self.old))
        bus = self.bus
        bus.calibration = {n: types.SimpleNamespace(id=i + 1, range_min=100, range_max=3000)
                           for i, n in enumerate(pad.JOINTS)}
        bus.bus = bus
        bus.is_connected = False
        bus.connect = lambda: setattr(bus, 'is_connected', True)
        bus.disconnect = lambda disable_torque=False: setattr(bus, 'is_connected', False)
        bus.read = lambda *args, **kwargs: 0
        previous = sys.modules.get('follower_pad_bus')
        fake_module = types.ModuleType('follower_pad_bus')
        fake_module.Follower = lambda port, calibration_path=None: bus
        sys.modules['follower_pad_bus'] = fake_module
        old_check, old_owner, old_path = pad.check_motor_status, bilateral.assert_no_other_owner, bilateral.LEADER_CAL
        pad.check_motor_status = lambda port, **kwargs: None
        bilateral.assert_no_other_owner = lambda port: None
        bilateral.LEADER_CAL = leader_file
        try:
            controller = pad.Controller()
            def wait_for(predicate):
                end = time.monotonic() + 3
                while time.monotonic() < end:
                    if predicate(): return
                    time.sleep(.01)
                self.fail(controller.state)
            controller.post({'kind': 'leader_cal_connect'})
            wait_for(lambda: controller.mode == 'leader_calibration')
            self.assertEqual(controller.calibration_target, 'Leader')
            controller.post({'kind': 'cal_start'})
            wait_for(lambda: controller.calibration_state == 'recording')
            bus.registers[2, 56] = 1000
            wait_for(lambda: controller.calibration_samples >= 10)
            controller.post({'kind': 'cal_finish'})
            wait_for(lambda: controller.calibration_state == 'review')
            controller.post({'kind': 'cal_apply'})
            wait_for(lambda: 'Leader の較正を保存' in controller.state)
            self.assertEqual(json.loads(leader_file.read_text())['shoulder_lift']['range_max'], 1000)
            self.assertEqual(json.loads(cal.CAL.read_text()), self.old)
            self.assertFalse(bus.is_connected)
        finally:
            pad.check_motor_status, bilateral.assert_no_other_owner, bilateral.LEADER_CAL = old_check, old_owner, old_path
            if previous is None: sys.modules.pop('follower_pad_bus', None)
            else: sys.modules['follower_pad_bus'] = previous

    def test_leader_communication_failure_never_opens_or_writes(self):
        old_check, old_owner = pad.check_motor_status, bilateral.assert_no_other_owner
        def fail(port):
            raise ValueError('モーター ID1 の応答を確認できません')
        pad.check_motor_status = fail
        bilateral.assert_no_other_owner = lambda port: None
        try:
            controller = pad.Controller()
            controller.post({'kind': 'leader_cal_connect'})
            end = time.monotonic() + 2
            while time.monotonic() < end and 'ID1' not in controller.state:
                time.sleep(.01)
            self.assertIn('ID1', controller.state)
            self.assertEqual(controller.mode, 'controller')
            self.assertEqual(controller.calibration_state, 'idle')
            self.assertEqual(json.loads(cal.CAL.read_text()), self.old)
        finally:
            pad.check_motor_status, bilateral.assert_no_other_owner = old_check, old_owner

    def test_leader_id5_only_wrap_saves_without_modifying_calibration(self):
        old_data = json.loads(json.dumps(self.old))
        old_data['wrist_roll']['range_min'], old_data['wrist_roll']['range_max'] = 0, 4095
        leader_file = Path(self.tmp.name) / 'leader-wrap.json'
        leader_file.write_text(json.dumps(old_data))
        original_bytes = leader_file.read_bytes()
        bus = self.bus
        bus.calibration = {n: types.SimpleNamespace(id=i + 1, range_min=v['range_min'], range_max=v['range_max'])
                           for i, (n, v) in enumerate(old_data.items())}
        bus.bus = bus; bus.is_connected = False
        bus.connect = lambda: setattr(bus, 'is_connected', True)
        bus.disconnect = lambda disable_torque=False: setattr(bus, 'is_connected', False)
        bus.read = lambda *args, **kwargs: 0
        bus.registers[5, 56] = 3800
        previous = sys.modules.get('follower_pad_bus')
        fake_module = types.ModuleType('follower_pad_bus')
        fake_module.Follower = lambda port, calibration_path=None: bus
        sys.modules['follower_pad_bus'] = fake_module
        old_check, old_owner, old_path = pad.check_motor_status, bilateral.assert_no_other_owner, bilateral.LEADER_CAL
        pad.check_motor_status = lambda port, **kwargs: None
        bilateral.assert_no_other_owner = lambda port: None
        bilateral.LEADER_CAL = leader_file
        try:
            controller = pad.Controller()
            def wait_for(predicate):
                end = time.monotonic() + 3
                while time.monotonic() < end:
                    if predicate(): return
                    time.sleep(.01)
                self.fail(controller.state)
            controller.post({'kind': 'leader_cal_connect'})
            wait_for(lambda: controller.mode == 'leader_calibration')
            controller.post({'kind': 'cal_start'})
            wait_for(lambda: controller.calibration_state == 'recording')
            bus.registers[5, 56] = 4050
            wait_for(lambda: controller.calibration_ranges['wrist_roll']['last'] == 4050)
            bus.registers[5, 56] = 10
            wait_for(lambda: controller.calibration_ranges['wrist_roll'].get('wrapped'))
            wait_for(lambda: controller.calibration_samples >= 10)
            controller.post({'kind': 'cal_finish'})
            wait_for(lambda: controller.calibration_state == 'review')
            controller.post({'kind': 'cal_apply'})
            wait_for(lambda: '較正値の変更なし' in controller.state)
            self.assertEqual(leader_file.read_bytes(), original_bytes)
            self.assertFalse(bus.is_connected)
            self.assertEqual((bus._read(5, 9, 2), bus._read(5, 11, 2)), (100, 3000))
        finally:
            pad.check_motor_status, bilateral.assert_no_other_owner, bilateral.LEADER_CAL = old_check, old_owner, old_path
            if previous is None: sys.modules.pop('follower_pad_bus', None)
            else: sys.modules['follower_pad_bus'] = previous


if __name__ == '__main__':
    unittest.main()
