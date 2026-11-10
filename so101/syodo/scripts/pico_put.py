#!/usr/bin/env python3
"""Verified MicroPython file upload over USB CDC, without mpremote."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import select
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from so101_calligraphy.force_plate_io import PicoStream


def raw_exec(port, source, *, timeout=8):
    with PicoStream(port) as stream:
        def send(data):
            end=time.monotonic()+timeout
            while data:
                if time.monotonic() >= end:
                    raise TimeoutError('Raw REPL write timed out')
                if select.select([],[stream.fd],[],.1)[1]:
                    try:
                        count=os.write(stream.fd,data[:128])
                        data=data[count:]
                    except BlockingIOError:
                        continue
                    time.sleep(.003)
        def receive(until, seconds):
            end=time.monotonic()+seconds
            buf=b''
            while time.monotonic() < end:
                if select.select([stream.fd],[],[],.1)[0]:
                    data=os.read(stream.fd,16384)
                    if not data:
                        raise OSError('Pico disconnected in raw REPL')
                    buf+=data
                    if until(buf):
                        return buf
            raise TimeoutError('Raw REPL response timed out: '+repr(buf[-300:]))
        send(b'\x03\x03\x01')
        receive(lambda b:b'raw REPL' in b and b.endswith(b'>'),3)
        send(source.encode('utf-8') if isinstance(source,str) else source)
        send(b'\x04')
        reply=receive(lambda b:b.count(b'\x04') >= 2,timeout)
        send(b'\x02')
        if not reply.startswith(b'OK'):
            raise RuntimeError('MicroPython did not accept source: '+repr(reply[:200]))
        stdout,stderr,*_=reply[2:].split(b'\x04')
        if stderr.strip():
            raise RuntimeError('MicroPython: '+stderr.decode('utf-8','replace'))
        return stdout


def put_text(port, dest, text):
    content=text.encode('utf-8')
    # Temporary file and rename leave the previous main.py intact on failed transfer.
    code=f"f=open({(dest+'.upload')!r},'wb')\n"
    for index in range(0,len(content),128):
        code+=f'f.write({content[index:index+128]!r})\n'
    code+='f.close()\n'
    code+=f"import os\nos.rename({(dest+'.upload')!r},{dest!r})\n"
    code+=f"import hashlib,binascii\nprint(binascii.hexlify(hashlib.sha256(open({dest!r},'rb').read()).digest()).decode())\n"
    result=raw_exec(port,code).decode().strip().splitlines()[-1]
    expected=hashlib.sha256(content).hexdigest()
    if result != expected:
        raise RuntimeError(f'Pico hash mismatch for {dest}')
    return expected


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',required=True)
    p.add_argument('--reset',action='store_true',help='Soft reset after verified upload')
    p.add_argument('src',type=Path)
    p.add_argument('dest')
    args=p.parse_args(argv)
    digest=put_text(Path(args.port),args.dest,args.src.read_text(encoding='utf-8'))
    print(f'Verified {args.src} -> {args.dest}: SHA256 {digest}')
    if args.reset:
        with PicoStream(args.port) as stream:
            os.write(stream.fd,b'\x04')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
