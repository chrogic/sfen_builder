"""
builders.py — SFENブロック文字列の生成

_build_board_block: 9×9グリッドを rank1→9、各rank内 file9→1 の順で走査して
                    盤面ブロック文字列を生成する。
_build_hand_block:  先後の持ち駒辞書から持ち駒ブロック文字列を生成する。
"""

from .constants import HAND_ORDER


def build_board_block(norm_board):
    """
    正規化済み盤面リストから SFEN 盤面ブロック文字列を生成する。

    SFEN走査順: rank 1(後手側)→9(先手側)、各rank内は file 9→1。
    先手駒=大文字、後手駒=小文字、成り駒は '+' 接頭辞。
    """
    grid = {}
    for entry in norm_board:
        piece    = entry["piece"]
        pos      = entry["pos"]
        side     = entry["side"]
        promoted = entry["promoted"]
        letter   = piece.upper() if side == "sente" else piece.lower()
        grid[pos] = ("+" if promoted else "") + letter

    rank_strings = []
    for rank in range(1, 10):
        rank_str    = ""
        empty_count = 0
        for file_ in range(9, 0, -1):
            cell = grid.get((file_, rank))
            if cell is None:
                empty_count += 1
            else:
                if empty_count:
                    rank_str   += str(empty_count)
                    empty_count = 0
                rank_str += cell
        if empty_count:
            rank_str += str(empty_count)
        rank_strings.append(rank_str)

    return "/".join(rank_strings)


def build_hand_block(sente_hand, gote_hand):
    """
    先手・後手の持ち駒辞書から SFEN 持ち駒ブロック文字列を生成する。
    順序: R,B,G,S,N,L,P の順で先手(大文字)→後手(小文字)。
    駒がなければ "-"。
    """
    parts = []
    for hand, to_letter in ((sente_hand, str.upper), (gote_hand, str.lower)):
        for piece in HAND_ORDER:
            cnt = hand.get(piece, 0)
            if cnt > 0:
                parts.append((str(cnt) if cnt > 1 else "") + to_letter(piece))
    return "".join(parts) if parts else "-"
