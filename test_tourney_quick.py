"""Quick test of bot_tourney"""
from bot_tourney import BotTournament

# Small test
configs = [
    {"num_players": 2, "bot_types": ["TAG", "FISH"], "repeat": 2},
    {"num_players": 3, "bot_types": ["LAG", "Top10%", "AllIn"], "repeat": 2},
]

tournament = BotTournament()
tournament.run_tournament(configs, hands_per_game=10, verbose=True)
tournament.print_summary()
tournament.save_results("/tmp/test_results.json")

