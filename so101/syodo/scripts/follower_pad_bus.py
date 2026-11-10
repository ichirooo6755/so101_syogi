"""Small Feetech SDK adapter using LeRobot's saved follower calibration."""
import json
import time
from pathlib import Path
from types import SimpleNamespace

NAMES = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper')


class Follower:
    def __init__(self, port, calibration_path=None):
        import scservo_sdk as sdk
        self.sdk = sdk
        path = calibration_path or (Path.home() / '.cache/huggingface/lerobot/calibration/robots/so_follower/syodo_follower.json')
        self.calibration = {k: SimpleNamespace(**v) for k, v in json.loads(Path(path).read_text()).items()}
        if set(self.calibration) != set(NAMES) or any(self.calibration[n].id != i for i, n in enumerate(NAMES, 1)):
            raise ValueError('Follower の較正ファイルが不正です')
        self.port = sdk.PortHandler(port)
        self.ph = sdk.PacketHandler(0)
        self.bus = self
        self.is_connected = False

    def connect(self):
        if not self.port.openPort():
            raise ValueError('USB ポートを開けません')
        self.is_connected = True
        if not self.port.setBaudRate(1000000):
            raise ValueError('通信速度の設定に失敗しました')
        self.port.setPacketTimeoutMillis(100)

    def _read(self, motor_id, address, length, allow_gripper_overload=False):
        # The SDK flushes outgoing bytes, not unread status packets.
        self.port.ser.reset_input_buffer()
        fn = self.ph.read1ByteTxRx if length == 1 else self.ph.read2ByteTxRx
        value, comm, error = fn(self.port, motor_id, address)
        if comm != 0 or error:
            from follower_motor_errors import MotorReadError
            exc = MotorReadError(motor_id, comm, error)
            if not (allow_gripper_overload and exc.gripper_overload):
                raise exc
        return value

    def _write(self, motor_id, address, length, value, allow_gripper_overload=False):
        # Some adapters/servos do not reliably return WRITE status packets.
        # Send once, allow EEPROM to settle, then verify the register by READ.
        fn = self.ph.write1ByteTxOnly if length == 1 else self.ph.write2ByteTxOnly
        comm = fn(self.port, motor_id, address, int(value))
        if comm != 0:
            raise ValueError(f'ID{motor_id}: 書込み送信エラー (comm={comm})')
        time.sleep(0.12)
        if self._read(motor_id, address, length, allow_gripper_overload=allow_gripper_overload) != int(value):
            raise ValueError(f'ID{motor_id}: 書込み後の読戻しが一致しません (register={address})')

    @property
    def is_calibrated(self):
        return self.calibration_matches()

    def calibration_matches(self, allow_gripper_overload=False):
        for name in NAMES:
            c = self.calibration[name]
            def read(address):
                return self._read(c.id, address, 2, allow_gripper_overload=allow_gripper_overload and c.id == 6)
            lo, hi, raw = read(9), read(11), read(31)
            offset = -(raw & 2047) if raw & 2048 else raw
            if (lo, hi, offset) != (c.range_min, c.range_max, c.homing_offset):
                return False
        return True

    def read(self, key, name, normalize=False):
        assert key == 'Operating_Mode'
        return self._read(self.calibration[name].id, 33, 1)

    def sync_read(self, key, names, num_retry=0):
        assert key == 'Present_Position'
        out = {}
        for n in names:
            c = self.calibration[n]
            raw = self._read(c.id, 56, 2)
            if raw < c.range_min or raw > c.range_max:
                from follower_motor_errors import MotorRangeError
                raise MotorRangeError(n, raw, c.range_min, c.range_max)
            out[n] = ((raw - c.range_min) * 100 / (c.range_max - c.range_min) if n == 'gripper'
                      else (raw - (c.range_min + c.range_max) / 2) * 360 / 4095)
        return out

    def sync_write(self, key, values):
        assert key == 'Goal_Position'
        group = self.sdk.GroupSyncWrite(self.port, self.ph, 42, 2)
        for n, value in values.items():
            c = self.calibration[n]
            raw = (c.range_min + value * (c.range_max - c.range_min) / 100 if n == 'gripper'
                   else value * 4095 / 360 + (c.range_min + c.range_max) / 2)
            raw = round(raw)
            if not c.range_min <= raw <= c.range_max:
                raise ValueError(f'{n} の目標が較正範囲外です')
            group.addParam(c.id, [raw & 255, (raw >> 8) & 255])
        if values and group.txPacket() != 0:
            raise ValueError('目標位置を送信できません')

    def enable_torque(self, names):
        for n in names:
            self._write(self.calibration[n].id, 40, 1, 1)

    def disconnect(self, disable_torque=False):
        if disable_torque:
            raise ValueError('Follower のトルクを自動解除しません')
        self.port.closePort()
        self.is_connected = False
