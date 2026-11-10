"""Only attribute failures to the square and operation supported by evidence."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import shogi

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import server
import teaching_tasks
from motion import legs


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.move={'usi':'7g7f','source':'7g','destination':'7f','drop':False,'capture':False}

    def test_ik_errors_identify_both_endpoints(self):
        report={'success':False,'reason':'ik_unreachable','ik_residuals':{
            'grasp':{'position_mm':9.,'angle_deg':0},'place':{'position_mm':1.,'angle_deg':20}}}
        candidates=teaching_tasks.from_failure(self.move,report)
        self.assertEqual([(x['square'],x['operation']) for x in candidates],[('7g','pick'),('7f','place')])
        self.assertTrue(all(x['origin']=='plan' for x in candidates))

    def test_dynamic_settle_failure_is_a_grasp_candidate(self):
        report={'success':False,'reason':'ik_unreachable','failure_phase':'grasp_settle',
                'ik_residuals':{'grasp':{'position_mm':.1,'angle_deg':0},'place':{'position_mm':.1,'angle_deg':0}}}
        candidates=teaching_tasks.from_failure(self.move,report)
        self.assertEqual([(x['square'],x['operation']) for x in candidates],[('7g','pick')])

    def test_stand_and_transport_are_not_mislabelled_as_board_squares(self):
        report={'success':False,'reason':'ik_unreachable','ik_residuals':{'grasp':{'position_mm':20}}}
        self.assertEqual(teaching_tasks.from_failure(self.move,report,'drop'),[])
        report={'success':False,'first_collision':{'phase':'carry','kind':'neighbor'},
                'max_lift_mm':1,'both_jaws_airborne_steps':0}
        self.assertEqual(teaching_tasks.from_failure(self.move,report),[])
        self.assertEqual(teaching_tasks.from_failure(self.move,{'success':False,'reason':'id5_cable_limit'}),[])

    def test_capture_preview_does_not_claim_the_two_steps_succeeded(self):
        move={**self.move,'capture':True}
        report={'success':False,'reason':'capture_preview_only',
                'captured_to_stand':{'success':False,'reason':'grasp_folded'},
                'own_piece_to_board':{'success':True}}
        candidates=teaching_tasks.from_simulation(move,report)
        self.assertEqual([(x['square'],x['operation'],x['role']) for x in candidates],
                         [('7f','pick','captured_to_stand')])

    def test_simulated_grasp_or_placement_is_distinguished(self):
        missed={'success':False,'max_lift_mm':1,'both_jaws_airborne_steps':0}
        placed={'success':False,'max_lift_mm':30,'both_jaws_airborne_steps':220,
                'position_error_mm':12,'target_radius_mm':8}
        self.assertEqual(teaching_tasks.from_simulation(self.move,missed)[0]['operation'],'pick')
        self.assertEqual(teaching_tasks.from_simulation(self.move,placed)[0]['operation'],'place')
        self.assertEqual(teaching_tasks.from_simulation(self.move,{'success':True}),[])
        learned={**missed,'controller':'learned_policy_no_ik_fallback'}
        self.assertEqual(teaching_tasks.from_simulation(self.move,learned)[0]['origin'],'learned_simulation')

    def test_new_simulation_does_not_erase_an_existing_plan_failure(self):
        old=teaching_tasks.from_failure(self.move,{'success':False,'reason':'grasp_folded'})
        self.assertEqual(teaching_tasks.combine(old,teaching_tasks.from_simulation(self.move,{'success':True})),old)
        self.assertEqual(len(teaching_tasks.combine(old,old)),1)

    def test_learned_samples_require_same_model_side_and_board_pose(self):
        sample={'success':False,'controller':'learned_policy_no_ik_fallback',
                'first_collision':{'phase':'descend'}}
        report={'stock_arm':True,'board_side':'white','board_mm':[330,360,12],
                'checkpoint_sha256':'abc','input_fingerprints':{'sim':'v1'},
                'board_center_x_m':.19,'board_y_m':0.,'board_yaw_deg':0.,
                'cases':[{'source_square':'9c','destination_square':'9b','result':sample}]}
        pose={'x':.19,'y':0.,'yaw':0.}
        result=teaching_tasks.learned_report_candidates(report,'white',pose,'abc',{'sim':'v1'})
        self.assertEqual([(x['square'],x['operation'],x['origin']) for x in result],
                         [('9c','pick','learned_simulation')])
        self.assertEqual(result[0]['simulated_move'],'9c9b')
        self.assertEqual(teaching_tasks.learned_report_candidates(report,'black',pose,'abc',{'sim':'v1'}),[])
        self.assertEqual(teaching_tasks.learned_report_candidates(report,'white',pose,'different',{'sim':'v1'}),[])
        self.assertEqual(teaching_tasks.learned_report_candidates(report,'white',pose,'abc',{'sim':'v2'}),[])
        self.assertEqual(teaching_tasks.learned_report_candidates(report,'white',{**pose,'x':.191},'abc',{'sim':'v1'}),[])
        self.assertEqual(teaching_tasks.learned_report_candidates(report,'white',{**pose,'yaw':.1},'abc',{'sim':'v1'}),[])

    def test_planner_failure_exposes_candidates_without_touching_robot(self):
        server.board=shogi.Board();server.ai_side=shogi.BLACK;server.game_revision=19
        server.pending=dict(self.move)
        report={'success':False,'reason':'ik_unreachable','ik_residuals':{'grasp':{'position_mm':9}}}
        with patch.object(server,'plan_leg',side_effect=server.PlanLegFailure('姿勢を計算できません',report)), \
             patch.object(server,'Arm') as arm:
            with self.assertRaises(server.PlanLegFailure): server.plan_pending_leg(server.pending,legs(server.pending)[0])
        self.assertEqual(server.pending['teach_suggestions'][0]['square'],'7g')
        self.assertEqual(server.board.sfen(),shogi.Board().sfen())
        arm.assert_not_called()

    def test_stale_planner_failure_does_not_modify_new_game(self):
        server.board=shogi.Board();server.ai_side=shogi.BLACK;server.game_revision=19
        server.pending=dict(self.move)
        def fail_after_new_game(*args):
            server.game_revision+=1
            raise server.PlanLegFailure('古い結果',{'success':False,'reason':'grasp_folded'})
        with patch.object(server,'plan_leg',side_effect=fail_after_new_game):
            with self.assertRaises(server.PlanLegFailure): server.plan_pending_leg(server.pending,legs(server.pending)[0])
        self.assertNotIn('teach_suggestions',server.pending)


if __name__=='__main__': unittest.main()
