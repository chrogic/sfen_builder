# sfen_builder

将棋盤面の構造化データを受け取り、SFEN文字列を生成するPythonモジュール。  
LLMエージェントが将棋局面を扱うことを想定して設計されています。

## Features

- 駒名の多形式対応（英語 / 日本語 / ローマ字）
- 座標の多形式対応（`"5a"` / `"５一"` / `(5, 1)`）
- 後手持ち駒の自動計算
- 王手・二歩・行き所なし等のバリデーション
- SFEN → 構造化データへの逆変換（`parse_sfen`）

## Requirements

- Python 3.9+
- python-shogi（王手チェック機能に使用、任意）

## Installation

```bash
pip install -r requirements.txt
```

python-shogi なしでも基本機能は動作します（王手チェックのみスキップ）。

## Usage

```python
from sfen_builder import build_sfen, parse_sfen

# 詰将棋局面の生成（デフォルト tsume=True）
result = build_sfen(
    board=[
        {"piece": "玉", "pos": "５一", "side": "gote",  "promoted": False},
        {"piece": "歩", "pos": "５三", "side": "sente", "promoted": False},
    ],
    sente_hand={"金": 1},
    turn="sente"
)
print(result["sfen"])
# → 4k4/9/4P4/9/9/9/9/9/9 b G2r2b3g4s4n4l17p 1

# 初期配置
build_sfen(board="initial")["sfen"]
# → lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1

# SFENを解析
parse_sfen("4k4/9/4P4/9/9/9/9/9/9 b G2r2b3g4s4n4l17p 1")
```

詳細は [`sfen_builder/GUIDE.md`](sfen_builder/GUIDE.md) を参照してください。

## Running Tests

```bash
python -m unittest sfen_builder.test.test_sfen_builder -v
```

## Project Structure

```
sfen_builder/
├── sfen_builder/
│   ├── __init__.py        # パッケージ入口
│   ├── sfen_builder.py    # 後方互換 facade
│   ├── constants.py       # 定数・エイリアステーブル
│   ├── normalizers.py     # 駒名・座標・手番の正規化
│   ├── initial_board.py   # 初期配置データ
│   ├── validators.py      # バリデーション・王手検出
│   ├── builders.py        # SFENブロック生成
│   ├── core.py            # build_sfen / parse_sfen 本体
│   ├── GUIDE.md           # LLMエージェント向け使用ガイド
│   └── test/
│       └── test_sfen_builder.py
├── requirements.txt
└── README.md
```
