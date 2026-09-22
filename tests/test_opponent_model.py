"""Opponent modelling: what the profiles measure, and how bots use them."""

import unittest

from poker.bot import PokerBot
from poker.game import GameObserver, PokerGame
from poker.opponent_model import (MIN_HANDS, NEUTRAL_FOLD_TO_BET, NEUTRAL_VPIP,
                                  OpponentModel, OpponentProfile)
from poker.tournament import BotTournament
from tests.support import FixedBot, silent_game


def profile_with(hands=40, vpip_hands=12, pfr_hands=6, bets=10, calls=10,
                 faced=20, folds_faced=10):
    p = OpponentProfile(1)
    p.hands_seen = hands
    p.hands_voluntarily_played = vpip_hands
    p.hands_raised_preflop = pfr_hands
    p.bets_and_raises = bets
    p.calls = calls
    p.folds = folds_faced
    p.times_facing_a_bet = faced
    p.folds_facing_a_bet = folds_faced
    return p


class TestProfileRates(unittest.TestCase):
    def test_rates_are_computed_from_the_counts(self):
        p = profile_with()
        self.assertAlmostEqual(p.vpip, 12 / 40)
        self.assertAlmostEqual(p.preflop_raise, 6 / 40)
        self.assertAlmostEqual(p.aggression, 10 / 20)
        self.assertAlmostEqual(p.fold_to_bet, 10 / 20)

    def test_an_unseen_seat_reads_neutral_rather_than_dividing_by_zero(self):
        p = OpponentProfile(3)
        self.assertEqual(p.vpip, NEUTRAL_VPIP)
        self.assertEqual(p.fold_to_bet, NEUTRAL_FOLD_TO_BET)
        self.assertEqual(p.preflop_raise, 0.0)

    def test_a_thin_sample_is_not_trusted(self):
        p = profile_with(hands=MIN_HANDS - 1)
        self.assertFalse(p.is_reliable)
        self.assertEqual(p.style, "unknown")

    def test_enough_hands_makes_it_reliable(self):
        self.assertTrue(profile_with(hands=MIN_HANDS).is_reliable)

    def test_styles_span_both_axes(self):
        tight_passive = profile_with(vpip_hands=4, bets=1, calls=20)
        tight_aggressive = profile_with(vpip_hands=4, bets=20, calls=1)
        loose_passive = profile_with(vpip_hands=32, bets=1, calls=20)
        loose_aggressive = profile_with(vpip_hands=32, bets=20, calls=1)
        self.assertEqual(tight_passive.style, "tight-passive")
        self.assertEqual(tight_aggressive.style, "tight-aggressive")
        self.assertEqual(loose_passive.style, "loose-passive")
        self.assertEqual(loose_aggressive.style, "loose-aggressive")

    def test_repr_names_the_seat(self):
        self.assertIn("seat=1", repr(profile_with()))


class TestTableRead(unittest.TestCase):
    def setUp(self):
        self.model = OpponentModel()

    def test_nothing_observed_reads_neutral(self):
        read = self.model.table_read()
        self.assertFalse(read.reliable)
        self.assertTrue(read.is_neutral)
        self.assertEqual(read.vpip, NEUTRAL_VPIP)

    def test_thin_profiles_are_ignored(self):
        self.model.profiles[1] = profile_with(hands=MIN_HANDS - 1)
        self.assertFalse(self.model.table_read().reliable)

    def test_the_read_excludes_the_asking_seat(self):
        self.model.profiles[0] = profile_with(vpip_hands=40)   # the hero
        self.model.profiles[1] = profile_with(vpip_hands=0)
        read = self.model.table_read(exclude=0)
        self.assertTrue(read.reliable)
        self.assertAlmostEqual(read.vpip, 0.0)

    def test_the_read_averages_the_opponents(self):
        self.model.profiles[1] = profile_with(vpip_hands=40)   # 100%
        self.model.profiles[2] = profile_with(vpip_hands=0)    # 0%
        self.assertAlmostEqual(self.model.table_read().vpip, 0.5)

    def test_reset_forgets_everything(self):
        self.model.profiles[1] = profile_with()
        self.model.hands_observed = 5
        self.model.reset()
        self.assertEqual(self.model.profiles, {})
        self.assertEqual(self.model.hands_observed, 0)


class TestLearningFromPlay(unittest.TestCase):
    """The model must recover strategies it was never told about."""

    def observe(self, bots, hands=50):
        model = OpponentModel()
        game = PokerGame(num_players=len(bots), starting_stack=1_000_000,
                         small_blind=5, big_blind=10, use_bots=True,
                         observer=model)
        game.bots = {i: BotTournament.BOT_FACTORY[name](i)
                     for i, name in enumerate(bots)}
        for _ in range(hands):
            game.play_hand()
        return model

    def test_it_counts_the_hands_it_watched(self):
        model = self.observe(["CheckCall", "CheckCall"], hands=7)
        self.assertEqual(model.hands_observed, 7)
        self.assertEqual(model.profile(0).hands_seen, 7)

    def test_a_folder_reads_tight_and_folding(self):
        model = self.observe(["Folder", "CheckCall", "AlwaysRaise"])
        folder = model.profile(0)
        self.assertLess(folder.vpip, 0.25)
        self.assertGreater(folder.fold_to_bet, 0.6)

    def test_a_calling_station_reads_loose_and_passive(self):
        model = self.observe(["CheckCall", "AlwaysRaise", "CheckCall"])
        station = model.profile(0)
        self.assertGreater(station.vpip, 0.6)
        self.assertLess(station.aggression, 0.2)
        self.assertLess(station.fold_to_bet, 0.2)
        self.assertEqual(station.style, "loose-passive")

    def test_a_raiser_reads_aggressive(self):
        model = self.observe(["AlwaysRaise", "CheckCall", "CheckCall"])
        raiser = model.profile(0)
        self.assertGreater(raiser.aggression, 0.5)
        self.assertGreater(raiser.preflop_raise, 0.5)
        self.assertEqual(raiser.style, "loose-aggressive")

    def test_seats_are_told_apart(self):
        model = self.observe(["Folder", "CheckCall", "AlwaysRaise"])
        styles = {p.player_id: p.style for p in model.summary()}
        self.assertNotEqual(styles[0], styles[1])
        self.assertNotEqual(styles[1], styles[2])

    def test_blinds_alone_are_not_voluntary_money(self):
        """A seat that only ever folds must not look like it entered pots."""
        model = self.observe(["Folder", "Folder", "AlwaysRaise"])
        self.assertLess(model.profile(0).vpip, 0.2)

    def test_summary_is_ordered_by_seat(self):
        model = self.observe(["CheckCall", "CheckCall", "CheckCall"], hands=5)
        self.assertEqual([p.player_id for p in model.summary()], [0, 1, 2])


class TestFacingABet(unittest.TestCase):
    """"Facing a bet" is tracked from the street's betting, not guessed."""

    def setUp(self):
        self.model = OpponentModel()
        self.game = silent_game(num_players=3, starting_stack=1000,
                                small_blind=5, big_blind=10, use_bots=False)

    def start_street(self, committed):
        for player, amount in zip(self.game.players, committed):
            player.total_bet_this_round = amount
        self.model.on_hand_start(self.game)
        self.model.on_stage(self.game, "Flop")

    def test_checking_into_an_unopened_pot_is_not_facing_a_bet(self):
        self.start_street([0, 0, 0])
        self.model.on_action(self.game, self.game.players[0], "check", 0, "Flop")
        self.assertEqual(self.model.profile(0).times_facing_a_bet, 0)

    def test_acting_after_a_bet_is_facing_one(self):
        self.start_street([0, 0, 0])
        self.model.on_action(self.game, self.game.players[0], "raise", 50, "Flop")
        self.model.on_action(self.game, self.game.players[1], "fold", 0, "Flop")
        self.assertEqual(self.model.profile(1).times_facing_a_bet, 1)
        self.assertEqual(self.model.profile(1).folds_facing_a_bet, 1)

    def test_the_bettor_is_not_counted_as_facing_its_own_bet(self):
        self.start_street([0, 0, 0])
        self.model.on_action(self.game, self.game.players[0], "raise", 50, "Flop")
        self.assertEqual(self.model.profile(0).times_facing_a_bet, 0)

    def test_a_big_blind_checking_its_option_is_not_facing_a_bet(self):
        # Pre-flop, the big blind has the largest commitment already in.
        for player, amount in zip(self.game.players, [0, 5, 10]):
            player.total_bet_this_round = amount
        self.model.on_hand_start(self.game)
        self.model.on_stage(self.game, "Pre-Flop")
        self.model.on_action(self.game, self.game.players[2], "check", 0, "Pre-Flop")
        self.assertEqual(self.model.profile(2).times_facing_a_bet, 0)

    def test_a_hand_is_counted_once_however_often_it_raises(self):
        self.model.on_hand_start(self.game)
        self.model.on_stage(self.game, "Pre-Flop")
        hero = self.game.players[0]
        self.model.on_action(self.game, hero, "raise", 30, "Pre-Flop")
        self.model.on_action(self.game, hero, "raise", 60, "Pre-Flop")
        profile = self.model.profile(0)
        self.assertEqual(profile.hands_voluntarily_played, 1)
        self.assertEqual(profile.hands_raised_preflop, 1)
        self.assertEqual(profile.bets_and_raises, 2)


class TestBotAdaptation(unittest.TestCase):
    def hero(self, model=None):
        bot = PokerBot(0, "TAG")
        bot.opponent_model = model
        return bot

    def table_of(self, fold_rate, vpip_rate, hands=40):
        model = OpponentModel()
        for seat in (1, 2):
            p = model.profile(seat)
            p.hands_seen = hands
            p.times_facing_a_bet = hands
            p.folds_facing_a_bet = round(hands * fold_rate)
            p.hands_voluntarily_played = round(hands * vpip_rate)
            p.bets_and_raises, p.calls = 10, 10
        return model

    def test_no_model_means_no_adjustment(self):
        self.assertEqual(self.hero()._adjust_to_table(), (1.0, 1.0))

    def test_a_fresh_table_means_no_adjustment(self):
        self.assertEqual(self.hero(OpponentModel())._adjust_to_table(), (1.0, 1.0))

    def test_a_thin_sample_means_no_adjustment(self):
        model = self.table_of(0.9, 0.1, hands=MIN_HANDS - 1)
        self.assertEqual(self.hero(model)._adjust_to_table(), (1.0, 1.0))

    def test_opponents_who_fold_make_it_raise_more(self):
        _, raise_multiplier = self.hero(self.table_of(0.9, 0.1))._adjust_to_table()
        self.assertGreater(raise_multiplier, 1.0)

    def test_opponents_who_never_fold_make_it_bluff_less(self):
        _, raise_multiplier = self.hero(self.table_of(0.05, 0.9))._adjust_to_table()
        self.assertLess(raise_multiplier, 1.0)

    def test_a_loose_table_makes_it_fold_less(self):
        fold_multiplier, _ = self.hero(self.table_of(0.5, 0.9))._adjust_to_table()
        self.assertLess(fold_multiplier, 1.0)

    def test_a_tight_table_makes_it_fold_more(self):
        fold_multiplier, _ = self.hero(self.table_of(0.5, 0.05))._adjust_to_table()
        self.assertGreater(fold_multiplier, 1.0)

    def test_adjustments_stay_within_their_bounds(self):
        """A read tilts the strategy; it must never take it over."""
        for fold_rate in (0.0, 0.5, 1.0):
            for vpip_rate in (0.0, 0.5, 1.0):
                with self.subTest(fold=fold_rate, vpip=vpip_rate):
                    fold_m, raise_m = self.hero(
                        self.table_of(fold_rate, vpip_rate))._adjust_to_table()
                    self.assertGreaterEqual(fold_m, 0.75)
                    self.assertLessEqual(fold_m, 1.30)
                    self.assertGreaterEqual(raise_m, 0.70)
                    self.assertLessEqual(raise_m, 1.50)

    def test_an_adapting_bot_still_returns_legal_actions(self):
        from tests.support import hand
        bot = self.hero(self.table_of(0.9, 0.1))
        for _ in range(20):
            action, amount = bot.decide_action(
                hand("AS KH"), hand("2C 7D 9H"), 20, 10, 1000, 60, "late", 2, 5, 10)
            self.assertIn(action, {"fold", "check", "call", "raise"})


class TestEngineWiring(unittest.TestCase):
    def test_every_game_carries_a_model(self):
        game = silent_game(num_players=2, use_bots=False)
        self.assertIsInstance(game.opponent_model, OpponentModel)

    def test_the_model_is_linked_to_bots_that_can_use_it(self):
        game = silent_game(num_players=2, starting_stack=1000, small_blind=5,
                           big_blind=10, use_bots=True)
        game.bots = {0: PokerBot(0, "TAG"), 1: PokerBot(1, "NIT")}
        game.play_hand()
        for bot in game.bots.values():
            self.assertIs(bot.opponent_model, game.opponent_model)

    def test_bots_that_cannot_use_a_read_are_left_alone(self):
        game = silent_game(num_players=2, starting_stack=1000, small_blind=5,
                           big_blind=10, use_bots=True)
        game.bots = {0: FixedBot(0, "call"), 1: FixedBot(1, "call")}
        game.play_hand()
        self.assertFalse(hasattr(game.bots[0], "opponent_model"))

    def test_an_explicit_model_survives_linking(self):
        """A caller who supplies a bot's model keeps it."""
        own = OpponentModel()
        game = silent_game(num_players=2, starting_stack=1000, small_blind=5,
                           big_blind=10, use_bots=True)
        game.bots = {0: PokerBot(0, "TAG", opponent_model=own),
                     1: PokerBot(1, "NIT")}
        game.play_hand()
        self.assertIs(game.bots[0].opponent_model, own)
        self.assertIs(game.bots[1].opponent_model, game.opponent_model)

    def test_the_game_learns_while_it_plays(self):
        game = silent_game(num_players=3, starting_stack=1_000_000,
                           small_blind=5, big_blind=10, use_bots=True)
        game.bots = {i: BotTournament.BOT_FACTORY[n](i)
                     for i, n in enumerate(["CheckCall", "AlwaysRaise", "Folder"])}
        for _ in range(MIN_HANDS + 5):
            game.play_hand()
        read = game.opponent_model.table_read(exclude=0)
        self.assertTrue(read.reliable)


if __name__ == "__main__":
    unittest.main()
