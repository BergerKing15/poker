#!/usr/bin/env python3
"""
Diagnostic tool to find which hand causes the tournament to hang.
Runs games with detailed per-hand timing and logs.
"""

import sys
import time
import signal
from poker_game import PokerGame
from poker_bot import PokerBot, SimpleBotCheckCall, SimpleBotRandom

def timeout_handler(signum, frame):
    raise TimeoutError("Hand execution timeout - infinite loop detected")

def test_single_game(num_players, bot_types, max_hands=20):
    """Test a single game with detailed hand-level logging"""
    print(f"\n{'='*70}")
    print(f"Testing: {num_players}p game with {', '.join(bot_types)}")
    print(f"{'='*70}")
    
    game = PokerGame(
        num_players=num_players,
        starting_stack=1000,
        small_blind=5,
        big_blind=10,
        use_bots=True
    )
    
    # Replace players with bots
    game.bots = {}
    for i in range(num_players):
        bot_type = bot_types[i % len(bot_types)]
        game.bots[i] = PokerBot(i, bot_type)
    
    hands_completed = 0
    try:
        for hand_num in range(max_hands):
            hand_start = time.time()
            
            # Set alarm for 5 second timeout per hand
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            
            try:
                print(f"  Hand {hand_num + 1:2d}: ", end='', flush=True)
                game.play_hand()
                
                # Cancel alarm
                signal.alarm(0)
                
                hand_time = time.time() - hand_start
                print(f"✓ ({hand_time:.2f}s) - Stacks: {[p.stack for p in game.players]}")
                hands_completed += 1
                
            except TimeoutError:
                signal.alarm(0)
                print(f"✗ TIMEOUT - Hand hung after 5 seconds!")
                print(f"     Current stacks: {[p.stack for p in game.players]}")
                print(f"     Active players: {len([p for p in game.players if not p.is_folded])}")
                print(f"     Game pot: ${game.pot}")
                
                # Try to identify which player is causing the issue
                for i, p in enumerate(game.players):
                    print(f"     Player {i} ({bot_types[i % len(bot_types)]}): " + 
                          f"${p.stack}, folded={p.is_folded}, all_in={p.is_all_in}")
                return hands_completed, True  # True = hang detected
                
            except Exception as e:
                signal.alarm(0)
                print(f"✗ ERROR: {type(e).__name__}: {e}")
                return hands_completed, False
                
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        signal.alarm(0)
        return hands_completed, False
    
    print(f"\n✓ All {hands_completed} hands completed successfully")
    return hands_completed, False

def main():
    print("Diagnostic: Finding Tournament Hangs")
    print("="*70)
    
    test_configs = [
        # Simple bots (should be fast)
        (2, ["Random", "CheckCall"]),
        (3, ["Random", "CheckCall", "AllIn"]),
        
        # Mix simple + AI
        (2, ["TAG", "Random"]),
        (2, ["NIT", "CheckCall"]),
        
        # Larger games
        (4, ["Random", "CheckCall", "AllIn", "NeverFold"]),
        (4, ["TAG", "LAG", "NIT", "Random"]),
    ]
    
    for num_players, bot_types in test_configs:
        hands_completed, hung = test_single_game(num_players, bot_types, max_hands=20)
        
        if hung:
            print(f"\n🔴 HANG DETECTED in {num_players}p: {', '.join(bot_types)}")
            print("This configuration causes infinite loops. NOT SUITABLE for tournament.")
            print("\nRerun with more verbose logging to debug:")
            print(f"  DEBUG=1 python diagnose_hang.py")
            break
        else:
            print(f"✓ {num_players}p: {', '.join(bot_types)} - OK ({hands_completed} hands)")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
