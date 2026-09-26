"""Game configuration for Neon Tetris."""

# Board
COLS = 10
ROWS = 20
BLOCK_SIZE = 32
PANEL_WIDTH = 268
WINDOW_PADDING = 0

# Tetrominoes: I O T L J S Z
SHAPES = [
    [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1], [0, 0, 0]],  # T
    [[0, 0, 1], [1, 1, 1], [0, 0, 0]],  # L
    [[1, 0, 0], [1, 1, 1], [0, 0, 0]],  # J
    [[0, 1, 1], [1, 1, 0], [0, 0, 0]],  # S
    [[1, 1, 0], [0, 1, 1], [0, 0, 0]],  # Z
]

PIECE_NAMES = ["I", "O", "T", "L", "J", "S", "Z"]

# Neon palette (RGB)
COLORS = [
    (0, 245, 255),     # I cyan
    (255, 230, 0),     # O yellow
    (210, 80, 255),    # T magenta
    (255, 150, 20),    # L orange
    (50, 110, 255),    # J blue
    (40, 255, 120),    # S green
    (255, 50, 90),     # Z red
]

BACKGROUND_COLOR = (6, 7, 14)
GRID_COLOR = (22, 26, 42)
PANEL_BG = (8, 9, 18)
ACCENT = (0, 245, 255)
ACCENT_2 = (255, 60, 160)

# Timing (milliseconds)
INITIAL_GRAVITY_MS = 800
MIN_GRAVITY_MS = 55
SOFT_DROP_MS = 28
LOCK_DELAY_MS = 500
MAX_LOCK_RESETS = 15
LINE_CLEAR_MS = 260
DAS_DELAY_MS = 160
ARR_MS = 28
ENTRY_DELAY_MS = 80

# Scoring (guideline-ish)
SCORE_PER_LINE = {1: 100, 2: 300, 3: 500, 4: 800}
TSPIN_SCORE = {0: 400, 1: 800, 2: 1200, 3: 1600}
COMBO_BASE = 50
SOFT_DROP_POINTS = 1
HARD_DROP_POINTS = 2
B2B_MULTIPLIER = 1.5

QUEUE_SIZE = 5
HIGHSCORE_FILE = "tetris_highscores.json"
MAX_HIGH_SCORES = 8

SOUND_ENABLED = True
MUSIC_ENABLED = True

# Display
FULLSCREEN_DEFAULT = False
