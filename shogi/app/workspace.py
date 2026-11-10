"""Conservative robot-frame workspace for long-side seating. From static IK."""
import math
from motion import legs


def in_reach(xy):
    x,y=xy
    if not math.isfinite(x) or not math.isfinite(y): return False
    if x<0.09 or x>0.32: return False
    if abs(y)>0.21: return False
    if x>0.30 and abs(y)>0.09: return False
    if x<0.12 and abs(y)<0.03: return False
    return True


def move_in_reach(move):
    for leg in legs(move):
        if not in_reach(leg['source']) or not in_reach(leg['target']):
            return False
    return True
