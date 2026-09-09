import random
from itertools import combinations
from typing import Optional, Tuple, List

class Card:
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    def __init__(self, suit, rank):
        if suit not in self.SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        if rank not in self.RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.rank}{self.suit[0]}"


class Deck:
    def __init__(self):
        self.cards = [Card(suit, rank) for suit in Card.SUITS for rank in Card.RANKS]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards):
        if num_cards > len(self.cards):
            raise ValueError("Not enough cards in the deck to deal")
        dealt_cards = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt_cards


class HandEvaluator:
    HAND_RANKS = {
        "High Card": 1,
        "One Pair": 2,
        "Two Pair": 3,
        "Three of a Kind": 4,
        "Straight": 5,
        "Flush": 6,
        "Full House": 7,
        "Four of a Kind": 8,
        "Straight Flush": 9,
        "Royal Flush": 10
    }

    @staticmethod
    def find_best_hand(hole_cards, community_cards):
        """Find the best 5-card hand from 7 cards (2 hole + 5 community)"""
        all_cards = hole_cards + community_cards
        best_hand: Optional[Tuple] = None
        best_rank = 0
        best_tiebreaker: Optional[Tuple] = None

        for combo in combinations(all_cards, 5):
            hand_info = HandEvaluator.evaluate_hand(list(combo))
            hand_type = hand_info[0]
            tiebreaker = hand_info[1]
            rank_value = HandEvaluator.HAND_RANKS[hand_type]
            
            if best_tiebreaker is None or rank_value > best_rank or (rank_value == best_rank and tiebreaker > best_tiebreaker):
                best_rank = rank_value
                best_tiebreaker = tiebreaker
                best_hand = (hand_type, list(combo))

        return best_hand

    @staticmethod
    def evaluate_hand(cards):
        """Evaluate a 5-card hand and return (hand_type, tiebreaker_values)"""
        ranks = [Card.RANKS.index(card.rank) for card in cards]
        suits = [card.suit for card in cards]
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1

        counts = sorted(rank_counts.values(), reverse=True)
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        sorted_ranks = sorted(ranks)
        is_straight = (sorted_ranks[-1] - sorted_ranks[0] == 4 and len(set(ranks)) == 5)
        # Check for A-2-3-4-5 straight (wheel)
        is_wheel = sorted_ranks == [0, 1, 2, 3, 12]

        # Create tiebreaker values based on card ranks in order of importance
        sorted_by_count = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        tiebreaker = tuple(r for r, c in sorted_by_count)

        if (is_straight or is_wheel) and is_flush and 12 in ranks and 9 in ranks:
            return ("Royal Flush", tiebreaker)
        if (is_straight or is_wheel) and is_flush:
            return ("Straight Flush", tiebreaker)
        if counts == [4, 1]:
            return ("Four of a Kind", tiebreaker)
        if counts == [3, 2]:
            return ("Full House", tiebreaker)
        if is_flush:
            return ("Flush", tuple(sorted(ranks, reverse=True)))
        if is_straight or is_wheel:
            return ("Straight", tiebreaker)
        if counts == [3, 1, 1]:
            return ("Three of a Kind", tiebreaker)
        if counts == [2, 2, 1]:
            return ("Two Pair", tiebreaker)
        if counts == [2, 1, 1, 1]:
            return ("One Pair", tiebreaker)
        return ("High Card", tuple(sorted(ranks, reverse=True)))


class Player:
    def __init__(self, player_id, stack, is_ai=True):
        self.player_id = player_id
        self.stack = stack
        self.is_ai = is_ai
        self.hole_cards = []
        self.bet_amount = 0
        self.total_bet_this_round = 0
        self.is_folded = False
        self.is_all_in = False

    def receive_cards(self, cards):
        self.hole_cards = cards

    def reset_for_new_hand(self):
        self.hole_cards = []
        self.bet_amount = 0
        self.total_bet_this_round = 0
        self.is_folded = False
        self.is_all_in = False

    def __repr__(self):
        return f"Player {self.player_id} (Stack: ${self.stack})"


class GameAborted(Exception):
    """Raised by an observer to abandon a hand in progress (e.g. the UI closed)."""


class GameObserver:
    """Hooks a front-end implements so the engine can own the betting rules.

    The engine decides what is legal and moves the money; a front-end supplies
    human actions and renders what happened. Every hook defaults to a no-op, so
    headless play and tournaments need nothing. This exists so the Tk UI can
    drive the same betting loop instead of keeping a parallel copy of it.
    """

    def on_hand_start(self, game):
        """A new hand is beginning, before blinds are posted."""

    def on_blinds(self, game, small_blind_player, big_blind_player):
        """Blinds have been posted."""

    def on_stage(self, game, stage):
        """A street has been dealt and is about to be bet."""

    def before_ai_action(self, game, player, to_call, stage):
        """Return False to pass over this bot and come back to it later."""
        return True

    def get_human_action(self, game, player, to_call, stage):
        """Return (action, raise_amount) for a seat that is not AI controlled."""
        return ("fold", None)

    def on_action(self, game, player, action, amount, stage):
        """An action has been applied.

        `action` is what the engine actually did, which is not always what was
        requested: an illegal check becomes a call, an unknown action a fold.
        """

    def on_turn_advanced(self, game, stage):
        """Action has moved on to the next seat."""

    def on_showdown(self, game):
        """Remaining hands are about to be compared."""

    def on_hand_end(self, game, winner_info):
        """The pot has been awarded."""


class ConsoleObserver(GameObserver):
    """Prompts a human at the terminal. The default for a bare PokerGame."""

    def get_human_action(self, game, player, to_call, stage):
        print()
        print(f"--- Player {player.player_id} (YOU) ---")
        print(f"Your cards: {player.hole_cards}")
        print(f"Your stack: ${player.stack}")
        print(f"Amount to call: ${to_call}")
        print(f"Current pot: ${game.pot}")

        if to_call == 0:
            action = input("Your action (check/raise/fold): ").lower().strip()
        else:
            action = input("Your action (call/raise/fold): ").lower().strip()
        return (action, None)


class PokerGame:
    DEBUG = False  # Toggle for print output
    
    def __init__(self, num_players=3, starting_stack=1000, small_blind=5, big_blind=10, use_bots=True, bot_types=None, observer=None):
        self.players = [Player(i, starting_stack) for i in range(num_players)]
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.pot = 0
        self.community_cards: List[Card] = []
        self.deck: Optional[Deck] = None
        self.button = 0
        self.current_bet = 0
        self.hand_number = 0
        self.side_pots: List = []  # List of {amount, eligible_players}
        self.total_bet_by_player = {}  # Track total bet amount per player for side pot calculation
        self.pending_raise_amount = 0  # Temporary storage for bot raise amounts
        # Front-end hooks; ConsoleObserver keeps the terminal demo working.
        self.observer = observer if observer is not None else ConsoleObserver()
        
        # Bot system
        self.use_bots = use_bots
        self.bots = {}  # Map player_id to PokerBot instance
        self.bot_types = bot_types or {}  # Map player_id to bot type string
        
        if use_bots:
            self._initialize_bots(num_players)

    def _assert_deck(self) -> Deck:
        """Assert deck is initialized and return it"""
        assert self.deck is not None, "Deck must be initialized before use"
        return self.deck

    def _initialize_bots(self, num_players: int):
        """Initialize poker bots for AI players"""
        try:
            from poker_bot import PokerBot
            
            # Default bot types for variety
            default_bot_types = ["TAG", "LAG", "CTR", "NIT", "FISH"]
            
            for i in range(1, num_players):  # Player 0 is the human
                # Use custom bot type if provided, otherwise use default
                if i in self.bot_types:
                    bot_type = self.bot_types[i]
                else:
                    bot_type = default_bot_types[(i - 1) % len(default_bot_types)]
                self.bots[i] = PokerBot(i, bot_type)
        except ImportError:
            if self.DEBUG:
                print("Warning: poker_bot module not found, using simple AI")
            self.use_bots = False

    def get_active_players(self) -> List:
        """Get all active players (not folded, with stack > 0)"""
        return [p for p in self.players if not p.is_folded and p.stack > 0]

    def get_unfolded_players(self) -> List:
        """Get all players who haven't folded"""
        return [p for p in self.players if not p.is_folded]

    def get_active_opponents(self, excluding_player) -> List:
        """Get active players excluding the specified player"""
        return [p for p in self.get_active_players() if p != excluding_player]

    def get_players_still_acting(self) -> List:
        """Players who can still act: neither folded nor already all-in."""
        return [p for p in self.players if not p.is_folded and not p.is_all_in]

    def get_unfolded_opponents(self, excluding_player) -> List:
        """Get unfolded players excluding the specified player"""
        return [p for p in self.get_unfolded_players() if p != excluding_player]

    def create_side_pots(self):
        """Create side pots based on all-in players' contributions"""
        # Get all non-folded players sorted by their total bet
        active_players = self.get_unfolded_players()
        if len(active_players) <= 1:
            return []
        
        # Sort by total bet amount (ascending)
        bet_levels = sorted(set(p.total_bet_this_round for p in active_players))
        
        pots = []
        previous_level = 0
        
        for level in bet_levels:
            # Create pot for this level
            eligible = [p for p in active_players if p.total_bet_this_round >= level]
            
            if not eligible:
                continue
                
            pot_amount = (level - previous_level) * len(eligible)
            
            if pot_amount > 0:
                pots.append({
                    'amount': pot_amount,
                    'eligible_players': [p.player_id for p in eligible]
                })
            
            previous_level = level
        
        return pots

    def post_blinds(self):
        """Post small blind and big blind"""
        # Initialize total bet tracking
        self.total_bet_by_player = {p.player_id: 0 for p in self.players}
        
        small_blind_player = (self.button + 1) % len(self.players)
        big_blind_player = (self.button + 2) % len(self.players)

        # Small blind
        sb_amount = min(self.small_blind, self.players[small_blind_player].stack)
        self.players[small_blind_player].stack -= sb_amount
        self.players[small_blind_player].total_bet_this_round = sb_amount
        self.pot += sb_amount
        
        # Big blind
        bb_amount = min(self.big_blind, self.players[big_blind_player].stack)
        self.players[big_blind_player].stack -= bb_amount
        self.players[big_blind_player].total_bet_this_round = bb_amount
        self.pot += bb_amount

        self.current_bet = bb_amount
        
        if self.DEBUG:
            print(f"Small blind: Player {small_blind_player} posts ${sb_amount}")
            print(f"Big blind: Player {big_blind_player} posts ${bb_amount}")

    def deal_hole_cards(self):
        """Deal 2 cards to each player"""
        self.deck = Deck()
        for player in self.players:
            cards = self.deck.deal(2)
            player.receive_cards(cards)

    def ai_decision(self, player, community_cards, current_bet, to_call):
        """Make AI decision using poker bots with position and game theory"""
        
        # Use enhanced bot if available
        if self.use_bots and player.player_id in self.bots:
            return self._bot_decision(player, community_cards, current_bet, to_call)
        
        # Fallback to simple AI
        return self._simple_ai_decision(player, community_cards, current_bet, to_call)
    
    def _calculate_position(self, player_idx: int, active_players_count: int) -> str:
        """
        Calculate player's position relative to button
        
        Args:
            player_idx: Player's index
            active_players_count: Number of active (non-folded) players
        
        Returns:
            "early", "middle", or "late"
        """
        # Position relative to button
        pos_from_button = (player_idx - self.button) % len(self.players)
        
        if active_players_count <= 3:
            # Heads-up or 3-way: button is late position
            return "late" if pos_from_button in [1, 2] else "early"
        elif active_players_count <= 6:
            # 4-6 players
            if pos_from_button in [1, 2]:
                return "early"
            elif pos_from_button in [3, 4]:
                return "middle"
            else:
                return "late"
        else:
            # 7+ players
            if pos_from_button in [1, 2, 3]:
                return "early"
            elif pos_from_button in [4, 5]:
                return "middle"
            else:
                return "late"
    
    def _bot_decision(self, player, community_cards, current_bet, to_call) -> str:
        """Make decision using poker bot"""
        bot = self.bots.get(player.player_id)
        if not bot:
            return self._simple_ai_decision(player, community_cards, current_bet, to_call)
        
        # Calculate position
        active_players = [p for p in self.players if not p.is_folded]
        position = self._calculate_position(player.player_id, len(active_players))
        num_opponents = len(active_players) - 1
        
        # Get bot decision
        try:
            action, raise_amount = bot.decide_action(
                hole_cards=player.hole_cards,
                community_cards=community_cards,
                current_bet=current_bet,
                to_call=to_call,
                player_stack=player.stack,
                pot=self.pot,
                position=position,
                num_opponents=num_opponents,
                small_blind=self.small_blind,
                big_blind=self.big_blind
            )
            
            # Convert raise action with amount to "raise" for the betting system
            if action == "raise" and raise_amount:
                # Store the raise amount for processing
                self.pending_raise_amount = raise_amount
                return "raise"
            
            return action
        except Exception as e:
            if self.DEBUG:
                print(f"Bot decision error: {e}, falling back to simple AI")
            return self._simple_ai_decision(player, community_cards, current_bet, to_call)
    
    def _simple_ai_decision(self, player, community_cards, current_bet, to_call) -> str:
        """Simple AI strategy for betting (fallback)"""
        if to_call > player.stack:
            # All-in or fold
            return "call" if random.random() > 0.7 else "fold"

        # Evaluate hand strength
        best_hand = HandEvaluator.find_best_hand(player.hole_cards, community_cards)
        hand_strength = HandEvaluator.HAND_RANKS[best_hand[0]] if best_hand else 1

        # Simple strategy
        if hand_strength >= 6:  # Flush or better
            return "raise" if random.random() > 0.5 else "call"
        elif hand_strength >= 4:  # Three of a kind or better
            return "call"
        elif hand_strength >= 2:  # One pair
            return "call" if to_call < self.big_blind else "fold"
        else:  # High card
            return "fold" if to_call > 0 else "check"

    def _request_action(self, player, to_call, stage):
        """Ask whoever controls this seat what to do.

        Returns (action, raise_amount). A None action means the observer wants
        this player passed over for now (the UI's "skip to my turn" button).
        """
        if not player.is_ai:
            return self.observer.get_human_action(self, player, to_call, stage)

        if not self.observer.before_ai_action(self, player, to_call, stage):
            return (None, None)

        if to_call == 0:
            return ("check", None)

        # ai_decision reports a raise size out of band via pending_raise_amount.
        self.pending_raise_amount = 0
        action = self.ai_decision(player, self.community_cards, self.current_bet, to_call)
        raise_amount = self.pending_raise_amount or None
        self.pending_raise_amount = 0
        return (action, raise_amount)

    def _apply_action(self, player, action, raise_amount, to_call, stage):
        """Move the money for one action and tell the observer what happened.

        Returns (effective_action, action_taken). The effective action is not
        always the requested one: a check facing a bet is turned into a call,
        and an unrecognised action into a fold.
        """
        action_taken = False
        amount = 0

        if action == "fold":
            player.is_folded = True
            action_taken = True

        elif action == "call":
            if to_call > 0:
                amount = min(to_call, player.stack)
                player.stack -= amount
                player.total_bet_this_round += amount
                self.pot += amount
                action_taken = True
                self.current_bet = max(self.current_bet, player.total_bet_this_round)

        elif action == "raise":
            increment = raise_amount if raise_amount else self.big_blind
            amount = min(to_call + increment, player.stack)
            player.stack -= amount
            player.total_bet_this_round += amount
            self.pot += amount
            self.current_bet = player.total_bet_this_round
            action_taken = True

        elif action == "check":
            if to_call == 0:
                action_taken = True
            else:
                # Not a legal check - the player must call or fold, so call.
                action = "call"
                amount = min(to_call, player.stack)
                if amount > 0:
                    player.stack -= amount
                    player.total_bet_this_round += amount
                    self.pot += amount
                    action_taken = True
                self.current_bet = max(self.current_bet, player.total_bet_this_round)

        else:
            if self.DEBUG:
                print(f"Player {player.player_id} returned unexpected action "
                      f"{action!r}, forcing fold")
            action = "fold"
            player.is_folded = True
            action_taken = True

        # A player with nothing behind is all-in, however they got there.
        # Without this they keep being asked to act and can never match the
        # current bet, which is what the UI's `stack == 0` skip papered over.
        if player.stack == 0 and not player.is_folded:
            player.is_all_in = True

        if self.DEBUG and action_taken:
            if action == "fold":
                print(f"Player {player.player_id} folds")
            elif action == "check":
                print(f"Player {player.player_id} checks")
            elif player.is_all_in:
                print(f"Player {player.player_id} goes all-in with ${amount}")
            elif action == "raise":
                print(f"Player {player.player_id} raises to ${player.total_bet_this_round}")
            else:
                print(f"Player {player.player_id} calls ${amount}")

        self.observer.on_action(self, player, action, amount, stage)
        return action, action_taken

    def betting_round(self, stage):
        """Execute a betting round.

        This is the only betting implementation in the project. The Tk UI runs
        the same loop through its observer instead of keeping a parallel copy,
        so the rules cannot drift between the GUI and headless play.
        """
        if self.DEBUG:
            print(f"--- {stage.upper()} ---")
            print(f"Pot: ${self.pot}")
            if self.community_cards:
                print(f"Community Cards: {self.community_cards}")

        if len(self.get_unfolded_players()) <= 1:
            return
        if not self.get_players_still_acting():
            return  # everyone left is all-in; there is nothing to bet

        if stage == "Pre-Flop":
            current_player_idx = (self.button + 3) % len(self.players)
        else:
            current_player_idx = (self.button + 1) % len(self.players)

        players_who_acted_this_level = set()
        max_iterations = len(self.players) * 100
        iteration_count = 0

        while True:
            iteration_count += 1
            if iteration_count > max_iterations:
                if self.DEBUG:
                    print(f"WARNING: Betting round exceeded {max_iterations} "
                          f"iterations, forcing termination")
                break

            player = self.players[current_player_idx]

            if player.is_folded or player.is_all_in:
                current_player_idx = (current_player_idx + 1) % len(self.players)
                continue

            to_call = self.current_bet - player.total_bet_this_round
            action, raise_amount = self._request_action(player, to_call, stage)

            if action is None:
                current_player_idx = (current_player_idx + 1) % len(self.players)
                continue

            effective, action_taken = self._apply_action(
                player, action, raise_amount, to_call, stage
            )

            if effective == "raise":
                # A raise reopens the action for everyone behind.
                players_who_acted_this_level = set()
            if action_taken:
                players_who_acted_this_level.add(player.player_id)

            if len(self.get_unfolded_players()) <= 1:
                break

            players_still_acting = self.get_players_still_acting()
            if len(players_still_acting) <= 1:
                break

            if all(p.player_id in players_who_acted_this_level
                   for p in players_still_acting):
                if all(p.total_bet_this_round == self.current_bet
                       for p in players_still_acting):
                    break

            current_player_idx = (current_player_idx + 1) % len(self.players)
            self.observer.on_turn_advanced(self, stage)

    def reset_round_bets(self):
        """Reset player bets for next betting round"""
        for player in self.players:
            player.total_bet_this_round = 0
        self.current_bet = 0

    def determine_winner(self):
        """Determine winner with side pots support"""
        active_players = [p for p in self.players if not p.is_folded]

        if len(active_players) == 1:
            winner = active_players[0]
            if self.DEBUG:
                print(f"\nPlayer {winner.player_id} wins ${self.pot}!")
            winner.stack += self.pot
            return {"winners": [winner], "pot": self.pot, "hand_type": "Opponents Folded"}

        # Create side pots
        pots = self.create_side_pots()
        if not pots:
            # Fallback to single pot
            pots = [{'amount': self.pot, 'eligible_players': [p.player_id for p in active_players]}]
        
        total_distributed = 0
        
        # Process each pot
        for pot_info in pots:
            pot_amount = pot_info['amount']
            eligible_ids = pot_info['eligible_players']
            eligible_players = [p for p in active_players if p.player_id in eligible_ids]
            
            if not eligible_players:
                continue
            
            # Find best hand among eligible players
            best_hand_rank = 0
            best_tiebreaker: Optional[Tuple] = None
            pot_winners = []
            winning_hand_type = ""
            
            for player in eligible_players:
                best_hand = HandEvaluator.find_best_hand(player.hole_cards, self.community_cards)
                if best_hand is None:
                    continue
                hand_type = best_hand[0]
                hand_rank = HandEvaluator.HAND_RANKS[hand_type]
                
                hand_info = HandEvaluator.evaluate_hand(best_hand[1])
                tiebreaker = hand_info[1]
                
                if self.DEBUG and pot_info == pots[0]:  # Only print hands once
                    print(f"Player {player.player_id}: {player.hole_cards} - {hand_type}")
                
                if best_tiebreaker is None or hand_rank > best_hand_rank or (hand_rank == best_hand_rank and tiebreaker > best_tiebreaker):
                    best_hand_rank = hand_rank
                    best_tiebreaker = tiebreaker
                    pot_winners = [player]
                    winning_hand_type = hand_type
                elif hand_rank == best_hand_rank and tiebreaker == best_tiebreaker:
                    pot_winners.append(player)
            
            # Distribute pot among winners
            if len(pot_winners) == 1:
                winner = pot_winners[0]
                winner.stack += pot_amount
                total_distributed += pot_amount
                if self.DEBUG and len(pots) > 1:
                    print(f"Player {winner.player_id} wins side pot of ${pot_amount}")
            else:
                split_amount = pot_amount // len(pot_winners)
                remainder = pot_amount % len(pot_winners)
                for i, winner in enumerate(pot_winners):
                    # Odd chips go to the first `remainder` winners, not
                    # unconditionally to the first - that minted a chip
                    # every time a split pot divided evenly.
                    amount = split_amount + (1 if i < remainder else 0)
                    winner.stack += amount
                    total_distributed += amount
                    if self.DEBUG and len(pots) > 1:
                        print(f"Player {winner.player_id} gets ${amount} from side pot")
        
        if self.DEBUG:
            print(f"\nMain pot distributed: ${total_distributed}")
        
        return {"winners": [], "pot": self.pot, "hand_type": "Showdown with side pots"}

    # (street name, cards dealt before that street's betting)
    STREETS = (("Pre-Flop", 0), ("Flop", 3), ("Turn", 1), ("River", 1))

    def play_hand(self):
        """Play a single hand of poker and return the winner info."""
        self.hand_number += 1
        if self.DEBUG:
            print("=" * 50)
            print(f"HAND #{self.hand_number}")
            print("=" * 50)

        for player in self.players:
            player.reset_for_new_hand()

        self.side_pots = []
        self.total_bet_by_player = {p.player_id: 0 for p in self.players}

        self.observer.on_hand_start(self)

        self.post_blinds()
        self.observer.on_blinds(self,
                                (self.button + 1) % len(self.players),
                                (self.button + 2) % len(self.players))

        self.deal_hole_cards()
        self.current_bet = self.big_blind
        self.community_cards = []

        if self.DEBUG:
            for player in self.players:
                print(f"Player {player.player_id}: {player.hole_cards}")

        for stage, cards_to_deal in self.STREETS:
            if cards_to_deal:
                self.reset_round_bets()
                deck = self._assert_deck()
                dealt = deck.deal(cards_to_deal)
                # The flop replaces the (empty) board, later streets extend it.
                self.community_cards = (dealt if stage == "Flop"
                                        else self.community_cards + dealt)

            self.observer.on_stage(self, stage)
            self.betting_round(stage)

            if len(self.get_unfolded_players()) <= 1:
                return self._finish_hand()

        self.observer.on_showdown(self)
        return self._finish_hand()

    def _finish_hand(self):
        """Award the pot, move the button and clear the table."""
        winner_info = self.determine_winner()
        self.observer.on_hand_end(self, winner_info)
        self.button = (self.button + 1) % len(self.players)
        self.pot = 0
        return winner_info

    def print_stacks(self):
        """Print current player stacks"""
        if self.DEBUG:
            print("\n--- Current Stacks ---")
            for player in self.players:
                print(f"Player {player.player_id}: ${player.stack}")


# Example usage
if __name__ == "__main__":
    print("Welcome to Texas Hold'em!")
    num_opponents = input("How many AI opponents? (1-5, default 2): ").strip()
    num_opponents = int(num_opponents) if num_opponents.isdigit() and 1 <= int(num_opponents) <= 5 else 2
    num_players = num_opponents + 1  # +1 for human player
    
    starting_stack = input("Starting stack for each player? (default $1000): ").strip()
    starting_stack = int(starting_stack) if starting_stack.isdigit() else 1000
    
    num_hands = input("How many hands to play? (default 5): ").strip()
    num_hands = int(num_hands) if num_hands.isdigit() else 5
    
    game = PokerGame(num_players=num_players, starting_stack=starting_stack, small_blind=5, big_blind=10)
    
    # Make first player human
    game.players[0].is_ai = False
    
    print(f"\nStarting Texas Hold'em game with {num_opponents} AI opponent(s)!")
    print(f"Initial stacks: ${starting_stack} each")
    print(f"Small blind: $5 | Big blind: $10")
    print(f"You are Player 0")
    game.print_stacks()
    
    # Play hands
    for _ in range(num_hands):
        try:
            game.play_hand()
            game.print_stacks()
        except KeyboardInterrupt:
            print("\nGame interrupted!")
            break
    
    print("\nGame complete!")
    game.print_stacks()


