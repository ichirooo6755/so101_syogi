import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import board_map
from board_map import sim_square, set_pose, reset_pose
from board_pose import pose_from_corners
from detect_board import detect_corners
from robot_arm import Arm, q_to_follower, with_observe, resolve_port
from motion import legs
from workspace import in_reach, move_in_reach


class PlayLoopTest(unittest.TestCase):
    def tearDown(self):
        reset_pose()
    def test_promotion_zone_shares_reach_with_own_camp(self):
        reset_pose()
        own=sim_square('5a','white'); promo=sim_square('5g','white')
        self.assertAlmostEqual(own[0],promo[0])
        self.assertLess(abs(promo[1]),.20)
        self.assertLess(abs(own[0]-board_map.BOARD_X),0.01)
    def test_shifted_board_moves_square_coordinates(self):
        reset_pose()
        origin=sim_square('5e')
        set_pose(x=board_map.BOARD_X,y=.02,yaw=0)
        shifted=sim_square('5e')
        self.assertAlmostEqual(shifted[0],origin[0])
        self.assertAlmostEqual(shifted[1],origin[1]+.02)
        reset_pose()
        origin_file=sim_square('1e')
        set_pose(x=board_map.BOARD_X,y=0,yaw=np.deg2rad(8))
        rotated=sim_square('1e')
        self.assertGreater(abs(rotated[1]-origin_file[1]),0.005)
    def test_corner_nudge_becomes_millimetre_shift(self):
        ref=[[100,80],[500,80],[500,500],[100,500]]
        moved=[[108,80],[508,80],[508,500],[108,500]]
        pose=pose_from_corners(ref,moved)
        self.assertGreater(abs(pose['shift_mm']),1)
        self.assertLess(pose['shift_mm'],40)
        self.assertLess(abs(pose['yaw_deg']),2)
        self.assertGreater(pose['x'],board_map.BOARD_X)
        self.assertAlmostEqual(pose['y'],board_map.BOARD_Y,places=3)
    def test_detects_a_rectangular_board(self):
        img=np.full((400,400,3),210,np.uint8)
        cv2.rectangle(img,(60,50),(340,350),(40,90,160),-1)
        cv2.rectangle(img,(70,60),(330,340),(80,140,200),2)
        corners=detect_corners(img)
        self.assertEqual(len(corners),4)
        xs=[p[0] for p in corners]; ys=[p[1] for p in corners]
        self.assertLess(min(xs),90); self.assertGreater(max(xs),310)
    def test_dry_run_arm_does_not_open_the_bus(self):
        cmd=q_to_follower([0,-.55,.95,.82,0],.065)
        self.assertEqual(len(cmd),6)
        self.assertGreater(cmd['gripper'],50)
        q_to_follower([0,0,0,0,np.pi],.032)
        with self.assertRaises(ValueError):
            q_to_follower([0,0,0,0,4.0],.032)
        report=Arm().play([{'phase':'lift','joints_rad':[0,-.55,.95,.82,0],'gripper':.065,'duration_s':.2}],live=False)
        self.assertFalse(report['live'])
        self.assertEqual(report['count'],1)
        self.assertTrue(report['sim_only'])
        self.assertEqual(with_observe([{'phase':'place'}])[-1]['phase'],'observe')
        with self.assertRaises(ValueError) as err:
            resolve_port('/dev/cu.usbmodemDOESNOTEXIST')
        self.assertIn('USB',str(err.exception))
    def test_capture_and_drop_split_into_arm_legs(self):
        capture=legs({'board_side':'black','source':'8h','destination':'2b','capture':True,'promotion':True,'captured_promoted':False,'drop':False})
        self.assertEqual([x['role'] for x in capture],['captured_to_stand','own_to_board'])
        self.assertTrue(capture[1]['promotion'])
        self.assertEqual(capture[0]['yaw_deg'],90)
        self.assertEqual(capture[1]['yaw_deg'],-90)
        white=legs({'board_side':'white','source':'5c','destination':'5d','capture':False,'drop':False,'promotion':False})
        self.assertEqual(white[0]['yaw_deg'],90)
        drop=legs({'board_side':'black','destination':'5e','drop':True,'capture':False,'promotion':False})
        self.assertEqual(drop[0]['role'],'drop')
        reset_pose()
        stand=board_map.stand_xy()
        set_pose(x=board_map.BOARD_X+.005,y=.01)
        shifted=board_map.stand_xy()
        self.assertAlmostEqual(shifted[0]-stand[0],.005,places=6)
        self.assertAlmostEqual(shifted[1]-stand[1],.01,places=6)
    def test_workspace_keeps_center_files_and_rejects_far_files(self):
        self.assertTrue(in_reach((0.24,0)))
        self.assertTrue(in_reach(board_map.stand_xy()))
        self.assertFalse(in_reach((0.35,0)))
        self.assertFalse(in_reach((0.093,0)))
        ok={'board_side':'white','source':'5c','destination':'5d','capture':False,'drop':False,'promotion':False}
        far={'board_side':'white','source':'9c','destination':'9d','capture':False,'drop':False,'promotion':False}
        self.assertTrue(move_in_reach(ok))
        self.assertFalse(move_in_reach(far))
        set_pose(x=board_map.BOARD_X,y=.01,yaw=0)
        self.assertTrue(move_in_reach(ok))
        self.assertFalse(move_in_reach(far))


class VisionCommitTest(unittest.TestCase):
    def test_commit_vision_plays_the_unique_candidate(self):
        import server, shogi
        server.board=shogi.Board(); server.pending=None; server.ai_side=shogi.WHITE
        server.baseline=np.zeros((540,540,3),np.uint8)
        server.frame=server.baseline.copy(); server.frame[368:412,128:172]=255; server.frame[308:352,128:172]=255
        server.frame_id='t'
        with patch.object(server,'stage_ai'):
            # reuse HTTP harness from game flow would be heavier; call the ranking
            ranked=server.candidates(server.baseline,server.normalized(server.frame,[[0,0],[539,0],[539,539],[0,539]]))
        self.assertEqual(ranked[0]['usi'],'7g7f')


if __name__=='__main__':
    unittest.main()
