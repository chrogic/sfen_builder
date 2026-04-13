"""
initial_board.py — 将棋の初期配置データ

parse_sfen との循環参照を避けるためリストリテラルで定義する。
期待SFEN: lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1

SFEN走査順: rank1(後手側)が先頭、各rank内はfile9→1の順。
"""

INITIAL_BOARD = [
    # 後手 rank1: 香桂銀金玉金銀桂香
    {"piece": "L", "pos": (9, 1), "side": "gote",  "promoted": False},
    {"piece": "N", "pos": (8, 1), "side": "gote",  "promoted": False},
    {"piece": "S", "pos": (7, 1), "side": "gote",  "promoted": False},
    {"piece": "G", "pos": (6, 1), "side": "gote",  "promoted": False},
    {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
    {"piece": "G", "pos": (4, 1), "side": "gote",  "promoted": False},
    {"piece": "S", "pos": (3, 1), "side": "gote",  "promoted": False},
    {"piece": "N", "pos": (2, 1), "side": "gote",  "promoted": False},
    {"piece": "L", "pos": (1, 1), "side": "gote",  "promoted": False},
    # 後手 rank2: 飛(file8) 角(file2)
    {"piece": "R", "pos": (8, 2), "side": "gote",  "promoted": False},
    {"piece": "B", "pos": (2, 2), "side": "gote",  "promoted": False},
    # 後手 rank3: 歩×9
    *[{"piece": "P", "pos": (f, 3), "side": "gote",  "promoted": False} for f in range(9, 0, -1)],
    # 先手 rank7: 歩×9
    *[{"piece": "P", "pos": (f, 7), "side": "sente", "promoted": False} for f in range(9, 0, -1)],
    # 先手 rank8: 角(file8) 飛(file2)
    {"piece": "B", "pos": (8, 8), "side": "sente", "promoted": False},
    {"piece": "R", "pos": (2, 8), "side": "sente", "promoted": False},
    # 先手 rank9: 香桂銀金玉金銀桂香
    {"piece": "L", "pos": (9, 9), "side": "sente", "promoted": False},
    {"piece": "N", "pos": (8, 9), "side": "sente", "promoted": False},
    {"piece": "S", "pos": (7, 9), "side": "sente", "promoted": False},
    {"piece": "G", "pos": (6, 9), "side": "sente", "promoted": False},
    {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
    {"piece": "G", "pos": (4, 9), "side": "sente", "promoted": False},
    {"piece": "S", "pos": (3, 9), "side": "sente", "promoted": False},
    {"piece": "N", "pos": (2, 9), "side": "sente", "promoted": False},
    {"piece": "L", "pos": (1, 9), "side": "sente", "promoted": False},
]
