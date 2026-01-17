import random
from typing import List, Tuple, Dict, Optional
from poker_game import Card, Deck, HandEvaluator


class WinProbabilityCalculator:
    """Calculate win probability for a given poker situation"""
    
    def __init__(self, num_simulations: int = 10000):
        """
        Initialize calculator
        
        Args:
            num_simulations: Number of Monte Carlo simulations to run
        """
        self.num_simulations = num_simulations
    
    def calculate_win_probability(
        self,
        player_hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int
    ) -> Dict[str, float]:
        """
        Calculate win probability for a player
        
        Args:
            player_hole_cards: Player's 2 hole cards
            community_cards: Community cards (0, 3, 4, or 5 cards)
            num_opponents: Number of opponents still in the hand
        
        Returns:
            Dictionary with:
            - 'win_prob': Probability of winning outright
            - 'tie_prob': Probability of tying
            - 'lose_prob': Probability of losing
            - 'equity': Win probability + (tie probability / num_players)
        """
        if len(player_hole_cards) != 2:
            raise ValueError("Player must have exactly 2 hole cards")
        
        if len(community_cards) not in [0, 3, 4, 5]:
            raise ValueError("Community cards must be 0, 3, 4, or 5 cards")
        
        if num_opponents < 1:
            raise ValueError("Must have at least 1 opponent")
        
        # Validate no duplicate cards
        all_player_cards = set(str(c) for c in player_hole_cards)
        all_community_cards = set(str(c) for c in community_cards)
        if all_player_cards & all_community_cards:
            raise ValueError("Player cards and community cards have duplicates")
        
        # Run simulations
        wins = 0
        ties = 0
        losses = 0
        
        for _ in range(self.num_simulations):
            result = self._simulate_game(
                player_hole_cards,
                community_cards,
                num_opponents
            )
            
            if result == "win":
                wins += 1
            elif result == "tie":
                ties += 1
            else:
                losses += 1
        
        total = self.num_simulations
        win_prob = wins / total
        tie_prob = ties / total
        lose_prob = losses / total
        
        # Equity = win_prob + (tie_prob / num_players)
        num_players = num_opponents + 1
        equity = win_prob + (tie_prob / num_players)
        
        return {
            'win_prob': win_prob,
            'tie_prob': tie_prob,
            'lose_prob': lose_prob,
            'equity': equity,
            'wins': wins,
            'ties': ties,
            'losses': losses
        }
    
    def _simulate_game(
        self,
        player_hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int
    ) -> str:
        """
        Simulate a single game and return result
        
        Returns:
            "win", "tie", or "loss"
        """
        # Create a fresh deck excluding known cards
        deck = self._create_remaining_deck(player_hole_cards, community_cards)
        
        # Generate opponent hole cards
        opponent_cards = []
        for _ in range(num_opponents):
            opp_hole = [deck.pop(), deck.pop()]
            opponent_cards.append(opp_hole)
        
        # Complete the community cards if needed
        remaining_community = self._complete_community_cards(community_cards, deck)
        
        # Evaluate all hands
        player_hand = HandEvaluator.find_best_hand(player_hole_cards, remaining_community)
        player_rank = HandEvaluator.HAND_RANKS[player_hand[0]]
        player_info = HandEvaluator.evaluate_hand(player_hand[1])
        player_tiebreaker = player_info[1]
        
        # Check opponent hands
        best_opponent_rank = 0
        best_opponent_tiebreaker = None
        opponents_with_best = 0
        
        for opp_hole in opponent_cards:
            opp_hand = HandEvaluator.find_best_hand(opp_hole, remaining_community)
            opp_rank = HandEvaluator.HAND_RANKS[opp_hand[0]]
            opp_info = HandEvaluator.evaluate_hand(opp_hand[1])
            opp_tiebreaker = opp_info[1]
            
            # Compare with current best
            if opp_rank > best_opponent_rank:
                best_opponent_rank = opp_rank
                best_opponent_tiebreaker = opp_tiebreaker
                opponents_with_best = 1
            elif opp_rank == best_opponent_rank and opp_tiebreaker == best_opponent_tiebreaker:
                opponents_with_best += 1
        
        # Determine result
        if player_rank > best_opponent_rank:
            return "win"
        elif player_rank == best_opponent_rank:
            if player_tiebreaker > best_opponent_tiebreaker:
                return "win"
            elif player_tiebreaker == best_opponent_tiebreaker:
                # Tie with at least one opponent
                return "tie"
            else:
                return "loss"
        else:
            return "loss"
    
    def _create_remaining_deck(
        self,
        player_cards: List[Card],
        community_cards: List[Card]
    ) -> List[Card]:
        """
        Create a deck with all known cards removed
        
        Returns:
            List of remaining cards (will be popped from the end)
        """
        # Create set of known card strings for easy lookup
        known_cards = set()
        for card in player_cards + community_cards:
            known_cards.add(str(card))
        
        # Create remaining deck
        remaining = []
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                card = Card(suit, rank)
                if str(card) not in known_cards:
                    remaining.append(card)
        
        random.shuffle(remaining)
        return remaining
    
    def _complete_community_cards(
        self,
        community_cards: List[Card],
        deck: List[Card]
    ) -> List[Card]:
        """
        Complete community cards to 5 cards by drawing from deck
        """
        cards_needed = 5 - len(community_cards)
        new_cards = [deck.pop() for _ in range(cards_needed)]
        return community_cards + new_cards
    
    def get_hand_strength(
        self,
        player_hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int
    ) -> str:
        """
        Get descriptive hand strength (weak, fair, good, very good, excellent)
        """
        result = self.calculate_win_probability(
            player_hole_cards,
            community_cards,
            num_opponents
        )
        
        equity = result['equity']
        num_players = num_opponents + 1
        
        # Categorize based on equity
        if equity < 1 / (num_players * 2):
            return "very weak"
        elif equity < 1 / num_players:
            return "weak"
        elif equity < 1 / num_players + 0.1:
            return "fair"
        elif equity < 1 / num_players + 0.2:
            return "good"
        elif equity < 1 / num_players + 0.35:
            return "very good"
        else:
            return "excellent"
    
    def calculate_vs_specific_hands(
        self,
        player_hole_cards: List[Card],
        community_cards: List[Card],
        opponent_hands: List[List[Card]]
    ) -> Dict[str, float]:
        """
        Calculate win probability vs specific known opponent hands
        (useful for testing/analysis)
        
        Args:
            player_hole_cards: Player's 2 hole cards
            community_cards: Community cards (0, 3, 4, or 5)
            opponent_hands: List of opponent hole card pairs
        
        Returns:
            Similar format to calculate_win_probability
        """
        if len(player_hole_cards) != 2:
            raise ValueError("Player must have exactly 2 hole cards")
        
        if len(community_cards) not in [0, 3, 4, 5]:
            raise ValueError("Community cards must be 0, 3, 4, or 5 cards")
        
        wins = 0
        ties = 0
        losses = 0
        
        num_opponents = len(opponent_hands)
        
        for _ in range(self.num_simulations):
            # Create remaining deck
            all_known = player_hole_cards + community_cards
            for opp_hand in opponent_hands:
                all_known.extend(opp_hand)
            
            deck = self._create_remaining_deck(player_hole_cards, all_known)
            
            # Complete community cards
            remaining_community = self._complete_community_cards(community_cards, deck)
            
            # Evaluate player hand
            player_hand = HandEvaluator.find_best_hand(player_hole_cards, remaining_community)
            player_rank = HandEvaluator.HAND_RANKS[player_hand[0]]
            player_info = HandEvaluator.evaluate_hand(player_hand[1])
            player_tiebreaker = player_info[1]
            
            # Evaluate opponent hands
            best_opponent_rank = 0
            best_opponent_tiebreaker = None
            
            for opp_hole in opponent_hands:
                opp_hand = HandEvaluator.find_best_hand(opp_hole, remaining_community)
                opp_rank = HandEvaluator.HAND_RANKS[opp_hand[0]]
                opp_info = HandEvaluator.evaluate_hand(opp_hand[1])
                opp_tiebreaker = opp_info[1]
                
                if opp_rank > best_opponent_rank:
                    best_opponent_rank = opp_rank
                    best_opponent_tiebreaker = opp_tiebreaker
                elif opp_rank == best_opponent_rank and opp_tiebreaker > best_opponent_tiebreaker:
                    best_opponent_tiebreaker = opp_tiebreaker
            
            # Determine result
            if player_rank > best_opponent_rank:
                wins += 1
            elif player_rank == best_opponent_rank:
                if player_tiebreaker > best_opponent_tiebreaker:
                    wins += 1
                elif player_tiebreaker == best_opponent_tiebreaker:
                    ties += 1
                else:
                    losses += 1
            else:
                losses += 1
        
        total = self.num_simulations
        win_prob = wins / total
        tie_prob = ties / total
        lose_prob = losses / total
        
        num_players = num_opponents + 1
        equity = win_prob + (tie_prob / num_players)
        
        return {
            'win_prob': win_prob,
            'tie_prob': tie_prob,
            'lose_prob': lose_prob,
            'equity': equity,
            'wins': wins,
            'ties': ties,
            'losses': losses
        }


# Example usage and testing
if __name__ == "__main__":
    from poker_game import Card
    
    calculator = WinProbabilityCalculator(num_simulations=10000)
    
    print("="*60)
    print("POKER WIN PROBABILITY CALCULATOR")
    print("="*60)
    
    # Example 1: Pre-flop with AA vs 3 opponents
    print("\nExample 1: Pocket Aces Pre-Flop (vs 3 opponents)")
    print("-" * 60)
    
    player_cards = [Card("Spades", "A"), Card("Hearts", "A")]
    community = []
    
    result = calculator.calculate_win_probability(player_cards, community, 3)
    print(f"Player: AA")
    print(f"Community: (empty)")
    print(f"Opponents: 3")
    print(f"Win Probability: {result['win_prob']:.2%}")
    print(f"Tie Probability: {result['tie_prob']:.2%}")
    print(f"Lose Probability: {result['lose_prob']:.2%}")
    print(f"Equity: {result['equity']:.2%}")
    print(f"Hand Strength: {calculator.get_hand_strength(player_cards, community, 3)}")
    
    # Example 2: Post-flop with made hand
    print("\n\nExample 2: Pair on Flop (vs 2 opponents)")
    print("-" * 60)
    
    player_cards = [Card("Hearts", "K"), Card("Diamonds", "K")]
    community = [Card("Clubs", "K"), Card("Hearts", "5"), Card("Diamonds", "3")]
    
    result = calculator.calculate_win_probability(player_cards, community, 2)
    print(f"Player: KK")
    print(f"Flop: K♣ 5♥ 3♦")
    print(f"Opponents: 2")
    print(f"Win Probability: {result['win_prob']:.2%}")
    print(f"Tie Probability: {result['tie_prob']:.2%}")
    print(f"Lose Probability: {result['lose_prob']:.2%}")
    print(f"Equity: {result['equity']:.2%}")
    print(f"Hand Strength: {calculator.get_hand_strength(player_cards, community, 2)}")
    
    # Example 3: Draw on turn
    print("\n\nExample 3: Open-Ended Straight Draw (vs 1 opponent)")
    print("-" * 60)
    
    player_cards = [Card("Clubs", "K"), Card("Diamonds", "Q")]
    community = [Card("Hearts", "J"), Card("Spades", "10"), Card("Hearts", "3"), Card("Clubs", "2")]
    
    result = calculator.calculate_win_probability(player_cards, community, 1)
    print(f"Player: KQ")
    print(f"Board: J♥ 10♠ 3♥ 2♣")
    print(f"Opponents: 1")
    print(f"Win Probability: {result['win_prob']:.2%}")
    print(f"Tie Probability: {result['tie_prob']:.2%}")
    print(f"Lose Probability: {result['lose_prob']:.2%}")
    print(f"Equity: {result['equity']:.2%}")
    print(f"Hand Strength: {calculator.get_hand_strength(player_cards, community, 1)}")
    
    # Example 4: vs specific hands
    print("\n\nExample 4: AA vs KK Heads-Up (pre-flop)")
    print("-" * 60)
    
    player_cards = [Card("Spades", "A"), Card("Hearts", "A")]
    opponent_cards = [Card("Clubs", "K"), Card("Diamonds", "K")]
    
    result = calculator.calculate_vs_specific_hands(
        player_cards,
        [],
        [opponent_cards]
    )
    print(f"Player: AA")
    print(f"Opponent: KK")
    print(f"Board: (empty)")
    print(f"Win Probability: {result['win_prob']:.2%}")
    print(f"Tie Probability: {result['tie_prob']:.2%}")
    print(f"Lose Probability: {result['lose_prob']:.2%}")
    print(f"Equity: {result['equity']:.2%}")
    
    print("\n" + "="*60)
