"""Dry-run the same IK→Follower path the GUI uses. No hardware."""
import http.client
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import shogi
import server
from board_map import reset_pose, set_pose, BOARD_X
from move_plan import build_plan


class RobotPathTest(unittest.TestCase):
    def setUp(self):
        reset_pose()
        server.robot_job={'status':'idle'}
        server.pending=None
        server.sim_job={'status':'idle'}
    def tearDown(self):
        reset_pose()
    def _play(self, move):
        server.execute_robot(move, live=False, apply=False)
        job=server.robot_job
        self.assertEqual(job.get('status'),'finished', job)
        self.assertFalse(job['robot']['live'])
        phases=[c['phase'] for c in job['robot']['commands']]
        self.assertIn('descend',phases)
        self.assertIn('place',phases)
        self.assertEqual(phases[-1],'observe')
        return job
    def test_move_capture_drop_and_promote_dry_run_on_the_long_side(self):
        set_pose(x=BOARD_X,y=.01,yaw=0)
        move=self._play({'board_side':'white','source':'5c','destination':'5d','capture':False,'drop':False,'promotion':False,'usi':'5c5d'})
        self.assertEqual(move['legs'],['move'])
        capture=self._play({'board_side':'white','source':'5c','destination':'5d','capture':True,'drop':False,'promotion':False,'captured_promoted':False,'usi':'5c5d'})
        self.assertEqual(capture['legs'],['captured_to_stand','own_to_board'])
        drop=self._play({'board_side':'white','destination':'5e','drop':True,'capture':False,'promotion':False,'usi':'P*5e'})
        self.assertEqual(drop['legs'],['drop'])
        promo=self._play({'board_side':'white','source':'5f','destination':'5g','capture':False,'drop':False,'promotion':True,'usi':'5f5g+'})
        self.assertEqual(promo['legs'],['move'])
        self.assertIn('flip',[c['phase'] for c in promo['robot']['commands']])
        self.assertIn('unwind',[c['phase'] for c in promo['robot']['commands']])
    def test_http_auto_move_runs_the_real_arm_path_for_a_reachable_pawn(self):
        server.board=shogi.Board(); server.pending=None; server.ai_side=shogi.WHITE
        server.engine_error=None; server.sim_job={'status':'idle'}; server.game_revision=0
        server.robot_job={'status':'idle'}; server.robot_live=False
        httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=httpd.serve_forever,daemon=True); thread.start()
        def post(action,**kwargs):
            h=f'127.0.0.1:{httpd.server_port}'
            c=http.client.HTTPConnection('127.0.0.1',httpd.server_port,timeout=20)
            c.request('POST','/api',json.dumps({'action':action,**kwargs}),{'Host':h,'Origin':'http://'+h,'X-Token':server.TOKEN,'Content-Type':'application/json'})
            r=c.getresponse(); body=json.loads(r.read()); c.close(); return r.status,body
        try:
            self.assertEqual(post('arm_live',live=True,confirmed=True)[0],400)
            with patch.object(server,'engine_move',return_value='3c3d'):
                self.assertEqual(post('move',usi='7g7f')[0],200)
            self.assertEqual(post('auto_move')[0],200)
            deadline=time.monotonic()+30
            while time.monotonic()<deadline and server.robot_job.get('status')=='running':
                time.sleep(.05)
            self.assertEqual(server.robot_job.get('status'),'finished',server.robot_job)
            self.assertFalse(server.robot_job['robot']['live'])
            self.assertIsNotNone(server.pending)
            self.assertIsNone(server.board.piece_at(shogi.D3))
        finally:
            httpd.shutdown(); httpd.server_close(); thread.join()
    def test_http_auto_move_capture_promote_then_drop(self):
        b=shogi.Board('4k4/9/9/9/9/4s4/4P4/9/4K4 w B 1')
        server.board=b; server.ai_side=shogi.WHITE; server.pending=build_plan(b,'5f5g+')
        server.engine_error=None; server.sim_job={'status':'idle'}; server.game_revision=0
        server.robot_job={'status':'idle'}; server.robot_live=False
        httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=httpd.serve_forever,daemon=True); thread.start()
        def post(action,**kwargs):
            h=f'127.0.0.1:{httpd.server_port}'
            c=http.client.HTTPConnection('127.0.0.1',httpd.server_port,timeout=20)
            c.request('POST','/api',json.dumps({'action':action,**kwargs}),{'Host':h,'Origin':'http://'+h,'X-Token':server.TOKEN,'Content-Type':'application/json'})
            r=c.getresponse(); body=json.loads(r.read()); c.close(); return r.status,body
        def wait():
            deadline=time.monotonic()+60
            while time.monotonic()<deadline and server.robot_job.get('status')=='running':
                time.sleep(.05)
            return server.robot_job
        try:
            self.assertEqual(post('auto_move')[0],200)
            job=wait()
            self.assertEqual(job.get('status'),'finished',job)
            self.assertEqual(job.get('legs'),['captured_to_stand','own_to_board'])
            phases=[c['phase'] for c in job['robot']['commands']]
            self.assertIn('flip',phases)
            self.assertIn('unwind',phases)
            self.assertEqual(phases[-1],'observe')
            self.assertIsNotNone(server.pending)
            self.assertEqual(server.board.piece_at(shogi.SQUARE_NAMES.index('5g')).symbol(),'P')
            server.board.push_usi('5f5g+')  # Set up the next case; not a hardware result.
            server.board.push(next(iter(server.board.legal_moves)))
            server.pending=build_plan(server.board,'P*5e')
            server.robot_job={'status':'idle'}
            self.assertEqual(post('auto_move')[0],200)
            job=wait()
            self.assertEqual(job.get('status'),'finished',job)
            self.assertEqual(job.get('legs'),['drop'])
            self.assertIsNotNone(server.pending)
            self.assertIsNone(server.board.piece_at(shogi.SQUARE_NAMES.index('5e')))
        finally:
            httpd.shutdown(); httpd.server_close(); thread.join()
    def test_http_corner_nudge_shifts_the_planned_square(self):
        import numpy as np
        from motion import legs
        server.frame=np.zeros((540,540,3),np.uint8); server.frame_id='f'
        server.reference_corners=None; server.corners=None; reset_pose()
        httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=httpd.serve_forever,daemon=True); thread.start()
        def post(action,**kwargs):
            h=f'127.0.0.1:{httpd.server_port}'
            c=http.client.HTTPConnection('127.0.0.1',httpd.server_port,timeout=20)
            c.request('POST','/api',json.dumps({'action':action,**kwargs}),{'Host':h,'Origin':'http://'+h,'X-Token':server.TOKEN,'Content-Type':'application/json'})
            r=c.getresponse(); body=json.loads(r.read()); c.close(); return r.status,body
        ref=[[100,80],[500,80],[500,500],[100,500]]
        moved=[[108,80],[508,80],[508,500],[108,500]]
        try:
            self.assertEqual(post('lock_board',corners=ref)[0],200)
            before=legs({'board_side':'white','source':'5c','destination':'5d','capture':False,'drop':False,'promotion':False})[0]['source']
            self.assertEqual(post('baseline',corners=moved,frame_id='f')[0],200)
            after=legs({'board_side':'white','source':'5c','destination':'5d','capture':False,'drop':False,'promotion':False})[0]['source']
            self.assertEqual(after,before)
        finally:
            httpd.shutdown(); httpd.server_close(); thread.join(); reset_pose()
    def test_observe_offsets_shift_follower_command(self):
        import tempfile
        from robot_arm import NAMES, OBSERVE, offsets_from_present, q_to_follower, save_offsets
        present={n:10.0 for n in NAMES}
        off=offsets_from_present(present)
        self.assertAlmostEqual(off['shoulder_pan'],-10.0)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'follower_offsets.json'
            with patch('robot_arm.OFFSETS_PATH',path):
                save_offsets(off)
                cmd=q_to_follower(OBSERVE['joints_rad'],OBSERVE['gripper'])
                self.assertAlmostEqual(cmd['shoulder_pan'],10.0,places=5)
    def test_snap_observe_requires_live_and_confirm(self):
        server.robot_live=False
        httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=httpd.serve_forever,daemon=True); thread.start()
        def post(action,**kwargs):
            h=f'127.0.0.1:{httpd.server_port}'
            c=http.client.HTTPConnection('127.0.0.1',httpd.server_port,timeout=20)
            c.request('POST','/api',json.dumps({'action':action,**kwargs}),{'Host':h,'Origin':'http://'+h,'X-Token':server.TOKEN,'Content-Type':'application/json'})
            r=c.getresponse(); body=json.loads(r.read()); c.close(); return r.status,body
        try:
            self.assertEqual(post('snap_observe',confirmed=True)[0],400)
            server.robot_live=True
            self.assertEqual(post('snap_observe')[0],400)
        finally:
            server.robot_live=False
            httpd.shutdown(); httpd.server_close(); thread.join()


if __name__=='__main__':
    unittest.main()
