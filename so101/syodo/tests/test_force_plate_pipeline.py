"""Force/position metrology, time alignment, and bounded transport regression tests."""
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import pty
import threading
import time
import types

import numpy as np
import pytest

from so101_calligraphy.force_plate import ForcePlateCalibration, PlateGeometry, estimate_sample
from so101_calligraphy.force_plate_calibration import fit_calibration, fit_registration
from so101_calligraphy.force_plate_io import PicoStream, timestamp_sample, ForceRecorder
from scripts.analyze_force_plate import analyze, read_samples
from scripts.force_plate import main


def cal():
    return ForcePlateCalibration(.270, .170, (0,)*4, (.01,)*4, .02, 10, .005)


def sample(raw=(25,25,25,25), t=1):
    return {'raw_counts': list(raw), 'channel_time_s': [t]*4, 'saturated': False,
            'hx711_ready': [True]*4, 'cell_ids': [2,4,3,1], 'boot_id': 'test',
            'sequence': int(t*1000)}


def test_missing_channel_cannot_appear_as_valid_contact():
    s = sample()
    s['hx711_ready'][2] = False
    row = estimate_sample(cal(), s, PlateGeometry())
    assert not row['valid']
    assert row['invalid_reason'] == 'channel_not_ready'
    assert row['board_x_mm'] is None


@pytest.mark.parametrize('raw,xy', [((100,0,0,0),(15,285)), ((0,100,0,0),(15,15)),
                                     ((0,0,100,0),(185,15)), ((0,0,0,100),(185,285)),
                                     ((25,25,25,25),(100,150))])
def test_actual_board_support_locations(raw,xy):
    row = estimate_sample(cal(), sample(raw), PlateGeometry())
    assert (row['board_x_mm'],row['board_y_mm']) == pytest.approx(xy)
    assert row['mass_equivalent_g'] == pytest.approx(1000/9.80665)


@pytest.mark.parametrize('field,value', [('hx711_ready',[1]*4),('hx711_ready',[True]),('cell_ids',[1,2,3,4])])
def test_bad_channel_metadata_is_rejected(field,value):
    s = sample()
    s[field] = value
    with pytest.raises(ValueError):
        estimate_sample(cal(),s)


def test_adc_rail_detected_even_when_saturation_flag_is_wrong():
    assert estimate_sample(cal(),sample([8388607,0,0,0]))['invalid_reason'] == 'adc_saturation'


@pytest.fixture
def synthetic(tmp_path):
    root = tmp_path/'demo'
    assert main(['demo','--out',str(root)]) == 0
    return root


def test_calibration_fits_different_signed_gains_and_heldout_points(synthetic):
    p = json.loads((synthetic/'calibration.json').read_text())
    assert p['calibration']['newtons_per_count'] == pytest.approx([.00002,-.000025,.000018,.00003],rel=.001)
    assert p['static_validation']['passed']
    assert all(c['position_error_mm'] < .1 for c in p['static_validation']['checks'])
    summary = json.loads((synthetic/'analysis/summary.json').read_text())
    assert summary['missing_contact_samples'] == 5
    assert summary['aligned_samples'] == 479
    assert summary['invalid_reasons']['channel_not_ready'] == 1
    assert summary['training_eligible'] is False
    assert (synthetic/'analysis/strokes.csv').exists()
    assert (synthetic/'analysis/force-plate.png').stat().st_size > 1000


@pytest.mark.parametrize('bad', ['rank','holdout','drift','missing','zero_mass'])
def test_bad_calibration_cannot_be_adopted(synthetic,bad):
    m = json.loads((synthetic/'calibration-measurements.json').read_text())
    if bad == 'rank':
        for p in m['placements']:
            p['samples'] = m['tare_samples']
    elif bad == 'holdout':
        m['placements'][-1]['mass_g'] *= 1.5
    elif bad == 'drift':
        m['final_tare_samples'] = json.loads(json.dumps(m['tare_samples']))
        for s in m['final_tare_samples']:
            s['raw_counts'][0] += 5000
    elif bad == 'missing':
        m['tare_samples'][0]['hx711_ready'][0] = False
    else:
        m['placements'][0]['mass_g'] = 0
    with pytest.raises(ValueError):
        fit_calibration(m)


def test_registration_checks_heldout_fiducial():
    points = [{'role':role,'board_xy_mm':[x,y], 'robot_xy_m':[.3-y*.001, -.1+x*.001]}
              for role,x,y in [('fit',0,0),('fit',210,0),('fit',0,297),('validate',150,200)]]
    reg = fit_registration(points,'desk123')
    assert reg['max_error_mm'] < 1e-9
    points[-1]['robot_xy_m'][0] += .01
    with pytest.raises(ValueError,match='error limit'):
        fit_registration(points,'desk123')


def test_fragmented_frames_buffered_and_timeout_bounded():
    master,slave = pty.openpty()
    try:
        with PicoStream(os.ttyname(slave)) as stream:
            os.write(master,b'{"a":1}\n{"b":2}\n{"c":')
            assert stream.read(.2)['a'] == 1
            assert stream.read(.2)['b'] == 2  # no new read required
            start=time.monotonic()
            with pytest.raises(TimeoutError):
                stream.read(.04)
            assert time.monotonic()-start < .2
            os.write(master,b'3}\n')
            assert stream.read(.2)['c'] == 3
    finally:
        os.close(master)
        os.close(slave)


def test_recorder_stops_even_without_a_newline(tmp_path):
    master,slave = pty.openpty()
    try:
        recorder=ForceRecorder(os.ttyname(slave),tmp_path/'raw.jsonl',synchronize=False).start()
        time.sleep(.05)
        os.write(master,b'partial')
        start=time.monotonic()
        recorder.close()
        assert time.monotonic()-start < 1
        with pytest.raises(FileExistsError):
            ForceRecorder(os.ttyname(slave),tmp_path/'raw.jsonl').start()
    finally:
        os.close(master)
        os.close(slave)


def test_clock_mapping_keeps_acquisition_and_arrival_distinct():
    s = sample(t=2)
    s['host_receive_monotonic_s']=202
    row=timestamp_sample(s,{'boot_id':'test','device_time_s':1,'offset_s':100,'uncertainty_s':.002})
    assert row['host_sample_monotonic_s'] == 102
    assert row['clock_uncertainty_s'] == pytest.approx(.003)
    with pytest.raises(ValueError,match='rebooted'):
        timestamp_sample(s,{'boot_id':'new'})


def test_offline_refuses_boot_and_clock_restarts(tmp_path):
    a,b=sample(t=1),sample(t=2)
    b['boot_id']='new'
    p=tmp_path/'raw.jsonl'
    p.write_text(json.dumps(a)+'\n'+json.dumps(b)+'\n')
    with pytest.raises(ValueError,match='rebooted'):
        list(read_samples(p))


def test_wrong_session_and_uncertain_clock_never_produce_training_metrics(synthetic):
    raw=[json.loads(s) for s in (synthetic/'raw.jsonl').read_text().splitlines()]
    for s in raw:
        s['clock_uncertainty_s']=1.0
    p=synthetic/'uncertain.jsonl'
    p.write_text(''.join(json.dumps(s)+'\n' for s in raw))
    summary=analyze(p,synthetic/'calibration.json',synthetic/'uncertain',robot_log=synthetic/'write.csv',plots=False)
    assert summary['aligned_samples'] == 0
    raw[0]['force_plate_session']='another-run'
    p.write_text(''.join(json.dumps(s)+'\n' for s in raw))
    with pytest.raises(ValueError,match='same force-plate'):
        analyze(p,synthetic/'calibration.json',synthetic/'wrong-session',robot_log=synthetic/'write.csv',plots=False)


def test_write_rejects_synthetic_calibration_before_any_process(synthetic,monkeypatch):
    from scripts.force_plate import write_with_plate
    from so101_calligraphy import hardware_desk
    monkeypatch.setattr(hardware_desk,'require_ready',lambda d:d)
    monkeypatch.setattr(hardware_desk,'load_desk',lambda p:{})
    args=types.SimpleNamespace(calibration=synthetic/'calibration.json')
    with pytest.raises(ValueError,match='実測'):
        write_with_plate(args)
