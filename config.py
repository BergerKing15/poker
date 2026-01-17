"""
Configuration constants for Poker AI application
"""

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
NUM_SIMULATIONS_SETUP = 5000  # simulations during gameplay
NUM_SIMULATIONS_SETUP_SCREEN = 10000  # simulations for info/testing

# Game Strategy
DEFAULT_BOT_TYPE = "TAG"  # Tight-Aggressive

# UI Appearance
CARD_IMAGE_FORMAT = ".png"
CARDS_DIRECTORY = "cards-png-100px"

# Debug/Logging
ENABLE_DEBUG = False  # Set to True for verbose output
ENABLE_PERFORMANCE_LOGGING = False  # Log performance metrics
