"""
core.py — 公開関数: build_sfen / parse_sfen
"""

import sys

from .constants import MAX_COUNT, HAND_ORDER, PIECE_ALIASES, PIECE_FULL_NAME, TURN_TO_SFEN
from .normalizers import normalize_pos, normalize_piece, normalize_side
from .initial_board import INITIAL_BOARD
from .validators import _validate, detect_check, _SHOGI_AVAILABLE
from .builders import build_board_block, build_hand_block


def build_sfen(board=None, sente_hand=None, turn="sente", tsume=True, debug=False):
    """
    将棋盤面データを受け取り、SFEN文字列と付随情報を返す。

    Args:
        board:      盤面エントリのリスト、または "initial"（初期配置）。
                    各エントリ: {"piece": str, "pos": str|tuple, "side": str, "promoted": bool}
        sente_hand: 先手持ち駒の辞書。例: {"P": 2, "G": 1}
        turn:       手番。"sente"/"b"/"先手" または "gote"/"w"/"後手"。
        tsume:      True（デフォルト）= 詰将棋モード、先手玉不在の警告を抑制。
                    False = 双玉モード、先手玉不在を警告。
        debug:      True にすると処理ログを stderr に出力する。

    Returns:
        {"sfen": str, "gote_hand": dict, "sente_hand_used": dict,
         "validation": {"ok": bool, "errors": list, "warnings": list}}
    """
    if debug:
        print("[build_sfen] START", file=sys.stderr)

    board      = [] if board is None else board
    sente_hand = {} if sente_hand is None else sente_hand

    norm_errors   = []
    norm_warnings = []

    # --- board="initial" ---
    if board == "initial":
        if sente_hand:
            norm_warnings.append(
                "board='initial' was specified; sente_hand is ignored. "
                "Standard starting position has no pieces in hand."
            )
        board      = list(INITIAL_BOARD)
        sente_hand = {}

    # --- 盤面エントリの正規化 ---
    norm_board = []
    for i, entry in enumerate(board):
        if not isinstance(entry, dict):
            norm_errors.append(
                f"board[{i}] must be a dict, got {type(entry).__name__!r}."
            )
            continue

        raw_piece    = entry.get("piece", "")
        raw_pos      = entry.get("pos")
        raw_side     = entry.get("side", "")
        raw_promoted = entry.get("promoted", False)

        piece, promoted_from_name = normalize_piece(str(raw_piece))
        if piece is None:
            valid = "K/king/玉, R/rook/飛, B/bishop/角, G/gold/金, S/silver/銀, N/knight/桂, L/lance/香, P/pawn/歩"
            norm_errors.append(
                f"board[{i}]: Unknown piece name {raw_piece!r}. Valid names: {valid}."
            )
            continue

        if raw_pos is None:
            norm_errors.append(
                f"board[{i}]: Missing 'pos'. Use \"5a\", \"５一\", or (file, rank) tuple."
            )
            continue
        pos = normalize_pos(raw_pos)
        if pos is None:
            norm_errors.append(
                f"board[{i}]: Invalid position {raw_pos!r}. "
                f"file must be 1-9, rank must be 1-9 (or a-i / 一-九)."
            )
            continue

        side = normalize_side(str(raw_side))
        if side is None:
            norm_errors.append(
                f"board[{i}]: Unknown side {raw_side!r}. "
                f"Use 'sente'/'b'/'先手' or 'gote'/'w'/'後手'."
            )
            continue

        # "promoted" は駒名の '+' 表記と entry["promoted"] フラグの OR
        norm_board.append({
            "piece":    piece,
            "pos":      pos,
            "side":     side,
            "promoted": promoted_from_name or bool(raw_promoted),
        })

    # --- 先手持ち駒の正規化 ---
    norm_sente_hand = {}
    for raw_key, count in sente_hand.items():
        piece, promoted_from_name = normalize_piece(str(raw_key))
        if piece is None:
            norm_errors.append(
                f"sente_hand: Unknown piece name {raw_key!r}. Valid: K, R, B, G, S, N, L, P."
            )
            continue
        if promoted_from_name:
            norm_errors.append(
                f"sente_hand: Promoted piece {raw_key!r} cannot be in hand. Use '{piece}' instead."
            )
            continue
        if not isinstance(count, int) or count <= 0:
            norm_errors.append(
                f"sente_hand: Invalid count for {raw_key!r}: {count!r}. Count must be integer >= 1."
            )
            continue
        norm_sente_hand[piece] = norm_sente_hand.get(piece, 0) + count

    # --- 手番の正規化 ---
    norm_turn = normalize_side(str(turn))
    if norm_turn is None:
        norm_errors.append(
            f"Invalid turn {turn!r}. "
            f"Use 'sente'/'b'/'先手'/'black' or 'gote'/'w'/'後手'/'white'."
        )

    if norm_errors:
        if debug:
            print(f"[build_sfen] Normalization errors: {norm_errors}", file=sys.stderr)
        return _error_result(norm_sente_hand, norm_errors, norm_warnings)

    # --- バリデーション（1パス）---
    val_errors, val_warnings, board_counts = _validate(norm_board, norm_sente_hand, tsume)
    all_errors   = val_errors
    all_warnings = norm_warnings + val_warnings

    if debug:
        print(f"[build_sfen] Validation: {len(all_errors)} errors, {len(all_warnings)} warnings.",
              file=sys.stderr)

    if all_errors:
        return _error_result(norm_sente_hand, all_errors, all_warnings)

    # --- 後手持ち駒の自動計算（board_counts を再利用）---
    gote_hand = {}
    for piece in HAND_ORDER:
        gote_c = MAX_COUNT[piece] - board_counts.get(piece, 0) - norm_sente_hand.get(piece, 0)
        if gote_c > 0:
            gote_hand[piece] = gote_c

    # --- SFEN組み立て ---
    board_block = build_board_block(norm_board)
    turn_block  = TURN_TO_SFEN[norm_turn]
    hand_block  = build_hand_block(norm_sente_hand, gote_hand)
    sfen        = f"{board_block} {turn_block} {hand_block} 1"

    if debug:
        print(f"[build_sfen] SFEN: {sfen}", file=sys.stderr)

    # --- 王手チェック（tsume=True のとき、python-shogi 必須）---
    if tsume:
        sente_in_check, gote_in_check = detect_check(sfen)
        if sente_in_check is None and not _SHOGI_AVAILABLE:
            all_warnings.append(
                "Check detection skipped: python-shogi is not installed. "
                "Install it with: pip install python-shogi"
            )
        else:
            check_errors = []
            for in_check, side_name in ((sente_in_check, "sente"), (gote_in_check, "gote")):
                if in_check:
                    check_errors.append(
                        f"Illegal position: {side_name}'s king is in check at the start. "
                        f"The position before sente moves must not have {side_name}'s king in check."
                    )
            if check_errors:
                return {
                    "sfen": "",
                    "gote_hand": gote_hand,
                    "sente_hand_used": norm_sente_hand,
                    "validation": {"ok": False, "errors": check_errors, "warnings": all_warnings},
                }

        if debug and _SHOGI_AVAILABLE:
            print(f"[build_sfen] Check: sente={sente_in_check}, gote={gote_in_check}",
                  file=sys.stderr)

    return {
        "sfen": sfen,
        "gote_hand": gote_hand,
        "sente_hand_used": norm_sente_hand,
        "validation": {"ok": True, "errors": [], "warnings": all_warnings},
    }


def parse_sfen(sfen_str, debug=False):
    """
    SFEN文字列を解析して構造化辞書を返す。

    Args:
        sfen_str: SFEN文字列
        debug:    True にすると処理ログを stderr に出力する。

    Returns:
        {"board": list, "sente_hand": dict, "gote_hand": dict,
         "turn": str, "errors": list}
    """
    if debug:
        print(f"[parse_sfen] START: {sfen_str!r}", file=sys.stderr)

    errors        = []
    board_entries = []
    sente_hand    = {}
    gote_hand     = {}
    turn          = ""

    if not isinstance(sfen_str, str):
        errors.append(f"sfen_str must be a string, got {type(sfen_str).__name__!r}.")
        return {"board": [], "sente_hand": {}, "gote_hand": {}, "turn": "", "errors": errors}

    parts = sfen_str.strip().split(" ")
    if len(parts) != 4:
        errors.append(
            f"Invalid SFEN format: expected 4 space-separated parts, got {len(parts)}. "
            f"Input: {sfen_str!r}"
        )
        return {"board": [], "sente_hand": {}, "gote_hand": {}, "turn": "", "errors": errors}

    board_str, turn_str, hand_str, _ = parts

    # 手番
    if   turn_str == "b": turn = "sente"
    elif turn_str == "w": turn = "gote"
    else:
        errors.append(f"Invalid turn {turn_str!r} in SFEN. Expected 'b' (sente) or 'w' (gote).")

    # 持ち駒
    if hand_str != "-":
        i = 0
        while i < len(hand_str):
            count_str = ""
            while i < len(hand_str) and hand_str[i].isdigit():
                count_str += hand_str[i]
                i += 1
            if i >= len(hand_str):
                errors.append(f"Unexpected end of hand string after digits {count_str!r}.")
                break
            letter = hand_str[i]
            i += 1
            base_piece = letter.upper()
            if base_piece not in MAX_COUNT:
                errors.append(f"Unknown piece {letter!r} in hand string {hand_str!r}.")
                continue
            count = int(count_str) if count_str else 1
            if letter.isupper():
                sente_hand[base_piece] = sente_hand.get(base_piece, 0) + count
            else:
                gote_hand[base_piece]  = gote_hand.get(base_piece, 0) + count

    # 盤面
    rank_strs = board_str.split("/")
    if len(rank_strs) != 9:
        errors.append(
            f"Invalid board block: expected 9 ranks separated by '/', got {len(rank_strs)}."
        )
    else:
        for rank_idx, rank_s in enumerate(rank_strs):
            rank  = rank_idx + 1
            file_ = 9
            j     = 0
            while j < len(rank_s):
                ch = rank_s[j]

                if ch.isdigit():
                    file_ -= int(ch)
                    j += 1
                    continue

                promoted = False
                if ch == "+":
                    promoted = True
                    j += 1
                    if j >= len(rank_s):
                        errors.append(f"rank {rank}: '+' at end of rank string.")
                        break
                    ch = rank_s[j]

                base_piece = ch.upper()
                side       = "sente" if ch.isupper() else "gote"

                if base_piece not in MAX_COUNT:
                    errors.append(f"rank {rank}: Unknown piece character {ch!r}.")
                    j += 1
                    continue

                if file_ < 1:
                    errors.append(f"rank {rank}: Too many pieces in rank string {rank_s!r}.")
                    break

                board_entries.append({
                    "piece":    base_piece,
                    "pos":      (file_, rank),
                    "side":     side,
                    "promoted": promoted,
                })
                file_ -= 1
                j += 1

    if debug:
        print(f"[parse_sfen] Parsed {len(board_entries)} pieces, "
              f"sente_hand={sente_hand}, gote_hand={gote_hand}, turn={turn!r}",
              file=sys.stderr)

    return {
        "board":      board_entries,
        "sente_hand": sente_hand,
        "gote_hand":  gote_hand,
        "turn":       turn,
        "errors":     errors,
    }


def _error_result(norm_sente_hand, errors, warnings):
    """エラー時の戻り値を統一して生成するヘルパー。"""
    return {
        "sfen": "",
        "gote_hand": {},
        "sente_hand_used": norm_sente_hand,
        "validation": {"ok": False, "errors": errors, "warnings": warnings},
    }
