"""Hand flow and pot construction: streets, button, elimination, side pots.

Ported from the original root suite, rewritten to drive the engine rather than
recompute arithmetic in the test.
"""

import unittest

from tests.support import ScriptedObserver, FixedBot, hand, silent_game


class FlowTestCase(unittest.TestCase):
    def game(self, players=3, stack=1000, action="call", **kwargs):
        kwargs.setdefault("small_blind", 5)
        kwargs.setdefault("big_blind", 10)
        game = silent_game(num_players=players, starting_stack=stack,
                           use_bots=True, **kwargs)
        game.bots = {i: FixedBot(i, action) for i in range(players)}
        return game


class TestHandProgression(FlowTestCase):
    def test_button_moves_one_seat_per_hand(self):
        game = self.game(players=3)
        seen = []
        for _ in range(4):
            seen.append(game.button)
            game.play_hand()
        self.assertEqual(seen, [0, 1, 2, 0])

    def test_button_wraps_heads_up(self):
        game = self.game(players=2)
        seen = []
        for _ in range(3):
            seen.append(game.button)
            game.play_hand()
        self.assertEqual(seen, [0, 1, 0])

    def test_each_street_is_dealt_in_turn(self):
        observer = ScriptedObserver()
        game = self.game(players=3, observer=observer)
        game.play_hand()
        stages = [e.split(":")[1] for e in observer.events if e.startswith("stage:")]
        self.assertEqual(stages, ["Pre-Flop", "Flop", "Turn", "River"])

    def test_board_grows_three_then_one_then_one(self):
        sizes = []

        class Watcher(ScriptedObserver):
            def on_stage(self, game, stage):
                super().on_stage(game, stage)
                sizes.append(len(game.community_cards))

        game = self.game(players=3, observer=Watcher())
        game.play_hand()
        self.assertEqual(sizes, [0, 3, 4, 5])

    def test_board_cards_are_all_distinct(self):
        game = self.game(players=3)
        game.play_hand()
        board = [str(c) for c in game.community_cards]
        self.assertEqual(len(board), len(set(board)))

    def test_hole_cards_never_appear_on_the_board(self):
        game = self.game(players=3)
        game.play_hand()
        board = {str(c) for c in game.community_cards}
        for player in game.players:
            self.assertFalse(board & {str(c) for c in player.hole_cards})

    def test_hand_number_increments(self):
        game = self.game(players=2)
        game.play_hand()
        game.play_hand()
        self.assertEqual(game.hand_number, 2)

    def test_pot_is_cleared_between_hands(self):
        game = self.game(players=3)
        game.play_hand()
        self.assertEqual(game.pot, 0)

    def test_everyone_folding_ends_the_hand_early(self):
        observer = ScriptedObserver()
        game = self.game(players=3, action="fold", observer=observer)
        game.play_hand()
        stages = [e for e in observer.events if e.startswith("stage:")]
        self.assertEqual(stages, ["stage:Pre-Flop"])
        self.assertNotIn("showdown", observer.events)


class TestRoundBookkeeping(FlowTestCase):
    def test_round_bets_reset_between_streets(self):
        game = self.game(players=2)
        game.players[0].total_bet_this_round = 50
        game.players[1].total_bet_this_round = 100
        game.current_bet = 100
        game.reset_round_bets()
        self.assertEqual([p.total_bet_this_round for p in game.players], [0, 0])
        self.assertEqual(game.current_bet, 0)

    def test_whole_hand_contributions_survive_the_reset(self):
        """The street bet is cleared, the hand total is not - side pots need it."""
        game = self.game(players=2)
        game.post_blinds()
        before = dict(game.total_bet_by_player)
        game.reset_round_bets()
        self.assertEqual(game.total_bet_by_player, before)
        self.assertGreater(sum(before.values()), 0)

    def test_current_bet_rises_with_raises_and_holds_on_a_call(self):
        game = self.game(players=3)
        game.current_bet = 10
        game._apply_raise(game.players[0], 50)
        self.assertEqual(game.current_bet, 50)
        game._apply_raise(game.players[1], 150)
        self.assertEqual(game.current_bet, 150)
        game._apply_action(game.players[2], "call", None, 150, "Pre-Flop")
        self.assertEqual(game.current_bet, 150)

    def test_blinds_go_into_the_pot(self):
        game = self.game(players=3)
        game.post_blinds()
        self.assertEqual(game.pot, game.small_blind + game.big_blind)

    def test_pot_equals_what_players_put_in(self):
        game = self.game(players=3)
        game.post_blinds()
        game._apply_raise(game.players[0], 60)
        self.assertEqual(game.pot, sum(game.total_bet_by_player.values()))


class TestActivePlayers(FlowTestCase):
    def test_a_busted_player_is_no_longer_active(self):
        game = self.game(players=3)
        game.players[1].stack = 0
        active = game.get_active_players()
        self.assertEqual(len(active), 2)
        self.assertNotIn(1, [p.player_id for p in active])

    def test_folded_players_are_excluded_from_unfolded(self):
        game = self.game(players=3)
        game.players[0].is_folded = True
        self.assertEqual([p.player_id for p in game.get_unfolded_players()], [1, 2])

    def test_all_in_players_cannot_act(self):
        game = self.game(players=3)
        game.players[2].is_all_in = True
        self.assertNotIn(2, [p.player_id for p in game.get_players_still_acting()])

    def test_opponent_helpers_exclude_the_subject(self):
        game = self.game(players=3)
        subject = game.players[0]
        self.assertNotIn(subject, game.get_active_opponents(subject))
        self.assertNotIn(subject, game.get_unfolded_opponents(subject))


class TestBettingOrder(FlowTestCase):
    def first_actor(self, players, stage):
        observer = ScriptedObserver()
        game = self.game(players=players, observer=observer)
        game.post_blinds()
        game.current_bet = game.big_blind if stage == "Pre-Flop" else 0
        game.betting_round(stage)
        actions = [e for e in observer.events if e.startswith("action:")]
        return int(actions[0].split(":")[1])

    def test_preflop_action_starts_left_of_the_big_blind(self):
        # Button 0, so blinds are seats 1 and 2 and seat 3 is first to act.
        self.assertEqual(self.first_actor(4, "Pre-Flop"), 3)

    def test_postflop_action_starts_left_of_the_button(self):
        self.assertEqual(self.first_actor(4, "Flop"), 1)


class TestSidePots(FlowTestCase):
    """Pot construction at each all-in shape.

    Contributions are set through total_bet_by_player, which is what the engine
    fills in as chips move.
    """

    def pots(self, contributions, folded=()):
        game = self.game(players=len(contributions))
        for player_id, amount in enumerate(contributions):
            game.total_bet_by_player[player_id] = amount
            game.players[player_id].is_folded = player_id in folded
        game.pot = sum(contributions)
        return game, game.create_side_pots()

    def assert_pots_account_for_everything(self, game, pots):
        self.assertEqual(sum(p["amount"] for p in pots), game.pot,
                         "pots must add up to every chip contributed")

    def test_three_unequal_all_ins(self):
        game, pots = self.pots([30, 70, 100])
        self.assertEqual([p["amount"] for p in pots], [90, 80, 30])
        self.assertEqual([set(p["eligible_players"]) for p in pots],
                         [{0, 1, 2}, {1, 2}, {2}])
        self.assert_pots_account_for_everything(game, pots)

    def test_heads_up_all_in_for_less(self):
        game, pots = self.pots([75, 100])
        self.assertEqual([p["amount"] for p in pots], [150, 25])
        self.assertEqual([set(p["eligible_players"]) for p in pots], [{0, 1}, {1}])
        self.assert_pots_account_for_everything(game, pots)

    def test_equal_stacks_make_one_pot(self):
        game, pots = self.pots([100, 100, 100])
        self.assertEqual([p["amount"] for p in pots], [300])
        self.assertEqual(set(pots[0]["eligible_players"]), {0, 1, 2})
        self.assert_pots_account_for_everything(game, pots)

    def test_four_all_in_levels(self):
        game, pots = self.pots([50, 150, 200, 250])
        self.assertEqual([p["amount"] for p in pots], [200, 300, 100, 50])
        self.assert_pots_account_for_everything(game, pots)

    def test_folded_chips_stay_in_as_dead_money(self):
        # Seat 0 folded after putting in 50: those chips remain in the pot, but
        # seat 0 cannot win any of it.
        game, pots = self.pots([50, 100, 150], folded={0})
        self.assertEqual([p["amount"] for p in pots], [250, 50])
        for pot in pots:
            self.assertNotIn(0, pot["eligible_players"])
        self.assert_pots_account_for_everything(game, pots)

    def test_one_player_left_needs_no_pots(self):
        game, pots = self.pots([50, 100], folded={0})
        self.assertEqual(pots, [])

    def test_street_bets_are_used_when_nothing_was_recorded(self):
        """Scenarios built by assigning total_bet_this_round still work."""
        game = self.game(players=3)
        for player, amount in zip(game.players, (30, 70, 100)):
            player.total_bet_this_round = amount
        self.assertEqual([p["amount"] for p in game.create_side_pots()],
                         [90, 80, 30])


class TestShowdownPayouts(FlowTestCase):
    def test_short_all_in_wins_only_the_main_pot(self):
        game = self.game(players=3)
        # Seat 0 is all-in for 50 and has the best hand; seats 1 and 2 put in
        # 150 each, so the side pot is theirs to contest.
        game.players[0].hole_cards = hand("AS AH")
        game.players[1].hole_cards = hand("KS KH")
        game.players[2].hole_cards = hand("2S 3H")
        game.community_cards = hand("AD KD 7C 4S 9H")
        for player_id, amount in enumerate((50, 150, 150)):
            game.total_bet_by_player[player_id] = amount
            game.players[player_id].stack = 0
        game.pot = 350

        game.determine_winner()

        # Main pot 150 to seat 0 (trip aces), side pot 200 to seat 1 (trip kings).
        self.assertEqual(game.players[0].stack, 150)
        self.assertEqual(game.players[1].stack, 200)
        self.assertEqual(game.players[2].stack, 0)
        self.assertEqual(sum(p.stack for p in game.players), 350)

    def test_uncalled_portion_comes_back(self):
        game = self.game(players=2)
        game.players[0].hole_cards = hand("AS AH")
        game.players[1].hole_cards = hand("KS KH")
        game.community_cards = hand("2D 7C 9H 4S 3C")
        game.total_bet_by_player[0] = 200
        game.total_bet_by_player[1] = 80
        game.players[0].stack = 0
        game.players[1].stack = 0
        game.pot = 280

        game.determine_winner()
        self.assertEqual(sum(p.stack for p in game.players), 280)


if __name__ == "__main__":
    unittest.main()
