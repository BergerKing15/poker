"""The observer contract: how a front-end drives and watches a hand.

The Tk UI cannot be exercised without a display, so these tests drive the same
hooks it implements.
"""

import unittest

from poker.game import ConsoleObserver, GameAborted, GameObserver, PokerGame
from tests.support import FixedBot, ScriptedObserver, silent_game


class TestHookLifecycle(unittest.TestCase):
    def play(self, actions=("check",) * 12, players=2, **kwargs):
        observer = ScriptedObserver([(a, None) for a in actions])
        game = silent_game(num_players=players, starting_stack=1000,
                           small_blind=5, big_blind=10, use_bots=True,
                           observer=observer, **kwargs)
        game.players[0].is_ai = False
        game.play_hand()
        return observer, game

    def test_hand_start_precedes_blinds(self):
        observer, _ = self.play()
        self.assertEqual(observer.events[0], "hand_start")
        self.assertTrue(observer.events[1].startswith("blinds:"))

    def test_hand_end_is_last(self):
        observer, _ = self.play()
        self.assertEqual(observer.events[-1], "hand_end")

    def test_streets_are_announced_in_order(self):
        observer, _ = self.play()
        stages = [e.split(":")[1] for e in observer.events if e.startswith("stage:")]
        self.assertEqual(stages[0], "Pre-Flop")
        self.assertEqual(stages, sorted(set(stages), key=stages.index))
        for stage in stages:
            self.assertIn(stage, ["Pre-Flop", "Flop", "Turn", "River"])

    def test_blinds_report_the_seats_that_posted(self):
        observer, game = self.play()
        _, small, big = observer.events[1].split(":")
        self.assertEqual(int(small), (0 + 1) % len(game.players))
        self.assertEqual(int(big), (0 + 2) % len(game.players))

    def test_showdown_fires_only_when_hands_are_compared(self):
        observer, _ = self.play()
        if "showdown" in observer.events:
            self.assertLess(observer.events.index("showdown"),
                            observer.events.index("hand_end"))

    def test_fold_win_skips_showdown(self):
        observer = ScriptedObserver([("fold", None)] * 6)
        game = silent_game(num_players=2, starting_stack=1000, small_blind=5,
                           big_blind=10, use_bots=True, observer=observer)
        game.players[0].is_ai = False
        game.bots = {1: FixedBot(1, "call")}
        game.play_hand()
        self.assertNotIn("showdown", observer.events)
        self.assertEqual(observer.events[-1], "hand_end")


class TestHumanActions(unittest.TestCase):
    def test_human_raise_reaches_the_pot(self):
        observer = ScriptedObserver([("raise", 120)] + [("check", None)] * 10)
        game = silent_game(num_players=2, starting_stack=1000, small_blind=5,
                           big_blind=10, use_bots=True, observer=observer)
        game.players[0].is_ai = False
        # A calling opponent, so the hand reaches the human rather than ending
        # on a fold before seat 0 ever acts.
        game.bots = {1: FixedBot(1, "call")}
        game.play_hand()
        self.assertIn("raise", observer.actions_of(0))
        # The event carries the chips spent. Seat 0 posted the big blind of 10,
        # so raising to 120 costs 110. (Pot and round bets are cleared by the
        # end of the hand, so they cannot be inspected afterwards.)
        raises = [e for e in observer.events if e.startswith("action:0:raise:")]
        self.assertEqual(int(raises[0].split(":")[3]), 110)

    def test_human_seat_is_asked_not_auto_played(self):
        observer = ScriptedObserver([("fold", None)] * 6)
        game = silent_game(num_players=2, starting_stack=1000, use_bots=True,
                           observer=observer)
        game.players[0].is_ai = False
        game.bots = {1: FixedBot(1, "call")}
        game.play_hand()
        self.assertIn("fold", observer.actions_of(0))

    def test_abort_propagates_out_of_play_hand(self):
        observer = ScriptedObserver([])  # runs out immediately
        game = silent_game(num_players=2, starting_stack=1000, use_bots=True,
                           observer=observer)
        game.players[0].is_ai = False
        with self.assertRaises(GameAborted):
            game.play_hand()

    def test_deferred_bot_does_not_hang_the_round(self):
        observer = ScriptedObserver([("check", None)] * 12, defer_bots=3)
        game = silent_game(num_players=3, starting_stack=1000, small_blind=5,
                           big_blind=10, use_bots=True, observer=observer)
        game.players[0].is_ai = False
        game.play_hand()
        self.assertEqual(observer.deferred, 3)
        self.assertEqual(observer.events[-1], "hand_end")
        self.assertEqual(sum(p.stack for p in game.players), 3000)


class TestDefaults(unittest.TestCase):
    def test_bare_game_gets_a_console_observer(self):
        game = PokerGame(num_players=2, use_bots=False)
        self.assertIsInstance(game.observer, ConsoleObserver)

    def test_base_observer_hooks_are_all_no_ops(self):
        observer = GameObserver()
        game = silent_game(num_players=2, use_bots=False)
        player = game.players[0]
        # None of these may raise, and none may return anything meaningful.
        self.assertIsNone(observer.on_hand_start(game))
        self.assertIsNone(observer.on_blinds(game, 0, 1))
        self.assertIsNone(observer.on_stage(game, "Flop"))
        self.assertIsNone(observer.on_action(game, player, "check", 0, "Flop"))
        self.assertIsNone(observer.on_turn_advanced(game, "Flop"))
        self.assertIsNone(observer.on_showdown(game))
        self.assertIsNone(observer.on_hand_end(game, None))
        self.assertTrue(observer.before_ai_action(game, player, 0, "Flop"))

    def test_ui_overrides_every_hook(self):
        """A misspelled hook silently inherits the base no-op, so check names."""
        try:
            from poker.ui.game_window import PokerUI
        except ImportError as exc:  # pragma: no cover - headless CI without Tk
            self.skipTest(f"Tk unavailable: {exc}")

        hooks = [name for name in vars(GameObserver)
                 if not name.startswith("_")]
        self.assertTrue(hooks)
        for name in hooks:
            with self.subTest(hook=name):
                self.assertIsNot(getattr(PokerUI, name), getattr(GameObserver, name),
                                 f"PokerUI does not override {name}")


class TestFanOut(unittest.TestCase):
    def test_all_observers_see_every_hook(self):
        from poker.hand_log import FanOutObserver

        first, second = ScriptedObserver(), ScriptedObserver()
        fan = FanOutObserver(first, second)
        game = silent_game(num_players=2, starting_stack=1000, use_bots=True,
                           observer=fan)
        game.bots = {0: FixedBot(0, "call"), 1: FixedBot(1, "call")}
        game.play_hand()
        self.assertEqual(first.events, second.events)
        self.assertIn("hand_start", first.events)

    def test_human_action_comes_from_the_observer_that_supplies_one(self):
        from poker.hand_log import FanOutObserver

        logger = GameObserver()  # does not supply actions
        front_end = ScriptedObserver([("fold", None)] * 6)
        fan = FanOutObserver(logger, front_end)
        game = silent_game(num_players=2, starting_stack=1000, use_bots=True,
                           observer=fan)
        game.players[0].is_ai = False
        game.bots = {1: FixedBot(1, "call")}
        game.play_hand()
        self.assertIn("fold", front_end.actions_of(0))

    def test_a_bot_is_deferred_only_if_all_observers_agree(self):
        from poker.hand_log import FanOutObserver

        willing = ScriptedObserver([("check", None)] * 12)
        blocking = ScriptedObserver([("check", None)] * 12, defer_bots=99)
        fan = FanOutObserver(willing, blocking)
        game = silent_game(num_players=2, use_bots=False, observer=fan)
        self.assertFalse(fan.before_ai_action(game, game.players[1], 0, "Flop"))


if __name__ == "__main__":
    unittest.main()
