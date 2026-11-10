"""Split a shogi move into pick/place legs the arm can replay."""
import math
from board_map import sim_square, stand_xy, piece_yaw_deg


def legs(move, stand_position=None):
    side=move.get('board_side') or 'black'
    dest=sim_square(move['destination'], side)
    own=piece_yaw_deg(side, True)
    opp=piece_yaw_deg(side, False)
    stand=stand_xy() if stand_position is None else tuple(stand_position)
    if move.get('drop'):
        return [{'source':stand,'target':dest,'promotion':False,'role':'drop','yaw_deg':own}]
    src=sim_square(move['source'], side)
    if move.get('capture'):
        return [
            {'source':dest,'target':stand,'promotion':bool(move.get('captured_promoted')),'role':'captured_to_stand','yaw_deg':opp},
            {'source':src,'target':dest,'promotion':bool(move.get('promotion')),'role':'own_to_board','yaw_deg':own},
        ]
    return [{'source':src,'target':dest,'promotion':bool(move.get('promotion')),'role':'move','yaw_deg':own}]


def physical_legs(move, stand_proposal=None, board_sfen=None):
    """Build a provisional physical plan only with a measured stand slot."""
    if move.get('capture') or move.get('drop'):
        if not stand_proposal or stand_proposal.get('usi')!=move.get('usi'):
            raise ValueError('A matching measured stand slot is required')
        if board_sfen is None or stand_proposal.get('board_sfen')!=board_sfen:
            raise ValueError('The stand proposal belongs to a different board position')
        expected='capture' if move.get('capture') else 'drop'
        if stand_proposal.get('operation')!=expected:
            raise ValueError('Stand operation does not match the move')
        if expected=='capture' and bool(move.get('captured_promoted'))!=bool(stand_proposal.get('demote_before_storage')):
            raise ValueError('Captured-piece promotion does not match the stand proposal')
        point=stand_proposal.get('xy_m')
        if not isinstance(point,(tuple,list)) or len(point)!=2 or not all(math.isfinite(float(v)) for v in point):
            raise ValueError('A measured stand position is required')
        return legs(move,stand_position=point)
    return legs(move)
