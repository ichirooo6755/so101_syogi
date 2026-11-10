"""Board squares in robot XY. Pose absorbs a small physical shift/yaw."""
import math
import re
import shogi

# Robot and human sit on opposite long sides. X follows the 330 mm files
# toward the human; Y follows the 360 mm ranks, so the promotion zone is
# not behind the far edge.
BOARD_X=.19
BOARD_Y=0.
BOARD_W=.330
BOARD_L=.360
_pose={'x':BOARD_X,'y':BOARD_Y,'yaw':0.0}


def set_pose(x=None,y=None,yaw=0.0):
    if x is not None:
        if not math.isfinite(x) or not .15<=x<=.40: raise ValueError('盤の前後位置が範囲外です')
        _pose['x']=float(x)
    if y is not None:
        if not math.isfinite(y) or not -.12<=y<=.12: raise ValueError('盤の左右位置が範囲外です')
        _pose['y']=float(y)
    if not math.isfinite(yaw) or abs(yaw)>math.radians(25): raise ValueError('盤の回転が大きすぎます')
    _pose['yaw']=float(yaw)
    return pose()


def reset_pose():
    _pose.update(x=BOARD_X,y=BOARD_Y,yaw=0.0)
    return pose()


def pose():
    return {'x':_pose['x'],'y':_pose['y'],'yaw':_pose['yaw'],
            'shift_mm':round(math.hypot(_pose['x']-BOARD_X,_pose['y']-BOARD_Y)*1000,2),
            'yaw_deg':round(math.degrees(_pose['yaw']),2)}


def stand_xy():
    """One assumed empty stand slot, beside the near rank."""
    return (_pose['x']-.04, _pose['y']-.20)


def sim_square(usi, ai_side='black', center_x=None):
    if not isinstance(usi,str) or not re.fullmatch(r'[1-9][a-i]',usi):
        raise ValueError('invalid USI square')
    if ai_side not in ('black','white'):
        raise ValueError('invalid AI side')
    file=int(usi[0]);rank=ord(usi[1])-ord('a')
    direction=1 if ai_side=='black' else -1
    cx=BOARD_X if center_x is None else center_x
    cy=BOARD_Y
    yaw=0.0
    if center_x is None:
        cx,cy,yaw=_pose['x'],_pose['y'],_pose['yaw']
    dx=direction*((9-file)-4)*BOARD_W/9
    dy=direction*(4-rank)*BOARD_L/9
    c,s=math.cos(yaw),math.sin(yaw)
    return (cx+c*dx-s*dy, cy+s*dx+c*dy)


def piece_yaw_deg(side, own=True):
    """Pieces point along ranks: white +Y, black -Y."""
    if side not in ('black','white',shogi.BLACK,shogi.WHITE):
        raise ValueError('invalid AI side')
    yaw=90. if side in ('white',shogi.WHITE) else -90.
    return yaw if own else yaw+180.


def simulation_obstacles(position, source, robot_side, exclude=()):
    """Return an assumed fixed obstacle for each other occupied square."""
    obstacles=[]
    board_side='black' if robot_side==shogi.BLACK else 'white'
    for square in shogi.SQUARES:
        piece=position.piece_at(square)
        name=shogi.SQUARE_NAMES[square]
        if piece is None or name==source or name in exclude: continue
        obstacles.append({'square':name,'position_m':sim_square(name,board_side),
                          'yaw_deg':piece_yaw_deg(board_side, own=piece.color==robot_side)})
    return obstacles
