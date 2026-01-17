#!/usr/bin/env python3
"""
Master test runner for all Poker AI test suites
Runs: game_test_suite.py, win_probability_test_suite.py, test_bot_ai.py
"""

import sys
import time
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr


def run_test_suite(module_name, description):
    """Run a single test suite and return results"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"Module: {module_name}")
    print(f"{'='*70}\n")
    
    try:
        # Dynamically import and run the test module
        if module_name == "game_test_suite":
            import game_test_suite
            # Suppress debug output
            from poker_game import PokerGame
            PokerGame.DEBUG = False
        elif module_name == "win_probability_test_suite":
            import win_probability_test_suite
        elif module_name == "test_bot_ai":
            import test_bot_ai
        else:
            print(f"❌ Unknown module: {module_name}")
            return False
        
        print(f"✓ {description} completed successfully\n")
        return True
    except Exception as e:
        print(f"❌ {description} failed with error:")
        print(f"   {type(e).__name__}: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all test suites and report results"""
    print("\n" + "="*70)
    print("POKER AI - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    test_suites = [
        ("game_test_suite", "Game Logic Tests (92 assertions)"),
        ("win_probability_test_suite", "Win Probability Calculator Tests"),
        ("test_bot_ai", "Bot AI Decision Tests"),
    ]
    
    results = {}
    start_time = time.time()
    
    for module_name, description in test_suites:
        try:
            results[description] = run_test_suite(module_name, description)
        except ImportError as e:
            print(f"⚠️  Skipping {module_name}: {e}\n")
            results[description] = None
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    total = len(results)
    
    for description, result in results.items():
        if result is True:
            status = "✓ PASSED"
        elif result is False:
            status = "✗ FAILED"
        else:
            status = "⊘ SKIPPED"
        print(f"{status:12} | {description}")
    
    print("="*70)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Exit with appropriate code
    if failed > 0:
        sys.exit(1)
    elif passed == 0:
        print("⚠️  No tests were run!")
        sys.exit(2)
    else:
        print("✓ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
