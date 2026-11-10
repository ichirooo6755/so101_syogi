"""Prepare robot hand-piece transfers from measured, individually tracked slots.

This is an offline ledger, not a camera recognizer or hardware controller.
It never mutates a slot while planning; a caller must reconcile physical
observations before persisting any proposed change.
"""
from collections import Counter
import math
import shogi

PIECES=set('PLNSGBR')


class PieceStand:
    def __init__(self, slots):
        self.slots=[]
        ids=set(); positions=set()
        for row in slots:
            ident=row.get('id');xy=row.get('xy_m');piece=row.get('piece')
            if not isinstance(ident,str) or not ident or ident in ids:
                raise ValueError('Each stand slot must have a unique ID')
            if not isinstance(xy,(list,tuple)) or len(xy)!=2 or not all(math.isfinite(float(v)) for v in xy):
                raise ValueError('Each stand slot needs a measured XY position')
            xy=tuple(float(v) for v in xy)
            if xy in positions: raise ValueError('Stand slot positions must be unique')
            if piece is not None and piece not in PIECES:
                raise ValueError('Stand pieces must be unpromoted shogi piece types')
            self.slots.append({'id':ident,'xy_m':xy,'piece':piece})
            ids.add(ident);positions.add(xy)
        if not self.slots: raise ValueError('Measured stand slots are required')

    def propose(self, board, move):
        if move not in board.legal_moves: raise ValueError('The move is not legal')
        expected=Counter({shogi.PIECE_SYMBOLS[k].upper():v for k,v in board.pieces_in_hand[board.turn].items() if v})
        actual=Counter(slot['piece'] for slot in self.slots if slot['piece'])
        if expected!=actual:
            raise ValueError('Stand inventory does not match the shogi position')
        captured=board.piece_at(move.to_square)
        if move.drop_piece_type is not None:
            piece=shogi.PIECE_SYMBOLS[move.drop_piece_type].upper()
            slot=next((s for s in self.slots if s['piece']==piece),None)
            if slot is None: raise ValueError('The required piece has no recorded slot')
            operation='drop';after=None;demote=False
        elif captured is not None:
            piece=captured.symbol().lstrip('+').upper()
            slot=next((s for s in self.slots if s['piece'] is None),None)
            if slot is None: raise ValueError('There is no empty stand slot for the captured piece')
            operation='capture';after=piece;demote=bool(captured.is_promoted())
        else:
            return None
        return {'board_sfen':board.sfen(),'usi':move.usi(),'operation':operation,
                'slot_id':slot['id'],'xy_m':slot['xy_m'],'piece':piece,
                'piece_before':slot['piece'],'piece_after':after,'demote_before_storage':demote}
