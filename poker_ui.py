import tkinter as tk
from tkinter import ttk, messagebox
import threading
from poker_game import PokerGame

class PokerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Texas Hold'em Poker")
        self.root.geometry("1000x700")
        self.root.configure(bg="#2d5016")
        
        self.game = None
        self.game_running = False
        self.current_player_action = None
        self.game_thread = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI"""
        # Setup screen
        self.setup_screen = ttk.Frame(self.root)
        self.setup_screen.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(self.setup_screen, text="Texas Hold'em Poker Setup", 
                  font=("Arial", 20, "bold")).pack(pady=20)
        
        # Number of opponents
        frame1 = ttk.Frame(self.setup_screen)
        frame1.pack(pady=10)
        ttk.Label(frame1, text="AI Opponents (1-5):").pack(side=tk.LEFT, padx=5)
        self.opponents_var = tk.StringVar(value="2")
        ttk.Spinbox(frame1, from_=1, to=5, textvariable=self.opponents_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Starting stack
        frame2 = ttk.Frame(self.setup_screen)
        frame2.pack(pady=10)
        ttk.Label(frame2, text="Starting Stack ($):").pack(side=tk.LEFT, padx=5)
        self.stack_var = tk.StringVar(value="1000")
        ttk.Spinbox(frame2, from_=100, to=10000, textvariable=self.stack_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Number of hands
        frame3 = ttk.Frame(self.setup_screen)
        frame3.pack(pady=10)
        ttk.Label(frame3, text="Hands to Play:").pack(side=tk.LEFT, padx=5)
        self.hands_var = tk.StringVar(value="5")
        ttk.Spinbox(frame3, from_=1, to=100, textvariable=self.hands_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Start button
        ttk.Button(self.setup_screen, text="Start Game", command=self.start_game).pack(pady=20)
        
        # Game screen
        self.game_screen = ttk.Frame(self.root)
        
        # Title
        self.title_label = ttk.Label(self.game_screen, text="", font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)
        
        # Community cards
        community_frame = ttk.LabelFrame(self.game_screen, text="Community Cards")
        community_frame.pack(pady=10, padx=10, fill=tk.X)
        self.community_label = ttk.Label(community_frame, text="", font=("Arial", 12))
        self.community_label.pack(pady=5)
        
        # Pot
        self.pot_label = ttk.Label(self.game_screen, text="", font=("Arial", 14, "bold"), foreground="gold")
        self.pot_label.pack(pady=5)
        
        # Players info
        players_frame = ttk.LabelFrame(self.game_screen, text="Players")
        players_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.players_text = tk.Text(players_frame, height=10, width=80, state=tk.DISABLED)
        self.players_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Your hand
        your_hand_frame = ttk.LabelFrame(self.game_screen, text="Your Hand")
        your_hand_frame.pack(pady=10, padx=10, fill=tk.X)
        self.your_hand_label = ttk.Label(your_hand_frame, text="", font=("Arial", 12))
        self.your_hand_label.pack(pady=5)
        
        # Action frame
        action_frame = ttk.LabelFrame(self.game_screen, text="Your Action")
        action_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.action_info_label = ttk.Label(action_frame, text="", font=("Arial", 11))
        self.action_info_label.pack(pady=5)
        
        buttons_frame = ttk.Frame(action_frame)
        buttons_frame.pack(pady=10)
        
        ttk.Button(buttons_frame, text="Check", command=lambda: self.player_action("check")).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Call", command=lambda: self.player_action("call")).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Raise", command=self.raise_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Fold", command=lambda: self.player_action("fold")).pack(side=tk.LEFT, padx=5)
        
        # Message label
        self.message_label = ttk.Label(self.game_screen, text="", font=("Arial", 10))
        self.message_label.pack(pady=5)
        
    def start_game(self):
        """Start a new game"""
        try:
            num_opponents = int(self.opponents_var.get())
            starting_stack = int(self.stack_var.get())
            num_hands = int(self.hands_var.get())
            
            if num_opponents < 1 or num_opponents > 5:
                messagebox.showerror("Error", "Opponents must be 1-5")
                return
            
            self.game = PokerGame(
                num_players=num_opponents + 1,
                starting_stack=starting_stack,
                small_blind=5,
                big_blind=10
            )
            self.game.players[0].is_ai = False
            self.num_hands = num_hands
            self.current_hand = 0
            
            self.setup_screen.pack_forget()
            self.game_screen.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            self.game_running = True
            self.game_thread = threading.Thread(target=self.play_game_loop, daemon=True)
            self.game_thread.start()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid input")
    
    def play_game_loop(self):
        """Main game loop"""
        for hand_num in range(self.num_hands):
            if not self.game_running:
                break
            self.current_hand = hand_num + 1
            self.play_single_hand()
            self.root.after(1000)  # Brief pause between hands
        
        if self.game_running:
            self.show_final_results()
    
    def play_single_hand(self):
        """Play a single hand"""
        self.game.hand_number += 1
        
        # Reset player state
        for player in self.game.players:
            player.reset_for_new_hand()
        
        # Post blinds and deal
        self.game.post_blinds()
        self.game.deal_hole_cards()
        self.game.current_bet = self.game.big_blind
        self.game.community_cards = []
        
        self.update_display("Pre-Flop")
        self.betting_round("Pre-Flop")
        
        # Check if only one player remains
        active_players = [p for p in self.game.players if not p.is_folded]
        if len(active_players) == 1:
            self.game.determine_winner()
            self.game.button = (self.game.button + 1) % len(self.game.players)
            self.game.pot = 0
            self.update_display("Hand Over")
            return
        
        # Reset for next round
        for player in self.game.players:
            player.total_bet_this_round = 0
        self.game.current_bet = 0
        
        # Flop
        self.game.community_cards = self.game.deck.deal(3)
        self.update_display("Flop")
        self.betting_round("Flop")
        
        if len([p for p in self.game.players if not p.is_folded]) == 1:
            self.game.determine_winner()
            self.game.button = (self.game.button + 1) % len(self.game.players)
            self.game.pot = 0
            self.update_display("Hand Over")
            return
        
        # Reset for next round
        for player in self.game.players:
            player.total_bet_this_round = 0
        self.game.current_bet = 0
        
        # Turn
        self.game.community_cards += self.game.deck.deal(1)
        self.update_display("Turn")
        self.betting_round("Turn")
        
        if len([p for p in self.game.players if not p.is_folded]) == 1:
            self.game.determine_winner()
            self.game.button = (self.game.button + 1) % len(self.game.players)
            self.game.pot = 0
            self.update_display("Hand Over")
            return
        
        # Reset for next round
        for player in self.game.players:
            player.total_bet_this_round = 0
        self.game.current_bet = 0
        
        # River
        self.game.community_cards += self.game.deck.deal(1)
        self.update_display("River")
        self.betting_round("River")
        
        # Showdown
        self.game.determine_winner()
        self.game.button = (self.game.button + 1) % len(self.game.players)
        self.game.pot = 0
        self.update_display("Showdown")
    
    def betting_round(self, stage):
        """Execute a betting round"""
        active_players = [p for p in self.game.players if not p.is_folded and p.stack > 0]
        if len(active_players) <= 1:
            return
        
        if stage == "Pre-Flop":
            first_to_act = (self.game.button + 3) % len(self.game.players)
        else:
            first_to_act = (self.game.button + 1) % len(self.game.players)
        
        current_player_idx = first_to_act
        players_who_acted_this_level = set()
        
        while True:
            player = self.game.players[current_player_idx]
            
            if player.is_folded or player.stack == 0:
                current_player_idx = (current_player_idx + 1) % len(self.game.players)
                continue
            
            to_call = self.game.current_bet - player.total_bet_this_round
            
            if player.is_ai:
                if to_call == 0:
                    action = "check"
                else:
                    action = self.game.ai_decision(player, self.game.community_cards, self.game.current_bet, to_call)
            else:
                # Human player - wait for action
                self.current_player_action = None
                self.player_action_info = {
                    "to_call": to_call,
                    "stack": player.stack,
                    "pot": self.game.pot
                }
                self.update_display(f"{stage} - Waiting for your action")
                
                # Wait for player action
                while self.current_player_action is None and self.game_running:
                    self.root.update()
                
                if not self.game_running:
                    return
                
                action = self.current_player_action
            
            self.process_action(player, action, stage)
            players_who_acted_this_level.add(player.player_id)
            
            # Check if betting round is complete
            active_players = [p for p in self.game.players if not p.is_folded and p.stack > 0]
            if len(active_players) <= 1:
                break
            
            active_unfolded = [p for p in self.game.players if not p.is_folded]
            if len(active_unfolded) <= 1:
                break
            
            if all(p.player_id in players_who_acted_this_level for p in active_unfolded):
                all_matched = all(
                    p.total_bet_this_round == self.game.current_bet
                    for p in active_unfolded
                )
                if all_matched:
                    break
            
            current_player_idx = (current_player_idx + 1) % len(self.game.players)
            self.update_display(stage)
    
    def process_action(self, player, action, stage):
        """Process a player's action"""
        to_call = self.game.current_bet - player.total_bet_this_round
        
        if action == "fold":
            player.is_folded = True
            self.message_label.config(text=f"Player {player.player_id} folds")
        elif action == "call":
            if to_call > 0:
                bet_amount = min(to_call, player.stack)
                player.stack -= bet_amount
                player.total_bet_this_round += bet_amount
                self.game.pot += bet_amount
                self.message_label.config(text=f"Player {player.player_id} calls ${bet_amount}")
                self.game.current_bet = max(self.game.current_bet, player.total_bet_this_round)
        elif action == "raise":
            raise_amount = self.current_player_action if isinstance(self.current_player_action, int) else self.game.big_blind
            bet_amount = min(to_call + raise_amount, player.stack)
            player.stack -= bet_amount
            player.total_bet_this_round += bet_amount
            self.game.pot += bet_amount
            self.game.current_bet = player.total_bet_this_round
            self.message_label.config(text=f"Player {player.player_id} raises to ${player.total_bet_this_round}")
        elif action == "check":
            if to_call == 0:
                self.message_label.config(text=f"Player {player.player_id} checks")
    
    def player_action(self, action):
        """Handle player action button press"""
        if action in ["check", "call", "fold"]:
            self.current_player_action = action
        self.update_display("Executing action...")
    
    def raise_dialog(self):
        """Show dialog to ask for raise amount"""
        if not hasattr(self, 'player_action_info'):
            return
        
        max_raise = self.player_action_info["stack"] - self.player_action_info["to_call"]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Raise Amount")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Max raise: ${max_raise}", font=("Arial", 11)).pack(pady=10)
        
        raise_var = tk.StringVar(value=str(self.game.big_blind))
        ttk.Label(dialog, text="Raise amount ($):").pack(pady=5)
        ttk.Spinbox(dialog, from_=1, to=max_raise, textvariable=raise_var, width=15).pack(pady=5)
        
        def confirm_raise():
            try:
                amount = int(raise_var.get())
                if amount <= max_raise:
                    self.current_player_action = amount
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", f"Max raise is ${max_raise}")
            except ValueError:
                messagebox.showerror("Error", "Invalid amount")
        
        ttk.Button(dialog, text="Raise", command=confirm_raise).pack(pady=10)
    
    def update_display(self, stage=""):
        """Update the game display"""
        self.root.after(0, self._update_display, stage)
    
    def _update_display(self, stage):
        """Actually update the display"""
        if not self.game:
            return
        
        # Update title
        self.title_label.config(text=f"Hand #{self.game.hand_number} - {stage} | Hand {self.current_hand}/{self.num_hands}")
        
        # Update community cards
        if self.game.community_cards:
            cards_str = ", ".join(str(card) for card in self.game.community_cards)
            self.community_label.config(text=f"Cards: {cards_str}")
        else:
            self.community_label.config(text="No community cards yet")
        
        # Update pot
        self.pot_label.config(text=f"Pot: ${self.game.pot}")
        
        # Update players info
        players_info = "Player | Cards | Stack | Bet\n" + "-" * 40 + "\n"
        for i, player in enumerate(self.game.players):
            status = " (YOU)" if i == 0 else " (AI)"
            folded = " (FOLDED)" if player.is_folded else ""
            cards = f"{player.hole_cards}" if i == 0 else "Hidden"
            players_info += f"{i}{status}{folded} | {cards} | ${player.stack} | ${player.total_bet_this_round}\n"
        
        self.players_text.config(state=tk.NORMAL)
        self.players_text.delete(1.0, tk.END)
        self.players_text.insert(tk.END, players_info)
        self.players_text.config(state=tk.DISABLED)
        
        # Update your hand
        player = self.game.players[0]
        self.your_hand_label.config(text=f"Your cards: {player.hole_cards} | Stack: ${player.stack}")
        
        # Update action info
        if hasattr(self, 'player_action_info'):
            to_call = self.player_action_info["to_call"]
            self.action_info_label.config(
                text=f"To call: ${to_call} | Pot: ${self.player_action_info['pot']} | Your stack: ${self.player_action_info['stack']}"
            )
    
    def show_final_results(self):
        """Show final game results"""
        self.root.after(0, self._show_final_results)
    
    def _show_final_results(self):
        """Actually show final results"""
        results = "Final Results\n" + "=" * 30 + "\n"
        for player in self.game.players:
            status = " (YOU)" if player.player_id == 0 else " (AI)"
            results += f"Player {player.player_id}{status}: ${player.stack}\n"
        
        self.message_label.config(text="Game Complete!")
        messagebox.showinfo("Game Over", results)
        self.game_running = False


if __name__ == "__main__":
    root = tk.Tk()
    ui = PokerUI(root)
    root.mainloop()
