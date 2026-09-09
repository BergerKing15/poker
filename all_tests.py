#!/usr/bin/env python3
"""
Master test runner for all Poker AI test suites
Runs: game_test_suite.py, win_probability_test_suite.py, test_bot_ai.py
"""

import importlib
import sys
import time

from poker.console import enable_utf8_output

enable_utf8_output()

from game_test_suite import GameTester


def run_test_suite(module_name, description):
    """Run one suite and report on it.

    Importing a suite is not enough: every test function is called from the
    module's __main__ block, so an import runs nothing at all. Calling the
    test_* functions directly runs the same work while keeping the module (and
    so the GameTester class the tallies live on) shared with this process --
    runpy would re-execute the module in a fresh namespace and register its
    assertions against a different class object.

    Returns (ok, passed, failed).
    """
    print()
    print("=" * 70)
    print(f"Running: {description}")
    print(f"Module: {module_name}")
    print("=" * 70)
    print()

    before_passed, before_failed = GameTester.totals()
    errors = []

    module = importlib.import_module(module_name)
    tests = [fn for name, fn in vars(module).items()
             if name.startswith("test_") and callable(fn)]

    for fn in tests:
        try:
            fn()
        except Exception as e:
            errors.append(f"{fn.__name__}: {type(e).__name__}: {e}")
            print(f"X {fn.__name__} raised {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    after_passed, after_failed = GameTester.totals()
    passed = after_passed - before_passed
    failed = after_failed - before_failed

    print()
    if failed or errors:
        print(f"X {description}: {failed} assertion(s) failed, "
              f"{len(errors)} test(s) raised, across {len(tests)} test function(s)")
    else:
        print(f"OK {description}: {passed} assertion(s) passed "
              f"across {len(tests)} test function(s)")
    print()
    return (failed == 0 and not errors), passed, failed


def main():
    """Run all test suites and report results"""
    print()
    print("=" * 70)
    print("POKER AI - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Keep engine debug output out of the test log.
    from poker.game import PokerGame
    PokerGame.DEBUG = False

    GameTester.reset_totals()

    test_suites = [
        ("game_test_suite", "Game Logic Tests"),
        ("win_probability_test_suite", "Win Probability Calculator Tests"),
        ("test_bot_ai", "Bot AI Decision Tests"),
    ]

    results = {}
    start_time = time.time()

    for module_name, description in test_suites:
        try:
            results[description] = run_test_suite(module_name, description)
        except ImportError as e:
            print(f"! Skipping {module_name}: {e}")
            print()
            results[description] = None

    elapsed_time = time.time() - start_time

    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results.values() if r and r[0])
    failed = sum(1 for r in results.values() if r and not r[0])
    skipped = sum(1 for r in results.values() if r is None)
    total = len(results)

    total_assertions = sum(r[1] for r in results.values() if r)
    total_failures = sum(r[2] for r in results.values() if r)

    for description, result in results.items():
        if result is None:
            status = "SKIPPED"
            detail = ""
        elif result[0]:
            status = "PASSED"
            detail = f"{result[1]} assertions"
        else:
            status = "FAILED"
            detail = f"{result[2]} of {result[1] + result[2]} assertions failed"
        print(f"{status:8} | {description:40} {detail}")

    print("=" * 70)
    print(f"Suites: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    print(f"Assertions: {total_assertions} passed, {total_failures} failed")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    if failed > 0 or total_failures > 0:
        print("Some tests FAILED")
        sys.exit(1)
    elif total_assertions == 0:
        print("No assertions were executed - the runner is not reaching the tests")
        sys.exit(2)
    else:
        print("All tests passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
