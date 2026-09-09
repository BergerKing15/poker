"""Equity calculation and its caching.

Monte Carlo results move between runs, so every bound here is set several
standard errors clear of the value it is checking. Anything that needs to sit
near a boundary is asserted as a set of acceptable answers instead.
"""

import random
import unittest

from poker.equity import WinProbabilityCalculator
from poker.equity_cache import (CachedEquityCalculator, RESULT_FIELDS,
                                load_preflop_table, save_preflop_table)
from poker.notation import all_preflop_keys, cards_for_key
from tests.support import hand

# Enough samples to keep the standard error near 1%, without making the suite
# unbearable: 0.5 / sqrt(2500) = 0.01.
SAMPLES = 2500
SEED = 20240501


class EquityTestCase(unittest.TestCase):
    def setUp(self):
        random.seed(SEED)
        self.calc = WinProbabilityCalculator(num_simulations=SAMPLES)

    def equity(self, hole, board="", opponents=1):
        return self.calc.calculate_win_probability(
            hand(hole), hand(board) if board else [], opponents)["equity"]


class TestValidation(EquityTestCase):
    def test_needs_exactly_two_hole_cards(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_win_probability(hand("AS"), [], 1)
        with self.assertRaises(ValueError):
            self.calc.calculate_win_probability(hand("AS KS QS"), [], 1)

    def test_board_must_be_a_real_street(self):
        for board in ("AS", "AS KS", "AS KS QS JS 10S 9S"):
            with self.subTest(board=board):
                with self.assertRaises(ValueError):
                    self.calc.calculate_win_probability(hand("2C 3D"), hand(board), 1)

    def test_needs_at_least_one_opponent(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_win_probability(hand("AS KS"), [], 0)

    def test_rejects_a_card_appearing_twice(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_win_probability(hand("AS KS"), hand("AS 2D 3C"), 1)
        with self.assertRaises(ValueError):
            self.calc.calculate_win_probability(hand("AS AS"), [], 1)


class TestProbabilities(EquityTestCase):
    def test_probabilities_sum_to_one(self):
        result = self.calc.calculate_win_probability(hand("AS KS"), [], 2)
        total = result["win_prob"] + result["tie_prob"] + result["lose_prob"]
        self.assertAlmostEqual(total, 1.0, places=6)

    def test_all_fields_present_and_in_range(self):
        result = self.calc.calculate_win_probability(hand("AS KS"), [], 2)
        for field in RESULT_FIELDS:
            self.assertIn(field, result)
            self.assertGreaterEqual(result[field], 0.0)
            self.assertLessEqual(result[field], 1.0)


class TestKnownEquities(EquityTestCase):
    """Values checked against published pre-flop equity tables."""

    def test_aces_heads_up(self):
        self.assertAlmostEqual(self.equity("AS AH", opponents=1), 0.85, delta=0.04)

    def test_big_slick_three_handed(self):
        # ~0.488. The suite used to assert a floor of 0.50 here and failed at random.
        self.assertAlmostEqual(self.equity("AS KH", opponents=2), 0.49, delta=0.05)

    def test_worst_hand_is_weak(self):
        self.assertLess(self.equity("7S 2D", opponents=2), 0.35)

    def test_equity_falls_as_opponents_are_added(self):
        heads_up = self.equity("AS AH", opponents=1)
        five_way = self.equity("AS AH", opponents=4)
        self.assertGreater(heads_up, five_way)

    def test_made_hand_beats_air_on_the_same_board(self):
        board = "KD 7C 2H"
        self.assertGreater(self.equity("KS KH", board, 2),
                           self.equity("5S 4H", board, 2))

    def test_the_nuts_on_the_river_is_almost_certain(self):
        self.assertGreater(self.equity("KS KD", "KC 5H 5D 5S 2C", 1), 0.90)

    def test_drawing_hand_improves_by_the_river(self):
        flop = self.equity("AS 2S", "KS 9S 4D", 1)
        made = self.equity("AS 2S", "KS 9S 4S", 1)
        self.assertGreater(made, flop)


class TestHandStrengthCategories(EquityTestCase):
    """The category bands must be reachable at every table size."""

    def category(self, hole, board="", opponents=1):
        return self.calc.get_hand_strength(
            hand(hole), hand(board) if board else [], opponents)

    def test_best_starting_hand_is_excellent_heads_up(self):
        self.assertEqual(self.category("AS AH", opponents=1), "excellent")

    def test_worst_starting_hand_is_weak(self):
        self.assertIn(self.category("7S 2D", opponents=2), {"very weak", "weak"})

    def test_the_nuts_is_excellent(self):
        self.assertEqual(self.category("KS KD", "KC 5H 5D 5S 2C", 1), "excellent")

    def test_top_band_is_reachable_at_every_table_size(self):
        """With fixed offsets the top band was unreachable past four players."""
        for opponents in range(1, 10):
            with self.subTest(opponents=opponents):
                self.assertEqual(
                    self.calc.get_hand_strength(
                        hand("KS KD"), hand("KC 5H 5D 5S 2C"), opponents),
                    "excellent")

    def test_categories_are_ordered_by_equity(self):
        order = ["very weak", "weak", "fair", "good", "very good", "excellent"]
        weak = self.category("7S 2D", "AH KD QC", 2)
        strong = self.category("AS AH", "AD KD QC", 2)
        self.assertLessEqual(order.index(weak), order.index(strong))


class TestCache(unittest.TestCase):
    def setUp(self):
        self.calc = CachedEquityCalculator(num_simulations=200,
                                           use_preflop_table=False)

    def test_repeated_postflop_question_is_answered_from_memory(self):
        args = (hand("AS KH"), hand("2C 7D 9H"), 2)
        first = self.calc.calculate_win_probability(*args)
        second = self.calc.calculate_win_probability(*args)
        self.assertEqual(first, second)
        self.assertEqual(self.calc.misses, 1)
        self.assertEqual(self.calc.hits, 1)

    def test_card_order_does_not_create_a_second_entry(self):
        self.calc.calculate_win_probability(hand("AS KH"), hand("2C 7D 9H"), 2)
        self.calc.calculate_win_probability(hand("KH AS"), hand("9H 2C 7D"), 2)
        self.assertEqual(self.calc.misses, 1)

    def test_suit_isomorphic_hands_share_an_entry(self):
        # AKo is AKo whichever offsuit combination it is.
        self.calc.calculate_win_probability(hand("AS KH"), hand("2C 7D 9H"), 2)
        self.calc.calculate_win_probability(hand("AD KC"), hand("2C 7D 9H"), 2)
        self.assertEqual(self.calc.misses, 1)

    def test_different_opponent_counts_are_separate(self):
        self.calc.calculate_win_probability(hand("AS KH"), hand("2C 7D 9H"), 1)
        self.calc.calculate_win_probability(hand("AS KH"), hand("2C 7D 9H"), 3)
        self.assertEqual(self.calc.misses, 2)

    def test_validation_still_runs_before_the_cache(self):
        with self.assertRaises(ValueError):
            self.calc.calculate_win_probability(hand("AS KH"), hand("2C"), 2)

    def test_callers_cannot_mutate_the_cache(self):
        args = (hand("AS KH"), hand("2C 7D 9H"), 2)
        first = self.calc.calculate_win_probability(*args)
        first["equity"] = 999
        self.assertNotEqual(self.calc.calculate_win_probability(*args)["equity"], 999)

    def test_stats_report_hits_and_misses(self):
        self.calc.calculate_win_probability(hand("AS KH"), hand("2C 7D 9H"), 2)
        self.calc.calculate_win_probability(hand("AS KH"), hand("2C 7D 9H"), 2)
        stats = self.calc.stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertAlmostEqual(stats["hit_rate"], 0.5)


class TestPreflopTable(unittest.TestCase):
    def test_a_table_answers_without_sampling(self):
        table = {"AKo": {"2": [0.45, 0.02, 0.53, 0.46]}}
        calc = CachedEquityCalculator(num_simulations=200, preflop_table=table)
        result = calc.calculate_win_probability(hand("AS KH"), [], 2)
        self.assertEqual(result["equity"], 0.46)
        self.assertEqual(calc.misses, 0)

    def test_a_gap_in_the_table_falls_back_to_sampling(self):
        table = {"AKo": {"2": [0.45, 0.02, 0.53, 0.46]}}
        calc = CachedEquityCalculator(num_simulations=200, preflop_table=table)
        calc.calculate_win_probability(hand("AS AH"), [], 2)  # not in the table
        self.assertEqual(calc.misses, 1)

    def test_missing_table_file_is_not_an_error(self):
        self.assertIsNone(load_preflop_table("no/such/table.json"))

    def test_round_trip_through_disk(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "table.json"
            table = {"AA": {"1": [0.84, 0.005, 0.155, 0.845]}}
            save_preflop_table(table, simulations=1000, path=path)
            self.assertEqual(load_preflop_table(path), table)

    def test_shipped_table_covers_every_hand_if_present(self):
        table = load_preflop_table()
        if not table:
            self.skipTest("pre-flop table has not been built")
        self.assertEqual(set(table), set(all_preflop_keys()))
        for key, row in table.items():
            with self.subTest(hand=key):
                self.assertEqual(set(row), {str(n) for n in range(1, 10)})
                for values in row.values():
                    self.assertEqual(len(values), len(RESULT_FIELDS))

    def test_shipped_table_agrees_with_fresh_sampling(self):
        table = load_preflop_table()
        if not table:
            self.skipTest("pre-flop table has not been built")
        random.seed(SEED)
        calc = WinProbabilityCalculator(num_simulations=SAMPLES)
        for key in ("AA", "AKs", "72o"):
            with self.subTest(hand=key):
                sampled = calc.calculate_win_probability(
                    cards_for_key(key), [], 1)["equity"]
                stored = table[key]["1"][RESULT_FIELDS.index("equity")]
                self.assertAlmostEqual(stored, sampled, delta=0.05)

    def test_shipped_table_orders_hands_correctly(self):
        table = load_preflop_table()
        if not table:
            self.skipTest("pre-flop table has not been built")
        equity = lambda key: table[key]["1"][RESULT_FIELDS.index("equity")]
        self.assertGreater(equity("AA"), equity("KK"))
        self.assertGreater(equity("KK"), equity("AKs"))
        self.assertGreater(equity("AKs"), equity("AKo"))
        self.assertGreater(equity("AKo"), equity("72o"))


if __name__ == "__main__":
    unittest.main()
