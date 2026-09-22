"""
Configuration constants for Poker AI application
"""

from pathlib import Path

# Resolved from this file so the paths hold no matter the working directory.
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

# UI Configuration
UI_WINDOW_WIDTH = 1200
UI_WINDOW_HEIGHT = 900
UI_BG_COLOR = "#2d5016"
UI_CARD_SIZE = 100  # pixels

# Game Configuration
DEFAULT_NUM_OPPONENTS = 2
DEFAULT_STARTING_STACK = 1000
DEFAULT_BIG_BLIND = 10
DEFAULT_SMALL_BLIND = 5

# AI Configuration
DEFAULT_AI_DELAY = 0.1  # seconds between AI moves
MAX_AI_DELAY = 5.0  # seconds
MIN_AI_DELAY = 0.0  # seconds
AI_DELAY_INCREMENT = 0.1

# Win Probability Calculation
# Simulations a bot runs per post-flop decision. Pre-flop costs nothing now
# (it reads the precomputed table), so this is the whole runtime cost of a bot.
#
# Measured trade-off, six-handed, against a 20,000-simulation reference:
#
#   sims   ms/call   RMS equity error   estimates >0.05 off
#    200      55.8              0.029                   11%
#    100      26.7              0.045                   27%
#     50      14.4              0.057                   32%
#     25       7.5              0.085                   58%
#
# Cost is linear in the count; accuracy falls off a cliff below 50. Calling a
# pot-sized bet needs about 33% equity, so an error past 0.05 near that line
# flips call into fold - which is what the last column is really counting.
BOT_SIMULATIONS = 100

NUM_SIMULATIONS_SETUP = 5000  # simulations during gameplay
NUM_SIMULATIONS_SETUP_SCREEN = 10000  # simulations for info/testing

# Game Strategy
DEFAULT_BOT_TYPE = "TAG"  # Tight-Aggressive

# UI Appearance
CARD_IMAGE_FORMAT = ".png"
CARDS_DIRECTORY = "cards-png-100px"
CARDS_DIR = ASSETS_DIR / CARDS_DIRECTORY

# Pre-computed pre-flop equity, built by tools/build_equity_table.py.
DATA_DIR = PACKAGE_ROOT / "data"
PREFLOP_TABLE_PATH = DATA_DIR / "preflop_equity.json"

# Debug/Logging
ENABLE_DEBUG = False  # Set to True for verbose output
ENABLE_PERFORMANCE_LOGGING = False  # Log performance metrics
