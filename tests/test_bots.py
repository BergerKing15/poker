"""Bots: notation, the decide_action contract, ranges and raise sizing."""

import itertools
import unittest

from poker.bot import (BotManager, PokerBot, raise_to_total)
from poker.game import Card
from poker.notation import (all_preflop_keys, cards_for_key, hand_key,
                            preflop_key, RANK_VALUES)
from poker.tournament import BotTournament
from tests.support import card, hand, silent_game

AI_BOTS = {"TAG", "LAG", "CTR", "NIT", "FISH"}
DECK = [Card(s, r) for s in Card.SUITS for r in Card.RANKS]


class TestNotation(unittest.TestCase):
    def test_ten_becomes_T(self):
        self.assertEqual(hand_key(hand("10S KH")), "KT")
        self.assertEqual(hand_key(hand("10S 10H")), "TT")
        self.assertEqual(hand_key(hand("AS 10H")), "AT")

    def test_high_card_comes_first(self):
        self.assertEqual(hand_key(hand("2S AH")), "A2")
        self.assertEqual(hand_key(hand("AH 2S")), "A2")

    def test_suitedness_suffix(self):
        self.assertEqual(hand_key(hand("AS KS"), True), "AKs")
        self.assertEqual(hand_key(hand("AS KH"), True), "AKo")
        self.assertEqual(hand_key(hand("AS AH"), True), "AA", "pairs take no suffix")

    def test_rank_values_accept_both_spellings_of_ten(self):
        self.assertEqual(RANK_VALUES["10"], RANK_VALUES["T"])

    def test_every_real_hand_produces_a_key(self):
        for pair in itertools.combinations(DECK, 2):
            self.assertTrue(hand_key(list(pair)))
            self.assertTrue(hand_key(list(pair), True))

    def test_there_are_exactly_169_starting_hands(self):
        keys = all_preflop_keys()
        self.assertEqual(len(keys), 169)
        self.assertEqual(len(set(keys)), 169)

    def test_every_generated_key_round_trips(self):
        for key in all_preflop_keys():
            self.assertEqual(preflop_key(cards_for_key(key)), key)

    def test_every_reachable_key_is_generated(self):
        reachable = {preflop_key(list(p)) for p in itertools.combinations(DECK, 2)}
        self.assertEqual(reachable, set(all_preflop_keys()))


class TestBotRanges(unittest.TestCase):
    def test_range_constants_are_all_reachable(self):
        """A low-card-first entry is a hand the bot can never be dealt."""
        import poker.bot as bot_module

        reachable = ({hand_key(list(p)) for p in itertools.combinations(DECK, 2)} |
                     {hand_key(list(p), True) for p in itertools.combinations(DECK, 2)})
        checked = 0
        for name in dir(bot_module):
            cls = getattr(bot_module, name)
            if not isinstance(cls, type):
                continue
            for attr in vars(cls):
                value = getattr(cls, attr)
                if (isinstance(value, (set, frozenset)) and value
                        and all(isinstance(h, str) for h in value)):
                    checked += 1
                    unreachable = sorted(h for h in value if h not in reachable)
                    self.assertEqual(unreachable, [],
                                     f"{name}.{attr} lists unplayable hands")
        self.assertGreater(checked, 0, "no range constants were found to check")


class TestRaiseToTotal(unittest.TestCase):
    def test_extra_is_added_to_the_current_bet(self):
        self.assertEqual(raise_to_total(current_bet=30, to_call=20,
                                        player_stack=1000, extra=40), 70)

    def test_capped_by_what_the_player_has(self):
        # Already in 10, holding 25: the most they can reach is 35.
        self.assertEqual(raise_to_total(current_bet=30, to_call=20,
                                        player_stack=25, extra=10_000), 35)

    def test_always_exceeds_the_current_bet(self):
        self.assertGreater(raise_to_total(30, 20, 1000, 0), 30)


class TestBotInterface(unittest.TestCase):
    def test_factory_builds_every_registered_type(self):
        self.assertEqual(len(BotTournament.BOT_FACTORY), 17)
        for name, factory in BotTournament.BOT_FACTORY.items():
            with self.subTest(bot=name):
                bot = factory(1)
                self.assertEqual(bot.player_id, 1)
                self.assertTrue(hasattr(bot, "decide_action"))

    def test_every_bot_returns_a_legal_action(self):
        legal = {"fold", "check", "call", "raise"}
        board = hand("2C 7D 9H")
        for name, factory in BotTournament.BOT_FACTORY.items():
            bot = factory(1)
            for hole in (hand("AS AH"), hand("10S 10H"), hand("7S 2D")):
                for to_call in (0, 20):
                    with self.subTest(bot=name, hole=str(hole), to_call=to_call):
                        action, amount = bot.decide_action(
                            hole, board, 20, to_call, 1000, 60, "late", 2, 5, 10)
                        self.assertIn(action, legal)
                        if action == "raise":
                            self.assertIsInstance(amount, int)

    def test_simple_bots_handle_every_hole_card_pair(self):
        """Exhaustive, because a rank typo only shows on specific cards."""
        for name, factory in BotTournament.BOT_FACTORY.items():
            if name in AI_BOTS:
                continue  # Monte Carlo bots are too slow to sweep
            bot = factory(1)
            for pair in itertools.combinations(DECK, 2):
                bot.decide_action(list(pair), [], 10, 10, 1000, 30,
                                  "late", 2, 5, 10)

    def test_ai_bots_handle_hands_containing_a_ten(self):
        tens = [p for p in itertools.combinations(DECK, 2)
                if any(c.rank == "10" for c in p)][:3]
        for name in sorted(AI_BOTS):
            bot = BotTournament.BOT_FACTORY[name](1)
            for pair in tens:
                bot.decide_action(list(pair), [], 10, 10, 1000, 30,
                                  "late", 2, 5, 10)


class TestPokerBot(unittest.TestCase):
    def test_five_styles_are_defined(self):
        self.assertEqual(set(PokerBot.TYPES), AI_BOTS)

    def test_styles_have_sane_parameters(self):
        for name, style in PokerBot.TYPES.items():
            with self.subTest(style=name):
                self.assertGreaterEqual(style.tightness, 0.0)
                self.assertLessEqual(style.tightness, 1.0)
                self.assertGreaterEqual(style.aggression, 0.0)
                self.assertLessEqual(style.aggression, 1.0)

    def test_unknown_style_falls_back_to_a_random_one(self):
        bot = PokerBot(0, "NOT A REAL STYLE")
        self.assertIn(bot.type, PokerBot.TYPES.values())

    def test_preflop_strength_orders_hands_sensibly(self):
        bot = PokerBot(0, "TAG")
        aces = bot._preflop_hand_strength(hand("AS AH"))
        big_slick = bot._preflop_hand_strength(hand("AS KH"))
        rags = bot._preflop_hand_strength(hand("7S 2D"))
        self.assertGreater(aces, big_slick)
        self.assertGreater(big_slick, rags)

    def test_preflop_strength_handles_tens(self):
        bot = PokerBot(0, "TAG")
        self.assertGreater(bot._preflop_hand_strength(hand("10S 10H")), 0)

    def test_position_multiplier_rises_with_position(self):
        bot = PokerBot(0, "TAG")
        self.assertLess(bot._get_position_multiplier("early"),
                        bot._get_position_multiplier("middle"))
        self.assertLess(bot._get_position_multiplier("middle"),
                        bot._get_position_multiplier("late"))

    def test_calculators_are_shared_between_bots(self):
        first, second = PokerBot(0, "TAG"), PokerBot(1, "NIT")
        self.assertIs(first.win_prob_calc, second.win_prob_calc)


class TestBotManager(unittest.TestCase):
    def test_mixed_pool_spreads_the_styles(self):
        manager = BotManager(5, mixed_types=True)
        self.assertEqual(len({bot.type.name for bot in manager.bots}), 5)

    def test_get_bot_finds_by_seat(self):
        manager = BotManager(3)
        self.assertEqual(manager.get_bot(2).player_id, 2)
        self.assertIsNone(manager.get_bot(99))


class TestEngineIntegration(unittest.TestCase):
    def test_a_broken_bot_is_survivable(self):
        """_bot_decision swallows bot errors, so the hand must still finish."""
        class Exploding:
            player_id = 1
            name = "Exploding"

            def decide_action(self, *args, **kwargs):
                raise RuntimeError("boom")

        game = silent_game(num_players=2, starting_stack=1000, small_blind=5,
                           big_blind=10, use_bots=True)
        game.bots = {0: BotTournament.BOT_FACTORY["CheckCall"](0), 1: Exploding()}
        game.play_hand()
        self.assertEqual(sum(p.stack for p in game.players), 2000)

    def test_every_registered_bot_can_play_a_hand(self):
        for name, factory in BotTournament.BOT_FACTORY.items():
            if name in AI_BOTS:
                continue
            with self.subTest(bot=name):
                game = silent_game(num_players=2, starting_stack=1000,
                                   small_blind=5, big_blind=10, use_bots=True)
                game.bots = {0: factory(0), 1: factory(1)}
                game.play_hand()
                self.assertEqual(sum(p.stack for p in game.players), 2000)


if __name__ == "__main__":
    unittest.main()
