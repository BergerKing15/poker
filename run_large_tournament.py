#!/usr/bin/env python3
"""
Run a very large tournament with diverse bot combinations.
Designed to take ~5 minutes with progress updates every 15 seconds.
"""

import sys
sys.path.insert(0, '/home/noahberg/Projects/PokerAI')

from bot_tourney import BotTournament

def main():
    print("\n" + "="*80)
    print("LARGE TOURNAMENT - ~5 MINUTE RUN")
    print("="*80)
    
    # Create diverse tournament config
    configs = [
        # Fast heads-up games (simple bots)
        {"num_players": 2, "bot_types": ["Random", "CheckCall"], "repeat": 20},
        {"num_players": 2, "bot_types": ["Random", "AllIn"], "repeat": 15},
        {"num_players": 2, "bot_types": ["CheckCall", "AllIn"], "repeat": 15},
        {"num_players": 2, "bot_types": ["Random", "NeverFold"], "repeat": 10},
        
        # Medium speed: 3-player games with simple bots
        {"num_players": 3, "bot_types": ["Random", "CheckCall", "AllIn"], "repeat": 12},
        {"num_players": 3, "bot_types": ["Random", "Random", "CheckCall"], "repeat": 12},
        {"num_players": 3, "bot_types": ["AllIn", "NeverFold", "CheckCall"], "repeat": 10},
        
        # 4-player simple bot games
        {"num_players": 4, "bot_types": ["Random", "CheckCall", "AllIn", "NeverFold"], "repeat": 10},
        {"num_players": 4, "bot_types": ["Random", "Random", "CheckCall", "AllIn"], "repeat": 8},
        
        # AI bots heads-up (slower but important data)
        {"num_players": 2, "bot_types": ["TAG", "FISH"], "repeat": 8},
        {"num_players": 2, "bot_types": ["LAG", "NIT"], "repeat": 8},
        {"num_players": 2, "bot_types": ["CTR", "TAG"], "repeat": 6},
        
        # Mixed AI and simple
        {"num_players": 3, "bot_types": ["TAG", "Random", "CheckCall"], "repeat": 6},
        {"num_players": 3, "bot_types": ["LAG", "AllIn", "NeverFold"], "repeat": 5},
        
        # 6-player mixed
        {"num_players": 6, "bot_types": ["Random", "CheckCall", "AllIn", "NeverFold", "Random", "CheckCall"], "repeat": 4},
        {"num_players": 6, "bot_types": ["TAG", "LAG", "NIT", "FISH", "Random", "CheckCall"], "repeat": 3},
    ]
    
    total_games = sum(cfg.get("repeat", 1) for cfg in configs)
    print(f"\nTournament Details:")
    print(f"  Total games to play: {total_games}")
    print(f"  Configurations: {len(configs)}")
    print(f"  Expected duration: ~5 minutes")
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
