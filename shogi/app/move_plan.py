"""Translate a legal shogi move into explicit physical tasks, without motor commands."""
import shogi

PIECES={'p':'歩','l':'香','n':'桂','s':'銀','g':'金','b':'角','r':'飛','k':'玉',
        '+p':'と金','+l':'成香','+n':'成桂','+s':'成銀','+b':'馬','+r':'龍'}

def square_name(index):
    usi=shogi.SQUARE_NAMES[index]
    return usi[0] + '一二三四五六七八九'[ord(usi[1])-ord('a')]

def piece_name(piece):
    return PIECES[piece.symbol().lower()]

def build_plan(board, usi):
    move=shogi.Move.from_usi(usi)
    if move not in board.legal_moves:
        raise ValueError('この局面では合法手ではありません')
    destination=square_name(move.to_square)
    target=board.piece_at(move.to_square)
    tasks=[]
    if target:
        tasks.append(f'{destination}の相手の{piece_name(target)}を取って、自分の駒台へ移す（成駒なら表に戻す）')
    if move.drop_piece_type is not None:
        piece=shogi.Piece(move.drop_piece_type,board.turn)
        tasks.append(f'自分の駒台から{piece_name(piece)}を取り、{destination}に打つ')
    else:
        piece=board.piece_at(move.from_square)
        tasks.append(f'{square_name(move.from_square)}の{piece_name(piece)}をつかみ、{destination}に置く')
    if move.promotion:
        tasks.append(f'{destination}の駒を裏返して成る')
    tasks.append('盤面と両者の持ち駒を確認する')
    return {'usi':usi,'tasks':tasks,'capture':target is not None,'drop':move.drop_piece_type is not None,
            'board_side':'black' if board.turn==shogi.BLACK else 'white',
            'promotion':bool(move.promotion),'captured_promoted':bool(target is not None and target.is_promoted()),
            'source':None if move.from_square is None else shogi.SQUARE_NAMES[move.from_square],
            'destination':shogi.SQUARE_NAMES[move.to_square],
            'ready_to_execute':False,
            'blockers':['実機の関節対応・盤座標・把持・停止と、駒台の位置は未検証']}
