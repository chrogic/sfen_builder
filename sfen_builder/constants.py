"""
constants.py — 将棋の定数・エイリアステーブル
"""

# 各駒種の全40枚における最大枚数（先後合計）
MAX_COUNT = {"K": 2, "R": 2, "B": 2, "G": 4, "S": 4, "N": 4, "L": 4, "P": 18}

# 持ち駒ブロックのSFEN標準順序
HAND_ORDER = ["R", "B", "G", "S", "N", "L", "P"]

# 成り可能な駒種（K=玉、G=金 は成り不可）
PROMOTABLE = {"R", "B", "S", "N", "L", "P"}

# 駒名エイリアス → 正規化された大文字1文字
PIECE_ALIASES: dict = {
    "k": "K", "king": "K", "gyoku": "K", "ou": "K", "gyou": "K",
    "玉": "K", "王": "K", "玉将": "K", "王将": "K",
    "r": "R", "rook": "R", "hisha": "R",
    "飛": "R", "飛車": "R",
    "b": "B", "bishop": "B", "kaku": "B",
    "角": "B", "角行": "B",
    "g": "G", "gold": "G", "kin": "G",
    "金": "G", "金将": "G",
    "s": "S", "silver": "S", "gin": "S",
    "銀": "S", "銀将": "S",
    "n": "N", "knight": "N", "kei": "N", "keima": "N",
    "桂": "N", "桂馬": "N",
    "l": "L", "lance": "L", "kyou": "L", "kyo": "L",
    "香": "L", "香車": "L",
    "p": "P", "pawn": "P", "fu": "P",
    "歩": "P", "歩兵": "P",
}

# 駒名の表記（エラーメッセージ用）
PIECE_FULL_NAME = {
    "K": "king/玉", "R": "rook/飛", "B": "bishop/角",
    "G": "gold/金", "S": "silver/銀", "N": "knight/桂",
    "L": "lance/香", "P": "pawn/歩",
}

# 手番エイリアス
TURN_SENTE = {"sente", "b", "先手", "black", "先"}
TURN_GOTE  = {"gote",  "w", "後手", "white", "後"}

# 手番 → SFENの1文字
TURN_TO_SFEN = {"sente": "b", "gote": "w"}

# ランク文字 → 数値（"5a" 形式: a→1 … i→9）
RANK_LETTER_TO_INT = {chr(ord("a") + i): i + 1 for i in range(9)}

# 漢数字 → 数値（"５一" 形式のランク部分）
RANK_KANJI_TO_INT = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9,
}

# 全角数字 → 数値（"５一" 形式のファイル部分）
FULLWIDTH_TO_INT = {
    "１": 1, "２": 2, "３": 3, "４": 4, "５": 5,
    "６": 6, "７": 7, "８": 8, "９": 9,
}
