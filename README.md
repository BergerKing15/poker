# Texas Hold'em Poker UI

![Tests](https://github.com/BergerKing15/poker/actions/workflows/tests.yml/badge.svg)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue)

A visual Texas Hold'em poker game built with Python and Tkinter, featuring AI opponents with game theory strategies and a clean GUI with card images. Built as a junior year software engineering project with comprehensive testing, performance optimizations, and automated CI/CD.

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
- **game_test_suite.py**: Comprehensive game logic tests (91 assertions)
- **win_probability_test_suite.py**: Win probability calculator tests
- **test_bot_ai.py**: Bot AI decision tests
- **docs/BOT_AI_GUIDE.md**: Comprehensive AI documentation
- **docs/BOT_QUICK_REFERENCE.md**: Quick reference guide

#### Running Tests
```bash
# Run all tests at once (recommended)
python all_tests.py

# Or run individual test suites
python game_test_suite.py
python win_probability_test_suite.py
python test_bot_ai.py
```

## Performance Benchmarks

### Execution Times
- **Betting Round**: ~50-100ms (5-10% faster after optimization)
- **Hand Evaluation**: <1ms per hand
- **Win Probability Calculation**: ~50-150ms (5000 Monte Carlo sims)
- **AI Decision Making**: ~100-200ms (including equity calculation)
- **Full Game Hand**: ~2-5 seconds (from deal to showdown)

### Test Suite Performance
```
$ python all_tests.py
PASSED   | Game Logic Tests                         91 assertions
PASSED   | Win Probability Calculator Tests         44 assertions
PASSED   | Bot AI Decision Tests                    0 assertions
Assertions: 135 passed, 0 failed
```
Runtime is roughly 1-2 minutes, nearly all of it the win probability suite's
Monte Carlo simulations. The Bot AI suite is demonstration output plus a
starting-range check that raises on failure, so it contributes no counted
assertions.

### Memory Usage
- **Base Application**: ~15-20 MB
- **With Card Images**: ~25-30 MB (PhotoImage cache)
- **Per Game Session**: Negligible (no memory leaks)

## Complexity Analysis

### Algorithm Complexities

**Hand Evaluation**
- Finding best hand: O(C(7,5)) = O(21) = O(1)
- Evaluating single hand: O(5 log 5) = O(1) - sorting 5 cards
- Overall: **O(1)** for any number of players

**Betting Round**
- Iterating through players: O(n) where n = number of players
- Processing each action: O(1)
- Overall: **O(n)** per betting round

**Win Probability (Monte Carlo)**
- Per simulation: O(n + 1) = O(n) - evaluating player + opponents
- k simulations: **O(k × n)**
- With k=5000, n=8: ~40,000 hand evaluations

**AI Decision Making**
- Position calculation: O(1)
- Hand strength evaluation: O(1)
- Pot odds calculation: O(1)
- Win probability lookup: O(k) - from simulation
- Overall: **O(k)** for complete decision

### Space Complexity

| Component | Space | Notes |
|-----------|-------|-------|
| Game State | O(n) | n players, fixed per player |
| Card Images | O(52) | Constant, cached PhotoImages |
| Hand History | O(h × n) | h hands × n players |
| Monte Carlo Samples | O(k) | k simulations in memory |

## Demo & Screenshots

To see the game in action:

```bash
python poker_ui.py
```

**Game Features Visible:**
- 🃏 High-quality card display
- 🤖 Live AI opponent play
- 💰 Real-time pot and stack tracking
- 📊 Optional win probability display
- 📝 Complete game history
- 🎰 Interactive betting controls

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

- **135 Test Assertions**: Comprehensive test coverage across 3 test suites
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

## Areas for Enhancement

### 🎰 Short-term (Feasible for Junior SWE)
- [ ] **Hand Statistics**: Track win rates, fold rates, average pot size per player
- [ ] **Replay System**: Save and replay games with step-through functionality
- [ ] **Configurable Blinds**: Allow tournament-style blind increases
- [ ] **Player Profiles**: Save/load player preferences and statistics
- [ ] **Sound Effects**: Add betting, dealing, and win/loss audio
- [ ] **Keyboard Shortcuts**: Improve UI responsiveness with hotkeys

### 🧠 Machine Learning Integration
- [ ] **Opponent Modeling**: Track AI opponent patterns and adapt strategy
- [ ] **Neural Network Hand Evaluation**: Learn hand strength beyond heuristics
- [ ] **Reinforcement Learning**: Self-play training for AI improvement
- [ ] **Clustering Algorithm**: Group similar game situations for faster lookup

### 🎲 Advanced Game Theory
- [ ] **GTO (Game Theory Optimal) Solver**: Calculate Nash equilibrium strategies
- [ ] **Pot Odds Tutorial**: Educational mode teaching optimal decisions
- [ ] **Range Analysis**: Analyze opponent betting ranges
- [ ] **Exploitative Strategies**: Adjust play based on opponent weaknesses
- [ ] **Variance Analysis**: Track results against expected value

### 🌐 Multiplayer & Networking
- [ ] **Network Multiplayer**: Play against other humans via TCP/websockets
- [ ] **Server Backend**: Store player stats, replays, leaderboards
- [ ] **Tournament System**: Multi-table tournaments with bracket generation
- [ ] **Real-time Sync**: Cross-platform game synchronization

### 📈 Analytics & Visualization
- [ ] **Hand Heatmap**: Visualize profitable positions and hands
- [ ] **Equity Charts**: Real-time equity calculation graphs
- [ ] **Decision Tree**: Show AI reasoning for each decision
- [ ] **Dashboard**: Stats dashboard with win rates, ROI, hand histories
- [ ] **Equity Graphs**: EV curves over time

### 🔧 Code Improvements
- [ ] **Async/Await**: Use asyncio for smoother UI during AI thinking
- [ ] **Cython Compilation**: Compile critical paths to C for 10x+ speed
- [ ] **Plugin Architecture**: Allow custom AI implementations
- [ ] **Database Integration**: Store games in SQLite/PostgreSQL
- [ ] **Configuration Hot-reload**: Change settings without restart

### 🚀 Deployment
- [ ] **Docker Container**: Containerize for easy deployment
- [ ] **Web Version**: Build web UI with React/Vue
- [ ] **Mobile App**: iOS/Android version with PyMobileToolchain
- [ ] **Package Distribution**: PyPI package for pip install

## Continuous Integration & CI/CD

**GitHub Actions Workflow**: Automated testing on every push and pull request

### Workflow Details (`.github/workflows/tests.yml`)

**Test Matrix:**
- **Python Versions**: 3.11, 3.12
- **OS**: Ubuntu (with headless Tkinter via Xvfb)
- **Trigger**: Pushes to `main`/`develop`, all pull requests

**Pipeline Steps:**
1. **Syntax Validation** (`py_compile`)
   - Validates all Python files compile without syntax errors
   - Runs: `python -m py_compile poker_game.py poker_ui.py ...`

2. **Comprehensive Testing**
   - Game logic tests (91 assertions)
   - Win probability calculations (44 assertions)
   - Bot AI decision making
   - Runs: `python all_tests.py` (135 assertions, ~1-2 minutes)

3. **Code Quality Checks**
   - Verifies import chain integrity
   - Checks for print statements in production code
   - Validates type annotations

4. **Performance Validation**
   - Benchmarks hand evaluation speed
   - Ensures performance hasn't regressed
   - Requires: <1.0ms for hand evaluation batch

**Badge Status**: ![Tests](https://github.com/BergerKing15/poker/actions/workflows/tests.yml/badge.svg)

**Quick Local Testing**:
```bash
python all_tests.py              # Run all 135 assertions (~1-2 min)
python game_test_suite.py        # Game logic tests
python win_probability_test_suite.py  # Equity calculator
python test_bot_ai.py            # Bot AI validation
```

## License

This poker game implementation is provided as-is for educational purposes. The playing card images retain their original public domain status from the Vector Playing Cards project.
