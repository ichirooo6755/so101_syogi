"""Cross-check the official-derived extended URDF with the MuJoCo chain."""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_official_urdf import build
from check_extended_collisions import build_extended_model
from study_opposed_layout import OpposedStudy, square_xy_opposed

ROOT=Path(__file__).resolve().parents[1]


class OfficialExtendedModelTest(unittest.TestCase):
    def test_forward_kinematics_matches_extended_mujoco(self):
        for length in (75,100):
            with self.subTest(length=length), tempfile.TemporaryDirectory(dir=ROOT/'simulation/model') as d:
                out=build(length,Path(d)/'arm.urdf')
                tree=ET.parse(out)
                cfg=ET.Element('mujoco')
                ET.SubElement(cfg,'compiler',{'fusestatic':'false'})
                tree.getroot().insert(0,cfg)
                tree.write(out,encoding='utf8',xml_declaration=True)
                urdf=mujoco.MjModel.from_xml_path(str(out))
                m,tmp=build_extended_model(length,.24)
                try:
                    ud=mujoco.MjData(urdf);md=mujoco.MjData(m)
                    body=mujoco.mj_name2id(urdf,mujoco.mjtObj.mjOBJ_BODY,'shogi_pinch_centre_link')
                    site=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_SITE,'pinch_centre')
                    self.assertGreaterEqual(body,0);self.assertGreaterEqual(site,0)
                    for q in ([0,0,0,0,0,.05],[.2,-.4,.7,.8,.1,.05],[-.5,.4,-.3,.2,-.9,.05]):
                        ud.qpos[:6]=q;md.qpos[:6]=q
                        mujoco.mj_forward(urdf,ud);mujoco.mj_forward(m,md)
                        np.testing.assert_allclose(ud.xpos[body],md.site_xpos[site],atol=1e-5)
                finally: tmp.cleanup()

    def test_rejects_changed_upstream(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'modified.urdf';src.write_text('<robot/>')
            with self.assertRaisesRegex(ValueError,'pinned'):
                build(75,Path(d)/'out.urdf',source=src)

    def test_opposed_board_has_ranks_along_robot_to_human(self):
        self.assertLess(square_xy_opposed('5i',.26,0.,0.)[0],.26)
        self.assertGreater(square_xy_opposed('5a',.26,0.,0.)[0],.26)
        self.assertGreater(square_xy_opposed('9e',.26,0.,0.)[1],0.)
        study=OpposedStudy(75)
        try:
            study.configure(.26,0.,0.,0.)
            np.testing.assert_allclose(study.model.geom_size[study.board,:2],[.18,.165])
            gap,_=study.base_board()
            self.assertGreater(gap,.005)
        finally: study.close()


if __name__=='__main__':unittest.main()
