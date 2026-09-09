"""Helpers shared by the tests: card parsing, scripted games, fake front-ends."""

from typing import Dict, List, Optional

from poker.game import Card, GameAborted, GameObserver, PokerGame

SUITS = {"S": "Spades", "H": "Hearts", "D": "Diamonds", "C": "Clubs"}


def card(text: str) -> Card:
    """Build a card from shorthand: ``"AS"``, ``"10D"``, ``"TD"``, ``"7h"``."""
    text = text.strip()
    suit = SUITS[text[-1].upper()]
    rank = text[:-1].upper()
    if rank == "T":
        rank = "10"
    return Card(suit, rank)


def hand(text: str) -> List[Card]:
    """Build a list of cards: ``hand("AS KS")``."""
    return [card(token) for token in text.split()]


def silent_game(**kwargs) -> PokerGame:
    """A game whose observer does nothing, so tests never block on input()."""
    kwargs.setdefault("observer", GameObserver())
    return PokerGame(**kwargs)


class ScriptedObserver(GameObserver):
    """A front-end stand-in.

    Supplies human actions from a list and records the hooks the engine calls,
    so the path the Tk UI uses can be exercised without a display.
    """

    def __init__(self, actions=(), defer_bots: int = 0):
        self.actions = list(actions)
        self.events: List[str] = []
        self.defer_bots = defer_bots
        self.deferred = 0

    def on_hand_start(self, game):
        self.events.append("hand_start")

    def on_blinds(self, game, small_blind_player, big_blind_player):
        self.events.append(f"blinds:{small_blind_player}:{big_blind_player}")

    def on_stage(self, game, stage):
        self.events.append(f"stage:{stage}")

    def on_action(self, game, player, action, amount, stage):
        self.events.append(f"action:{player.player_id}:{action}:{amount}")

    def on_turn_advanced(self, game, stage):
        self.events.append("advanced")

    def on_showdown(self, game):
        self.events.append("showdown")

    def on_hand_end(self, game, winner_info):
        self.events.append("hand_end")

    def before_ai_action(self, game, player, to_call, stage):
        if self.deferred < self.defer_bots:
            self.deferred += 1
            return False
        return True

    def get_human_action(self, game, player, to_call, stage):
        if not self.actions:
            raise GameAborted()
        return self.actions.pop(0)

    def actions_of(self, player_id: int) -> List[str]:
        prefix = f"action:{player_id}:"
        return [e.split(":")[2] for e in self.events if e.startswith(prefix)]


class FixedBot:
    """A bot that always returns the action it was constructed with."""

    def __init__(self, player_id: int, action: str = "check", amount=None):
        self.player_id = player_id
        self.name = f"Fixed-{action}"
        self._action = action
        self._amount = amount
        self.calls = 0

    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        self.calls += 1
        return (self._action, self._amount)


class GameScript:
    """Pin the cards a game deals, so a hand plays out deterministically."""

    def __init__(self, num_players: int = 2, starting_stack: int = 1000):
        self.num_players = num_players
        self.starting_stack = starting_stack
        self.hole_cards: Dict[int, List[Card]] = {}
        self.community_cards: List[Card] = []

    def set_hole_cards(self, player_id: int, cards: List[Card]) -> "GameScript":
        self.hole_cards[player_id] = cards
        return self

    def set_community_cards(self, cards: List[Card]) -> "GameScript":
        self.community_cards = cards
        return self


class ScriptedGame(PokerGame):
    """A PokerGame that deals the cards a :class:`GameScript` specifies."""

    def __init__(self, script: GameScript, observer: Optional[GameObserver] = None,
                 **kwargs):
        kwargs.setdefault("small_blind", 5)
        kwargs.setdefault("big_blind", 10)
        super().__init__(
            num_players=script.num_players,
            starting_stack=script.starting_stack,
            observer=observer or GameObserver(),
            **kwargs,
        )
        self.script = script

    def deal_hole_cards(self):
        if not self.script.hole_cards:
            return super().deal_hole_cards()
        for player_id, cards in self.script.hole_cards.items():
            self.players[player_id].receive_cards(cards)
        # Keep the deck consistent with what was dealt.
        dealt = {str(c) for cards in self.script.hole_cards.values() for c in cards}
        deck = self._assert_deck()
        deck.cards = [c for c in deck.cards if str(c) not in dealt]

    def betting_round(self, stage):
        if self.script.community_cards:
            sizes = {"Flop": 3, "Turn": 4, "River": 5}
            if stage in sizes and len(self.script.community_cards) >= sizes[stage]:
                self.community_cards = self.script.community_cards[:sizes[stage]]
        return super().betting_round(stage)
