# Bot Tournament System - ML Training Data Generator

## Overview

`bot_tourney.py` is a comprehensive tournament runner that plays thousands of poker hands between different bot types to generate ML training data and performance statistics.

## Bot Types Available

### AI Bots (Game-Theory Based)
- **TAG** (Tight Aggressive) - Professional poker player style
  - Tightness: 0.75 | Aggression: 0.85
  - Plays premium hands, raises frequently
  
- **LAG** (Loose Aggressive) - Aggressive player
  - Tightness: 0.35 | Aggression: 0.80
  - Plays many hands, very aggressive
  
- **CTR** (Call-Fold) - Passive player
  - Tightness: 0.55 | Aggression: 0.40
  - Calls often, rarely raises
  
- **NIT** (Nitty) - Super tight player
  - Tightness: 0.90 | Aggression: 0.50
  - Only plays premium hands
  
- **FISH** (Loose-Passive) - Weak player
  - Tightness: 0.30 | Aggression: 0.20
  - Plays many hands passively

### Baseline Strategy Bots (Perfect ML Targets)
- **Top10%** - Only plays top 10% of hands pre-flop, calls post-flop
  - Great baseline for tight strategies
  
- **AllIn** - Always goes all-in
  - Extreme aggressive baseline
  
- **CheckCall** - Always checks or calls, never raises or folds
  - Perfect neutral baseline
  
- **Random** - Plays completely randomly
  - Worst-case baseline for comparison

## Usage

### Run Full Tournament
```bash
python bot_tourney.py
```

### Run Quick Test
```bash
python test_tourney_quick.py
```

### Programmatic Usage
```python
from bot_tourney import BotTournament

configs = [
    {"num_players": 2, "bot_types": ["TAG", "FISH"], "repeat": 20},
    {"num_players": 3, "bot_types": ["LAG", "AllIn", "CheckCall"], "repeat": 20},
]

tournament = BotTournament()
tournament.run_tournament(configs, hands_per_game=50, verbose=True)
tournament.print_summary()
tournament.save_results("my_results.json")
```

## Output

### Console Summary
Displays win rates, average stacks, and per-game stats:
```
Bot Type        Games    Wins     Win %      Avg Stack     Avg Gain     Hands/Game  
TAG             100      75       75.0%      $1250         $250         50.0        
FISH            100      15       15.0%      $600          $-400        50.0        
```

### JSON Results
Saves detailed statistics to `tournament_results.json`:
```json
{
  "timestamp": "2026-01-29T16:03:59.738742",
  "summary": {
    "TAG": {
      "games_played": 100,
      "hands_played": 5000,
      "wins": 75,
      "win_rate": "75.0%",
      "avg_stack": "$1250",
      "avg_gain_per_game": "$250",
      "hands_per_game": "50.0"
    }
  },
  "stats": {
    "TAG": {
      "games_played": 100,
      "hands_played": 5000,
      "wins": 75,
      "total_gain": 25000,
      "final_stacks": [1200, 1350, ...]
    }
  }
}
```

## Statistics Tracked

Per bot type:
- **games_played**: Total games played
- **hands_played**: Total hands played
- **wins**: Games won (highest chip count)
- **win_rate**: Percentage of games won
- **avg_stack**: Average final stack
- **total_gain**: Total chips gained/lost across all games
- **avg_gain_per_game**: Average stack change per game
- **hands_per_game**: Average hands completed per game
- **final_stacks**: List of all final stack sizes

## Tournament Configuration

Each config specifies:
```python
{
    "num_players": 3,           # Number of players in each game
    "bot_types": ["TAG", "FISH", "LAG"],  # Bot type sequence
    "repeat": 20                # Number of games to play with these settings
}
```

When `repeat=20` with different bot type allocations:
- 3-player game uses bot_types[0], bot_types[1], bot_types[2]
- Stats are aggregated by bot type across all games

## ML Training Use

This tournament system generates data perfect for ML training:

1. **Consistent Performance Metrics**: Track bot performance across thousands of hands
2. **Diverse Matchups**: Test every bot vs every other bot type in various configurations
3. **Scalability**: Easily configure different game sizes (2-9 players) and repetitions
4. **Exportable Data**: JSON output ready for ML pipeline

### Example ML Usage
```python
import json

# Load tournament results
with open('tournament_results.json') as f:
    results = json.load(f)

# Use win rates as training labels
win_rates = {name: float(stats['win_rate'].rstrip('%'))
             for name, stats in results['summary'].items()}

# Train ML model to predict performance
for bot_type, win_rate in win_rates.items():
    print(f"{bot_type}: {win_rate}% win rate")
```

## Performance Notes

- Each hand takes ~0.1-0.5 seconds depending on game complexity
- 100 games × 50 hands × 9 players ≈ 3-5 minutes
- Adjust `hands_per_game` and `repeat` counts for speed/accuracy tradeoff
- Results are saved immediately upon completion
- No data loss if process interrupted - resume with another tournament run

## Default Tournament Configuration

The full tournament (run via `python bot_tourney.py`) includes:
- 5 heads-up matchups (2 players): 125 total games
- 3 three-player games: 60 total games  
- 2 four-player games: 30 total games
- 1 six-player game: 10 total games
- 1 nine-player game: 5 total games

**Total: ~230 games = ~11,500 hands**

Estimated runtime: 10-20 minutes

## Future Enhancements

1. Hand-by-hand action logging for detailed analysis
2. Position-specific statistics
3. Win rate confidence intervals (running average)
4. Matchup-specific win rates (TAG vs FISH, etc.)
5. Stack evolution tracking (how stacks change throughout game)
