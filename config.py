"""Game configuration constants for Tetris."""

import pygame

# Board dimensions
COLS = 10
ROWS = 20
BLOCK_SIZE = 30

# Tetromino shapes (I, O, T, L, J, S, Z)
SHAPES = [
    [[0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]]   # Z
]

# Enhanced colors with neon glow effect
COLORS = [
    (0, 255, 255, 180),   # Cyan (I) - with alpha for glow
    (255, 255, 0, 180),   # Yellow (O)
    (128, 0, 128, 180),   # Purple (T)
    (255, 165, 0, 180),   # Orange (L)
    (0, 0, 255, 180),     # Blue (J)
    (0, 255, 0, 180),     # Green (S)
    (255, 0, 0, 180)      # Red (Z)
]

# Background colors (dark theme)
BACKGROUND_COLOR = (12, 12, 18)
GRID_COLOR = (20, 20, 30)

# Game settings
INITIAL_SPEED = 800  # milliseconds per game tick (slower start)
SOFT_DROP_SPEED = 50  # Faster speed when holding down
HARD_DROP_SPEED = 5   # Instant hard drop speed
DROP_DELAY = 50       # Delay before auto-repeat

# Scoring (Nintendo system)
SCORE_PER_LINE = {1: 40, 2: 100, 3: 300, 4: 1200}

# Combo bonuses
COMBO_BONUS = {0: 0, 1: 50, 2: 100, 3: 150, 4: 200, 5: 300, 6: 400, 7: 500}

# File paths
HIGHSCORE_FILE = "tetris_highscores.json"

# Sound settings
SOUND_ENABLED = True

# Sound preferences (enhanced)
SOUND_PREFERENCES = {
    "rotate": {"frequency": 880, "duration": 0.05, "type": "sine"},
    "move": {"frequency": 440, "duration": 0.03, "type": "triangle"},
    "drop": {"frequency": 220, "duration": 0.04, "type": "square"},
    "hard_drop": {"frequency": 110, "duration": 0.08, "type": "square"},
    "line_clear": {"frequencies": [523, 659, 784, 1047, 784, 659, 523], "duration": 0.25, "type": "arpeggio"},
    "combo": {"frequencies": [880, 1109, 1319, 1760], "duration": 0.15, "type": "arpeggio"},
    "game_over": {"frequencies": [400, 350, 300, 260, 220, 180], "duration": 0.4, "type": "descending"},
    "level_up": {"frequencies": [523, 659, 784, 1047, 1319, 1568, 2093], "duration": 0.5, "type": "ascending"}
}
