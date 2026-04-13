"""
test_sfen_builder.py — SFEN Builderのテストスイート（60テストケース）
標準ライブラリ unittest を使用。
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfen_builder.sfen_builder import build_sfen, parse_sfen


# ==============================================================================
# TestNormalize — 正規化関数のテスト（8件）
# ==============================================================================
class TestNormalize(unittest.TestCase):

    def test_normalize_piece_english(self):
        """英語エイリアスで駒名を正規化できる"""
        result = build_sfen(board=[
            {"piece": "king", "pos": (5, 9), "side": "sente", "promoted": False}
        ])
        self.assertEqual(result["validation"]["errors"], [])

    def test_normalize_piece_japanese(self):
        """日本語エイリアスで駒名を正規化できる"""
        result = build_sfen(board=[
            {"piece": "飛", "pos": (2, 8), "side": "sente", "promoted": False}
        ])
        self.assertEqual(result["validation"]["errors"], [])

    def test_normalize_piece_case_insensitive(self):
        """大文字小文字を区別しない"""
        result = build_sfen(board=[
            {"piece": "BISHOP", "pos": (8, 8), "side": "sente", "promoted": False}
        ])
        self.assertEqual(result["validation"]["errors"], [])

    def test_normalize_piece_unknown_returns_error(self):
        """未知の駒名はエラーを返す"""
        result = build_sfen(board=[
            {"piece": "X", "pos": (5, 5), "side": "sente", "promoted": False}
        ])
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(any("Unknown piece" in e for e in result["validation"]["errors"]))

    def test_normalize_pos_letter_format(self):
        """座標 "5a" 形式を受け付ける（file=5, rank=a=1 → rank1の先頭セグメントに K が出現）"""
        result = build_sfen(board=[
            {"piece": "K", "pos": "5a", "side": "sente", "promoted": False}
        ])
        self.assertEqual(result["validation"]["errors"], [])
        # rank1 = SFENの最初のセグメント。file5 = 左4マス空き + K + 右4マス空き = "4K4"
        board_block = result["sfen"].split(" ")[0]
        self.assertTrue(board_block.startswith("4K4"), f"Expected rank1 to start with '4K4', got: {board_block}")

    def test_normalize_pos_kanji_format(self):
        """座標 "５一" 形式（全角数字＋漢数字）を受け付ける"""
        result = build_sfen(board=[
            {"piece": "K", "pos": "５一", "side": "sente", "promoted": False}
        ])
        self.assertEqual(result["validation"]["errors"], [])

    def test_normalize_pos_tuple_format(self):
        """座標 (file, rank) タプル形式を受け付ける"""
        result = build_sfen(board=[
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False}
        ])
        self.assertEqual(result["validation"]["errors"], [])

    def test_normalize_pos_out_of_range_error(self):
        """範囲外の座標はエラーを返す"""
        result = build_sfen(board=[
            {"piece": "K", "pos": (10, 1), "side": "sente", "promoted": False}
        ])
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(any("Invalid position" in e for e in result["validation"]["errors"]))


# ==============================================================================
# TestBuildSfenNormal — 正常系テスト（10件）
# ==============================================================================
class TestBuildSfenNormal(unittest.TestCase):

    def test_empty_board(self):
        """空盤面では全38駒が後手持ち駒として自動計算される（玉は持ち駒に入らない）"""
        result = build_sfen(board=[], turn="sente")
        self.assertEqual(result["sfen"], "9/9/9/9/9/9/9/9/9 b 2r2b4g4s4n4l18p 1")
        self.assertTrue(result["validation"]["ok"])

    def test_initial_board(self):
        """初期配置は標準SFEN文字列と一致する"""
        result = build_sfen(board="initial")
        self.assertEqual(
            result["sfen"],
            "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
        )

    def test_single_sente_piece(self):
        """先手の駒1枚だけの盤面を正しく生成する"""
        result = build_sfen(board=[
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False}
        ])
        self.assertIn("K", result["sfen"])
        self.assertEqual(result["validation"]["errors"], [])

    def test_promoted_sente_piece(self):
        """先手の成り駒は '+' 付きで出力される（竜が後手玉と別筋・別段）"""
        # 竜(5五)が後手玉(1一)と同筋・同段・斜め1マス以内にならないよう配置
        result = build_sfen(board=[
            {"piece": "R", "pos": (5, 5), "side": "sente", "promoted": True},
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (1, 1), "side": "gote",  "promoted": False},
        ])
        self.assertIn("+R", result["sfen"])
        self.assertEqual(result["validation"]["errors"], [])

    def test_gote_piece_lowercase(self):
        """後手の駒は小文字で出力される"""
        result = build_sfen(board=[
            {"piece": "K", "pos": (5, 1), "side": "gote", "promoted": False}
        ])
        self.assertIn("k", result["sfen"])

    def test_gote_promoted_piece(self):
        """後手の成り駒は '+' + 小文字で出力される"""
        result = build_sfen(board=[
            {"piece": "B", "pos": (5, 5), "side": "gote", "promoted": True},
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
        ])
        self.assertIn("+b", result["sfen"])

    def test_turn_gote(self):
        """手番が後手の場合 'w' が出力される"""
        result = build_sfen(board=[], turn="gote")
        self.assertIn(" w ", result["sfen"])

    def test_piece_name_alias_romaji(self):
        """ローマ字エイリアス (hisha) で指定できる"""
        result = build_sfen(board=[
            {"piece": "hisha", "pos": (5, 5), "side": "sente", "promoted": False}
        ])
        self.assertEqual(result["validation"]["errors"], [])
        self.assertIn("R", result["sfen"])

    def test_spec_example(self):
        """仕様書の例: 6k2/4B4/9/... b G3SP2r... 1"""
        # 盤面: 後手玉を9筋6段目、先手角を5筋8段目
        result = build_sfen(
            board=[
                {"piece": "K", "pos": (3, 1), "side": "gote", "promoted": False},
                {"piece": "B", "pos": (5, 2), "side": "sente", "promoted": False},
            ],
            sente_hand={"G": 1, "S": 1, "P": 3},
            turn="sente"
        )
        self.assertEqual(result["validation"]["errors"], [])
        self.assertIn(" b ", result["sfen"])
        # 先手持ち駒に G, S, 3P が含まれるか確認
        hand_part = result["sfen"].split(" ")[2]
        self.assertIn("G", hand_part)
        self.assertIn("S", hand_part)
        self.assertIn("3P", hand_part)

    def test_initial_with_sente_hand_warns(self):
        """board='initial' + sente_hand指定は警告を出して手を無視する"""
        result = build_sfen(board="initial", sente_hand={"P": 1})
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(any("initial" in w for w in result["validation"]["warnings"]))
        # 初期配置SFENと一致すること
        self.assertEqual(
            result["sfen"],
            "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
        )


# ==============================================================================
# TestAutoCompletion — 持ち駒自動計算テスト（4件）
# ==============================================================================
class TestAutoCompletion(unittest.TestCase):

    def test_two_kings_only(self):
        """先後玉のみの盤面では残り全駒が後手持ち駒になる"""
        result = build_sfen(board=[
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
        ])
        gote = result["gote_hand"]
        self.assertEqual(gote.get("R", 0), 2)
        self.assertEqual(gote.get("B", 0), 2)
        self.assertEqual(gote.get("G", 0), 4)
        self.assertEqual(gote.get("P", 0), 18)

    def test_sente_hand_reduces_gote_hand(self):
        """先手持ち駒が指定されると後手持ち駒が減る"""
        result = build_sfen(
            board=[
                {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
                {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
            ],
            sente_hand={"R": 1}
        )
        # 飛車は全2枚。先手が1枚持つなら後手持ち駒は1枚
        self.assertEqual(result["gote_hand"].get("R", 0), 1)

    def test_zero_count_omitted_from_gote_hand(self):
        """後手持ち駒が0枚の駒はgote_handのキーに含まれない"""
        result = build_sfen(
            board=[
                {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
                {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
            ],
            sente_hand={"R": 2}  # 飛車は全2枚を先手が保持
        )
        self.assertNotIn("R", result["gote_hand"])

    def test_all_pieces_on_board_hand_dash(self):
        """全駒が盤面にある場合、持ち駒ブロックは '-'"""
        result = build_sfen(board="initial")
        self.assertTrue(result["sfen"].endswith("b - 1"))


# ==============================================================================
# TestErrors — エラー系テスト（10件）
# ==============================================================================
class TestErrors(unittest.TestCase):

    def _has_error(self, result, keyword):
        return any(keyword.lower() in e.lower() for e in result["validation"]["errors"])

    def test_error_duplicate_position(self):
        """同じ座標に2枚は重複エラー"""
        result = build_sfen(board=[
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
            {"piece": "R", "pos": (5, 9), "side": "sente", "promoted": False},
        ])
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "Duplicate"))

    def test_error_piece_count_18_pawns_exceed(self):
        """歩を19枚以上指定するとエラー"""
        board = [{"piece": "P", "pos": (f, 7), "side": "sente", "promoted": False}
                 for f in range(1, 10)]
        board += [{"piece": "P", "pos": (f, 3), "side": "gote", "promoted": False}
                  for f in range(1, 10)]
        result = build_sfen(
            board=board,
            sente_hand={"P": 1}  # 18枚盤面 + 1枚持ち駒 = 19枚 → エラー
        )
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "exceeds maximum"))

    def test_error_piece_count_sente_hand_overflow(self):
        """持ち駒だけで最大枚数を超えるとエラー"""
        result = build_sfen(
            board=[],
            sente_hand={"R": 3}  # 飛車は最大2枚
        )
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "exceeds maximum"))

    def test_error_cannot_promote_K(self):
        """玉将を成りにするとエラー"""
        result = build_sfen(board=[
            {"piece": "K", "pos": (5, 5), "side": "sente", "promoted": True}
        ])
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "Cannot promote"))

    def test_error_cannot_promote_G(self):
        """金将を成りにするとエラー"""
        result = build_sfen(board=[
            {"piece": "G", "pos": (5, 5), "side": "sente", "promoted": True}
        ])
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "Cannot promote"))

    def test_error_invalid_coord_out_of_range(self):
        """file=10は範囲外エラー"""
        result = build_sfen(board=[
            {"piece": "K", "pos": (10, 1), "side": "sente", "promoted": False}
        ])
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "Invalid position"))

    def test_error_invalid_coord_bad_rank_letter(self):
        """rank文字 'j' は無効（a-i のみ有効）"""
        result = build_sfen(board=[
            {"piece": "K", "pos": "5j", "side": "sente", "promoted": False}
        ])
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "Invalid position"))

    def test_error_unknown_piece_name(self):
        """未知の駒名 'X' はエラー"""
        result = build_sfen(board=[
            {"piece": "X", "pos": (5, 5), "side": "sente", "promoted": False}
        ])
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "Unknown piece"))

    def test_error_promoted_piece_in_hand(self):
        """持ち駒に成り駒を指定するとエラー"""
        result = build_sfen(
            board=[],
            sente_hand={"+R": 1}
        )
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "cannot be in hand") or
                        self._has_error(result, "Promoted piece"))

    def test_error_sente_hand_zero_count(self):
        """持ち駒の枚数0はエラー"""
        result = build_sfen(
            board=[],
            sente_hand={"P": 0}
        )
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(self._has_error(result, "count") or self._has_error(result, "invalid"))


# ==============================================================================
# TestWarnings — 警告系テスト（8件）
# ==============================================================================
class TestWarnings(unittest.TestCase):

    def _has_warning(self, result, keyword):
        return any(keyword.lower() in w.lower() for w in result["validation"]["warnings"])

    def test_warning_double_pawn_sente(self):
        """先手の同筋二歩は警告を出してSFENを生成する"""
        result = build_sfen(board=[
            {"piece": "P", "pos": (5, 4), "side": "sente", "promoted": False},
            {"piece": "P", "pos": (5, 6), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (9, 9), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (9, 1), "side": "gote",  "promoted": False},
        ])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(self._has_warning(result, "Double pawn"))

    def test_warning_double_pawn_gote(self):
        """後手の同筋二歩は警告を出してSFENを生成する"""
        result = build_sfen(board=[
            {"piece": "P", "pos": (3, 3), "side": "gote", "promoted": False},
            {"piece": "P", "pos": (3, 5), "side": "gote", "promoted": False},
            {"piece": "K", "pos": (9, 9), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (9, 1), "side": "gote",  "promoted": False},
        ])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(self._has_warning(result, "Double pawn"))

    def test_warning_dead_pawn_sente_rank1(self):
        """先手の歩が1段目は行き所なし警告"""
        result = build_sfen(board=[
            {"piece": "P", "pos": (5, 1), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 2), "side": "gote",  "promoted": False},
        ])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(self._has_warning(result, "Dead piece"))

    def test_warning_dead_lance_sente_rank1(self):
        """先手の香が1段目は行き所なし警告"""
        result = build_sfen(board=[
            {"piece": "L", "pos": (1, 1), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 2), "side": "gote",  "promoted": False},
        ])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(self._has_warning(result, "Dead piece"))

    def test_warning_dead_knight_sente_rank1(self):
        """先手の桂が1段目は行き所なし警告"""
        result = build_sfen(board=[
            {"piece": "N", "pos": (2, 1), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 3), "side": "gote",  "promoted": False},
        ])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(self._has_warning(result, "Dead piece"))

    def test_warning_dead_knight_sente_rank2(self):
        """先手の桂が2段目も行き所なし警告"""
        result = build_sfen(board=[
            {"piece": "N", "pos": (2, 2), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 3), "side": "gote",  "promoted": False},
        ])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(self._has_warning(result, "Dead piece"))

    def test_warning_dead_gote_pawn_rank9(self):
        """後手の歩が9段目は行き所なし警告"""
        result = build_sfen(board=[
            {"piece": "P", "pos": (5, 9), "side": "gote", "promoted": False},
            {"piece": "K", "pos": (5, 8), "side": "sente", "promoted": False},
            {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
        ])
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(self._has_warning(result, "Dead piece"))

    def test_warning_sente_king_missing(self):
        """先手玉不在 + tsume=False（双玉モード）のとき警告が出る"""
        result = build_sfen(
            board=[{"piece": "K", "pos": (5, 1), "side": "gote", "promoted": False}],
            tsume=False  # 双玉モード: 先手玉不在を警告
        )
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(self._has_warning(result, "Sente king"))


# ==============================================================================
# TestTsumeMode — 詰将棋モードテスト（3件）
# ==============================================================================
class TestTsumeMode(unittest.TestCase):

    def test_tsume_suppresses_sente_king_warning(self):
        """tsume=True のとき先手玉不在の警告が出ない"""
        result = build_sfen(
            board=[
                {"piece": "K", "pos": (5, 1), "side": "gote", "promoted": False},
            ],
            tsume=True
        )
        self.assertTrue(result["validation"]["ok"])
        sente_king_warnings = [w for w in result["validation"]["warnings"]
                                if "sente king" in w.lower()]
        self.assertEqual(sente_king_warnings, [])

    def test_tsume_still_warns_gote_king_missing(self):
        """tsume=True でも後手玉不在は警告"""
        result = build_sfen(board=[], tsume=True)
        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(any("gote king" in w.lower() for w in result["validation"]["warnings"]))

    def test_tsume_normal_validation_still_runs(self):
        """tsume=True でも重複位置などのエラーは検出される"""
        result = build_sfen(
            board=[
                {"piece": "R", "pos": (5, 5), "side": "sente", "promoted": False},
                {"piece": "B", "pos": (5, 5), "side": "sente", "promoted": False},
            ],
            tsume=True
        )
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(any("Duplicate" in e for e in result["validation"]["errors"]))

    def test_tsume_error_gote_king_in_check(self):
        """tsume=True: 後手玉に王手がかかっている初形はエラー"""
        # 先手金5二 → 後手玉5一に隣接 = 王手
        result = build_sfen(
            board=[
                {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
                {"piece": "G", "pos": (5, 2), "side": "sente", "promoted": False},
            ],
            tsume=True
        )
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(any("gote's king is in check" in e for e in result["validation"]["errors"]))

    def test_tsume_error_sente_king_in_check(self):
        """tsume=True: 先手玉に王手がかかっている初形はエラー"""
        # 後手金5八 → 先手玉5九に隣接 = 王手
        result = build_sfen(
            board=[
                {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
                {"piece": "G", "pos": (5, 8), "side": "gote",  "promoted": False},
                {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
            ],
            tsume=True
        )
        self.assertFalse(result["validation"]["ok"])
        self.assertTrue(any("sente's king is in check" in e for e in result["validation"]["errors"]))

    def test_tsume_valid_no_check(self):
        """tsume=True: 王手なし局面は正常"""
        result = build_sfen(
            board=[
                {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
                {"piece": "P", "pos": (5, 3), "side": "sente", "promoted": False},
            ],
            sente_hand={"G": 1},
            tsume=True
        )
        self.assertTrue(result["validation"]["ok"])
        self.assertNotEqual(result["sfen"], "")


# ==============================================================================
# TestParseSfen — parse_sfen テスト（10件）
# ==============================================================================
class TestParseSfen(unittest.TestCase):

    def test_parse_initial_sfen(self):
        """初期配置SFENを正しくパースできる"""
        result = parse_sfen("lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["turn"], "sente")
        self.assertEqual(result["sente_hand"], {})
        self.assertEqual(result["gote_hand"],  {})
        # 40枚の駒が盤面にあるか確認
        self.assertEqual(len(result["board"]), 40)

    def test_parse_turn_b_is_sente(self):
        """手番 'b' は 'sente' に変換される"""
        result = parse_sfen("9/9/9/9/9/9/9/9/9 b - 1")
        self.assertEqual(result["turn"], "sente")
        self.assertEqual(result["errors"], [])

    def test_parse_turn_w_is_gote(self):
        """手番 'w' は 'gote' に変換される"""
        result = parse_sfen("9/9/9/9/9/9/9/9/9 w - 1")
        self.assertEqual(result["turn"], "gote")

    def test_parse_hand_multiple_pieces(self):
        """複数種・複数枚の持ち駒を正しくパースする"""
        result = parse_sfen("9/9/9/9/9/9/9/9/9 b 3S2Pg 1")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["sente_hand"].get("S"), 3)
        self.assertEqual(result["sente_hand"].get("P"), 2)
        self.assertEqual(result["gote_hand"].get("G"), 1)

    def test_parse_hand_single_piece_no_count(self):
        """枚数省略（1枚）の持ち駒を正しくパースする"""
        result = parse_sfen("9/9/9/9/9/9/9/9/9 b Rg 1")
        self.assertEqual(result["sente_hand"].get("R"), 1)
        self.assertEqual(result["gote_hand"].get("G"), 1)

    def test_parse_hand_empty_dash(self):
        """持ち駒が '-' のとき両持ち駒は空"""
        result = parse_sfen("9/9/9/9/9/9/9/9/9 b - 1")
        self.assertEqual(result["sente_hand"], {})
        self.assertEqual(result["gote_hand"],  {})

    def test_parse_promoted_pieces(self):
        """成り駒（+R, +b等）を正しくパースする"""
        result = parse_sfen("9/9/9/9/4+R4/9/9/9/9 b - 1")
        self.assertEqual(result["errors"], [])
        promoted_entries = [e for e in result["board"] if e["promoted"]]
        self.assertEqual(len(promoted_entries), 1)
        self.assertEqual(promoted_entries[0]["piece"], "R")
        self.assertEqual(promoted_entries[0]["side"], "sente")

    def test_parse_gote_pieces_lowercase(self):
        """小文字は後手の駒として解釈される"""
        result = parse_sfen("9/9/9/9/4k4/9/9/9/9 b - 1")
        king = next((e for e in result["board"] if e["piece"] == "K"), None)
        self.assertIsNotNone(king)
        self.assertEqual(king["side"], "gote")

    def test_parse_gote_promoted_piece(self):
        """後手の成り駒 '+b' が正しくパースされる"""
        result = parse_sfen("9/9/9/9/4+b4/9/9/9/9 b - 1")
        self.assertEqual(result["errors"], [])
        entry = next((e for e in result["board"] if e["piece"] == "B"), None)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["side"], "gote")
        self.assertTrue(entry["promoted"])

    def test_parse_error_wrong_format(self):
        """スペース区切りが4つでない場合はエラー"""
        result = parse_sfen("9/9/9/9/9/9/9/9/9 b -")
        self.assertTrue(len(result["errors"]) > 0)

    def test_parse_error_invalid_turn(self):
        """不正な手番文字はエラー"""
        result = parse_sfen("9/9/9/9/9/9/9/9/9 x - 1")
        self.assertTrue(any("turn" in e.lower() or "Invalid" in e for e in result["errors"]))


# ==============================================================================
# TestRoundTrip — ラウンドトリップテスト（7件）
# ==============================================================================
class TestRoundTrip(unittest.TestCase):
    """build_sfen → parse_sfen → build_sfen で同一SFEN文字列を生成することを確認"""

    def _round_trip(self, sfen_str):
        """SFENをパースして再生成し、元のSFENと一致するか検証するヘルパー"""
        parsed = parse_sfen(sfen_str)
        self.assertEqual(parsed["errors"], [], f"parse_sfen failed for {sfen_str!r}: {parsed['errors']}")
        rebuilt = build_sfen(
            board=parsed["board"],
            sente_hand=parsed["sente_hand"],
            turn=parsed["turn"],
        )
        self.assertEqual(rebuilt["validation"]["errors"], [],
                         f"build_sfen failed: {rebuilt['validation']['errors']}")
        self.assertEqual(rebuilt["sfen"], sfen_str,
                         f"Round-trip mismatch:\n  Expected: {sfen_str!r}\n  Got:      {rebuilt['sfen']!r}")

    def test_roundtrip_initial(self):
        """初期配置のラウンドトリップ"""
        self._round_trip("lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1")

    def test_roundtrip_empty_board(self):
        """空盤面のラウンドトリップ（38枚すべて後手持ち駒）"""
        self._round_trip("9/9/9/9/9/9/9/9/9 b 2r2b4g4s4n4l18p 1")

    def test_roundtrip_promoted_pieces(self):
        """成り駒を含む完全な局面のラウンドトリップ（+R盤上 + 残り後手持ち駒）"""
        # +R(先手)が盤上 → 飛車1枚残りは後手持ち駒
        self._round_trip("9/9/9/9/4+R4/9/9/9/9 b r2b4g4s4n4l18p 1")

    def test_roundtrip_with_hands(self):
        """先後両方の持ち駒がある完全な局面のラウンドトリップ"""
        # 先後玉のみ盤上、先手持ち R1 G2 P5、残りを後手が保持
        self._round_trip("4k4/9/9/9/9/9/9/9/4K4 b R2G5Pr2b2g4s4n4l13p 1")

    def test_roundtrip_gote_turn(self):
        """後手番のラウンドトリップ"""
        self._round_trip("lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL w - 1")

    def test_roundtrip_gote_promoted(self):
        """後手の成り駒を含む完全な局面のラウンドトリップ"""
        # +b(後手)が盤上 → 角残り1枚が後手持ち駒
        self._round_trip("9/9/9/9/4+b4/9/9/9/9 b 2rb4g4s4n4l18p 1")

    def test_roundtrip_mixed_hand(self):
        """先後両方の持ち駒があるラウンドトリップ"""
        self._round_trip("9/9/9/9/9/9/9/9/9 b 2R2B4G4S4N4L18P 1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
