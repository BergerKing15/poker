import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from PIL import Image, ImageTk
from poker_game import PokerGame, HandEvaluator

class PokerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Texas Hold'em Poker")
        self.root.geometry("1200x900")
        self.root.configure(bg="#2d5016")
        
        self.game = None
        self.game_running = False
        self.current_player_action = None
        self.game_thread = None
        self.card_images = {}
        self.photo_cache = {}  # Cache PhotoImages by card name (prevents memory leak)
        self.game_history = []
        self.raise_amount = 0
        self.community_cards_cached = []  # Track currently displayed cards
        self.hand_cards_cached = []  # Track currently displayed hand cards
        
        self.load_card_images()
        self.setup_ui()
        
    def load_card_images(self):
        """Load all card PNG images into memory"""
        cards_dir = os.path.join(os.path.dirname(__file__), "cards-png-100px")
        if os.path.exists(cards_dir):
            for filename in os.listdir(cards_dir):
                if filename.endswith(".png"):
                    card_name = filename  # Keep full filename with .png
                    try:
                        img = Image.open(os.path.join(cards_dir, filename))
                        self.card_images[card_name] = img
                    except Exception as e:
                        print(f"Error loading card image {filename}: {e}")
        else:
            print(f"Card directory not found: {cards_dir}")
    
    def get_card_photo(self, card_name):
        """Get a cached PhotoImage for a card name (prevents duplicate image creation)"""
        if card_name not in self.photo_cache:
            if card_name in self.card_images:
                img = self.card_images[card_name]
                self.photo_cache[card_name] = ImageTk.PhotoImage(img)
        return self.photo_cache.get(card_name)
    
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
        self.community_cards_frame = tk.Frame(community_frame, bg="#2d5016", height=150)
        self.community_cards_frame.pack(pady=10, padx=5, fill=tk.X, expand=True)
        self.community_cards_frame.pack_propagate(False)  # Maintain height
        self.community_label = ttk.Label(community_frame, text="", font=("Arial", 10))
        self.community_label.pack(pady=5)
        
        # Pot
        self.pot_label = ttk.Label(self.game_screen, text="", font=("Arial", 14, "bold"), foreground="gold")
        self.pot_label.pack(pady=5)
        
        # Main content frame with left and right columns
        content_frame = ttk.Frame(self.game_screen)
        content_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1)  # Left column expands
        content_frame.columnconfigure(1, weight=0)  # Right column fixed width
        content_frame.rowconfigure(0, weight=1)  # Row expands vertically
        
        # Left column: Game History and Actions
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        
        # Game history
        history_label_frame = ttk.LabelFrame(left_frame, text="Game History")
        history_label_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.history_text = tk.Text(history_label_frame, height=12, width=40, state=tk.DISABLED, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(history_label_frame, orient=tk.VERTICAL, command=self.history_text.yview)
        self.history_text.config(yscrollcommand=scrollbar.set)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action frame
        action_frame = ttk.LabelFrame(left_frame, text="Your Action")
        action_frame.pack(pady=5, fill=tk.X)
        
        self.action_info_label = ttk.Label(action_frame, text="", font=("Arial", 10))
        self.action_info_label.pack(pady=5, padx=5)
        
        # Buttons
        buttons_frame = ttk.Frame(action_frame)
        buttons_frame.pack(pady=10, padx=5)
        
        self.check_button = ttk.Button(buttons_frame, text="Check", command=lambda: self.player_action("check"))
        self.check_button.pack(side=tk.LEFT, padx=5)
        self.call_button = ttk.Button(buttons_frame, text="Call", command=lambda: self.player_action("call"))
        self.call_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Fold", command=lambda: self.player_action("fold")).pack(side=tk.LEFT, padx=5)
        
        # Right column: Players, hand, and raise
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        right_frame.rowconfigure(0, weight=1)  # Players expands
        right_frame.rowconfigure(1, weight=0)  # Your hand fixed
        right_frame.rowconfigure(2, weight=0)  # Raise fixed
        
        # Players info - make it more compact
        players_frame = ttk.LabelFrame(right_frame, text="Players")
        players_frame.grid(row=0, column=0, sticky="nsew", pady=5)
        self.players_text = tk.Text(players_frame, height=12, width=40, state=tk.DISABLED, font=("Courier", 11))
        self.players_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Your hand
        your_hand_frame = ttk.LabelFrame(right_frame, text="Your Hand")
        your_hand_frame.grid(row=1, column=0, sticky="ew", pady=5)
        self.your_hand_cards_frame = tk.Frame(your_hand_frame, bg="#2d5016")
        self.your_hand_cards_frame.pack(pady=10, padx=5)
        self.your_hand_label = ttk.Label(your_hand_frame, text="", font=("Arial", 10))
        self.your_hand_label.pack(pady=5)
        
        # Raise frame
        raise_frame = ttk.LabelFrame(right_frame, text="Raise Amount")
        raise_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        self.raise_slider_frame = ttk.Frame(raise_frame)
        self.raise_slider_frame.pack(padx=5, pady=5, fill=tk.X)
        
        self.raise_var = tk.IntVar(value=0)
        self.raise_slider = ttk.Scale(self.raise_slider_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                      variable=self.raise_var, command=self.update_raise_label)
        self.raise_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.raise_amount_label = ttk.Label(self.raise_slider_frame, text="$0", width=8)
        self.raise_amount_label.pack(side=tk.LEFT, padx=5)
        
        # Raise amount entry
        entry_frame = ttk.Frame(raise_frame)
        entry_frame.pack(padx=5, pady=5, fill=tk.X)
        ttk.Label(entry_frame, text="Amount:").pack(side=tk.LEFT, padx=3)
        self.raise_entry = ttk.Entry(entry_frame, width=12)
        self.raise_entry.pack(side=tk.LEFT, padx=3)
        self.raise_entry.insert(0, "0")
        self.raise_entry.bind('<KeyRelease>', self.update_raise_from_entry)
        
        ttk.Button(raise_frame, text="Raise", command=self.confirm_raise).pack(pady=5)
        
        # Message label
        self.message_label = ttk.Label(self.game_screen, text="", font=("Arial", 10))
        self.message_label.pack(pady=5)
        
    def start_game(self):
        """Start a new game"""
        try:
            num_opponents = int(self.opponents_var.get())
            starting_stack = int(self.stack_var.get())
            
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
            
            self.setup_screen.pack_forget()
            self.game_screen.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            self.game_running = True
            self.game_thread = threading.Thread(target=self.play_game_loop, daemon=True)
            self.game_thread.start()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid input")
    
    def play_game_loop(self):
        """Main game loop - runs indefinitely"""
        hand_num = 0
        while self.game_running:
            if not self.game_running:
                break
            hand_num += 1
            self.current_hand = hand_num
            self.play_single_hand()
            self.root.after(1000)  # Brief pause between hands
    
    def play_single_hand(self):
        """Play a single hand"""
        self.game.hand_number += 1
        # Don't clear history - accumulate across hands
        self.log_event(f"\n{'='*50}")
        self.log_event(f"HAND #{self.game.hand_number}")
        self.log_event(f"{'='*50}")
        self.update_history_display()
        
        # Reset player state
        for player in self.game.players:
            player.reset_for_new_hand()
        
        # Post blinds and deal
        self.game.post_blinds()
        self.game.deal_hole_cards()
        self.game.current_bet = self.game.big_blind
        self.game.community_cards = []
        
        self.log_event("=== PRE-FLOP ===")
        self.update_history_display()
        self.update_display("Pre-Flop")
        self.betting_round("Pre-Flop")
        
        # Check if only one player remains
        active_players = [p for p in self.game.players if not p.is_folded]
        if len(active_players) == 1:
            winner_info = self.game.determine_winner()
            self._log_winner(winner_info)
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
        cards_str = ", ".join(str(card) for card in self.game.community_cards)
        self.log_event(f"=== FLOP: {cards_str} ===")
        self.update_history_display()
        self.update_display("Flop")
        self.betting_round("Flop")
        
        if len([p for p in self.game.players if not p.is_folded]) == 1:
            winner_info = self.game.determine_winner()
            self._log_winner(winner_info)
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
        cards_str = ", ".join(str(card) for card in self.game.community_cards)
        self.log_event(f"=== TURN: {cards_str} ===")
        self.update_history_display()
        self.update_display("Turn")
        self.betting_round("Turn")
        
        if len([p for p in self.game.players if not p.is_folded]) == 1:
            winner_info = self.game.determine_winner()
            self._log_winner(winner_info)
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
        cards_str = ", ".join(str(card) for card in self.game.community_cards)
        self.log_event(f"=== RIVER: {cards_str} ===")
        self.update_history_display()
        self.update_display("River")
        self.betting_round("River")
        
        # Showdown
        self._reveal_all_hands()
        winner_info = self.game.determine_winner()
        self._log_winner(winner_info)
        self.game.button = (self.game.button + 1) % len(self.game.players)
        self.game.pot = 0
        self.update_history_display()
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
                self.update_action_buttons(to_call)
                self.setup_raise_controls(to_call, player.stack)
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
            msg = f"Player {player.player_id} folds"
            self.log_event(msg)
            self.message_label.config(text=msg)
        elif action == "call":
            if to_call > 0:
                bet_amount = min(to_call, player.stack)
                player.stack -= bet_amount
                player.total_bet_this_round += bet_amount
                self.game.pot += bet_amount
                msg = f"Player {player.player_id} calls ${bet_amount}"
                self.log_event(msg)
                self.message_label.config(text=msg)
                self.game.current_bet = max(self.game.current_bet, player.total_bet_this_round)
        elif action == "raise":
            raise_amount = self.raise_amount if isinstance(self.raise_amount, int) else self.game.big_blind
            bet_amount = min(to_call + raise_amount, player.stack)
            player.stack -= bet_amount
            player.total_bet_this_round += bet_amount
            self.game.pot += bet_amount
            self.game.current_bet = player.total_bet_this_round
            msg = f"Player {player.player_id} raises to ${player.total_bet_this_round}"
            self.log_event(msg)
            self.message_label.config(text=msg)
        elif action == "check":
            if to_call == 0:
                msg = f"Player {player.player_id} checks"
                self.log_event(msg)
                self.message_label.config(text=msg)
    
    def player_action(self, action):
        """Handle player action button press"""
        if action in ["check", "call", "fold"]:
            self.current_player_action = action
        self.update_display("Executing action...")
    
    def update_action_buttons(self, to_call):
        """Update which action buttons are enabled/disabled"""
        if to_call == 0:
            self.check_button.config(state=tk.NORMAL)
            self.call_button.config(state=tk.DISABLED)
        else:
            self.check_button.config(state=tk.DISABLED)
            self.call_button.config(state=tk.NORMAL)
    
    def update_raise_label(self, value):
        """Update raise label when slider changes"""
        self.raise_amount_label.config(text=f"${int(float(value))}")
        self.raise_entry.delete(0, tk.END)
        self.raise_entry.insert(0, str(int(float(value))))
    
    def update_raise_from_entry(self, event):
        """Update raise slider when entry changes"""
        try:
            val = int(self.raise_entry.get())
            self.raise_var.set(val)
            self.raise_amount_label.config(text=f"${val}")
        except ValueError:
            pass
    
    def confirm_raise(self):
        """Confirm raise amount"""
        try:
            amount = int(self.raise_entry.get())
            self.current_player_action = "raise"
            self.raise_amount = amount
        except ValueError:
            messagebox.showerror("Error", "Invalid raise amount")
    
    def setup_raise_controls(self, to_call, stack):
        """Setup raise slider based on to_call and stack"""
        # Calculate min and max raise
        if self.game.current_bet == 0:
            min_raise = self.game.big_blind
        else:
            min_raise = self.game.current_bet
        
        max_raise = stack  # All-in
        
        self.raise_slider.config(from_=min_raise, to=max_raise)
        self.raise_var.set(min_raise)
        self.raise_entry.delete(0, tk.END)
        self.raise_entry.insert(0, str(min_raise))
        self.raise_amount_label.config(text=f"${min_raise}")
    
    def update_display(self, stage=""):
        """Update the game display"""
        self.root.after(0, self._update_display, stage)
    
    def _update_display(self, stage):
        """Actually update the display"""
        if not self.game:
            return
        
        # Update title
        self.title_label.config(text=f"Hand #{self.game.hand_number} - {stage}")
        
        # Update community cards with images only if changed
        if self.game.community_cards != self.community_cards_cached:
            self.community_cards_cached = list(self.game.community_cards)
            for widget in self.community_cards_frame.winfo_children():
                widget.destroy()
            if self.game.community_cards:
                cards_str = ", ".join(str(card) for card in self.game.community_cards)
                self.community_label.config(text=cards_str)
                # Create a sub-frame to center the cards
                cards_container = tk.Frame(self.community_cards_frame, bg="#2d5016")
                cards_container.pack(expand=True)
                for card in self.game.community_cards:
                    card_name = self.card_to_filename(card)
                    photo = self.get_card_photo(card_name)
                    if photo:
                        label = tk.Label(cards_container, image=photo, bg="#2d5016")
                        label.image = photo
                        label.pack(side=tk.LEFT, padx=5)
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
        
        # Update your hand with images only if changed
        player = self.game.players[0]
        if player.hole_cards != self.hand_cards_cached:
            self.hand_cards_cached = list(player.hole_cards) if player.hole_cards else []
            for widget in self.your_hand_cards_frame.winfo_children():
                widget.destroy()
            if player.hole_cards:
                cards_str = ", ".join(str(card) for card in player.hole_cards)
                self.your_hand_label.config(text=f"{cards_str} | Stack: ${player.stack}")
                for card in player.hole_cards:
                    card_name = self.card_to_filename(card)
                    photo = self.get_card_photo(card_name)
                    if photo:
                        label = tk.Label(self.your_hand_cards_frame, image=photo, bg="#2d5016")
                        label.image = photo
                        label.pack(side=tk.LEFT, padx=10)
            else:
                self.your_hand_label.config(text=f"Stack: ${player.stack}")
        
        # Update action info
        if hasattr(self, 'player_action_info'):
            to_call = self.player_action_info["to_call"]
            self.action_info_label.config(
                text=f"To call: ${to_call} | Pot: ${self.player_action_info['pot']} | Your stack: ${self.player_action_info['stack']}"
            )
    
    def _reveal_all_hands(self):
        """Reveal all player hands and best 5-card hands at showdown"""
        self.log_event("=== SHOWDOWN ===")
        for i, player in enumerate(self.game.players):
            status = " (YOU)" if i == 0 else " (AI)"
            if not player.is_folded:
                hole_cards_str = ", ".join(str(card) for card in player.hole_cards)
                self.log_event(f"Player {i}{status}: {hole_cards_str}")
                
                # Show best 5-card hand
                best_hand = HandEvaluator.find_best_hand(player.hole_cards, self.game.community_cards)
                if best_hand:
                    hand_type = best_hand[0]
                    best_five = best_hand[1]
                    best_five_str = ", ".join(str(card) for card in best_five)
                    self.log_event(f"  Best Hand: {hand_type} - {best_five_str}")
            else:
                self.log_event(f"Player {i}{status}: FOLDED")
    
    def _log_winner(self, winner_info):
        """Log winner information to game history"""
        if not winner_info:
            return
        
        winners = winner_info.get("winners", [])
        pot = winner_info.get("pot", 0)
        hand_type = winner_info.get("hand_type", "Unknown")
        
        if len(winners) == 1:
            winner = winners[0]
            status = " (YOU)" if winner.player_id == 0 else " (AI)"
            self.log_event(f"Player {winner.player_id}{status} wins ${pot}!")
            self.log_event(f"  Hand Type: {hand_type}")
            self.log_event(f"  Stack: ${winner.stack}")
        else:
            winner_ids = [w.player_id for w in winners]
            self.log_event(f"Pot split among players: {winner_ids} (${pot} total)")
            for winner in winners:
                status = " (YOU)" if winner.player_id == 0 else " (AI)"
                self.log_event(f"  Player {winner.player_id}{status} gets a share - Stack: ${winner.stack}")
    
    def card_to_filename(self, card):
        """Convert card object to PNG filename (e.g., '2H', '10S', 'AH')"""
        # Card.__repr__ returns format like "2H", "10D", "AS", etc.
        # PNG files are named like 2H.png, 10D.png, AS.png
        return str(card) + ".png"
    
    def log_event(self, message):
        """Log an event to the game history"""
        self.game_history.append(message)
    
    def update_history_display(self):
        """Update the game history display"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        for event in self.game_history:
            self.history_text.insert(tk.END, event + "\n")
        self.history_text.see(tk.END)  # Scroll to bottom
        self.history_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    ui = PokerUI(root)
    root.mainloop()
