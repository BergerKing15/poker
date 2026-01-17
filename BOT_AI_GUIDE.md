# Poker Bot AI System

## Overview

The poker bot system provides game theory-based AI opponents using win probability calculations and position-aware decision making. Bots have randomized player types with different styles to create varied and realistic opponents.

## Architecture

### Components

1. **PokerBot** - Individual AI player class
   - Uses Monte Carlo win probability calculation
   - Considers position, stack sizes, and pot odds
   - Randomized playing style based on type

2. **PokerBotType** - Predefined playing styles
   - Tightness (hand selection)
   - Aggression (betting frequency)

3. **BotManager** - Manages a pool of varied bots

## Player Types

### Five Predefined Styles

| Type | Name | Tightness | Aggression | Description |
|------|------|-----------|-----------|-------------|
| **TAG** | Tight Aggressive | 75% | 85% | Professional style: selective hand ranges, aggressive betting |
| **LAG** | Loose Aggressive | 35% | 80% | High variance: wide ranges, constantly pressuring |
| **CTR** | Call-Fold | 55% | 40% | Balanced: moderate ranges, conservative play |
| **NIT** | Nitty | 90% | 50% | Super tight: only premium hands, minimal aggression |
| **FISH** | Loose-Passive | 30% | 20% | Weak player: calls too much, rarely raises |

### Distribution

When a game starts with 3-10 players:
- Each AI player (except the human) gets a random or cycling bot type
- Types cycle through the list to ensure variety
- Example with 5 players: TAG, LAG, CTR, NIT, FISH (then cycles back)

## Decision Making Algorithm

### Step 1: Hand Strength Evaluation

**Pre-flop**: Evaluates based on hole cards
- Pairs from 2-2 to A-A
- High cards: AK, AQ, AJ, etc.
- Suited connectors
- Returns normalized 0.0-1.0 score

**Post-flop**: Uses best 5-card hand ranking
- High Card, One Pair, Two Pair, etc.
- Converted to 0.0-1.0 scale

### Step 2: Win Probability Calculation

- Monte Carlo simulation with 1,000 iterations
- Accounts for all active opponents
- Considers community cards at any stage
- Returns equity (win% + tie%/num_players)

### Step 3: Position Evaluation

Position affects hand selection thresholds:

```
Positions (relative to button):
- Early Position: First to act post-flop (30-50% multiplier)
- Middle Position: Middle stage (80% multiplier)
- Late Position: Last to act, dealer (130% multiplier)
```

Early position requires stronger hands to play.

### Step 4: Decision Logic

**If checking is available (to_call = 0)**:
- Strong hands (strength > 0.65) → Bet with probability = aggression
- Weak hands → Check

**If facing a bet (to_call > 0)**:
1. Calculate fold threshold = `(0.35 + tightness×0.30) × position_multiplier`
2. If equity < fold_threshold → Fold
3. If equity ≥ pot_odds or equity > 50% → Consider raising
   - Probability to raise = `aggression × hand_strength`
   - Raise amount = `call_amount + (aggression × stack_percentage)`
4. Otherwise → Call

**If all-in forced (to_call > stack)**:
- Call if equity > 40%
- Fold otherwise

### Step 5: Aggression Modulation

Raise amounts vary by player type:
```python
raise_amount = call_amount + (max_stack × aggression × hand_strength)
```

- **TAG** (0.85 agg): Large raises with good hands
- **LAG** (0.80 agg): Frequent raises even with moderate hands
- **CTR** (0.40 agg): Minimal raises, mostly calls
- **NIT** (0.50 agg): Selective raises only
- **FISH** (0.20 agg): Rarely raises

## Usage in Games

### Automatic Initialization

When a game starts:
```python
game = PokerGame(num_players=5, use_bots=True)
# Automatically creates bots for players 1-4, with human as player 0
```

### Disabling Bots

```python
game = PokerGame(num_players=5, use_bots=False)
# Falls back to simple AI
```

### Bot Information

Access bot information during or after game:
```python
bot = game.bots.get(player_id)
if bot:
    print(f"Player type: {bot.type.name}")
    print(f"Tightness: {bot.type.tightness:.0%}")
    print(f"Aggression: {bot.type.aggression:.0%}")
```

## Key Features

✅ **Position-Aware**: Adjusts hand requirements based on table position  
✅ **Win Probability**: Uses accurate equity calculations (1,000 simulations)  
✅ **Varied Playing Styles**: 5 distinct player archetypes  
✅ **Game Theory**: Pot odds, stack depth, and equity-based decisions  
✅ **Randomized**: Each game creates different opponent mix  
✅ **Scalable**: Works with 2-10 total players  
✅ **Fallback**: Gracefully reverts to simple AI if errors occur  

## Technical Details

### Files
- **poker_bot.py**: Core bot implementation
- **poker_game.py**: Integration with game engine

### Performance
- Win probability calculation: ~1-3 seconds per decision (1,000 sims)
- Can be tuned down to 100-500 sims for faster gameplay
- Position calculation: < 1ms
- Decision logic: < 10ms

### Extensibility

To add new bot types:
```python
# In poker_bot.py, add to PokerBot.TYPES:
TYPES = {
    "CUSTOM": PokerBotType("My Custom Type", tightness=0.65, aggression=0.75),
    ...
}
```

## Game State Helper Methods

PokerGame provides helper methods for efficient player filtering:

```python
from poker_game import PokerGame

game = PokerGame(num_players=3)

# Get all active players (not folded, with stack > 0)
active = game.get_active_players()

# Get all unfolded players
unfolded = game.get_unfolded_players()

# Get active players excluding a specific player
opponents = game.get_active_opponents(player)

# Get unfolded players excluding a specific player
unfolded_opponents = game.get_unfolded_opponents(player)
```

These methods optimize performance by eliminating redundant list comprehensions throughout the codebase.

## Future Enhancements

Possible improvements (no ML yet):
- Hand history tracking for adaptation
- GTO-based adjustments
- Stack-to-pot ratio (SPR) awareness
- Multi-table position dynamics
- Villain-specific strategy adjustments
