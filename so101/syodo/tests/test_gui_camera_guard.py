import json
import time
from scripts import gui_camera_guard as guard


def test_arm_camera_records_frame_and_timestamp_without_background_comparison(tmp_path,monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,n): return b'\xff\xd8frame\xff\xd9'
    monkeypatch.setattr(guard,'urlopen',lambda *a,**kw: Response())
    camera=guard.CameraGuard('http://camera',tmp_path)
    camera.start()
    try:
        assert camera.wait_ready(2)
        assert camera.arm()
        assert (tmp_path/'camera/000000.jpg').read_bytes()==b'\xff\xd8frame\xff\xd9'
        entry=json.loads((tmp_path/'camera/frames.jsonl').read_text().splitlines()[0])
        assert entry['clock_uncertainty_s']>=0
        assert camera.failure is None
    finally: camera.stop()


def test_camera_failure_prevents_start(tmp_path,monkeypatch):
    def failed(*args,**kwargs): raise OSError('unreachable')
    monkeypatch.setattr(guard,'urlopen',failed)
    camera=guard.CameraGuard('http://camera',tmp_path)
    camera.start()
    try:
        assert not camera.wait_ready(2)
        assert not camera.arm()
        assert camera.failure=='unreachable'
    finally: camera.stop()
