"""Game state and mode enumerations for Breakout Precision."""

from enum import Enum, auto


class GameMode(Enum):
    CLASSIC = auto()     # Standard 3 lives, trajectory guide enabled, standard scoring
    PRECISION = auto()   # 1 Life run, trajectory guide forced OFF, 1.5x score multiplier


class GameState(Enum):
    TITLE = auto()        # Main Title Screen
    MODE_SELECT = auto()  # Mode Selection Screen
    READY = auto()        # Ball mounted to paddle waiting for launch
    PLAYING = auto()      # Active physics and gameplay
    PAUSED = auto()       # Freeze frame pause menu
    LEVEL_CLEAR = auto()  # All breakable bricks destroyed
    GAME_OVER = auto()    # Zero lives remaining
    HIGH_SCORES = auto()  # Local High Scores Leaderboard Screen
    SETTINGS = auto()     # Interactive Audio & Volume Settings Screen