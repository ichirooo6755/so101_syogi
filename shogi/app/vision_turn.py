"""Conservative temporal detection of one human shogi move.

This is a heuristic, not a piece-recognition model. Ambiguous promotion and
drop types are deliberately returned for a person to resolve.
"""
from __future__ import annotations
import cv2
import numpy as np


def cell_changes(old, new):
    a = cv2.cvtColor(old, cv2.COLOR_BGR2GRAY).astype(np.float32)
    b = cv2.cvtColor(new, cv2.COLOR_BGR2GRAY).astype(np.float32)
    delta = b - a
    diff = np.abs(delta - np.median(delta))
    return [float(np.mean(diff[y*60+8:y*60+52, x*60+8:x*60+52]))
            for y in range(9) for x in range(9)]


def move_candidates(old, new, board):
    scores = cell_changes(old, new)
    ranked = []
    for move in board.legal_moves:
        changed = {move.to_square}
        if move.from_square is not None:
            changed.add(move.from_square)
        inside = sum(scores[i] for i in changed) / len(changed)
        outside = sum(v for i, v in enumerate(scores) if i not in changed) / (81-len(changed))
        weakest = min(scores[i] for i in changed)
        strongest_other = max((v for i, v in enumerate(scores) if i not in changed), default=0)
        ranked.append({'usi': move.usi(), 'score': round(inside-outside, 2),
                       'weakest': round(weakest, 2), 'other': round(strongest_other, 2),
                       'squares': tuple(sorted(changed))})
    return sorted(ranked, key=lambda x: x['score'], reverse=True)


class VisionTurn:
    """Require repeated stable frames and a clearly localized legal move."""
    def __init__(self, stable_frames=3, motion_threshold=2.5):
        self.stable_frames = stable_frames
        self.motion_threshold = motion_threshold
        self.baseline = None
        self.previous = None
        self.stable = 0

    def feed(self, frame, board):
        if self.previous is None:
            self.previous = frame.copy()
            return {'status': 'settling'}
        prev = cv2.cvtColor(self.previous, cv2.COLOR_BGR2GRAY).astype(np.float32)
        curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        change = curr - prev
        motion = float(np.mean(np.abs(change - np.median(change))))
        self.previous = frame.copy()
        self.stable = self.stable + 1 if motion <= self.motion_threshold else 0
        if self.stable < self.stable_frames:
            return {'status': 'settling', 'motion': round(motion, 2)}
        if self.baseline is None:
            self.baseline = frame.copy()
            return {'status': 'waiting'}
        ranked = move_candidates(self.baseline, frame, board)
        if not ranked or ranked[0]['score'] < 7:
            return {'status': 'waiting'}
        best = ranked[0]
        matching = [r for r in ranked if r['squares'] == best['squares']]
        different = next((r for r in ranked if r['squares'] != best['squares']), None)
        # Requiring both squares to change avoids accepting a piece temporarily
        # lifted from the board. An unrelated strong change can be a hand/occlusion.
        clear = (best['weakest'] >= 6 and best['other'] < best['weakest'] * 0.75
                 and (different is None or best['score']-different['score'] >= 3))
        choices = [{'usi': r['usi'], 'score': r['score']} for r in matching]
        if clear and len(matching) == 1:
            return {'status': 'detected', 'usi': best['usi']}
        return {'status': 'ambiguous', 'candidates': choices if clear else
                [{'usi': r['usi'], 'score': r['score']} for r in ranked[:6]]}
