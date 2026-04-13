"""
normalizers.py — 駒名・座標・手番の正規化
"""

from .constants import (
    PIECE_ALIASES, TURN_SENTE, TURN_GOTE,
    RANK_LETTER_TO_INT, RANK_KANJI_TO_INT, FULLWIDTH_TO_INT,
)


def normalize_pos(pos):
    """
    座標を (file:1-9, rank:1-9) タプルに正規化する。
    受け付ける形式: "5a" | "５一" | (5,1) | [5,1]
    失敗時は None を返す。
    """
    if isinstance(pos, (tuple, list)):
        if len(pos) != 2:
            return None
        try:
            file_, rank_ = int(pos[0]), int(pos[1])
        except (TypeError, ValueError):
            return None
        return (file_, rank_) if 1 <= file_ <= 9 and 1 <= rank_ <= 9 else None

    if not isinstance(pos, str):
        return None

    s = pos.strip()
    if not s:
        return None

    # ファイル部分を前方から読み取る
    i = 0
    file_chars = []
    while i < len(s) and (s[i].isdigit() or s[i] in FULLWIDTH_TO_INT):
        file_chars.append(s[i])
        i += 1
    if not file_chars or i >= len(s):
        return None

    file_str = "".join(file_chars)
    if len(file_str) == 1 and file_str in FULLWIDTH_TO_INT:
        file_ = FULLWIDTH_TO_INT[file_str]
    else:
        try:
            file_ = int(file_str)
        except ValueError:
            return None

    rank_str = s[i:]
    if rank_str in RANK_LETTER_TO_INT:
        rank_ = RANK_LETTER_TO_INT[rank_str]
    elif rank_str in RANK_KANJI_TO_INT:
        rank_ = RANK_KANJI_TO_INT[rank_str]
    else:
        return None

    return (file_, rank_) if 1 <= file_ <= 9 and 1 <= rank_ <= 9 else None


def normalize_piece(raw):
    """
    駒名を正規化して (canonical_piece: str, promoted: bool) を返す。
    失敗時は (None, False)。
    "+R" のような成り表記は promoted=True として解釈する。
    """
    if not isinstance(raw, str):
        return None, False
    s = raw.strip()
    promoted = s.startswith("+")
    key = s[1:].lower() if promoted else s.lower()
    piece = PIECE_ALIASES.get(key)
    return piece, promoted


def normalize_side(raw):
    """
    手番/陣営を "sente" または "gote" に正規化する。失敗時は None。
    """
    if not isinstance(raw, str):
        return None
    s = raw.strip().lower()
    if s in {x.lower() for x in TURN_SENTE}:
        return "sente"
    if s in {x.lower() for x in TURN_GOTE}:
        return "gote"
    return None
