"""Estimate board XY/yaw from 4 image corners. No camera extrinsics."""
import math
import numpy as np
from board_map import BOARD_L, BOARD_W, BOARD_X, BOARD_Y

# Click order is 9a, 1a, 1i, 9i. 9a→1a is files (width), 1a→1i is ranks (length).
# Robot +X is toward the human along files; +Y follows ranks.


def _quad(points):
    pts=np.asarray(points,dtype=np.float64)
    if pts.shape!=(4,2) or not np.isfinite(pts).all():
        raise ValueError('盤の四隅を4点指定してください')
    return pts


def pose_from_corners(ref_corners, new_corners, ref_pose=None):
    """Map a small corner shift onto robot-frame board pose.

    Pixel translation is expressed in the file/rank basis of the reference
    quad, then scaled by the known board size. Signs follow the black-side
    layout used by sim_square.
    """
    ref=_quad(ref_corners); new=_quad(new_corners)
    v_file=ref[1]-ref[0]; v_rank=ref[2]-ref[1]
    basis=np.column_stack([v_file,v_rank])
    if abs(np.linalg.det(basis))<1e-6:
        raise ValueError('四隅が一直線です')
    delta=new.mean(0)-ref.mean(0)
    frac=np.linalg.solve(basis, delta)
    dx=float(frac[0])*BOARD_W
    dy=-float(frac[1])*BOARD_L
    yaw=math.atan2(v_file[1],v_file[0])
    new_file=new[1]-new[0]
    yaw_new=math.atan2(new_file[1],new_file[0])
    d_yaw=float(np.arctan2(math.sin(yaw_new-yaw), math.cos(yaw_new-yaw)))
    base=ref_pose or {'x':BOARD_X,'y':BOARD_Y,'yaw':0.0}
    x=base['x']+dx; y=base['y']+dy; yaw_out=base.get('yaw',0.0)+d_yaw
    return {'x':x,'y':y,'yaw':yaw_out,
            'shift_mm':round(math.hypot(dx,dy)*1000,2),
            'yaw_deg':round(math.degrees(d_yaw),2)}


def same_view(ref_corners, new_corners, max_scale=1.25):
    """Reject a huge zoom/pan that is not a small board nudge."""
    ref=_quad(ref_corners); new=_quad(new_corners)
    def span(q):
        return max(np.linalg.norm(q[1]-q[0]), np.linalg.norm(q[2]-q[1]), 1.0)
    ratio=span(new)/span(ref)
    if not 1/max_scale<=ratio<=max_scale:
        raise ValueError('カメラの距離が大きく変わっています。同じ観測姿勢で撮り直してください')
    return True
