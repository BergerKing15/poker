#!/usr/bin/env python3
"""
Run a large tournament with simple bots only (no AI).
Designed to take ~2-3 minutes and complete without hangs.
"""

import sys
sys.path.insert(0, '/home/noahberg/Projects/PokerAI')

from poker.tournament import BotTournament

def main():
    print("\n" + "="*80)
    print("LARGE TOURNAMENT - SIMPLE BOTS ONLY (NO AI)")
    print("="*80)
    
    # Create diverse tournament config with SIMPLE BOTS ONLY
    configs = [
        # Heads-up games - very fast
        {"num_players": 2, "bot_types": ["Random", "CheckCall"], "repeat": 30},
        {"num_players": 2, "bot_types": ["Random", "AllIn"], "repeat": 25},
        {"num_players": 2, "bot_types": ["CheckCall", "AllIn"], "repeat": 20},
        {"num_players": 2, "bot_types": ["Random", "NeverFold"], "repeat": 15},
        {"num_players": 2, "bot_types": ["CheckCall", "CheckCall"], "repeat": 15},
        
        # 3-player games - fast
        {"num_players": 3, "bot_types": ["Random", "CheckCall", "AllIn"], "repeat": 15},
        {"num_players": 3, "bot_types": ["Random", "Random", "CheckCall"], "repeat": 15},
        {"num_players": 3, "bot_types": ["AllIn", "NeverFold", "CheckCall"], "repeat": 12},
        
        # 4-player games - medium speed
        {"num_players": 4, "bot_types": ["Random", "CheckCall", "AllIn", "NeverFold"], "repeat": 12},
        {"num_players": 4, "bot_types": ["Random", "Random", "CheckCall", "AllIn"], "repeat": 10},
        
        # 6-player games - still fast enough
        {"num_players": 6, "bot_types": ["Random", "CheckCall", "AllIn", "NeverFold", "Random", "CheckCall"], "repeat": 8},
        {"num_players": 6, "bot_types": ["CheckCall", "CheckCall", "AllIn", "AllIn", "NeverFold", "NeverFold"], "repeat": 6},
        
        # 9-player game
        {"num_players": 9, "bot_types": ["Random", "CheckCall", "AllIn", "NeverFold", "Random", "CheckCall", "AllIn", "NeverFold", "Random"], "repeat": 2},
    ]
    
    total_games = sum(cfg.get("repeat", 1) for cfg in configs)
    print(f"\nTournament Details:")
    print(f"  Total games to play: {total_games}")
    print(f"  Configurations: {len(configs)}")
    print(f"  Bot types: Random, CheckCall, AllIn, NeverFold (SIMPLE ONLY - NO AI)")
    print(f"  Expected duration: ~2-3 minutes")
    print(f"  Progress updates: Every 15 seconds")
    print(f"  Hands per game: 15 (for speed)")
    print("\n" + "="*80 + "\n")
    
    # Run tournament with 15-second update interval
    tournament = BotTournament()
    tournament.run_tournament(
        configs, 
        hands_per_game=15, 
        verbose=True,
        update_interval=15  # Update every 15 seconds
    )
    
    # Print summary
    summary = tournament.get_summary()
    
    print("\n" + "="*80)
    print("TOURNAMENT SUMMARY")
    print("="*80)
    print(f"\nTop 5 Performers by Win Rate:\n")
    
    # Sort by win rate
    ranked = sorted(
        summary.items(),
        key=lambda x: float(x[1]['win_rate'].rstrip('%')),
        reverse=True
    )
    
    for rank, (bot_type, stats) in enumerate(ranked[:5], 1):
        print(f"{rank}. {bot_type:15} | Games: {stats['games_played']:3} | "
              f"Wins: {stats['wins']:3} | Win Rate: {stats['win_rate']:>6} | "
              f"Avg Gain: {stats['avg_gain_per_game']:>8}")
    
    print(f"\nBottom 5 Performers by Win Rate:\n")
    for rank, (bot_type, stats) in enumerate(ranked[-5:], 1):
        print(f"{len(ranked)-5+rank}. {bot_type:15} | Games: {stats['games_played']:3} | "
              f"Wins: {stats['wins']:3} | Win Rate: {stats['win_rate']:>6} | "
              f"Avg Gain: {stats['avg_gain_per_game']:>8}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
