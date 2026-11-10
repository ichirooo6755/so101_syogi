#!/usr/bin/env python3
"""Local, dead-man controlled SO-101 leader console. No follower commands."""
import json
import math
import os
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Verified against the connected leader's six saved calibration records.
PORT = '/dev/cu.usbmodem5B7B0136431'
JOINTS = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'gripper')
TOKEN = secrets.token_urlsafe(32)
PAGE = Path(__file__).with_name('leader_pad') / 'index.html'
TIMEOUT = 0.30


def check_motor_status(port):
    """Read Feetech status packets before loading LeRobot or enabling torque."""
    import serial
    with serial.Serial(port, 1_000_000, timeout=0.3) as device:
        for motor_id in range(1, 7):
            body = [motor_id, 4, 2, 62, 1]
            device.reset_input_buffer()
            device.write(bytes([255, 255, *body, (~sum(body)) & 255]))
            packet = device.read(7)
            if (len(packet) != 7 or packet[:4] != bytes([255, 255, motor_id, 3])
                    or sum(packet[2:]) & 255 != 255):
                raise ValueError(f'モーター ID{motor_id} の応答を確認できません')
            error = packet[4]
            if error:
                detail = '電圧エラー' if error & 1 else f'エラー 0x{error:02x}'
                raise ValueError(f'モーター ID{motor_id}: {detail}（測定 {packet[5] / 10:.1f} V）。電源とサーボ仕様を確認してください')


def next_goals(present, inputs, limits, dt):
    """Small bounded step from measured position; units are degrees and grip %."""
    result = {}
    for name, value in zip(JOINTS, inputs):
        value = float(value)
        if not math.isfinite(value) or abs(value) > 1:
            raise ValueError('不正な入力')
        if abs(value) < 0.18:
            continue
        lo, hi = limits[name]
        now = float(present[name])
        if not math.isfinite(now) or not lo <= now <= hi:
            raise ValueError(f'{name} が安全範囲外です')
        speed = 5 if name != 'gripper' else 4
        result[name] = max(lo, min(hi, now + value * speed * min(dt, 0.05)))
    return result


class Controller:
    def __init__(self):
        self.lock = threading.Lock()
        self.command = None
        self.input = None
        self.neutral = False
        self.last = 0.0
        self.state = '未接続'
        self.armed = False
        self.worker = threading.Thread(target=self.run, daemon=True)
        self.worker.start()

    def post(self, body):
        kind = body.get('kind')
        with self.lock:
            if kind in ('connect', 'arm', 'stop', 'disconnect'):
                if self.command is not None:
                    raise ValueError('処理中です')
                self.command = kind
                if kind in ('stop', 'disconnect'):
                    self.input = None
                    self.armed = False
            elif kind == 'input':
                values = body.get('axes')
                if not isinstance(values, list) or len(values) != 5:
                    raise ValueError('入力形式エラー')
                values = [float(x) for x in values]
                if any(not math.isfinite(x) or abs(x) > 1 for x in values):
                    raise ValueError('入力範囲エラー')
                self.input = values if body.get('deadman') is True else None
                self.neutral = body.get('deadman') is False and all(abs(x) < 0.18 for x in values)
                self.last = time.monotonic()
            else:
                raise ValueError('不明な操作')

    def run(self):
        leader = None
        limits = {}
        holding = False
        last_cycle = time.monotonic()
        while True:
            try:
                with self.lock:
                    cmd, self.command = self.command, None
                    inputs, stamp, armed = self.input, self.last, self.armed
                if cmd == 'connect' and leader is None:
                    self.state = '接続確認中…'
                    check_motor_status(PORT)
                    from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
                    leader = SO101Leader(SO101LeaderConfig(port=PORT, id='syodo_leader'))
                    if not leader.calibration or any(n not in leader.calibration for n in JOINTS):
                        raise ValueError('Leader の較正ファイルがありません')
                    leader.bus.connect()
                    if not leader.is_calibrated:
                        raise ValueError('Leader の較正がモーターと一致しません')
                    for n in JOINTS:
                        if leader.bus.read('Operating_Mode', n, normalize=False) != 0:
                            raise ValueError(f'{n} が位置制御モードではありません')
                        c = leader.calibration[n]
                        span = (c.range_max - c.range_min) * 360 / 4095 / 2
                        limits[n] = (5, 95) if n == 'gripper' else (-span + 5, span - 5)
                        if limits[n][0] >= limits[n][1]:
                            raise ValueError(f'{n} の較正範囲が狭すぎます')
                    leader.bus.sync_read('Present_Position', list(JOINTS), num_retry=2)
                    self.state = '接続済み・操作待ち'
                elif cmd == 'arm' and leader is not None:
                    if inputs is not None or not self.neutral or time.monotonic() - stamp > TIMEOUT:
                        raise ValueError('RB を離し、スティックを中央に戻してから操作開始してください')
                    pos = leader.bus.sync_read('Present_Position', list(JOINTS), num_retry=2)
                    for n in JOINTS:
                        if not math.isfinite(float(pos[n])) or not limits[n][0] <= pos[n] <= limits[n][1]:
                            raise ValueError(f'{n} が較正範囲の端にあります。安全な範囲に置いてください')
                    leader.bus.sync_write('Goal_Position', pos)
                    leader.bus.enable_torque(list(JOINTS))
                    holding = True
                    with self.lock:
                        self.armed = True
                    self.state = '操作可能・RB を押して動かす'
                elif cmd in ('stop', 'disconnect') and leader is not None:
                    if holding:
                        pos = leader.bus.sync_read('Present_Position', list(JOINTS), num_retry=2)
                        leader.bus.sync_write('Goal_Position', pos)
                    self.state = '停止・現在位置を保持中' if holding else '停止'
                    if cmd == 'disconnect':
                        leader.bus.disconnect(disable_torque=False)
                        leader = None
                        holding = False
                        self.state = '切断・トルクは保持設定のまま'
                now = time.monotonic()
                if leader is not None and armed and cmd is None:
                    if now - stamp > TIMEOUT:
                        with self.lock:
                            self.armed = False
                            self.input = None
                        if holding:
                            pos = leader.bus.sync_read('Present_Position', list(JOINTS), num_retry=2)
                            leader.bus.sync_write('Goal_Position', pos)
                        self.state = '通信停止・現在位置を保持中。再度操作開始してください'
                    elif inputs is not None:
                        pos = leader.bus.sync_read('Present_Position', list(JOINTS), num_retry=2)
                        goals = next_goals(pos, inputs, limits, now - last_cycle)
                        if goals:
                            leader.bus.sync_write('Goal_Position', goals)
                    elif holding:
                        # Releasing RB cancels the last small in-flight command.
                        pos = leader.bus.sync_read('Present_Position', list(JOINTS), num_retry=2)
                        leader.bus.sync_write('Goal_Position', pos)
                last_cycle = now
            except Exception as exc:
                with self.lock:
                    self.armed = False
                    self.input = None
                self.state = 'エラー・操作停止: ' + str(exc)
                if leader is not None:
                    try:
                        if holding:
                            pos = leader.bus.sync_read('Present_Position', list(JOINTS), num_retry=2)
                            leader.bus.sync_write('Goal_Position', pos)
                        if leader.bus.is_connected:
                            leader.bus.disconnect(disable_torque=False)
                    except Exception:
                        pass
                    leader = None
                    holding = False
            time.sleep(0.05)


control = Controller()


class Handler(BaseHTTPRequestHandler):
    def valid(self):
        return (self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}' and
                self.headers.get('Origin') == f'http://127.0.0.1:{self.server.server_port}' and
                secrets.compare_digest(self.headers.get('X-Token', ''), TOKEN))

    def do_GET(self):
        if self.path != '/' + TOKEN or self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
            self.send_error(404); return
        data = PAGE.read_bytes().replace(b'__TOKEN__', TOKEN.encode())
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != '/api' or not self.valid():
            self.send_error(403); return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 2048:
                raise ValueError('サイズエラー')
            body = json.loads(self.rfile.read(size))
            if body.get('kind') != 'status':
                control.post(body)
            data = json.dumps({'state': control.state, 'armed': control.armed,
                               'usb': os.path.exists(PORT)}, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            self.send_error(400)

    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    url = f'http://127.0.0.1:{server.server_port}/{TOKEN}'
    print('Leader 操作画面:', url, flush=True)
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        with control.lock:
            control.armed = False
            control.input = None
            control.command = 'disconnect'
        time.sleep(0.5)
        server.server_close()


if __name__ == '__main__':
    main()
