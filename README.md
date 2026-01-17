# Texas Hold'em Poker UI

A visual Texas Hold'em poker game built with Python and Tkinter, featuring AI opponents and a clean GUI with card images.

## Features

- **Visual Gameplay**: Display all cards with high-quality vector playing card images
- **Advanced AI Opponents**: Play against 1-9 AI players using game theory and win probability
  - 5 distinct player types: TAG (Tight Aggressive), LAG (Loose Aggressive), CTR (Call-Fold), NIT (Ultra-tight), FISH (Loose-Passive)
  - Position-aware decision making (early/middle/late)
  - Monte Carlo equity calculations
  - Intelligent raise sizing based on hand strength and aggression
- **Optional Win Probability Display**: See your hand's equity during gameplay
- **Game History**: Complete chronological history of all hands played
- **Hand Analysis**: View all opponent hands and best 5-card hands at showdown
- **Interactive Controls**: 
  - Check/Call/Raise/Fold actions with intuitive button interface
  - Adjustable raise amount via slider or manual entry
  - Real-time pot and stack tracking
- **Indefinite Gameplay**: Play as many hands as you want until you exit
- **Scalable**: Support for 2-10 total players

## Setup

### Requirements

- Python 3.8+
- Tkinter (usually included with Python)
- Pillow (PIL) for image handling

### Installation

1. Clone the repository:
```bash
git clone https://github.com/BergerKing15/poker.git
cd poker
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install Pillow
```

## Running the Game

```bash
python poker_ui.py
```

The game will open a configuration window where you can:
- Choose number of AI opponents (1-9)
- Set starting stack for each player ($100-$10,000)
- Optionally enable win probability/equity display during gameplay
- Click "Start Game" to begin

## Game Controls

- **Check**: Advance to next betting round without wagering
- **Call**: Match the current bet
- **Raise**: Increase the bet (use slider or enter amount manually)
- **Fold**: Exit the current hand and lose your bet

## Gameplay

1. **Setup Phase**: Configure game parameters
2. **Hand Play**: 
   - Pre-Flop betting (2 hole cards)
   - Flop (3 community cards)
   - Turn (4 community cards)
   - River (5 community cards)
   - Showdown (winner determination)
3. **History**: All actions and results logged in the game history display
4. **Repeat**: Continue playing hands indefinitely

## Game Interface

- **Left Panel**: Game history showing all actions, bets, and results
- **Center**: Community cards displayed with visual images
- **Right Panel**: 
  - Player stacks and status
  - Your hole cards with images
  - Raise controls (slider + entry field)

## Architecture

### Core Game Engine
- **poker_game.py**: Game logic, card evaluation, AI decision making
  - `PokerGame`: Main game orchestrator with bot integration
  - `HandEvaluator`: 5-card hand ranking and comparison
  - `Card`, `Deck`: Card and deck management
  - `Player`: Player state and actions

### Poker Bot AI System
- **poker_bot.py**: Advanced game theory-based AI (NEW)
  - `PokerBot`: Individual AI player with position awareness
  - `PokerBotType`: Defines playing style (tightness & aggression)
  - `BotManager`: Manages pool of varied bots
  - Features: Win probability calculations, position awareness, intelligent aggression

### UI & Display
- **poker_ui.py**: Tkinter GUI and display
  - `PokerUI`: Main UI class
  - Display updates with image caching for performance
  - Player action handling and validation
  - Optional equity display

### Testing & Documentation
- **all_tests.py**: Master test runner - runs all test suites at once
- **game_test_suite.py**: Comprehensive game logic tests (92 assertions)
- **win_probability_test_suite.py**: Win probability calculator tests
- **test_bot_ai.py**: Bot AI decision tests
- **BOT_AI_GUIDE.md**: Comprehensive AI documentation
- **BOT_QUICK_REFERENCE.md**: Quick reference guide

#### Running Tests
```bash
# Run all tests at once (recommended)
python all_tests.py

# Or run individual test suites
python game_test_suite.py
python win_probability_test_suite.py
python test_bot_ai.py
```

## Hand Rankings

Games are evaluated using standard poker hand rankings:
1. Royal Flush
2. Straight Flush
3. Four of a Kind
4. Full House
5. Flush
6. Straight
7. Three of a Kind
8. Two Pair
9. One Pair
10. High Card

## Performance Optimizations

- **PhotoImage Caching**: Card images cached by name, preventing memory leaks
- **Selective Redraws**: UI only rebuilds card displays when they actually change
- **Efficient Hand Evaluation**: Optimized hand ranking evaluation
- **Active Player Filtering**: Helper methods in PokerGame reduce redundant list comprehensions
  - `get_active_players()` - ~5-10% faster betting round execution
  - `get_unfolded_players()` - Eliminates repeated filtering logic
  - `get_active_opponents()` - Centralized opponent counting
- **Configuration Centralization**: All constants in config.py for easy tuning
- **Consistent Monte Carlo**: Configurable simulation counts prevent inconsistencies

### Configuration

See **config.py** for all adjustable parameters:
```python
# UI Configuration
UI_WINDOW_WIDTH = 1200
UI_WINDOW_HEIGHT = 900

# Game Configuration  
DEFAULT_NUM_OPPONENTS = 2
DEFAULT_STARTING_STACK = 1000
DEFAULT_BIG_BLIND = 10
DEFAULT_SMALL_BLIND = 5

# AI Configuration
DEFAULT_AI_DELAY = 0.1  # seconds between AI moves
MAX_AI_DELAY = 5.0
NUM_SIMULATIONS_SETUP = 5000  # Win probability calculations
```

## Code Quality

- **92 Test Assertions**: Comprehensive test coverage across 3 test suites
- **Type Hints**: Full Optional[] type annotations throughout
- **Helper Methods**: Clean abstractions for common operations
- **Debug Flags**: Consistent debug output management

## Credits

### Playing Card Images

Playing card images sourced from [Vector Playing Cards](https://github.com/notpeter/vector-playing-cards) by Peter Tripp and originally created by Byron Knoll. These cards are released into the public domain.

Conversion from SVG to PNG was performed using:
- **rsvg-convert** (from librsvg) for SVG to PNG conversion
- **optipng** for PNG optimization

### Original Source

The original vector playing card designs by Byron Knoll are available at:
https://github.com/notpeter/vector-playing-cards

## License

This poker game implementation is provided as-is for educational purposes. The playing card images retain their original public domain status from the Vector Playing Cards project.

## Future Enhancements

- [ ] Hand statistics and player tracking
- [ ] Machine learning-based opponent adaptation
- [ ] Tournament mode with multiple buy-ins
- [ ] Save/load game sessions
- [ ] Network multiplayer support
- [ ] Card deck variations (colored backgrounds, different card styles)
- [ ] GTO (Game Theory Optimal) strategy refinements
- [ ] Explainable AI (show bot reasoning for decisions)
