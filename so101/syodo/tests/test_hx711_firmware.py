import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "firmware" / "pico2w-hx711"))
from hx711 import is_saturated, sample_dict, signed_24  # noqa: E402


def test_signed_24_and_sat():
    assert signed_24(0) == 0
    assert signed_24(0x7FFFFF) == 0x7FFFFF
    assert signed_24(0xFFFFFF) == -1
    assert signed_24(0x800000) == -0x800000
    assert is_saturated(signed_24(0x7FFFFF))
    assert not is_saturated(0)


def test_jsonl_matches_force_plate_input():
    row = sample_dict([1, 2, 3, 4], [0.1, 0.1, 0.11, 0.12], False)
    parsed = json.loads(json.dumps(row))
    assert parsed["raw_counts"] == [1, 2, 3, 4]
    assert parsed["saturated"] is False
    assert len(parsed["channel_time_s"]) == 4


def firmware(monkeypatch, tmp_path):
    import importlib.util
    import types
    monkeypatch.chdir(tmp_path)
    machine = types.SimpleNamespace(Pin=object, disable_irq=lambda: 0, enable_irq=lambda _: None)
    monkeypatch.setitem(sys.modules, 'machine', machine)
    spec = importlib.util.spec_from_file_location('plate_firmware', ROOT/'firmware/pico2w-hx711/main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unresponsive_channels_cannot_overwrite_tare(monkeypatch, tmp_path):
    import types
    module = firmware(monkeypatch,tmp_path)
    clock = types.SimpleNamespace(now=0.)
    clock.seconds = lambda: clock.now
    chip = types.SimpleNamespace(ready=lambda: False)
    events=[]
    board=module.Controller([chip]*4,clock,events.append)
    board.zero=[1.,2.,3.,4.]
    board.command('tare')
    for _ in range(45):
        clock.now += .3
        board.step()
    assert board.zero == [1.,2.,3.,4.]
    assert any(e.get('error') == 'calibration_timeout' for e in events)
    assert not (tmp_path/'cal.json').exists()
    assert all(e['hx711_ready'] == [False]*4 for e in events if 'raw_counts' in e)


def test_firmware_handles_partial_availability_and_sync(monkeypatch,tmp_path):
    import types
    module=firmware(monkeypatch,tmp_path)
    clock=types.SimpleNamespace(now=1.)
    clock.seconds=lambda:clock.now
    live=types.SimpleNamespace(ready=lambda:True,read=lambda:123)
    dead=types.SimpleNamespace(ready=lambda:False)
    events=[]
    board=module.Controller([live,dead,live,live],clock,events.append)
    board.command('sync abc')
    assert events[-1]['token'] == 'abc'
    assert events[-1]['device_time_s'] == 1
    board.step()
    clock.now += .3
    board.step()
    assert events[-1]['hx711_ready'] == [True,False,True,True]
    assert events[-1]['raw_counts'] == [123,0,123,123]
    for command in ['cal -1 1', 'cal 5 1','cal 0 nan','cal 0 -1','tare 9','blah']:
        board.command(command)
        assert 'error' in events[-1]


def test_hx711_has_25_bounded_pulses_and_finishes_low(monkeypatch,tmp_path):
    import types
    module=firmware(monkeypatch,tmp_path)
    events=[]
    class Pin:
        IN,OUT,PULL_UP=0,1,2
        def __init__(self,number,*args,**kwargs):
            self.number=number
        def value(self,*value):
            if value:
                events.append((self.number,value[0]))
            else:
                return 1
    module.Pin=Pin
    module.time=types.SimpleNamespace(sleep_us=lambda us:events.append(('sleep',us)))
    module.disable_irq=lambda:events.append(('irq',False))
    module.enable_irq=lambda _:events.append(('irq',True))
    chip=module.Hx711(2,6)
    assert chip.read() == -1
    assert sum(e == (6,1) for e in events) == 25
    assert events[-1] == (6,0)
    irq_on=True
    for kind,value in events:
        if kind == 'irq':
            irq_on=value
        if kind == 6 and value == 1:
            assert not irq_on
