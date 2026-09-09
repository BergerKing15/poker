# Tournament Progress Tracking Guide

## Overview
The tournament runner now includes **real-time progress tracking** without massive slowdown. A background thread monitors tournament progress and displays live statistics every 3 seconds.

## Features

### ✅ Real-Time Progress Display
The progress tracker shows:
- **Games completed** - Which game out of total (e.g., 3/10)
- **Hands played** - Total hands across all games
- **Speed metrics** - Games per second (g/s) and hands per second (h/s)
- **Time estimate** - ETA in seconds and minutes based on current speed

### ✅ Detect Stuck Games
If a game hangs or is extremely slow, the tracker will show:
- Speed dropping significantly (e.g., 1.0 g/s → 0.1 g/s)
- ETA increasing dramatically
- Game-level timing: Each game shows how long it took "[20 hands in 0.5s]"

### ✅ Timeout Protection
- Per-hand timeout: If a single hand takes >10 seconds, the game is aborted
- Game continues with fewer hands than planned
- Prevents infinite loops from blocking the entire tournament

## Usage

### Standard Run (with AI bots)
```bash
python bot_tourney.py
```
Shows real-time progress for the full comprehensive tournament.

### Fast Mode (testing only)
For quick testing without AI calculations (much faster):
```bash
python bot_tourney.py --fast
```
Converts AI bots to simple random bots, completes in seconds.

### With UI
```bash
python bot_tourney.py --ui
```
Includes both real-time progress tracking AND UI dashboard.

### Programmatic Usage
```python
from bot_tourney import BotTournament

tournament = BotTournament()
config = [
    {"num_players": 2, "bot_types": ["TAG", "NIT"], "hands_per_game": 20},
] * 5

# Run with progress tracking
tournament.run_tournament(config, verbose=True, fast_mode=False)

# Or fast mode for testing
tournament.run_tournament(config, verbose=True, fast_mode=True)
```

## Example Output

```
Running 5 games: 2 players
  Bots: Random, CheckCall
  [1/5] Starting game: 2p: Random, CheckCall... [20 hands in 0.1s]
  [2/5] Starting game: 2p: Random, CheckCall... [20 hands in 0.1s]
  ⏱ [1/5 games | 40 hands] (2.0 g/s, 40 h/s) ETA: 2s (0m)
  [3/5] Starting game: 2p: Random, CheckCall... [20 hands in 0.1s]
  ⏱ [2/5 games | 60 hands] (1.3 g/s, 27 h/s) ETA: 2s (0m)
  [4/5] Starting game: 2p: Random, CheckCall... [20 hands in 0.1s]
  ⏱ [3/5 games | 80 hands] (1.0 g/s, 20 h/s) ETA: 2s (0m)
  [5/5] Starting game: 2p: Random, CheckCall... [20 hands in 0.1s]
  ⏱ [4/5 games | 100 hands] (0.8 g/s, 16 h/s) ETA: 1s (0m)
Tournament complete! (5.0s)
Games completed: 5 / 5
```

## Interpretation Guide

### Speed Metrics

| g/s (games/sec) | Status | Meaning |
|---|---|---|
| > 1.0 | ✅ Fast | Simple bots, progressing well |
| 0.5-1.0 | ✅ Normal | AI bots with moderate calculations |
| 0.1-0.5 | ⚠️ Slow | Complex AI calculations or larger games |
| < 0.1 | 🔴 Very Slow | May be stuck or extremely heavy calculations |
| 0.0 | 🔴 Stuck | Game is not progressing |

### Detecting Problems

**Game completely stalled:**
```
⏱ [3/10 games | 60 hands] (0.2 g/s, 4 h/s) ETA: 35s (0m)
⏱ [3/10 games | 60 hands] (0.1 g/s, 3 h/s) ETA: 70s (1m)   ← No progress!
⏱ [3/10 games | 60 hands] (0.1 g/s, 2 h/s) ETA: 110s (1m)  ← Timeout likely
```

**Solution:** Use `--fast` mode or reduce hands_per_game during testing.

## Performance Notes

### Why AI Bots Are Slow
- TAG/LAG/CTR/NIT/FISH use Monte Carlo simulations (1000 iterations per decision)
- Win probability calculations require evaluating all possible opponent hands
- Larger games (6-9 players) = more opponents = exponentially more calculations

### Why Simple Bots Are Fast
- Random: picks random action (instant)
- CheckCall: no AI calculation (instant)
- AllIn: fixed strategy (instant)

### Rough Speed Expectations
- 2p heads-up with simple bots: **~1-2 games/sec** (0.1s per game)
- 2p heads-up with AI bots: **~0.2 games/sec** (5s per game)
- 6p game with mixed bots: **~0.05 games/sec** (20s per game)
- 9p game with AI bots: **~0.02 games/sec** (40-60s per game)

## Troubleshooting

### "Game taking too long, aborting..."
The game timeout (10s/hand) was triggered. Possible causes:
1. **Infinite loop in bot logic** - Check poker_bot.py
2. **Slow hand evaluation** - Too many cards to evaluate
3. **System under load** - Other processes using CPU

**Fix:** Use `--fast` mode or contact dev team about bot optimization.

### Progress stops entirely
Tournament hung. Most common causes:
1. **Memory leak** - Old game objects not being garbage collected
2. **Deadlock** - Rare race condition in threading
3. **Exception silently caught** - Check error log

**Fix:** Restart with `--fast` mode or reduce game count. Report to dev team with the config that caused it.

### ETA keeps increasing
The tournament is running but slower than expected:
- Check if AI bots are being used (they're much slower)
- Reduce hands_per_game to speed up testing
- Use `--fast` mode for quick verification

## Configuration Tips

### For Fastest Testing
```python
# Change to this:
{"num_players": 2, "bot_types": ["Random", "CheckCall"], "hands_per_game": 5}
```
Expected: 5-10 games per second

### For Balanced Testing
```python
{"num_players": 3, "bot_types": ["Random", "Top10%", "CheckCall"], "hands_per_game": 10}
```
Expected: 1-2 games per second

### For AI Evaluation (slow but accurate)
```python
{"num_players": 2, "bot_types": ["TAG", "LAG"], "hands_per_game": 50}
```
Expected: 0.1-0.2 games per second, but good data quality
