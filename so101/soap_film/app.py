import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread, Lock, Event
from urllib.parse import urlparse, parse_qs
import json, secrets, webbrowser, traceback
from dataclasses import asdict
from datetime import datetime
from particle_film import ParticleParams, ParticleFilm, export as export_particle
from sphere_grid import GridParams, GridFilm, export as export_grid

ROOT=Path(__file__).resolve().parent
TOKEN=secrets.token_urlsafe(24)
lock=Lock(); stop=Event()
status={'state':'idle','message':'準備完了', 'frame':0, 'preview':None}

def work(data):
    try:
        mode=data.get('solver','grid')
        common=dict(grid_width=int(data['grid_width']),fine_vortices=float(data['fine_vortices']),dt=float(data['dt']),swirl=float(data['swirl']),gravity=float(data['gravity']),marangoni=float(data['marangoni']),thickness_nm=float(data['thickness']),variation_nm=float(data['variation']),surfactant_variation=float(data['surfactant']),exposure=float(data['exposure']),saturation=float(data['saturation']),seed=int(data['seed']))
        if mode=='grid':
            p=GridParams(**common,initial_detail_nm=float(data.get('initial_detail_nm',0)));model=GridFilm;save_frame=export_grid
        elif mode=='particle':
            p=ParticleParams(**common,subdivision=int(data['subdivision']),particles_per_face=int(data['particles']),damping=float(data['damping']));model=ParticleFilm;save_frame=export_particle
        else: raise ValueError('未知の計算方式です')
        width=int(data['width']); frames=int(data['frames']); steps=int(data['steps']); vr=float(data['velocity_range']); preroll=int(data['preroll']);time_scale=float(data['time_scale'])
        if width not in (512,1024,2048,4096,8192) or not 1<=frames<=1000 or not 1<=steps<=100 or not 0<=preroll<=2000 or not 0<vr<=100 or not 0.05<=time_scale<=3: raise ValueError('出力パラメータが許容範囲外です')
        folder=ROOT/'output'/(mode+'_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        folder.mkdir(parents=True,exist_ok=False)
        manifest={'solver':mode,'parameters':asdict(p),'preparation_steps':preroll,'frame_steps':steps,'frame_time_scale':time_scale,'frame_step_dt':p.dt*time_scale,'output_width':width,'frames':frames,'velocity_range':vr}
        (folder/'settings.json').write_text(json.dumps(manifest,indent=2))
        film=model(p)
        for j in range(preroll):
            if stop.is_set():
                with lock: status.update(state='stopped',message='開始前の計算を停止しました')
                return
            if j%5==0:
                with lock: status.update(message=f'流れを準備中 {j}/{preroll}')
            film.step()
        for i in range(frames):
            if stop.is_set(): break
            with lock: status.update(message=f'フレーム {i+1}/{frames} を書き出し中',frame=i)
            save_frame(film,folder,i,width,vr)
            from PIL import Image
            image=Image.open(folder/f'color_{i:04d}.png'); image.thumbnail((768,384)); image.save(folder/'preview.png')
            with lock: status.update(preview=str(folder.relative_to(ROOT)),frame=i+1)
            if i+1<frames:
                for _ in range(steps):
                    if stop.is_set(): break
                    film.step(p.dt*time_scale)
        with lock: status.update(state='stopped' if stop.is_set() else 'done',message=f'{"停止" if stop.is_set() else "完了"}: {folder}')
    except Exception as e:
        traceback.print_exc()
        with lock: status.update(state='error',message=f'エラー: {e}')

class Handler(BaseHTTPRequestHandler):
    def allowed(self):
        host=self.headers.get('Host',''); origin=self.headers.get('Origin')
        return host==f'127.0.0.1:{self.server.server_port}' and (origin is None or origin==f'http://{host}')
    def reply(self,code,body,typ):
        self.send_response(code); self.send_header('Content-Type',typ); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if not self.allowed(): return self.reply(403,b'Forbidden','text/plain')
        u=urlparse(self.path)
        if u.path=='/' and parse_qs(u.query).get('token')==[TOKEN]: return self.reply(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
        if self.headers.get('X-Token')!=TOKEN and parse_qs(u.query).get('token')!=[TOKEN]: return self.reply(403,b'Forbidden','text/plain')
        if u.path=='/status':
            with lock: body=json.dumps(status).encode()
            return self.reply(200,body,'application/json')
        if u.path=='/preview':
            with lock: folder=status.get('preview')
            if folder:
                try: return self.reply(200,(ROOT/folder/'preview.png').read_bytes(),'image/png')
                except OSError: pass
        return self.reply(404,b'Not found','text/plain')
    def do_POST(self):
        if not self.allowed() or self.headers.get('X-Token')!=TOKEN or self.path not in ('/run','/stop'): return self.reply(403,b'Forbidden','text/plain')
        if self.path=='/stop':
            stop.set();return self.reply(200,b'{}','application/json')
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<4096: raise ValueError('invalid request size')
            data=json.loads(self.rfile.read(length))
            with lock:
                if status['state']=='running': return self.reply(409,b'Busy','text/plain')
                stop.clear(); status.update(state='running',message='球面の計算を初期化中',frame=0,preview=None)
            Thread(target=work,args=(data,),daemon=True).start()
            return self.reply(200,b'{}','application/json')
        except Exception as e: return self.reply(400,str(e).encode(),'text/plain')

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    url=f'http://127.0.0.1:{server.server_port}/?token={TOKEN}'
    print('Open:',url,flush=True); webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
