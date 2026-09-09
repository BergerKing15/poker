# Poker Game Testing Guide

This guide explains how to use the game testing framework to script games and verify backend logic.

## Quick Start

### Run All Tests
```bash
python all_tests.py
```

This runs all 3 test suites:
- **Game Logic Tests** (92 assertions) - Core poker mechanics
- **Win Probability Tests** - Equity calculations
- **Bot AI Tests** - AI decision making

### Run Individual Tests
```bash
python game_test_suite.py
python win_probability_test_suite.py
python test_bot_ai.py
```

## Overview

The testing framework provides:
- **GameScript**: Script games with predetermined cards and actions
- **MockPokerGame**: Extended game that uses scripted cards/actions
- **GameTester**: Assertion utilities for verifying results

## Basic Usage

### 1. Create a Game Script

```python
from game_test_suite import GameScript, MockPokerGame, GameTester

# Initialize script for 2 players with $1000 each
script = GameScript(num_players=2, starting_stack=1000)

# Set hole cards using card strings (Rank + Suit: AS, 2H, 10D, KS, etc.)
tester = GameTester()
script.set_hole_cards(0, tester.parse_hand("AS KS"))  # Player 0: Ace-King of spades
script.set_hole_cards(1, tester.parse_hand("2D 2C"))  # Player 1: Pair of 2s

# Set community cards (3, 4, or 5 cards)
script.set_community_cards(tester.parse_hand("2H 5D 8C 3S 6H"))
```

### 2. Script Player Actions

```python
# Add actions for each betting round
script.add_action("pre-flop", 0, "call")      # Player 0 calls
script.add_action("pre-flop", 1, "check")     # Player 1 checks

script.add_action("flop", 1, "check")         # Player 1 checks
script.add_action("flop", 0, "raise", 50)     # Player 0 raises $50

script.add_action("turn", 1, "call")          # Player 1 calls
script.add_action("turn", 0, "check")         # Player 0 checks

script.add_action("river", 0, "check")        # Player 0 checks
script.add_action("river", 1, "check")        # Player 1 checks
```

### 3. Create and Run the Game

```python
# Create game from script
game = MockPokerGame(script)
game.DEBUG = False  # Disable debug output

# Run a hand
game.play_hand()

# Check results
print(f"Player 0 stack: ${game.players[0].stack}")
print(f"Player 1 stack: ${game.players[1].stack}")
```

### 4. Assert Results

```python
tester = GameTester()

# Assert specific conditions
tester.assert_equal(game.players[0].stack, 950, "Player 0 lost $50")
tester.assert_equal(game.players[1].stack, 1050, "Player 1 won $50")
tester.assert_true(game.players[1].stack > game.players[0].stack, "Player 1 has more chips")

# Print summary
tester.print_summary()
```

## Card String Format

Use the format: `RANK + SUIT`

**Ranks**: 2-10, J, Q, K, A
**Suits**: H (Hearts), D (Diamonds), C (Clubs), S (Spades)

Examples:
- `AS` = Ace of Spades
- `2H` = 2 of Hearts
- `10D` = 10 of Diamonds
- `KS` = King of Spades

## Hand Parsing

The `GameTester.parse_hand()` method parses space-separated cards:

```python
tester = GameTester()
cards = tester.parse_hand("AS KS QS JS 10S")  # Royal flush on board
```

## Assertion Methods

### Basic Assertions

```python
tester.assert_equal(actual, expected, "message")
tester.assert_true(condition, "message")
tester.assert_false(condition, "message")
```

### Game-Specific Assertions

```python
# Check player stack
tester.assert_stack(player, 1000, "after hand 1")

# Check hand evaluation
cards = tester.parse_hand("AS KS QS JS 10S")
tester.assert_hand_type(cards, "Royal Flush", "on the board")
```

## Example: Test All-In Scenario

```python
from game_test_suite import GameScript, MockPokerGame, GameTester

tester = GameTester()

# Create 2-player game with $100 starting stacks
script = GameScript(num_players=2, starting_stack=100)

# Set up all-in scenario
script.set_hole_cards(0, tester.parse_hand("AS AH"))   # AA (best hand)
script.set_hole_cards(1, tester.parse_hand("KS KH"))   # KK (second best)
script.set_community_cards(tester.parse_hand("2D 3D 4D 5D 6D"))  # Flush on board

# Player 0 goes all-in pre-flop, Player 1 calls
script.add_action("pre-flop", 0, "raise", 100)  # All-in
script.add_action("pre-flop", 1, "call")        # Calls all-in

game = MockPokerGame(script)
game.DEBUG = False

# Script the all-in state
game.players[0].is_all_in = True
game.players[1].is_all_in = True
game.players[0].total_bet_this_round = 100
game.players[1].total_bet_this_round = 100

# Check that side pots are created correctly
pots = game.create_side_pots()
tester.assert_equal(len(pots), 1, "Should have 1 pot (equal all-in)")
tester.assert_equal(pots[0]['amount'], 200, "Pot should be $200 total")
```

## Example: Test Hand Evaluation

```python
tester = GameTester()

# Test each hand rank
royal_flush = tester.parse_hand("AS KS QS JS 10S")
tester.assert_hand_type(royal_flush, "Royal Flush")

straight_flush = tester.parse_hand("9H 8H 7H 6H 5H")
tester.assert_hand_type(straight_flush, "Straight Flush")

four_kind = tester.parse_hand("2D 2C 2H 2S KH")
tester.assert_hand_type(four_kind, "Four of a Kind")

full_house = tester.parse_hand("3D 3C 3H 5S 5H")
tester.assert_hand_type(full_house, "Full House")

flush = tester.parse_hand("2C 4C 6C 8C 10C")
tester.assert_hand_type(flush, "Flush")

straight = tester.parse_hand("9D 8C 7H 6S 5D")
tester.assert_hand_type(straight, "Straight")

tester.print_summary()
```

## Running Tests

Execute the test suite:

```bash
python game_test_suite.py
```

This will run all included tests and print a summary:

```
============================================================
POKER GAME TEST SUITE
============================================================
Testing Hand Evaluation...

============================================================
TEST SUMMARY: 10/10 passed
============================================================

...
```

## Tips

1. **Use `DEBUG = False`** to suppress game output during scripted games
2. **Parse cards consistently** using `tester.parse_hand()` for all card inputs
3. **Test edge cases** like all-ins, multiple side pots, and ties
4. **Assert after each meaningful step** to catch bugs early
5. **Use descriptive messages** in assertions for easier debugging

## Extending the Framework

### Add Custom Assertions

```python
class GameTester:
    def assert_player_folded(self, player: Player, message: str = ""):
        return self.assert_true(player.is_folded, 
                               f"Player {player.player_id} folded: {message}")
```

### Create Test Functions

```python
def test_flush_beats_straight():
    """Test that flush always beats straight"""
    tester = GameTester()
    
    straight = tester.parse_hand("9D 8C 7H 6S 5D")
    flush = tester.parse_hand("2C 4C 6C 8C 10C")
    
    # Evaluate both hands
    straight_info = HandEvaluator.evaluate_hand(straight)
    flush_info = HandEvaluator.evaluate_hand(flush)
    
    straight_rank = HandEvaluator.HAND_RANKS[straight_info[0]]
    flush_rank = HandEvaluator.HAND_RANKS[flush_info[0]]
    
    tester.assert_true(flush_rank > straight_rank, "Flush beats straight")
    tester.print_summary()
```

## Test-Driven Development Workflow

1. **Write the test** first for the feature you want
2. **Run the test** (it should fail)
3. **Implement the feature** in poker_game.py
4. **Run the test** again (it should pass)
5. **Refactor** code if needed while tests still pass

This ensures your backend logic is robust and correct!
