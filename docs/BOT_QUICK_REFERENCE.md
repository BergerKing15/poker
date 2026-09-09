# Poker Bot AI - Quick Reference

## Bot Types at a Glance

```
┌─────┬────────────────────┬───────────┬────────────┐
│ Type │ Name               │ Tightness │ Aggression │
├─────┼────────────────────┼───────────┼────────────┤
│ TAG  │ Tight Aggressive   │    75%    │     85%    │ ← Pro style
│ LAG  │ Loose Aggressive   │    35%    │     80%    │ ← Gambler
│ CTR  │ Call-Fold          │    55%    │     40%    │ ← Balanced
│ NIT  │ Nitty              │    90%    │     50%    │ ← Super tight
│ FISH │ Loose-Passive      │    30%    │     20%    │ ← Weak player
└─────┴────────────────────┴───────────┴────────────┘
```

## Playing Style Characteristics

### TAG (Tight Aggressive) - Pro Player
- **Hand Selection**: Only premium hands (AA-TT, AK, AQ, AJ)
- **Betting**: Aggressive raises with strong hands
- **Weakness**: Can be exploited by aggressive opponents
- **Meta**: Most profitable against weak fields

### LAG (Loose Aggressive) - Gambler  
- **Hand Selection**: Broad range, plays many hands
- **Betting**: Constant pressure, frequent bluffs
- **Strength**: Tough to predict, high variance
- **Meta**: Requires skilled opponents to beat

### CTR (Call-Fold) - Balanced Player
- **Hand Selection**: Moderate standards
- **Betting**: Checks/calls more than raises
- **Strength**: Steady, predictable
- **Meta**: Exploitable but safe

### NIT (Nitty) - Ultra-Tight
- **Hand Selection**: Only premium hands (AA-QQ, AK)
- **Betting**: Minimal aggression, value-focused
- **Weakness**: Exploitable with aggressive play
- **Meta**: Easy to read, easy to exploit

### FISH (Loose-Passive) - Weak Player
- **Hand Selection**: Calls with weak hands
- **Betting**: Rarely raises, mostly calls
- **Strength**: Predictable
- **Meta**: Easy money for skilled players

## Decision Factors

### 1. Hand Strength (Pre-flop)
```
1.00 | AA
0.97 | KK
0.93 | QQ-JJ
0.75 | AK, AQ
0.55 | KQ, KJ
0.21 | 76 (weak hands)
0.00 | 32 (worst hand)
```

### 2. Position Impact
```
Early (UTG):       0.50x - Need stronger hands
Middle (MP):       0.80x - Moderate standards
Late (Button):     1.30x - Can play more hands
```

### 3. Pot Odds
```
If to_call/pot ≤ equity → +EV (worth calling)
If to_call/pot > equity → -EV (should fold)
```

### 4. Aggression Factors
- **Tightness**: Controls fold frequency
- **Aggression**: Controls raise frequency
- **Hand Strength**: Modulates bet size
- **Position**: Adjusts initial hand standards

## Key Concepts

### Tightness (Hand Selection)
- How selective the player is
- High tightness = fold more weak hands
- Low tightness = play more hands

### Aggression (Betting Style)
- How often they bet/raise vs call
- High aggression = frequent raises
- Low aggression = mostly calls/checks

### Position
- **Early** = harder to win (fewer opponents to collect from)
- **Late** = easier to win (acts last, best information)

### Equity
- Win probability in current hand
- TAG wants > 50% equity before raising
- FISH might call with 30% equity

## Common Scenarios

### Scenario 1: TAG Pre-flop with AA
- Hand strength: 100%
- Action: Aggressive raise (likely 3-4x bet)
- Reason: Premium hand, value extraction

### Scenario 2: LAG Post-flop Miss
- Hand strength: 40%
- Action: Might bet anyway (bluff)
- Reason: Aggression + pressure

### Scenario 3: NIT with Second Pair
- Hand strength: 60%
- Action: Check/call (avoid commitment)
- Reason: Conservative, value-focused

### Scenario 4: FISH with Weak Hand
- Hand strength: 35%
- Action: Call (loose call)
- Reason: Weak player tendency

## Game Theory Foundations

✓ **Pot Odds**: Money in pot vs money to call
✓ **Position**: Acting last = information advantage
✓ **Stack Depth**: Deep stacks = more variance
✓ **Hand Equity**: Actual win probability
✓ **Expected Value**: Long-term profitability

## Integration

### Enable Bots
```python
game = PokerGame(num_players=6, use_bots=True)
```

### Disable Bots
```python
game = PokerGame(num_players=6, use_bots=False)
```

### Access Bot Info
```python
bot = game.bots.get(player_id)
print(f"Type: {bot.type.name}")
print(f"Aggression: {bot.type.aggression:.0%}")
```

## Performance Notes

- Win probability: 1-3 seconds (1,000 sims)
- Can reduce to 100 sims for faster play (~200ms)
- Position calculation: < 1ms
- Decision logic: < 10ms

## Testing

Run test suite:
```bash
python test_bot_ai.py      # Bot system tests
python game_test_suite.py  # Game integration tests
python poker_bot.py        # Display bot types
```

## Troubleshooting

**Issue**: Slow gameplay
- **Fix**: Reduce simulations in WinProbabilityCalculator (100-500)

**Issue**: Bots not using new types
- **Fix**: Check poker_bot.py TYPES dictionary

**Issue**: Always same bot type
- **Fix**: Check BotManager distribution logic

**Issue**: Bots playing too tight/loose
- **Fix**: Adjust tightness/aggression in TYPES

## Testing

Run bot tests:
```bash
python test_bot_ai.py
```

Run all tests:
```bash
python all_tests.py
```

Tests verify:
- ✓ Bot initialization with different types
- ✓ Decision logic against various scenarios
- ✓ Equity calculations
- ✓ Position awareness

