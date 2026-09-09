"""Cards, decks and hand evaluation."""

import unittest
from itertools import combinations

from poker.game import Card, Deck, HandEvaluator, Player
from tests.support import card, hand


class TestCard(unittest.TestCase):
    def test_rejects_invalid_suit_and_rank(self):
        with self.assertRaises(ValueError):
            Card("Wands", "A")
        with self.assertRaises(ValueError):
            Card("Spades", "1")

    def test_ten_is_spelled_with_two_characters(self):
        # A recurring source of bugs: notation writes "T", cards write "10".
        self.assertIn("10", Card.RANKS)
        self.assertNotIn("T", Card.RANKS)
        self.assertEqual(str(Card("Diamonds", "10")), "10D")

    def test_repr_is_rank_plus_suit_initial(self):
        self.assertEqual(str(Card("Spades", "A")), "AS")
        self.assertEqual(str(Card("Hearts", "K")), "KH")


class TestDeck(unittest.TestCase):
    def test_deck_has_52_unique_cards(self):
        deck = Deck()
        self.assertEqual(len(deck.cards), 52)
        self.assertEqual(len({str(c) for c in deck.cards}), 52)

    def test_dealing_removes_cards(self):
        deck = Deck()
        dealt = deck.deal(5)
        self.assertEqual(len(dealt), 5)
        self.assertEqual(len(deck.cards), 47)
        self.assertFalse({str(c) for c in dealt} & {str(c) for c in deck.cards})

    def test_dealing_more_than_remains_raises(self):
        deck = Deck()
        deck.deal(50)
        with self.assertRaises(ValueError):
            deck.deal(3)


class TestHandEvaluator(unittest.TestCase):
    def assert_hand(self, cards_text, expected):
        self.assertEqual(HandEvaluator.evaluate_hand(hand(cards_text))[0], expected)

    def test_each_hand_category(self):
        self.assert_hand("AS KS QS JS 10S", "Royal Flush")
        self.assert_hand("9H 8H 7H 6H 5H", "Straight Flush")
        self.assert_hand("7S 7H 7D 7C 2S", "Four of a Kind")
        self.assert_hand("7S 7H 7D 2C 2S", "Full House")
        self.assert_hand("AS JS 9S 5S 2S", "Flush")
        self.assert_hand("9H 8S 7D 6C 5S", "Straight")
        self.assert_hand("7S 7H 7D 9C 2S", "Three of a Kind")
        self.assert_hand("7S 7H 9D 9C 2S", "Two Pair")
        self.assert_hand("7S 7H 9D 5C 2S", "One Pair")
        self.assert_hand("AS JH 9D 5C 2S", "High Card")

    def test_wheel_is_a_straight(self):
        # A-2-3-4-5, where the ace plays low.
        self.assert_hand("AS 2H 3D 4C 5S", "Straight")
        self.assert_hand("AS 2S 3S 4S 5S", "Straight Flush")

    def test_royal_flush_beats_straight_flush(self):
        royal = HandEvaluator.evaluate_hand(hand("AS KS QS JS 10S"))
        straight = HandEvaluator.evaluate_hand(hand("9H 8H 7H 6H 5H"))
        self.assertGreater(HandEvaluator.HAND_RANKS[royal[0]],
                           HandEvaluator.HAND_RANKS[straight[0]])

    def test_ranking_order_is_strictly_increasing(self):
        order = ["High Card", "One Pair", "Two Pair", "Three of a Kind",
                 "Straight", "Flush", "Full House", "Four of a Kind",
                 "Straight Flush", "Royal Flush"]
        values = [HandEvaluator.HAND_RANKS[name] for name in order]
        self.assertEqual(values, sorted(values))
        self.assertEqual(len(set(values)), len(values))

    def test_find_best_hand_picks_the_flush_over_the_pair(self):
        best = HandEvaluator.find_best_hand(hand("AS 2S"), hand("KS 9S 5S 9D 3C"))
        self.assertEqual(best[0], "Flush")
        self.assertEqual(len(best[1]), 5)

    def test_find_best_hand_uses_the_board_when_it_is_better(self):
        # The board is a straight; the hole cards add nothing.
        best = HandEvaluator.find_best_hand(hand("2C 3D"), hand("9H 8S 7D 6C 5S"))
        self.assertEqual(best[0], "Straight")

    def test_higher_pair_wins_on_tiebreaker(self):
        aces = HandEvaluator.evaluate_hand(hand("AS AH 9D 5C 2S"))
        kings = HandEvaluator.evaluate_hand(hand("KS KH 9D 5C 2S"))
        self.assertEqual(aces[0], kings[0])
        self.assertGreater(aces[1], kings[1])

    def test_kicker_decides_equal_pairs(self):
        better = HandEvaluator.evaluate_hand(hand("AS AH KD 5C 2S"))
        worse = HandEvaluator.evaluate_hand(hand("AS AH QD 5C 2S"))
        self.assertGreater(better[1], worse[1])

    def test_every_five_card_combination_evaluates(self):
        """No hand of five real cards may raise or return an unknown type."""
        deck = [Card(s, r) for s in Card.SUITS for r in Card.RANKS]
        for combo in list(combinations(deck[:14], 5)):
            hand_type, tiebreaker = HandEvaluator.evaluate_hand(list(combo))
            self.assertIn(hand_type, HandEvaluator.HAND_RANKS)
            self.assertIsInstance(tiebreaker, tuple)


class TestPlayer(unittest.TestCase):
    def test_reset_clears_per_hand_state(self):
        player = Player(0, 1000)
        player.receive_cards(hand("AS KS"))
        player.is_folded = True
        player.is_all_in = True
        player.total_bet_this_round = 50

        player.reset_for_new_hand()

        self.assertFalse(player.is_folded)
        self.assertFalse(player.is_all_in)
        self.assertEqual(player.total_bet_this_round, 0)
        self.assertEqual(player.hole_cards, [])

    def test_reset_keeps_the_stack(self):
        player = Player(0, 1000)
        player.stack = 640
        player.reset_for_new_hand()
        self.assertEqual(player.stack, 640)


if __name__ == "__main__":
    unittest.main()
