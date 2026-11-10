"""Fit four signed sensitivities from masses placed on an assembled plate."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from .force_plate import CELL_IDS, ForcePlateCalibration, PlateGeometry, estimate_sample

GRAVITY = 9.80665


def load_calibration(path):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if payload.get('schema') != 1:
        raise ValueError('Unsupported force plate calibration schema')
    calibration = ForcePlateCalibration(**payload['calibration'])
    geometry = PlateGeometry(**payload['geometry']) if 'geometry' in payload else None
    if geometry and not np.allclose(
        [calibration.support_x_m, calibration.support_y_m],
        [(geometry.bottom_mm-geometry.top_mm)/1000, (geometry.right_mm-geometry.left_mm)/1000],
        rtol=0, atol=1e-9,
    ):
        raise ValueError('Calibration and board support spacing differ')
    return payload, calibration, geometry


def capture_mean(samples):
    if len(samples) < 16:
        raise ValueError('At least 16 complete frames per static placement are required')
    raw = []
    last = None
    boot = samples[0].get('boot_id')
    for sample in samples:
        if sample.get('hx711_ready') != [True]*4 or tuple(sample.get('cell_ids', ())) != CELL_IDS:
            raise ValueError('All four identified HX711 channels must be ready')
        values = np.asarray(sample['raw_counts'], dtype=float)
        if values.shape != (4,) or not np.isfinite(values).all() or np.any(np.abs(values) >= 8388607) or sample['saturated'] is not False:
            raise ValueError('Saturated or invalid calibration sample')
        times = np.asarray(sample['channel_time_s'], dtype=float)
        if times.shape != (4,) or not np.isfinite(times).all() or np.any(times < 0):
            raise ValueError('Invalid calibration timestamp')
        if last is not None and np.any(times <= last):
            raise ValueError('Repeated or backwards calibration timestamp')
        if sample.get('boot_id') != boot:
            raise ValueError('Pico rebooted during calibration capture')
        last = times
        raw.append(values)
    raw = np.asarray(raw)
    return raw.mean(axis=0), raw.std(axis=0, ddof=1)


def fit_calibration(manifest):
    """Force + two moments identify each gain without assuming bilinear reactions."""
    geometry = PlateGeometry(**manifest['geometry'])
    zero, noise_counts = capture_mean(manifest['tare_samples'])
    supports = np.array(geometry.supports_mm, dtype=float)
    # Dimensionless moment rows give force and moments comparable numerical weight.
    moment = np.stack([np.ones(4), supports[:, 0]/geometry.width_mm,
                       supports[:, 1]/geometry.height_mm])
    fit = [p for p in manifest['placements'] if p['role'] == 'fit']
    validate = [p for p in manifest['placements'] if p['role'] == 'validate']
    if len(fit) + len(validate) != len(manifest['placements']):
        raise ValueError('Placement role must be fit or validate')
    if len(fit) < 4 or len(validate) < 3:
        raise ValueError('Need >=4 fit placements and >=3 separate validation placements')
    matrices, targets = [], []
    captures = []
    for p in fit + validate:
        mass, x, y = float(p['mass_g']), float(p['x_mm']), float(p['y_mm'])
        if not all(math.isfinite(v) for v in (mass, x, y)) or mass <= 0:
            raise ValueError('Finite known positive mass and position required')
        if not geometry.left_mm <= x <= geometry.right_mm or not geometry.top_mm <= y <= geometry.bottom_mm:
            raise ValueError('Calibration load must lie within the support rectangle')
        mean, std = capture_mean(p['samples'])
        force = mass / 1000 * GRAVITY
        captures.append((p, mean, std, force))
        if p['role'] == 'fit':
            matrices.append(moment * (mean - zero))
            targets.append(force * np.array([1, x/geometry.width_mm, y/geometry.height_mm]))
    matrix, target = np.vstack(matrices), np.concatenate(targets)
    gains, _, rank, singular = np.linalg.lstsq(matrix, target, rcond=None)
    condition = float(singular[0] / singular[-1]) if singular[-1] else math.inf
    if rank != 4 or condition > 1e4 or not np.isfinite(gains).all() or np.any(gains == 0):
        raise ValueError('Unidentifiable channel gains; spread weights over all four corners')
    noise_n = float(np.linalg.norm(noise_counts * gains))
    threshold = max(float(manifest.get('minimum_force_n', .02)), 6 * noise_n)
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError('Invalid contact threshold')
    # Only certify loads actually exercised. Five percent allows measurement error.
    maximum = min(max(item[3] for item in captures if item[0]['role'] == 'fit'),
                  max(item[3] for item in captures if item[0]['role'] == 'validate')) * 1.05
    cal = ForcePlateCalibration((geometry.bottom_mm-geometry.top_mm)/1000,
                               (geometry.right_mm-geometry.left_mm)/1000,
                               tuple(zero), tuple(gains), threshold, maximum,
                               float(manifest.get('maximum_channel_skew_s', .005)))
    checks = []
    force_limit = float(manifest.get('force_error_limit_n', .03))
    position_limit = float(manifest.get('position_error_limit_mm', 5.0))
    if not math.isfinite(force_limit + position_limit) or min(force_limit, position_limit) <= 0:
        raise ValueError('Positive finite validation limits required')
    for p, mean, std, force in captures:
        # Static means use equilibrium; timing is checked separately during dynamic recording.
        row = geometry.locate(cal.estimate(mean, [1]*4))
        error_mm = (math.hypot(row['board_x_mm'] - p['x_mm'], row['board_y_mm'] - p['y_mm'])
                    if row['valid'] else None)
        stability_n = float(np.linalg.norm(std * gains))
        checks.append({'role': p['role'], 'x_mm': p['x_mm'], 'y_mm': p['y_mm'],
                       'force_error_n': row['normal_force_n'] - force,
                       'position_error_mm': error_mm, 'noise_n': stability_n,
                       'passed': row['valid'] and abs(row['normal_force_n'] - force) <= force_limit
                       and error_mm <= position_limit and 6*stability_n <= force_limit})
    if not all(c['passed'] for c in checks):
        raise ValueError('Static calibration validation failed: ' + json.dumps(checks))
    drift_n = None
    if 'final_tare_samples' in manifest:
        final_zero, _ = capture_mean(manifest['final_tare_samples'])
        drift_n = float(np.linalg.norm((final_zero-zero)*gains))
        if drift_n > min(threshold, force_limit):
            raise ValueError('Zero drift after calibration exceeds the contact/error threshold')
    return {'schema': 1, 'geometry': asdict(geometry), 'calibration': asdict(cal),
            'cell_ids': CELL_IDS, 'source': manifest.get('source', 'measured'),
            'static_validation': {'passed': True, 'checks': checks, 'noise_n': noise_n,
                                  'condition_number': condition, 'rank': int(rank), 'zero_drift_n': drift_n},
            'desk_fingerprint': manifest.get('desk_fingerprint'),
            'manifest_sha256': hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
            'training_eligible': False,
            'limitations': ['static validation only', 'dynamic timing and brush/camera validation required']}


def fit_registration(points, desk_fingerprint, *, max_error_mm=2.0):
    """Fit board millimetres -> robot world metres, with held-out fiducials."""
    fit = [p for p in points if p['role'] == 'fit']
    test = [p for p in points if p['role'] == 'validate']
    if len(fit) < 3 or len(test) < 1 or not desk_fingerprint:
        raise ValueError('Three fit points, a held-out point and desk fingerprint required')
    a = np.array([[*p['board_xy_mm'], 1] for p in fit], dtype=float)
    b = np.array([p['robot_xy_m'] for p in fit], dtype=float)
    if a.shape != (len(fit), 3) or b.shape != (len(fit), 2) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Invalid registration points')
    transform, _, rank, _ = np.linalg.lstsq(a, b, rcond=None)
    if rank != 3 or abs(np.linalg.det(transform[:2])) < 1e-10:
        raise ValueError('Registration points must span a plane')
    errors = []
    for p in fit + test:
        xy, robot = np.asarray(p['board_xy_mm'], float), np.asarray(p['robot_xy_m'], float)
        if xy.shape != (2,) or robot.shape != (2,) or not np.isfinite(xy).all() or not np.isfinite(robot).all():
            raise ValueError('Invalid registration validation point')
        errors.append(float(np.linalg.norm(np.append(xy, 1) @ transform - robot) * 1000))
    if not math.isfinite(max_error_mm) or max_error_mm <= 0 or max(errors) > max_error_mm:
        raise ValueError('Board registration exceeds the position error limit')
    return {'schema': 1, 'board_to_robot_xy': transform.tolist(), 'desk_fingerprint': desk_fingerprint,
            'max_error_mm': max(errors), 'points': points, 'validated': True}
