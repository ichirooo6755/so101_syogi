import math
import importlib.util
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import follower_bilateral as b
spec = importlib.util.spec_from_file_location('follower_pad_bilateral_test', Path(__file__).parents[1] / 'scripts/follower_pad.py')
pad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pad)


class FakeArm:
    def __init__(self, port, calibration_path=None):
        self.calibration = {n: SimpleNamespace(id=i + 1, range_min=0, range_max=4095)
                            for i, n in enumerate(b.NAMES)}
        self.position = {n: (50.0 if n == 'gripper' else 0.0) for n in b.NAMES}
        self.torque = {i: 0 for i in range(1, 7)}
        self.torque_limit = {i: 500 for i in range(1, 7)}
        self.is_connected = False
        self.is_calibrated = True
        self.writes = []

    def connect(self): self.is_connected = True
    def disconnect(self, disable_torque=False): self.is_connected = False
    def read(self, *args, **kwargs): return 0
    def sync_read(self, *args, **kwargs): return dict(self.position)
    def sync_write(self, name, values): self.writes.append(dict(values))
    def _read(self, i, address, length): return {40: self.torque, 48: self.torque_limit}[address][i]
    def _write(self, i, address, length, value): {40: self.torque, 48: self.torque_limit}[address][i] = value
    def enable_torque(self, names):
        for n in names: self.torque[self.calibration[n].id] = 1


class BilateralTests(unittest.TestCase):
    def setUp(self):
        self.factory = patch.object(b, 'Follower', FakeArm)
        self.owner = patch.object(b, 'assert_no_other_owner')
        self.factory.start(); self.owner.start()
        self.pair = b.BilateralPair('/follower', '/leader')

    def tearDown(self):
        self.factory.stop(); self.owner.stop()

    def test_read_only_connect_and_start_at_current_positions(self):
        self.pair.follower.position['shoulder_pan'] = 20
        self.pair.connect()
        self.assertEqual(self.pair.master.writes, [])
        self.assertEqual(self.pair.follower.writes, [])
        self.pair.start()
        self.assertEqual(self.pair.follower.writes[0]['shoulder_pan'], 20)
        self.assertEqual(self.pair.master.writes[0]['shoulder_pan'], 0)
        self.assertEqual(self.pair.offsets['shoulder_pan'], 20)
        self.assertEqual(self.pair.master.torque_limit[1], 200)
        self.pair.step()
        self.assertEqual(self.pair.follower.writes[-1]['shoulder_pan'], 20)
        self.assertEqual(self.pair.master.writes[-1]['shoulder_pan'], 0)

    def test_bidirectional_limits_and_error_stop(self):
        self.pair.connect(); self.pair.start()
        self.pair.master.position['shoulder_pan'] = 3
        self.pair.step()
        self.assertAlmostEqual(self.pair.follower.writes[-1]['shoulder_pan'], .7)
        self.assertAlmostEqual(self.pair.master.writes[-1]['shoulder_pan'], 2.3)
        self.assertEqual(self.pair.master_limits['wrist_roll'], (-15, 15))
        self.pair.master.position['wrist_roll'] = 16
        with self.assertRaises(ValueError): self.pair.step()
        self.pair.master.position['wrist_roll'] = 0
        self.pair.master.position['shoulder_pan'] = 16
        with self.assertRaises(ValueError): self.pair.step()

    def test_torque_off_restores_leader_limit(self):
        self.pair.connect(); self.pair.start(); self.pair.torque_off()
        self.assertTrue(all(x == 0 for x in self.pair.master.torque.values()))
        self.assertTrue(all(x == 0 for x in self.pair.follower.torque.values()))
        self.assertTrue(all(x == 500 for x in self.pair.master.torque_limit.values()))
        self.assertFalse(self.pair.armed)

    def test_failed_calibration_closes_both_without_writes(self):
        self.pair.master.is_calibrated = False
        with self.assertRaisesRegex(ValueError, '較正'): self.pair.connect()
        self.assertFalse(self.pair.master.is_connected)
        self.assertEqual(self.pair.master.writes, [])
        self.assertEqual(self.pair.follower.writes, [])

    def test_same_port_and_nonfinite_rejected(self):
        with self.assertRaises(ValueError): b.BilateralPair('/same', '/same')
        self.pair.connect(); self.pair.start()
        self.pair.master.position['shoulder_pan'] = math.nan
        with self.assertRaises(ValueError): self.pair.step()

    def test_partial_start_error_is_held_before_closing(self):
        self.pair.connect()
        def fail(_names):
            raise OSError('injected torque failure')
        self.pair.follower.enable_torque = fail
        with self.assertRaises(OSError): self.pair.start()
        self.assertTrue(self.pair.armed)
        self.pair.close(hold=True)
        self.assertFalse(self.pair.armed)
        self.assertFalse(self.pair.follower.is_connected)
        self.assertGreaterEqual(len(self.pair.follower.writes), 2)

    def test_start_cancel_does_not_enable_torque(self):
        self.pair.connect()
        with self.assertRaisesRegex(ValueError, '中止'):
            self.pair.start(lambda: False)
        self.assertTrue(all(x == 0 for x in self.pair.master.torque.values()))
        self.assertTrue(all(x == 0 for x in self.pair.follower.torque.values()))


class WorkerTests(unittest.TestCase):
    def test_bilateral_uses_visible_ui_watchdog_without_gamepad(self):
        class Pair:
            def __init__(self, port):
                self.armed = False; self.steps = 0; self.holds = 0
            def connect(self): pass
            def start(self, guard): self.armed = True
            def step(self): self.steps += 1
            def hold(self): self.armed = False; self.holds += 1
            def close(self, hold=True):
                if hold and self.armed: self.hold()
        made = []
        def factory(port):
            obj = Pair(port); made.append(obj); return obj
        def wait_for(predicate):
            end = time.monotonic() + 2
            while time.monotonic() < end:
                if predicate(): return
                time.sleep(.01)
            self.fail(controller.state)
        with patch.object(b, 'BilateralPair', factory):
            controller = pad.Controller()
            controller.post({'kind': 'bilateral_connect'})
            wait_for(lambda: controller.mode == 'bilateral')
            controller.ui_last = time.monotonic()
            controller.post({'kind': 'bilateral_start'})
            wait_for(lambda: controller.armed)
            wait_for(lambda: made[0].steps > 0)
            controller.ui_last = time.monotonic() - 1
            wait_for(lambda: not controller.armed)
            self.assertEqual(made[0].holds, 1)
            self.assertIn('通信が途絶', controller.state)


if __name__ == '__main__': unittest.main()
