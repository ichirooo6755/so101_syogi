import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import shogi

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import server
from markers import MARKER_DICT, detect_marker_corners
from vision_turn import VisionTurn


def board_image(pieces=()):
    image = np.full((600, 600, 3), 255, np.uint8)
    cv2.rectangle(image, (120,120), (480,480), (185, 205, 225), -1)
    for n in range(10):
        cv2.line(image, (120+40*n,120), (120+40*n,480), (70,70,70), 1)
        cv2.line(image, (120,120+40*n), (480,120+40*n), (70,70,70), 1)
    for square in pieces:
        x=120+(9-int(square[0]))*40
        y=120+(ord(square[1])-ord('a'))*40
        cv2.rectangle(image, (x+9,y+9), (x+30,y+30), (25,25,25), -1)
    for ident,(x,y) in {0:(60,60),1:(480,60),2:(480,480),3:(60,480)}.items():
        marker=cv2.aruco.generateImageMarker(MARKER_DICT,ident,60)
        image[y:y+60,x:x+60]=cv2.cvtColor(marker,cv2.COLOR_GRAY2BGR)
    return image


def normalized(image):
    return server.normalized(image, detect_marker_corners(image))


class AutomaticVisionTest(unittest.TestCase):
    def test_four_markers_follow_a_translated_board_and_reject_missing(self):
        original=board_image(['7g'])
        shift=np.float32([[1,0,13],[0,1,8]])
        moved=cv2.warpAffine(original,shift,(600,600),borderValue=(255,255,255))
        p=np.array(detect_marker_corners(original)); q=np.array(detect_marker_corners(moved))
        np.testing.assert_allclose(q-p, np.tile([13,8],(4,1)), atol=1)
        hidden=original.copy(); hidden[45:125,45:125]=255
        with self.assertRaisesRegex(ValueError,'0'):
            detect_marker_corners(hidden)

    def test_stable_legal_move_is_detected_but_lift_alone_is_not(self):
        board=shogi.Board(); tracker=VisionTurn(stable_frames=2)
        before=normalized(board_image(['7g']))
        lifted=normalized(board_image([]))
        after=normalized(board_image(['7f']))
        for _ in range(4): result=tracker.feed(before,board)
        self.assertEqual(result['status'],'waiting')
        for _ in range(4): result=tracker.feed(lifted,board)
        self.assertNotEqual(result['status'],'detected')
        for _ in range(4): result=tracker.feed(after,board)
        self.assertEqual(result, {'status':'detected','usi':'7g7f'})

    def test_promotion_is_never_guessed_from_the_same_two_changed_squares(self):
        board=shogi.Board();board.push_usi('7g7f');board.push_usi('3c3d')
        tracker=VisionTurn(stable_frames=2)
        before=normalized(board_image(['8h']))
        after=normalized(board_image(['2b']))
        for _ in range(4): tracker.feed(before,board)
        for _ in range(4): result=tracker.feed(after,board)
        self.assertEqual(result['status'],'ambiguous')
        self.assertTrue({'8h2b','8h2b+'}.issubset({c['usi'] for c in result['candidates']}))

    def test_multiple_legal_drop_types_require_selection(self):
        board=shogi.Board('4k4/9/9/9/9/9/9/9/4K4 b PGS 1')
        tracker=VisionTurn(stable_frames=2)
        before=normalized(board_image()); after=normalized(board_image(['5e']))
        for _ in range(4): tracker.feed(before,board)
        for _ in range(4): result=tracker.feed(after,board)
        self.assertEqual(result['status'],'ambiguous')
        self.assertTrue({'P*5e','G*5e','S*5e'}.issubset({c['usi'] for c in result['candidates']}))

    def test_detection_survives_a_small_board_rotation_and_translation(self):
        board=shogi.Board(); tracker=VisionTurn(stable_frames=2)
        before=normalized(board_image(['7g']))
        matrix=cv2.getRotationMatrix2D((300,300),3,1)
        matrix[:,2]+=[8,6]
        moved=cv2.warpAffine(board_image(['7f']),matrix,(600,600),borderValue=(255,255,255))
        after=normalized(moved)
        for _ in range(4): tracker.feed(before,board)
        for _ in range(4): result=tracker.feed(after,board)
        self.assertEqual(result, {'status':'detected','usi':'7g7f'})

    def test_auto_loop_stages_engine_move_without_touching_arm(self):
        class Stop:
            calls=0
            def is_set(self): return self.calls>=12
            def wait(self, _): self.calls+=1
        images=[board_image(['7g'])]*5+[board_image(['7f'])]*8
        server.board=shogi.Board(); server.ai_side=shogi.WHITE; server.pending=None
        server.engine_error=None;server.game_revision=0;server.auto={'status':'settling'}
        with patch.object(server,'_camera_frame',side_effect=images), \
             patch.object(server,'engine_move',return_value='3c3d'), \
             patch.object(server,'plan_leg',return_value={'success':True,'waypoints':[{}]}), \
             patch.object(server,'Arm') as arm:
            server.automatic_game('mac','',Stop())
        self.assertEqual(server.auto['last_human'],'7g7f')
        self.assertEqual(server.auto['status'],'robot_blocked')
        self.assertEqual(server.pending['usi'],'3c3d')
        self.assertEqual(server.board.turn,shogi.WHITE)
        arm.assert_not_called()
        self.assertEqual(server.pending['reach'],'ok')

    def test_unreachable_ai_move_asks_the_human_to_place_it(self):
        class Stop:
            calls=0
            def is_set(self): return self.calls>=12
            def wait(self, _): self.calls+=1
        images=[board_image(['7g'])]*5+[board_image(['7f'])]*8
        server.board=shogi.Board(); server.ai_side=shogi.WHITE; server.pending=None
        server.engine_error=None;server.game_revision=0;server.auto={'status':'settling'}
        with patch.object(server,'_camera_frame',side_effect=images), \
             patch.object(server,'engine_move',return_value='9c9d'), \
             patch.object(server,'plan_leg',side_effect=ValueError('このマスへは腕が届きません')), \
             patch.object(server,'Arm') as arm:
            server.automatic_game('mac','',Stop())
        self.assertEqual(server.auto['status'],'robot_blocked')
        self.assertIn('届きません', server.auto['message'])
        self.assertEqual(server.board.turn, shogi.WHITE)
        arm.assert_not_called()

    def test_live_bus_is_blocked_and_dry_run_does_not_count_as_a_move(self):
        with self.assertRaisesRegex(ValueError,'未検証'):
            server.Arm()._connect()
        self.assertFalse(server.sim_succeeded({'reason':'capture_preview_only',
                         'captured_to_stand':{'success':True},'own_piece_to_board':{'success':True}}))

    def test_pause_and_resume_preserves_the_comparison_baseline(self):
        class FastStop:
            def __init__(self): self.event=threading.Event()
            def is_set(self): return self.event.is_set()
            def wait(self, _): return self.event.wait(.005)
        stop=FastStop(); image=[board_image(['7g'])]
        server.board=shogi.Board();server.ai_side=shogi.WHITE;server.pending=None
        server.engine_error=None;server.game_revision=0;server.auto={'status':'settling'}
        with patch.object(server,'_camera_frame',side_effect=lambda *_: image[0]), \
             patch.object(server,'engine_move',return_value='3c3d'), \
             patch.object(server,'plan_leg',return_value={'success':True,'waypoints':[{}]}):
            worker=threading.Thread(target=server.automatic_game,args=('mac','',stop))
            worker.start()
            try:
                deadline=time.monotonic()+3
                while server.auto.get('status')!='waiting' and time.monotonic()<deadline: time.sleep(.01)
                self.assertEqual(server.auto['status'],'waiting')
                with server.LOCK:
                    server.auto['status']='paused';image[0]=board_image(['7f'])
                time.sleep(.1)
                self.assertEqual(server.board.turn,shogi.BLACK)
                with server.LOCK:
                    server.auto.update(status='settling',reset_stability=True)
                deadline=time.monotonic()+3
                while server.auto.get('status')!='robot_blocked' and time.monotonic()<deadline: time.sleep(.01)
                self.assertEqual(server.auto.get('last_human'),'7g7f')
                self.assertEqual(server.pending['usi'],'3c3d')
            finally:
                stop.event.set();worker.join(timeout=3)


if __name__ == '__main__': unittest.main()
