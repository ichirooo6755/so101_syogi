"""Verify that the optional surface audit uses the real mesh transforms."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))


@unittest.skipUnless(importlib.util.find_spec('fcl'),'optional python-fcl is not installed')
class MeshContactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from check_75_mesh_contacts import SurfaceAudit
        from study_75_layouts import Study
        cls.study=Study();cls.audit=SurfaceAudit(cls.study)

    @classmethod
    def tearDownClass(cls): cls.study.close()

    def test_actual_base_mesh_intersects_near_board_and_clears_farther_board(self):
        geom=next(i for i in self.study.base_geoms if self.study.label(i)=='base_so101_v2')
        self.study.configure(.210,0.,0.,0.)
        self.assertTrue(self.audit.surface_contact(geom,self.study.board)['triangle_intersection'])
        self.study.configure(.235,0.,0.,0.)
        contact=self.audit.surface_contact(geom,self.study.board)
        self.assertFalse(contact['triangle_intersection'])
        self.assertGreater(contact['surface_distance_mm'],5.)

    def test_failed_near_pose_has_actual_mesh_intersections(self):
        import mujoco
        from study_75_layouts import GRIP
        report=json.loads((Path(__file__).resolve().parents[1]/'output/upper_arm_extension/layout_study_75_base.json').read_text())
        layout=next(x for x in report['full_board'] if x['center_mm']==[235.,0.])
        pose=next(x for x in layout['squares'] if x['square']=='9e')
        self.study.configure(.235,0.,0.,0.)
        self.study.data.qpos[:5]=pose['q_rad'];self.study.data.qpos[5]=GRIP
        mujoco.mj_forward(self.study.model,self.study.data)
        pairs=self.audit.candidates()
        self.assertTrue(any(self.audit.surface_contact(a,b)['triangle_intersection'] for a,b in pairs))


if __name__=='__main__': unittest.main()
