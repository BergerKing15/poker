"""Betting rules: raise sizing, the minimum-raise rule, all-ins, round completion."""

import random
import unittest

from poker.game import GameObserver, PokerGame
from tests.support import FixedBot, ScriptedObserver, hand, silent_game


class BettingTestCase(unittest.TestCase):
    def game(self, players=2, stack=1000, **kwargs):
        kwargs.setdefault("small_blind", 5)
        kwargs.setdefault("big_blind", 10)
        kwargs.setdefault("use_bots", False)
        return silent_game(num_players=players, starting_stack=stack, **kwargs)

    def facing_a_raise(self, stack=990, already_in=10, current_bet=30, last_raise=20):
        """A player who posted `already_in` and now faces a bet of `current_bet`."""
        game = self.game()
        player = game.players[0]
        player.stack = stack
        player.total_bet_this_round = already_in
        game.current_bet = current_bet
        game.last_raise_size = last_raise
        game.pot = current_bet + already_in
        return game, player


class TestRaiseSemantics(BettingTestCase):
    def test_raise_amount_is_a_total_not_an_increment(self):
        game, player = self.facing_a_raise()
        spent = game._apply_raise(player, 60)
        self.assertEqual(player.total_bet_this_round, 60)
        self.assertEqual(spent, 50)  # 20 to call, 40 more on top

    def test_raise_moves_the_current_bet_up(self):
        game, player = self.facing_a_raise()
        game._apply_raise(player, 60)
        self.assertEqual(game.current_bet, 60)

    def test_chips_leave_the_stack_and_enter_the_pot(self):
        game, player = self.facing_a_raise()
        pot_before, stack_before = game.pot, player.stack
        spent = game._apply_raise(player, 60)
        self.assertEqual(player.stack, stack_before - spent)
        self.assertEqual(game.pot, pot_before + spent)


class TestMinimumRaise(BettingTestCase):
    def test_minimum_is_current_bet_plus_last_raise(self):
        game, _ = self.facing_a_raise(current_bet=30, last_raise=20)
        self.assertEqual(game.minimum_raise_to(), 50)

    def test_minimum_is_never_below_the_big_blind(self):
        game, _ = self.facing_a_raise(current_bet=30, last_raise=2)
        self.assertEqual(game.minimum_raise_to(), 30 + game.big_blind)

    def test_undersized_raise_is_clamped_up(self):
        game, player = self.facing_a_raise(current_bet=30, last_raise=20)
        game._apply_raise(player, 31)
        self.assertEqual(player.total_bet_this_round, 50)

    def test_a_raise_sets_the_next_minimum(self):
        game, player = self.facing_a_raise(current_bet=30, last_raise=20)
        game._apply_raise(player, 90)
        self.assertEqual(game.last_raise_size, 60)
        self.assertEqual(game.minimum_raise_to(), 150)

    def test_short_stack_may_shove_below_the_minimum(self):
        game, player = self.facing_a_raise(stack=25, already_in=10)
        game._apply_raise(player, 10_000)
        self.assertEqual(player.stack, 0)
        self.assertEqual(player.total_bet_this_round, 35)
        self.assertLess(player.total_bet_this_round, 50)

    def test_short_all_in_does_not_reopen_betting(self):
        game, player = self.facing_a_raise(stack=25, already_in=10,
                                           current_bet=30, last_raise=20)
        game._apply_raise(player, 10_000)
        # The shove was only 5 over the current bet, so the minimum stands.
        self.assertEqual(game.last_raise_size, 20)

    def test_huge_number_means_all_in(self):
        game, player = self.facing_a_raise()
        game._apply_raise(player, 10 ** 9)
        self.assertEqual(player.stack, 0)

    def test_last_raise_size_resets_between_streets(self):
        game, player = self.facing_a_raise()
        game._apply_raise(player, 200)
        game.reset_round_bets()
        self.assertEqual(game.last_raise_size, game.big_blind)
        self.assertEqual(game.current_bet, 0)


class TestActionHandling(BettingTestCase):
    def apply(self, action, raise_amount=None, to_call=20, **kwargs):
        game, player = self.facing_a_raise(**kwargs)
        effective, taken = game._apply_action(player, action, raise_amount,
                                              to_call, "Pre-Flop")
        return game, player, effective, taken

    def test_fold_marks_the_player(self):
        _, player, effective, taken = self.apply("fold")
        self.assertTrue(player.is_folded)
        self.assertEqual(effective, "fold")
        self.assertTrue(taken)

    def test_call_matches_the_bet(self):
        _, player, effective, _ = self.apply("call")
        self.assertEqual(effective, "call")
        self.assertEqual(player.total_bet_this_round, 30)

    def test_check_facing_a_bet_becomes_a_call(self):
        _, player, effective, _ = self.apply("check")
        self.assertEqual(effective, "call")
        self.assertEqual(player.total_bet_this_round, 30)

    def test_check_is_legal_when_nothing_is_owed(self):
        game, player = self.facing_a_raise(current_bet=10, already_in=10)
        effective, taken = game._apply_action(player, "check", None, 0, "Flop")
        self.assertEqual(effective, "check")
        self.assertTrue(taken)

    def test_unknown_action_folds(self):
        _, player, effective, _ = self.apply("interpretive dance")
        self.assertEqual(effective, "fold")
        self.assertTrue(player.is_folded)

    def test_empty_stack_always_marks_all_in(self):
        # Whatever route empties the stack, the player must be flagged, or the
        # round asks them to act forever and they can never match the bet.
        game, player = self.facing_a_raise(stack=5, already_in=10)
        game._apply_action(player, "call", None, 20, "Pre-Flop")
        self.assertEqual(player.stack, 0)
        self.assertTrue(player.is_all_in)

    def test_folded_player_is_not_marked_all_in(self):
        game, player = self.facing_a_raise(stack=0, already_in=10)
        game._apply_action(player, "fold", None, 20, "Pre-Flop")
        self.assertTrue(player.is_folded)
        self.assertFalse(player.is_all_in)


class TestBettingRound(BettingTestCase):
    def test_round_ends_when_all_bets_match(self):
        game = self.game(players=3, use_bots=True)
        game.bots = {i: FixedBot(i, "call") for i in range(3)}
        game.post_blinds()
        game.current_bet = game.big_blind
        game.betting_round("Pre-Flop")
        still_acting = game.get_players_still_acting()
        bets = {p.total_bet_this_round for p in still_acting}
        self.assertLessEqual(len(bets), 1)

    def test_round_returns_immediately_when_everyone_is_all_in(self):
        game = self.game(players=3, use_bots=True)
        game.bots = {i: FixedBot(i, "call") for i in range(3)}
        for player in game.players:
            player.is_all_in = True
        game.betting_round("Flop")  # must not spin to the iteration guard
        self.assertEqual(sum(b.calls for b in game.bots.values()), 0)

    def test_round_returns_when_only_one_player_is_left(self):
        game = self.game(players=3, use_bots=True)
        game.bots = {i: FixedBot(i, "call") for i in range(3)}
        game.players[1].is_folded = True
        game.players[2].is_folded = True
        game.betting_round("Flop")
        self.assertEqual(sum(b.calls for b in game.bots.values()), 0)

    def test_a_raise_reopens_action_for_players_who_already_acted(self):
        observer = ScriptedObserver()
        game = self.game(players=3, use_bots=True, observer=observer)
        # Seat 2 raises once, everyone else calls, so seats that acted before
        # the raise must be asked again.
        game.bots = {0: FixedBot(0, "call"), 1: FixedBot(1, "call"),
                     2: FixedBot(2, "raise", 40)}
        game.post_blinds()
        game.current_bet = game.big_blind
        game.betting_round("Pre-Flop")
        self.assertGreaterEqual(len(observer.actions_of(0)), 2)


class TestChipConservation(BettingTestCase):
    def test_chips_are_conserved_across_many_random_games(self):
        from poker.tournament import BotTournament

        random.seed(4242)
        names = list(BotTournament.BOT_FACTORY)
        for num_players in (2, 3, 5):
            for _ in range(3):
                types = [random.choice(names) for _ in range(num_players)]
                game = silent_game(num_players=num_players, starting_stack=1000,
                                   small_blind=5, big_blind=10, use_bots=True)
                game.bots = {i: BotTournament.BOT_FACTORY[t](i)
                             for i, t in enumerate(types)}
                for _ in range(8):
                    game.play_hand()
                self.assertEqual(
                    sum(p.stack for p in game.players), 1000 * num_players,
                    f"chips leaked with {types}",
                )

    def test_split_pot_does_not_mint_a_chip(self):
        game = self.game()
        game.players[0].hole_cards = hand("AS KH")
        game.players[1].hole_cards = hand("AD KC")
        game.community_cards = hand("2S 5H 9C JD QS")
        game.players[0].stack = 900
        game.players[1].stack = 900
        game.pot = 200
        game.determine_winner()
        self.assertEqual(sum(p.stack for p in game.players), 2000)

    def test_split_pot_awards_odd_chips_once(self):
        game = self.game()
        game.players[0].hole_cards = hand("AS KH")
        game.players[1].hole_cards = hand("AD KC")
        game.community_cards = hand("2S 5H 9C JD QS")
        game.players[0].stack = 900
        game.players[1].stack = 900
        game.pot = 201
        game.determine_winner()
        self.assertEqual(sum(p.stack for p in game.players), 2001)


class TestWinnerReporting(BettingTestCase):
    def test_showdown_reports_who_won(self):
        game = self.game()
        game.players[0].hole_cards = hand("AS AH")
        game.players[1].hole_cards = hand("2D 7C")
        game.community_cards = hand("AD 5H 9C JD QS")
        game.pot = 100
        info = game.determine_winner()
        self.assertEqual([p.player_id for p in info["winners"]], [0])
        self.assertEqual(info["hand_type"], "Three of a Kind")

    def test_fold_win_reports_the_survivor(self):
        game = self.game()
        game.players[1].is_folded = True
        game.pot = 40
        info = game.determine_winner()
        self.assertEqual([p.player_id for p in info["winners"]], [0])
        self.assertEqual(info["hand_type"], "Opponents Folded")

    def test_split_pot_reports_both_winners(self):
        game = self.game()
        game.players[0].hole_cards = hand("AS KH")
        game.players[1].hole_cards = hand("AD KC")
        game.community_cards = hand("2S 5H 9C JD QS")
        game.pot = 100
        info = game.determine_winner()
        self.assertEqual(len(info["winners"]), 2)


if __name__ == "__main__":
    unittest.main()
