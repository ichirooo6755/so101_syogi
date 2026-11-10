import importlib.util
import math
from pathlib import Path
import time

import pytest

spec = importlib.util.spec_from_file_location('leader_pad', Path(__file__).parents[1] / 'scripts/leader_pad.py')
pad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pad)


def test_small_steps_deadzone_and_limits():
    pos = dict(zip(pad.JOINTS, (0, 0, 0, 9.99, 50)))
    limits = {name: (-10, 10) for name in pad.JOINTS}
    limits['gripper'] = (5, 95)
    result = pad.next_goals(pos, [1, 0.1, -1, 1, 1], limits, 10)
    assert result == {'shoulder_pan': .25, 'elbow_flex': -.25, 'wrist_flex': 10, 'gripper': 50.2}
    assert 'wrist_roll' not in result


def test_reject_bad_input_and_position():
    pos = dict.fromkeys(pad.JOINTS, 0)
    limits = dict.fromkeys(pad.JOINTS, (-10, 10))
    with pytest.raises(ValueError):
        pad.next_goals(pos, [math.nan, 0, 0, 0, 0], limits, .05)
    pos['shoulder_pan'] = 11
    with pytest.raises(ValueError):
        pad.next_goals(pos, [1, 0, 0, 0, 0], limits, .05)


def test_stop_revokes_motion_and_input_validation():
    controller = pad.Controller()
    controller.armed = True
    controller.post({'kind': 'input', 'deadman': True, 'axes': [1, 0, 0, 0, 0]})
    controller.post({'kind': 'stop'})
    assert controller.armed is False
    assert controller.input is None
    with pytest.raises(ValueError):
        controller.post({'kind': 'input', 'deadman': True, 'axes': [2, 0, 0, 0, 0]})
