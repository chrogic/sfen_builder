# sfen_builder — Agent Usage Guide

Converts structured shogi board descriptions into canonical SFEN strings. Designed for LLM agents: structured JSON output, actionable error messages, no interactive prompts.

```python
from sfen_builder import build_sfen, parse_sfen          # recommended
from sfen_builder.sfen_builder import build_sfen, parse_sfen  # also works
```

---

## `build_sfen(board, sente_hand, turn, tsume) -> dict`

**You only specify board pieces and sente's hand. gote_hand is always auto-calculated.**

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `board` | `list[dict]` or `"initial"` | required | Pieces on the board, or `"initial"` for standard starting position |
| `sente_hand` | `dict` | `{}` | Pieces in sente's hand. e.g. `{"G": 1, "P": 3}` |
| `turn` | `str` | `"sente"` | Who moves next |
| `tsume` | `bool` | `True` | `True` = tsume-shogi mode (no warning if sente king is absent). `False` = dual-king mode (warns if either king is missing) |
| `debug` | `bool` | `False` | `True` = print processing logs to stderr. Silent by default. |

### board entry keys

| Key | Type | Required | Notes |
|---|---|---|---|
| `"piece"` | `str` | Yes | Piece name — see table below |
| `"pos"` | `str` or `tuple` | Yes | Coordinate — see formats below |
| `"side"` | `str` | Yes | `"sente"` or `"gote"` |
| `"promoted"` | `bool` | No (default `False`) | Only R, B, S, N, L, P can be promoted. K and G cannot. |

### Return value

```python
{
    "sfen": str,               # SFEN string. Empty string "" if errors occurred.
    "gote_hand": dict,         # Auto-calculated gote hand
    "sente_hand_used": dict,   # Normalized sente hand (echo for verification)
    "validation": {
        "ok": bool,
        "errors": list[str],   # Fatal — sfen is "" when errors exist
        "warnings": list[str]  # Non-fatal — sfen is still generated
    }
}
```

**Always check `validation.ok` before using `sfen`.**

---

## `parse_sfen(sfen_str, debug=False) -> dict`

```python
{
    "board": list[dict],  # Same format as build_sfen board input
    "sente_hand": dict, "gote_hand": dict,
    "turn": str,          # "sente" or "gote"
    "errors": list[str]
}
```

---

## Piece Names (case-insensitive)

| Piece | Accepted names |
|---|---|
| King | `K`, `king`, `玉`, `王`, `玉将`, `王将`, `gyoku`, `ou` |
| Rook | `R`, `rook`, `飛`, `飛車`, `hisha` |
| Bishop | `B`, `bishop`, `角`, `角行`, `kaku` |
| Gold | `G`, `gold`, `金`, `金将`, `kin` |
| Silver | `S`, `silver`, `銀`, `銀将`, `gin` |
| Knight | `N`, `knight`, `桂`, `桂馬`, `kei` |
| Lance | `L`, `lance`, `香`, `香車`, `kyou` |
| Pawn | `P`, `pawn`, `歩`, `歩兵`, `fu` |

---

## Coordinate Formats (all equivalent)

| Format | Example | Notes |
|---|---|---|
| Letter | `"5a"` | file 1–9, rank a–i (a=1, i=9) |
| Kanji | `"５一"` | fullwidth digit + kanji numeral |
| Tuple | `(5, 1)` | (file, rank), both 1–9 |

file: 1=right, 9=left (from sente's perspective). rank: 1=gote's back rank, 9=sente's back rank.

---

## Piece Count Limits (board + both hands combined)

K=2, R=2, B=2, G=4, S=4, N=4, L=4, P=18. Promoted pieces count as their original type.

---

## Errors vs Warnings

**Errors** (`ok=False`, `sfen=""`): duplicate position, piece count exceeded, illegal promotion (K/G), unknown piece name, invalid coordinate, promoted piece in hand, king in check at start (tsume=True, requires python-shogi).

**Warnings** (`ok=True`, sfen generated): double pawn (二歩), dead piece (行き所なし), missing king.

Error messages echo the bad input value and state the valid range — read them to self-correct and retry.

---

## Examples

### Standard starting position
```python
build_sfen(board="initial")["sfen"]
# → "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
```

### Tsume-shogi (default tsume=True, sente king absent)
```python
result = build_sfen(
    board=[
        {"piece": "玉", "pos": "５一", "side": "gote",  "promoted": False},
        {"piece": "歩", "pos": "５三", "side": "sente", "promoted": False},
    ],
    sente_hand={"金": 1},
    turn="sente"
)
# result["sfen"] → "4k4/9/4P4/9/9/9/9/9/9 b G2r2b3g4s4n4l17p 1"
```

### Dual-king position (tsume=False)
```python
result = build_sfen(
    board=[
        {"piece": "K", "pos": (5, 9), "side": "sente", "promoted": False},
        {"piece": "K", "pos": (5, 1), "side": "gote",  "promoted": False},
    ],
    tsume=False  # warns if either king is missing
)
```

### Promoted piece
```python
# Two equivalent ways to specify a promoted piece:
{"piece": "R",  "pos": (5, 5), "side": "sente", "promoted": True}
{"piece": "+R", "pos": (5, 5), "side": "sente"}   # promoted flag inferred from piece name
# → both appear as "+R" in the SFEN board block
```

### Parse → edit → rebuild
```python
parsed = parse_sfen("lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1")
# modify parsed["board"] here
result = build_sfen(board=parsed["board"], sente_hand=parsed["sente_hand"], turn=parsed["turn"])
```

### Error handling
```python
result = build_sfen(board=[], sente_hand={"P": 19})
if not result["validation"]["ok"]:
    print(result["validation"]["errors"])
# → ["Piece count exceeds maximum: P (pawn/歩) has 19 (max 18). Board: 0, sente_hand: 19."]
```

---

## Notes

- **Check detection** requires `python-shogi` (`pip install python-shogi`). If not installed, a warning is added and the check is skipped.
- Never specify `gote_hand` — it is always auto-calculated from the remaining pieces.
- Pieces in hand are never promoted. `"+R"` in `sente_hand` is an error; use `"R"`.
- `"initial"` is the only accepted string value for `board`. Everything else must be a list.
- `tsume=True` is the default. Use `tsume=False` only when both kings must be present on the board.
