"""Physics and policy integration checks, run in the simulation environment."""
import unittest

import numpy as np

from pick_place import run
from capture_preview import preview


class PickPlaceTest(unittest.TestCase):
    def test_contact_based_move_checks_orientation_and_obstacles(self):
        result=run((.20,-.075),(.20,-.035),neighbors=True)
        self.assertTrue(result['sim_only'])
        self.assertEqual(result['object_pose_writes_during_rollout'],0)
        self.assertEqual(result['controller'],'ik_expert')
        self.assertIn('orientation_ok',result)
        if result['success']:
            self.assertGreaterEqual(result['both_jaws_airborne_steps'],200)
            self.assertEqual(result['board_contact_steps'],0)
            self.assertEqual(result['neighbor_contact_steps'],0)
            self.assertTrue(result['orientation_ok'])

    def test_custom_policy_replaces_expert_and_can_fail(self):
        calls=[]
        def stationary(source,target,phase,progress):
            calls.append(phase)
            return np.zeros(6)
        result=run((.20,-.075),(.20,-.035),neighbors=True,policy=stationary)
        self.assertFalse(result['success'])
        self.assertGreater(len(calls),0)
        self.assertEqual(result['policy_calls'],len(calls))
        self.assertEqual(result['controller'],'learned_policy_no_ik_fallback')
        self.assertEqual(result['ik_residuals'],{})

    def test_reverse_facing_piece_uses_its_initial_orientation_as_reference(self):
        result=run((.20,-.075),(.20,-.035),neighbors=True,piece_yaw_deg=180.)
        self.assertEqual(result['assumptions']['piece_initial_yaw_deg'],180.)
        self.assertLess(result['orientation_error_deg'],30.)

    def test_board_snapshot_replaces_synthetic_neighbors(self):
        obstacles=[{'position_m':[.20+.330/9,-.075],'yaw_deg':180}]
        result=run((.20,-.075),(.20,-.035),obstacles=obstacles)
        self.assertEqual(result['assumptions']['obstacle_mode'],'position_snapshot')
        self.assertEqual(result['assumptions']['obstacle_count'],1)

    def test_capture_preview_keeps_two_transfers_separate(self):
        result=preview((.20,-.075),(.20,-.035),[])
        self.assertFalse(result['success'])
        self.assertEqual(result['reason'],'capture_preview_only')
        self.assertTrue(result['captured_to_stand']['success'])
        self.assertTrue(result['own_piece_to_board']['success'])
        self.assertTrue(result['captured_to_stand']['assumptions']['stand_included'])
        self.assertIn('independently initialized',result['preview_scope'])

    def test_folded_near_base_plan_is_rejected(self):
        result=run((.105,-.037),(.145,-.037),neighbors=False,plan_only=True,board_x=.265)
        self.assertFalse(result['success'])
        self.assertEqual(result['reason'],'grasp_folded')

    def test_gote_gold_on_near_rank_lifts_when_board_is_30cm_out(self):
        result=run((.14,-.037),(.18,-.037),neighbors=False,board_x=.30)
        self.assertTrue(result['success'])
        self.assertGreater(result['max_lift_mm'],20)

    def test_near_base_carry_that_misses_the_square_is_not_sent(self):
        result=run((.105,-.073),(.105,-.037),neighbors=False,plan_only=True)
        self.assertFalse(result['success'])
        self.assertEqual(result['reason'],'ik_unreachable')
        self.assertGreater(result['ik_residuals']['carry']['position_mm'],8)

    def test_plan_only_returns_follower_waypoints_without_physics(self):
        result=run((.20,-.075),(.20,-.035),neighbors=False,plan_only=True)
        self.assertTrue(result['plan_only'])
        self.assertTrue(result['success'])
        names=[w['phase'] for w in result['waypoints']]
        self.assertIn('descend',names); self.assertIn('place',names)
        self.assertEqual(len(result['waypoints'][0]['joints_rad']),5)

    def test_long_side_move_promote_drop_and_capture_physics(self):
        move=run((.24,-.08),(.24,-.04),neighbors=False,piece_yaw_deg=90)
        promo=run((.24,.04),(.24,.08),neighbors=False,promote=True,piece_yaw_deg=90)
        drop=run((.20,-.20),(.24,0),neighbors=False,with_stand=True,piece_yaw_deg=90)
        cap=preview((.24,-.08),(.24,0),[])
        self.assertTrue(move['success'])
        self.assertTrue(promo['success'])
        self.assertTrue(promo['id5_unwound'])
        self.assertTrue(drop['success'])
        self.assertTrue(cap['captured_to_stand']['success'])
        self.assertTrue(cap['own_piece_to_board']['success'])
        far=run((.35,0),(.313,0),neighbors=False,plan_only=True)
        self.assertFalse(far['success'])
    def test_id5_can_flip_then_must_unwind_to_cable_home(self):
        from scene import WRIST_ROLL_LIMIT
        self.assertGreater(WRIST_ROLL_LIMIT,3.14)
        result=run((.20,-.075),(.20,-.035),neighbors=False,promote=True)
        self.assertEqual(result['assumptions']['id5_range_deg'],365)
        self.assertTrue(result['id5_unwound'])
        self.assertTrue(result['success'])
        self.assertIn('flip',result['ik_residuals'])
        self.assertIn('unwind',{f['phase'] for f in result['trace']})


if __name__=='__main__':
    unittest.main()
