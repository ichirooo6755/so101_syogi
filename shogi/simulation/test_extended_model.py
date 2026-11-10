"""Check that extending the link moves the elbow motor with the elbow joint."""
import sys
import unittest
from pathlib import Path
import mujoco
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_extended_collisions import build_extended_model
from scene import build_scene


class ExtendedModelTest(unittest.TestCase):
    def test_elbow_motor_and_joint_move_together(self):
        scene=build_scene(neighbors=False,board_x=.20)
        try: original=mujoco.MjModel.from_xml_path(str(scene))
        finally: scene.unlink(missing_ok=True)
        extended,tmp=build_extended_model(75,.20)
        try:
            def locations(model):
                upper=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'upper_arm')
                elbow=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'lower_arm')
                motor=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_MESH,'sts3215_03a_v1')
                ids=[i for i in range(model.ngeom)
                     if model.geom_bodyid[i]==upper and model.geom_dataid[i]==motor]
                self.assertEqual(len(ids),2)
                return model.body_pos[elbow].copy(),model.geom_pos[ids].copy()
            old_joint,old_motor=locations(original)
            new_joint,new_motor=locations(extended)
            np.testing.assert_allclose(new_joint-old_joint,[-.075,0,0],atol=1e-9)
            np.testing.assert_allclose(new_motor-old_motor,np.tile([-.075,0,0],(2,1)),atol=1e-9)
            np.testing.assert_allclose(new_motor-new_joint,old_motor-old_joint,atol=1e-9)
        finally:
            tmp.cleanup()

    def test_extended_scene_keeps_board_and_obstacles(self):
        obstacle={'square':'5e','position_m':(.26,.08),'yaw_deg':90.}
        options={'board_y':.015,'source':(.26,0.),'obstacles':[obstacle],'neighbors':True}
        scene=build_scene(board_x=.26,**options)
        try: stock=mujoco.MjModel.from_xml_path(str(scene))
        finally: scene.unlink(missing_ok=True)
        model,tmp=build_extended_model(100,.26,options)
        try:
            board=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'shogi_board')
            neighbor=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'neighbor_0')
            self.assertGreaterEqual(neighbor,0)
            np.testing.assert_allclose(model.geom_pos[board,:2],[.26,.015])
            reference=mujoco.mj_name2id(stock,mujoco.mjtObj.mjOBJ_GEOM,'neighbor_0')
            np.testing.assert_allclose(model.geom_pos[neighbor],stock.geom_pos[reference])
        finally:
            tmp.cleanup()

    def test_extended_pick_place_uses_same_cad_model(self):
        from pick_place import run
        from unittest.mock import patch
        import check_extended_collisions as builder
        with patch.object(builder,'build_extended_model',wraps=builder.build_extended_model) as called:
            result=run((.25,0.),(.25,.04),board_x=.25,neighbors=True,upper_extend_m=.1)
        called.assert_called_once()
        self.assertEqual(result['upper_extension_mm'],100)
        self.assertTrue(result['sim_only'])
        self.assertIn('inertia remains stock',result['extension_warning'])
        self.assertGreater(result.get('max_lift_mm',0),20)


if __name__=='__main__': unittest.main()
