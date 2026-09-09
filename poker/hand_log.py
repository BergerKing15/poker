"""Per-hand history in SQLite, for analysis and as ML training data.

The tournament runner used to keep only aggregates — win rate, total gain,
final stacks — written to a JSON file that was overwritten on every run. That
throws away everything interesting: which hand was held, from what position,
what the board was, what the bot did and what it cost.

This records one row per player per hand, plus the action sequence, so runs
accumulate instead of replacing each other. ``sqlite3`` is in the standard
library, so this adds no dependency.

It is a :class:`~poker.game.GameObserver`, so it attaches to any game — the
GUI included — without the engine knowing it exists::

    with HandLog("hands.db") as log:
        game = PokerGame(num_players=3, observer=log)
        game.play_hand()

Queries are then ordinary SQL::

    SELECT bot_type, COUNT(*), AVG(net) FROM hand_players GROUP BY bot_type;
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from poker.game import GameObserver

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    label       TEXT,
    metadata    TEXT
);

CREATE TABLE IF NOT EXISTS hands (
    hand_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL REFERENCES runs(run_id),
    hand_number INTEGER NOT NULL,
    num_players INTEGER NOT NULL,
    button      INTEGER NOT NULL,
    small_blind INTEGER NOT NULL,
    big_blind   INTEGER NOT NULL,
    board       TEXT NOT NULL,
    pot         INTEGER NOT NULL,
    winners     TEXT NOT NULL,
    hand_type   TEXT
);

CREATE TABLE IF NOT EXISTS hand_players (
    hand_id     INTEGER NOT NULL REFERENCES hands(hand_id),
    player_id   INTEGER NOT NULL,
    bot_type    TEXT,
    position    TEXT,
    hole_cards  TEXT NOT NULL,
    starting_stack INTEGER NOT NULL,
    final_stack INTEGER NOT NULL,
    net         INTEGER NOT NULL,
    folded      INTEGER NOT NULL,
    all_in      INTEGER NOT NULL,
    won         INTEGER NOT NULL,
    PRIMARY KEY (hand_id, player_id)
);

CREATE TABLE IF NOT EXISTS actions (
    hand_id     INTEGER NOT NULL REFERENCES hands(hand_id),
    seq         INTEGER NOT NULL,
    stage       TEXT NOT NULL,
    player_id   INTEGER NOT NULL,
    action      TEXT NOT NULL,
    amount      INTEGER NOT NULL,
    pot_after   INTEGER NOT NULL,
    PRIMARY KEY (hand_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_hand_players_bot ON hand_players(bot_type);
CREATE INDEX IF NOT EXISTS idx_hands_run ON hands(run_id);
CREATE INDEX IF NOT EXISTS idx_actions_hand ON actions(hand_id);
"""


class HandLog(GameObserver):
    """Records every hand played by a game into SQLite.

    Attach as the game's observer. Safe to use alongside no other observer;
    to log a GUI game as well, see :class:`FanOutObserver`.
    """

    def __init__(self, path="hands.db", label: Optional[str] = None,
                 metadata: Optional[dict] = None, bot_types: Optional[Dict[int, str]] = None):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.executescript(SCHEMA)

        cursor = self.connection.execute(
            "INSERT INTO runs (started_at, label, metadata) VALUES (?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), label,
             json.dumps(metadata or {})),
        )
        self.run_id = cursor.lastrowid
        self.connection.commit()

        # player_id -> bot type name, for grouping in queries.
        self.bot_types = dict(bot_types or {})
        self._starting_stacks: Dict[int, int] = {}
        self._actions: List[tuple] = []
        self._stage = "Pre-Flop"
        self.hands_recorded = 0

    # -- context manager ----------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()
        return False

    def close(self):
        self.connection.commit()
        self.connection.close()

    # -- naming -------------------------------------------------------------

    def describe_bots(self, game) -> None:
        """Label each seat with the bot driving it, for later grouping."""
        for player_id, bot in getattr(game, "bots", {}).items():
            name = getattr(bot, "name", None)
            if name is None:
                bot_type = getattr(bot, "type", None)
                name = getattr(bot_type, "name", type(bot).__name__)
            self.bot_types[player_id] = name

    # -- observer hooks -----------------------------------------------------

    def on_hand_start(self, game):
        if not self.bot_types:
            self.describe_bots(game)
        self._starting_stacks = {p.player_id: p.stack for p in game.players}
        self._actions = []
        self._stage = "Pre-Flop"

    def on_stage(self, game, stage):
        self._stage = stage

    def on_action(self, game, player, action, amount, stage):
        self._actions.append(
            (len(self._actions), stage, player.player_id, action, amount, game.pot)
        )

    def on_hand_end(self, game, winner_info):
        winner_info = winner_info or {}
        winners = [p.player_id for p in winner_info.get("winners", [])]
        pot = winner_info.get("pot", 0)

        cursor = self.connection.execute(
            """INSERT INTO hands (run_id, hand_number, num_players, button,
                                  small_blind, big_blind, board, pot, winners, hand_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (self.run_id, game.hand_number, len(game.players), game.button,
             game.small_blind, game.big_blind,
             " ".join(str(c) for c in game.community_cards),
             pot, json.dumps(winners), winner_info.get("hand_type")),
        )
        hand_id = cursor.lastrowid

        rows = []
        for player in game.players:
            started = self._starting_stacks.get(player.player_id, player.stack)
            rows.append((
                hand_id, player.player_id,
                self.bot_types.get(player.player_id),
                self._position(game, player.player_id),
                " ".join(str(c) for c in player.hole_cards),
                started, player.stack, player.stack - started,
                int(player.is_folded), int(player.is_all_in),
                int(player.player_id in winners),
            ))
        self.connection.executemany(
            """INSERT OR REPLACE INTO hand_players
               (hand_id, player_id, bot_type, position, hole_cards,
                starting_stack, final_stack, net, folded, all_in, won)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )

        self.connection.executemany(
            """INSERT OR REPLACE INTO actions
               (hand_id, seq, stage, player_id, action, amount, pot_after)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [(hand_id,) + row for row in self._actions],
        )

        self.connection.commit()
        self.hands_recorded += 1

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _position(game, player_id) -> Optional[str]:
        calculate = getattr(game, "_calculate_position", None)
        if calculate is None:
            return None
        active = len([p for p in game.players if not p.is_folded])
        return calculate(player_id, max(active, 2))

    # -- reading back -------------------------------------------------------

    def summary_by_bot(self) -> List[dict]:
        """Hands, win rate and average net result per bot type."""
        cursor = self.connection.execute(
            """SELECT bot_type,
                      COUNT(*)              AS hands,
                      SUM(won)              AS wins,
                      ROUND(AVG(net), 2)    AS avg_net,
                      SUM(net)              AS total_net
               FROM hand_players
               GROUP BY bot_type
               ORDER BY total_net DESC"""
        )
        columns = [c[0] for c in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def action_counts(self) -> List[dict]:
        """How often each bot type takes each action."""
        cursor = self.connection.execute(
            """SELECT hp.bot_type, a.action, COUNT(*) AS n
               FROM actions a
               JOIN hand_players hp
                 ON hp.hand_id = a.hand_id AND hp.player_id = a.player_id
               GROUP BY hp.bot_type, a.action
               ORDER BY hp.bot_type, n DESC"""
        )
        columns = [c[0] for c in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


class FanOutObserver(GameObserver):
    """Sends every hook to several observers in turn.

    Lets a front-end and a :class:`HandLog` watch the same game::

        game = PokerGame(observer=FanOutObserver(ui, hand_log))

    Hooks are written out explicitly rather than generated through
    ``__getattr__``: GameObserver already defines every hook name, so attribute
    lookup would find the inherited no-op and the dynamic version would never
    run.
    """

    def __init__(self, *observers):
        self.observers = [o for o in observers if o is not None]

    def on_hand_start(self, game):
        for o in self.observers:
            o.on_hand_start(game)

    def on_blinds(self, game, small_blind_player, big_blind_player):
        for o in self.observers:
            o.on_blinds(game, small_blind_player, big_blind_player)

    def on_stage(self, game, stage):
        for o in self.observers:
            o.on_stage(game, stage)

    def on_action(self, game, player, action, amount, stage):
        for o in self.observers:
            o.on_action(game, player, action, amount, stage)

    def on_turn_advanced(self, game, stage):
        for o in self.observers:
            o.on_turn_advanced(game, stage)

    def on_showdown(self, game):
        for o in self.observers:
            o.on_showdown(game)

    def on_hand_end(self, game, winner_info):
        for o in self.observers:
            o.on_hand_end(game, winner_info)

    def before_ai_action(self, game, player, to_call, stage):
        """Every observer must agree before a bot is passed over."""
        return all(o.before_ai_action(game, player, to_call, stage)
                   for o in self.observers)

    def get_human_action(self, game, player, to_call, stage):
        """Exactly one observer can answer; the first real answer wins.

        A HandLog inherits the base implementation, so it must not be the one
        that answers - hence the check for an observer that actually overrides
        the hook.
        """
        for observer in self.observers:
            if type(observer).get_human_action is GameObserver.get_human_action:
                continue
            return observer.get_human_action(game, player, to_call, stage)
        raise RuntimeError(
            "no observer supplies human actions; a non-AI seat cannot act"
        )
