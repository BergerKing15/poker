#!/usr/bin/env python3
"""Run a bot tournament from the command line."""

import sys

from poker.console import enable_utf8_output
from poker.tournament import main, main_with_ui

if __name__ == "__main__":
    enable_utf8_output()
    if "--ui" in sys.argv:
        main_with_ui()
    else:
        main()
