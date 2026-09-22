"""Opponent modelling: watch how people play, and adjust to it.

A bot that only reads its own cards plays the same way against a rock and a
calling station, which are the two situations that call for the most different
play. This module keeps a running profile of every seat and hands the bots a
read they can act on.

The three numbers are the ones a poker tracker shows, because they are the ones
that change decisions:

* **VPIP** - how often a player voluntarily puts money in pre-flop. High means a
  wide, weak range; low means they only play strong hands.
* **Aggression** - of the actions that are not folds, how many are bets or
  raises rather than calls. Separates a passive caller from someone who applies
  pressure.
* **Fold to a bet** - how often they give up when facing one. This is the number
  that decides whether bluffing and stealing are profitable at all.

:class:`OpponentModel` is a :class:`~poker.game.GameObserver`, so it learns by
watching an ordinary game - the engine does not know it exists, and neither do
the bots that ignore it.

Nothing is inferred from a handful of hands: until a profile reaches
``MIN_HANDS``, the read comes back neutral and bots play their base strategy.
"""

from typing import Dict, Iterable, List, Optional

from poker.game import GameObserver

# Neutral values, used until there is enough evidence to say otherwise.
NEUTRAL_VPIP = 0.30
NEUTRAL_AGGRESSION = 0.50
NEUTRAL_FOLD_TO_BET = 0.50

# Hands a seat must be watched for before its profile is trusted.
MIN_HANDS = 12


class OpponentProfile:
    """Running counts for one seat, and the rates derived from them."""

    def __init__(self, player_id: int):
        self.player_id = player_id
        self.hands_seen = 0
        self.hands_voluntarily_played = 0   # called or raised pre-flop
        self.hands_raised_preflop = 0
        self.bets_and_raises = 0
        self.calls = 0
        self.folds = 0
        self.times_facing_a_bet = 0
        self.folds_facing_a_bet = 0

    # -- derived rates ------------------------------------------------------

    @property
    def vpip(self) -> float:
        """Share of hands entered by choice; blinds do not count."""
        if not self.hands_seen:
            return NEUTRAL_VPIP
        return self.hands_voluntarily_played / self.hands_seen

    @property
    def preflop_raise(self) -> float:
        if not self.hands_seen:
            return 0.0
        return self.hands_raised_preflop / self.hands_seen

    @property
    def aggression(self) -> float:
        """Bets and raises as a share of non-folding actions."""
        acted = self.bets_and_raises + self.calls
        if not acted:
            return NEUTRAL_AGGRESSION
        return self.bets_and_raises / acted

    @property
    def fold_to_bet(self) -> float:
        """How often this seat gives up when it is facing a bet."""
        if not self.times_facing_a_bet:
            return NEUTRAL_FOLD_TO_BET
        return self.folds_facing_a_bet / self.times_facing_a_bet

    @property
    def is_reliable(self) -> bool:
        return self.hands_seen >= MIN_HANDS

    @property
    def style(self) -> str:
        """The usual two-axis label, or "unknown" on a thin sample."""
        if not self.is_reliable:
            return "unknown"
        tight = self.vpip < 0.28
        passive = self.aggression < 0.45
        if tight:
            return "tight-passive" if passive else "tight-aggressive"
        return "loose-passive" if passive else "loose-aggressive"

    def __repr__(self) -> str:
        return (f"<OpponentProfile seat={self.player_id} hands={self.hands_seen} "
                f"vpip={self.vpip:.0%} aggr={self.aggression:.0%} "
                f"fold={self.fold_to_bet:.0%} {self.style}>")


class TableRead:
    """What the live opponents look like, taken together."""

    def __init__(self, sample: int, vpip: float, aggression: float,
                 fold_to_bet: float, reliable: bool):
        self.sample = sample
        self.vpip = vpip
        self.aggression = aggression
        self.fold_to_bet = fold_to_bet
        self.reliable = reliable

    @property
    def is_neutral(self) -> bool:
        return not self.reliable

    def __repr__(self) -> str:
        return (f"<TableRead sample={self.sample} vpip={self.vpip:.0%} "
                f"aggr={self.aggression:.0%} fold={self.fold_to_bet:.0%} "
                f"reliable={self.reliable}>")


NEUTRAL_READ = TableRead(0, NEUTRAL_VPIP, NEUTRAL_AGGRESSION,
                         NEUTRAL_FOLD_TO_BET, False)


class OpponentModel(GameObserver):
    """Builds a profile per seat by watching hands go by.

    Attach it as the game's observer, or alongside a front-end with
    :class:`~poker.game.FanOutObserver`::

        model = OpponentModel()
        game = PokerGame(num_players=6, observer=model)

    A :class:`~poker.game.PokerGame` already makes one of these and links it to
    the bots it drives, so most callers never construct it directly.
    """

    def __init__(self):
        self.profiles: Dict[int, OpponentProfile] = {}
        self.hands_observed = 0
        # Per-street bookkeeping, so "was this player facing a bet?" is exact
        # rather than guessed from the action name.
        self._committed: Dict[int, int] = {}
        self._bet_level = 0
        self._stage = "Pre-Flop"
        self._entered_pot: set = set()
        self._raised_preflop: set = set()

    # -- access -------------------------------------------------------------

    def profile(self, player_id: int) -> OpponentProfile:
        if player_id not in self.profiles:
            self.profiles[player_id] = OpponentProfile(player_id)
        return self.profiles[player_id]

    def table_read(self, exclude: Optional[int] = None,
                   seats: Optional[Iterable[int]] = None) -> TableRead:
        """Aggregate read on the opponents, ignoring seats without a sample.

        Averaging across opponents rather than reporting one of them keeps the
        bot contract unchanged: a bot is told how many opponents it faces, not
        which seats they are.
        """
        candidates: List[OpponentProfile] = [
            p for seat, p in self.profiles.items()
            if seat != exclude and (seats is None or seat in seats) and p.is_reliable
        ]
        if not candidates:
            return NEUTRAL_READ

        count = len(candidates)
        return TableRead(
            sample=min(p.hands_seen for p in candidates),
            vpip=sum(p.vpip for p in candidates) / count,
            aggression=sum(p.aggression for p in candidates) / count,
            fold_to_bet=sum(p.fold_to_bet for p in candidates) / count,
            reliable=True,
        )

    def summary(self) -> List[OpponentProfile]:
        """Profiles ordered by seat, for reporting."""
        return [self.profiles[seat] for seat in sorted(self.profiles)]

    def reset(self) -> None:
        self.profiles.clear()
        self.hands_observed = 0

    # -- observer hooks -----------------------------------------------------

    def on_hand_start(self, game):
        self.hands_observed += 1
        self._entered_pot = set()
        self._raised_preflop = set()
        for player in game.players:
            self.profile(player.player_id).hands_seen += 1

    def on_stage(self, game, stage):
        # Seed from what is already in front of each player, so the blinds count
        # towards the bet level without counting as voluntary money.
        self._stage = stage
        self._committed = {p.player_id: p.total_bet_this_round for p in game.players}
        self._bet_level = max(self._committed.values()) if self._committed else 0

    def on_action(self, game, player, action, amount, stage):
        seat = player.player_id
        profile = self.profile(seat)
        already_in = self._committed.get(seat, 0)
        facing_a_bet = self._bet_level > already_in

        if facing_a_bet:
            profile.times_facing_a_bet += 1

        if action == "fold":
            profile.folds += 1
            if facing_a_bet:
                profile.folds_facing_a_bet += 1
        elif action == "call":
            profile.calls += 1
            self._note_entry(profile, seat, stage)
        elif action == "raise":
            profile.bets_and_raises += 1
            self._note_entry(profile, seat, stage, raised=True)

        # Keep the street's picture current for whoever acts next.
        self._committed[seat] = already_in + amount
        self._bet_level = max(self._bet_level, self._committed[seat])

    def _note_entry(self, profile, seat, stage, raised=False):
        """Count a seat as entering the pot by choice - once per hand, each way.

        VPIP and pre-flop-raise are per-hand rates, so a player who raises and
        then re-raises the same hand counts once for each, not twice.
        """
        if stage != "Pre-Flop":
            return
        if seat not in self._entered_pot:
            self._entered_pot.add(seat)
            profile.hands_voluntarily_played += 1
        if raised and seat not in self._raised_preflop:
            self._raised_preflop.add(seat)
            profile.hands_raised_preflop += 1
