"""Moving-arm camera: record frames and stop on transport failure only.

A changing picture is expected as the wrist moves; it is not a collision
classifier. Timestamps are host request midpoint with half-round-trip bounds.
"""
import json
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

class CameraGuard:
    def __init__(self, url, directory):
        self.url=url.rstrip('/')+'/capture'
        self.directory=Path(directory)/'camera'
        self.failure=None
        self.ready=threading.Event()
        self.stopping=threading.Event()
        self.thread=None
        self._armed=False

    def start(self):
        self.directory.mkdir(parents=True,exist_ok=True)
        self.thread=threading.Thread(target=self._run,daemon=True)
        self.thread.start()

    def _run(self):
        index=0
        try:
            while not self.stopping.is_set():
                start=time.monotonic()
                with urlopen(Request(self.url,headers={'User-Agent':'syodo-gui/1'}),timeout=3) as response:
                    frame=response.read(4_000_001)
                end=time.monotonic()
                if len(frame)>4_000_000 or not frame.startswith(b'\xff\xd8') or not frame.endswith(b'\xff\xd9'):
                    raise ValueError('カメラがJPEGを返しませんでした')
                name=f'{index:06d}.jpg'
                (self.directory/name).write_bytes(frame)
                record={'frame':name,'host_monotonic_s':(start+end)/2,'clock_uncertainty_s':(end-start)/2,'armed':self._armed}
                with (self.directory/'frames.jsonl').open('a') as f: f.write(json.dumps(record)+'\n')
                index+=1
                self.ready.set()
                self.stopping.wait(max(0,1-(time.monotonic()-start)))
        except Exception as exc:
            if not self.stopping.is_set(): self.failure=str(exc)
            self.ready.set()

    def wait_ready(self,timeout):
        return self.ready.wait(timeout) and self.failure is None

    def arm(self):
        self._armed=True
        return self.failure is None and self.ready.is_set()

    def disarm(self): self._armed=False

    def stop(self):
        self.stopping.set()
        if self.thread: self.thread.join(timeout=4)
