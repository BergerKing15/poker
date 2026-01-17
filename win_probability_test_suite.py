"""
Test suite for win_probability.py

Uses GameTester from game_test_suite.py for common assertion utilities
"""

from game_test_suite import GameTester
from win_probability import WinProbabilityCalculator
from poker_game import Card


class WinProbabilityTester(GameTester):
    """Extended tester with win probability specific assertions"""
    
    def __init__(self):
        super().__init__()
        self.calculator = WinProbabilityCalculator(num_simulations=5000)
    
    def assert_equity_range(
        self,
        actual_equity: float,
        min_equity: float,
        max_equity: float,
        message: str = ""
    ) -> bool:
        """Assert equity is within an expected range"""
        if min_equity <= actual_equity <= max_equity:
            self.assertions_passed += 1
            return True
        else:
            self.assertions_failed += 1
            msg = f"FAIL: {message}\n  Expected: {min_equity:.1%} - {max_equity:.1%}\n  Actual: {actual_equity:.1%}"
            self.test_results.append(msg)
            print(msg)
            return False
    
    def assert_equity_greater(
        self,
        actual_equity: float,
        min_equity: float,
        message: str = ""
    ) -> bool:
        """Assert equity is greater than a threshold"""
        if actual_equity > min_equity:
            self.assertions_passed += 1
            return True
        else:
            self.assertions_failed += 1
            msg = f"FAIL: {message}\n  Expected: > {min_equity:.1%}\n  Actual: {actual_equity:.1%}"
            self.test_results.append(msg)
            print(msg)
            return False
    
    def assert_hand_strength(
        self,
        player_cards,
        community_cards,
        num_opponents: int,
        expected_strength: str,
        message: str = ""
    ) -> bool:
        """Assert hand strength matches expected"""
        actual = self.calculator.get_hand_strength(player_cards, community_cards, num_opponents)
        return self.assert_equal(actual, expected_strength, f"Hand strength: {message}")


def test_premium_preflop_hands():
    """Test premium starting hands"""
    print("Testing Premium Pre-Flop Hands...")
    tester = WinProbabilityTester()
    
    # Test AA
    aa = tester.parse_hand("AS AH")
    result = tester.calculator.calculate_win_probability(aa, [], num_opponents=1)
    tester.assert_equity_range(result['equity'], 0.75, 0.95, "AA heads-up equity")
    tester.assert_hand_strength(aa, [], 1, "excellent", "AA pre-flop")
    
    # Test AA vs 4 opponents (weakens in multi-way)
    result_4way = tester.calculator.calculate_win_probability(aa, [], num_opponents=4)
    tester.assert_equity_range(result_4way['equity'], 0.50, 0.65, "AA in 5-way pot equity")
    
    # Test AK (strong hand)
    ak = tester.parse_hand("AS KH")
    result = tester.calculator.calculate_win_probability(ak, [], num_opponents=2)
    tester.assert_equity_range(result['equity'], 0.50, 0.70, "AK equity vs 2 opponents")
    tester.assert_hand_strength(ak, [], 2, "good", "AK pre-flop")
    
    # Test AQ
    aq = tester.parse_hand("AS QD")
    result = tester.calculator.calculate_win_probability(aq, [], num_opponents=2)
    tester.assert_equity_range(result['equity'], 0.45, 0.65, "AQ equity vs 2 opponents")
    
    # Test 99 (medium pair)
    nines = tester.parse_hand("9S 9D")
    result = tester.calculator.calculate_win_probability(nines, [], num_opponents=3)
    tester.assert_equity_range(result['equity'], 0.40, 0.55, "99 equity vs 3 opponents")
    
    # Test KK
    kk = tester.parse_hand("KS KH")
    result = tester.calculator.calculate_win_probability(kk, [], num_opponents=1)
    tester.assert_equity_greater(result['equity'], 0.70, "KK heads-up equity > 70%")
    
    tester.print_summary()
    return tester


def test_weak_preflop_hands():
    """Test weak starting hands"""
    print("\nTesting Weak Pre-Flop Hands...")
    tester = WinProbabilityTester()
    
    # Test 72o (worst hand)
    weak = tester.parse_hand("7S 2D")
    result = tester.calculator.calculate_win_probability(weak, [], num_opponents=2)
    tester.assert_equity_range(result['equity'], 0.20, 0.40, "72o equity vs 2 opponents")
    tester.assert_hand_strength(weak, [], 2, "weak", "72o pre-flop")
    
    # Test 92o
    weak2 = tester.parse_hand("9S 2H")
    result = tester.calculator.calculate_win_probability(weak2, [], num_opponents=1)
    tester.assert_hand_strength(weak2, [], 1, "weak", "92o heads-up")
    
    tester.print_summary()
    return tester


def test_made_hands_postflop():
    """Test made hands on various streets"""
    print("\nTesting Made Hands (Post-Flop)...")
    tester = WinProbabilityTester()
    
    # Trips on flop (best possible made hand at this point)
    trips = tester.parse_hand("KS KD")
    flop_with_trips = tester.parse_hand("KC 5H 3D")
    result = tester.calculator.calculate_win_probability(trips, flop_with_trips, num_opponents=2)
    tester.assert_equity_greater(result['equity'], 0.85, "Trips on flop equity > 85%")
    tester.assert_hand_strength(trips, flop_with_trips, 2, "excellent", "Trips on flop")
    
    # Pair on flop
    pair = tester.parse_hand("QS QH")
    flop_with_pair = tester.parse_hand("2C 3D 4H")
    result = tester.calculator.calculate_win_probability(pair, flop_with_pair, num_opponents=2)
    tester.assert_equity_range(result['equity'], 0.45, 0.70, "Pair on flop equity")
    tester.assert_hand_strength(pair, flop_with_pair, 2, "very good", "Pair on flop")
    
    # Two pair on turn
    two_pair = tester.parse_hand("KS KD")
    turn_with_two_pair = tester.parse_hand("KC 5H 5D 2S")
    result = tester.calculator.calculate_win_probability(two_pair, turn_with_two_pair, num_opponents=1)
    tester.assert_equity_greater(result['equity'], 0.80, "Two pair equity > 80%")
    tester.assert_hand_strength(two_pair, turn_with_two_pair, 1, "excellent", "Two pair on turn")
    
    # Full house on river
    full_house = tester.parse_hand("KS KD")
    river_full_house = tester.parse_hand("KC 5H 5D 5S 2C")
    result = tester.calculator.calculate_win_probability(full_house, river_full_house, num_opponents=1)
    tester.assert_equity_greater(result['equity'], 0.90, "Full house equity > 90%")
    tester.assert_hand_strength(full_house, river_full_house, 1, "excellent", "Full house")
    
    tester.print_summary()
    return tester


def test_drawing_hands():
    """Test drawing hands (flush draws, straight draws, etc)"""
    print("\nTesting Drawing Hands...")
    tester = WinProbabilityTester()
    
    # Flush draw on flop (4 to a flush with overcard)
    flush_draw = tester.parse_hand("AS KS")
    flop_flush_draw = tester.parse_hand("2S 5H 8D")
    result = tester.calculator.calculate_win_probability(flush_draw, flop_flush_draw, num_opponents=1)
    tester.assert_equity_range(result['equity'], 0.50, 0.70, "Flush draw with overcard equity on flop")
    
    # Open-ended straight draw on flop (with overcards)
    oesd = tester.parse_hand("KS QH")
    flop_oesd = tester.parse_hand("JS 10D 5C")
    result = tester.calculator.calculate_win_probability(oesd, flop_oesd, num_opponents=1)
    tester.assert_equity_range(result['equity'], 0.60, 0.75, "OESD with overcards equity on flop")
    
    # Combo draw (flush + straight) on flop
    combo = tester.parse_hand("AS KS")
    flop_combo = tester.parse_hand("QS JD 10C")
    result = tester.calculator.calculate_win_probability(combo, flop_combo, num_opponents=1)
    tester.assert_equity_greater(result['equity'], 0.70, "Combo draw equity > 70%")
    
    # Gutshot on turn (with overcards)
    gutshot = tester.parse_hand("KS QH")
    turn_gutshot = tester.parse_hand("JS 10D 5C 3H")
    result = tester.calculator.calculate_win_probability(gutshot, turn_gutshot, num_opponents=1)
    tester.assert_equity_range(result['equity'], 0.45, 0.60, "Gutshot with overcards equity on turn")
    
    tester.print_summary()
    return tester


def test_high_card_hands():
    """Test high card only hands"""
    print("\nTesting High Card Hands...")
    tester = WinProbabilityTester()
    
    # Ace high on flop (no pair)
    ace_high = tester.parse_hand("AS KH")
    flop_no_pair = tester.parse_hand("2D 3H 4C")
    result = tester.calculator.calculate_win_probability(ace_high, flop_no_pair, num_opponents=1)
    tester.assert_hand_strength(ace_high, flop_no_pair, 1, "fair", "Ace-king high on flop")
    
    # Queen high
    queen_high = tester.parse_hand("QS JD")
    flop = tester.parse_hand("2C 5H 8D")
    result = tester.calculator.calculate_win_probability(queen_high, flop, num_opponents=2)
    tester.assert_hand_strength(queen_high, flop, 2, "weak", "Queen-jack high vs 2 opponents")
    
    tester.print_summary()
    return tester


def test_equity_decreases_with_opponents():
    """Test that equity decreases as number of opponents increases"""
    print("\nTesting Equity vs Different Opponent Counts...")
    tester = WinProbabilityTester()
    
    # Same strong hand, increasing opponents
    pair = tester.parse_hand("AS AD")
    preflop = []
    
    result_1 = tester.calculator.calculate_win_probability(pair, preflop, num_opponents=1)
    result_2 = tester.calculator.calculate_win_probability(pair, preflop, num_opponents=2)
    result_3 = tester.calculator.calculate_win_probability(pair, preflop, num_opponents=3)
    result_4 = tester.calculator.calculate_win_probability(pair, preflop, num_opponents=4)
    
    tester.assert_true(
        result_1['equity'] > result_2['equity'],
        f"Equity decreases with more opponents (1 vs 2): {result_1['equity']:.1%} vs {result_2['equity']:.1%}"
    )
    tester.assert_true(
        result_2['equity'] > result_3['equity'],
        f"Equity decreases with more opponents (2 vs 3): {result_2['equity']:.1%} vs {result_3['equity']:.1%}"
    )
    tester.assert_true(
        result_3['equity'] > result_4['equity'],
        f"Equity decreases with more opponents (3 vs 4): {result_3['equity']:.1%} vs {result_4['equity']:.1%}"
    )
    
    tester.print_summary()
    return tester


def test_equity_improves_with_community_cards():
    """Test that made hands improve relative to the board"""
    print("\nTesting Equity Improvement as Board Develops...")
    tester = WinProbabilityTester()
    
    # Pair pre-flop vs flop with extra pair
    pair = tester.parse_hand("KS KD")
    flop = tester.parse_hand("KC 5H 3D")
    turn = tester.parse_hand("KC 5H 3D 2S")
    river = tester.parse_hand("KC 5H 3D 2S 8H")
    
    result_preflop = tester.calculator.calculate_win_probability(pair, [], num_opponents=1)
    result_flop = tester.calculator.calculate_win_probability(pair, flop, num_opponents=1)
    result_turn = tester.calculator.calculate_win_probability(pair, turn, num_opponents=1)
    result_river = tester.calculator.calculate_win_probability(pair, river, num_opponents=1)
    
    # More equity on flop with trips
    tester.assert_true(
        result_flop['equity'] > result_preflop['equity'],
        "Equity improves when pair hits trips on flop"
    )
    
    # Equity should be very high by river
    tester.assert_equity_greater(result_river['equity'], 0.90, "Three of a kind on river > 90%")
    
    tester.print_summary()
    return tester


def test_specific_hand_matchups():
    """Test calculate_vs_specific_hands with known matchups"""
    print("\nTesting Specific Hand Matchups...")
    tester = WinProbabilityTester()
    
    # AA vs KK heads-up
    aa = tester.parse_hand("AS AH")
    kk = tester.parse_hand("KS KD")
    result = tester.calculator.calculate_vs_specific_hands(aa, [], [kk])
    tester.assert_equity_range(result['equity'], 0.80, 0.90, "AA vs KK heads-up equity")
    
    # AA vs KK + QQ vs 2 opponents
    qq = tester.parse_hand("QS QD")
    result_3way = tester.calculator.calculate_vs_specific_hands(aa, [], [kk, qq])
    tester.assert_equity_greater(result_3way['equity'], 0.50, "AA vs KK+QQ equity > 50%")
    
    # AK vs 72 heads-up
    ak = tester.parse_hand("AS KH")
    seventy_two = tester.parse_hand("7D 2C")
    result = tester.calculator.calculate_vs_specific_hands(ak, [], [seventy_two])
    tester.assert_equity_greater(result['equity'], 0.60, "AK vs 72 equity > 60%")
    
    tester.print_summary()
    return tester


def test_input_validation():
    """Test input validation and error handling"""
    print("\nTesting Input Validation...")
    tester = WinProbabilityTester()
    
    calculator = tester.calculator
    card_a = Card("Spades", "A")
    card_k = Card("Hearts", "K")
    card_q = Card("Diamonds", "Q")
    
    # Test invalid hole card count
    try:
        calculator.calculate_win_probability([card_a], [], 1)
        tester.assert_false(True, "Should fail with 1 hole card")
    except ValueError:
        tester.assert_true(True, "Correctly rejects 1 hole card")
    
    # Test invalid community card count
    try:
        calculator.calculate_win_probability([card_a, card_k], [card_q, card_a], 1)
        tester.assert_false(True, "Should fail with 2 community cards")
    except ValueError:
        tester.assert_true(True, "Correctly rejects 2 community cards")
    
    # Test zero opponents
    try:
        calculator.calculate_win_probability([card_a, card_k], [], 0)
        tester.assert_false(True, "Should fail with 0 opponents")
    except ValueError:
        tester.assert_true(True, "Correctly rejects 0 opponents")
    
    # Test duplicate cards
    try:
        calculator.calculate_win_probability([card_a, card_k], [card_a], 1)
        tester.assert_false(True, "Should fail with duplicate cards")
    except ValueError:
        tester.assert_true(True, "Correctly rejects duplicate cards")
    
    tester.print_summary()
    return tester


def test_community_card_counts():
    """Test that calculator works at all valid community card counts"""
    print("\nTesting All Community Card Counts...")
    tester = WinProbabilityTester()
    
    hand = tester.parse_hand("AS KS")
    
    # Pre-flop (0 cards)
    result_0 = tester.calculator.calculate_win_probability(hand, [], 1)
    tester.assert_true(result_0['equity'] > 0, "Pre-flop calculation works")
    
    # Flop (3 cards)
    flop = tester.parse_hand("2D 5H 8C")
    result_3 = tester.calculator.calculate_win_probability(hand, flop, 1)
    tester.assert_true(result_3['equity'] > 0, "Flop calculation works")
    
    # Turn (4 cards)
    turn = tester.parse_hand("2D 5H 8C 3S")
    result_4 = tester.calculator.calculate_win_probability(hand, turn, 1)
    tester.assert_true(result_4['equity'] > 0, "Turn calculation works")
    
    # River (5 cards)
    river = tester.parse_hand("2D 5H 8C 3S 6H")
    result_5 = tester.calculator.calculate_win_probability(hand, river, 1)
    tester.assert_true(result_5['equity'] > 0, "River calculation works")
    
    tester.print_summary()
    return tester


def test_probabilities_sum_to_one():
    """Test that win + tie + lose = 1.0"""
    print("\nTesting Probability Sum...")
    tester = WinProbabilityTester()
    
    hand = tester.parse_hand("AS KS")
    flop = tester.parse_hand("2D 5H 8C")
    
    result = tester.calculator.calculate_win_probability(hand, flop, 2)
    
    total_prob = result['win_prob'] + result['tie_prob'] + result['lose_prob']
    tester.assert_true(
        abs(total_prob - 1.0) < 0.01,  # Allow small rounding error
        f"Probabilities sum to 1.0 (actual: {total_prob:.4f})"
    )
    
    tester.print_summary()
    return tester


def test_equity_calculation():
    """Test that equity is calculated correctly"""
    print("\nTesting Equity Calculation Formula...")
    tester = WinProbabilityTester()
    
    hand = tester.parse_hand("AS KS")
    flop = tester.parse_hand("2D 5H 8C")
    
    result = tester.calculator.calculate_win_probability(hand, flop, 2)
    
    # Manual calculation: equity = win_prob + (tie_prob / num_players)
    num_players = 3
    expected_equity = result['win_prob'] + (result['tie_prob'] / num_players)
    
    tester.assert_true(
        abs(result['equity'] - expected_equity) < 0.001,
        f"Equity calculation correct (expected: {expected_equity:.4f}, actual: {result['equity']:.4f})"
    )
    
    tester.print_summary()
    return tester


def test_heads_up_higher_equity():
    """Test that heads-up has higher equity than multi-way"""
    print("\nTesting Heads-Up vs Multi-Way Equity...")
    tester = WinProbabilityTester()
    
    hand = tester.parse_hand("AS KS")
    flop = tester.parse_hand("2D 5H 8C")
    
    # Same hand, heads-up vs 3-way
    result_hu = tester.calculator.calculate_win_probability(hand, flop, 1)
    result_3way = tester.calculator.calculate_win_probability(hand, flop, 3)
    
    tester.assert_true(
        result_hu['equity'] > result_3way['equity'],
        f"Heads-up equity ({result_hu['equity']:.1%}) > 3-way equity ({result_3way['equity']:.1%})"
    )
    
    tester.print_summary()
    return tester


if __name__ == "__main__":
    print("="*60)
    print("WIN PROBABILITY TEST SUITE")
    print("="*60)
    
    # Run all tests
    test_premium_preflop_hands()
    test_weak_preflop_hands()
    test_made_hands_postflop()
    test_drawing_hands()
    test_high_card_hands()
    test_equity_decreases_with_opponents()
    test_equity_improves_with_community_cards()
    test_specific_hand_matchups()
    test_input_validation()
    test_community_card_counts()
    test_probabilities_sum_to_one()
    test_equity_calculation()
    test_heads_up_higher_equity()
    
    print("\n" + "="*60)
    print("All test suites completed!")
    print("="*60)
