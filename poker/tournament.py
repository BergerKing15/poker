#!/usr/bin/env python3
"""
Bot Tournament Runner - Runs thousands of hands to compare bot strategies
Generates ML training data and performance statistics
"""

from poker.console import enable_utf8_output

import json
import time
import threading
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any
from poker.game import PokerGame, Player
from poker.hand_log import HandLog
from poker.bot import (
    PokerBot, SimpleBotTop10Percent, SimpleBotAlwaysAllIn,
    SimpleBotCheckCall, SimpleBotRandom, SimpleBotNeverFold,
    SimpleBotAlwaysRaise, SimpleBotBottom50Percent, SimpleBotNeverBet,
    SimpleBotLimper, SimpleBotFolder, SimpleBotPositionBased, SimpleBotStackBased
)


class ProgressTracker:
    """Non-blocking progress tracker for tournament"""
    def __init__(self, total_games, total_hands_estimate, update_interval=5):
        self.total_games = total_games
        self.total_hands_estimate = total_hands_estimate
        self.update_interval = update_interval
        
        self.games_completed = 0
        self.hands_completed = 0
        self.start_time = time.time()
        self.last_update = self.start_time
        self.lock = threading.Lock()
        self.running = True
        
        # Start background thread for periodic status
        self.thread = threading.Thread(target=self._print_status, daemon=True)
        self.thread.start()
    
    def update(self, games=0, hands=0):
        """Update progress (thread-safe)"""
        with self.lock:
            self.games_completed += games
            self.hands_completed += hands
    
    def _print_status(self):
        """Periodically print status (runs in background thread)"""
        while self.running:
            with self.lock:
                elapsed = time.time() - self.start_time
                now = time.time()
                
                # Print every update_interval seconds
                if now - self.last_update >= self.update_interval:
                    games = self.games_completed
                    hands = self.hands_completed
                    self.last_update = now
                    
                    # Calculate rates
                    if elapsed > 0:
                        games_per_sec = games / elapsed
                        hands_per_sec = hands / elapsed
                        
                        # Estimate remaining time
                        remaining_games = self.total_games - games
                        remaining_hands = self.total_hands_estimate - hands
                        
                        if games_per_sec > 0:
                            eta_games = remaining_games / games_per_sec
                        else:
                            eta_games = 0
                        
                        # Print status
                        print(f"  ⏱ [{games}/{self.total_games} games | {hands} hands] "
                              f"({games_per_sec:.1f} g/s, {hands_per_sec:.0f} h/s) "
                              f"ETA: {eta_games:.0f}s ({eta_games//60:.0f}m)")
            
            time.sleep(0.1)  # Check frequently but don't consume CPU
    
    def stop(self):
        """Stop the progress tracker"""
        self.running = False
        self.thread.join(timeout=1)


class BotTournament:
    """Runs multiple poker games and tracks statistics"""
    
    # Bot factory for creating bots by type string
    BOT_FACTORY = {
        "TAG": lambda pid: PokerBot(pid, "TAG"),
        "LAG": lambda pid: PokerBot(pid, "LAG"),
        "CTR": lambda pid: PokerBot(pid, "CTR"),
        "NIT": lambda pid: PokerBot(pid, "NIT"),
        "FISH": lambda pid: PokerBot(pid, "FISH"),
        "Top10%": lambda pid: SimpleBotTop10Percent(pid),
        "AllIn": lambda pid: SimpleBotAlwaysAllIn(pid),
        "CheckCall": lambda pid: SimpleBotCheckCall(pid),
        "Random": lambda pid: SimpleBotRandom(pid),
        "NeverFold": lambda pid: SimpleBotNeverFold(pid),
        "AlwaysRaise": lambda pid: SimpleBotAlwaysRaise(pid),
        "Bottom50%": lambda pid: SimpleBotBottom50Percent(pid),
        "NeverBet": lambda pid: SimpleBotNeverBet(pid),
        "Limper": lambda pid: SimpleBotLimper(pid),
        "Folder": lambda pid: SimpleBotFolder(pid),
        "PositionBased": lambda pid: SimpleBotPositionBased(pid),
        "StackBased": lambda pid: SimpleBotStackBased(pid),
    }
    
    def __init__(self):
        self.stats: Dict[str, Dict[str, Any]] = {}
    
    def run_tournament(self, config_list, hands_per_game=100, verbose=True,
                       fast_mode=False, update_interval=5, hand_log_path=None):
        """
        Run tournament with specified bot configurations
        
        Args:
            config_list: List of {num_players, bot_types, repeat_count}
                        Example: [{"num_players": 3, "bot_types": ["TAG", "FISH", "LAG"], "repeat": 20}]
            hands_per_game: Number of hands per game
            verbose: Print progress
            fast_mode: Use only simple bots (no AI calculations, much faster for testing)
            update_interval: Progress update interval in seconds (default: 5)
            hand_log_path: If given, record every hand to this SQLite file for
                later analysis. Runs accumulate rather than overwriting.
        """
        self.hand_log = HandLog(hand_log_path, label="tournament") if hand_log_path else None
        # Fast mode: only allow simple bot types
        SIMPLE_BOTS = {"Random", "CheckCall", "AllIn", "NeverFold", "AlwaysRaise", "Bottom50%", "NeverBet", "Limper", "Folder"}
        if fast_mode:
            config_list = [
                {**cfg, "bot_types": [b if b in SIMPLE_BOTS else "Random" for b in cfg["bot_types"]]}
                for cfg in config_list
            ]
        
        start_time = time.time()
        total_games = sum(cfg.get("repeat", 1) for cfg in config_list)
        total_hands_estimate = total_games * hands_per_game
        games_completed = 0
        
        # Start progress tracker
        progress_tracker = ProgressTracker(total_games, total_hands_estimate, update_interval=update_interval)
        
        try:
            for config in config_list:
                num_players = config["num_players"]
                bot_types = config["bot_types"]
                repeat = config.get("repeat", 1)
                
                if verbose:
                    print(f"\nRunning {repeat} games: {num_players} players")
                    print(f"  Bots: {', '.join(bot_types)}")
                
                for game_num in range(repeat):
                    games_completed += 1
                    progress = f"[{games_completed}/{total_games}]"
                    
                    if verbose:
                        game_desc = f"{num_players}p: {', '.join(bot_types)}"
                        print(f"  {progress} Starting game: {game_desc}...", end='', flush=True)
                    
                    initial_stacks = {i: 1000 for i in range(num_players)}
                    game_start = time.time()
                    game_stats = self._run_single_game(
                        num_players, bot_types, hands_per_game, initial_stacks
                    )
                    game_elapsed = time.time() - game_start
                    
                    if verbose:
                        hands_this_game = game_stats[list(game_stats.keys())[0]]["hands"] if game_stats else 0
                        print(f" [{hands_this_game} hands in {game_elapsed:.1f}s]")
                    
                    # Update progress tracker
                    hands_this_game = game_stats[list(game_stats.keys())[0]]["hands"] if game_stats else hands_per_game
                    progress_tracker.update(games=1, hands=hands_this_game)
                    
                    # Update stats
                    for bot_type, stats_dict in game_stats.items():
                        if bot_type not in self.stats:
                            self.stats[bot_type] = {
                                "games_played": 0,
                                "hands_played": 0,
                                "wins": 0,
                                "total_gain": 0,
                                "final_stacks": [],
                                "matchups": {},
                            }
                        
                        # Count number of instances of this bot type in this game
                        num_instances = len(stats_dict["final_stacks"])
                        
                        # Add 1/num_instances to games_played (each instance counts as partial game)
                        self.stats[bot_type]["games_played"] += 1
                        self.stats[bot_type]["hands_played"] += stats_dict["hands"]
                        self.stats[bot_type]["wins"] += stats_dict["wins"]
                        
                        # Sum all stack changes for all instances in this game
                        total_change = sum(stats_dict["stack_changes"])
                        self.stats[bot_type]["total_gain"] += total_change
                        
                        # Store all individual stacks for averaging
                        self.stats[bot_type]["final_stacks"].extend(stats_dict["final_stacks"])
                        
                        # Track matchup
                        for opponent in game_stats.keys():
                            if opponent != bot_type:
                                if opponent not in self.stats[bot_type]["matchups"]:
                                    self.stats[bot_type]["matchups"][opponent] = {"games": 0, "wins": 0}
                                self.stats[bot_type]["matchups"][opponent]["games"] += 1
                    
                    if verbose and (game_num + 1) % 10 == 0:
                        print(f"  {progress} - {game_num + 1}/{repeat} games completed")
        except Exception as e:
            if verbose:
                print(f"\n⚠ Tournament interrupted at game {games_completed}/{total_games}")
                print(f"Error: {type(e).__name__}: {e}")
        finally:
            progress_tracker.stop()
        
        elapsed = time.time() - start_time
        if verbose:
            print(f"\nTournament complete! ({elapsed:.1f}s)")
            print(f"Games completed: {games_completed} / {total_games}")
        
        return self.get_summary()
    
    def _run_single_game(self, num_players, bot_types, hands_to_play, initial_stacks):
        """Run a single multi-hand game"""
        # Create game
        hand_log = getattr(self, "hand_log", None)
        game = PokerGame(
            num_players=num_players,
            starting_stack=1000,
            small_blind=5,
            big_blind=10,
            use_bots=True,  # Enable bots so AI decisions are used
            observer=hand_log,  # None keeps the default no-op observer
        )
        if hand_log is not None:
            # Label seats by configured type, not by the bot's own name, so the
            # log groups the same way the summary does.
            hand_log.bot_types = {i: bot_types[i % len(bot_types)]
                                  for i in range(num_players)}
        
        # Replace players with bots
        game.bots = {}
        for i in range(num_players):
            bot_type = bot_types[i % len(bot_types)]
            if bot_type in self.BOT_FACTORY:
                game.bots[i] = self.BOT_FACTORY[bot_type](i)
            else:
                game.bots[i] = PokerBot(i, bot_type)
        
        # Track stats per bot type
        bot_stats: Dict[str, Dict[str, Any]] = {}
        
        # Assign bot types to players
        bot_type_map = {}
        for i in range(num_players):
            bot_type = bot_types[i % len(bot_types)]
            bot_type_map[i] = bot_type
            if bot_type not in bot_stats:
                bot_stats[bot_type] = {
                    "hands": 0,
                    "wins": 0,
                    "final_stacks": [],  # List to store stacks for each instance
                    "stack_changes": [],  # List to store changes for each instance
                    "player_ids": [],
                }
            bot_stats[bot_type]["player_ids"].append(i)
        
        # Play hands with timeout protection
        hand_start_time = time.time()
        max_time_per_hand = 10  # seconds
        hands_played = 0
        try:
            for hand_num in range(hands_to_play):
                # Check if a single hand is taking too long
                hand_elapsed = time.time() - hand_start_time
                if hand_elapsed > max_time_per_hand:
                    print(f"\n⚠ Hand #{hand_num} taking too long ({hand_elapsed:.1f}s) - aborting game")
                    break
                
                hand_start_time = time.time()
                try:
                    game.play_hand()
                    hands_played += 1
                except Exception as hand_error:
                    # Single hand failed - log and continue
                    print(f"\n⚠ Hand #{hand_num} error: {type(hand_error).__name__} - continuing")
                    break
                
                # Update hand count
                for bot_type in bot_stats.keys():
                    bot_stats[bot_type]["hands"] += 1
        except KeyboardInterrupt:
            print(f"\n⚠ Game interrupted after {hands_played} hands")
            raise
        
        # Determine results
        for i in range(num_players):
            bot_type = bot_type_map[i]
            final_stack = game.players[i].stack
            bot_stats[bot_type]["final_stacks"].append(final_stack)  # Append to list
            bot_stats[bot_type]["stack_changes"].append(final_stack - 1000)  # Append to list
        
        # Count wins (who has most chips)
        winner_id = max(range(num_players), key=lambda i: game.players[i].stack)
        winner_type = bot_type_map[winner_id]
        bot_stats[winner_type]["wins"] += 1
        
        # Explicit cleanup - clear bots and game references
        if hasattr(game, 'deck') and game.deck:
            game.deck.cards.clear()
            game.deck = None
        game.bots.clear()
        game.players.clear()
        game.community_cards.clear()
        del game
        
        # Force garbage collection periodically
        import gc
        gc.collect()
        
        return bot_stats
    
    def get_summary(self):
        """Return summary statistics"""
        summary = {}
        
        for bot_type, stats_dict in self.stats.items():
            games = stats_dict["games_played"]
            hands = stats_dict["hands_played"]
            
            if games == 0:
                continue
            
            win_rate = stats_dict["wins"] / games * 100
            avg_gain = stats_dict["total_gain"] / games
            avg_stack = sum(stats_dict["final_stacks"]) / len(stats_dict["final_stacks"]) if stats_dict["final_stacks"] else 0
            
            summary[bot_type] = {
                "games_played": games,
                "hands_played": hands,
                "wins": stats_dict["wins"],
                "win_rate": f"{win_rate:.1f}%",
                "avg_stack": f"${avg_stack:.0f}",
                "total_gain": f"${stats_dict['total_gain']:.0f}",
                "avg_gain_per_game": f"${avg_gain:.0f}",
                "hands_per_game": f"{hands / games:.1f}",
            }
        
        return summary
    
    def print_summary(self):
        """Print formatted summary"""
        summary = self.get_summary()
        
        print("\n" + "=" * 110)
        print("TOURNAMENT RESULTS SUMMARY")
        print("=" * 110)
        
        # Sort by win rate
        sorted_stats = sorted(
            summary.items(),
            key=lambda x: float(x[1]["win_rate"].rstrip("%")),
            reverse=True
        )
        
        header = f"{'Bot Type':<15} {'Games':<8} {'Wins':<8} {'Win %':<10} {'Avg Stack':<13} {'Avg Gain':<12} {'Hands/Game':<12}"
        print(header)
        print("-" * 110)
        
        for bot_type, stats in sorted_stats:
            line = f"{bot_type:<15} {stats['games_played']:<8} {stats['wins']:<8} {stats['win_rate']:<10} {stats['avg_stack']:<13} {stats['avg_gain_per_game']:<12} {stats['hands_per_game']:<12}"
            print(line)
        
        print("=" * 110)
    
    def save_results(self, filename="tournament_results.json"):
        """Save results to JSON for analysis"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "stats": {
                bot_type: {
                    "games_played": stats_dict["games_played"],
                    "hands_played": stats_dict["hands_played"],
                    "wins": stats_dict["wins"],
                    "total_gain": stats_dict["total_gain"],
                    "final_stacks": stats_dict["final_stacks"],
                }
                for bot_type, stats_dict in self.stats.items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {filename}")


def main():
    """Run comprehensive bot tournament"""
    
    print("Initializing Bot Tournament Runner...")
    print("=" * 100)
    print("\nBot Types Available:")
    print("\n  AI Bots (Game Theory Based):")
    print("    - TAG: Tight Aggressive (pro style)")
    print("    - LAG: Loose Aggressive")
    print("    - CTR: Call-Fold (passive)")
    print("    - NIT: Nitty (super tight)")
    print("    - FISH: Loose-Passive (weak player)")
    print("\n  Simple Strategy Bots (Baseline & ML Training):")
    print("    - Top10%: Only plays top 10% hands pre-flop")
    print("    - AllIn: Always goes all-in")
    print("    - CheckCall: Always checks or calls")
    print("    - NeverFold: Never folds, always calls or raises")
    print("    - AlwaysRaise: Always raises pre-flop, calls post-flop")
    print("    - Bottom50%: Only plays worst 50% of hands")
    print("    - NeverBet: Folds most hands, only calls premium")
    print("    - Limper: Always limps/calls, never raises")
    print("    - Folder: Folds almost everything (~95% fold rate)")
    print("    - PositionBased: Plays position-based hand selection")
    print("    - StackBased: Adjusts strategy based on stack depth")
    print("    - Random: Plays completely randomly")
    print("\n" + "=" * 100 + "\n")
    
    # Comprehensive test configurations with all bot types
    configs = [
        # AI vs Baseline Heads-up
        {"num_players": 2, "bot_types": ["TAG", "Top10%"], "repeat": 20},
        {"num_players": 2, "bot_types": ["TAG", "AllIn"], "repeat": 20},
        {"num_players": 2, "bot_types": ["LAG", "NeverFold"], "repeat": 20},
        {"num_players": 2, "bot_types": ["LAG", "Folder"], "repeat": 20},
        {"num_players": 2, "bot_types": ["FISH", "Bottom50%"], "repeat": 20},
        
        # Simple vs Simple Heads-up (exploitability tests)
        {"num_players": 2, "bot_types": ["NeverFold", "NeverBet"], "repeat": 20},
        {"num_players": 2, "bot_types": ["AlwaysRaise", "CheckCall"], "repeat": 20},
        {"num_players": 2, "bot_types": ["AllIn", "AllIn"], "repeat": 20},
        {"num_players": 2, "bot_types": ["Limper", "PositionBased"], "repeat": 20},
        {"num_players": 2, "bot_types": ["StackBased", "Random"], "repeat": 20},
        
        # 3-player mixed games
        {"num_players": 3, "bot_types": ["TAG", "LAG", "FISH"], "repeat": 15},
        {"num_players": 3, "bot_types": ["Top10%", "Bottom50%", "NeverFold"], "repeat": 15},
        {"num_players": 3, "bot_types": ["Folder", "AlwaysRaise", "CheckCall"], "repeat": 15},
        {"num_players": 3, "bot_types": ["PositionBased", "StackBased", "Random"], "repeat": 15},
        
        # 4-player games
        {"num_players": 4, "bot_types": ["TAG", "LAG", "CTR", "FISH"], "repeat": 12},
        {"num_players": 4, "bot_types": ["Top10%", "Bottom50%", "NeverBet", "AllIn"], "repeat": 12},
        {"num_players": 4, "bot_types": ["NeverFold", "Limper", "Folder", "AlwaysRaise"], "repeat": 12},
        
        # 6-player games
        {"num_players": 6, "bot_types": ["TAG", "LAG", "NIT", "CTR", "FISH", "Top10%"], "repeat": 10},
        {"num_players": 6, "bot_types": ["AllIn", "CheckCall", "NeverFold", "Folder", "PositionBased", "StackBased"], "repeat": 10},
        {"num_players": 6, "bot_types": ["Random", "NeverBet", "AlwaysRaise", "Bottom50%", "Limper", "TAG"], "repeat": 10},
        
        # 9-player games (full table)
        {"num_players": 9, 
         "bot_types": ["TAG", "LAG", "CTR", "NIT", "FISH", "Top10%", "AllIn", "CheckCall", "Random"],
         "repeat": 8},
        {"num_players": 9,
         "bot_types": ["NeverFold", "AlwaysRaise", "Bottom50%", "NeverBet", "Limper", "Folder", "PositionBased", "StackBased", "Random"],
         "repeat": 8},
    ]
    
    tournament = BotTournament()
    tournament.run_tournament(configs, hands_per_game=50, verbose=True)
    tournament.print_summary()
    tournament.save_results("tournament_results.json")


def main_with_ui():
    """Run tournament with real-time analytics UI"""
    import sys
    
    configs = [
        # AI vs Baseline Heads-up
        {"num_players": 2, "bot_types": ["TAG", "Top10%"], "repeat": 20},
        {"num_players": 2, "bot_types": ["TAG", "AllIn"], "repeat": 20},
        {"num_players": 2, "bot_types": ["LAG", "NeverFold"], "repeat": 20},
        {"num_players": 2, "bot_types": ["LAG", "Folder"], "repeat": 20},
        {"num_players": 2, "bot_types": ["FISH", "Bottom50%"], "repeat": 20},
        
        # Simple vs Simple Heads-up (exploitability tests)
        {"num_players": 2, "bot_types": ["NeverFold", "NeverBet"], "repeat": 20},
        {"num_players": 2, "bot_types": ["AlwaysRaise", "CheckCall"], "repeat": 20},
        {"num_players": 2, "bot_types": ["AllIn", "AllIn"], "repeat": 20},
        {"num_players": 2, "bot_types": ["Limper", "PositionBased"], "repeat": 20},
        {"num_players": 2, "bot_types": ["StackBased", "Random"], "repeat": 20},
        
        # 3-player mixed games
        {"num_players": 3, "bot_types": ["TAG", "LAG", "FISH"], "repeat": 15},
        {"num_players": 3, "bot_types": ["Top10%", "Bottom50%", "NeverFold"], "repeat": 15},
        {"num_players": 3, "bot_types": ["Folder", "AlwaysRaise", "CheckCall"], "repeat": 15},
        {"num_players": 3, "bot_types": ["PositionBased", "StackBased", "Random"], "repeat": 15},
        
        # 4-player games
        {"num_players": 4, "bot_types": ["TAG", "LAG", "CTR", "FISH"], "repeat": 12},
        {"num_players": 4, "bot_types": ["Top10%", "Bottom50%", "NeverBet", "AllIn"], "repeat": 12},
        {"num_players": 4, "bot_types": ["NeverFold", "Limper", "Folder", "AlwaysRaise"], "repeat": 12},
        
        # 6-player games
        {"num_players": 6, "bot_types": ["TAG", "LAG", "NIT", "CTR", "FISH", "Top10%"], "repeat": 10},
        {"num_players": 6, "bot_types": ["AllIn", "CheckCall", "NeverFold", "Folder", "PositionBased", "StackBased"], "repeat": 10},
        {"num_players": 6, "bot_types": ["Random", "NeverBet", "AlwaysRaise", "Bottom50%", "Limper", "TAG"], "repeat": 10},
        
        # 9-player games (full table)
        {"num_players": 9, 
         "bot_types": ["TAG", "LAG", "CTR", "NIT", "FISH", "Top10%", "AllIn", "CheckCall", "Random"],
         "repeat": 8},
        {"num_players": 9,
         "bot_types": ["NeverFold", "AlwaysRaise", "Bottom50%", "NeverBet", "Limper", "Folder", "PositionBased", "StackBased", "Random"],
         "repeat": 8},
    ]
    
    try:
        from poker.ui.tournament_window import run_tournament_with_ui
        
        # Convert configs to list format for UI
        bot_configs = []
        for config in configs:
            for _ in range(config["repeat"]):
                bot_configs.append(config["bot_types"])
        
        print(f"Running tournament with UI ({len(bot_configs)} games total)...")
        results = run_tournament_with_ui(bot_configs, 1, small_blind=1, big_blind=2)
        
        print(f"\nTournament Complete: {results['games_completed']} games")
        
    except ImportError:
        print("Tkinter not available. Running without UI...")
        main()


if __name__ == "__main__":
    enable_utf8_output()
    import sys
    
    # Check for UI flag
    if "--ui" in sys.argv or "-ui" in sys.argv:
        main_with_ui()
    else:
        print("PokerAI Tournament Runner")
        print("=" * 80)
        print("Usage:")
        print("  python bot_tourney.py              # Run full tournament without UI")
        print("  python bot_tourney.py --ui         # Run with real-time analytics UI")
        print("  python bot_tourney.py --fast       # Fast mode (simple bots only, for testing)")
        print()
        print("For testing progress tracking without waiting:")
        print("  from bot_tourney import BotTournament")
        print("  t = BotTournament()")
        print("  config = [{\"num_players\": 2, \"bot_types\": [\"Random\", \"CheckCall\"],")
        print("             \"hands_per_game\": 20}] * 50")
        print("  t.run_tournament(config, fast_mode=True, verbose=True)")
        print()
        print("⏱ Progress tracker shows: games_completed | hands_played | speed (g/s, h/s) | ETA")
        print("=" * 80)
        print()
        
        if "--fast" in sys.argv:
            print("Running in FAST MODE (simple bots only)...")
            configs = [
                {"num_players": 2, "bot_types": ["Random", "CheckCall"], "repeat": 20},
                {"num_players": 3, "bot_types": ["Random", "CheckCall", "AllIn"], "repeat": 15},
                {"num_players": 4, "bot_types": ["Random", "CheckCall", "AllIn", "NeverFold"], "repeat": 10},
            ]
            tournament = BotTournament()
            tournament.run_tournament(configs, hands_per_game=20, verbose=True, fast_mode=True)
        else:
            main()
