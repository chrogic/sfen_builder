"""
validators.py — 盤面バリデーション・王手検出

_validate() は norm_board を1パスで走査し、重複位置・不正成り・駒数超過・
二歩・行き所なし・玉不在をまとめて検出する。
board_counts を呼び出し元に返すことで build_sfen() での再計算を防ぐ。
"""

from .constants import MAX_COUNT, HAND_ORDER, PROMOTABLE, PIECE_FULL_NAME

try:
    import shogi as _shogi
    _SHOGI_AVAILABLE = True
except ImportError:
    _shogi = None
    _SHOGI_AVAILABLE = False


# 行き所のない駒の制約: side → piece → 不正ランクの条件
# (piece, side): (min_rank, max_rank) の範囲が "不正"
_DEAD_PIECE_RANKS = {
    ("P", "sente"): lambda r: r == 1,
    ("L", "sente"): lambda r: r == 1,
    ("N", "sente"): lambda r: r <= 2,
    ("P", "gote"):  lambda r: r == 9,
    ("L", "gote"):  lambda r: r == 9,
    ("N", "gote"):  lambda r: r >= 8,
}


def _validate(norm_board, norm_sente_hand, tsume):
    """
    正規化済みの盤面・持ち駒・詰将棋フラグを検証する。

    norm_board を1パスで走査し、全チェックを同時に実行する。
    戻り値: (errors, warnings, board_counts)
      - errors が空でない場合は SFEN 生成を中止すること
      - board_counts は build_sfen() での再計算に再利用する
    """
    errors   = []
    warnings = []

    # --- 1パスで収集するデータ ---
    seen_pos    = {}       # pos → "side piece"（重複チェック用）
    board_counts = {}      # 正規駒名 → 枚数
    pawn_files  = {"sente": {}, "gote": {}}  # side → file → 枚数（二歩チェック用）
    sente_kings = 0
    gote_kings  = 0

    for entry in norm_board:
        piece   = entry["piece"]
        pos     = entry["pos"]
        side    = entry["side"]
        rank    = pos[1]
        file_   = pos[0]
        promoted = entry["promoted"]

        # 重複位置
        desc = f"{side} {piece}"
        if pos in seen_pos:
            errors.append(
                f"Duplicate position: ({pos[0]},{pos[1]}) has 2+ pieces "
                f"({seen_pos[pos]} and {desc}). Each square can hold exactly one piece."
            )
        else:
            seen_pos[pos] = desc

        # 不正な成り（K, G は成り不可）
        if promoted and piece not in PROMOTABLE:
            errors.append(
                f"Cannot promote {piece} ({PIECE_FULL_NAME.get(piece, piece)}). "
                f"Only R, B, S, N, L, P can promote."
            )

        # 駒数カウント
        board_counts[piece] = board_counts.get(piece, 0) + 1

        # 玉カウント
        if piece == "K":
            if side == "sente":
                sente_kings += 1
            else:
                gote_kings += 1

        # 二歩チェック用: 不成り歩のファイルを収集
        if piece == "P" and not promoted:
            pawn_files[side][file_] = pawn_files[side].get(file_, 0) + 1

        # 行き所のない駒（成り駒は対象外）
        if not promoted:
            is_dead = _DEAD_PIECE_RANKS.get((piece, side))
            if is_dead and is_dead(rank):
                warnings.append(
                    f"Dead piece: {side} {piece} ({PIECE_FULL_NAME.get(piece, '')}) "
                    f"at ({file_},{rank}) cannot move from rank {rank}."
                )

    # --- 持ち駒のバリデーション ---
    for raw_key, count in norm_sente_hand.items():
        if raw_key.startswith("+"):
            errors.append(
                f"Promoted piece '{raw_key}' cannot be in sente_hand. "
                f"Pieces in hand are always unpromoted; use '{raw_key[1:]}' instead."
            )
        if not isinstance(count, int) or count <= 0:
            errors.append(
                f"Invalid piece count in sente_hand: {raw_key}={count}. Count must be >= 1."
            )

    # --- 駒数超過チェック（盤面 + 先手持ち駒 ≤ MAX_COUNT）---
    for piece, max_c in MAX_COUNT.items():
        board_c = board_counts.get(piece, 0)
        hand_c  = norm_sente_hand.get(piece, 0)
        total   = board_c + hand_c
        if total > max_c:
            errors.append(
                f"Piece count exceeds maximum: {piece} ({PIECE_FULL_NAME.get(piece, piece)}) "
                f"has {total} (max {max_c}). Board: {board_c}, sente_hand: {hand_c}."
            )

    # --- 二歩チェック ---
    for side in ("sente", "gote"):
        for f, cnt in pawn_files[side].items():
            if cnt >= 2:
                warnings.append(
                    f"Double pawn (二歩): {side} file {f} has {cnt} unpromoted pawns."
                )

    # --- 玉将不在チェック ---
    if sente_kings == 0 and not tsume:
        warnings.append(
            "Sente king is missing from the board. "
            "This is expected for tsume-shogi (tsume=True by default). "
            "Set tsume=False only for dual-king positions where both kings must be present."
        )
    if gote_kings == 0:
        warnings.append("Gote king is missing from the board.")

    return errors, warnings, board_counts


def detect_check(sfen):
    """
    SFEN文字列を受け取り、先手玉・後手玉それぞれに王手がかかっているか判定する。
    python-shogi が利用不可の場合や SFEN が不正な場合は (None, None) を返す。

    戻り値: (sente_in_check: bool|None, gote_in_check: bool|None)
    """
    if not _SHOGI_AVAILABLE:
        return None, None

    parts = sfen.split(" ")
    if len(parts) != 4:
        return None, None

    sente_in_check = None
    gote_in_check  = None

    try:
        parts_b = parts[:]
        parts_b[1] = "b"
        sente_in_check = _shogi.Board(" ".join(parts_b)).is_check()
    except Exception:
        pass

    try:
        parts_w = parts[:]
        parts_w[1] = "w"
        gote_in_check = _shogi.Board(" ".join(parts_w)).is_check()
    except Exception:
        pass

    return sente_in_check, gote_in_check
