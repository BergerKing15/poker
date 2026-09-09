#!/usr/bin/env python3
"""Test that all bot types load correctly"""

from bot_tourney import BotTournament

t = BotTournament()
print(f"✓ {len(t.BOT_FACTORY)} bot types loaded:\n")
for name in sorted(t.BOT_FACTORY.keys()):
    print(f"  - {name}")

print(f"\nAll bots successfully imported!")
print(f"\nBot Type Breakdown:")
print(f"  AI Bots: TAG, LAG, CTR, NIT, FISH (5)")
print(f"  Simple Strategy Bots: {len(t.BOT_FACTORY) - 5} (comprehensive baseline strategies)")
