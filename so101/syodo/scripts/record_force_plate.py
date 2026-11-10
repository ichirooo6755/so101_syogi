#!/usr/bin/env python3
"""Record bounded USB JSONL with device/host clock correspondence."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from so101_calligraphy.force_plate_io import ForceRecorder


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seconds', type=float, default=0)
    p.add_argument('--no-sync', action='store_true', help='Raw diagnosis of old firmware only')
    args = p.parse_args(argv)
    if not 0 <= args.seconds < float('inf'):
        p.error('--seconds must be finite and nonnegative')
    recorder = ForceRecorder(args.port, args.out, synchronize=not args.no_sync).start()
    started = time.monotonic()
    try:
        while args.seconds == 0 or time.monotonic() - started < args.seconds:
            if recorder.error:
                break
            time.sleep(.1)
    except KeyboardInterrupt:
        pass
    finally:
        recorder.close()
    print(f'Saved {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
