
from poker.console import enable_utf8_output
import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime, timedelta


class TournamentAnalyticsUI:
    """Real-time tournament analytics dashboard"""
    
    def __init__(self, total_games, bot_names):
        self.window = tk.Tk()
        self.window.title("PokerAI Tournament Analytics")
        self.window.geometry("900x600")
        
        self.total_games = total_games
        self.bot_names = sorted(bot_names)
        self.games_completed = 0
        self.start_time = datetime.now()
        self.last_update = self.start_time
        
        # Stats tracking
        self.bot_stats = {bot: {"wins": 0, "games": 0, "hands": 0} for bot in self.bot_names}
        
        self._create_ui()
        self.is_running = True
    
    def _create_ui(self):
        """Create the UI layout"""
        # Title
        title_frame = tk.Frame(self.window, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            title_frame,
            text="PokerAI Tournament Analytics",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=10)
        
        # Progress frame
        progress_frame = tk.LabelFrame(
            self.window,
            text="Tournament Progress",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Games progress bar
        games_label = tk.Label(progress_frame, text="Games Completed:")
        games_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            maximum=self.total_games,
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_text = tk.Label(
            progress_frame,
            text=f"0 / {self.total_games} games (0%)",
            font=("Arial", 10)
        )
        self.progress_text.pack(anchor=tk.W)
        
        # Stats frame
        stats_label_frame = tk.LabelFrame(
            self.window,
            text="Bot Statistics",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        stats_label_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview for stats
        self.tree = ttk.Treeview(
            stats_label_frame,
            columns=("Wins", "Games", "Win Rate", "Hands", "Hands/Game"),
            height=15,
            show="tree headings"
        )
        
        # Define columns
        self.tree.column("#0", width=120, anchor=tk.W)
        self.tree.column("Wins", width=80, anchor=tk.CENTER)
        self.tree.column("Games", width=80, anchor=tk.CENTER)
        self.tree.column("Win Rate", width=100, anchor=tk.CENTER)
        self.tree.column("Hands", width=100, anchor=tk.CENTER)
        self.tree.column("Hands/Game", width=100, anchor=tk.CENTER)
        
        self.tree.heading("#0", text="Bot", anchor=tk.W)
        self.tree.heading("Wins", text="Wins")
        self.tree.heading("Games", text="Games")
        self.tree.heading("Win Rate", text="Win Rate")
        self.tree.heading("Hands", text="Hands")
        self.tree.heading("Hands/Game", text="Hands/Game")
        
        # Add rows for each bot
        for bot in self.bot_names:
            self.tree.insert("", tk.END, iid=bot, text=bot, values=("0", "0", "0%", "0", "0"))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(stats_label_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Info frame
        info_frame = tk.LabelFrame(
            self.window,
            text="Tournament Info",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.info_text = tk.Label(
            info_frame,
            text="Starting tournament...",
            font=("Arial", 9),
            justify=tk.LEFT
        )
        self.info_text.pack(anchor=tk.W)
    
    def update_progress(self, games_completed, bot_stats):
        """Update UI with current progress
        
        Args:
            games_completed: Number of games completed so far
            bot_stats: Dict of {bot_name: {wins, games, hands}}
        """
        self.games_completed = games_completed
        self.bot_stats = bot_stats.copy()
        self._refresh_ui()
    
    def _refresh_ui(self):
        """Refresh all UI elements with current data"""
        # Update progress bar
        progress = min(self.games_completed, self.total_games)
        self.progress_bar['value'] = progress
        
        percentage = (progress / self.total_games * 100) if self.total_games > 0 else 0
        self.progress_text.config(
            text=f"{progress} / {self.total_games} games ({percentage:.1f}%)"
        )
        
        # Update stats table
        for bot in self.bot_names:
            if bot in self.bot_stats:
                stats = self.bot_stats[bot]
                wins = stats.get("wins", 0)
                games = stats.get("games", 0)
                hands = stats.get("hands", 0)
                
                win_rate = (wins / games * 100) if games > 0 else 0
                hands_per_game = (hands / games) if games > 0 else 0
                
                values = (
                    str(wins),
                    str(games),
                    f"{win_rate:.1f}%",
                    str(hands),
                    f"{hands_per_game:.1f}"
                )
                
                self.tree.item(bot, values=values)
        
        # Update info
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"{int(elapsed.total_seconds() // 60)}:{int(elapsed.total_seconds() % 60):02d}"
        
        if self.games_completed > 0:
            avg_time_per_game = elapsed.total_seconds() / self.games_completed
            remaining_games = self.total_games - self.games_completed
            estimated_remaining = timedelta(seconds=avg_time_per_game * remaining_games)
            eta_str = f"{int(estimated_remaining.total_seconds() // 60)}:{int(estimated_remaining.total_seconds() % 60):02d}"
        else:
            eta_str = "calculating..."
        
        info = f"Elapsed: {elapsed_str} | ETA: {eta_str} | Status: Running..."
        self.info_text.config(text=info)
        
        self.window.update()
    
    def close(self):
        """Close the UI window"""
        self.is_running = False
        try:
            self.window.destroy()
        except:
            pass
    
    def show_completion(self):
        """Show tournament completion message"""
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"{int(elapsed.total_seconds() // 60)}:{int(elapsed.total_seconds() % 60):02d}"
        
        info = f"✓ Tournament Complete! | Total Time: {elapsed_str} | Games: {self.games_completed}"
        self.info_text.config(text=info, fg="green")
        
        # Keep window open for 5 seconds then close
        self.window.after(5000, self.close)


def run_tournament_with_ui(bot_configs, num_games_per_config, small_blind=1, big_blind=2):
    """Run tournament with real-time UI
    
    Args:
        bot_configs: List of game configurations (each is a list of bot names)
        num_games_per_config: Number of games to play for each configuration
        small_blind: Small blind amount
        big_blind: Big blind amount
    
    Returns:
        tournament_results: Dict with all game results
    """
    from poker.game import PokerGame
    from poker.bot import (
        PokerBot, SimpleBotTop10Percent, SimpleBotAlwaysAllIn,
        SimpleBotCheckCall, SimpleBotRandom, SimpleBotNeverFold,
        SimpleBotAlwaysRaise, SimpleBotBottom50Percent, SimpleBotNeverBet,
        SimpleBotLimper, SimpleBotFolder, SimpleBotPositionBased,
        SimpleBotStackBased
    )
    
    # Calculate total games
    total_games = len(bot_configs) * num_games_per_config
    
    # Get all unique bot names
    all_bots = set()
    for config in bot_configs:
        all_bots.update(config)
    
    # Create UI
    ui = TournamentAnalyticsUI(total_games, list(all_bots))
    
    # Bot factory - creates bots with player ID
    def create_bot_factory(player_id):
        factory = {
            'TAG': lambda: PokerBot(player_id, 'TAG'),
            'LAG': lambda: PokerBot(player_id, 'LAG'),
            'CTR': lambda: PokerBot(player_id, 'CTR'),
            'NIT': lambda: PokerBot(player_id, 'NIT'),
            'FISH': lambda: PokerBot(player_id, 'FISH'),
            'Top10%': lambda: SimpleBotTop10Percent(player_id),
            'AllIn': lambda: SimpleBotAlwaysAllIn(player_id),
            'CheckCall': lambda: SimpleBotCheckCall(player_id),
            'Random': lambda: SimpleBotRandom(player_id),
            'NeverFold': lambda: SimpleBotNeverFold(player_id),
            'AlwaysRaise': lambda: SimpleBotAlwaysRaise(player_id),
            'Bottom50%': lambda: SimpleBotBottom50Percent(player_id),
            'NeverBet': lambda: SimpleBotNeverBet(player_id),
            'Limper': lambda: SimpleBotLimper(player_id),
            'Folder': lambda: SimpleBotFolder(player_id),
            'PositionBased': lambda: SimpleBotPositionBased(player_id),
            'StackBased': lambda: SimpleBotStackBased(player_id),
        }
        return factory
    
    # Track stats
    bot_stats = {bot: {"wins": 0, "games": 0, "hands": 0} for bot in all_bots}
    games_completed = 0
    all_games = []
    update_frequency = 5  # Update UI every 5 games instead of every game
    
    try:
        # Run games
        for config_idx, bot_config in enumerate(bot_configs):
            for game_num in range(num_games_per_config):
                if not ui.is_running:
                    break
                
                # Create game
                num_players = len(bot_config)
                BOT_FACTORY = create_bot_factory(0)  # Will create factories for each player
                bot_types = {}
                for i, bot_name in enumerate(bot_config):
                    player_name = f"Player {i+1}"
                    BOT_FACTORY_FOR_PLAYER = create_bot_factory(i)
                    bot_types[player_name] = BOT_FACTORY_FOR_PLAYER[bot_name]()
                
                game = PokerGame(
                    num_players=num_players,
                    starting_stack=1000,
                    small_blind=small_blind,
                    big_blind=big_blind,
                    bot_types=bot_types
                )
                
                # Play hands
                hands_played = 0
                try:
                    for _ in range(50):  # Play up to 50 hands
                        game.play_hand()
                        hands_played += 1
                except Exception:
                    # Game ended (someone busted out)
                    pass
                
                # Record results
                winner_idx = 0
                max_stack = max(p.stack for p in game.players)
                for i, player in enumerate(game.players):
                    if player.stack == max_stack:
                        winner_idx = i
                        break
                
                winner_name = bot_config[winner_idx]
                bot_stats[winner_name]["wins"] += 1
                
                # Update all bot stats for this game
                for bot_name in bot_config:
                    bot_stats[bot_name]["games"] += 1
                    bot_stats[bot_name]["hands"] += hands_played
                
                games_completed += 1
                
                # Update UI (batched - every 5 games)
                if games_completed % update_frequency == 0 or games_completed == total_games:
                    ui.update_progress(games_completed, bot_stats)
            
            if not ui.is_running:
                break
        
        # Show completion
        ui.show_completion()
        
        # Keep window open
        ui.window.mainloop()
        
    except Exception as e:
        print(f"Error during tournament: {e}")
        ui.close()
        raise
    
    return {
        'games_completed': games_completed,
        'bot_stats': bot_stats,
        'total_games': total_games
    }


if __name__ == "__main__":
    enable_utf8_output()
    # Example usage
    from poker.tournament import get_tournament_configs
    
    configs = get_tournament_configs()
    results = run_tournament_with_ui(configs, 20)
    print(f"Tournament completed: {results['games_completed']} / {results['total_games']} games")
