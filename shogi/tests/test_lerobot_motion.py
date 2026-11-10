"""Exercise the LeRobot joint-action contract without connecting hardware."""
import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from lerobot_motion import KEYS, MotionStopped, PositionController


class FakeClock:
    def __init__(self): self.t=0.
    def now(self): return self.t
    def sleep(self,seconds): self.t+=seconds


class Robot:
    def __init__(self,follow=True):
        self.config=SimpleNamespace(use_degrees=True,max_relative_target=1.)
        self.is_connected=True
        self.position={k:0. for k in KEYS}
        self.follow=follow;self.commands=[];self.bad_read=False

    def get_observation(self):
        if self.bad_read: raise OSError('unavailable')
        return dict(self.position)

    def send_action(self,action):
        self.commands.append(dict(action))
        if self.follow:self.position=dict(action)
        return dict(action)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.robot=Robot();self.clock=FakeClock()
        self.limits={k:(-20.,20.) for k in KEYS}
        self.rates={k:4. for k in KEYS}
        self.tolerances={k:.01 for k in KEYS}
        self.errors={k:1. for k in KEYS}

    def controller(self):
        return PositionController(self.robot,self.limits,self.rates,self.tolerances,self.errors,
                                  clock=self.clock.now,sleep=self.clock.sleep)

    def test_feedback_converges_with_bounded_complete_actions(self):
        target={k:1. for k in KEYS}
        result=self.controller().move_to(target,timeout=3.)
        self.assertTrue(result['reached'])
        previous={k:0. for k in KEYS}
        for action in self.robot.commands:
            self.assertEqual(set(action),set(KEYS))
            for k in KEYS:self.assertLessEqual(abs(action[k]-previous[k]),.200001)
            previous=action
        self.assertTrue(all(abs(v-1.)<.01 for v in result['observed'].values()))

    def test_no_control_without_official_relative_limit(self):
        self.robot.config.max_relative_target=None
        with self.assertRaisesRegex(ValueError,'max_relative_target'):self.controller()
        self.assertEqual(self.robot.commands,[])

    def test_no_goal_outside_validated_limits(self):
        target={k:0. for k in KEYS};target[KEYS[2]]=50.
        with self.assertRaisesRegex(ValueError,'outside'):self.controller().move_to(target,timeout=2.)
        self.assertEqual(self.robot.commands,[])

    def test_stalled_arm_is_not_reported_as_reached(self):
        self.robot.follow=False
        target={k:4. for k in KEYS}
        with self.assertRaisesRegex(MotionStopped,'follow') as caught:
            self.controller().move_to(target,timeout=5.)
        self.assertTrue(caught.exception.hold_command_sent)
        self.assertEqual(self.robot.commands[-1],self.robot.position)

    def test_cancel_before_start_sends_nothing(self):
        target={k:1. for k in KEYS}
        with self.assertRaises(MotionStopped):self.controller().move_to(target,timeout=2.,cancel=lambda:True)
        self.assertEqual(self.robot.commands,[])

    def test_invalid_observation_does_not_generate_a_goal(self):
        self.robot.position[KEYS[0]]=math.nan
        with self.assertRaisesRegex(ValueError,'finite'):
            self.controller().move_to({k:1. for k in KEYS},timeout=2.)
        self.assertEqual(self.robot.commands,[])


if __name__=='__main__':unittest.main()
