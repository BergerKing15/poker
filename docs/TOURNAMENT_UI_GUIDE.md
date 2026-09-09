# Tournament Analytics UI

## Overview

A real-time Tkinter-based dashboard that displays tournament progress and live bot statistics while the tournament runs. Watch your bots compete in real-time with continuously updated win rates, game counts, and performance metrics.

## Features

✓ **Real-time Progress Tracking**
- Visual progress bar showing games completed vs total
- Percentage complete indicator
- Elapsed time and ETA calculation

✓ **Live Bot Statistics**
- Table showing each bot's performance
- Columns: Wins, Games, Win Rate, Total Hands, Avg Hands/Game
- Automatically sorted and updated after each game
- All 17 bot types tracked simultaneously

✓ **Tournament Info**
- Elapsed time counter
- Estimated time remaining (ETA)
- Tournament status indicator

✓ **Clean, Responsive UI**
- Non-blocking tournament execution
- Smooth updates without freezing
- Scrollable statistics table
- Dark theme for easy viewing during long tournaments

## Usage

### Run Tournament with UI

```bash
cd /home/noahberg/Projects/PokerAI
python bot_tourney.py --ui
```

The UI will pop up immediately and begin displaying:
1. Tournament progress (games completed / total)
2. Real-time win rates for all bots
3. Hands played statistics
4. Time elapsed and remaining

### Run Tournament without UI (Normal Mode)

```bash
python bot_tourney.py
```

Runs the tournament normally with console output only.

## UI Layout

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    PokerAI Tournament Analytics                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Tournament Progress                                                       ║
│  Games Completed: [████████░░░░░░░░░░░░░░] 250 / 1028 games (24.3%)        │
║                                                                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║  Bot Statistics                                                            ║
║                                                                            ║
│  Bot           │ Wins │ Games │ Win Rate │ Hands │ Hands/Game │          │
│  ────────────────────────────────────────────────────────────────          │
│  TAG           │  45  │  85   │  52.9%   │ 4250  │   50.0     │          │
│  LAG           │  35  │  82   │  42.7%   │ 4100  │   50.0     │          │
│  FISH          │  28  │  76   │  36.8%   │ 3800  │   50.0     │          │
│  AllIn         │  32  │  70   │  45.7%   │ 3500  │   50.0     │          │
│  ...           │ ...  │ ...   │  ...     │ ...   │   ...      │          │
║                                                                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║  Elapsed: 15:32 | ETA: 42:18 | Status: Running...                         ║
╚════════════════════════════════════════════════════════════════════════════╝
```

## Data Displayed

### Progress Section
- **Games Completed**: Number of games finished so far
- **Total Games**: Total games configured for tournament
- **Percentage**: Progress indicator (0-100%)
- **Visual Progress Bar**: Real-time animated progress

### Bot Statistics Table
For each bot, tracks:
- **Wins**: Number of games won
- **Games**: Number of games played
- **Win Rate**: Calculated as Wins / Games × 100%
- **Hands**: Total hands participated in
- **Hands/Game**: Average hands per game (Hands / Games)

### Tournament Info
- **Elapsed**: Time since tournament started (MM:SS format)
- **ETA**: Estimated time remaining (MM:SS format)
- **Status**: Current tournament status

## How It Works

1. **Initialization**
   - Reads all tournament configurations
   - Calculates total games to be played
   - Identifies all unique bot types
   - Creates Tkinter window with tables

2. **Game Execution**
   - Runs games sequentially through configurations
   - After each game, updates statistics
   - Refreshes UI display
   - Calculates running averages

3. **Progress Calculation**
   - Tracks elapsed time for each game
   - Estimates time remaining based on average game duration
   - Updates ETA every game

4. **Completion**
   - Shows completion message
   - Keeps UI visible for 5 seconds
   - Returns results for further analysis

## Technical Details

### Module: `tournament_ui.py`

#### Class: `TournamentAnalyticsUI`
```python
TournamentAnalyticsUI(total_games, bot_names)
- __init__()          # Initialize UI window
- _create_ui()        # Build UI layout
- update_progress()   # Update with new stats
- _refresh_ui()       # Refresh all display elements
- close()             # Close the window
- show_completion()   # Show completion message
```

#### Function: `run_tournament_with_ui()`
```python
run_tournament_with_ui(bot_configs, num_games_per_config, 
                       small_blind=1, big_blind=2)
- Orchestrates tournament with UI updates
- Returns results dict with final statistics
```

### Integration with `bot_tourney.py`

New command-line flags:
- `--ui`: Run tournament with real-time analytics UI
- Default: Run tournament without UI

New functions:
- `main_with_ui()`: Tournament entry point with UI
- Updated `__main__`: Command-line interface selection

## Example Output

```
PokerAI Tournament Runner
================================================================================
Usage:
  python bot_tourney.py          # Run without UI
  python bot_tourney.py --ui     # Run with real-time analytics UI
================================================================================

Running tournament with UI (1028 games total)...
[TournamentAnalyticsUI window opens with live updates]
```

## Performance Notes

- **Non-blocking**: Tournament runs while UI updates occur
- **Responsive**: UI refreshes after each game (~1-2 second interval)
- **Scalable**: Handles 1000+ games smoothly
- **Memory efficient**: Statistics stored in dictionaries, not full game logs

## Troubleshooting

### UI doesn't appear
- Ensure Tkinter is installed: `python -m tkinter`
- On Linux, may need: `sudo apt-get install python3-tk`

### Slow performance
- Normal for large tournaments (1000+ games)
- Each game takes 1-5 seconds depending on hand count
- UI updates don't significantly impact tournament speed

### Numbers don't match terminal output
- The UI shows running totals that update after each game
- Terminal output shows final summary (same numbers when complete)
- Tournament always generates the same results regardless of UI

## Next Steps

1. **Run a tournament with UI**: `python bot_tourney.py --ui`
2. **Watch real-time statistics** as bots compete
3. **See final results** in terminal output
4. **Use tournament_results.json** for ML training

## Future Enhancements

Potential improvements:
- Show individual game details (cards, winners, stacks)
- Real-time charts/graphs of win rates over time
- Export live statistics to CSV
- Pause/resume tournament capability
- Head-to-head bot comparison view
