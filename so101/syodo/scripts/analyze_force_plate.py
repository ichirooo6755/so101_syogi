#!/usr/bin/env python3
"""Analyze four loads and align calibrated contact data to robot writing logs."""
from __future__ import annotations
import argparse
from bisect import bisect_right
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from so101_calligraphy.force_plate import estimate_sample
from so101_calligraphy.force_plate_calibration import load_calibration


def read_samples(path):
    previous = boot = sequence = None
    for number, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        sample = json.loads(line)
        if 'raw_counts' not in sample:
            continue
        times = tuple(float(t) for t in sample['channel_time_s'])
        if len(times) != 4 or any(not math.isfinite(t) or t < 0 for t in times):
            raise ValueError(f'Line {number}: invalid acquisition timestamp')
        if previous is not None and any(t <= p for t, p in zip(times, previous)):
            raise ValueError(f'Line {number}: repeated or backwards acquisition timestamp')
        if previous is not None and boot != sample.get('boot_id'):
            raise ValueError('Pico rebooted during recording')
        seq = sample.get('sequence')
        if sequence is not None and seq is not None and seq <= sequence:
            raise ValueError('Repeated or backwards sequence')
        previous, boot, sequence = times, sample.get('boot_id'), seq
        yield sample


def truth(value):
    return value in (True, 'True', 'true', '1')


def analyze(recording, calibration_path, out, *, robot_log=None, registration=None,
            maximum_alignment_s=.03, plots=True):
    payload, calibration, geometry = load_calibration(calibration_path)
    recording_errors = [r.get('detail') for r in
                        (json.loads(line) for line in Path(recording).read_text().splitlines() if line.strip())
                        if r.get('event') == 'recording_error']
    robot = []
    if robot_log:
        with Path(robot_log).open(newline='') as stream:
            robot = [r for r in csv.DictReader(stream) if r.get('phase') == 'write']
        if not robot or any(not r.get('command_start_monotonic_s') or not r.get('host_monotonic_s') for r in robot):
            raise ValueError('Robot log needs command_start_monotonic_s and host_monotonic_s; old wall-clock logs cannot be aligned')
        starts = [float(r['command_start_monotonic_s']) for r in robot]
        ends = [float(r['host_monotonic_s']) for r in robot]
        if any(not math.isfinite(t) for t in starts + ends) or any(b <= a for a, b in zip(starts, starts[1:])) or any(b < a for a, b in zip(starts, ends)):
            raise ValueError('Invalid robot monotonic clock')
    transform = None
    if registration:
        import numpy as np
        reg = json.loads(Path(registration).read_text())
        if not robot_log:
            raise ValueError('Registration requires a robot log')
        meta = json.loads(Path(robot_log).with_name('write.json').read_text())
        if reg.get('validated') is not True or not reg.get('desk_fingerprint') or reg['desk_fingerprint'] != meta.get('desk_fingerprint'):
            raise ValueError('Registration does not match the writing desk')
        if payload.get('desk_fingerprint') != reg['desk_fingerprint']:
            raise ValueError('Plate calibration does not match the registered desk')
        transform = np.asarray(reg['board_to_robot_xy'], dtype=float)
        if transform.shape != (3, 2) or not np.isfinite(transform).all() or abs(np.linalg.det(transform[:2])) < 1e-10:
            raise ValueError('Invalid board registration transform')
    rows = []
    previous_host = None
    for sample in read_samples(recording):
        row = estimate_sample(calibration, sample, geometry)
        if robot and (not sample.get('force_plate_session') or
                      any(r.get('force_plate_session') != sample['force_plate_session'] for r in robot)):
            raise ValueError('Robot and Pico logs must belong to the same force-plate write session')
        host = sample.get('host_sample_monotonic_s')
        uncertainty = sample.get('clock_uncertainty_s')
        if host is not None:
            if not math.isfinite(host) or (previous_host is not None and host <= previous_host):
                raise ValueError('Host acquisition clock is not monotonic')
            previous_host = host
        row.update({'host_sample_monotonic_s': host, 'clock_uncertainty_s': uncertainty,
                    'robot_index': None, 'cell': None, 'pen_down': None, 'target_pressure': None,
                    'alignment_valid': False, 'contact_missing': None, 'unexpected_contact': None,
                    'target_force_error_n': None, 'command_centre_error_mm': None})
        # Missing metadata in old raw logs remains diagnostic-only.
        health = (sample.get('hx711_ready') == [True]*4 and sample['saturated'] is False
                  and all(-8388608 < r < 8388607 for r in sample['raw_counts'])
                  and row['channel_skew_s'] <= calibration.maximum_channel_skew_s)
        poll = sample.get('ready_poll_uncertainty_s')
        poll_ok = (isinstance(poll, list) and len(poll) == 4 and
                   all(math.isfinite(v) and 0 <= v <= maximum_alignment_s for v in poll))
        clock_ok = (uncertainty is not None and math.isfinite(uncertainty) and
                    0 <= uncertainty <= maximum_alignment_s)
        if robot and host is not None and clock_ok and poll_ok and health:
            index = bisect_right(starts, host) - 1
            if index >= 0 and starts[index] <= host <= ends[index]:
                r = robot[index]
                # Do not classify contact around a pen-up/down transition whose
                # uncertainty interval straddles either state.
                margin = uncertainty + max(poll) + row['channel_skew_s']/2
                left = bisect_right(starts, host - margin) - 1
                right = bisect_right(starts, host + margin) - 1
                states = {truth(v['pen_down']) for v in robot[max(left, 0):right+1]}
                aligned = left >= 0 and host + margin <= ends[-1] and len(states) == 1
                row.update({'robot_index': r['index'], 'cell': r.get('cell'),
                            'pen_down': truth(r['pen_down']), 'target_pressure': r.get('target_pressure'),
                            'alignment_valid': aligned})
                if aligned:
                    row['contact_missing'] = row['pen_down'] and row['normal_force_n'] < calibration.minimum_force_n
                    row['unexpected_contact'] = not row['pen_down'] and row['normal_force_n'] >= calibration.minimum_force_n
                    if r.get('target_force_n') and row['valid']:
                        row['target_force_error_n'] = row['normal_force_n'] - float(r['target_force_n'])
                    if transform is not None and row['valid'] and row.get('board_x_mm') is not None and r.get('expected_tip_x_m') and r.get('expected_tip_y_m'):
                        point = np.array([row['board_x_mm'], row['board_y_mm'], 1]) @ transform
                        row['command_centre_error_mm'] = float(np.linalg.norm(point - [float(r['expected_tip_x_m']), float(r['expected_tip_y_m'])]) * 1000)
        forces = row.pop('channel_force_n')
        row.update({f'force_{i}_n': f for i, f in enumerate(forces)})
        rows.append(row)
    if not rows:
        raise ValueError('Recording contains no samples')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    def save_csv(path, values):
        if values:
            with path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(values[0]))
                writer.writeheader()
                writer.writerows(values)
    save_csv(out/'force-plate.csv', rows)
    valid = [r for r in rows if r['valid']]
    aligned = [r for r in rows if r['alignment_valid']]
    strokes = []
    stroke_indices = {}
    current = None
    for r in robot:
        if truth(r['pen_down']):
            if current is None or current['cell'] != r.get('cell'):
                current = {'stroke': len(strokes), 'cell': r.get('cell'), 'indices': []}
                strokes.append(current)
            current['indices'].append(str(r['index']))
            stroke_indices[str(r['index'])] = current['stroke']
        else:
            current = None
    stroke_rows = []
    for s in strokes:
        points = [r for r in aligned if stroke_indices.get(str(r['robot_index'])) == s['stroke']]
        loads = [r['normal_force_n'] for r in points if r['valid']]
        mean = statistics.mean(loads) if loads else None
        std = statistics.pstdev(loads) if loads else None
        stroke_rows.append({'stroke': s['stroke'], 'cell': s['cell'], 'samples': len(points),
                            'valid_contact_samples': len(loads), 'mean_force_n': mean,
                            'std_force_n': std, 'cv': std/mean if mean and mean > 0 else None,
                            'peak_force_n': max(loads) if loads else None,
                            'missing_contact_samples': sum(bool(r['contact_missing']) for r in points)})
    save_csv(out/'strokes.csv', stroke_rows)
    summary = {
        'samples': len(rows), 'valid_samples': len(valid), 'aligned_samples': len(aligned),
        'recording_errors': recording_errors,
        'invalid_reasons': dict(Counter(r['invalid_reason'] for r in rows if not r['valid'])),
        'mean_force_n': statistics.mean(r['normal_force_n'] for r in valid) if valid else None,
        'peak_force_n': max((r['normal_force_n'] for r in valid), default=None),
        'missing_contact_samples': sum(bool(r['contact_missing']) for r in aligned),
        'unexpected_contact_samples': sum(bool(r['unexpected_contact']) for r in aligned),
        'physical_writing_verified': False, 'training_eligible': False,
        'source': payload.get('source', 'unspecified'),
        'reason': 'Diagnostic dataset; dynamic delay, independent ink/camera validation and held-out writing evaluation required',
        'recording_sha256': hashlib.sha256(Path(recording).read_bytes()).hexdigest(),
        'calibration_sha256': hashlib.sha256(Path(calibration_path).read_bytes()).hexdigest(),
        'robot_log_sha256': hashlib.sha256(Path(robot_log).read_bytes()).hexdigest() if robot_log else None,
        'registration_sha256': hashlib.sha256(Path(registration).read_bytes()).hexdigest() if registration else None,
        'clock_note': 'DOUT-ready plus USB round-trip clock fit; HX711 filter delay is not removed',
        'advice': ['Use stroke force variation and contact gaps to select depth/speed experiments.',
                   'target_pressure remains the existing model unit; it is not a Newton target.',
                   'The centre is the resultant of all contacts, not a pressure map or measured brush tip.'],
    }
    if plots:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(11, 6), layout='constrained')
        t0 = rows[0]['time_s']
        force_series = [None if r['invalid_reason'] in
                        ('channel_not_ready', 'adc_saturation', 'asynchronous_channels')
                        else r['normal_force_n'] for r in rows]
        axes[0].plot([r['time_s']-t0 for r in rows], force_series, lw=1)
        axes[0].axhline(calibration.minimum_force_n, color='orange', ls='--', label='Contact threshold')
        axes[0].set(xlabel='Device time (s)', ylabel='Normal force (N)', title='Four-channel resultant force')
        axes[0].legend()
        if geometry:
            points = [r for r in valid if r.get('board_x_mm') is not None]
            if points:
                scatter = axes[1].scatter([r['board_x_mm'] for r in points], [r['board_y_mm'] for r in points],
                                          c=[r['normal_force_n'] for r in points], s=9, cmap='viridis')
                fig.colorbar(scatter, ax=axes[1], label='Force (N)')
            axes[1].scatter(*zip(*geometry.supports_mm), marker='s', color='gray')
            axes[1].set(xlim=(0, geometry.width_mm), ylim=(geometry.height_mm, 0), aspect='equal',
                        xlabel='Right from board left (mm)', ylabel='Down from board top (mm)', title='200 × 300 mm load centre')
        fig.suptitle('SYNTHETIC DEMO' if summary['source'] == 'synthetic' else 'Force plate measurement')
        fig.savefig(out/'force-plate.png', dpi=160)
        plt.close(fig)
    (out/'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('recording', type=Path)
    p.add_argument('--calibration', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--robot-log', type=Path)
    p.add_argument('--registration', type=Path)
    p.add_argument('--no-plots', action='store_true')
    args = p.parse_args(argv)
    print(json.dumps(analyze(args.recording, args.calibration, args.out, robot_log=args.robot_log,
                             registration=args.registration, plots=not args.no_plots), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
