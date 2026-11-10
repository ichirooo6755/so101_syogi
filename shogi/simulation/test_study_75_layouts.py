"""Check the layout study's board transform and explicit base screening."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
import study_75_layouts as study


class LayoutStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.study=study.Study()

    @classmethod
    def tearDownClass(cls): cls.study.close()

    def test_near_and_far_square_transform(self):
        self.assertLess(study.square_xy('9e',.210,0.,0.)[0], .210)
        self.assertGreater(study.square_xy('1e',.210,0.,0.)[0], .210)
        self.assertAlmostEqual(study.square_xy('5a',.210,0.,0.)[1],.160)

    def test_base_board_checked_even_though_visual_geoms_do_not_collide(self):
        self.assertGreater(len(self.study.base_geoms),0)
        self.study.configure(.210,0.,0.,0.)
        near,_=self.study.base_board()
        self.study.configure(.250,0.,0.,0.)
        far,_=self.study.base_board()
        self.assertLess(near,0.)
        self.assertGreater(far,.005)

    def test_raised_board_also_raises_target(self):
        targets=[]
        def fake_ik(model,data,site,seed,target,grip,direction):
            targets.append(target.copy())
            return np.zeros(5),1.,90.
        with patch.object(study,'solve_pose_ik',side_effect=fake_ik):
            result=self.study.search('9e',.21,0.,0.,.04)
        self.assertFalse(result['ik'])
        self.assertAlmostEqual(targets[0][2],.04+.012+.010)


if __name__=='__main__': unittest.main()
