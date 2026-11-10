"""Descriptions for Feetech status flags, without clearing servo protection."""

def describe_status(status):
    flags = ((1, '電圧'), (2, '角度'), (4, '温度'), (8, '電流'),
             (32, '過負荷'))
    names = [name for bit, name in flags if status & bit]
    unknown = status & ~47
    if unknown:
        names.append(f'不明なフラグ 0x{unknown:02x}')
    return '・'.join(names) or 'エラーなし'


class MotorReadError(ValueError):
    def __init__(self, motor_id, comm, status):
        self.motor_id, self.comm, self.status = motor_id, comm, status
        detail = describe_status(status) if status else '通信エラー'
        super().__init__(f'ID{motor_id}: {detail} (comm={comm}, status=0x{status:02x})')

    @property
    def gripper_overload(self):
        return self.motor_id == 6 and self.comm == 0 and self.status == 32


class MotorRangeError(ValueError):
    def __init__(self, name, raw, minimum, maximum):
        self.name, self.raw, self.minimum, self.maximum = name, raw, minimum, maximum
        super().__init__(f'{name} が較正範囲外です（現在 {raw}、範囲 {minimum}〜{maximum}）')
