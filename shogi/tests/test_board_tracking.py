import math
import sys
import unittest
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from board_tracking import PlanarBoardCalibration
import server
from board_map import sim_square, reset_pose


class BoardTrackingTest(unittest.TestCase):
    def setUp(self):
        self.ref=np.array([[.08,.18],[.41,.18],[.41,-.18],[.08,-.18]],dtype=np.float64)
        self.pixels=np.array([[120,90],[650,120],[620,530],[140,500]],dtype=np.float64)
        self.K=np.array([[700,0,400],[0,700,300],[0,0,1]],dtype=float)
        self.cal=PlanarBoardCalibration(self.pixels,self.ref,self.K,np.zeros(5),[0,1,2,3,4])
        self.world_to_image=cv2.getPerspectiveTransform(self.ref.astype(np.float32),self.pixels.astype(np.float32))
    def image_of(self,world):
        return cv2.perspectiveTransform(np.asarray(world,dtype=np.float64).reshape(1,4,2),self.world_to_image).reshape(4,2)
    def test_projective_camera_recovers_small_translation_and_rotation(self):
        a=math.radians(4); r=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
        center=self.ref.mean(axis=0);shift=np.array([.012,-.008])
        moved=(self.ref-center)@r.T+center+shift
        result=self.cal.track(self.image_of(moved),[0,1,2,3,4])
        np.testing.assert_allclose(result['corners_robot_m'],moved,atol=1e-6)
        np.testing.assert_allclose(result['shift_m'],shift,atol=1e-6)
        self.assertAlmostEqual(result['yaw_deg'],4,places=3)
    def test_rejects_wrong_wrist_pose_large_move_and_nonrigid_corners(self):
        with self.assertRaisesRegex(ValueError,'observation pose'):
            self.cal.track(self.pixels,[0,1,2,3,5])
        with self.assertRaisesRegex(ValueError,'tracking range'):
            self.cal.track(self.image_of(self.ref+[.04,0]),[0,1,2,3,4])
        warped=self.ref.copy();warped[0]+=[.012,.01]
        with self.assertRaisesRegex(ValueError,'rigid board'):
            self.cal.track(self.image_of(warped),[0,1,2,3,4])
    def test_tracked_shift_moves_the_arm_square(self):
        a=math.radians(4); r=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
        center=self.ref.mean(axis=0);shift=np.array([.012,-.008])
        moved=(self.ref-center)@r.T+center+shift
        before=sim_square('5e','white')
        pose=server.use_tracked_board(self.cal.track(self.image_of(moved),[0,1,2,3,4]))
        after=sim_square('5e','white')
        self.assertAlmostEqual(pose['x']-server.BOARD_X,0.012,places=3)
        self.assertAlmostEqual(pose['y'],-0.008,places=3)
        self.assertGreater(abs(after[0]-before[0])+abs(after[1]-before[1]),0.01)
        reset_pose()
    def test_refuses_missing_camera_calibration(self):
        with self.assertRaisesRegex(ValueError,'intrinsics'):
            PlanarBoardCalibration(self.pixels,self.ref,np.zeros((3,3)),np.zeros(5),[0]*5)


if __name__=='__main__': unittest.main()
