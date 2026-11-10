#!/usr/bin/env python3
"""200 × 300 mm load-cell plate: setup, calibrate, capture, analyze, and robot integration."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT)]
from so101_calligraphy.force_plate import PlateGeometry
from so101_calligraphy.force_plate_calibration import fit_calibration, fit_registration, load_calibration
from so101_calligraphy.force_plate_io import PicoStream, ForceRecorder


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def capture(stream, seconds):
    rows = []
    deadline = time.monotonic() + seconds
    # Clear pre-placement USB frames, then let the static load settle.
    stream.buffer = b''
    import termios
    termios.tcflush(stream.fd, termios.TCIFLUSH)
    settle = time.monotonic() + 1
    while time.monotonic() < deadline + 1:
        try:
            row = stream.read(.25)
        except TimeoutError:
            continue
        if 'raw_counts' in row and time.monotonic() >= settle:
            if row.get('hx711_ready') != [True]*4:
                raise ValueError('4台すべてのHX711が応答する必要があります。配線を確認してください。')
            rows.append(row)
    from so101_calligraphy.force_plate_calibration import capture_mean
    capture_mean(rows)
    return rows


def calibrate(args):
    if args.out.exists():
        raise ValueError(f'Output already exists: {args.out}')
    profile = json.loads(args.geometry.read_text())
    geometry = PlateGeometry(**profile['geometry'])
    print('200 × 300 mm縦、左上が原点、右＋X・下＋Y。番号: 左上④ 右上③ 左下② 右下①。')
    print(f'支持点mm（②④③①）: {geometry.supports_mm}')
    if input('現物の支持位置を測り、この設定と一致していますか？ yes を入力: ').strip() != 'yes':
        raise ValueError('geometry JSONを実測の支持位置に変更してから再実行してください')
    fingerprint = None
    if args.desk:
        from so101_calligraphy.hardware_desk import load_desk, desk_fingerprint, require_ready
        fingerprint = desk_fingerprint(require_ready(load_desk(args.desk)))
    manifest = {'geometry': asdict(geometry), 'source': 'measured', 'placements': [],
                'maximum_channel_skew_s': args.maximum_channel_skew_s,
                'desk_fingerprint': fingerprint}
    x0, x1, y0, y1 = geometry.left_mm, geometry.right_mm, geometry.top_mm, geometry.bottom_mm
    positions = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), ((x0+x1)/2, (y0+y1)/2)]
    heldout = [(x0+.25*(x1-x0), y0+.25*(y1-y0)),
               (x0+.75*(x1-x0), y0+.35*(y1-y0)),
               (x0+.4*(x1-x0), y0+.75*(y1-y0))]
    with PicoStream(args.port) as stream:
        input('板・下敷き・紙・紙留めを載せ、筆も手も離して Enter: ')
        manifest['tare_samples'] = capture(stream, args.seconds)
        for role, points in [('fit', positions), ('validate', heldout)]:
            for x, y in points:
                input(f'{args.mass_g:g} g の重りの中心を左から{x:g} mm・上から{y:g} mmへ置いて Enter [{role}]: ')
                samples = capture(stream, args.seconds)
                manifest['placements'].append({'role': role, 'mass_g': args.mass_g,
                                                'x_mm': x, 'y_mm': y, 'samples': samples})
        input('重りを取り去り、板も紙も動かさず Enter（ゼロ点の再確認）: ')
        final_zero = capture(stream, args.seconds)
    # Retain evidence even when the fit or drift check fails.
    args.out.mkdir(parents=True, exist_ok=False)
    manifest['final_tare_samples'] = final_zero
    write_json(args.out/'calibration-measurements.json', manifest)
    result = fit_calibration(manifest)
    write_json(args.out/'calibration.json', result)
    print(f'較正を保存: {args.out / "calibration.json"}')


def demo(args):
    import numpy as np
    from scripts.analyze_force_plate import analyze
    geometry = PlateGeometry()
    rng = np.random.default_rng(42)
    zeros = np.array([100000, -300000, 250000, 120000])
    gains = np.array([.00002, -.000025, .000018, .00003])
    sequence = 0
    def frame(force, x, y, t):
        nonlocal sequence
        a = (geometry.bottom_mm-y)/(geometry.bottom_mm-geometry.top_mm)
        b = (x-geometry.left_mm)/(geometry.right_mm-geometry.left_mm)
        reactions = force * np.array([(1-a)*(1-b), a*(1-b), a*b, (1-a)*b])
        raw = np.rint(zeros + reactions/gains + rng.normal(0, 1, 4)).astype(int).tolist()
        row = {'schema': 2, 'raw_counts': raw, 'channel_time_s': [t+i*.0001 for i in range(4)],
               'hx711_ready': [True]*4, 'cell_ids': [2, 4, 3, 1], 'saturated': False,
               'sequence': sequence, 'boot_id': 'synthetic-demo', 'source': 'synthetic',
               'ready_poll_uncertainty_s': [.0002]*4}
        sequence += 1
        return row
    def samples(f, x, y):
        return [frame(f, x, y, 1+i*.1) for i in range(32)]
    manifest = {'source': 'synthetic', 'geometry': asdict(geometry), 'placements': [],
                'tare_samples': samples(0, 100, 150)}
    for role, points in [('fit', [(20,20),(180,20),(180,280),(20,280),(100,150)]),
                         ('validate', [(60,90),(150,100),(95,220)])]:
        for x,y in points:
            manifest['placements'].append({'role': role, 'mass_g': 100., 'x_mm': x, 'y_mm': y,
                                            'samples': samples(.980665, x, y)})
    result = fit_calibration(manifest)
    args.out.mkdir(parents=True, exist_ok=False)
    write_json(args.out/'calibration.json', result)
    write_json(args.out/'calibration-measurements.json', manifest)
    import csv
    with (args.out/'raw.jsonl').open('x') as f, (args.out/'write.csv').open('x', newline='') as robot_file:
        writer = csv.DictWriter(robot_file, fieldnames=['index','phase','cell','pen_down','target_pressure',
                                    'command_start_monotonic_s','host_monotonic_s','force_plate_session'])
        writer.writeheader()
        for i in range(480):
            t = 10 + i*.025
            down = (i // 80) % 2 == 0
            force = (.35+.1*math.sin(i*.06)) if down else 0
            # Deliberate gap and one missing sensor validate the failure paths.
            if 35 <= i < 40:
                force = 0
            row = frame(force, 100+60*math.sin(i*.017), 150+85*math.cos(i*.023), t)
            if i == 200:
                row['hx711_ready'][2] = False
            row.update({'host_sample_monotonic_s': 1000+t+.00015,
                        'clock_uncertainty_s': .0003, 'force_plate_session': 'synthetic-demo'})
            f.write(json.dumps(row)+'\n')
            writer.writerow({'index': i, 'phase': 'write', 'cell': 0, 'pen_down': down,
                             'target_pressure': .6 if down else 0,
                             'command_start_monotonic_s': 1000+t-.012,
                             'host_monotonic_s': 1000+t+.013,
                             'force_plate_session': 'synthetic-demo'})
    summary = analyze(args.out/'raw.jsonl', args.out/'calibration.json', args.out/'analysis', robot_log=args.out/'write.csv')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f'デモ結果: {args.out / "analysis" / "force-plate.png"}')


def write_with_plate(args):
    from so101_calligraphy.force_plate import estimate_sample
    from so101_calligraphy.hardware_desk import DEFAULT_DESK_PATH, load_desk, require_ready, desk_fingerprint
    from scripts.analyze_force_plate import analyze
    payload, calibration, geometry = load_calibration(args.calibration)
    desk = require_ready(load_desk(DEFAULT_DESK_PATH))
    if payload.get('source') != 'measured' or payload.get('static_validation', {}).get('passed') is not True:
        raise ValueError('書字記録には実測で検証済みの較正が必要です')
    if payload.get('desk_fingerprint') != desk_fingerprint(desk):
        raise ValueError('板設置後のdesk再較正と、同じdeskに紐づくロードセル較正が必要です')
    if args.registration:
        reg = json.loads(args.registration.read_text())
        if reg.get('validated') is not True or reg.get('desk_fingerprint') != desk_fingerprint(desk):
            raise ValueError('Registration does not match the current desk')
    args.out.mkdir(parents=True, exist_ok=False)
    session = uuid.uuid4().hex
    recorder = ForceRecorder(args.port, args.out/'raw.jsonl', session_id=session).start()
    process = None
    write_json(args.out/'session.json', {'schema': 1, 'force_plate_session': session,
                'desk_fingerprint': desk_fingerprint(desk), 'mode': 'measurement_only',
                'calibration': str(args.calibration.resolve()), 'started_unix_s': time.time()})
    try:
        if not recorder.ready.wait(12) or recorder.error or not recorder.last_sample:
            raise ValueError(f'Picoから時刻同期済みのデータを取得できません: {recorder.error}')
        sample = recorder.last_sample
        row = estimate_sample(calibration, sample, geometry)
        if sample.get('hx711_ready') != [True]*4 or sample.get('saturated') is not False:
            raise ValueError('HX711の4台応答・非飽和を確認できません')
        if (abs(row['normal_force_n']) >= calibration.minimum_force_n or
                max(abs(v) for v in row['channel_force_n']) >= calibration.minimum_force_n):
            raise ValueError('開始前に筆・手を離してください。荷重ゼロ点がずれた場合は再較正してください')
        if row['channel_skew_s'] > calibration.maximum_channel_skew_s or sample['clock_uncertainty_s'] > .03:
            raise ValueError('チャンネル時刻差またはUSB時刻同期の精度が不足しています')
        env = dict(os.environ, SYODO_FORCE_PLATE_SESSION=session)
        command = [str(ROOT/'scripts/hw-write'), args.text, '--speed', str(args.speed),
                   '--log', str(args.out.resolve()/'write.csv')]
        print('ロードセルの同時記録付きで書字を開始します。', flush=True)
        process = subprocess.Popen(command, cwd=ROOT, env=env)
        status = process.wait()
        if status:
            raise RuntimeError(f'hw-write exited with status {status}')
    finally:
        # Preserve raw and partial robot logs on interruption/failure.
        if process is not None and process.poll() is None:
            import signal
            process.send_signal(signal.SIGINT)
            process.wait()
        try:
            recorder.close()
        finally:
            if (args.out/'write.csv').exists():
                analyze(args.out/'raw.jsonl', args.calibration, args.out/'analysis',
                        robot_log=args.out/'write.csv', registration=args.registration)
    print(f'書字・荷重の分析を保存: {args.out}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='Write editable 200 × 300 mm support geometry')
    init.add_argument('--out', type=Path, default=Path('data/hardware/force-plate-geometry.json'))
    fit = sub.add_parser('fit', help='Fit offline calibration measurements')
    fit.add_argument('manifest', type=Path)
    fit.add_argument('--out', type=Path, required=True)
    cal = sub.add_parser('calibrate', help='Interactive assembled-board weight calibration')
    cal.add_argument('--port', required=True)
    cal.add_argument('--geometry', type=Path, default=Path('data/hardware/force-plate-geometry.json'))
    cal.add_argument('--mass-g', type=float, required=True)
    cal.add_argument('--seconds', type=float, default=4)
    cal.add_argument('--maximum-channel-skew-s', type=float, default=.005)
    cal.add_argument('--desk', type=Path)
    cal.add_argument('--out', type=Path, required=True)
    reg = sub.add_parser('register', help='Fit measured board-to-robot fiducials')
    reg.add_argument('points', type=Path, help='JSON with points and desk_fingerprint')
    reg.add_argument('--out', type=Path, required=True)
    d = sub.add_parser('demo', help='Synthetic end-to-end test; no hardware')
    d.add_argument('--out', type=Path, required=True)
    write = sub.add_parser('write', help='Write with synchronized force logging')
    write.add_argument('text')
    write.add_argument('--port', required=True)
    write.add_argument('--calibration', type=Path, required=True)
    write.add_argument('--registration', type=Path)
    write.add_argument('--speed', type=float, default=1.5)
    write.add_argument('--out', type=Path, required=True)
    # Forward these command-specific arguments to their existing entry points.
    for name in ('record', 'analyze', 'live'):
        sub.add_parser(name, add_help=False)
    args, extra = parser.parse_known_args(argv)
    if args.command in ('record', 'analyze', 'live'):
        modules = {'record':'record_force_plate', 'analyze':'analyze_force_plate', 'live':'force_plate_live'}
        import importlib
        return importlib.import_module('scripts.'+modules[args.command]).main(extra)
    if extra:
        parser.error('unrecognized arguments: '+' '.join(extra))
    if args.command == 'init':
        write_json(args.out, {'schema': 1, 'geometry': asdict(PlateGeometry()),
                              'supports_measured': False, 'cell_ids': [2,4,3,1],
                              'plate': {'material': 'aluminium', 'thickness_mm': 2.0},
                              'load_cell': {'model': 'SC616C-1kg', 'capacity_g_each': 1000,
                                            'product_url': 'https://akizukidenshi.com/catalog/g/g117084/'}})
        print(args.out)
    elif args.command == 'fit':
        write_json(args.out, fit_calibration(json.loads(args.manifest.read_text())))
    elif args.command == 'calibrate':
        if not math.isfinite(args.mass_g) or args.mass_g <= 0 or not math.isfinite(args.seconds) or args.seconds < 2:
            parser.error('Positive finite mass and at least 2 seconds per placement required')
        calibrate(args)
    elif args.command == 'register':
        payload = json.loads(args.points.read_text())
        write_json(args.out, fit_registration(payload['points'], payload['desk_fingerprint']))
    elif args.command == 'demo':
        demo(args)
    elif args.command == 'write':
        if not 1 <= len(args.text) <= 4 or not math.isfinite(args.speed) or args.speed <= 0:
            parser.error('Use 1-4 characters and a positive speed')
        write_with_plate(args)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
