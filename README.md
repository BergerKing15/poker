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
python play.py
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

```
poker/          engine, bots, equity, tournament runner
poker/ui/       Tkinter front-ends
tests/          unittest suite
tools/          developer utilities
scripts/        ready-made tournament runs
assets/         card images
docs/           design notes
play.py, run_tournament.py    launchers
```

### Core Game Engine
- **poker/game.py**: Game logic, card evaluation, hand flow
  - `PokerGame`: Blinds, betting rounds, side pots, showdown
  - `HandEvaluator`: 5-card hand ranking and comparison
  - `Card`, `Deck`, `Player`: Cards and player state
  - `GameObserver` / `ConsoleObserver` / `GameAborted`: the front-end contract

The engine owns the betting rules and drives a hand through observer hooks
(`on_hand_start`, `on_stage`, `get_human_action`, `on_action`, `on_hand_end`, and so on).
Every hook defaults to a no-op, so headless play and tournaments pass no observer at all.
There is exactly one betting implementation — the GUI runs the same loop rather than
keeping a copy of it.

### Poker Bot AI System
- **poker/bot.py**: Game theory based AI
  - `PokerBot`: Position-aware decisions from equity and pot odds
  - `PokerBot.TYPES`: TAG, LAG, CTR, NIT, FISH
  - 12 `SimpleBot*` fixed-strategy baselines used as controls
- **poker/notation.py**: Starting-hand notation (`AA`, `AKs`, `T9o`) and the 169-hand
  enumeration

### Equity
- **poker/equity.py**: `WinProbabilityCalculator`, Monte Carlo, returns win/tie/lose/equity
- **poker/equity_cache.py**: `CachedEquityCalculator` — answers pre-flop from a
  precomputed table of all 169 starting hands × 9 opponent counts, and memoises post-flop
  for the life of the process

### Tools
- **tools/equity_heatmap.py**: Draws the equity table as the 13x13 range chart poker
  players already read - suited above the diagonal, offsuit below, pairs on it. Runs in
  the terminal with ANSI colour, or exports a standalone interactive page.
  A correct table fades smoothly from AA to 32o; sampling noise shows up as cells
  breaking that gradient.
- **tools/build_equity_table.py**: Builds the precomputed table

### Data
- **poker/hand_log.py**: `HandLog`, a `GameObserver` writing one row per player per hand
  plus the action sequence to SQLite, so runs accumulate instead of overwriting
- **poker/tournament.py**: `BotTournament` with an optional `hand_log_path`

### UI & Display
- **poker/ui/game_window.py**: `PokerUI` — the table, with image caching and an optional
  equity readout
- **poker/ui/tournament_window.py**: live tournament analytics dashboard

### Testing
- **tests/**: `unittest` suite, 179 tests
- **tests/support.py**: shared helpers — card shorthand, scripted observers, fixed bots

#### Running Tests
```bash
# Everything (~2.5 minutes)
python -m unittest discover -s tests -t .

# One module, class or test
python -m unittest tests.test_betting
python -m unittest tests.test_betting.TestMinimumRaise
python -m unittest discover -s tests -t . -k raise
```

`-t .` sets the top-level directory so the packages import; discovery fails without it.
Note that `-k` matches the test *method* name, not the class.

## Performance Benchmarks

### Execution Times
- **Betting Round**: ~50-100ms (5-10% faster after optimization)
- **Hand Evaluation**: <1ms per hand
- **Win Probability Calculation**: ~50-150ms (5000 Monte Carlo sims)
- **AI Decision Making**: ~100-200ms (including equity calculation)
- **Full Game Hand**: ~2-5 seconds (from deal to showdown)

### Test Suite Performance
```
$ python -m unittest discover -s tests -t .
Ran 179 tests in 242s
OK (skipped=3)
```
Most modules finish in under five seconds. The time is dominated by the two that sample:
`test_betting` (~100s) and `test_equity` (~190s). The three skips are checks against the
precomputed equity table, which skip when it has not been built.

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
python play.py
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

- **179 Tests**: `unittest` suite covering the engine, bots, equity, caching and the
  SQLite hand log
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
- [x] **Hand History Database**: Per-hand SQLite records to train on (`poker/hand_log.py`)
- [ ] **Opponent Modeling**: Track AI opponent patterns and adapt strategy
- [ ] **Neural Network Hand Evaluation**: Learn hand strength beyond heuristics
- [ ] **Reinforcement Learning**: Self-play training for AI improvement
- [ ] **Clustering Algorithm**: Group similar game situations for faster lookup
- [x] **Precomputed Equity**: Pre-flop lookup table plus post-flop memoisation
  (`poker/equity_cache.py`)

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
- [x] **Database Integration**: Games stored in SQLite (`--log` on the tournament runner)
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
1. **Installation check** (`python -m tools.verify_installation`)
   - Imports, bot types, game creation, a bot decision and an equity calculation
   - Exits non-zero on failure

2. **Syntax validation**
   - `python -m compileall -q poker tools scripts`

3. **Bot interface checks**
   - Builds all 17 registered bots and asserts the `decide_action` contract
   - Plays real hands with every bot type, because a bot that raises is swallowed by the
     engine's fallback and would otherwise look merely unlucky

4. **Tests**
   - `python -m unittest discover -s tests -t . -v`

5. **Code quality**
   - Import chain integrity
   - `python -m tools.check_prints`: an AST walk that fails on prints outside a `DEBUG`
     guard, with a documented allowlist

6. **Performance check**
   - Benchmarks hand evaluation, requiring under 1.0s per 1000 evaluations

Every step propagates its exit code — there is no `|| echo` masking, so a green badge
means the pipeline actually passed.

**Badge Status**: ![Tests](https://github.com/BergerKing15/poker/actions/workflows/tests.yml/badge.svg)

**Quick Local Testing**:
```bash
python -m unittest discover -s tests -t .      # the whole suite (~2.5 min)
python -m unittest tests.test_betting          # one module
python -m tools.verify_installation            # installation smoke check
python -m tools.check_prints                   # print-guard check
```

## License

This poker game implementation is provided as-is for educational purposes. The playing card images retain their original public domain status from the Vector Playing Cards project.
