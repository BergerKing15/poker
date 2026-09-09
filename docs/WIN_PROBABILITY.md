# Win Probability Calculator Documentation

## Overview

The `WinProbabilityCalculator` uses Monte Carlo simulation to calculate the probability that a player will win a poker hand given:
- Their own hole cards (2 cards)
- Community cards (0, 3, 4, or 5 cards)
- Number of opponents still in the hand

The calculator **does not** assume knowledge of opponents' cards - it simulates random opponent hands and calculates the player's equity against average opposition.

## Basic Usage

### Initialize the Calculator

```python
from win_probability import WinProbabilityCalculator
from poker_game import Card

# Create calculator with 10,000 simulations (default)
calculator = WinProbabilityCalculator(num_simulations=10000)

# Or use fewer simulations for faster calculation (less accuracy)
calculator = WinProbabilityCalculator(num_simulations=1000)
```

### Calculate Win Probability

```python
# Create player's hole cards
player_cards = [Card("Spades", "A"), Card("Hearts", "K")]

# Create community cards (can be 0, 3, 4, or 5)
community = [Card("Clubs", "A"), Card("Hearts", "5"), Card("Diamonds", "3")]

# Calculate probability vs 2 opponents
result = calculator.calculate_win_probability(player_cards, community, num_opponents=2)

# Result dictionary
print(result)
# {
#     'win_prob': 0.68,        # 68% chance to win outright
#     'tie_prob': 0.02,        # 2% chance to tie
#     'lose_prob': 0.30,       # 30% chance to lose
#     'equity': 0.68,          # Win% + (Tie% / num_players)
#     'wins': 6800,            # Simulations won
#     'ties': 200,             # Simulations tied
#     'losses': 3000           # Simulations lost
# }
```

## Return Values

### `calculate_win_probability()` Returns

```python
{
    'win_prob': float,      # Probability of winning outright
    'tie_prob': float,      # Probability of tying (splitting pot)
    'lose_prob': float,     # Probability of losing
    'equity': float,        # Expected value as % of pot
    'wins': int,            # Number of winning simulations
    'ties': int,            # Number of tie simulations
    'losses': int           # Number of losing simulations
}
```

### Equity Calculation

**Equity** represents the player's share of the pot:
- `equity = win_prob + (tie_prob / num_players)`
- In a 3-player pot: if win 60% and tie 6%, equity = 60% + (6% / 3) = 62%

## Configuration

Simulation count is configurable via config.py:

```python
# During gameplay (faster)
NUM_SIMULATIONS_SETUP = 5000

# For testing/analysis (more accurate)
NUM_SIMULATIONS_SETUP_SCREEN = 10000
```

Usage in poker_ui.py:
```python
from config import NUM_SIMULATIONS_SETUP
self.win_probability_calculator = WinProbabilityCalculator(num_simulations=NUM_SIMULATIONS_SETUP)
```

## Hand Strength Categories

Use `get_hand_strength()` for descriptive feedback:

```python
strength = calculator.get_hand_strength(player_cards, community, num_opponents)
# Returns: "very weak", "weak", "fair", "good", "very good", or "excellent"
```

Categories are relative to the number of opponents:
- **Very Weak**: Below half the average equity
- **Weak**: Below average equity
- **Fair**: Around average equity
- **Good**: Slightly above average
- **Very Good**: Significantly above average
- **Excellent**: Far above average

## Advanced Usage

### Calculate vs Specific Known Hands

For analysis, testing, or debugging, you can calculate probability against specific known opponent hands:

```python
player_cards = [Card("Spades", "A"), Card("Hearts", "A")]
opponent_hand_1 = [Card("Clubs", "K"), Card("Diamonds", "K")]
opponent_hand_2 = [Card("Hearts", "Q"), Card("Spades", "Q")]

result = calculator.calculate_vs_specific_hands(
    player_cards,
    [],  # No community cards yet
    [opponent_hand_1, opponent_hand_2]
)

print(f"AA vs KK + QQ: {result['equity']:.2%} equity")
```

## Examples

### Example 1: Premium Hand Pre-Flop

```python
# Pocket Aces (best starting hand)
player = [Card("Spades", "A"), Card("Hearts", "A")]
community = []

result = calculator.calculate_win_probability(player, community, num_opponents=3)
print(f"Equity: {result['equity']:.2%}")  # ~64% in 4-way pot
```

### Example 2: Made Hand on Flop

```python
# Trips (three of a kind)
player = [Card("Hearts", "K"), Card("Diamonds", "K")]
community = [
    Card("Clubs", "K"),
    Card("Hearts", "5"),
    Card("Diamonds", "3")
]

result = calculator.calculate_win_probability(player, community, num_opponents=2)
print(f"Equity: {result['equity']:.2%}")  # ~92% in 3-way pot
```

### Example 3: Drawing Hand

```python
# Open-ended straight draw + flush draw
player = [Card("Clubs", "K"), Card("Diamonds", "Q")]
community = [
    Card("Hearts", "J"),
    Card("Spades", "10"),
    Card("Hearts", "3"),
    Card("Clubs", "2")
]

result = calculator.calculate_win_probability(player, community, num_opponents=1)
print(f"Equity: {result['equity']:.2%}")  # ~50% heads-up
```

### Example 4: Weak Hand

```python
# High card only
player = [Card("Spades", "A"), Card("Hearts", "9")]
community = [
    Card("Diamonds", "K"),
    Card("Clubs", "Q"),
    Card("Hearts", "J")
]

result = calculator.calculate_win_probability(player, community, num_opponents=3)
print(f"Equity: {result['equity']:.2%}")  # ~15-20% in 4-way pot
```

## Card Creation

Cards are created using the `Card` class:

```python
from poker_game import Card

# Format: Card(suit, rank)
# Suits: "Hearts", "Diamonds", "Clubs", "Spades"
# Ranks: "2"-"10", "J", "Q", "K", "A"

ace_spades = Card("Spades", "A")
king_hearts = Card("Hearts", "K")
ten_diamonds = Card("Diamonds", "10")
two_clubs = Card("Clubs", "2")
```

## Simulation Accuracy

The calculator uses Monte Carlo simulation. More simulations = more accurate but slower:

```python
# Fast but less accurate (±1-2%)
fast_calc = WinProbabilityCalculator(num_simulations=1000)

# Balanced (±0.5-1%)
balanced_calc = WinProbabilityCalculator(num_simulations=10000)

# Slow but very accurate (±0.1-0.5%)
accurate_calc = WinProbabilityCalculator(num_simulations=100000)
```

### Typical Simulation Times (10,000 sims):
- Pre-flop: ~0.5 seconds
- Flop: ~1 second
- Turn: ~2 seconds
- River: ~3 seconds

## Error Handling

The calculator validates inputs:

```python
try:
    # Must have exactly 2 hole cards
    calculator.calculate_win_probability([card1], [], 1)  # ❌ ValueError
    
    # Community cards must be 0, 3, 4, or 5
    calculator.calculate_win_probability(cards, [c1, c2], 1)  # ❌ ValueError
    
    # Must have at least 1 opponent
    calculator.calculate_win_probability(cards, [], 0)  # ❌ ValueError
    
    # No duplicate cards between player and community
    player = [Card("Spades", "A"), Card("Hearts", "A")]
    community = [Card("Spades", "K"), Card("Spades", "A"), Card("Hearts", "5")]
    calculator.calculate_win_probability(player, community, 1)  # ❌ ValueError
    
except ValueError as e:
    print(f"Invalid input: {e}")
```

## Integration with Game UI

```python
from win_probability import WinProbabilityCalculator
from poker_game import Card, PokerGame

# During a game, calculate player equity
calculator = WinProbabilityCalculator(num_simulations=5000)

# Get player's cards and community cards from game state
player_cards = game.players[0].hole_cards
community_cards = game.community_cards
num_opponents = len([p for p in game.players if not p.is_folded and p.player_id != 0])

# Calculate and display
result = calculator.calculate_win_probability(
    player_cards,
    community_cards,
    num_opponents
)

print(f"Your win probability: {result['equity']:.2%}")
print(f"Hand strength: {calculator.get_hand_strength(player_cards, community_cards, num_opponents)}")
```

## How It Works

1. **Create remaining deck**: Remove known cards from a full 52-card deck
2. **For each simulation**:
   - Generate random hole cards for each opponent
   - Complete community cards by drawing remaining cards
   - Evaluate all hands using `HandEvaluator`
   - Compare hands and determine winner
3. **Calculate results**: Convert simulation counts to probabilities

The algorithm assumes:
- All opponents play randomly (unknown cards)
- Probability is calculated against average opposition
- Hands are evaluated to showdown
- All players go to river if no one folds

## Notes

- **Real poker**: Actual equity depends on opponent tendencies, bet sizes, and fold probability
- **All-in only**: This calculator assumes game goes to showdown
- **Hidden cards**: Opponent cards are unknown, so this represents average equity
- **Pre-flop standards**: AA ~65%, AK ~60%, 72o ~25% vs 3 opponents

## Testing

See [TESTING.md](TESTING.md) for how to test the calculator:

```python
from game_test_suite import GameTester
from win_probability import WinProbabilityCalculator

tester = GameTester()
calculator = WinProbabilityCalculator()

# Test specific scenario
player_cards = tester.parse_hand("AS AH")
community = tester.parse_hand("KS 5D 3C")

result = calculator.calculate_win_probability(player_cards, community, 1)
tester.assert_true(result['equity'] > 0.8, "AA vs unknown should have 80%+ equity")
```
