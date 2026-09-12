"""Game state management for Tetris - handles all game logic."""

import random
import json
import os
from config import COLS, ROWS, SHAPES, COLORS, SCORE_PER_LINE, HIGHSCORE_FILE


class GameState:
    """Manages all game state and logic without any rendering."""
    
    def __init__(self):
        self.board = None
        self.score = 0
        self.lines_cleared_total = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.current_piece = None
        self.next_piece = None
        self.high_score = 0
        self.key_queue = []  # Input buffer for rapid key presses
        self.reset()
    
    def reset(self):
        """Reset the game state to initial values."""
        self.board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.lines_cleared_total = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.high_score = self.load_highscores()
        self.key_queue = []  # Clear input buffer on reset
    
    def new_piece(self):
        """Generate a new random piece."""
        if self.next_piece is None:
            shape_idx = random.randint(0, len(SHAPES) - 1)
            piece = {
                "shape": SHAPES[shape_idx],
                "color": COLORS[shape_idx],
                "x": COLS // 2 - len(SHAPES[shape_idx][0]) // 2,
                "y": 0
            }
        else:
            piece = self.next_piece
            piece["x"] = COLS // 2 - len(piece["shape"][0]) // 2
            piece["y"] = 0
            shape_idx = random.randint(0, len(SHAPES) - 1)
            self.next_piece = {
                "shape": SHAPES[shape_idx],
                "color": COLORS[shape_idx],
                "x": COLS // 2 - len(SHAPES[shape_idx][0]) // 2,
                "y": 0
            }
        return piece
    
    def is_valid_move(self, x, y, shape):
        """Check if a piece can be placed at the given position."""
        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    new_x = x + col_idx
                    new_y = y + row_idx
                    
                    if (new_x < 0 or new_x >= COLS or 
                        new_y >= ROWS or 
                        (new_y >= 0 and self.board[new_y][new_x])):
                        return False
        return True
    
    def rotate_piece(self, piece):
        """Rotate a piece clockwise with wall kick support."""
        original_shape = piece["shape"]
        # Transpose and reverse for rotation
        rotated = [list(row) for row in zip(*original_shape[::-1])]
        
        # Try original position
        if self.is_valid_move(piece["x"], piece["y"], rotated):
            piece["shape"] = rotated
            return
        
        # Try wall kick - shift left
        if self.is_valid_move(piece["x"] - 1, piece["y"], rotated):
            piece["x"] -= 1
            piece["shape"] = rotated
            return
        
        # Try wall kick - shift right
        if self.is_valid_move(piece["x"] + 1, piece["y"], rotated):
            piece["x"] += 1
            piece["shape"] = rotated
            return
    
    def merge_piece_to_board(self):
        """Lock the current piece into the board."""
        for row_idx, row in enumerate(self.current_piece["shape"]):
            for col_idx, cell in enumerate(row):
                if cell:
                    board_y = self.current_piece["y"] + row_idx
                    board_x = self.current_piece["x"] + col_idx
                    if 0 <= board_y < ROWS:
                        self.board[board_y][board_x] = self.current_piece["color"]
    
    def clear_lines(self):
        """Clear completed lines and update score."""
        lines_cleared = 0
        new_board = []
        
        for row in self.board:
            if 0 in row:
                new_board.append(row)
            else:
                lines_cleared += 1
        
        # Add new empty lines at the top
        for _ in range(lines_cleared):
            new_board.insert(0, [0 for _ in range(COLS)])
        
        self.board = new_board

        # Update lines cleared total and level
        self.lines_cleared_total += lines_cleared
        self.level = self.lines_cleared_total // 10 + 1

        # Standard Tetris scoring: 40, 100, 300, 1200 * level
        line_scores = {1: 40, 2: 100, 3: 300, 4: 1200}
        if lines_cleared > 0:
            self.score += line_scores.get(lines_cleared, 0) * self.level
        return lines_cleared
    
    def get_level(self):
        """Return current level."""
        return self.level

    def get_lines_cleared(self):
        """Return total lines cleared."""
        return self.lines_cleared_total

    def get_next_piece(self):
        """Return the next piece for preview."""
        return self.next_piece
    
    def check_high_score(self):
        """Check if current score beats the high score and update if needed."""
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_highscores()
            return True
        return False
    
    def load_highscores(self):
        """Load high scores from file."""
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0
    
    def save_highscores(self):
        """Save high scores to file."""
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump({"high_score": self.high_score}, f, indent=2)

    def queue_key(self, key):
        """Add a key press to the input buffer."""
        # Limit queue size to prevent unbounded growth
        if len(self.key_queue) < 10:
            self.key_queue.append(key)

    def process_key_queue(self):
        """Process all queued key presses."""
        processed = 0
        while self.key_queue:
            key = self.key_queue.pop(0)
            if key == "Left":
                if self.is_valid_move(
                    self.current_piece["x"] - 1,
                    self.current_piece["y"],
                    self.current_piece["shape"]
                ):
                    self.current_piece["x"] -= 1
                    processed += 1
            elif key == "Right":
                if self.is_valid_move(
                    self.current_piece["x"] + 1,
                    self.current_piece["y"],
                    self.current_piece["shape"]
                ):
                    self.current_piece["x"] += 1
                    processed += 1
            elif key == "Down":
                if self.is_valid_move(
                    self.current_piece["x"],
                    self.current_piece["y"] + 1,
                    self.current_piece["shape"]
                ):
                    self.current_piece["y"] += 1
                    processed += 1
            elif key == "Up":
                self.rotate_piece(self.current_piece)
                processed += 1
        return processed
