#!/usr/bin/env python3
"""Launch the poker table."""

from poker.console import enable_utf8_output
from poker.ui.game_window import main

if __name__ == "__main__":
    enable_utf8_output()
    main()
