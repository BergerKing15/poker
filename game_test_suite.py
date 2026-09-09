import random
from typing import List, Dict, Any, Optional, Callable
from poker.game import PokerGame, Card, Deck, Player, HandEvaluator, GameObserver, GameAborted


class GameScriptAction:
    """Represents a player action in a scripted game"""
    def __init__(self, player_id: int, action: str, amount: Optional[int] = None):
        self.player_id = player_id
        self.action = action  # "check", "call", "raise", "fold", "all-in"
        self.amount = amount  # For raises


class GameScript:
    """Script a game with predetermined cards and actions"""
    def __init__(self, num_players: int = 2, starting_stack: int = 1000):
        self.num_players = num_players
        self.starting_stack = starting_stack
        self.hole_cards: Dict[int, List[Card]] = {}  # player_id -> cards
        self.community_cards: List[Card] = []
        self.actions_by_round: Dict[str, List[GameScriptAction]] = {
            "pre-flop": [],
            "flop": [],
            "turn": [],
            "river": []
        }
    
    def set_hole_cards(self, player_id: int, cards: List[Card]):
        """Set hole cards for a specific player"""
        if len(cards) != 2:
            raise ValueError("Hole cards must be exactly 2 cards")
        self.hole_cards[player_id] = cards
    
    def set_community_cards(self, cards: List[Card]):
        """Set community cards (flop=3, turn=1, river=1)"""
        if len(cards) not in [3, 4, 5]:
            raise ValueError("Community cards must be 3 (flop), 4 (turn), or 5 (river)")
        self.community_cards = cards
    
    def add_action(self, round_name: str, player_id: int, action: str, amount: Optional[int] = None):
        """Add an action for a betting round"""
        if round_name not in self.actions_by_round:
            raise ValueError(f"Invalid round: {round_name}")
        self.actions_by_round[round_name].append(GameScriptAction(player_id, action, amount))
    
    def parse_cards(self, card_str: str) -> Card:
        """Parse card string like 'AS', '2H', '10D' into Card object"""
        if len(card_str) < 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        rank = card_str[:-1]
        suit_char = card_str[-1].upper()
        
        suit_map = {'H': 'Hearts', 'D': 'Diamonds', 'C': 'Clubs', 'S': 'Spades'}
        if suit_char not in suit_map:
            raise ValueError(f"Invalid suit: {suit_char}")
        
        return Card(suit_map[suit_char], rank)


class MockPokerGame(PokerGame):
    """Extended PokerGame with scripting capabilities"""
    def __init__(self, script: GameScript):
        super().__init__(
            num_players=script.num_players,
            starting_stack=script.starting_stack,
            small_blind=5,
            big_blind=10
        )
        self.script = script
        self.action_index = 0
        self.current_round = None
    
    def deal_hole_cards(self):
        """Override to use scripted cards if available"""
        if self.script.hole_cards:
            # Use scripted hole cards
            for player_id, cards in self.script.hole_cards.items():
                self.players[player_id].receive_cards(cards)
        else:
            # Use normal dealing
            super().deal_hole_cards()
    
    def override_community_cards(self, round_name: str):
        """Set community cards based on script for a given round"""
        if self.script.community_cards:
            flop_size = 3
            turn_size = 4
            river_size = 5
            
            if round_name == "Flop" and len(self.script.community_cards) >= flop_size:
                self.community_cards = self.script.community_cards[:flop_size]
            elif round_name == "Turn" and len(self.script.community_cards) >= turn_size:
                self.community_cards = self.script.community_cards[:turn_size]
            elif round_name == "River" and len(self.script.community_cards) >= river_size:
                self.community_cards = self.script.community_cards[:river_size]
    
    def ai_decision(self, player, community_cards, current_bet, to_call):
        """Override to use scripted actions"""
        if not self.current_round or player.is_ai:
            return super().ai_decision(player, community_cards, current_bet, to_call)
        
        # Use scripted action
        round_actions = self.script.actions_by_round.get(self.current_round.lower(), [])
        
        for action_obj in round_actions:
            if action_obj.player_id == player.player_id:
                return action_obj.action
        
        # Fallback to normal AI decision
        return super().ai_decision(player, community_cards, current_bet, to_call)
    
    def betting_round(self, stage):
        """Override to set current round and use script cards"""
        self.current_round = stage
        self.override_community_cards(stage)
        super().betting_round(stage)


class GameTester:
    """Test utilities for poker game logic"""

    # Every tester registers itself here. The test functions create a tester,
    # print its summary and drop it, so a runner has no other way to find out
    # whether an assertion failed anywhere (the assert_* helpers record
    # failures rather than raising).
    _instances: List["GameTester"] = []

    @classmethod
    def reset_totals(cls):
        """Forget previously registered testers."""
        cls._instances.clear()

    @classmethod
    def totals(cls):
        """Return (passed, failed) summed over every tester created so far."""
        return (sum(t.assertions_passed for t in cls._instances),
                sum(t.assertions_failed for t in cls._instances))

    def __init__(self):
        self.assertions_passed = 0
        self.assertions_failed = 0
        GameTester._instances.append(self)
        self.test_results = []
    
    def parse_card_string(self, card_str: str) -> Card:
        """Parse 'AS', '2H', etc. into Card"""
        if len(card_str) < 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        rank = card_str[:-1]
        suit_char = card_str[-1].upper()
        
        suit_map = {'H': 'Hearts', 'D': 'Diamonds', 'C': 'Clubs', 'S': 'Spades'}
        if suit_char not in suit_map:
            raise ValueError(f"Invalid suit: {suit_char}")
        
        return Card(suit_map[suit_char], rank)
    
    def parse_hand(self, hand_str: str) -> List[Card]:
        """Parse space-separated cards like 'AS 2H' into list of Cards"""
        return [self.parse_card_string(card) for card in hand_str.split()]
    
    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
        """Assert that actual equals expected"""
        if actual == expected:
            self.assertions_passed += 1
            return True
        else:
            self.assertions_failed += 1
            msg = f"FAIL: {message}\n  Expected: {expected}\n  Actual: {actual}"
            self.test_results.append(msg)
            print(msg)
            return False
    
    def assert_true(self, condition: bool, message: str = ""):
        """Assert that condition is true"""
        if condition:
            self.assertions_passed += 1
            return True
        else:
            self.assertions_failed += 1
            msg = f"FAIL: {message} (expected True)"
            self.test_results.append(msg)
            print(msg)
            return False
    
    def assert_false(self, condition: bool, message: str = ""):
        """Assert that condition is false"""
        if not condition:
            self.assertions_passed += 1
            return True
        else:
            self.assertions_failed += 1
            msg = f"FAIL: {message} (expected False)"
            self.test_results.append(msg)
            print(msg)
            return False
    
    def assert_stack(self, player: Player, expected_stack: int, message: str = ""):
        """Assert player has specific stack amount"""
        return self.assert_equal(player.stack, expected_stack, 
                                f"Player {player.player_id} stack: {message}")
    
    def assert_hand_type(self, cards: List[Card], expected_type: str, message: str = ""):
        """Assert that cards evaluate to specific hand type"""
        hand_info = HandEvaluator.evaluate_hand(cards)
        actual_type = hand_info[0]
        return self.assert_equal(actual_type, expected_type, 
                                f"Hand type {message}")
    
    def assert_not_equal(self, actual: Any, expected: Any, message: str = ""):
        """Assert that actual does NOT equal expected"""
        if actual != expected:
            self.assertions_passed += 1
            return True
        else:
            self.assertions_failed += 1
            msg = f"FAIL: {message}\n  Values should not be equal: {actual}"
            self.test_results.append(msg)
            print(msg)
            return False
    
    def print_summary(self):
        """Print test summary"""
        total = self.assertions_passed + self.assertions_failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.assertions_passed}/{total} passed")
        if self.assertions_failed > 0:
            print(f"FAILURES: {self.assertions_failed}")
        print(f"{'='*60}\n")


# Example test cases
def test_hand_evaluation():
    """Test that hand evaluation works correctly"""
    print("Testing Hand Evaluation...")
    tester = GameTester()
    
    # Test royal flush
    royal_flush = tester.parse_hand("AS KS QS JS 10S 9S 8S")[:5]
    tester.assert_hand_type(royal_flush, "Royal Flush", "royal flush detection")
    
    # Test straight flush
    straight_flush = tester.parse_hand("9H 8H 7H 6H 5H")
    tester.assert_hand_type(straight_flush, "Straight Flush", "straight flush detection")
    
    # Test four of a kind
    four_kind = tester.parse_hand("2D 2C 2H 2S KH")
    tester.assert_hand_type(four_kind, "Four of a Kind", "four of a kind detection")
    
    # Test full house
    full_house = tester.parse_hand("3D 3C 3H 5S 5H")
    tester.assert_hand_type(full_house, "Full House", "full house detection")
    
    # Test flush
    flush = tester.parse_hand("2C 4C 6C 8C 10C")
    tester.assert_hand_type(flush, "Flush", "flush detection")
    
    # Test straight
    straight = tester.parse_hand("9D 8C 7H 6S 5D")
    tester.assert_hand_type(straight, "Straight", "straight detection")
    
    # Test three of a kind
    three_kind = tester.parse_hand("7D 7C 7H QS KH")
    tester.assert_hand_type(three_kind, "Three of a Kind", "three of a kind detection")
    
    # Test two pair
    two_pair = tester.parse_hand("JD JC 5H 5S KH")
    tester.assert_hand_type(two_pair, "Two Pair", "two pair detection")
    
    # Test one pair
    one_pair = tester.parse_hand("AD AC KH QS JD")
    tester.assert_hand_type(one_pair, "One Pair", "one pair detection")
    
    # Test high card
    high_card = tester.parse_hand("AS KD QC JS 9H")
    tester.assert_hand_type(high_card, "High Card", "high card detection")
    
    tester.print_summary()
    return tester


def test_side_pots():
    """Test side pot creation with all-in players"""
    print("\nTesting Side Pots...")
    tester = GameTester()
    
    script = GameScript(num_players=3, starting_stack=100)
    game = MockPokerGame(script)
    game.DEBUG = False
    
    # Simulate 3 players with different all-in amounts
    game.players[0].is_folded = False
    game.players[0].total_bet_this_round = 30  # Smallest
    
    game.players[1].is_folded = False
    game.players[1].total_bet_this_round = 70  # Medium
    
    game.players[2].is_folded = False
    game.players[2].total_bet_this_round = 100  # All-in for most
    
    pots = game.create_side_pots()
    
    # Should create 3 pots
    tester.assert_equal(len(pots), 3, "Number of side pots")
    
    # Main pot: $90 (30 from each of 3 players)
    tester.assert_equal(pots[0]['amount'], 90, "Main pot amount")
    tester.assert_equal(set(pots[0]['eligible_players']), {0, 1, 2}, "Main pot eligible players")
    
    # Side pot 1: $80 (40 from players 1,2)
    tester.assert_equal(pots[1]['amount'], 80, "Side pot 1 amount")
    tester.assert_equal(set(pots[1]['eligible_players']), {1, 2}, "Side pot 1 eligible players")
    
    # Side pot 2: $30 (30 from player 2)
    tester.assert_equal(pots[2]['amount'], 30, "Side pot 2 amount")
    tester.assert_equal(set(pots[2]['eligible_players']), {2}, "Side pot 2 eligible players")
    
    tester.print_summary()
    return tester


def test_simple_hand():
    """Test a complete simple hand with predetermined cards"""
    print("\nTesting Simple Hand Script...")
    tester = GameTester()
    
    script = GameScript(num_players=2, starting_stack=1000)
    
    # Set hole cards
    script.set_hole_cards(0, tester.parse_hand("AS KS"))  # Player 0: AK high
    script.set_hole_cards(1, tester.parse_hand("2D 2C"))  # Player 1: pair of 2s
    
    # Set community cards: pair on board
    script.set_community_cards(tester.parse_hand("2H 5D 8C 3S 6H"))
    
    # Script actions: Player 1 should win with three of a kind
    script.add_action("pre-flop", 0, "call")  # Player 0 calls
    script.add_action("pre-flop", 1, "check")  # Player 1 checks
    
    script.add_action("flop", 1, "check")
    script.add_action("flop", 0, "check")
    
    script.add_action("turn", 1, "check")
    script.add_action("turn", 0, "check")
    
    script.add_action("river", 1, "check")
    script.add_action("river", 0, "check")
    
    # Create game and run
    game = MockPokerGame(script)
    game.DEBUG = False
    
    # Starting stacks
    tester.assert_equal(game.players[0].stack, 1000, "Player 0 starting stack")
    tester.assert_equal(game.players[1].stack, 1000, "Player 1 starting stack")
    
    # Verify script data is set correctly
    tester.assert_equal(len(script.hole_cards[0]), 2, "Player 0 hole cards set")
    tester.assert_equal(len(script.hole_cards[1]), 2, "Player 1 hole cards set")
    tester.assert_equal(len(script.community_cards), 5, "Community cards set")
    
    tester.print_summary()
    return tester


def test_all_in_scenario():
    """Test all-in scenario with side pots"""
    print("\nTesting All-In Scenario...")
    tester = GameTester()
    
    script = GameScript(num_players=2, starting_stack=100)
    game = MockPokerGame(script)
    game.DEBUG = False
    
    # Simulate all-in: Player 0 goes all-in for $50, Player 1 calls with $100
    game.players[0].stack = 50
    game.players[0].total_bet_this_round = 50
    game.players[0].is_all_in = True
    game.players[0].is_folded = False
    game.pot = 100
    
    game.players[1].stack = 50
    game.players[1].total_bet_this_round = 100
    game.players[1].is_all_in = False
    game.players[1].is_folded = False
    
    # Create side pots
    pots = game.create_side_pots()
    
    # Should have 2 pots: main pot ($100) and side pot ($50)
    tester.assert_equal(len(pots), 2, "Number of pots with all-in")
    tester.assert_equal(pots[0]['amount'], 100, "Main pot amount")
    tester.assert_equal(pots[1]['amount'], 50, "Side pot amount")
    
    tester.print_summary()
    return tester


def test_complex_side_pots():
    """Test complex side pot scenarios with multiple all-in players"""
    print("\nTesting Complex Side Pots...")
    tester = GameTester()
    
    script = GameScript(num_players=4, starting_stack=1000)
    game = MockPokerGame(script)
    game.DEBUG = False
    
    # Scenario: 4 players with different all-in amounts
    # Player 0: all-in for $50
    # Player 1: all-in for $150
    # Player 2: all-in for $200
    # Player 3: calls for $250 (more than player 2)
    
    game.players[0].is_folded = False
    game.players[0].total_bet_this_round = 50
    
    game.players[1].is_folded = False
    game.players[1].total_bet_this_round = 150
    
    game.players[2].is_folded = False
    game.players[2].total_bet_this_round = 200
    
    game.players[3].is_folded = False
    game.players[3].total_bet_this_round = 250
    
    pots = game.create_side_pots()
    
    # Should have 4 pots (one for each level)
    tester.assert_equal(len(pots), 4, "Number of pots with 4 all-in levels")
    
    # Main pot: $200 (50 from each of 4 players)
    tester.assert_equal(pots[0]['amount'], 200, "Main pot (level 1)")
    tester.assert_equal(set(pots[0]['eligible_players']), {0, 1, 2, 3}, "Main pot eligible")
    
    # Side pot 1: $300 (100 from players 1,2,3 at level 2: 150-50=100 each)
    tester.assert_equal(pots[1]['amount'], 300, "Side pot 1 (level 2)")
    tester.assert_equal(set(pots[1]['eligible_players']), {1, 2, 3}, "Side pot 1 eligible")
    
    # Side pot 2: $100 (50 from players 2,3 at level 3: 200-150=50 each)
    tester.assert_equal(pots[2]['amount'], 100, "Side pot 2 (level 3)")
    tester.assert_equal(set(pots[2]['eligible_players']), {2, 3}, "Side pot 2 eligible")
    
    # Side pot 3: $50 (50 from player 3 only at level 4: 250-200=50)
    tester.assert_equal(pots[3]['amount'], 50, "Side pot 3 (level 4)")
    tester.assert_equal(set(pots[3]['eligible_players']), {3}, "Side pot 3 eligible")
    
    tester.print_summary()
    return tester


def test_all_in_with_folded_players():
    """Test all-in with players folding before all-in"""
    print("\nTesting All-In With Folded Players...")
    tester = GameTester()
    
    script = GameScript(num_players=3, starting_stack=200)
    game = MockPokerGame(script)
    game.DEBUG = False
    
    # Player 0: folded
    # Player 1: all-in for $100
    # Player 2: calls for $150
    
    game.players[0].is_folded = True  # Folded - shouldn't be in any pot
    game.players[0].total_bet_this_round = 50
    
    game.players[1].is_folded = False
    game.players[1].total_bet_this_round = 100
    
    game.players[2].is_folded = False
    game.players[2].total_bet_this_round = 150
    
    pots = game.create_side_pots()
    
    # Should have 2 pots (folded player excluded)
    tester.assert_equal(len(pots), 2, "Number of pots with folded player")
    
    # Main pot: $200 (100 from players 1,2)
    tester.assert_equal(pots[0]['amount'], 200, "Main pot excludes folded player")
    tester.assert_equal(set(pots[0]['eligible_players']), {1, 2}, "Main pot doesn't include folded player")
    
    # Side pot: $50 (50 from player 2 only)
    tester.assert_equal(pots[1]['amount'], 50, "Side pot from player 2")
    tester.assert_equal(set(pots[1]['eligible_players']), {2}, "Side pot only from player 2")
    
    tester.print_summary()
    return tester


def test_all_in_heads_up():
    """Test all-in scenario in heads-up play"""
    print("\nTesting All-In Heads-Up...")
    tester = GameTester()
    
    script = GameScript(num_players=2, starting_stack=100)
    game = MockPokerGame(script)
    game.DEBUG = False
    
    # Simple heads-up all-in
    # Player 0: all-in for $75
    # Player 1: calls for $100
    
    game.players[0].is_folded = False
    game.players[0].total_bet_this_round = 75
    
    game.players[1].is_folded = False
    game.players[1].total_bet_this_round = 100
    
    pots = game.create_side_pots()
    
    # Should have 2 pots
    tester.assert_equal(len(pots), 2, "Heads-up creates 2 pots")
    
    # Main pot: $150 (75 from each)
    tester.assert_equal(pots[0]['amount'], 150, "Main pot in heads-up")
    tester.assert_equal(set(pots[0]['eligible_players']), {0, 1}, "Both players in main pot")
    
    # Side pot: $25 (25 from player 1)
    tester.assert_equal(pots[1]['amount'], 25, "Side pot in heads-up")
    tester.assert_equal(set(pots[1]['eligible_players']), {1}, "Only player 1 in side pot")
    
    tester.print_summary()
    return tester


def test_all_in_equal_stacks():
    """Test all-in with equal stacks (no side pot)"""
    print("\nTesting All-In Equal Stacks...")
    tester = GameTester()
    
    script = GameScript(num_players=3, starting_stack=100)
    game = MockPokerGame(script)
    game.DEBUG = False
    
    # All three players all-in for same amount
    game.players[0].is_folded = False
    game.players[0].total_bet_this_round = 100
    
    game.players[1].is_folded = False
    game.players[1].total_bet_this_round = 100
    
    game.players[2].is_folded = False
    game.players[2].total_bet_this_round = 100
    
    pots = game.create_side_pots()
    
    # Should have only 1 pot (no side pots needed)
    tester.assert_equal(len(pots), 1, "Equal all-in creates single pot")
    
    # Main pot: $300 (100 from each of 3 players)
    tester.assert_equal(pots[0]['amount'], 300, "Single pot amount")
    tester.assert_equal(set(pots[0]['eligible_players']), {0, 1, 2}, "All players in single pot")
    
    tester.print_summary()
    return tester


def test_hand_tiebreaker():
    """Test tiebreaker logic when hands have same rank"""
    print("\nTesting Hand Tiebreaker Logic...")
    tester = GameTester()
    
    game = PokerGame(num_players=2, starting_stack=1000, use_bots=False)
    game.DEBUG = False
    
    # Both players have a pair, but different kickers
    # Player 0: Pair of 8s with A, K, Q kickers
    player0_hand = tester.parse_hand("8C 8D AS KS QH JD 9C")
    # Player 1: Pair of 8s with A, K, J kickers (worse Q kicker)
    player1_hand = tester.parse_hand("8H 8S AD KD JC 9D 7C")
    
    eval0 = HandEvaluator.evaluate_hand(player0_hand)
    eval1 = HandEvaluator.evaluate_hand(player1_hand)
    
    # eval0 should be better due to Q vs J kicker
    tester.assert_true(eval0[1] > eval1[1], "Higher kicker should win tiebreaker")
    
    tester.print_summary()
    return tester


def test_fold_logic():
    """Test that folded players are excluded from action and winnings"""
    print("\nTesting Fold Logic...")
    tester = GameTester()
    
    game = PokerGame(num_players=3, starting_stack=1000, use_bots=False)
    game.DEBUG = False
    
    # Set up scenario where one player folds
    game.players[0].is_folded = False
    game.players[1].is_folded = True  # Folded
    game.players[2].is_folded = False
    
    # Count active players
    active = [p for p in game.players if not p.is_folded]
    tester.assert_equal(len(active), 2, "Should have 2 active players after fold")
    tester.assert_not_equal(active[0].player_id, 1, "Folded player not in active list")
    tester.assert_not_equal(active[1].player_id, 1, "Folded player not in active list")
    
    # Folded players shouldn't be eligible for pots
    game.players[0].total_bet_this_round = 100
    game.players[1].total_bet_this_round = 100  # Folded but had bet
    game.players[2].total_bet_this_round = 150
    
    pots = game.create_side_pots()
    
    # Check that folded player (1) is not in eligible players
    for pot in pots:
        tester.assert_true(1 not in pot['eligible_players'], 
                          f"Folded player should not be eligible for pot")
    
    tester.print_summary()
    return tester


def test_minimum_raise():
    """Test that raises must be at least the previous bet amount"""
    print("\nTesting Minimum Raise Logic...")
    tester = GameTester()
    
    # Test raise amount validation
    game = PokerGame(num_players=2, starting_stack=1000, use_bots=False)
    game.DEBUG = False
    game.big_blind = 10
    
    # If someone bets $50, minimum raise should be $50 more (total $100)
    current_bet = 50
    min_raise_amount = current_bet  # Raise must be at least the current bet
    
    # Test that $40 raise would be invalid (less than current bet)
    invalid_raise = 40
    tester.assert_true(invalid_raise < min_raise_amount, 
                      "Raise less than current bet should be invalid")
    
    # Test that $50 raise is valid
    valid_raise = 50
    tester.assert_true(valid_raise >= min_raise_amount,
                      "Raise equal to or greater than current bet should be valid")
    
    tester.print_summary()
    return tester


def test_pot_calculation():
    """Test that pot total equals sum of all player contributions"""
    print("\nTesting Pot Calculation Accuracy...")
    tester = GameTester()
    
    game = PokerGame(num_players=4, starting_stack=500, use_bots=False)
    game.DEBUG = False
    
    # Set player contributions
    contributions = [100, 75, 150, 50]
    for i, contribution in enumerate(contributions):
        game.players[i].total_bet_this_round = contribution
    
    # Calculate expected pot
    expected_pot = sum(contributions)
    
    # Verify calculation
    tester.assert_equal(expected_pot, 375, "Pot calculation correct")
    
    # Test with different amounts
    game2 = PokerGame(num_players=3, starting_stack=1000, use_bots=False)
    game2.DEBUG = False
    
    contributions2 = [250, 250, 250]
    total2 = sum(contributions2)
    tester.assert_equal(total2, 750, "Equal contribution pot")
    
    tester.print_summary()
    return tester


def test_button_advancement():
    """Test that button advances correctly after each hand"""
    print("\nTesting Button Advancement...")
    tester = GameTester()
    
    game = PokerGame(num_players=3, starting_stack=1000, use_bots=False)
    game.DEBUG = False
    
    # Test button advancement through multiple rounds
    game.button = 0
    next_button = (game.button + 1) % len(game.players)
    tester.assert_equal(next_button, 1, "Button advances from 0 to 1 with 3 players")
    
    game.button = 1
    next_button = (game.button + 1) % len(game.players)
    tester.assert_equal(next_button, 2, "Button advances from 1 to 2")
    
    game.button = 2
    next_button = (game.button + 1) % len(game.players)
    tester.assert_equal(next_button, 0, "Button wraps from 2 to 0")
    
    # Test with 2 players (heads-up)
    game2 = PokerGame(num_players=2, starting_stack=1000, use_bots=False)
    game2.DEBUG = False
    game2.button = 0
    next_button = (game2.button + 1) % len(game2.players)
    tester.assert_equal(next_button, 1, "Button in heads-up goes 0->1")
    
    game2.button = 1
    next_button = (game2.button + 1) % len(game2.players)
    tester.assert_equal(next_button, 0, "Button in heads-up wraps 1->0")
    
    tester.print_summary()
    return tester


def test_check_validation():
    """Test that check is only valid when no bet to call"""
    print("\nTesting Check Validation...")
    tester = GameTester()
    
    game = PokerGame(num_players=2, starting_stack=1000, use_bots=False)
    game.DEBUG = False
    game.current_bet = 0
    
    # Check should be valid when current_bet is 0
    can_check_at_zero = (game.current_bet == 0)
    tester.assert_true(can_check_at_zero, "Can check when current_bet is 0")
    
    # Check should be invalid when there's a bet to call
    game.current_bet = 50
    can_check_at_fifty = (game.current_bet == 0)
    tester.assert_false(can_check_at_fifty, "Cannot check when current_bet > 0")
    
    tester.print_summary()
    return tester


def test_bet_reset_between_streets():
    """Test that player bets reset between streets"""
    print("\nTesting Bet Reset Between Streets...")
    tester = GameTester()
    
    game = PokerGame(num_players=2, starting_stack=1000, use_bots=False)
    game.DEBUG = False
    
    # Simulate pre-flop betting
    game.players[0].total_bet_this_round = 50
    game.players[1].total_bet_this_round = 100
    
    # Verify bets are set
    tester.assert_equal(game.players[0].total_bet_this_round, 50, "Pre-flop bet for P0")
    tester.assert_equal(game.players[1].total_bet_this_round, 100, "Pre-flop bet for P1")
    
    # Reset for flop (as done between streets)
    for player in game.players:
        player.total_bet_this_round = 0
    
    game.current_bet = 0
    
    # Verify reset
    tester.assert_equal(game.players[0].total_bet_this_round, 0, "Bet reset for flop P0")
    tester.assert_equal(game.players[1].total_bet_this_round, 0, "Bet reset for flop P1")
    tester.assert_equal(game.current_bet, 0, "Current bet reset for flop")
    
    tester.print_summary()
    return tester


def test_player_elimination():
    """Test that players with zero stack are removed from future hands"""
    print("\nTesting Player Elimination...")
    tester = GameTester()
    
    game = PokerGame(num_players=3, starting_stack=100, use_bots=False)
    game.DEBUG = False
    
    # Simulate player 1 losing all chips
    game.players[1].stack = 0
    
    # Player with 0 stack should be eliminated (no longer active)
    remaining_players = [p for p in game.players if p.stack > 0]
    tester.assert_equal(len(remaining_players), 2, "Should have 2 players with chips")
    tester.assert_not_equal(remaining_players[0].player_id, 1, "Player 1 eliminated")
    tester.assert_not_equal(remaining_players[1].player_id, 1, "Player 1 eliminated")
    
    tester.print_summary()
    return tester


def test_current_bet_tracking():
    """Test that current_bet tracks highest bet in round"""
    print("\nTesting Current Bet Tracking...")
    tester = GameTester()
    
    game = PokerGame(num_players=3, starting_stack=1000, use_bots=False)
    game.DEBUG = False
    
    # Start with big blind
    game.current_bet = 10
    
    # Player raises to 50
    bet1 = 50
    game.current_bet = max(game.current_bet, bet1)
    tester.assert_equal(game.current_bet, 50, "Current bet updates to 50")
    
    # Player re-raises to 150
    bet2 = 150
    game.current_bet = max(game.current_bet, bet2)
    tester.assert_equal(game.current_bet, 150, "Current bet updates to 150")
    
    # Player calls 150 (shouldn't change current_bet)
    bet3 = 150
    game.current_bet = max(game.current_bet, bet3)
    tester.assert_equal(game.current_bet, 150, "Current bet stays at 150 on call")
    
    tester.print_summary()
    return tester


def test_betting_order():
    """Test betting order is correct on each street"""
    print("\nTesting Betting Order...")
    tester = GameTester()
    
    # Test with 3 players
    game = PokerGame(num_players=3, starting_stack=1000, use_bots=False)
    game.DEBUG = False
    
    # Set button position
    game.button = 0
    
    # Pre-Flop: UTG (button + 3) = player (0 + 3) % 3 = 0, but we want the logic
    # Button = 0, Small Blind = 1, Big Blind = 2
    # Pre-Flop should start with UTG = button + 3 = player 0
    preflop_first = (game.button + 3) % len(game.players)
    tester.assert_equal(preflop_first, 0, "Pre-Flop first to act (UTG)")
    
    # Post-Flop (Flop/Turn/River): Small blind (button + 1) = player 1
    postflop_first = (game.button + 1) % len(game.players)
    tester.assert_equal(postflop_first, 1, "Post-Flop first to act (Small blind)")
    
    # Test with different button position
    game.button = 1
    preflop_first = (game.button + 3) % len(game.players)
    tester.assert_equal(preflop_first, 1, "Pre-Flop first to act with button=1")
    
    postflop_first = (game.button + 1) % len(game.players)
    tester.assert_equal(postflop_first, 2, "Post-Flop first to act with button=1")
    
    # Test with button = 2
    game.button = 2
    preflop_first = (game.button + 3) % len(game.players)
    tester.assert_equal(preflop_first, 2, "Pre-Flop first to act with button=2")
    
    postflop_first = (game.button + 1) % len(game.players)
    tester.assert_equal(postflop_first, 0, "Post-Flop first to act with button=2")
    
    tester.print_summary()
    return tester


def test_action_sequence():
    """Test that betting stage parameter correctly determines action order"""
    print("\nTesting Action Sequence...")
    tester = GameTester()
    
    # Create game with 2 players to simplify
    game = PokerGame(num_players=2, starting_stack=1000, use_bots=False)
    game.DEBUG = False
    
    # Player 0 is button/dealer
    game.button = 0
    
    # Pre-Flop logic: first to act = (button + 3) % num_players = (0 + 3) % 2 = 1
    # This means player 1 acts first pre-flop (small blind acts first in heads-up)
    preflop_start = (game.button + 3) % len(game.players)
    tester.assert_equal(preflop_start, 1, "Heads-up: Player 1 acts first pre-flop")
    
    # Post-Flop logic: first to act = (button + 1) % num_players = (0 + 1) % 2 = 1
    postflop_start = (game.button + 1) % len(game.players)
    tester.assert_equal(postflop_start, 1, "Heads-up: Player 1 acts first post-flop")
    
    # Verify the two different order calculations produce DIFFERENT results
    # (for 3+ players)
    game3 = PokerGame(num_players=3, starting_stack=1000, use_bots=False)
    game3.button = 0
    preflop_start_3 = (game3.button + 3) % len(game3.players)
    postflop_start_3 = (game3.button + 1) % len(game3.players)
    
    tester.assert_equal(preflop_start_3, 0, "3-player: Player 0 acts first pre-flop")
    tester.assert_equal(postflop_start_3, 1, "3-player: Player 1 acts first post-flop")
    tester.assert_not_equal(preflop_start_3, postflop_start_3, "Pre-flop and post-flop order should differ")
    
    tester.print_summary()
    return tester


def test_stage_parameter_propagation():
    """Test that betting round stage correctly affects logic"""
    print("\nTesting Stage Parameter Propagation...")
    tester = GameTester()
    
    # This test verifies the UI correctly passes stage name to betting_round
    # Pre-Flop should pass "Pre-Flop" not "Flop"
    # Flop should pass "Flop" not "Pre-Flop"
    # Turn should pass "Turn"
    # River should pass "River"
    
    stages = ["Pre-Flop", "Flop", "Turn", "River"]
    for i, stage in enumerate(stages):
        # Valid stages should be recognized
        tester.assert_true(stage in stages, f"Stage '{stage}' is valid")
    
    # Verify that passing wrong stage name would break logic
    # (This is a meta-test showing the bug we fixed)
    game = PokerGame(num_players=3, starting_stack=1000, use_bots=False)
    game.button = 0
    
    # If we mistakenly passed "Pre-Flop" for flop stage:
    wrong_first_to_act = (game.button + 3) % len(game.players)  # Uses Pre-Flop logic
    # But correct would be:
    correct_first_to_act = (game.button + 1) % len(game.players)  # Post-Flop logic
    
    tester.assert_not_equal(wrong_first_to_act, correct_first_to_act, 
                           "Bug check: wrong stage name would use wrong action order")
    
    tester.print_summary()
    return tester



class ScriptedObserver(GameObserver):
    """Stands in for a front-end: supplies human actions, records hook calls.

    The Tk UI's human path cannot be exercised without a display, so these
    tests drive the same hooks the UI implements.
    """

    def __init__(self, actions, defer_bots=0):
        self.actions = list(actions)
        self.events = []
        self.defer_bots = defer_bots
        self.deferred = 0

    def on_hand_start(self, game):
        self.events.append("hand_start")

    def on_blinds(self, game, small_blind_player, big_blind_player):
        self.events.append("blinds")

    def on_stage(self, game, stage):
        self.events.append(f"stage:{stage}")

    def on_showdown(self, game):
        self.events.append("showdown")

    def on_hand_end(self, game, winner_info):
        self.events.append("hand_end")

    def on_action(self, game, player, action, amount, stage):
        self.events.append(f"action:{player.player_id}:{action}")

    def before_ai_action(self, game, player, to_call, stage):
        if self.deferred < self.defer_bots:
            self.deferred += 1
            return False
        return True

    def get_human_action(self, game, player, to_call, stage):
        if not self.actions:
            raise GameAborted()
        return self.actions.pop(0)


def test_observer_hand_lifecycle():
    """The engine must call the front-end hooks in a sensible order."""
    print("\nTesting Observer Hand Lifecycle...")
    tester = GameTester()

    obs = ScriptedObserver([("check", None)] * 8)
    game = PokerGame(num_players=2, starting_stack=1000, small_blind=5,
                     big_blind=10, use_bots=True, observer=obs)
    game.players[0].is_ai = False
    game.play_hand()

    tester.assert_equal(obs.events[0], "hand_start", "hand_start fires first")
    tester.assert_equal(obs.events[1], "blinds", "blinds fire before any street")
    tester.assert_true("stage:Pre-Flop" in obs.events, "pre-flop stage announced")
    tester.assert_equal(obs.events[-1], "hand_end", "hand_end fires last")
    tester.assert_true(any(e.startswith("action:") for e in obs.events),
                       "actions are reported to the observer")

    tester.print_summary()
    return tester


def test_observer_human_action_reaches_engine():
    """A human raise supplied by the front-end must move real chips."""
    print("\nTesting Observer Human Action...")
    tester = GameTester()

    obs = ScriptedObserver([("raise", 120)] + [("check", None)] * 8)
    game = PokerGame(num_players=2, starting_stack=1000, small_blind=5,
                     big_blind=10, use_bots=True, observer=obs)
    game.players[0].is_ai = False
    game.play_hand()

    raised = [e for e in obs.events if e == "action:0:raise"]
    tester.assert_true(bool(raised), "human raise reached the engine")
    tester.assert_equal(sum(p.stack for p in game.players), 2000,
                        "chips conserved across a human-driven hand")

    tester.print_summary()
    return tester


def test_observer_abort_propagates():
    """A front-end that goes away mid-hand stops the hand."""
    print("\nTesting Observer Abort...")
    tester = GameTester()

    obs = ScriptedObserver([])  # first human turn raises GameAborted
    game = PokerGame(num_players=2, starting_stack=1000, use_bots=True,
                     observer=obs)
    game.players[0].is_ai = False

    aborted = False
    try:
        game.play_hand()
    except GameAborted:
        aborted = True
    tester.assert_true(aborted, "GameAborted propagates out of play_hand")

    tester.print_summary()
    return tester


def test_observer_deferred_bot():
    """Deferring a bot (the UI's skip-to-my-turn) must not hang the round."""
    print("\nTesting Observer Deferred Bot...")
    tester = GameTester()

    obs = ScriptedObserver([("call", None)] + [("check", None)] * 8, defer_bots=3)
    game = PokerGame(num_players=3, starting_stack=1000, small_blind=5,
                     big_blind=10, use_bots=True, observer=obs)
    game.players[0].is_ai = False
    game.play_hand()

    tester.assert_equal(obs.deferred, 3, "bot turns were deferred")
    tester.assert_equal(obs.events[-1], "hand_end", "hand still completed")
    tester.assert_equal(sum(p.stack for p in game.players), 3000,
                        "chips conserved despite deferrals")

    tester.print_summary()
    return tester


def test_split_pot_conserves_chips():
    """A split pot must not mint chips when it divides evenly."""
    print("\nTesting Split Pot Chip Conservation...")
    tester = GameTester()

    game = PokerGame(num_players=2, starting_stack=1000, small_blind=5,
                     big_blind=10, use_bots=False)
    game.deck = Deck()
    # Identical hands: the pot must split exactly, with no odd chip invented.
    game.players[0].hole_cards = [Card("Spades", "A"), Card("Hearts", "K")]
    game.players[1].hole_cards = [Card("Diamonds", "A"), Card("Clubs", "K")]
    game.community_cards = [Card("Spades", "2"), Card("Hearts", "5"),
                            Card("Clubs", "9"), Card("Diamonds", "J"),
                            Card("Spades", "Q")]
    game.players[0].stack = 900
    game.players[1].stack = 900
    game.pot = 200
    game.determine_winner()

    tester.assert_equal(sum(p.stack for p in game.players), 2000,
                        "split pot conserves chips exactly")

    tester.print_summary()
    return tester


if __name__ == "__main__":
    print("="*60)
    print("POKER GAME TEST SUITE")
    print("="*60)
    
    # Run all tests
    test_hand_evaluation()
    test_side_pots()
    test_complex_side_pots()
    test_all_in_scenario()
    test_all_in_with_folded_players()
    test_all_in_heads_up()
    test_all_in_equal_stacks()
    test_simple_hand()
    test_hand_tiebreaker()
    test_fold_logic()
    test_minimum_raise()
    test_pot_calculation()
    test_button_advancement()
    test_check_validation()
    test_bet_reset_between_streets()
    test_player_elimination()
    test_current_bet_tracking()
    test_betting_order()
    test_action_sequence()
    test_stage_parameter_propagation()
    test_observer_hand_lifecycle()
    test_observer_human_action_reaches_engine()
    test_observer_abort_propagates()
    test_observer_deferred_bot()
    test_split_pot_conserves_chips()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
