"""Canonical starting-hand notation.

`Card.RANKS` spells ten as ``"10"``, but poker notation writes hands with a
single character per rank — ``"AA"``, ``"AKs"``, ``"T9o"``. Everything that
needs to name a starting hand goes through here so the two spellings cannot
drift apart again.

This module deliberately depends on nothing but :mod:`poker.game`, so both
:mod:`poker.bot` and :mod:`poker.equity_cache` can use it without an import
cycle.
"""

from typing import List

from poker.game import Card

# Accepts both spellings of ten so callers never have to care which they hold.
RANK_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
               '10': 10, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

# Card.RANKS spelling -> notation spelling, and back.
HAND_KEY_RANKS = {'10': 'T'}
CARD_RANKS = {'T': '10'}

# High to low, in notation spelling.
NOTATION_RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']


def hand_key(hole_cards, include_suitedness: bool = False) -> str:
    """Canonical starting-hand notation, high card first.

    ``hand_key([As, Kh])`` is ``"AK"``, or ``"AKo"`` with ``include_suitedness``.
    Pairs never carry a suitedness suffix.
    """
    r1, r2 = hole_cards[0].rank, hole_cards[1].rank
    v1, v2 = RANK_VALUES[r1], RANK_VALUES[r2]
    k1, k2 = HAND_KEY_RANKS.get(r1, r1), HAND_KEY_RANKS.get(r2, r2)

    if v1 == v2:
        return f"{k1}{k2}"

    high, low = (k1, k2) if v1 > v2 else (k2, k1)
    if include_suitedness:
        suited = "s" if hole_cards[0].suit == hole_cards[1].suit else "o"
        return f"{high}{low}{suited}"
    return f"{high}{low}"


def preflop_key(hole_cards) -> str:
    """The 169-bucket key for a starting hand: ``"AA"``, ``"AKs"``, ``"AKo"``."""
    return hand_key(hole_cards, include_suitedness=True)


def all_preflop_keys() -> List[str]:
    """Every distinct starting hand: 13 pairs + 78 suited + 78 offsuit = 169."""
    keys = []
    for i, high in enumerate(NOTATION_RANKS):
        for j, low in enumerate(NOTATION_RANKS):
            if i == j:
                keys.append(f"{high}{low}")
            elif i < j:
                keys.append(f"{high}{low}s")
                keys.append(f"{high}{low}o")
    return keys


def cards_for_key(key: str) -> List[Card]:
    """A representative pair of cards for a 169-bucket key.

    Every hand in a bucket has identical equity against random opponents, so
    any representative will do.
    """
    if key[-1] in "so":
        ranks, suited = key[:-1], key[-1] == "s"
    else:
        ranks, suited = key, False

    r1 = CARD_RANKS.get(ranks[0], ranks[0])
    r2 = CARD_RANKS.get(ranks[1], ranks[1])
    second_suit = "Spades" if suited else "Hearts"
    return [Card("Spades", r1), Card(second_suit, r2)]
