"""
Test script demonstrating the poker bot AI system
"""

from poker_game import PokerGame, Card
from poker_bot import PokerBot

def test_bot_types():
    """Display and test different bot types"""
    print("=" * 70)
    print("POKER BOT AI TEST")
    print("=" * 70)
    
    # Show all bot types
    print("\n1. Available Bot Types:")
    print("-" * 70)
    for name, bot_type in PokerBot.TYPES.items():
        print(f"\n{name:8} - {bot_type.name}")
        print(f"  Tightness:  {bot_type.tightness:.0%}")
        print(f"  Aggression: {bot_type.aggression:.0%}")


def test_preflop_decisions():
    """Test bot decision making pre-flop"""
    print("\n\n2. Pre-flop Hand Strength Evaluation:")
    print("-" * 70)
    
    bot = PokerBot(0, "TAG")
    
    test_hands = [
        (Card("Spades", "A"), Card("Hearts", "A"), "AA (Pocket Aces)"),
        (Card("Spades", "K"), Card("Hearts", "K"), "KK (Pocket Kings)"),
        (Card("Spades", "A"), Card("Hearts", "K"), "AK (Big Slick)"),
        (Card("Spades", "A"), Card("Diamonds", "K"), "AK (offsuit)"),
        (Card("Spades", "Q"), Card("Hearts", "Q"), "QQ (Pocket Queens)"),
        (Card("Spades", "7"), Card("Hearts", "2"), "72 (The Hammer)"),
        (Card("Spades", "K"), Card("Hearts", "J"), "KJ (Nice hand)"),
    ]
    
    for card1, card2, name in test_hands:
        strength = bot._preflop_hand_strength([card1, card2])
        print(f"{name:20} -> Strength: {strength:.2f} ({strength:.0%})")


def test_position_multiplier():
    """Test position multipliers"""
    print("\n\n3. Position Multipliers:")
    print("-" * 70)
    
    bot = PokerBot(0, "TAG")
    
    positions = [
        ("early", "Early Position (UTG, UTG+1)"),
        ("middle", "Middle Position (MP, MP+1)"),
        ("late", "Late Position (CO, Button)"),
    ]
    
    for pos, desc in positions:
        mult = bot._get_position_multiplier(pos)
        print(f"{desc:30} -> {mult:.2f}x multiplier")


def test_game_with_bots():
    """Create a game and show bot initialization"""
    print("\n\n4. Game with Bot Integration:")
    print("-" * 70)
    
    game = PokerGame(num_players=6, starting_stack=1000, use_bots=True)
    
    print(f"Created game with {len(game.players)} players:")
    for player in game.players:
        if player.player_id == 0:
            print(f"Player {player.player_id}: HUMAN")
        else:
            bot = game.bots.get(player.player_id)
            bot_type = bot.type.name if bot else "Simple AI"
            print(f"Player {player.player_id}: {bot_type}")


def test_bot_decision():
    """Test a specific bot decision"""
    print("\n\n5. Bot Decision Making Example:")
    print("-" * 70)
    
    # Create a TAG bot (Tight Aggressive)
    bot = PokerBot(1, "TAG")
    
    # Create some cards
    hole_cards = [Card("Spades", "A"), Card("Hearts", "K")]
    community = [Card("Clubs", "A"), Card("Diamonds", "7"), Card("Hearts", "2")]
    
    # Get decision
    action, raise_amount = bot.decide_action(
        hole_cards=hole_cards,
        community_cards=community,
        current_bet=100,
        to_call=50,
        player_stack=1000,
        pot=300,
        position="late",
        num_opponents=2,
        small_blind=5,
        big_blind=10
    )
    
    print(f"Scenario: TAG bot with AK on flop A72 (after 50-100 raise)")
    print(f"Position: late | Pot: $300 | Stack: $1000")
    print(f"Decision: {action.upper()}", end="")
    if raise_amount:
        print(f" (raise by ${raise_amount})")
    else:
        print()


def test_different_positions():
    """Test how position affects decisions"""
    print("\n\n6. Position Impact on Decisions:")
    print("-" * 70)
    
    bot_tag = PokerBot(0, "TAG")
    
    # Same weak hand, different positions
    hole_cards = [Card("Spades", "7"), Card("Hearts", "6")]
    community = []
    
    positions = ["early", "middle", "late"]
    
    print("Test: 76o (seven-six offsuit) pre-flop vs 50 bet with 1000 stack")
    
    for pos in positions:
        strength = bot_tag._preflop_hand_strength(hole_cards)
        multiplier = bot_tag._get_position_multiplier(pos)
        adjusted = strength * multiplier
        
        print(f"\n{pos.upper():8} - Hand strength: {strength:.2f}, Multiplier: {multiplier:.2f}x")
        print(f"         Adjusted: {adjusted:.2f}")
        
        # Determine fold threshold
        fold_threshold = (0.35 + bot_tag.type.tightness * 0.30) * multiplier
        print(f"         Fold threshold: {fold_threshold:.2f}")
        print(f"         Decision: {'FOLD' if adjusted < fold_threshold else 'CONSIDER'}")


if __name__ == "__main__":
    test_bot_types()
    test_preflop_decisions()
    test_position_multiplier()
    test_game_with_bots()
    test_bot_decision()
    test_different_positions()
    
    print("\n\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
