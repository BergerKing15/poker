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
    
    # Shared win probability calculator (1 per process, not per bot)
    _shared_win_prob_calc = None
    
    @classmethod
    def get_shared_calculator(cls, num_simulations=200):
        """Get or create shared WinProbabilityCalculator"""
        if cls._shared_win_prob_calc is None:
            cls._shared_win_prob_calc = WinProbabilityCalculator(num_simulations=num_simulations)
        return cls._shared_win_prob_calc
    
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
        
        # Use shared calculator instead of creating new instance per bot
        self.win_prob_calc = self.get_shared_calculator()
    
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
        
        # Fold threshold strongly adjusted by tightness
        # Loose players (LAG, FISH) fold less: 1.0 - 0.35 = 0.65 multiplier
        # Tight players (TAG, NIT) fold more: 1.0 - 0.90 = 0.10 multiplier
        looseness = 1.0 - self.type.tightness
        fold_threshold = (0.20 + (self.type.tightness * 0.25)) * position_multiplier
        fold_threshold = fold_threshold * (0.3 + looseness * 0.5)  # Loose players fold way less
        
        # If checking is available, decide check or bet
        if to_call == 0:
            return self._decide_check_or_bet(
                equity, hand_strength, num_opponents, player_stack, current_bet
            )
        
        # Fold decision
        if equity < fold_threshold:
            return ("fold", None)
        
        # Call threshold - compare equity to pot odds
        # Loose/aggressive players are willing to call with lower equity
        call_threshold = pot_odds * (0.5 + self.type.aggression * 0.3)
        
        if equity >= call_threshold or equity > (0.35 - looseness * 0.15):
            # Consider raising - aggressive players raise more often
            raise_probability = self.type.aggression * (0.4 + looseness * 0.4)
            if random.random() < raise_probability and hand_strength > (0.3 - looseness * 0.1):
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
        
        # Aggressive players bet more often, even with moderate hands
        looseness = 1.0 - self.type.tightness
        
        # Strong hands should bet
        bet_threshold = 0.55 - (self.type.aggression * 0.15) - (looseness * 0.1)
        if hand_strength > bet_threshold or (equity > 0.60 and num_opponents <= 2):
            if random.random() < self.type.aggression:
                # Bet
                bet_size = int(player_stack * (0.20 + self.type.aggression * 0.15))
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


# ============================================================================
# SIMPLE STRATEGY BOTS FOR BASELINE COMPARISON AND ML TRAINING
# ============================================================================

# Card.RANKS spells ten as "10", but hand keys use the standard one-character
# poker notation ("AT", "T9o"), so ten is folded to "T" when building a key.
RANK_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
               '10': 10, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

HAND_KEY_RANKS = {'10': 'T'}


def hand_key(hole_cards, include_suitedness: bool = False) -> str:
    """Canonical starting-hand notation, high card first (e.g. "AK", "JJ", "T9o")."""
    r1, r2 = hole_cards[0].rank, hole_cards[1].rank
    v1, v2 = RANK_VALUES[r1], RANK_VALUES[r2]
    k1, k2 = HAND_KEY_RANKS.get(r1, r1), HAND_KEY_RANKS.get(r2, r2)

    if v1 == v2:
        return f"{k1}{k2}"

    high, low = (k1, k2) if v1 > v2 else (k2, k1)
    if include_suitedness:
        suited = "s" if hole_cards[0].suit == hole_cards[1].suit else "o"
        return f"{high}{low}{suited}"
    return f"{high}{low}"


class SimpleBotTop10Percent:
    """Only plays top 10% of hands pre-flop, calls post-flop"""
    
    TOP_10_PERCENT = {
        'AA', 'KK', 'QQ', 'JJ', 'TT',
        'AK', 'AQ', 'AJ', 'AT',
        'KQ', 'KJ',
    }
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "Top10%"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Always fold unless top 10% hand pre-flop"""
        if len(community_cards) == 0:  # Pre-flop
            hand_key = self._get_hand_key(hole_cards)
            if hand_key not in self.TOP_10_PERCENT:
                return ("fold", None)
        
        # Post-flop: always call/check
        if to_call == 0:
            return ("check", None)
        elif to_call > player_stack:
            return ("call", None)  # All-in
        else:
            return ("call", None)
    
    def _get_hand_key(self, hole_cards):
        """Get canonical hand representation"""
        return hand_key(hole_cards)


class SimpleBotAlwaysAllIn:
    """Always goes all-in"""
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "AllIn"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Always go all-in"""
        return ("raise", max(player_stack, to_call))


class SimpleBotCheckCall:
    """Always checks or calls, never raises or folds (except forced situations)"""
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "CheckCall"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Always check or call"""
        if to_call == 0:
            return ("check", None)
        elif to_call > player_stack:
            return ("call", None)  # All-in call
        else:
            return ("call", None)


class SimpleBotNeverFold:
    """Never folds, always calls or raises"""
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "NeverFold"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Never fold, always call or occasionally raise"""
        if to_call == 0:
            # Check or bet
            if random.random() < 0.3:  # 30% chance to raise
                return ("raise", int(player_stack * 0.1))
            return ("check", None)
        elif to_call > player_stack:
            return ("call", None)  # All-in
        else:
            # Occasionally raise instead of call
            if random.random() < 0.2:
                return ("raise", to_call * 2)
            return ("call", None)


class SimpleBotAlwaysRaise:
    """Always raises pre-flop, calls post-flop"""
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "AlwaysRaise"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Always raise pre-flop, call post-flop"""
        if len(community_cards) == 0:  # Pre-flop
            if to_call == 0:
                return ("raise", int(big_blind * 2))
            elif to_call > player_stack:
                return ("call", None)  # All-in
            else:
                return ("raise", max(to_call * 2, int(big_blind * 3)))
        else:  # Post-flop
            if to_call == 0:
                return ("check", None)
            elif to_call > player_stack:
                return ("call", None)
            else:
                return ("call", None)


class SimpleBotBottom50Percent:
    """Only plays bottom 50% of hands (worst hands)"""
    
    BOTTOM_50_PERCENT = {
        '72o', '73o', '74o', '75o', '76o', '77', '78o', '79o', '7T', '7Jo',
        '82o', '83o', '84o', '85o', '86o', '87o', '88', '89o', '8T', '8Jo', '8Qo',
        '92o', '93o', '94o', '95o', '96o', '97o', '98o', '99', '9T', '9Jo', '9Qo', '9Ko',
        'T2o', 'T3o', 'T4o', 'T5o', 'T6o', 'T7o', 'T8o', 'T9o', 'TT', 'TJo', 'TQo',
        'J2o', 'J3o', 'J4o', 'J5o', 'J6o', 'J7o', 'J8o', 'J9o', 'JT', 'JJ',
        'Q2o', 'Q3o', 'Q4o', 'Q5o', 'Q6o', 'Q7o', 'Q8o', 'Q9o',
        'K2o', 'K3o', 'K4o', 'K5o', 'K6o', 'K7o', 'K8o',
        'A2o', 'A3o', 'A4o', 'A5o', 'A6o', 'A7o',
    }
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "Bottom50%"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Only play worst 50% of hands"""
        if len(community_cards) == 0:  # Pre-flop
            hand_key = self._get_hand_key(hole_cards)
            if hand_key not in self.BOTTOM_50_PERCENT:
                return ("fold", None)
        
        # Post-flop: call/check
        if to_call == 0:
            return ("check", None)
        elif to_call > player_stack:
            return ("call", None)
        else:
            return ("call", None)
    
    def _get_hand_key(self, hole_cards):
        """Get canonical hand representation"""
        return hand_key(hole_cards, include_suitedness=True)


class SimpleBotNeverBet:
    """Folds most hands, only calls with premium hands"""
    
    PREMIUM_HANDS = {'AA', 'KK', 'QQ', 'AK', 'AQ'}
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "NeverBet"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Only call/check with premium hands pre-flop, fold post-flop"""
        if len(community_cards) == 0:  # Pre-flop
            hand_key = self._get_hand_key(hole_cards)
            if hand_key not in self.PREMIUM_HANDS:
                return ("fold", None)
        else:  # Post-flop - fold most hands
            if random.random() < 0.7:  # 70% fold rate post-flop
                return ("fold", None)
        
        # Call/check when not folding
        if to_call == 0:
            return ("check", None)
        elif to_call > player_stack:
            return ("call", None)
        else:
            return ("call", None)
    
    def _get_hand_key(self, hole_cards):
        """Get canonical hand representation"""
        return hand_key(hole_cards)


class SimpleBotLimper:
    """Limps pre-flop (calls without raising), calls post-flop"""
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "Limper"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Limp (min-call) pre-flop, call post-flop"""
        if to_call == 0:
            return ("check", None)
        elif to_call > player_stack:
            return ("call", None)  # All-in
        else:
            return ("call", None)  # Always just call (limp)


class SimpleBotFolder:
    """Folds almost everything except blinds"""
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "Folder"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Fold everything except big blind"""
        if to_call == 0:
            # In big blind, check
            return ("check", None)
        else:
            # Fold almost everything
            if random.random() < 0.95:  # 95% fold rate
                return ("fold", None)
            else:
                # Occasionally call
                if to_call > player_stack:
                    return ("call", None)
                else:
                    return ("call", None)


class SimpleBotPositionBased:
    """Play loose in late position, tight in early position"""
    
    EARLY_HANDS = {'AA', 'KK', 'QQ', 'JJ', 'AK', 'AQ'}
    LATE_HANDS = {
        'AA', 'KK', 'QQ', 'JJ', 'TT', 'AK', 'AQ', 'AJ', 'AT',
        'KQ', 'KJ', 'QJ', '22', '33', '44', '55', '66', '77', '88', '99',
    }
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "PositionBased"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Play position-based hand selection"""
        if len(community_cards) == 0:  # Pre-flop
            hand_key = self._get_hand_key(hole_cards)
            
            if position == "early":
                allowed_hands = self.EARLY_HANDS
            elif position == "late":
                allowed_hands = self.LATE_HANDS
            else:  # middle
                allowed_hands = self.LATE_HANDS
            
            if hand_key not in allowed_hands:
                return ("fold", None)
        
        # Post-flop: call/check
        if to_call == 0:
            return ("check", None)
        elif to_call > player_stack:
            return ("call", None)
        else:
            return ("call", None)
    
    def _get_hand_key(self, hole_cards):
        """Get canonical hand representation"""
        return hand_key(hole_cards)


class SimpleBotStackBased:
    """Adjusts strategy based on stack depth"""
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "StackBased"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Play tighter/looser based on stack depth"""
        stack_depth = player_stack / big_blind if big_blind > 0 else 0
        
        if len(community_cards) == 0:  # Pre-flop
            hand_key = self._get_hand_key(hole_cards)
            
            # Determine hand quality
            r1, r2 = hole_cards[0].rank, hole_cards[1].rank
            v1, v2 = RANK_VALUES[r1], RANK_VALUES[r2]
            avg_value = (v1 + v2) / 2
            is_pair = r1 == r2
            
            # Deep stacks: play loose
            if stack_depth > 50:
                if avg_value < 7 and not is_pair:
                    return ("fold", None)
            # Medium stacks: play normal
            elif stack_depth > 20:
                if avg_value < 5 and not is_pair:
                    return ("fold", None)
            # Short stacks: play tight
            else:
                if avg_value < 10 or (is_pair and v1 < 8):
                    return ("fold", None)
        
        # Post-flop: call/check
        if to_call == 0:
            return ("check", None)
        elif to_call > player_stack:
            return ("call", None)
        else:
            return ("call", None)
    
    def _get_hand_key(self, hole_cards):
        """Get canonical hand representation"""
        return hand_key(hole_cards)


class SimpleBotRandom:
    """Plays completely randomly"""
    
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.name = "Random"
    
    def decide_action(self, hole_cards, community_cards, current_bet, to_call,
                      player_stack, pot, position, num_opponents,
                      small_blind, big_blind):
        """Random action"""
        action = random.choice(["fold", "check/call", "raise"])
        
        if action == "fold":
            return ("fold", None)
        elif action == "check/call":
            if to_call == 0:
                return ("check", None)
            else:
                amount = min(to_call, player_stack)
                return ("call", None)
        else:  # raise
            if to_call == 0:
                raise_amount = random.randint(1, int(player_stack * 0.5))
                return ("raise", raise_amount)
            else:
                raise_amount = min(random.randint(to_call, int(player_stack * 0.7)), player_stack)
                return ("raise", raise_amount)

