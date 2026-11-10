#!/usr/bin/env python3
"""200 × 300 mm live force/centre display; uncalibrated mode shows raw diagnostics only."""
from __future__ import annotations
import argparse
from collections import deque
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import queue
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from so101_calligraphy.force_plate import ForcePlateCalibration, PlateGeometry, estimate_sample
from so101_calligraphy.force_plate_io import PicoStream


def find_port(explicit):
    if explicit:
        return Path(explicit)
    ports = sorted(Path('/dev').glob('cu.usbmodem*'))
    if len(ports) > 1:
        raise ValueError('Picoが複数あります。--portで指定してください')
    return ports[0] if ports else None


def load_config(path, demo=False):
    if demo:
        return ForcePlateCalibration(.270, .170, (0,)*4, (.001,)*4, .02, 2, .005), PlateGeometry()
    if path is None:
        return None, PlateGeometry()
    payload = json.loads(path.read_text())
    if payload.get('schema') != 1 or 'geometry' not in payload:
        raise ValueError('200 × 300 mm geometryを含む較正ファイルが必要です')
    cal, geo = ForcePlateCalibration(**payload['calibration']), PlateGeometry(**payload['geometry'])
    if abs(cal.support_x_m*1000-(geo.bottom_mm-geo.top_mm)) > 1e-6 or abs(cal.support_y_m*1000-(geo.right_mm-geo.left_mm)) > 1e-6:
        raise ValueError('Support spacing and calibration disagree')
    return cal, geo


def demo_sample(t, geometry):
    a, b = .5+.32*math.sin(t/.9), .5+.32*math.cos(t/1.5)
    force = .6+.3*math.sin(t)
    raw = [force*(1-a)*(1-b)*1000, force*a*(1-b)*1000, force*a*b*1000, force*(1-a)*b*1000]
    return {'raw_counts': raw, 'channel_time_s': [t]*4, 'saturated': False,
            'hx711_ready': [True]*4, 'cell_ids': [2,4,3,1]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port')
    parser.add_argument('--calibration', type=Path)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--ascii', action='store_true')
    parser.add_argument('--seconds', type=float, default=0)
    args = parser.parse_args(argv)
    calibration, geometry = load_config(args.calibration, args.demo)
    port = None if args.demo else find_port(args.port)
    if not args.demo and (port is None or not port.exists()):
        raise SystemExit('PicoのUSB CDCがありません。--demoで画面を確認できます')
    if not math.isfinite(args.seconds) or args.seconds < 0:
        parser.error('--seconds must be finite and nonnegative')
    q = queue.Queue(maxsize=100)
    stop = threading.Event()
    def reader():
        try:
            with PicoStream(port) as stream:
                while not stop.is_set():
                    try:
                        row = stream.read(.2)
                    except TimeoutError:
                        continue
                    if q.full():
                        q.get_nowait()
                    q.put_nowait(row)
        except Exception as exc:
            q.put({'event': 'error', 'detail': str(exc)})
    worker = None
    if not args.demo:
        worker = threading.Thread(target=reader, daemon=True)
        worker.start()
    started = time.monotonic()
    if args.ascii:
        try:
            while args.seconds == 0 or time.monotonic()-started < args.seconds:
                if args.demo:
                    sample = demo_sample(time.monotonic()-started, geometry)
                    time.sleep(.1)
                else:
                    try:
                        sample = q.get(timeout=.2)
                    except queue.Empty:
                        continue
                if sample.get('event') == 'error':
                    raise OSError(sample['detail'])
                if 'raw_counts' not in sample:
                    continue
                row = estimate_sample(calibration, sample, geometry) if calibration else sample
                print(json.dumps(row, ensure_ascii=False, allow_nan=False), flush=True)
        finally:
            stop.set()
            if worker:
                worker.join(1)
        return 0
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        stop.set()
        if worker:
            worker.join(1)
        mac = '/usr/bin/python3'
        if os.path.exists(mac) and os.path.realpath(sys.executable) != os.path.realpath(mac):
            os.execv(mac, [mac, str(Path(__file__).resolve()), *(sys.argv[1:] if argv is None else argv)])
        raise SystemExit('tkinterがありません。--asciiでテキスト表示できます')
    root = tk.Tk()
    root.title('書道フォースプレート' + (' — デモ' if args.demo else ''))
    root.geometry('650x760')
    root.minsize(520, 620)
    status = tk.StringVar(value='合成データのデモ' if args.demo else '受信待ち')
    total = tk.StringVar(value='合計荷重 —')
    location = tk.StringVar(value='荷重中心 —')
    cell_text = tk.StringVar(value='')
    ttk.Label(root, text='200 × 300 mm 荷重計測', font=('', 22, 'bold')).pack(pady=(12,4))
    ttk.Label(root, textvariable=total, font=('', 20)).pack()
    ttk.Label(root, textvariable=location).pack(pady=4)
    canvas = tk.Canvas(root, bg='#eef1f4', highlightthickness=0)
    canvas.pack(fill='both', expand=True, padx=20, pady=8)
    ttk.Label(root, textvariable=cell_text, justify='center').pack(pady=4)
    ttk.Label(root, textvariable=status, wraplength=580).pack(pady=4)
    ttk.Label(root, text='筆だけが触れているときの合計荷重・荷重中心。複数の接触は分離できません。', wraplength=580).pack(pady=(2,12))
    trail = deque(maxlen=100)
    last_sample = started
    last_row = None
    last_raw = None
    tare_frames = None
    def tare():
        nonlocal tare_frames
        tare_frames = []
        status.set('無荷重のままお待ちください。16フレーム平均でこの画面の風袋を更新します。')
    ttk.Button(root, text='無荷重で風袋を取る（表示のみ）', command=tare, state='normal' if calibration else 'disabled').pack(pady=(0,10))
    def render():
        canvas.delete('all')
        w,h = max(canvas.winfo_width(),200), max(canvas.winfo_height(),300)
        scale = min((w-100)/geometry.width_mm, (h-55)/geometry.height_mm)
        left, top = (w-geometry.width_mm*scale)/2, 30
        def point(x,y):
            return left+x*scale, top+y*scale
        x1,y1 = point(geometry.width_mm,geometry.height_mm)
        canvas.create_rectangle(left,top,x1,y1, fill='white',outline='#64748b',width=2)
        canvas.create_text((left+x1)/2,12,text=f'奥 / 上　{geometry.width_mm:g} × {geometry.height_mm:g} mm',fill='#334155')
        for cell, (x,y) in zip((2,4,3,1), geometry.supports_mm):
            px,py = point(x,y)
            canvas.create_rectangle(px-5,py-5,px+5,py+5,fill='#64748b',outline='')
            canvas.create_text(px,py+16,text=str(cell),fill='#334155')
        for x,y,force in trail:
            px,py = point(x,y)
            canvas.create_oval(px-2,py-2,px+2,py+2,fill='#9fbfcc',outline='')
        if last_row and last_row['valid']:
            px,py = point(last_row['board_x_mm'],last_row['board_y_mm'])
            radius = min(24, 6+last_row['normal_force_n']*10)
            canvas.create_oval(px-radius,py-radius,px+radius,py+radius,fill='#dc6b36',outline='#9a3412',width=2)
            canvas.create_line(px-10,py,px+10,py,fill='white',width=2)
            canvas.create_line(px,py-10,px,py+10,fill='white',width=2)
        elif not calibration:
            canvas.create_text((left+x1)/2,(top+y1)/2,text='未較正\nN・g相当・位置は較正後に表示',justify='center',fill='#64748b')
    def apply(sample):
        nonlocal calibration, last_row, last_sample, last_raw, tare_frames
        last_sample = time.monotonic()
        last_raw = sample
        ready = sample.get('hx711_ready', [False]*4)
        if tare_frames is not None:
            if ready != [True]*4 or sample['saturated'] is not False:
                tare_frames = None
                status.set('欠測・飽和のため風袋を更新できません')
            else:
                tare_frames.append(sample['raw_counts'])
                if len(tare_frames) >= 16:
                    calibration = replace(calibration, zero_counts=tuple(sum(v[i] for v in tare_frames)/len(tare_frames) for i in range(4)))
                    tare_frames = None
                    trail.clear()
                    status.set('表示の風袋を更新しました。保存済み較正ファイルは変更していません。')
        if calibration:
            last_row = estimate_sample(calibration, sample, geometry)
            if last_row['invalid_reason'] in ('channel_not_ready', 'adc_saturation', 'asynchronous_channels'):
                total.set('合計荷重 — （計測無効）')
            else:
                total.set(f"合計 {last_row['normal_force_n']:.3f} N　/　{last_row['mass_equivalent_g']:.1f} g相当")
            if last_row['valid']:
                location.set(f"左から {last_row['board_x_mm']:.1f} mm　上から {last_row['board_y_mm']:.1f} mm")
                trail.append((last_row['board_x_mm'],last_row['board_y_mm'],last_row['normal_force_n']))
            else:
                location.set('荷重中心 —　'+str(last_row['invalid_reason']))
            values = last_row['channel_force_n']
            cell_text.set('　'.join(f'{cell}: {v:.3f} N' if ok else f'{cell}: 未応答' for cell,v,ok in zip((2,4,3,1),values,ready)))
        else:
            total.set('未較正：個別の生カウントを表示')
            cell_text.set('　'.join(f'{cell}: {v:.0f}' if ok else f'{cell}: 未応答' for cell,v,ok in zip((2,4,3,1),sample['raw_counts'],ready)))
            status.set(f'HX711応答 {sum(ready)}/4。既知の重りでcalibrateを実行してください。')
        render()
    def tick():
        nonlocal last_row
        if args.seconds and time.monotonic()-started >= args.seconds:
            root.destroy()
            return
        try:
            if args.demo:
                apply(demo_sample(time.monotonic()-started,geometry))
            else:
                while not q.empty():
                    sample=q.get_nowait()
                    if sample.get('event') == 'error':
                        status.set(sample['detail'])
                    elif 'raw_counts' in sample:
                        apply(sample)
                if time.monotonic()-last_sample > 1:
                    last_row=None
                    total.set('合計荷重 —')
                    location.set('荷重中心 —')
                    status.set('データが1秒以上届いていません')
                    render()
        except (ValueError, KeyError, TypeError) as exc:
            last_row=None
            status.set(str(exc))
            render()
        root.after(50,tick)
    canvas.bind('<Configure>',lambda e:render())
    root.after(50,tick)
    try:
        root.mainloop()
    finally:
        stop.set()
        if worker:
            worker.join(1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
