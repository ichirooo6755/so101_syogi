#!/usr/bin/env python3
"""Capture stills or sampled frames from the ESP32-Sense MJPEG endpoint."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _base_url(value: str) -> str:
    return value.rstrip("/")


def _get(url: str, timeout: float):
    return urlopen(Request(url, headers={"User-Agent": "syodo-esp32-camera/1"}), timeout=timeout)


def _valid_jpeg(frame: bytes) -> bool:
    return len(frame) > 100 and frame.startswith(b"\xff\xd8") and frame.endswith(b"\xff\xd9")


def _frames(response, *, deadline: float | None = None):
    buffer = bytearray()
    while deadline is None or time.monotonic() < deadline:
        chunk = response.read(8192)
        if not chunk:
            return
        buffer.extend(chunk)
        while True:
            start = buffer.find(b"\xff\xd8")
            if start < 0:
                if len(buffer) > 1:
                    del buffer[:-1]
                break
            end = buffer.find(b"\xff\xd9", start + 2)
            if end < 0:
                if start:
                    del buffer[:start]
                break
            end += 2
            frame = bytes(buffer[start:end])
            del buffer[:end]
            if _valid_jpeg(frame):
                yield frame


def _new_dir() -> Path:
    path = Path("runs") / "esp32-camera" / time.strftime("%Y%m%d-%H%M%S")
    path.mkdir(parents=True, exist_ok=True)
    return path


def capture(args: argparse.Namespace) -> None:
    out = args.out or (_new_dir() / "capture.jpg")
    try:
        with _get(f"{_base_url(args.url)}/capture", args.timeout) as response:
            frame = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SystemExit(f"ESP32のcaptureへ接続できません: {exc}") from exc
    if not _valid_jpeg(frame):
        raise SystemExit(f"JPEGではない応答です（{len(frame)} bytes）。/health とシリアルログを確認してください。")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(frame)
    print(f"保存 {out} {len(frame)} bytes")


def stream(args: argparse.Namespace) -> None:
    out_dir = args.out_dir or _new_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + args.seconds if args.seconds > 0 else None
    saved = 0
    seen = 0
    try:
        with _get(f"{_base_url(args.url)}/stream", args.timeout) as response:
            for frame in _frames(response, deadline=deadline):
                seen += 1
                if seen % args.every:
                    continue
                path = out_dir / f"frame-{saved:05d}.jpg"
                path.write_bytes(frame)
                saved += 1
                print(f"保存 {path} {len(frame)} bytes")
                if args.max_frames and saved >= args.max_frames:
                    break
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SystemExit(f"ESP32のstreamへ接続できません: {exc}") from exc
    if saved == 0:
        raise SystemExit("MJPEGフレームを受信できませんでした。/health とシリアルログを確認してください。")


def health(args: argparse.Namespace) -> None:
    try:
        with _get(f"{_base_url(args.url)}/health", args.timeout) as response:
            print(response.read().decode("utf-8", "replace"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SystemExit(f"ESP32のhealthへ接続できません: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("url", help="ESP32のベースURL（例: http://192.168.4.1）")
    common.add_argument("--timeout", type=float, default=5.0)
    one = sub.add_parser("capture", parents=[common])
    one.add_argument("--out", type=Path)
    one.set_defaults(func=capture)
    many = sub.add_parser("stream", parents=[common])
    many.add_argument("--out-dir", type=Path)
    many.add_argument("--seconds", type=float, default=10.0)
    many.add_argument("--every", type=int, default=4, help="何フレームに1枚保存するか")
    many.add_argument("--max-frames", type=int, default=0)
    many.set_defaults(func=stream)
    check = sub.add_parser("health", parents=[common])
    check.set_defaults(func=health)
    args = parser.parse_args()
    if args.command == "stream" and args.every < 1:
        parser.error("--every は1以上です")
    args.func(args)


if __name__ == "__main__":
    main()
