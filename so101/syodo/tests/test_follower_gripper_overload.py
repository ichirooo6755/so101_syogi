import importlib.util
import sys
import time
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from follower_motor_errors import MotorReadError, MotorRangeError
import follower_pad_bus

spec = importlib.util.spec_from_file_location('overload_test_pad', Path(__file__).parents[1] / 'scripts/follower_pad.py')
pad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pad)

class FakeFollower:
    def __init__(self, overloaded=False):
        self.bus = self
        self.is_connected = False
        self.is_calibrated = True
        self.overloaded = overloaded
        self.out_of_range = False
        self.calibration = {n: types.SimpleNamespace(id=i, range_min=100, range_max=3000)
                            for i, n in enumerate(pad.JOINTS, 1)}
        self.writes = []
    def connect(self): self.is_connected = True
    def disconnect(self, disable_torque=False): self.is_connected = False
    def calibration_matches(self, allow_gripper_overload=False): return allow_gripper_overload
    def read(self, *args, **kwargs): return 0
    def _read(self, i, address, length, allow_gripper_overload=False):
        if i == 6 and self.overloaded and not allow_gripper_overload:
            raise MotorReadError(6, 0, 32)
        return 0 if address in (33, 40) else 1500
    def sync_read(self, key, names, **kwargs):
        if self.overloaded and 'gripper' in names: raise MotorReadError(6, 0, 32)
        if self.out_of_range and 'elbow_flex' in names: raise MotorRangeError('elbow_flex', 3002, 100, 3000)
        return {n: 0 for n in names}
    def sync_write(self, key, values): self.writes.append(dict(values))
    def enable_torque(self, names): self.enabled = list(names)

class GripperOverloadTests(unittest.TestCase):
    def wait(self, predicate, ctl):
        end = time.monotonic() + 3
        while time.monotonic() < end:
            if predicate(): return
            time.sleep(.01)
        self.fail(ctl.state)
    def run_case(self, at_connect):
        arm = FakeFollower(at_connect)
        orig_follower, orig_check = follower_pad_bus.Follower, pad.check_motor_status
        follower_pad_bus.Follower = lambda *a, **k: arm
        pad.check_motor_status = lambda *a, **k: {6} if at_connect else set()
        try:
            ctl = pad.Controller()
            ctl.post({'kind':'connect'})
            self.wait(lambda: ctl.calibration_connected, ctl)
            ctl.post({'kind':'input','axes':[0]*6})
            ctl.post({'kind':'arm'})
            self.wait(lambda: ctl.armed, ctl)
            if at_connect:
                self.assertNotIn('gripper', arm.enabled)
                self.assertTrue(all('gripper' not in row for row in arm.writes))
            else:
                arm.overloaded = True
                ctl.post({'kind':'input','axes':[0]*6})
                self.wait(lambda: 'ID6 過負荷・グリッパーを除外して停止' in ctl.state, ctl)
                self.assertFalse(ctl.armed)
                self.assertNotIn('gripper', arm.writes[-1])
                ctl.post({'kind':'input','axes':[0]*6})
                ctl.post({'kind':'arm'})
                self.wait(lambda: ctl.armed, ctl)
                self.assertNotIn('gripper', arm.enabled)
            ctl.post({'kind':'disconnect'})
            self.wait(lambda: not arm.is_connected, ctl)
        finally:
            follower_pad_bus.Follower, pad.check_motor_status = orig_follower, orig_check
    def test_overload_at_connection_blocks_only_gripper(self): self.run_case(True)
    def test_overload_while_running_requires_explicit_restart(self): self.run_case(False)
    def test_range_fault_holds_other_joints_without_commanding_faulted_joint(self):
        arm = FakeFollower()
        orig_follower, orig_check = follower_pad_bus.Follower, pad.check_motor_status
        follower_pad_bus.Follower = lambda *a, **k: arm
        pad.check_motor_status = lambda *a, **k: set()
        try:
            ctl = pad.Controller()
            ctl.post({'kind':'connect'})
            self.wait(lambda: ctl.calibration_connected, ctl)
            ctl.post({'kind':'input','axes':[0]*6})
            ctl.post({'kind':'arm'})
            self.wait(lambda: ctl.armed, ctl)
            arm.out_of_range = True
            ctl.post({'kind':'input','axes':[0]*6})
            self.wait(lambda: 'ひじが較正範囲外' in ctl.state, ctl)
            self.assertFalse(ctl.armed)
            self.assertNotIn('elbow_flex', arm.writes[-1])
            self.assertEqual(set(arm.writes[-1]), set(pad.JOINTS) - {'elbow_flex'})
            ctl.post({'kind':'disconnect'})
            self.wait(lambda: not arm.is_connected, ctl)
        finally:
            follower_pad_bus.Follower, pad.check_motor_status = orig_follower, orig_check
    def test_only_exact_id6_overload_is_special(self):
        self.assertTrue(MotorReadError(6, 0, 32).gripper_overload)
        for args in [(5, 0, 32), (6, -6, 32), (6, 0, 33)]:
            self.assertFalse(MotorReadError(*args).gripper_overload)

if __name__ == '__main__': unittest.main()
