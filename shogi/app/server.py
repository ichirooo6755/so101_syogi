#!/usr/bin/env python3
"""Local shogi workbench: candidate vision, legal moves and manual robot control."""
import base64
import hashlib
import math
import ipaddress
import queue
import json
import secrets
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np
import shogi
from move_plan import build_plan
import board_map
from board_map import BOARD_X, sim_square, simulation_obstacles, set_pose, reset_pose, pose as board_pose, piece_yaw_deg, stand_xy
from board_pose import pose_from_corners, same_view
from detect_board import detect_corners
from robot_arm import Arm, with_observe, OBSERVE, resolve_port, load_offsets
from motion import legs
from workspace import move_in_reach
from markers import detect_marker_corners
from vision_turn import VisionTurn
import usb_camera
import mac_camera
import teach_store
import teaching_tasks

ROOT = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.RLock()
board = shogi.Board()
frame = None
frame_id = None
baseline = None
corners = None
controller_process = None
ai_side = shogi.WHITE
pending = None
engine_error = None
sim_job = {"status":"idle"}
robot_job = {"status":"idle"}
game_revision = 0
reference_corners = None
robot_live = False
auto = {'status':'idle'}
auto_stop = threading.Event()
auto_thread = None
auto_camera = None
teach_session = None


def teaching_ports():
    """List serial devices without probing or moving them; omit the XIAO camera."""
    return [{'device':p.device,'description':p.description or p.device}
            for p in usb_camera.list_ports.comports()
            if p.device.startswith('/dev/cu.') and (p.vid,p.pid) not in usb_camera.XIAO_IDS]


def learned_teaching_candidates(side):
    """Show saved simulation failures only while their model and board match."""
    if abs(board_map.BOARD_W-.33)>1e-9 or abs(board_map.BOARD_L-.36)>1e-9: return []
    report=ROOT.parent/'output/stock_arm/learned_failure_samples.json'
    checkpoint=ROOT.parent/'simulation/runs/waypoint_id5/policy.pt'
    try:
        if report.stat().st_size>5_000_000 or checkpoint.stat().st_size>50_000_000: return []
        data=json.loads(report.read_text())
        digest=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        fingerprints=teaching_tasks.simulation_fingerprints(ROOT.parent)
        return teaching_tasks.learned_report_candidates(data,side,board_pose(),digest,fingerprints)
    except (OSError,ValueError,TypeError):
        return []


def capture_teaching_position(follower_port,leader_port=None):
    """Ask the existing Follower adapter for a read-only stable snapshot."""
    python=Path.home()/'Documents/lerobot-hw/.venv/bin/python'
    if not python.is_file(): raise ValueError('既存 Follower の Python 環境が見つかりません')
    available={p['device'] for p in teaching_ports()}
    if follower_port not in available or (leader_port is not None and leader_port not in available):
        raise ValueError('アームの USB を選び直してください')
    if leader_port is not None and leader_port==follower_port:
        raise ValueError('Leader と Follower に同じ USB を選べません')
    cmd=[str(python),str(ROOT/'teach_capture.py'),follower_port]
    if leader_port is not None: cmd.append(leader_port)
    try:
        proc=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Follower の位置読み取りがタイムアウトしました') from exc
    if proc.returncode:
        try: message=json.loads(proc.stderr).get('error')
        except (ValueError,AttributeError): message=None
        raise ValueError(message or 'Follower の位置を読み取れません')
    try: return json.loads(proc.stdout)
    except ValueError as exc: raise ValueError('Follower の読み取り結果が不正です') from exc


def jpeg(url):
    u = urllib.parse.urlsplit(url)
    if u.scheme != 'http' or not u.hostname or u.username or u.password:
        raise ValueError('カメラの HTTP アドレスを入力してください')
    try:
        ip = ipaddress.ip_address(u.hostname)
    except ValueError:
        raise ValueError('カメラの IP アドレスを数字で指定してください')
    if not (ip.is_private and not ip.is_loopback and not ip.is_link_local):
        raise ValueError('ローカルネットワークのカメラ IP を指定してください')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise ValueError('カメラからの転送は使えません')
    req = urllib.request.Request(url, headers={'Accept': 'image/jpeg'})
    with urllib.request.build_opener(NoRedirect).open(req, timeout=5) as response:
        data = response.read(5_000_001)
    if len(data) > 5_000_000:
        raise ValueError('画像が大きすぎます。静止画 URL を指定してください')
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.size > 20_000_000:
        raise ValueError('JPEG 画像を読み取れません')
    return image


def normalized(image, points):
    pts = np.array(points, dtype=np.float32)
    if pts.shape != (4, 2) or not np.isfinite(pts).all():
        raise ValueError('盤の四隅を順番に指定してください')
    h,w = image.shape[:2]
    if np.any(pts[:,0]<0) or np.any(pts[:,0]>=w) or np.any(pts[:,1]<0) or np.any(pts[:,1]>=h):
        raise ValueError('四隅が画像の外です')
    contour=pts.reshape(-1,1,2)
    if not cv2.isContourConvex(contour) or abs(cv2.contourArea(contour)) < 0.01*w*h:
        raise ValueError('四隅の順番または範囲を確認してください')
    target=np.float32([[0,0],[539,0],[539,539],[0,539]])
    return cv2.warpPerspective(image, cv2.getPerspectiveTransform(pts,target),(540,540))


def candidates(old, new):
    # Compare central cell interiors; grid edges, hand movements and illumination can mislead.
    a=cv2.cvtColor(old,cv2.COLOR_BGR2GRAY).astype(np.float32)
    b=cv2.cvtColor(new,cv2.COLOR_BGR2GRAY).astype(np.float32)
    diff=np.abs((b-a)-np.median(b-a))
    scores=[]
    for y in range(9):
        for x in range(9):
            cell=diff[y*60+8:y*60+52,x*60+8:x*60+52]
            scores.append(float(np.mean(cell)))
    ranked=[]
    for move in board.legal_moves:
        changed=[move.to_square]
        if move.from_square is not None:
            changed.append(move.from_square)
        changed=list(set(changed))
        inside=sum(scores[i] for i in changed)/len(changed)
        outside=sum(v for i,v in enumerate(scores) if i not in changed)/(81-len(changed))
        ranked.append({'usi':move.usi(), 'score':round(inside-outside,2)})
    return sorted(ranked,key=lambda x:x['score'],reverse=True)[:10]


def engine_move():
    engine = ROOT.parent / 'vendor' / 'Fairy-Stockfish' / 'src' / 'stockfish'
    if not engine.is_file():
        raise ValueError('将棋エンジンが見つかりません。README を確認してください')
    proc=subprocess.Popen([str(engine)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL,text=True,bufsize=1)
    lines=queue.Queue()
    def read_output():
        for line in proc.stdout:
            lines.put(line.strip())
    threading.Thread(target=read_output,daemon=True).start()
    def send(line):
        proc.stdin.write(line+'\n');proc.stdin.flush()
    def wait_for(prefix):
        import time
        deadline=time.monotonic()+15
        while True:
            try: line=lines.get(timeout=max(0,deadline-time.monotonic()))
            except queue.Empty: raise ValueError('将棋エンジンの応答がありません')
            if line.startswith(prefix): return line
    try:
        send('usi');wait_for('usiok')
        send('isready');wait_for('readyok')
        send('position sfen '+board.sfen())
        # The engine chooses from all legal moves. Robot reach is a separate
        # mechanical constraint and must not silently change shogi strategy.
        send('go movetime 500')
        result=wait_for('bestmove ').split()[1]
        if result in ('resign','(none)','0000'): return None
        move=shogi.Move.from_usi(result)
        if move not in board.legal_moves: raise ValueError('エンジンの手が合法手と一致しません')
        return result
    finally:
        proc.kill();proc.wait(timeout=3)
        proc.stdin.close();proc.stdout.close()


def use_tracked_board(track):
    """Apply a calibrated board track to the coordinates the arm plans with."""
    shift=track['shift_m']
    set_pose(x=BOARD_X+float(shift[0]), y=float(shift[1]), yaw=math.radians(float(track['yaw_deg'])))
    return board_pose()


def stage_ai():
    global pending, engine_error
    if board.turn != ai_side or board.is_game_over():
        return
    try:
        usi=engine_move()
        pending=build_plan(board,usi) if usi else None
        engine_error=None if usi else 'エンジンに指し手がありません'
    except Exception as exc:
        pending=None
        engine_error=str(exc)


class PlanLegFailure(ValueError):
    def __init__(self,message,report):
        super().__init__(message)
        self.report=report


def plan_pending_leg(move,leg):
    """Associate a failed offline leg with the unchanged pending move."""
    with LOCK:
        revision=game_revision
        usi=move.get('usi')
    try:
        return plan_leg(leg['source'],leg['target'],leg['promotion'],leg.get('yaw_deg',0))
    except PlanLegFailure as exc:
        suggestions=teaching_tasks.from_failure(move,exc.report,leg.get('role','move'))
        with LOCK:
            if pending and pending.get('usi')==usi and revision==game_revision:
                pending['teach_suggestions']=teaching_tasks.combine(
                    pending.get('teach_suggestions',[]),suggestions)
        raise


def mark_reach():
    """Plan the pending move once. Does not move the arm or the board."""
    with LOCK:
        move=None if pending is None or pending.get('reach') else dict(pending)
        side='black' if ai_side==shogi.BLACK else 'white'
        usi=None if move is None else move.get('usi')
        revision=game_revision
    if not move: return
    move['board_side']=side
    try:
        for leg in legs(move):
            plan_pending_leg(move,leg)
        reach='ok'
    except Exception as exc:
        reach=str(exc)
    with LOCK:
        if pending and pending.get('usi')==usi and revision==game_revision:
            pending['reach']=reach


def sim_succeeded(result):
    # Two independent previews are not a successful continuous capture.
    if result.get('reason')=='capture_preview_only': return False
    return bool(result.get('success'))


def apply_pending_move():
    global pending, baseline, game_revision
    if not pending or board.turn!=ai_side: return False
    move=shogi.Move.from_usi(pending['usi'])
    if move not in board.legal_moves: return False
    board.push(move);pending=None;baseline=None;game_revision+=1
    return True


def simulate_pending(move, original_sfen, original_revision, apply=False):
    """Run one offline MuJoCo trial, with no hardware communication."""
    global sim_job, pending, baseline, game_revision
    sim_python=ROOT.parent/'.venv-sim/bin/python'
    script=ROOT.parent/('simulation/capture_preview.py' if move['capture'] else 'simulation/adaptive_pick_place.py')
    result_path=ROOT.parent/'simulation/runs'/('gui_'+secrets.token_hex(6)+'.json')
    source=sim_square(move['source'],move['board_side']);target=sim_square(move['destination'],move['board_side'])
    try:
        if not sim_python.is_file() or not script.is_file(): raise ValueError('シミュレーション環境が見つかりません')
        cmd=[str(sim_python),str(script),'--source',str(source[0]),str(source[1]),'--target',str(target[0]),str(target[1]),
             '--obstacles-json',json.dumps(move['obstacles'],separators=(',',':')),'--out',str(result_path)]
        if not move['capture']:
            cmd+=['--yaw-deg',str(move['piece_yaw_deg'])]
            if move.get('promotion'): cmd.append('--promote')
        else:
            if move.get('captured_promoted'): cmd.append('--promote-captured')
            if move.get('promotion'): cmd.append('--promote-own')
        proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=180)
        if not result_path.is_file(): raise ValueError('MuJoCo の試行結果がありません: '+proc.stderr[-300:])
        result=json.loads(result_path.read_text());result.pop('trace',None)
        if result.get('reason')=='capture_preview_only':
            for name in ('captured_to_stand','own_piece_to_board'):
                result[name].pop('trace',None)
        with LOCK:
            applied=bool(sim_job.get('applied'))
            if original_revision==game_revision and pending and pending.get('usi')==move['usi']:
                pending['teach_suggestions']=teaching_tasks.combine(
                    pending.get('teach_suggestions',[]),teaching_tasks.from_simulation(move,result))
            if apply and original_revision==game_revision and pending and pending['usi']==move['usi'] and sim_succeeded(result):
                applied=apply_pending_move()
            sim_job={'status':'finished','usi':move['usi'],'sfen':original_sfen,'revision':original_revision,'result':result,'exit_code':proc.returncode,'result_path':str(result_path),'applied':applied,
                     'source':move.get('source'),'destination':move.get('destination')}
    except Exception as exc:
        with LOCK: sim_job={'status':'error','usi':move['usi'],'sfen':original_sfen,'revision':original_revision,'error':str(exc),'applied':bool(sim_job.get('applied'))}


def plan_leg(source, target, promote=False, yaw_deg=0):
    sim_python=ROOT.parent/'.venv-sim/bin/python'
    script=ROOT.parent/'simulation/pick_place.py'
    result_path=ROOT.parent/'simulation/runs'/('robot_'+secrets.token_hex(6)+'.json')
    if not sim_python.is_file(): raise ValueError('シミュレーション環境が見つかりません')
    cmd=[str(sim_python),str(script),'--source',str(source[0]),str(source[1]),'--target',str(target[0]),str(target[1]),
         '--board-x',str(board_pose()['x']),'--board-y',str(board_pose()['y']),'--yaw-deg',str(yaw_deg),
         '--no-neighbors','--plan-only','--out',str(result_path)]
    sx,sy=stand_xy()
    if abs(float(source[0])-sx)<0.04 and abs(float(source[1])-sy)<0.04 or abs(float(target[0])-sx)<0.04 and abs(float(target[1])-sy)<0.04:
        cmd.append('--with-stand')
    if promote: cmd.append('--promote')
    proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=60)
    if not result_path.is_file(): raise ValueError('経由点を作れません: '+(proc.stderr or '')[-300:])
    plan=json.loads(result_path.read_text()); plan.pop('trace',None)
    if not plan.get('success'):
        message={'ik_unreachable':'このマスの姿勢を計算できません','grasp_folded':'根元すぎて爪が空振りします','id5_cable_limit':'この成りは手首の配線範囲を超えます'}.get(plan.get('reason'),'経由点を作れません')
        raise PlanLegFailure(message,plan)
    if not plan.get('waypoints'): raise ValueError('経由点が空です')
    return plan


def execute_robot(move, live=False, apply=False):
    """Plan IK legs (move / capture / drop) and optionally send them to the Follower."""
    global robot_job, sim_job
    try:
        parts=[]
        waypoints=[]
        for leg in legs(move):
            plan=plan_pending_leg(move,leg)
            parts.append({'role':leg['role'],'plan':plan})
            waypoints.extend(plan['waypoints'])
        report=Arm().play(with_observe(waypoints), live=live)
        with LOCK:
            # Planning/air playback never proves that a physical piece moved.
            # The live path is gated separately until visual verification exists.
            applied=False
            if applied: sim_job={**sim_job,'applied':True}
            robot_job={'status':'finished','usi':move.get('usi'),'legs':[p['role'] for p in parts],'robot':report,'live':live,'applied':applied}
    except Exception as exc:
        with LOCK: robot_job={'status':'error','usi':move.get('usi'),'error':str(exc),'live':live,'applied':False}


def go_observe(live=False):
    global robot_job
    try:
        report=Arm().play([dict(OBSERVE)], live=live)
        with LOCK: robot_job={'status':'finished','usi':None,'legs':['observe'],'robot':report,'live':live}
    except Exception as exc:
        with LOCK: robot_job={'status':'error','error':str(exc),'live':live}


def _camera_frame(source, value):
    if source == 'usb':
        data = usb_camera.read_jpeg(value)
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if image is None or image.size > 20_000_000:
            raise ValueError('USB カメラの画像を読み取れません')
        return image
    if source == 'wifi': return jpeg(value)
    if source == 'mac': return mac_camera.grab()
    raise ValueError('カメラの種類が不正です')


def _preview(image):
    h, w = image.shape[:2]
    scale = min(1.0, 800 / max(w, h))
    resized = cv2.resize(image, None, fx=scale, fy=scale) if scale < 1 else image
    ok, encoded = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return base64.b64encode(encoded).decode() if ok else None


def automatic_game(source, value, stop):
    """Observe one human move at a time; pause before unverified robot motion."""
    global auto, game_revision
    tracker, revision = VisionTurn(), None
    while not stop.is_set():
        probe=False
        with LOCK:
            if stop.is_set(): break
            if auto.pop('reset_stability',False):
                tracker.previous = None
                tracker.stable = 0
            if board.is_game_over():
                auto.update(status='finished', message='対局が終わりました')
                return
            if auto.get('status') == 'paused':
                need_wait = True
            elif board.turn == ai_side:
                if pending is None and engine_error is None:
                    stage_ai()
                probe=bool(pending) and not pending.get('reach')
                if pending and pending.get('reach') not in (None,'ok'):
                    message=pending['usi']+' は'+pending['reach']+'。人が置いて、実盤に合わせて記録してください。'
                elif pending:
                    message='AI の手を計算しました。実機の把持は未検証のため停止中です。'
                else:
                    message='AI の手を計算できません: '+str(engine_error)
                auto.update(status='robot_blocked', message=message)
                need_wait = True
            elif auto.get('status') == 'ambiguous' and auto.get('revision') == game_revision:
                need_wait = True
            else:
                need_wait = False
                position = shogi.Board(board.sfen())
                current_revision = game_revision
                if revision != current_revision:
                    tracker, revision = VisionTurn(), current_revision
        if probe:
            mark_reach()
            with LOCK:
                if pending and pending.get('reach') not in (None,'ok'):
                    auto['message']=pending['usi']+' は'+pending['reach']+'。人が置いて、実盤に合わせて記録してください。'
        if need_wait:
            stop.wait(1)
            continue
        try:
            image = _camera_frame(source, value)
            preview = _preview(image)
            pts = detect_marker_corners(image)
            result = tracker.feed(normalized(image, pts), position)
            with LOCK:
                if stop.is_set() or auto.get('status') == 'paused' or current_revision != game_revision: continue
                auto['image'] = preview
                auto['corners'] = pts
                status = result['status']
                if status == 'detected':
                    move = shogi.Move.from_usi(result['usi'])
                    if move not in board.legal_moves: raise ValueError('局面が変わりました')
                    board.push(move)
                    game_revision += 1
                    stage_ai()
                    auto.update(status='robot_blocked', last_human=move.usi(),
                                message='人の手を検知しました。実機動作は未検証のため停止中です。')
                elif status == 'ambiguous':
                    auto.update(status='ambiguous', candidates=result['candidates'], revision=game_revision,
                                message='画像だけでは指し手を一意に決められません。実盤に合う手を選んでください。')
                else:
                    auto.update(status=status, candidates=[], message=(
                        '盤が静止するのを待っています' if status == 'settling' else 'あなたの手を待っています'))
        except Exception as exc:
            # Missing or occluded markers interrupt stability, not the stored baseline.
            tracker.previous = None
            tracker.stable = 0
            with LOCK:
                if stop.is_set(): break
                if auto.get('status') == 'paused': continue
                auto.update(status='looking', message=str(exc))
                if 'preview' in locals(): auto['image'] = preview
        stop.wait(1.2)


def state():
    side='black' if ai_side==shogi.BLACK else 'white'
    return {'sfen':board.sfen(),'board':board.sfen().split()[0], 'turn':'先手' if board.turn==shogi.BLACK else '後手',
            'legal_count':len(list(board.legal_moves)), 'game_over':board.is_game_over(),
            'ai_side':'先手' if ai_side==shogi.BLACK else '後手', 'ai_turn':board.turn==ai_side,
            'pending':pending, 'engine_error':engine_error,
            'simulation':{**sim_job,'stale':sim_job.get('revision') is not None and sim_job.get('revision')!=game_revision},
            'board_pose':board_pose(),'robot':robot_job,'robot_live':robot_live,'offsets':load_offsets(),
            'auto':dict(auto), 'teaching':teach_store.public_state(teach_session),
            'learned_teaching':{'side':side,'candidates':learned_teaching_candidates(side)}}


class Handler(BaseHTTPRequestHandler):
    def respond(self, data, status=200, content='application/json; charset=utf-8'):
        if isinstance(data,dict): data=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type',content);self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def host_ok(self): return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'
    def do_GET(self):
        if not self.host_ok():
            return self.respond({'error':'Not found'},404)
        if self.path == '/'+TOKEN+'/markers.svg':
            return self.respond((ROOT/'board_markers.svg').read_bytes(), content='image/svg+xml')
        if self.path != '/'+TOKEN:
            return self.respond({'error':'Not found'},404)
        return self.respond((ROOT/'index.html').read_bytes(),content='text/html; charset=utf-8')
    def do_POST(self):
        global board, frame, frame_id, baseline, corners, controller_process, ai_side, pending, engine_error, sim_job, game_revision
        global reference_corners, robot_live, robot_job, auto, auto_thread, auto_stop, auto_camera, teach_session
        if (not self.host_ok() or self.path != '/api' or self.headers.get('Origin') != f'http://127.0.0.1:{self.server.server_port}' or self.headers.get('X-Token') != TOKEN):
            return self.respond({'error':'Forbidden'},403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<16384: raise ValueError('リクエストが不正です')
            data=json.loads(self.rfile.read(length)); action=data.get('action')
            with LOCK:
                out={}
                if action=='state': pass
                elif action=='teach_begin':
                    if auto.get('status') not in ('idle','paused','finished'):
                        raise ValueError('自動検知を停止してから教えてください')
                    if robot_job.get('status')=='running': raise ValueError('アーム動作中です')
                    square=data.get('square');operation=data.get('operation','pick')
                    issue=None
                    pending_side=(pending.get('board_side') if pending else None) or ('black' if ai_side==shogi.BLACK else 'white')
                    if pending and data.get('side')==pending_side:
                        match=next((s for s in pending.get('teach_suggestions',[])
                                    if s.get('square')==square and s.get('operation')==operation),None)
                        if match:
                            issue={**match,'usi':pending.get('usi'),'sfen':board.sfen()}
                    if issue is None:
                        match=next((s for s in learned_teaching_candidates(data.get('side'))
                                    if s.get('square')==square and s.get('operation')==operation),None)
                        if match:
                            issue={**match,'sfen_at_teaching':board.sfen()}
                    teach_session=teach_store.begin(square,data.get('side'),board_pose(),
                                                    mode=data.get('mode','leader'),operation=operation,issue=issue)
                elif action=='teach_capture':
                    if auto.get('status') not in ('idle','paused','finished'):
                        raise ValueError('自動検知を停止してから記録してください')
                    if robot_job.get('status')=='running': raise ValueError('アーム動作中です')
                    if teach_session is None or data.get('id')!=teach_session.get('id'):
                        raise ValueError('記録するマスを選び直してください')
                    if teach_session.get('status')!='recording':
                        raise ValueError('次に教えるマスを選んでください')
                    leader_port=data.get('leader_port') if teach_session['mode']=='leader' else None
                    if teach_session['mode']=='leader' and not leader_port:
                        raise ValueError('Leader の USB を選んでください')
                    teach_session=teach_store.add_capture(teach_session,
                        capture_teaching_position(data.get('follower_port'),leader_port))
                elif action=='auto_start':
                    source=data.get('source','usb'); value=data.get('value','')
                    if source=='usb' and value not in {p['device'] for p in usb_camera.ports()}:
                        raise ValueError('XIAO カメラの USB を選択してください')
                    if source not in ('usb','wifi','mac'): raise ValueError('カメラを選んでください')
                    if auto_thread is not None and auto_thread.is_alive():
                        if auto.get('status')!='paused' or auto_camera!=(source,value):
                            raise ValueError('再開時は元のカメラを選んでください。新しい対局では停止完了を待ってください')
                        auto.update(status='settling',message='カメラを再開しています',reset_stability=True)
                    else:
                        auto_stop=threading.Event();auto_camera=(source,value)
                        auto={'status':'settling','message':'カメラを準備しています','candidates':[]}
                        auto_thread=threading.Thread(target=automatic_game,args=(source,value,auto_stop),daemon=True)
                        auto_thread.start()
                elif action=='auto_stop':
                    auto.update(status='paused',candidates=[],message='自動検知を一時停止しました')
                elif action=='auto_select':
                    if auto.get('status')!='ambiguous' or auto.get('revision')!=game_revision:
                        raise ValueError('確認する指し手がありません')
                    usi=data.get('usi')
                    if usi not in {x['usi'] for x in auto.get('candidates',[])}:
                        raise ValueError('表示された候補から選んでください')
                    move=shogi.Move.from_usi(usi)
                    if move not in board.legal_moves: raise ValueError('局面が変わりました')
                    board.push(move); game_revision+=1; stage_ai()
                    auto.update(status='robot_blocked',last_human=usi,candidates=[],
                                message='人の手を記録しました。実機動作は未検証のため停止中です。')
                elif action=='auto_retry':
                    if auto.get('status')!='ambiguous': raise ValueError('確認待ちの候補がありません')
                    auto.update(status='settling',candidates=[],message='盤とマーカーを確認して、もう一度撮影します')
                elif action=='usb_ports': out['ports']=usb_camera.ports()
                elif action=='teaching_ports': out['ports']=teaching_ports()
                elif action=='capture':
                    frame=jpeg(data.get('url',''))
                    frame_id=secrets.token_urlsafe(12);out['frame_id']=frame_id
                    ok,encoded=cv2.imencode('.jpg',frame)
                    if not ok: raise ValueError('画像の変換に失敗しました')
                    out['image']=base64.b64encode(encoded).decode()
                elif action=='capture_usb':
                    data_bytes=usb_camera.read_jpeg(data.get('port',''))
                    frame=cv2.imdecode(np.frombuffer(data_bytes,np.uint8),cv2.IMREAD_COLOR)
                    if frame is None or frame.size>20_000_000: raise ValueError('USB 画像を読み取れません')
                    frame_id=secrets.token_urlsafe(12);out['frame_id']=frame_id
                    out['image']=base64.b64encode(data_bytes).decode()
                elif action=='capture_mac':
                    frame=mac_camera.grab()
                    frame_id=secrets.token_urlsafe(12);out['frame_id']=frame_id
                    ok,encoded=cv2.imencode('.jpg',frame)
                    if not ok: raise ValueError('画像の変換に失敗しました')
                    out['image']=base64.b64encode(encoded).decode()
                elif action=='baseline':
                    if frame is None: raise ValueError('先に画像を取得してください')
                    if not frame_id or data.get('frame_id')!=frame_id: raise ValueError('画像が更新されました。再取得して四隅を指定してください')
                    corners=data.get('corners')
                    if reference_corners is None:
                        reference_corners=[list(map(float,p)) for p in corners]
                    else:
                        same_view(reference_corners, corners)
                    # Pixel shifts alone cannot establish robot coordinates.
                    baseline=normalized(frame,corners)
                elif action=='lock_board':
                    pts=data.get('corners') or corners
                    if not pts: raise ValueError('先に四隅を指定してください')
                    corners=pts
                    reference_corners=[list(map(float,p)) for p in pts]
                    reset_pose()
                elif action=='detect_corners':
                    if frame is None: raise ValueError('先に画像を取得してください')
                    out['corners']=detect_corners(frame)
                elif action=='arm_live':
                    if data.get('confirmed') is not True: raise ValueError('実機を動かすには確認が必要です')
                    if data.get('live'):
                        raise ValueError('実機動作は未検証です。関節対応・盤座標・把持と停止の実機検証が必要です')
                    robot_live=False
                elif action=='commit_vision':
                    if pending or board.turn==ai_side:
                        raise ValueError('AI の手番です。相手の指し手は入力できません')
                    if frame is None or baseline is None: raise ValueError('先に比較元を設定してください')
                    if not frame_id or data.get('frame_id')!=frame_id: raise ValueError('画像が更新されました。再取得して四隅を指定してください')
                    ranked=candidates(baseline,normalized(frame,data.get('corners')))
                    if not ranked: raise ValueError('候補がありません')
                    if len(ranked)>1 and ranked[0]['score']-ranked[1]['score']<3:
                        out['candidates']=ranked
                        raise ValueError('候補が分かれています。手を選んで確定してください')
                    move=shogi.Move.from_usi(ranked[0]['usi'])
                    if move not in board.legal_moves: raise ValueError('この局面では合法手ではありません')
                    board.push(move); baseline=None; game_revision+=1
                    stage_ai(); out['accepted']=ranked[0]['usi']
                elif action=='compare':
                    if frame is None or baseline is None: raise ValueError('先に比較元を設定してください')
                    if not frame_id or data.get('frame_id')!=frame_id: raise ValueError('画像が更新されました。再取得して四隅を指定してください')
                    out['candidates']=candidates(baseline,normalized(frame,data.get('corners')))
                elif action=='move':
                    if pending or board.turn==ai_side:
                        raise ValueError('AI の手番です。相手の指し手は入力できません')
                    move=shogi.Move.from_usi(data.get('usi',''))
                    if move not in board.legal_moves: raise ValueError('この局面では合法手ではありません')
                    board.push(move); baseline=None;game_revision+=1
                    stage_ai()
                elif action=='reset':
                    side=data.get('ai_side','white')
                    if side not in ('black','white'): raise ValueError('AI の手番を選択してください')
                    ai_side=shogi.BLACK if side=='black' else shogi.WHITE
                    auto_stop.set();auto={'status':'idle'}
                    board=shogi.Board(); baseline=None; pending=None;engine_error=None;game_revision+=1
                    robot_job={'status':'idle'}; reset_pose()
                    stage_ai()
                elif action=='suggest':
                    if board.turn!=ai_side: raise ValueError('相手の手番です')
                    if pending is None: stage_ai()
                elif action=='confirm_ai':
                    if board.turn!=ai_side: raise ValueError('確認待ちの AI の指し手がありません')
                    if data.get('confirmed') is not True: raise ValueError('盤と持ち駒を確認してください')
                    usi=pending['usi'] if pending else data.get('usi')
                    if pending and data.get('usi')!=pending['usi']: raise ValueError('盤と持ち駒を確認してください')
                    if not usi: raise ValueError('動かした手を入力してください')
                    move=shogi.Move.from_usi(usi)
                    if move not in board.legal_moves: raise ValueError('局面が変わりました。確認し直してください')
                    board.push(move);pending=None;baseline=None;game_revision+=1
                elif action in ('simulate_ai','auto_move'):
                    if not pending or board.turn!=ai_side: raise ValueError('先に AI の手を決めてください')
                    if action=='simulate_ai' and sim_job['status']=='running': raise ValueError('シミュレーションを実行中です')
                    if action=='auto_move' and robot_job.get('status')=='running': raise ValueError('アーム動作中です')
                    if pending['drop']:
                        if action!='auto_move': raise ValueError('持ち駒の打ちは、このシミュレーションでは未対応です')
                        usi=pending['usi'];source,destination=pending.get('source'),pending['destination']
                        sim_move=dict(pending)
                        sim_move['board_side']='black' if ai_side==shogi.BLACK else 'white'
                        sim_job={'status':'finished','usi':usi,'applied':False,
                                 'result':{'success':False,'sim_only':True,'digital_only':True,
                                           'reason':'drop_not_simulated'},
                                 'source':source,'destination':destination,'revision':game_revision}
                        robot_job={'status':'running','usi':usi,'live':robot_live}
                        threading.Thread(target=execute_robot,args=(sim_move,robot_live,True),daemon=True).start()
                    else:
                        sim_move=dict(pending)
                        sim_move['board_side']='black' if ai_side==shogi.BLACK else 'white'
                        sim_move['piece_yaw_deg']=piece_yaw_deg(sim_move['board_side'])
                        exclude=(pending['destination'],) if pending['capture'] else ()
                        sim_move['obstacles']=simulation_obstacles(board,pending['source'],ai_side,exclude)
                        usi,source,destination=pending['usi'],pending['source'],pending['destination']
                        sfen,rev=board.sfen(),game_revision
                        if action=='auto_move':
                            robot_job={'status':'running','usi':usi,'live':robot_live}
                            threading.Thread(target=execute_robot,args=(sim_move,robot_live,True),daemon=True).start()
                        else:
                            sim_job={'status':'running','usi':usi,'sfen':sfen,'revision':rev,'applied':False,
                                     'source':source,'destination':destination}
                            threading.Thread(target=simulate_pending,args=(sim_move,sfen,rev,False),daemon=True).start()
                elif action=='observe':
                    if robot_job.get('status')=='running': raise ValueError('アーム動作中です')
                    robot_job={'status':'running','live':robot_live}
                    threading.Thread(target=go_observe,args=(robot_live,),daemon=True).start()
                elif action=='snap_observe':
                    if data.get('confirmed') is not True: raise ValueError('観測姿勢の記録には確認が必要です')
                    if not robot_live: raise ValueError('実機チェックを入れてください')
                    out['offsets']=Arm().snap_observe()
                elif action=='controller':
                    script=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101/syodo/Followerコントローラー.command')
                    if not script.is_file(): raise ValueError('Follower コントローラーが見つかりません')
                    if not Path.home().joinpath('Documents/lerobot-hw/.venv/bin/python').is_file():
                        raise ValueError('既存 Follower の Python 環境が見つかりません')
                    if controller_process is None or controller_process.poll() is not None:
                        controller_process=subprocess.Popen([str(script)], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else: raise ValueError('不明な操作')
                out.update(state())
            self.respond(out)
        except Exception as exc:
            self.respond({'error':str(exc)},400)
    def log_message(self,*args): pass


def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    url=f'http://127.0.0.1:{server.server_port}/{TOKEN}'
    print('将棋 GUI:',url,flush=True);webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__': main()
