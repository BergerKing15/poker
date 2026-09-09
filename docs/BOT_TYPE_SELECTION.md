# Bot Type Selection Feature

## Overview
Added the ability to set bot types before starting a game in the Poker AI UI.

## Changes Made

### 1. **poker_game.py** - Modified PokerGame class
- Added `bot_types` parameter to `__init__()` method
  - Accepts a dictionary mapping player_id to bot type string
  - Example: `{1: "TAG", 2: "LAG", 3: "FISH"}`
- Updated `_initialize_bots()` method to use custom bot types when provided
  - Falls back to default variety if bot type not specified for a player
  - Supports: "TAG", "LAG", "CTR", "NIT", "FISH", and None (random)

### 2. **poker_ui.py** - Enhanced PokerUI class

#### New UI Elements
- Added "Bot Types" labeled frame in the setup screen
- Added dropdown selectors for each AI opponent
- Options for each opponent:
  - TAG (Tight Aggressive) - Professional tight/aggressive player
  - LAG (Loose Aggressive) - Aggressive player playing many hands
  - CTR (Call-Fold) - Passive caller/folder
  - NIT (Nitty) - Super tight player
  - FISH (Loose-Passive) - Weak player
  - Random - Randomly selected type

#### New Methods
- `_create_bot_type_selectors(parent_frame)`: Generates dropdown selectors based on number of opponents
- `_update_bot_type_selectors(event)`: Updates selectors when opponent count changes

#### Modified Methods
- `setup_ui()`: Added bot type selection frame and event binding
- `start_game()`: 
  - Collects selected bot types from dropdowns
  - Maps display names to bot type codes
  - Passes bot_types dictionary to PokerGame constructor

## Usage

1. Set the number of AI opponents (1-9)
2. Select the desired bot type for each opponent from the dropdown
3. Choose "Random" for a randomly selected bot type
4. Click "Start Game"
5. Each opponent will play with the selected personality/strategy

## Bot Type Descriptions

| Type | Code | Tightness | Aggression | Description |
|------|------|-----------|------------|-------------|
| TAG | TAG | 0.75 | 0.85 | Tight aggressive - professional poker player |
| LAG | LAG | 0.35 | 0.80 | Loose aggressive - plays many hands aggressively |
| CTR | CTR | 0.55 | 0.40 | Call-fold - passive player |
| NIT | NIT | 0.90 | 0.50 | Nitty - super tight, conservative |
| FISH | FISH | 0.30 | 0.20 | Loose-passive - weak player |
| Random | None | - | - | Randomly selected from available types |

## Example

```python
# Creating a game with specific bot types
bot_types = {
    1: "TAG",    # Opponent 1 is Tight Aggressive
    2: "FISH",   # Opponent 2 is Loose-Passive
    3: "LAG"     # Opponent 3 is Loose Aggressive
}

game = PokerGame(
    num_players=4,
    starting_stack=1000,
    bot_types=bot_types
)
```

## Testing

The feature has been tested to verify:
- ✅ Bot types are correctly passed to PokerGame
- ✅ Custom bot types override default assignments
- ✅ UI properly displays and collects selections
- ✅ Dropping down from opponent spinbox dynamically updates selectors
- ✅ "Random" option correctly maps to None (triggers PokerBot's random selection)
