"""Game configuration constants for Tetris."""

# Board dimensions
COLS = 10
ROWS = 20
BLOCK_SIZE = 30

# Tetromino shapes (I, O, T, L, J, S, Z)
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 0, 0], [1, 1, 1]],  # L
    [[0, 0, 1], [1, 1, 1]],  # J
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]]   # Z
]

# Colors corresponding to shapes (I, O, T, L, J, S, Z)
COLORS = [
    "#00FFFF",  # Cyan (I)
    "#FFFF00",  # Yellow (O)
    "#800080",  # Purple (T)
    "#FFA500",  # Orange (L)
    "#0000FF",  # Blue (J)
    "#00FF00",  # Green (S)
    "#FF0000"   # Red (Z)
]

# Game settings
INITIAL_SPEED = 200  # milliseconds per game tick
SCORE_PER_LINE = 100  # Standard Tetris scoring multiplier

# File paths
HIGHSCORE_FILE = "tetris_highscores.json"

# Sound settings
SOUND_ENABLED = True

# Sound preferences (for easy experimentation)
SOUND_PREFERENCES = {
    "rotation": {"frequency": 800, "duration": 0.1, "type": "sine"},
    "move": {"frequency": 400, "duration": 0.05, "type": "sine"},
    "drop": {"frequency": 200, "duration": 0.1, "type": "sine"},
    "line_clear": {"frequencies": [523, 659, 784, 1047], "duration": 0.15, "type": "arpeggio"},
    "game_over": {"frequencies": [600, 450, 300, 200], "duration": 0.3, "type": "descending"}
}
