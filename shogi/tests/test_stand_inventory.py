import sys
import unittest
from pathlib import Path
import shogi

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from stand_inventory import PieceStand
from motion import physical_legs
from move_plan import build_plan


class StandInventoryTest(unittest.TestCase):
    def test_capture_promoted_piece_reserves_empty_slot_without_mutating(self):
        board=shogi.Board('4k4/9/9/9/9/4s4/4+P4/9/4K4 w - 1')
        stand=PieceStand([{'id':'a','xy_m':[.22,-.20],'piece':None}])
        proposal=stand.propose(board,shogi.Move.from_usi('5f5g+'))
        self.assertEqual(proposal['piece'],'P')
        self.assertTrue(proposal['demote_before_storage'])
        self.assertEqual(proposal['piece_after'],'P')
        self.assertIsNone(stand.slots[0]['piece'])
        move=build_plan(board,'5f5g+')
        transfers=physical_legs(move,proposal,board.sfen())
        self.assertEqual(transfers[0]['target'],(.22,-.20))
        self.assertEqual([x['role'] for x in transfers],['captured_to_stand','own_to_board'])

    def test_drop_uses_correct_piece_type_not_first_slot(self):
        board=shogi.Board('4k4/9/9/9/9/9/9/9/4K4 b PGS 1')
        stand=PieceStand([{'id':'silver','xy_m':[.20,-.20],'piece':'S'},
                          {'id':'gold','xy_m':[.23,-.20],'piece':'G'},
                          {'id':'pawn','xy_m':[.26,-.20],'piece':'P'}])
        move=shogi.Move.from_usi('P*5e');proposal=stand.propose(board,move)
        self.assertEqual(proposal['slot_id'],'pawn')
        self.assertIsNone(proposal['piece_after'])
        self.assertEqual(physical_legs(build_plan(board,move.usi()),proposal,board.sfen())[0]['source'],(.26,-.20))
        with self.assertRaisesRegex(ValueError,'different board'):
            physical_legs(build_plan(board,move.usi()),proposal,'stale')
        self.assertEqual(stand.slots[2]['piece'],'P')

    def test_unverified_or_inconsistent_stand_is_rejected(self):
        board=shogi.Board('4k4/9/9/9/9/9/9/9/4K4 b P 1')
        move=shogi.Move.from_usi('P*5e')
        stand=PieceStand([{'id':'empty','xy_m':[.2,-.2],'piece':None}])
        with self.assertRaisesRegex(ValueError,'inventory'):
            stand.propose(board,move)
        with self.assertRaisesRegex(ValueError,'measured stand slot'):
            physical_legs(build_plan(board,move.usi()))


if __name__=='__main__': unittest.main()
