"""Caching in front of the Monte Carlo equity calculator.

Every :class:`~poker.bot.PokerBot` decision runs a fresh simulation, which is
the single largest cost in the project — a bot decision is milliseconds of
poker logic wrapped around tens of milliseconds of sampling.

Two caches help, for different reasons:

* **Pre-flop** is a closed problem. There are only 169 distinct starting hands
  and nine opponent counts, so 1,521 numbers cover every pre-flop decision that
  can ever be made. They are computed once by ``tools/build_equity_table.py``
  and shipped as JSON.
* **Post-flop** cannot be enumerated (roughly 29 million hole/flop pairings
  before turn and river), so results are memoised for the life of the process
  instead. Tournaments replay similar spots often enough for this to pay.

Both make a bot's equity *deterministic* for a given situation where it
previously jittered between runs. That is usually what you want — results
become reproducible — but it does mean numbers from before and after caching
are not directly comparable.
"""

import json
from typing import Dict, List, Optional

from poker.config import PREFLOP_TABLE_PATH
from poker.equity import WinProbabilityCalculator
from poker.game import Card
from poker.notation import preflop_key

# Keys of the four-number result the calculator returns.
RESULT_FIELDS = ("win_prob", "tie_prob", "lose_prob", "equity")


def load_preflop_table(path=None) -> Optional[Dict[str, Dict[str, List[float]]]]:
    """Load the pre-computed pre-flop table, or None if it has not been built.

    Shape is ``{hand_key: {opponent_count: [win, tie, lose, equity]}}`` with the
    opponent count stringified, because JSON object keys are strings.
    """
    path = path or PREFLOP_TABLE_PATH
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload.get("table")


def save_preflop_table(table, simulations: int, path=None) -> None:
    """Write a table plus the sample size it was built at."""
    path = path or PREFLOP_TABLE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "simulations": simulations,
        "fields": list(RESULT_FIELDS),
        "table": table,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"), sort_keys=True)


class CachedEquityCalculator(WinProbabilityCalculator):
    """A calculator that answers from a table or a memo where it can.

    Drop-in for :class:`WinProbabilityCalculator`: same constructor, same
    ``calculate_win_probability`` contract. Falls back to sampling whenever the
    table is missing or the situation is post-flop and unseen.
    """

    def __init__(self, num_simulations: int = 10000, preflop_table=None,
                 use_preflop_table: bool = True, memoise_postflop: bool = True):
        super().__init__(num_simulations=num_simulations)
        self.preflop_table = (preflop_table if preflop_table is not None
                              else (load_preflop_table() if use_preflop_table else None))
        self.memoise_postflop = memoise_postflop
        self._postflop: Dict[tuple, Dict[str, float]] = {}
        self.hits = 0
        self.misses = 0

    # -- keys ---------------------------------------------------------------

    @staticmethod
    def _board_key(community_cards: List[Card]) -> tuple:
        """Board identity, order-independent: the same cards in any order match."""
        return tuple(sorted(str(card) for card in community_cards))

    # -- lookup -------------------------------------------------------------

    def _from_preflop_table(self, hole_cards, num_opponents):
        if not self.preflop_table:
            return None
        row = self.preflop_table.get(preflop_key(hole_cards))
        if not row:
            return None
        values = row.get(str(num_opponents))
        if not values:
            return None
        return dict(zip(RESULT_FIELDS, values))

    def calculate_win_probability(self, player_hole_cards, community_cards,
                                  num_opponents):
        """Equity for this spot, from cache when possible.

        Validation still runs on every call: a cache must not turn a bad
        request into a plausible-looking answer.
        """
        self._validate(player_hole_cards, community_cards, num_opponents)

        if not community_cards:
            cached = self._from_preflop_table(player_hole_cards, num_opponents)
            if cached is not None:
                self.hits += 1
                return dict(cached)

        key = None
        if self.memoise_postflop:
            key = (preflop_key(player_hole_cards),
                   self._board_key(community_cards),
                   num_opponents)
            if key in self._postflop:
                self.hits += 1
                return dict(self._postflop[key])

        self.misses += 1
        result = super().calculate_win_probability(
            player_hole_cards, community_cards, num_opponents
        )
        if key is not None:
            self._postflop[key] = result
        return dict(result)

    # -- introspection ------------------------------------------------------

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def stats(self) -> Dict[str, float]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
            "preflop_entries": len(self.preflop_table or {}),
            "postflop_entries": len(self._postflop),
        }
