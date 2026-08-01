"""
core.py — 公開関数: build_sfen / parse_sfen
"""

import sys

from .builders import build_board_block, build_hand_block
from .constants import HAND_ORDER, MAX_COUNT, PIECE_FULL_NAME, PROMOTABLE, TURN_TO_SFEN
from .initial_board import INITIAL_BOARD
from .normalizers import normalize_piece, normalize_pos, normalize_side
from .validators import _SHOGI_AVAILABLE, _validate, detect_check


def build_sfen(
    board=None,
    sente_hand=None,
    turn="sente",
    tsume=True,
    debug=False,
    move_number=1,
):
    """将棋盤面データを受け取り、SFEN文字列と付随情報を返す。

    ``move_number`` は後方互換性のため既存の引数群の末尾に追加している。
    不正入力は例外を送出せず、従来の ``validation`` 形式で返す。
    """
    if debug:
        print("[build_sfen] START", file=sys.stderr)

    board = [] if board is None else board
    sente_hand = {} if sente_hand is None else sente_hand
    norm_errors = []
    norm_warnings = []
    norm_sente_hand = {}

    # コンテナを走査する前にライブラリ境界で型を確定する。
    if not isinstance(board, list) and board != "initial":
        norm_errors.append(
            f"board must be a list of dicts or 'initial', got {type(board).__name__!r}."
        )
    if not isinstance(sente_hand, dict):
        norm_errors.append(
            f"sente_hand must be a dict, got {type(sente_hand).__name__!r}."
        )
    if not isinstance(tsume, bool):
        norm_errors.append(f"tsume must be a bool, got {type(tsume).__name__!r}.")
    if isinstance(move_number, bool) or not isinstance(move_number, int) or move_number < 1:
        norm_errors.append(
            f"move_number must be an integer >= 1, got {move_number!r}."
        )

    if norm_errors:
        return _error_result(norm_sente_hand, norm_errors, norm_warnings)

    # board="initial" は従来どおり、指定された先手持駒を警告付きで無視する。
    if board == "initial":
        if sente_hand:
            norm_warnings.append(
                "board='initial' was specified; sente_hand is ignored. "
                "Standard starting position has no pieces in hand."
            )
        board = list(INITIAL_BOARD)
        sente_hand = {}

    # 盤面エントリの正規化
    norm_board = []
    for i, entry in enumerate(board):
        if not isinstance(entry, dict):
            norm_errors.append(
                f"board[{i}] must be a dict, got {type(entry).__name__!r}."
            )
            continue

        raw_piece = entry.get("piece", "")
        raw_pos = entry.get("pos")
        raw_side = entry.get("side", "")
        raw_promoted = entry.get("promoted", False)

        if not isinstance(raw_promoted, bool):
            norm_errors.append(
                f"board[{i}]: 'promoted' must be a bool, "
                f"got {type(raw_promoted).__name__!r}."
            )
            continue

        piece, promoted_from_name = normalize_piece(str(raw_piece))
        if piece is None:
            valid = (
                "K/king/玉, R/rook/飛, B/bishop/角, G/gold/金, "
                "S/silver/銀, N/knight/桂, L/lance/香, P/pawn/歩"
            )
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
                "file must be 1-9, rank must be 1-9 (or a-i / 一-九)."
            )
            continue

        side = normalize_side(str(raw_side))
        if side is None:
            norm_errors.append(
                f"board[{i}]: Unknown side {raw_side!r}. "
                "Use 'sente'/'b'/'先手' or 'gote'/'w'/'後手'."
            )
            continue

        norm_board.append(
            {
                "piece": piece,
                "pos": pos,
                "side": side,
                "promoted": promoted_from_name or raw_promoted,
            }
        )

    # 先手持駒の正規化。不正な項目は sente_hand_used に残さない。
    for raw_key, count in sente_hand.items():
        piece, promoted_from_name = normalize_piece(str(raw_key))
        if piece is None:
            norm_errors.append(
                f"sente_hand: Unknown piece name {raw_key!r}. "
                "Valid: R, B, G, S, N, L, P."
            )
            continue
        if promoted_from_name:
            norm_errors.append(
                f"sente_hand: Promoted piece {raw_key!r} cannot be in hand. "
                f"Use '{piece}' instead."
            )
            continue
        if piece == "K":
            norm_errors.append(
                f"sente_hand: King {raw_key!r} cannot be in hand."
            )
            continue
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            norm_errors.append(
                f"sente_hand: Invalid count for {raw_key!r}: {count!r}. "
                "Count must be an integer >= 1 (bool is not accepted)."
            )
            continue
        norm_sente_hand[piece] = norm_sente_hand.get(piece, 0) + count

    norm_turn = normalize_side(str(turn))
    if norm_turn is None:
        norm_errors.append(
            f"Invalid turn {turn!r}. "
            "Use 'sente'/'b'/'先手'/'black' or 'gote'/'w'/'後手'/'white'."
        )

    if norm_errors:
        if debug:
            print(f"[build_sfen] Normalization errors: {norm_errors}", file=sys.stderr)
        return _error_result(norm_sente_hand, norm_errors, norm_warnings)

    val_errors, val_warnings, board_counts = _validate(
        norm_board, norm_sente_hand, tsume
    )
    all_errors = val_errors
    all_warnings = norm_warnings + val_warnings

    if debug:
        print(
            f"[build_sfen] Validation: {len(all_errors)} errors, "
            f"{len(all_warnings)} warnings.",
            file=sys.stderr,
        )

    if all_errors:
        return _error_result(norm_sente_hand, all_errors, all_warnings)

    gote_hand = {}
    for piece in HAND_ORDER:
        gote_count = (
            MAX_COUNT[piece]
            - board_counts.get(piece, 0)
            - norm_sente_hand.get(piece, 0)
        )
        if gote_count > 0:
            gote_hand[piece] = gote_count

    board_block = build_board_block(norm_board)
    turn_block = TURN_TO_SFEN[norm_turn]
    hand_block = build_hand_block(norm_sente_hand, gote_hand)
    sfen = f"{board_block} {turn_block} {hand_block} {move_number}"

    if debug:
        print(f"[build_sfen] SFEN: {sfen}", file=sys.stderr)

    if tsume:
        sente_in_check, gote_in_check = detect_check(sfen)
        if sente_in_check is None and not _SHOGI_AVAILABLE:
            all_warnings.append(
                "Check detection skipped: python-shogi is not installed. "
                "Install it with: pip install python-shogi"
            )
        else:
            check_errors = []
            for in_check, side_name in (
                (sente_in_check, "sente"),
                (gote_in_check, "gote"),
            ):
                if in_check:
                    check_errors.append(
                        f"Illegal position: {side_name}'s king is in check at the start. "
                        "The position before sente moves must not have "
                        f"{side_name}'s king in check."
                    )
            if check_errors:
                return {
                    "sfen": "",
                    "gote_hand": gote_hand,
                    "sente_hand_used": norm_sente_hand,
                    "validation": {
                        "ok": False,
                        "errors": check_errors,
                        "warnings": all_warnings,
                    },
                }

        if debug and _SHOGI_AVAILABLE:
            print(
                f"[build_sfen] Check: sente={sente_in_check}, gote={gote_in_check}",
                file=sys.stderr,
            )

    return {
        "sfen": sfen,
        "gote_hand": gote_hand,
        "sente_hand_used": norm_sente_hand,
        "validation": {"ok": True, "errors": [], "warnings": all_warnings},
    }


def parse_sfen(sfen_str, debug=False):
    """SFEN文字列を厳密に検証し、構造化辞書へ変換する。

    4フィールドに分割できる場合、エラーがあっても安全に解析できた部分は
    従来どおり返す。無効な駒トークンや0枚の持駒は部分結果へ含めない。
    ``board[].pos`` はJSON親和性の高い ``[file, rank]`` 形式で返す。
    """
    if debug:
        print(f"[parse_sfen] START: {sfen_str!r}", file=sys.stderr)

    errors = []
    board_entries = []
    sente_hand = {}
    gote_hand = {}
    turn = ""
    move_number = 0

    if not isinstance(sfen_str, str):
        errors.append(f"sfen_str must be a string, got {type(sfen_str).__name__!r}.")
        return _parse_result([], {}, {}, "", 0, errors)

    parts = sfen_str.strip().split()
    if len(parts) != 4:
        errors.append(
            f"Invalid SFEN format: expected 4 whitespace-separated fields, "
            f"got {len(parts)}. Input: {_preview(sfen_str)}"
        )
        return _parse_result([], {}, {}, "", 0, errors)

    board_str, turn_str, hand_str, move_str = parts

    if turn_str == "b":
        turn = "sente"
    elif turn_str == "w":
        turn = "gote"
    else:
        errors.append(
            f"Invalid turn {turn_str!r} in SFEN. Expected 'b' (sente) or 'w' (gote)."
        )

    if _is_ascii_integer(move_str):
        parsed_move_number = _ascii_decimal_to_int(move_str)
        if parsed_move_number >= 1:
            move_number = parsed_move_number
        else:
            errors.append(
                f"Invalid move number {_preview(move_str)} in SFEN. "
                "Expected an integer >= 1."
            )
    else:
        errors.append(
            f"Invalid move number {move_str!r} in SFEN. Expected an integer >= 1."
        )

    _parse_hand_block(hand_str, sente_hand, gote_hand, errors)
    _parse_board_block(board_str, board_entries, errors)
    _validate_parsed_piece_counts(board_entries, sente_hand, gote_hand, errors)

    if debug:
        print(
            f"[parse_sfen] Parsed {len(board_entries)} pieces, "
            f"sente_hand={sente_hand}, gote_hand={gote_hand}, "
            f"turn={turn!r}, move_number={move_number}",
            file=sys.stderr,
        )

    return _parse_result(
        board_entries, sente_hand, gote_hand, turn, move_number, errors
    )


def _parse_hand_block(hand_str, sente_hand, gote_hand, errors):
    if hand_str == "-":
        return

    i = 0
    while i < len(hand_str):
        count_start = i
        while i < len(hand_str) and "0" <= hand_str[i] <= "9":
            i += 1
        count_str = hand_str[count_start:i]

        if i >= len(hand_str):
            errors.append(
                f"Unexpected end of hand string after a {len(count_str)}-digit count."
            )
            break

        letter = hand_str[i]
        i += 1
        base_piece = letter.upper()

        if base_piece not in MAX_COUNT or not letter.isascii() or not letter.isalpha():
            errors.append(
                f"Unknown piece {letter!r} in hand string {_preview(hand_str)}."
            )
            continue
        if base_piece == "K":
            errors.append(f"King {letter!r} cannot be in an SFEN hand.")
            continue

        normalized_count = count_str.lstrip("0") or "0"
        maximum_count = str(MAX_COUNT[base_piece])
        if len(normalized_count) > len(maximum_count) or (
            len(normalized_count) == len(maximum_count)
            and normalized_count > maximum_count
        ):
            errors.append(
                f"Hand count for {letter!r} exceeds the piece maximum "
                f"of {MAX_COUNT[base_piece]}."
            )
            continue
        count = int(normalized_count) if count_str else 1
        if count < 1:
            errors.append(
                f"Invalid hand count {count_str!r} for piece {letter!r}. "
                "Count must be an integer >= 1."
            )
            continue
        hand = sente_hand if letter.isupper() else gote_hand
        hand[base_piece] = hand.get(base_piece, 0) + count


def _parse_board_block(board_str, board_entries, errors):
    rank_strings = board_str.split("/")
    if len(rank_strings) != 9:
        errors.append(
            f"Invalid board block: expected 9 ranks separated by '/', "
            f"got {len(rank_strings)}."
        )
        return

    for rank_index, rank_str in enumerate(rank_strings):
        rank = rank_index + 1
        expanded_width = 0
        i = 0

        while i < len(rank_str):
            ch = rank_str[i]

            if "0" <= ch <= "9":
                digit_start = i
                while i < len(rank_str) and "0" <= rank_str[i] <= "9":
                    i += 1
                digit_run = rank_str[digit_start:i]
                if len(digit_run) > 1:
                    errors.append(
                        f"rank {rank}: Empty-square counts must be one ASCII digit; "
                        f"got {_preview(digit_run)} in {_preview(rank_str)}."
                    )
                elif ch == "0":
                    errors.append(
                        f"rank {rank}: Invalid empty-square count '0'. "
                        "Expected one ASCII digit from '1' to '9'."
                    )
                else:
                    expanded_width += int(ch)
                continue

            if ch.isdigit():
                digit_start = i
                while i < len(rank_str) and rank_str[i].isdigit() and not (
                    "0" <= rank_str[i] <= "9"
                ):
                    i += 1
                digit_run = rank_str[digit_start:i]
                errors.append(
                    f"rank {rank}: Invalid non-ASCII empty-square digit {digit_run!r}. "
                    "Expected one ASCII digit from '1' to '9'."
                )
                continue

            promoted = ch == "+"
            if promoted:
                i += 1
                if i >= len(rank_str):
                    errors.append(f"rank {rank}: '+' at end of rank string.")
                    break
                ch = rank_str[i]

            base_piece = ch.upper()
            is_ascii_piece = (
                ch.isascii() and ch.isalpha() and base_piece in MAX_COUNT
            )
            file_number = 9 - expanded_width

            if not is_ascii_piece:
                if promoted:
                    errors.append(
                        f"rank {rank}: '+' must be followed by one of R/B/S/N/L/P, "
                        f"got {ch!r}."
                    )
                else:
                    errors.append(f"rank {rank}: Unknown piece character {ch!r}.")
                expanded_width += 1
                i += 1
                continue

            if promoted and base_piece not in PROMOTABLE:
                errors.append(
                    f"rank {rank}: Cannot promote {base_piece}. "
                    "Only R, B, S, N, L, P can follow '+'."
                )

            if 1 <= file_number <= 9:
                board_entries.append(
                    {
                        "piece": base_piece,
                        "pos": [file_number, rank],
                        "side": "sente" if ch.isupper() else "gote",
                        "promoted": promoted,
                    }
                )
            expanded_width += 1
            i += 1

        if expanded_width != 9:
            errors.append(
                f"rank {rank}: Expanded width must be exactly 9 squares, "
                f"got {expanded_width} from {_preview(rank_str)}."
            )


def _validate_parsed_piece_counts(board, sente_hand, gote_hand, errors):
    board_counts = {}
    for entry in board:
        piece = entry["piece"]
        board_counts[piece] = board_counts.get(piece, 0) + 1

    for piece, maximum in MAX_COUNT.items():
        board_count = board_counts.get(piece, 0)
        sente_count = sente_hand.get(piece, 0)
        gote_count = gote_hand.get(piece, 0)
        total = board_count + sente_count + gote_count
        if total > maximum:
            errors.append(
                f"Piece count exceeds maximum: {piece} "
                f"({PIECE_FULL_NAME.get(piece, piece)}) has {total} (max {maximum}). "
                f"Board: {board_count}, sente_hand: {sente_count}, "
                f"gote_hand: {gote_count}."
            )


def _is_ascii_integer(value):
    return bool(value) and all("0" <= ch <= "9" for ch in value)


def _ascii_decimal_to_int(value):
    """Pythonの10進数文字列桁数制限に依存せず非負整数へ変換する。"""
    result = 0
    for start in range(0, len(value), 9):
        chunk = value[start:start + 9]
        result = result * (10 ** len(chunk)) + int(chunk)
    return result


def _preview(value, limit=40):
    """エラーメッセージへ巨大な入力全体を複製しない短縮表現を返す。"""
    if len(value) <= limit:
        return repr(value)
    return f"{value[:limit]!r}... ({len(value)} chars)"


def _parse_result(board, sente_hand, gote_hand, turn, move_number, errors):
    return {
        "board": board,
        "sente_hand": sente_hand,
        "gote_hand": gote_hand,
        "turn": turn,
        "move_number": move_number,
        "errors": errors,
    }


def _error_result(norm_sente_hand, errors, warnings):
    """エラー時の戻り値を統一して生成するヘルパー。"""
    return {
        "sfen": "",
        "gote_hand": {},
        "sente_hand_used": norm_sente_hand,
        "validation": {"ok": False, "errors": errors, "warnings": warnings},
    }
