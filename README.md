# Texas Hold'em Poker UI

A visual Texas Hold'em poker game built with Python and Tkinter, featuring AI opponents and a clean GUI with card images.

## Features

- **Visual Gameplay**: Display all cards with high-quality vector playing card images
- **AI Opponents**: Play against 1-5 AI players with simple betting strategy
- **Game History**: Complete chronological history of all hands played
- **Hand Analysis**: View all opponent hands and best 5-card hands at showdown
- **Interactive Controls**: 
  - Check/Call/Raise/Fold actions with intuitive button interface
  - Adjustable raise amount via slider or manual entry
  - Real-time pot and stack tracking
- **Indefinite Gameplay**: Play as many hands as you want until you exit

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
- Choose number of AI opponents (1-5)
- Set starting stack for each player ($100-$10,000)
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

- **poker_game.py**: Game logic, card evaluation, AI decision making
  - `PokerGame`: Main game orchestrator
  - `HandEvaluator`: 5-card hand ranking and comparison
  - `Card`, `Deck`: Card and deck management
  - `Player`: Player state and actions

- **poker_ui.py**: Tkinter GUI and display
  - `PokerUI`: Main UI class
  - Display updates with image caching for performance
  - Player action handling and validation

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
- **Efficient Hand Evaluation**: Memoized best-hand calculations

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

- [ ] Tournament mode with multiple buy-ins
- [ ] Customizable AI strategy levels
- [ ] Hand statistics and player tracking
- [ ] Save/load game sessions
- [ ] Network multiplayer support
- [ ] Card deck variations (colored backgrounds, different card styles)
