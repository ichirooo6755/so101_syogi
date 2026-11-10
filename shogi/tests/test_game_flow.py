import http.client
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import server
from move_plan import build_plan
import shogi


class GameFlowTest(unittest.TestCase):
    def setUp(self):
        server.board=shogi.Board(); server.pending=None; server.ai_side=shogi.WHITE
        server.baseline=None;server.engine_error=None;server.sim_job={'status':'idle'};server.game_revision=0
        server.robot_job={'status':'idle'};server.robot_live=False;server.reference_corners=None
        server.reset_pose()
        self.httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.thread=threading.Thread(target=self.httpd.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.httpd.shutdown();self.httpd.server_close();self.thread.join()
    def post(self,action,**kwargs):
        h=f'127.0.0.1:{self.httpd.server_port}'
        c=http.client.HTTPConnection('127.0.0.1',self.httpd.server_port,timeout=20)
        c.request('POST','/api',json.dumps({'action':action,**kwargs}),{'Host':h,'Origin':'http://'+h,'X-Token':server.TOKEN,'Content-Type':'application/json'})
        r=c.getresponse(); body=json.loads(r.read());c.close();return r.status,body
    def test_opponent_move_triggers_only_ai_move_and_waits_for_physical_confirmation(self):
        with patch.object(server,'engine_move',return_value='3c3d'):
            status,d=self.post('move',usi='7g7f')
        self.assertEqual(status,200);self.assertEqual(d['pending']['usi'],'3c3d')
        self.assertEqual(d['turn'],'後手');self.assertFalse(d['pending']['ready_to_execute'])
        self.assertEqual(self.post('move',usi='3c3d')[0],400)
        self.assertEqual(self.post('confirm_ai',usi='3c3d',confirmed=False)[0],400)
        self.assertEqual(self.post('confirm_ai',usi='8c8d',confirmed=True)[0],400)
        status,d=self.post('confirm_ai',usi='3c3d',confirmed=True)
        self.assertEqual(status,200);self.assertIsNone(d['pending']);self.assertEqual(d['turn'],'先手')
    def test_engine_failure_does_not_undo_opponent_move(self):
        with patch.object(server,'engine_move',side_effect=ValueError('engine offline')):
            status,d=self.post('move',usi='7g7f')
        self.assertEqual(status,200);self.assertEqual(d['turn'],'後手');self.assertEqual(d['engine_error'],'engine offline')
        with patch.object(server,'engine_move',return_value='3c3d'):
            self.assertEqual(self.post('suggest')[1]['pending']['usi'],'3c3d')
    def test_unreachable_engine_lets_human_place_the_ai_move(self):
        with patch.object(server,'engine_move',return_value=None):
            status,d=self.post('move',usi='7g7f')
        self.assertEqual(status,200);self.assertIsNone(d['pending'])
        self.assertIn('指し手がありません',d['engine_error'])
        status,d=self.post('confirm_ai',usi='3c3d',confirmed=True)
        self.assertEqual(status,200);self.assertIsNone(d['pending']);self.assertEqual(d['turn'],'先手')
    def test_ai_can_go_first(self):
        with patch.object(server,'engine_move',return_value='7g7f'):
            status,d=self.post('reset',ai_side='black')
        self.assertEqual(status,200);self.assertEqual(d['pending']['usi'],'7g7f');self.assertEqual(d['turn'],'先手')
    def test_real_engine_generates_ai_response_after_opponent_move(self):
        status,d=self.post('move',usi='7g7f')
        self.assertEqual(status,200)
        self.assertIsNotNone(d['pending'],d.get('engine_error'))
        self.assertIn(shogi.Move.from_usi(d['pending']['usi']),server.board.legal_moves)
        self.assertEqual(server.board.turn,shogi.WHITE)
    def test_usb_capture_enters_same_image_pipeline(self):
        import cv2
        import numpy as np
        ok,jpeg=cv2.imencode('.jpg',np.zeros((30,30,3),dtype=np.uint8))
        self.assertTrue(ok)
        with patch.object(server.usb_camera,'read_jpeg',return_value=jpeg.tobytes()):
            status,body=self.post('capture_usb',port='/dev/cu.example')
        self.assertEqual(status,200);self.assertIn('image',body);self.assertEqual(server.frame.shape,(30,30,3))
        frame_id=body['frame_id']
        points=[[1,1],[28,1],[28,28],[1,28]]
        self.assertEqual(self.post('baseline',corners=points,frame_id=frame_id)[0],200)
        with patch.object(server.usb_camera,'read_jpeg',return_value=jpeg.tobytes()):
            self.post('capture_usb',port='/dev/cu.example')
        self.assertEqual(self.post('compare',corners=points,frame_id=frame_id)[0],400)
    def test_mac_capture_follow_updates_pose_from_detected_corners(self):
        import cv2
        import numpy as np
        img=np.full((400,400,3),210,np.uint8)
        cv2.rectangle(img,(60,50),(340,350),(40,90,160),-1)
        cv2.rectangle(img,(70,60),(330,340),(80,140,200),2)
        moved=cv2.warpAffine(img,np.float32([[1,0,8],[0,1,0]]),(400,400),borderValue=(210,210,210))
        with patch.object(server.mac_camera,'grab',return_value=img):
            status,body=self.post('capture_mac')
        self.assertEqual(status,200);self.assertIn('image',body)
        status,d=self.post('detect_corners')
        self.assertEqual(status,200)
        self.assertEqual(self.post('lock_board',corners=d['corners'])[0],200)
        before=server.board_pose()['x']
        with patch.object(server.mac_camera,'grab',return_value=moved):
            status,body=self.post('capture_mac')
        self.assertEqual(status,200)
        status,d=self.post('detect_corners')
        self.assertEqual(self.post('baseline',corners=d['corners'],frame_id=body['frame_id'])[0],200)
        self.assertEqual(server.board_pose()['x'],before)
    def test_capture_promotion_and_drop_plans(self):
        b=shogi.Board()
        for usi in ['7g7f','3c3d']: b.push_usi(usi)
        p=build_plan(b,'8h2b+')
        self.assertTrue(p['capture']);self.assertTrue(p['promotion']);self.assertEqual(p['source'],'8h')
        self.assertIn('駒台',p['tasks'][0]);self.assertIn('裏返',p['tasks'][2])
        b.push_usi('8h2b+')
        b.push(next(iter(b.legal_moves)))
        drop=next(m for m in b.legal_moves if m.drop_piece_type==shogi.BISHOP)
        p=build_plan(b,drop.usi());self.assertTrue(p['drop']);self.assertIsNone(p['source']);self.assertIn('駒台',p['tasks'][0])
    def test_simulation_requires_pending_move_and_rejects_drops(self):
        self.assertEqual(self.post('simulate_ai')[0],400)
        server.board.push_usi('7g7f')
        server.pending={'capture':False,'drop':True,'promotion':False,'usi':'P*5e'}
        status,body=self.post('simulate_ai')
        self.assertEqual(status,400)
        self.assertIn('未対応',body['error'])
    def test_capture_preview_runs_two_independent_transfers_without_confirming_move(self):
        server.board.push_usi('7g7f');server.board.push_usi('3c3d')
        server.ai_side=shogi.BLACK;server.pending=build_plan(server.board,'8h2b+')
        before=server.board.sfen()
        status,result=self.post('simulate_ai')
        self.assertEqual(status,200)
        deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            time.sleep(.15);result=self.post('state')[1]
            if result['simulation']['status']!='running':break
        sim=result['simulation'];self.assertEqual(sim['status'],'finished',sim)
        preview=sim['result'];self.assertFalse(preview['success'])
        self.assertEqual(preview['reason'],'capture_preview_only')
        self.assertTrue(preview['captured_to_stand']['sim_only'])
        self.assertTrue(preview['own_piece_to_board']['sim_only'])
        self.assertNotIn('trace',preview['captured_to_stand'])
        self.assertEqual(server.board.sfen(),before)
        self.assertEqual(result['pending']['usi'],'8h2b+')
    def test_simulation_worker_is_offline_and_result_becomes_stale_on_reset(self):
        with patch.object(server,'engine_move',return_value='7c7d'):
            self.assertEqual(self.post('move',usi='7g7f')[0],200)
        status,result=self.post('simulate_ai')
        self.assertEqual(status,200);self.assertEqual(result['simulation']['status'],'running')
        deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            time.sleep(.15)
            result=self.post('state')[1]
            if result['simulation']['status']!='running':break
        sim=result['simulation']
        self.assertEqual(sim['status'],'finished',sim)
        self.assertTrue(sim['result']['sim_only']);self.assertFalse(sim['stale'])
        self.assertEqual(sim['usi'],'7c7d')
        self.assertEqual(sim['result']['assumptions']['obstacle_mode'],'position_snapshot')
        self.assertEqual(sim['result']['assumptions']['obstacle_count'],39)
        self.assertEqual(sim['result']['assumptions']['piece_initial_yaw_deg'],90)
        self.assertEqual(sim['result']['assumptions']['layout'],'robot_and_human_opposite_ends')
        for actual,expected in zip(sim['result']['source_m'][:2],server.sim_square('7c','white')):
            self.assertAlmostEqual(actual,expected)
        status,result=self.post('reset',ai_side='white')
        self.assertEqual(status,200);self.assertTrue(result['simulation']['stale'])
    def test_simulated_board_uses_current_piece_positions_and_both_orientations(self):
        server.board.push_usi('7g7f')
        items=server.simulation_obstacles(server.board,'3c',shogi.WHITE)
        self.assertEqual(len(items),39)
        self.assertNotIn('3c',{p['square'] for p in items})
        by_square={p['square']:p for p in items}
        self.assertEqual(by_square['7f']['yaw_deg'],270)
        self.assertEqual(by_square['3a']['yaw_deg'],90)
        self.assertEqual(tuple(by_square['7f']['position_m']),server.sim_square('7f','white'))
        other_side=server.simulation_obstacles(server.board,'7f',shogi.BLACK)
        by_square={p['square']:p for p in other_side}
        self.assertEqual(by_square['3a']['yaw_deg'],90)
        self.assertEqual(by_square['5g']['yaw_deg'],-90)
        self.assertEqual(by_square['5g']['position_m'],server.sim_square('5g','black'))
    def test_dry_run_does_not_apply_the_board(self):
        with patch.object(server,'engine_move',return_value='3c3d'):
            self.assertEqual(self.post('move',usi='7g7f')[0],200)
        before=server.board.sfen()
        move={**server.pending,'board_side':'white'}
        with patch.object(server,'plan_leg',return_value={'waypoints':[{'phase':'x'}]}), \
             patch.object(server.Arm,'play',return_value={'live':False}):
            server.execute_robot(move,live=False,apply=True)
        self.assertFalse(server.robot_job['applied'])
        self.assertIsNotNone(server.pending)
        self.assertEqual(server.board.sfen(),before)
    def test_auto_move_ignores_a_stuck_simulation_job(self):
        with patch.object(server,'engine_move',return_value='3c3d'):
            self.assertEqual(self.post('move',usi='7g7f')[0],200)
        server.sim_job={'status':'running','usi':'stale'}
        def fake_robot(move, live=False, apply=False):
            with server.LOCK:
                server.robot_job={'status':'finished','usi':move.get('usi'),'applied':False,'live':live}
        with patch.object(server,'execute_robot',side_effect=fake_robot):
            self.assertEqual(self.post('auto_move')[0],200)
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and server.robot_job.get('status')=='running': time.sleep(.05)
        self.assertIsNotNone(server.pending)
    def test_drop_preview_does_not_claim_a_simulated_or_physical_success(self):
        b=shogi.Board()
        for usi in ['7g7f','3c3d']: b.push_usi(usi)
        b.push_usi('8h2b+')
        b.push(next(iter(b.legal_moves)))
        drop=next(m for m in b.legal_moves if m.drop_piece_type==shogi.BISHOP)
        server.board=b;server.ai_side=b.turn;server.pending=build_plan(b,drop.usi())
        def fake_robot(move, live=False, apply=False):
            with server.LOCK:
                server.robot_job={'status':'finished','usi':move.get('usi'),'applied':False,'live':live}
        with patch.object(server,'execute_robot',side_effect=fake_robot):
            status,d=self.post('auto_move')
        self.assertEqual(status,200)
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and server.robot_job.get('status')=='running': time.sleep(.05)
        self.assertFalse(server.sim_job.get('applied'))
        self.assertTrue(server.sim_job['result']['digital_only'])
        self.assertEqual(server.sim_job['result']['reason'],'drop_not_simulated')
        self.assertIsNotNone(server.pending)
        self.assertFalse(server.sim_succeeded({'reason':'capture_preview_only','captured_to_stand':{'success':True},'own_piece_to_board':{'success':True}}))
        self.assertFalse(server.sim_succeeded({'reason':'capture_preview_only','captured_to_stand':{'success':True},'own_piece_to_board':{'success':False}}))
    def test_auto_move_starts_robot_for_capture_and_observe_goes_home(self):
        server.board.push_usi('7g7f');server.board.push_usi('3c3d')
        server.ai_side=shogi.BLACK;server.pending=build_plan(server.board,'8h2b+')
        seen=[]
        def fake_robot(move, live=False, apply=False):
            seen.append((move.get('capture'),move.get('source'),move.get('destination'),live))
            with server.LOCK:
                if apply: server.apply_pending_move()
                server.robot_job={'status':'finished','usi':move.get('usi'),'legs':['captured_to_stand','own_to_board'],'live':live,'applied':True}
                server.sim_job={**server.sim_job,'applied':True}
        with patch.object(server,'execute_robot',side_effect=fake_robot):
            status,d=self.post('auto_move')
        self.assertEqual(status,200)
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and not seen: time.sleep(.05)
        self.assertEqual(seen,[(True,'8h','2b',False)])
        home=[]
        def fake_home(live=False):
            home.append(live)
            with server.LOCK: server.robot_job={'status':'finished','legs':['observe'],'live':live}
        with patch.object(server,'go_observe',side_effect=fake_home):
            status,d=self.post('observe')
        self.assertEqual(status,200)
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and not home: time.sleep(.05)
        self.assertEqual(home,[False])
    def test_auto_move_keeps_pending_when_arm_cannot_reach(self):
        with patch.object(server,'engine_move',return_value='3c3d'):
            self.assertEqual(self.post('move',usi='7g7f')[0],200)
        before=server.board.sfen()
        def fail_robot(move, live=False, apply=False):
            with server.LOCK: server.robot_job={'status':'error','usi':move.get('usi'),'error':'このマスへは腕が届きません','applied':False}
        with patch.object(server,'execute_robot',side_effect=fail_robot):
            self.assertEqual(self.post('auto_move')[0],200)
        deadline=time.monotonic()+2
        while time.monotonic()<deadline and server.robot_job.get('status')=='running': time.sleep(.05)
        self.assertEqual(server.board.sfen(),before)
        self.assertEqual(server.pending['usi'],'3c3d')
        self.assertEqual(self.post('confirm_ai',usi='3c3d',confirmed=True)[0],200)
        self.assertNotEqual(server.board.sfen(),before)

if __name__=='__main__': unittest.main()
