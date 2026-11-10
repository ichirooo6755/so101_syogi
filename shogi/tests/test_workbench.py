import http.client
import json
import sys
import threading
import unittest
from pathlib import Path

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import server
from board_map import sim_square, BOARD_X, reset_pose


class WorkbenchTest(unittest.TestCase):
    def setUp(self):
        server.board=server.shogi.Board()
        server.baseline=None
        server.ai_side=server.shogi.WHITE
        server.pending=None
        server.engine_error=None
    def test_legal_image_candidate(self):
        old=np.zeros((540,540,3),dtype=np.uint8)
        new=old.copy()
        # USI 7g7f changes x=2, rows g/f. Add more than global lighting offset.
        new[368:412,128:172]=255
        new[308:352,128:172]=255
        self.assertEqual(server.candidates(old,new)[0]['usi'],'7g7f')
    def test_corner_validation(self):
        img=np.zeros((600,600,3),dtype=np.uint8)
        self.assertEqual(server.normalized(img,[[10,10],[590,10],[590,590],[10,590]]).shape,(540,540,3))
        with self.assertRaises(ValueError): server.normalized(img,[[10,10],[590,590],[590,10],[10,590]])
    def test_simulated_board_coordinates_follow_file_width_and_rank_length(self):
        reset_pose()
        self.assertAlmostEqual(sim_square('5e')[0],BOARD_X)
        self.assertAlmostEqual(sim_square('5e')[1],0.)
        self.assertAlmostEqual(sim_square('1e')[0]-sim_square('9e')[0],8*.330/9)
        self.assertAlmostEqual(sim_square('5a')[1]-sim_square('5i')[1],8*.360/9)
        self.assertLess(sim_square('5i','black')[1],sim_square('5a','black')[1])
        self.assertLess(sim_square('5a','white')[1],sim_square('5i','white')[1])
        for square in ('1a','5e','9i'):
            black=sim_square(square,'black');white=sim_square(square,'white')
            self.assertAlmostEqual(black[0]+white[0],2*BOARD_X)
            self.assertAlmostEqual(black[1]+white[1],0.)
        with self.assertRaises(ValueError):sim_square('0z')
        with self.assertRaises(ValueError):sim_square('5e','invalid')
    def test_engine_returns_legal_move(self):
        move=server.shogi.Move.from_usi(server.engine_move())
        self.assertIn(move,server.board.legal_moves)
    def test_api_requires_origin_and_rejects_illegal_move(self):
        httpd=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        t=threading.Thread(target=httpd.serve_forever,daemon=True);t.start()
        host=f'127.0.0.1:{httpd.server_port}'
        try:
            def post(data,origin):
                c=http.client.HTTPConnection('127.0.0.1',httpd.server_port,timeout=10)
                c.request('POST','/api',json.dumps(data),{'Host':host,'Origin':origin,'X-Token':server.TOKEN,'Content-Type':'application/json'})
                r=c.getresponse();body=json.loads(r.read());c.close();return r.status,body
            self.assertEqual(post({'action':'state'},'http://evil.example')[0],403)
            self.assertEqual(post({'action':'move','usi':'7g7e'},'http://'+host)[0],400)
            status,body=post({'action':'move','usi':'7g7f'},'http://'+host)
            self.assertEqual(status,200);self.assertEqual(body['turn'],'後手')
        finally:
            httpd.shutdown();httpd.server_close();t.join()

if __name__=='__main__': unittest.main()
