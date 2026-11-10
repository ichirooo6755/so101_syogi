"""Read framed JPEG from our XIAO firmware over native USB CDC."""
import time
import serial
from serial.tools import list_ports

# Arduino XIAO_ESP32S3 board definition, TinyUSB mode. Do not probe robot ports.
XIAO_IDS={(0x2886,0x0056),(0x2886,0x8056)}
MAX_JPEG=5_000_000


def ports():
    return [{'device':p.device,'description':p.description} for p in list_ports.comports()
            if (p.vid,p.pid) in XIAO_IDS and p.device.startswith('/dev/cu.')]


def read_jpeg(port):
    if port not in {p['device'] for p in ports()}:
        raise ValueError('XIAO カメラの USB ポートを選択してください')
    device=serial.Serial(port=None,baudrate=115200,timeout=.25,write_timeout=3)
    device.dtr=False;device.rts=False
    device.port=port
    device.open()
    try:
        device.reset_input_buffer()
        ready_deadline=time.monotonic()+8
        ready=False
        next_ping=0
        while time.monotonic()<ready_deadline:
            now=time.monotonic()
            if now>=next_ping:
                device.write(b'SHOGI/1 PING\n');device.flush();next_ping=now+1
            line=device.readline().strip()
            if line==b'SHOGI/1 READY':
                ready=True;break
            if line.startswith(b'SHOGI/1 ERROR '):
                raise ValueError('カメラが準備できません: '+line.decode('ascii','replace'))
        if not ready: raise ValueError('USB カメラの準備応答がありません')
        device.write(b'SHOGI/1 CAPTURE\n');device.flush()
        deadline=time.monotonic()+12
        size=None
        while time.monotonic()<deadline:
            line=device.readline().strip()
            if line.startswith(b'SHOGI/1 ERROR '):
                raise ValueError('カメラが撮影できません: '+line.decode('ascii','replace'))
            if line.startswith(b'SHOGI/1 JPEG '):
                try: size=int(line.split()[-1])
                except ValueError: raise ValueError('USB カメラの応答が不正です')
                break
        if size is None: raise ValueError('カメラの応答がありません。ファームと USB ポートを確認してください')
        if not 0<size<=MAX_JPEG: raise ValueError('カメラ画像の長さが不正です')
        data=bytearray()
        while len(data)<size and time.monotonic()<deadline:
            data.extend(device.read(min(65536,size-len(data))))
        if len(data)!=size: raise ValueError('USB 画像の受信が途中で切れました')
        if not (data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9')):
            raise ValueError('JPEG 画像として読み取れません')
        return bytes(data)
    finally:
        device.close()
