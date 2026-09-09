#!/usr/bin/env python3
"""Run a bot tournament from the command line.

    python run_tournament.py                     # comprehensive run
    python run_tournament.py --ui                # with the analytics dashboard
    python run_tournament.py --log hands.db      # record every hand to SQLite
"""

import argparse

from poker.console import enable_utf8_output
from poker.tournament import BotTournament, main, main_with_ui


def quick_run(hand_log_path):
    """A modest run that exercises the log without taking all evening."""
    configs = [
        {"num_players": 3, "bot_types": ["TAG", "CheckCall", "Random"], "repeat": 4},
        {"num_players": 4, "bot_types": ["NIT", "AllIn", "Limper", "Top10%"], "repeat": 4},
    ]
    tournament = BotTournament()
    tournament.run_tournament(configs, hands_per_game=40, verbose=True,
                              hand_log_path=hand_log_path)
    tournament.print_summary()
    if tournament.hand_log:
        print()
        print(f"Recorded {tournament.hand_log.hands_recorded} hands to {hand_log_path}")
        for row in tournament.hand_log.summary_by_bot():
            print(f"  {row}")
        tournament.hand_log.close()


if __name__ == "__main__":
    enable_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ui", action="store_true", help="show the dashboard")
    parser.add_argument("--log", metavar="PATH",
                        help="record every hand to this SQLite database")
    args = parser.parse_args()

    if args.log:
        quick_run(args.log)
    elif args.ui:
        main_with_ui()
    else:
        main()
