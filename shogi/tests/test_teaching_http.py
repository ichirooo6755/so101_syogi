"""Exercise the teaching flow through the same local API as the GUI."""
import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import server
import teach_store


class TeachingHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        server.auto={'status':'idle'};server.robot_job={'status':'idle'};server.teach_session=None
        self.httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.thread=threading.Thread(target=self.httpd.serve_forever,daemon=True);self.thread.start()
        begin,add=teach_store.begin,teach_store.add_capture
        self.start_patch=patch.object(teach_store,'begin',side_effect=lambda s,side,pose,mode='leader',operation='pick',issue=None:begin(s,side,pose,self.temp.name,mode,operation,issue))
        self.add_patch=patch.object(teach_store,'add_capture',side_effect=lambda session,capture:add(session,capture,self.temp.name))
        self.start_patch.start();self.add_patch.start()

    def tearDown(self):
        self.start_patch.stop();self.add_patch.stop()
        self.httpd.shutdown();self.httpd.server_close();self.thread.join()

    def post(self,action,**values):
        host=f'127.0.0.1:{self.httpd.server_port}'
        conn=http.client.HTTPConnection('127.0.0.1',self.httpd.server_port,timeout=10)
        conn.request('POST','/api',json.dumps({'action':action,**values}),
                     {'Host':host,'Origin':'http://'+host,'X-Token':server.TOKEN,'Content-Type':'application/json'})
        response=conn.getresponse();data=json.loads(response.read());conn.close()
        return response.status,data

    def test_records_four_snapshots_without_changing_game(self):
        before=server.board.sfen()
        capture={'calibration_verified':True,'calibration_sha256':'a'*64,'follower_usb_id':'f'*64,
                 'positions':{name:(20 if name=='gripper' else 0.) for name in teach_store.NAMES}}
        status,data=self.post('teach_begin',square='9e',side='white',mode='manual')
        self.assertEqual(status,200);ident=data['teaching']['id']
        with patch.object(server,'capture_teaching_position',return_value=capture) as read:
            self.assertEqual(self.post('teach_capture',id='stale')[0],400)
            for _ in range(4):
                status,data=self.post('teach_capture',id=ident)
                self.assertEqual(status,200)
            self.assertEqual(read.call_count,4)
        self.assertEqual(data['teaching']['status'],'recorded_unverified')
        self.assertEqual(server.board.sfen(),before)

    def test_teaching_rejected_while_automatic_game_running(self):
        server.auto={'status':'waiting'}
        status,_=self.post('teach_begin',square='9e',side='white')
        self.assertEqual(status,400)
        self.assertIsNone(server.teach_session)

    def test_leader_mode_requires_two_ports_and_saves_both_measurements(self):
        positions={n:(20 if n=='gripper' else 0.) for n in teach_store.NAMES}
        capture={'positions':positions,'calibration_verified':True,'calibration_sha256':'a'*64,'follower_usb_id':'f'*64,
                 'leader_positions':positions,'leader_calibration_verified':True,'leader_calibration_sha256':'b'*64,
                 'leader_usb_id':'e'*64}
        status,data=self.post('teach_begin',square='9e',side='white',mode='leader')
        self.assertEqual(status,200);ident=data['teaching']['id']
        with patch.object(server,'capture_teaching_position',return_value=capture) as read:
            self.assertEqual(self.post('teach_capture',id=ident,follower_port='/dev/cu.follower')[0],400)
            status,data=self.post('teach_capture',id=ident,follower_port='/dev/cu.follower',leader_port='/dev/cu.leader')
        self.assertEqual(status,200)
        read.assert_called_once_with('/dev/cu.follower','/dev/cu.leader')
        self.assertEqual(data['teaching']['recorded'],1)
        self.assertEqual(server.teach_session['samples'][0]['leader_positions'],positions)

    def test_teaching_start_retains_matching_failure_context(self):
        server.pending={'usi':'7g7f','board_side':'black','teach_suggestions':[{'square':'7f','operation':'place',
                            'stage':'place','evidence':'ik_residual','role':'move','origin':'plan'}]}
        status,data=self.post('teach_begin',square='7f',side='black',mode='leader',operation='place')
        self.assertEqual(status,200)
        self.assertEqual(data['teaching']['operation'],'place')
        self.assertEqual(server.teach_session['failure_context']['usi'],'7g7f')
        self.assertEqual(server.teach_session['failure_context']['square'],'7f')

    def test_learned_failure_can_be_selected_without_a_pending_move(self):
        server.pending=None
        candidate={'square':'9c','operation':'pick','origin':'learned_simulation','simulated_move':'9c9b'}
        with patch.object(server,'learned_teaching_candidates',return_value=[candidate]):
            status,data=self.post('teach_begin',square='9c',side='white',mode='leader',operation='pick')
        self.assertEqual(status,200)
        self.assertEqual(data['teaching']['square'],'9c')
        self.assertEqual(server.teach_session['failure_context']['origin'],'learned_simulation')
        self.assertEqual(server.teach_session['failure_context']['simulated_move'],'9c9b')


if __name__=='__main__': unittest.main()
