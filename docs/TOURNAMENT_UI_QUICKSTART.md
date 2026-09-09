# Tournament UI Quick Start

## One-Minute Guide

### Run Tournament with Real-Time UI Analytics

```bash
cd /home/noahberg/Projects/PokerAI
python bot_tourney.py --ui
```

**That's it!** A window will pop up showing:
- Live tournament progress bar
- Real-time win rates for all 17 bots
- Games completed counter
- Time elapsed and estimated time remaining
- Hands played statistics

### What You'll See

1. **Window Title**: "PokerAI Tournament Analytics"
2. **Progress Bar**: Shows games completed (e.g., 250/1028 games = 24.3%)
3. **Statistics Table**: Live table with columns:
   - Bot name
   - Wins (games won)
   - Games (games played)
   - Win Rate (%)
   - Hands (total hands played)
   - Hands/Game (average)
4. **Status Line**: Shows elapsed time, ETA, and status

### Example Output

```
Tournament Progress
Games Completed: [████████░░░░░░░░░░░░] 250 / 1028 games (24.3%)

Bot Statistics
Bot          | Wins | Games | Win Rate | Hands | Hands/Game
TAG          |  85  | 150   | 56.7%    | 7500  | 50.0
LAG          |  72  | 160   | 45.0%    | 8000  | 50.0
AllIn        |  68  | 125   | 54.4%    | 6250  | 50.0
...

Elapsed: 25:34 | ETA: 64:12 | Status: Running...
```

## Why Use the UI?

✓ **Watch Progress Live**: See tournament completion in real-time
✓ **Track Bot Performance**: Compare win rates as they change
✓ **Estimate Completion**: Know how long until tournament finishes
✓ **Professional Appearance**: Better than staring at console logs
✓ **Data Validation**: Verify bots are performing as expected

## Running Modes

### With UI (Recommended)
```bash
python bot_tourney.py --ui
```
- Real-time dashboard
- Easy to monitor
- Great for presentations/demos

### Without UI (Classic Mode)
```bash
python bot_tourney.py
```
- Console output only
- Smaller memory footprint
- Good for batch processing

## The UI Display

The window shows:

**Tournament Progress Section**
- Progress bar (visual)
- Game counter (text)
- Percentage complete

**Bot Statistics Section** (Main Table)
- Scrollable list of all 17 bots
- Updated after each game
- Sorted by bot name

**Tournament Info Section**
- Elapsed time (since start)
- ETA (estimated completion)
- Running status

## What Happens When Tournament Completes

1. Status changes to "Tournament Complete!" in green
2. UI window stays open for 5 seconds
3. Window auto-closes
4. Results saved to `tournament_results.json`
5. Terminal shows final summary statistics

## Behind the Scenes

The UI module (`tournament_ui.py`):
- Runs tournament in the main thread
- Updates display after each game
- Calculates statistics on-the-fly
- Estimates remaining time based on average game duration
- Non-blocking (UI stays responsive)

## System Requirements

- Python 3.11+
- Tkinter (included with Python on most systems)
- Linux: `sudo apt-get install python3-tk`
- macOS: Should be included with Python
- Windows: Should be included with Python

## Troubleshooting

**UI doesn't appear?**
```bash
# Test Tkinter
python -m tkinter
# If this shows a window, Tkinter is working
```

**Slow updates?**
- Normal for large tournaments (1000+ games)
- Each game takes 1-5 seconds
- UI updates don't slow down tournament

**Numbers seem wrong?**
- Running totals update after each game
- Terminal shows final summary (same numbers when complete)
- Always generates same results

## Example Session

```bash
$ python bot_tourney.py --ui
PokerAI Tournament Runner
================================================================================
Usage:
  python bot_tourney.py          # Run without UI
  python bot_tourney.py --ui     # Run with real-time analytics UI
================================================================================

Running tournament with UI (1028 games total)...
[TournamentAnalyticsUI window opens]

[After 30 minutes...]
✓ Tournament Complete!

[Results summary in terminal]
TAG:        57.9% win rate
AllIn:      57.1% win rate
FISH:       49.2% win rate
...

Results saved to: tournament_results.json
```

## Next Steps

1. **Run tournament with UI**: `python bot_tourney.py --ui`
2. **Monitor progress** - The window will update in real-time
3. **Wait for completion** - Tournament runs while you watch
4. **Check results** - View `tournament_results.json` for ML training
5. **Analyze data** - Use tournament results for bot strategy analysis

## Advanced Usage

### Customize Tournament in UI
Edit the `main_with_ui()` function in `bot_tourney.py`:
```python
# Change number of games per configuration
results = run_tournament_with_ui(bot_configs, 1, ...)

# Modify blinds
results = run_tournament_with_ui(
    bot_configs, 1, 
    small_blind=2, 
    big_blind=4
)
```

### Use UI Programmatically
```python
from tournament_ui import run_tournament_with_ui

# Define your bot matchups
configs = [
    ["TAG", "LAG"],
    ["FISH", "NIT"],
    # ... more matchups
]

# Run with UI
results = run_tournament_with_ui(configs, 50)
```

## Files Involved

- `bot_tourney.py` - Main tournament runner (updated with --ui flag)
- `tournament_ui.py` - Real-time analytics UI (new)
- `TOURNAMENT_UI_GUIDE.md` - Detailed documentation (new)
- `tournament_results.json` - Output data file

## Tips & Tricks

1. **Maximize window** for better visibility of all bot stats
2. **Leave running** while you work on other tasks
3. **Scroll down** to see less-common bots if needed
4. **Check ETA** to know when results will be ready
5. **Take screenshots** for tournament reports

## Support

For issues:
1. Check `TOURNAMENT_UI_GUIDE.md` for detailed docs
2. Run without UI: `python bot_tourney.py`
3. Check terminal output for errors
4. Verify Tkinter installation: `python -m tkinter`

---

**Happy bot tournaments!** 🎰🤖
