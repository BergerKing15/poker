#!/usr/bin/env python3
"""
Verification script for Poker Bot AI installation
"""

def check_imports():
    """Check all required imports"""
    print("Checking imports...", end=" ")
    try:
        from poker_game import PokerGame, Card, HandEvaluator
        from poker_bot import PokerBot, PokerBotType
        from win_probability import WinProbabilityCalculator
        print("✓")
        return True
    except ImportError as e:
        print(f"✗ {e}")
        return False

def check_bot_types():
    """Check bot types are defined"""
    print("Checking bot types...", end=" ")
    from poker_bot import PokerBot
    
    expected_types = {"TAG", "LAG", "CTR", "NIT", "FISH"}
    actual_types = set(PokerBot.TYPES.keys())
    
    if expected_types == actual_types:
        print(f"✓ ({len(actual_types)} types)")
        return True
    else:
        print(f"✗ Missing: {expected_types - actual_types}")
        return False

def check_game_creation():
    """Check game can be created with bots"""
    print("Creating game with bots...", end=" ")
    try:
        from poker_game import PokerGame
        game = PokerGame(num_players=4, use_bots=True)
        
        # Verify bots created
        bot_count = len([b for b in game.bots.values() if b])
        if bot_count >= 1:
            print(f"✓ ({bot_count} bots)")
            return True
        else:
            print("✗ No bots created")
            return False
    except Exception as e:
        print(f"✗ {e}")
        return False

def check_bot_decision():
    """Check bot can make decisions"""
    print("Testing bot decision making...", end=" ")
    try:
        from poker_game import Card
        from poker_bot import PokerBot
        
        bot = PokerBot(0, "TAG")
        hole = [Card("Spades", "A"), Card("Hearts", "K")]
        community = []
        
        action, raise_amt = bot.decide_action(
            hole_cards=hole,
            community_cards=community,
            current_bet=10,
            to_call=10,
            player_stack=1000,
            pot=20,
            position="late",
            num_opponents=2,
            small_blind=5,
            big_blind=10
        )
        
        if action in ["fold", "check", "call", "raise"]:
            print(f"✓ ({action})")
            return True
        else:
            print(f"✗ Invalid action: {action}")
            return False
    except Exception as e:
        print(f"✗ {e}")
        return False

def check_equity():
    """Check win probability calculation"""
    print("Testing equity calculation...", end=" ")
    try:
        from poker_game import Card
        from win_probability import WinProbabilityCalculator
        
        calc = WinProbabilityCalculator(num_simulations=100)
        hole = [Card("Spades", "A"), Card("Hearts", "A")]
        result = calc.calculate_win_probability(hole, [], 1)
        
        equity = result.get('equity', 0)
        if 0.5 < equity <= 1.0:
            print(f"✓ (AA equity: {equity:.1%})")
            return True
        else:
            print(f"✗ Invalid equity: {equity}")
            return False
    except Exception as e:
        print(f"✗ {e}")
        return False

def check_files():
    """Check all required files exist"""
    print("Checking files...", end=" ")
    import os
    
    required = [
        "poker_game.py",
        "poker_bot.py",
        "win_probability.py",
        "poker_ui.py",
        "game_test_suite.py",
        "BOT_AI_GUIDE.md",
        "BOT_QUICK_REFERENCE.md",
    ]
    
    missing = [f for f in required if not os.path.exists(f)]
    
    if not missing:
        print(f"✓ ({len(required)} files)")
        return True
    else:
        print(f"✗ Missing: {missing}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("POKER BOT AI - INSTALLATION VERIFICATION")
    print("=" * 60)
    print()
    
    checks = [
        ("File integrity", check_files),
        ("Import system", check_imports),
        ("Bot types", check_bot_types),
        ("Game creation", check_game_creation),
        ("Bot decisions", check_bot_decision),
        ("Equity calc", check_equity),
    ]
    
    results = []
    for name, check_fn in checks:
        results.append(check_fn())
    
    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        print("=" * 60)
        print("\nYour Poker Bot AI system is ready!")
        print("\nQuick start:")
        print("  python poker_ui.py          # Play the game")
        print("  python test_bot_ai.py       # Test AI system")
        print("  python game_test_suite.py   # Run all tests")
        print("\nDocumentation:")
        print("  BOT_AI_GUIDE.md             # Comprehensive guide")
        print("  BOT_QUICK_REFERENCE.md      # Quick reference")
    else:
        print(f"✗ SOME CHECKS FAILED ({passed}/{total})")
        print("=" * 60)
    
    print()
