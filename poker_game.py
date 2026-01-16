import random
from itertools import combinations

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
        best_hand = None
        best_rank = 0
        best_tiebreaker = None

        for combo in combinations(all_cards, 5):
            hand_info = HandEvaluator.evaluate_hand(list(combo))
            hand_type = hand_info[0]
            tiebreaker = hand_info[1]
            rank_value = HandEvaluator.HAND_RANKS[hand_type]
            
            if rank_value > best_rank or (rank_value == best_rank and tiebreaker > best_tiebreaker):
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

    def receive_cards(self, cards):
        self.hole_cards = cards

    def reset_for_new_hand(self):
        self.hole_cards = []
        self.bet_amount = 0
        self.total_bet_this_round = 0
        self.is_folded = False

    def __repr__(self):
        return f"Player {self.player_id} (Stack: ${self.stack})"


class PokerGame:
    def __init__(self, num_players=3, starting_stack=1000, small_blind=5, big_blind=10):
        self.players = [Player(i, starting_stack) for i in range(num_players)]
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.pot = 0
        self.community_cards = []
        self.deck = None
        self.button = 0
        self.current_bet = 0
        self.hand_number = 0

    def post_blinds(self):
        """Post small blind and big blind"""
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
        
        print(f"Small blind: Player {small_blind_player} posts ${sb_amount}")
        print(f"Big blind: Player {big_blind_player} posts ${bb_amount}")

    def deal_hole_cards(self):
        """Deal 2 cards to each player"""
        self.deck = Deck()
        for player in self.players:
            cards = self.deck.deal(2)
            player.receive_cards(cards)

    def ai_decision(self, player, community_cards, current_bet, to_call):
        """Simple AI strategy for betting"""
        if to_call > player.stack:
            # All-in or fold
            return "call" if random.random() > 0.7 else "fold"

        # Evaluate hand strength
        if len(community_cards) < 5:
            # Only evaluate existing cards, don't copy deck
            best_hand = HandEvaluator.find_best_hand(player.hole_cards, community_cards)
        else:
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

    def betting_round(self, stage):
        """Execute a betting round"""
        print(f"\n--- {stage.upper()} ---")
        print(f"Pot: ${self.pot}")
        if self.community_cards:
            print(f"Community Cards: {self.community_cards}")

        active_players = [p for p in self.players if not p.is_folded and p.stack > 0]
        if len(active_players) <= 1:
            return

        # Determine starting player (left of big blind for pre-flop, after button for others)
        if stage == "Pre-Flop":
            first_to_act = (self.button + 3) % len(self.players)
        else:
            first_to_act = (self.button + 1) % len(self.players)

        current_player_idx = first_to_act
        players_who_acted_this_level = set()
        
        while True:
            player = self.players[current_player_idx]

            if player.is_folded or player.stack == 0:
                current_player_idx = (current_player_idx + 1) % len(self.players)
                continue

            to_call = self.current_bet - player.total_bet_this_round

            if player.is_ai:
                if to_call == 0:
                    action = "check"
                else:
                    action = self.ai_decision(player, self.community_cards, self.current_bet, to_call)
            else:
                # Human player - always prompt
                print(f"\n--- Player {player.player_id} (YOU) ---")
                print(f"Your cards: {player.hole_cards}")
                print(f"Your stack: ${player.stack}")
                print(f"Amount to call: ${to_call}")
                print(f"Current pot: ${self.pot}")
                
                if to_call == 0:
                    action = input("Your action (check/raise/fold): ").lower().strip()
                else:
                    action = input("Your action (call/raise/fold): ").lower().strip()

            if action == "fold":
                player.is_folded = True
                print(f"Player {player.player_id} folds")
            elif action == "call":
                if to_call > 0:
                    bet_amount = min(to_call, player.stack)
                    player.stack -= bet_amount
                    player.total_bet_this_round += bet_amount
                    self.pot += bet_amount
                    print(f"Player {player.player_id} calls ${bet_amount}")
                    self.current_bet = max(self.current_bet, player.total_bet_this_round)
            elif action == "raise":
                if player.is_ai:
                    raise_amount = min(self.big_blind, player.stack)
                else:
                    # Ask human player how much to raise
                    max_raise = player.stack - to_call
                    try:
                        raise_input = input(f"How much to raise? (max ${max_raise}): ").strip()
                        raise_amount = int(raise_input) if raise_input.isdigit() else self.big_blind
                        raise_amount = min(raise_amount, max_raise)
                    except:
                        raise_amount = min(self.big_blind, max_raise)
                
                bet_amount = min(to_call + raise_amount, player.stack)
                player.stack -= bet_amount
                player.total_bet_this_round += bet_amount
                self.pot += bet_amount
                self.current_bet = player.total_bet_this_round
                print(f"Player {player.player_id} raises to ${player.total_bet_this_round}")
                players_who_acted_this_level = {player.player_id}  # Reset who has acted
            elif action == "check":
                if to_call == 0:
                    print(f"Player {player.player_id} checks")
                else:
                    print(f"Player {player.player_id} can't check, must call or fold")

            players_who_acted_this_level.add(player.player_id)
            
            # Check if betting round is complete
            active_players = [p for p in self.players if not p.is_folded and p.stack > 0]
            if len(active_players) <= 1:
                break
            
            # All active players have acted and are at the same bet level
            active_unfolded = [p for p in self.players if not p.is_folded]
            if len(active_unfolded) <= 1:
                break
                
            if all(p.player_id in players_who_acted_this_level for p in active_unfolded):
                all_matched = all(
                    p.total_bet_this_round == self.current_bet 
                    for p in active_unfolded
                )
                if all_matched:
                    break
            
            current_player_idx = (current_player_idx + 1) % len(self.players)

    def reset_round_bets(self):
        """Reset player bets for next betting round"""
        for player in self.players:
            player.total_bet_this_round = 0
        self.current_bet = 0

    def determine_winner(self):
        """Determine winner and return winner info"""
        active_players = [p for p in self.players if not p.is_folded]

        if len(active_players) == 1:
            winner = active_players[0]
            print(f"\nPlayer {winner.player_id} wins ${self.pot}!")
            winner.stack += self.pot
            return {"winners": [winner], "pot": self.pot, "hand_type": "Opponents Folded"}

        # Compare hands
        best_hand_rank = 0
        best_tiebreaker = None
        winners = []
        winning_hand_type = ""

        for player in active_players:
            best_hand = HandEvaluator.find_best_hand(player.hole_cards, self.community_cards)
            hand_type = best_hand[0]
            hand_rank = HandEvaluator.HAND_RANKS[hand_type]
            
            # Evaluate to get tiebreaker
            hand_info = HandEvaluator.evaluate_hand(best_hand[1])
            tiebreaker = hand_info[1]

            print(f"Player {player.player_id}: {player.hole_cards} - {hand_type}")

            if hand_rank > best_hand_rank or (hand_rank == best_hand_rank and tiebreaker > best_tiebreaker):
                best_hand_rank = hand_rank
                best_tiebreaker = tiebreaker
                winners = [player]
                winning_hand_type = hand_type
            elif hand_rank == best_hand_rank and tiebreaker == best_tiebreaker:
                winners.append(player)

        if len(winners) == 1:
            winner = winners[0]
            print(f"\nPlayer {winner.player_id} wins ${self.pot}!")
            winner.stack += self.pot
            return {"winners": [winner], "pot": self.pot, "hand_type": winning_hand_type}
        else:
            # Split pot among winners
            split_amount = self.pot // len(winners)
            remainder = self.pot % len(winners)
            print(f"\nPot split among players: {[w.player_id for w in winners]}")
            for i, winner in enumerate(winners):
                amount = split_amount + (1 if i == 0 else 0)  # Give remainder to first winner
                winner.stack += amount
                print(f"Player {winner.player_id} gets ${amount}")
            return {"winners": winners, "pot": self.pot, "hand_type": winning_hand_type}

    def play_hand(self):
        """Play a single hand of poker"""
        self.hand_number += 1
        print(f"\n{'='*50}")
        print(f"HAND #{self.hand_number}")
        print(f"{'='*50}")

        # Reset player state
        for player in self.players:
            player.reset_for_new_hand()

        # Post blinds and deal
        self.post_blinds()
        self.deal_hole_cards()
        self.current_bet = self.big_blind
        self.community_cards = []

        for player in self.players:
            print(f"Player {player.player_id}: {player.hole_cards}")

        # Pre-flop betting
        self.betting_round("Pre-Flop")

        # Check if only one player remains
        active_players = [p for p in self.players if not p.is_folded]
        if len(active_players) == 1:
            self.determine_winner()
            self.button = (self.button + 1) % len(self.players)
            self.pot = 0
            return

        # Reset for next round
        self.reset_round_bets()

        # Flop
        self.community_cards = self.deck.deal(3)
        self.betting_round("Flop")

        if len([p for p in self.players if not p.is_folded]) == 1:
            self.determine_winner()
            self.button = (self.button + 1) % len(self.players)
            self.pot = 0
            return

        # Reset for next round
        self.reset_round_bets()

        # Turn
        self.community_cards += self.deck.deal(1)
        self.betting_round("Turn")

        if len([p for p in self.players if not p.is_folded]) == 1:
            self.determine_winner()
            self.button = (self.button + 1) % len(self.players)
            self.pot = 0
            return

        # Reset for next round
        self.reset_round_bets()

        # River
        self.community_cards += self.deck.deal(1)
        self.betting_round("River")

        # Showdown
        self.determine_winner()
        self.button = (self.button + 1) % len(self.players)
        self.pot = 0

    def print_stacks(self):
        """Print current player stacks"""
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


