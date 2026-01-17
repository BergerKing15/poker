"""
Enhanced AI player for Texas Hold'em using game theory and win probability
"""

import random
from typing import List, Tuple, Optional
from poker_game import Card, HandEvaluator
from win_probability import WinProbabilityCalculator


class PokerBotType:
    """Defines a player's style: tight/loose and aggressive/passive"""
    
    def __init__(self, name: str, tightness: float, aggression: float):
        """
        Args:
            name: Display name of the type (e.g., "TAG", "LAG", "NIT", "Fish")
            tightness: 0.0 (loose) to 1.0 (tight) - hand selection threshold
            aggression: 0.0 (passive) to 1.0 (aggressive) - tendency to bet/raise vs call
        """
        self.name = name
        self.tightness = tightness  # Probability of folding weak hands
        self.aggression = aggression  # Probability of raising vs calling


class PokerBot:
    """
    Game theory-based poker AI that uses win probability and position awareness
    """
    
    # Predefined player types
    TYPES = {
        "TAG": PokerBotType("TAG (Tight Aggressive)", 0.75, 0.85),      # Pro style
        "LAG": PokerBotType("LAG (Loose Aggressive)", 0.35, 0.80),      # Aggressive
        "CTR": PokerBotType("CTR (Call-Fold)", 0.55, 0.40),             # Passive
        "NIT": PokerBotType("NIT (Nitty)", 0.90, 0.50),                 # Super tight
        "FISH": PokerBotType("FISH (Loose-Passive)", 0.30, 0.20),       # Weak player
    }
    
    def __init__(self, player_id: int, bot_type: Optional[str] = None):
        """
        Initialize a poker bot
        
        Args:
            player_id: The player's ID in the game
            bot_type: One of "TAG", "LAG", "CTR", "NIT", "FISH", or None for random
        """
        self.player_id = player_id
        
        if bot_type and bot_type in self.TYPES:
            self.type = self.TYPES[bot_type]
        else:
            # Random type
            self.type = random.choice(list(self.TYPES.values()))
        
        self.win_prob_calc = WinProbabilityCalculator(num_simulations=1000)
    
    def decide_action(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        current_bet: int,
        to_call: int,
        player_stack: int,
        pot: int,
        position: str,  # "early", "middle", "late"
        num_opponents: int,
        small_blind: int,
        big_blind: int
    ) -> Tuple[str, Optional[int]]:
        """
        Make an action decision based on game theory and position
        
        Args:
            hole_cards: Player's 2 hole cards
            community_cards: Current community cards (0-5)
            current_bet: Current bet amount to match
            to_call: Amount needed to call
            player_stack: Player's remaining stack
            pot: Current pot size
            position: Position relative to button ("early", "middle", "late")
            num_opponents: Number of active opponents
            small_blind: Small blind amount
            big_blind: Big blind amount
        
        Returns:
            Tuple of (action, raise_amount) where:
            - action: "fold", "check", "call", or "raise"
            - raise_amount: Amount to raise (only for "raise" action)
        """
        
        # All-in forced situations
        if to_call > player_stack:
            decision = self._decide_with_limited_equity(
                hole_cards, community_cards, num_opponents, to_call, player_stack
            )
            return decision
        
        # Calculate hand strength
        equity = self._get_equity(hole_cards, community_cards, num_opponents)
        hand_strength = self._evaluate_hand_strength(hole_cards, community_cards)
        
        # Pot odds
        pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0
        
        # Stack depth (useful for position-based decisions)
        stack_depth = player_stack / big_blind if big_blind > 0 else 0
        
        # Position multiplier (late position = looser, early = tighter)
        position_multiplier = self._get_position_multiplier(position)
        
        # Decide action based on equity and position
        return self._make_decision(
            to_call=to_call,
            player_stack=player_stack,
            equity=equity,
            hand_strength=hand_strength,
            pot_odds=pot_odds,
            stack_depth=stack_depth,
            position_multiplier=position_multiplier,
            num_opponents=num_opponents,
            is_preflop=(len(community_cards) == 0),
            current_bet=current_bet
        )
    
    def _get_equity(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int
    ) -> float:
        """Calculate win equity using Monte Carlo"""
        try:
            if num_opponents < 1:
                return 0.5
            
            result = self.win_prob_calc.calculate_win_probability(
                hole_cards,
                community_cards,
                num_opponents
            )
            return result['equity']
        except Exception:
            # Fallback if calculation fails
            return self._simple_hand_strength(hole_cards, community_cards)
    
    def _evaluate_hand_strength(
        self,
        hole_cards: List[Card],
        community_cards: List[Card]
    ) -> float:
        """
        Evaluate hand strength from 0.0 to 1.0
        Returns a normalized value for the hand type
        """
        if len(community_cards) < 3:
            # Pre-flop: evaluate based on hole cards
            return self._preflop_hand_strength(hole_cards)
        
        best_hand = HandEvaluator.find_best_hand(hole_cards, community_cards)
        if not best_hand:
            return 0.0
        
        hand_type = best_hand[0]
        rank = HandEvaluator.HAND_RANKS.get(hand_type, 1)
        
        # Normalize to 0-1 scale
        return rank / 10.0
    
    def _preflop_hand_strength(self, hole_cards: List[Card]) -> float:
        """Evaluate pre-flop hand strength"""
        if len(hole_cards) != 2:
            return 0.0
        
        r1, r2 = hole_cards[0].rank, hole_cards[1].rank
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
                       '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        
        v1, v2 = rank_values[r1], rank_values[r2]
        is_pair = r1 == r2
        is_suited = hole_cards[0].suit == hole_cards[1].suit
        
        # Evaluate: AA-KK pairs = 1.0, AK suited = 0.90, down to 32o = 0.05
        if is_pair:
            high_value = max(v1, v2)
            return 0.60 + (high_value - 2) / 12.0 * 0.40  # Pairs: 0.60-1.0
        elif v1 == 14 or v2 == 14:
            # Ace
            low_value = min(v1, v2)
            base = 0.75 if low_value >= 10 else 0.50 if low_value >= 6 else 0.35
            return base + (0.15 if is_suited else 0.0)
        elif v1 >= 12 or v2 >= 12:
            # KQ, KJ, QJ
            base = 0.55
            return base + (0.10 if is_suited else 0.0)
        elif is_suited:
            high_value = max(v1, v2)
            return 0.30 + (high_value - 2) / 12.0 * 0.20
        else:
            high_value = max(v1, v2)
            return 0.15 + (high_value - 2) / 12.0 * 0.15
    
    def _simple_hand_strength(
        self,
        hole_cards: List[Card],
        community_cards: List[Card]
    ) -> float:
        """Simple fallback hand strength evaluation"""
        best_hand = HandEvaluator.find_best_hand(hole_cards, community_cards)
        if not best_hand:
            return 0.0
        rank = HandEvaluator.HAND_RANKS.get(best_hand[0], 1)
        return rank / 10.0
    
    def _get_position_multiplier(self, position: str) -> float:
        """
        Get position multiplier for hand selection
        Early position = tighter (0.5), late = looser (1.5)
        """
        return {"early": 0.5, "middle": 0.8, "late": 1.3}.get(position, 0.8)
    
    def _make_decision(
        self,
        to_call: int,
        player_stack: int,
        equity: float,
        hand_strength: float,
        pot_odds: float,
        stack_depth: float,
        position_multiplier: float,
        num_opponents: int,
        is_preflop: bool,
        current_bet: int
    ) -> Tuple[str, Optional[int]]:
        """Make final decision based on all factors"""
        
        # Fold threshold adjusted by tightness and position
        fold_threshold = (0.35 + (self.type.tightness * 0.30)) * position_multiplier
        
        # If checking is available, decide check vs bet
        if to_call == 0:
            return self._decide_check_or_bet(
                equity, hand_strength, num_opponents, player_stack, current_bet
            )
        
        # Fold decision
        if equity < fold_threshold:
            return ("fold", None)
        
        # Call threshold - compare equity to pot odds
        # If equity > pot_odds, it's +EV to call
        call_threshold = pot_odds * 0.8  # Require slightly better odds due to variance
        
        if equity >= call_threshold or equity > 0.5:
            # Consider raising
            if random.random() < self.type.aggression and hand_strength > 0.4:
                raise_amount = self._calculate_raise_amount(
                    to_call, player_stack, pot_odds, hand_strength
                )
                return ("raise", raise_amount)
            else:
                return ("call", None)
        else:
            # Fold if equity is too low
            return ("fold", None)
    
    def _decide_check_or_bet(
        self,
        equity: float,
        hand_strength: float,
        num_opponents: int,
        player_stack: int,
        current_bet: int
    ) -> Tuple[str, Optional[int]]:
        """Decide between checking and betting when it's free"""
        
        # Strong hands should bet
        if hand_strength > 0.65 or (equity > 0.65 and num_opponents <= 2):
            if random.random() < self.type.aggression:
                # Bet
                bet_size = int(player_stack * 0.25)
                return ("raise", bet_size)
        
        # Check with weaker hands
        return ("check", None)
    
    def _calculate_raise_amount(
        self,
        to_call: int,
        player_stack: int,
        pot_odds: float,
        hand_strength: float
    ) -> int:
        """Calculate raise amount based on hand strength"""
        
        # Tighter players and more aggressive players raise more
        aggression_factor = self.type.aggression
        
        # Stronger hands = larger raises
        strength_factor = hand_strength
        
        # Base raise: call amount + small aggression raise
        min_raise = to_call
        
        # Max raise: all-in or reasonable aggressive raise
        max_raise = int(player_stack * 0.5)
        
        # Calculate raise amount
        raise_amount = int(min_raise + (max_raise - min_raise) * aggression_factor * strength_factor)
        raise_amount = max(min_raise, min(raise_amount, player_stack))
        
        return raise_amount
    
    def _decide_with_limited_equity(
        self,
        hole_cards: List[Card],
        community_cards: List[Card],
        num_opponents: int,
        to_call: int,
        player_stack: int
    ) -> Tuple[str, Optional[int]]:
        """Decide when all-in is forced (to_call > stack)"""
        
        equity = self._get_equity(hole_cards, community_cards, num_opponents)
        
        # Call if equity suggests it's close or we have reasonable pot odds
        # Otherwise fold if we have time to make the decision
        if equity > 0.40:
            return ("call", None)
        else:
            return ("fold", None)
    
    def __repr__(self) -> str:
        return f"PokerBot-{self.type.name}"


class BotManager:
    """Manages a pool of poker bots with varied types"""
    
    def __init__(self, num_bots: int, mixed_types: bool = True):
        """
        Create a pool of bots
        
        Args:
            num_bots: Number of bots to create
            mixed_types: If True, assign different types; if False, all same
        """
        self.bots = []
        
        if mixed_types:
            # Distribute types evenly across bots
            type_names = list(PokerBot.TYPES.keys())
            for i in range(num_bots):
                bot_type = type_names[i % len(type_names)]
                self.bots.append(PokerBot(i, bot_type))
        else:
            # Random assignment to each bot
            for i in range(num_bots):
                self.bots.append(PokerBot(i))
    
    def get_bot(self, player_id: int) -> Optional[PokerBot]:
        """Get a bot by player ID"""
        for bot in self.bots:
            if bot.player_id == player_id:
                return bot
        return None


if __name__ == "__main__":
    # Example usage
    print("Poker Bot Types:")
    print("=" * 60)
    for name, bot_type in PokerBot.TYPES.items():
        print(f"{name:8} - {bot_type.name}")
        print(f"  Tightness: {bot_type.tightness:.0%} (fold threshold)")
        print(f"  Aggression: {bot_type.aggression:.0%} (raise frequency)")
        print()
    
    # Create sample bots
    print("\nSample Bot Pool:")
    print("=" * 60)
    manager = BotManager(5, mixed_types=True)
    for bot in manager.bots:
        print(f"Player {bot.player_id}: {bot}")
