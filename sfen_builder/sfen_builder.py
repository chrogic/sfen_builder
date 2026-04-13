"""
sfen_builder.py — 後方互換性のための facade

既存の import 文が引き続き動作するよう公開 API を再エクスポートする。
  from sfen_builder.sfen_builder import build_sfen, parse_sfen
"""

from .core import build_sfen, parse_sfen  # noqa: F401

__all__ = ["build_sfen", "parse_sfen"]
