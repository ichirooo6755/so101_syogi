import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import usb_camera

JPEG=b'\xff\xd8example\xff\xd9'
class FakeSerial:
    def __init__(self, **kwargs):
        self.dtr=True;self.rts=True;self.port=None;self.closed=False;self.lines=[];self.payload=b''
    def open(self): pass
    def close(self): self.closed=True
    def reset_input_buffer(self): pass
    def flush(self): pass
    def write(self,data):
        if data==b'SHOGI/1 PING\n': self.lines.append(b'SHOGI/1 READY\n')
        elif data==b'SHOGI/1 CAPTURE\n':
            self.lines.append(b'SHOGI/1 JPEG %d\n'%len(JPEG));self.payload=JPEG
    def readline(self): return self.lines.pop(0) if self.lines else b''
    def read(self,n):
        out=self.payload[:n];self.payload=self.payload[n:];return out

class USBTest(unittest.TestCase):
    def test_capture_framing(self):
        fake=FakeSerial()
        with patch.object(usb_camera,'ports',return_value=[{'device':'/dev/cu.usbmodemX','description':'XIAO'}]),patch.object(usb_camera.serial,'Serial',return_value=fake):
            self.assertEqual(usb_camera.read_jpeg('/dev/cu.usbmodemX'),JPEG)
        self.assertTrue(fake.closed);self.assertFalse(fake.dtr);self.assertFalse(fake.rts)
    def test_never_open_unlisted_or_robot_port(self):
        with patch.object(usb_camera,'ports',return_value=[]),patch.object(usb_camera.serial,'Serial') as serial:
            with self.assertRaises(ValueError): usb_camera.read_jpeg('/dev/cu.usbmodem5B7B0140931')
            serial.assert_not_called()

if __name__=='__main__': unittest.main()
