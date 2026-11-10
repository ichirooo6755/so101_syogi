"""Four independent HX711s. VDD=3V3 OUT; see README before using 5 V.

USB JSONL in logical order near-left(2), far-left(4), far-right(3), near-right(1).
Commands: sync TOKEN, show, tare [logical_channel], cal CHANNEL NEWTONS.
Host calibration is authoritative. Board-mounted corner weights must be fitted
with static equilibrium, not assigned wholly to an individual support.
"""
import gc
import json
import math
import os
import select
import sys
import time
from machine import Pin, disable_irq, enable_irq
from hx711 import is_saturated, sample_dict, signed_24

PINS = ((3, 7), (5, 9), (4, 8), (2, 6))
CELL_IDS = (2, 4, 3, 1)
READY_TIMEOUT_S = 0.25
TARE_SAMPLES = 16
CAL_PATH = "cal.json"
# Physical RATE jumper setting. Change to 80 only after changing all four boards.
RATE_HZ = 10


class Clock:
    def __init__(self):
        self.last = time.ticks_us()
        self.elapsed_us = 0

    def seconds(self):
        now = time.ticks_us()
        self.elapsed_us += time.ticks_diff(now, self.last)
        self.last = now
        return self.elapsed_us / 1000000.0


class Hx711:
    def __init__(self, dout_gp, sck_gp):
        self.dout = Pin(dout_gp, Pin.IN, Pin.PULL_UP)
        self.sck = Pin(sck_gp, Pin.OUT, value=0)

    def ready(self):
        return self.dout.value() == 0

    def read(self):
        # Interrupts/GC cannot stretch a HIGH beyond 50 us (60 us powers down).
        # Shift/allocate only with clock LOW; explicit delays meet T2/T3/T4.
        value = 0
        gc.disable()
        try:
            for _ in range(24):
                irq = disable_irq()
                try:
                    self.sck.value(1)
                    time.sleep_us(1)
                    bit = self.dout.value()
                finally:
                    self.sck.value(0)
                    enable_irq(irq)
                value = (value << 1) | bit
                time.sleep_us(1)
            irq = disable_irq()
            try:
                self.sck.value(1)
                time.sleep_us(1)
            finally:
                self.sck.value(0)
                enable_irq(irq)
            time.sleep_us(1)  # 25 clocks: next conversion is A, gain 128
        finally:
            self.sck.value(0)
            gc.enable()
        return signed_24(value)


class Controller:
    def __init__(self, chips, clock, emit):
        self.chips, self.clock, self.emit = chips, clock, emit
        self.zero = [0.0] * 4
        self.gain = [0.0] * 4
        self.boot_id = ''.join('%02x' % b for b in os.urandom(8))
        self.sequence = 0
        self.pending_cal = None
        self.last_poll = clock.seconds()
        self.reset_frame()
        try:
            with open(CAL_PATH) as f:
                data = json.load(f)
            zero, gain = data['zero_counts'], data['newtons_per_count']
            if len(zero) == len(gain) == 4 and all(math.isfinite(v) for v in zero + gain):
                self.zero, self.gain = zero, gain
        except (OSError, ValueError, KeyError, TypeError):
            pass

    def reset_frame(self):
        self.raw, self.times, self.ready = [0] * 4, [0.0] * 4, [False] * 4
        self.uncertainty = [0.0] * 4
        self.frame_start = self.clock.seconds()

    def save(self):
        # Rename after close prevents a partial JSON calibration on interruption.
        with open(CAL_PATH + '.tmp', 'w') as f:
            json.dump({'zero_counts': self.zero, 'newtons_per_count': self.gain}, f)
        os.rename(CAL_PATH + '.tmp', CAL_PATH)

    def command(self, line):
        parts = line.strip().split()
        if not parts:
            return
        cmd = parts[0]
        try:
            if cmd == 'sync' and len(parts) == 2:
                self.emit({'event': 'sync', 'token': parts[1], 'device_time_s': self.clock.seconds(),
                           'boot_id': self.boot_id})
            elif cmd == 'show' and len(parts) == 1:
                self.emit({'event': 'show', 'zero_counts': self.zero, 'newtons_per_count': self.gain,
                           'boot_id': self.boot_id, 'cell_ids': CELL_IDS, 'rate_hz': RATE_HZ})
            elif cmd in ('tare', 'cal'):
                if self.pending_cal:
                    raise ValueError('calibration_busy')
                if cmd == 'tare' and len(parts) in (1, 2):
                    channels = list(range(4)) if len(parts) == 1 else [int(parts[1])]
                    force = None
                elif cmd == 'cal' and len(parts) == 3:
                    channels, force = [int(parts[1])], float(parts[2])
                    if not math.isfinite(force) or force <= 0:
                        raise ValueError('known_force_must_be_positive')
                else:
                    raise ValueError('invalid_arguments')
                if any(ch < 0 or ch > 3 for ch in channels):
                    raise ValueError('invalid_channel')
                self.pending_cal = [cmd, channels, force, [0.0] * 4, 0, self.clock.seconds()]
                self.reset_frame()
            else:
                raise ValueError('unknown_command')
        except (ValueError, IndexError, OSError) as exc:
            self.emit({'event': cmd, 'error': str(exc)})

    def calibration_sample(self, saturated):
        if self.pending_cal is None:
            return
        cmd, channels, force, sums, count, start = self.pending_cal
        if self.clock.seconds() - start > 10:
            self.pending_cal = None
            self.emit({'event': cmd, 'error': 'calibration_timeout'})
            return
        if not all(self.ready[ch] for ch in channels) or saturated:
            return
        for ch in channels:
            sums[ch] += self.raw[ch]
        count += 1
        self.pending_cal[4] = count
        if count < TARE_SAMPLES:
            return
        self.pending_cal = None
        zero, gain = self.zero[:], self.gain[:]
        for ch in channels:
            mean = sums[ch] / count
            if cmd == 'tare':
                zero[ch] = mean
            else:
                delta = mean - zero[ch]
                if abs(delta) < 1:
                    self.emit({'event': cmd, 'error': 'zero_delta'})
                    return
                gain[ch] = force / delta
        self.zero, self.gain = zero, gain
        try:
            self.save()
            self.emit({'event': cmd, 'zero_counts': zero, 'newtons_per_count': gain})
        except OSError as exc:
            self.emit({'event': cmd, 'error': str(exc)})

    def step(self):
        now = self.clock.seconds()
        gap = now - self.last_poll
        self.last_poll = now
        for ch, chip in enumerate(self.chips):
            if not self.ready[ch] and chip.ready():
                self.times[ch] = self.clock.seconds()  # observed DOUT-ready, not USB arrival
                self.uncertainty[ch] = gap
                self.raw[ch] = chip.read()
                self.ready[ch] = True
        now = self.clock.seconds()
        if not all(self.ready) and now - self.frame_start < READY_TIMEOUT_S:
            return
        for ch in range(4):
            if not self.ready[ch]:
                self.times[ch] = now
        saturated = any(is_saturated(v) for v, ready in zip(self.raw, self.ready) if ready)
        self.calibration_sample(saturated)
        self.emit(sample_dict(self.raw, self.times, saturated, {
            'schema': 2, 'sequence': self.sequence, 'boot_id': self.boot_id,
            'hx711_ready': self.ready, 'cell_ids': CELL_IDS,
            'force_n': [(v-z)*g if g and ready else None
                        for v, z, g, ready in zip(self.raw, self.zero, self.gain, self.ready)],
            'device_emit_time_s': self.clock.seconds(), 'rate_hz': RATE_HZ,
            'ready_poll_uncertainty_s': self.uncertainty,
        }))
        self.sequence += 1
        self.reset_frame()


def main():
    def emit(row):
        sys.stdout.write(json.dumps(row) + '\n')
    controller = Controller([Hx711(d, c) for d, c in PINS], Clock(), emit)
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)
    line = ''
    while True:
        # Never readline() a partial command and stall acquisition.
        while poll.poll(0):
            char = sys.stdin.read(1)
            if char in ('\n', '\r'):
                controller.command(line)
                line = ''
            elif char:
                line = (line + char)[-128:]
            else:
                break
        controller.step()
        time.sleep_us(100)


if __name__ == '__main__':
    main()
