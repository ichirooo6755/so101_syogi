"""Bounded USB CDC acquisition and Pico/host clock correspondence (POSIX)."""
from __future__ import annotations

import fcntl
import json
import math
import os
from pathlib import Path
import select
import termios
import threading
import time
import tty
import uuid


class PicoStream:
    def __init__(self, port):
        self.fd = os.open(str(port), os.O_RDWR | os.O_NONBLOCK | os.O_NOCTTY)
        self.buffer = b''
        self.original = None
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.original = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)
            termios.tcflush(self.fd, termios.TCIFLUSH)
        except BaseException:
            os.close(self.fd)
            raise

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        try:
            if self.original is not None:
                termios.tcsetattr(self.fd, termios.TCSANOW, self.original)
        finally:
            os.close(self.fd)

    def send(self, command):
        data = (command + '\n').encode('ascii')
        end = time.monotonic() + 1
        while data:
            if time.monotonic() >= end:
                raise TimeoutError('Pico command write timed out')
            if select.select([], [self.fd], [], .05)[1]:
                try:
                    data = data[os.write(self.fd, data):]
                except BlockingIOError:
                    pass

    def read(self, timeout=1.0):
        end = time.monotonic() + timeout
        while True:
            while b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                try:
                    row = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    continue
                if isinstance(row, dict):
                    row['host_receive_monotonic_s'] = time.monotonic()
                    row['host_receive_unix_s'] = time.time()
                    return row
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('No complete JSON frame from Pico')
            if select.select([self.fd], [], [], min(remaining, .1))[0]:
                try:
                    chunk = os.read(self.fd, 16384)
                except BlockingIOError:
                    continue
                if not chunk:
                    raise OSError('Pico disconnected')
                self.buffer += chunk
                if len(self.buffer) > 131072:
                    self.buffer = b''
                    raise ValueError('Oversized Pico frame')


def sync_clock(stream, attempts=5):
    """Midpoint estimate with RTT/2 uncertainty; no arrival-time substitution."""
    measurements = []
    boot_id = None
    for index in range(attempts):
        token = str(time.monotonic_ns()) + str(index)
        sent = time.monotonic()
        stream.send('sync ' + token)
        end = sent + 2
        while time.monotonic() < end:
            try:
                row = stream.read(min(.25, max(.001, end - time.monotonic())))
            except TimeoutError:
                continue
            if row.get('event') != 'sync' or row.get('token') != token:
                continue
            received = row['host_receive_monotonic_s']
            device = float(row['device_time_s'])
            if not math.isfinite(device) or device < 0 or not row.get('boot_id'):
                raise ValueError('Invalid Pico clock response')
            if boot_id is not None and boot_id != row['boot_id']:
                raise ValueError('Pico rebooted during synchronization')
            boot_id = row['boot_id']
            measurements.append({'device_time_s': device, 'host_sent_s': sent,
                                 'host_received_s': received,
                                 'offset_s': (sent + received) / 2 - device,
                                 'uncertainty_s': (received - sent) / 2})
            break
    if not measurements:
        raise TimeoutError('Pico firmware does not answer sync; install current main.py')
    best = min(measurements, key=lambda m: m['uncertainty_s'])
    return {'method': 'usb_round_trip_midpoint', 'boot_id': boot_id, **best,
            'attempts': measurements}


def timestamp_sample(row, sync):
    row = dict(row)
    if row.get('boot_id') != sync['boot_id']:
        raise ValueError('Pico rebooted; a new recording and clock sync are required')
    device_time = sum(row['channel_time_s']) / 4
    age = abs(device_time - sync['device_time_s'])
    # Drift is not measured. Conservative budget, recorded explicitly, resync every 10s.
    row['host_sample_monotonic_s'] = device_time + sync['offset_s']
    row['clock_uncertainty_s'] = sync['uncertainty_s'] + age * .001
    row['clock_drift_budget_ppm'] = 1000
    row['clock_sync_device_time_s'] = sync['device_time_s']
    return row


class ForceRecorder:
    """One port owner. Preserves events, raw counts, timestamps, and failures."""
    def __init__(self, port, out, *, synchronize=True, session_id=None):
        self.port, self.out = str(port), Path(out)
        self.synchronize = synchronize
        self.session_id = session_id or uuid.uuid4().hex
        self.stop_event = threading.Event()
        self.ready = threading.Event()
        self.error = None
        self.last_sample = None
        self.thread = None

    def start(self):
        self.out.parent.mkdir(parents=True, exist_ok=True)
        # Reserve before spawning so an existing measurement is never overwritten.
        self.output = self.out.open('x', encoding='utf-8')
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return self

    def _run(self):
        def save(row):
            row['force_plate_session'] = self.session_id
            self.output.write(json.dumps(row, allow_nan=False) + '\n')
            self.output.flush()
        try:
            with PicoStream(self.port) as stream:
                sync = sync_clock(stream) if self.synchronize else None
                save({'event': 'clock_sync', 'sync': sync})
                next_sync = time.monotonic() + 10
                last_seq = None
                last_times = None
                while not self.stop_event.is_set():
                    if sync and time.monotonic() >= next_sync:
                        new_sync = sync_clock(stream, attempts=1)
                        if new_sync['boot_id'] != sync['boot_id']:
                            raise ValueError('Pico rebooted during recording')
                        sync = new_sync
                        save({'event': 'clock_sync', 'sync': sync})
                        next_sync = time.monotonic() + 10
                    try:
                        row = stream.read(.2)
                    except TimeoutError:
                        continue
                    if 'raw_counts' in row:
                        times = row['channel_time_s']
                        if len(times) != 4 or any(not math.isfinite(t) or t < 0 for t in times):
                            raise ValueError('Invalid device acquisition times')
                        if last_times is not None and any(t <= p for t, p in zip(times, last_times)):
                            raise ValueError('Repeated or backwards Pico timestamp')
                        last_times = times
                        if sync:
                            row = timestamp_sample(row, sync)
                        seq = row.get('sequence')
                        if seq is not None and last_seq is not None:
                            if seq <= last_seq:
                                raise ValueError('Repeated or backwards Pico sequence')
                            row['dropped_frames_before'] = max(0, seq - last_seq - 1)
                        last_seq = seq
                        self.last_sample = row
                        self.ready.set()
                    save(row)
        except BaseException as exc:
            self.error = exc
            save({'event': 'recording_error', 'detail': str(exc)})
        finally:
            self.ready.set()
            self.output.close()

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(4)
            if self.thread.is_alive():
                raise TimeoutError('Recorder did not stop')
        if self.error:
            raise RuntimeError(str(self.error)) from self.error
