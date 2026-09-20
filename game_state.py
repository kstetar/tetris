"""Game state management for Tetris - handles all game logic."""

import random
import json
import os
from config import COLS, ROWS, SHAPES, COLORS, SCORE_PER_LINE, COMBO_BONUS, HIGHSCORE_FILE

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
        self.last_move_time = 0
        self.drop_delay = 0
        self.combo = 0
        self.lines_since_last_piece = 0
        self.bag = []  # 7-bag randomizer
        self.particles = []  # Line clear particles
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
        self.key_queue = []
        self.last_move_time = 0
        self.drop_delay = INITIAL_SPEED
        self.combo = 0
        self.lines_since_last_piece = 0
        self.bag = []
        self.particles = []
    
    def _fill_bag(self):
        """Fill the 7-bag with all 7 pieces."""
        indices = list(range(len(SHAPES)))
        random.shuffle(indices)
        self.bag.extend(indices)
    
    def new_piece(self):
        """Generate a new random piece using 7-bag randomizer."""
        if len(self.bag) < 7:
            self._fill_bag()
        
        shape_idx = self.bag.pop(0)
        
        if self.next_piece is None:
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
            shape_idx = self.bag.pop(0) if self.bag else random.randint(0, len(SHAPES) - 1)
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
    
    def rotate_piece(self, piece, direction=1):
        """Rotate a piece clockwise or counter-clockwise with wall kick support."""
        original_shape = piece["shape"]
        
        # Rotate: transpose + reverse for CW, reverse + transpose for CCW
        if direction > 0:
            rotated = [list(row) for row in zip(*original_shape[::-1])]
        else:
            rotated = [list(row) for row in reversed(list(zip(*original_shape)))]
        
        # Try original position
        if self.is_valid_move(piece["x"], piece["y"], rotated):
            piece["shape"] = rotated
            return True
        
        # Try wall kicks
        kicks = [(1, 0), (-1, 0), (0, -1), (2, 0), (-2, 0)]
        for kick_x, kick_y in kicks:
            if self.is_valid_move(piece["x"] + kick_x, piece["y"] + kick_y, rotated):
                piece["x"] += kick_x
                piece["y"] += kick_y
                piece["shape"] = rotated
                return True
        
        return False
    
    def hard_drop(self):
        """Instantly drop the piece to the bottom."""
        if not self.current_piece:
            return
        
        while self.is_valid_move(self.current_piece["x"], self.current_piece["y"] + 1, self.current_piece["shape"]):
            self.current_piece["y"] += 1
        
        self.drop_delay = INITIAL_SPEED  # Reset speed
        return self.current_piece["y"]
    
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
        """Clear completed lines and update score with combo system."""
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
        old_level = self.level
        self.level = self.lines_cleared_total // 10 + 1
        
        # Calculate score with combo
        if lines_cleared > 0:
            self.combo += 1
            if self.combo > 1:
                self.score += COMBO_BONUS.get(min(self.combo, 7), 500)
            
            base_score = SCORE_PER_LINE.get(lines_cleared, 0) * self.level
            self.score += base_score
            self.lines_since_last_piece = lines_cleared
        else:
            self.combo = 0
            self.lines_since_last_piece = 0
        
        # Level up sound effect
        if self.level > old_level and self.level > 1:
            self.level_up = True
        else:
            self.level_up = False
        
        # Generate particles for line clears
        if lines_cleared > 0:
            self._create_particles(lines_cleared)
        
        return lines_cleared
    
    def _create_particles(self, lines_cleared):
        """Create particle effects for line clears."""
        self.particles = []
        colors = [(255, 255, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        
        for _ in range(lines_cleared * 20):
            particle = {
                "x": random.randint(0, COLS * BLOCK_SIZE),
                "y": random.randint(0, ROWS * BLOCK_SIZE),
                "vx": random.uniform(-3, 3),
                "vy": random.uniform(-3, 3),
                "life": 30,
                "max_life": 30,
                "color": random.choice(colors)
            }
            self.particles.append(particle)
    
    def update_particles(self):
        """Update particle positions and lifetimes."""
        for particle in self.particles[:]:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["life"] -= 1
            if particle["life"] <= 0:
                self.particles.remove(particle)
    
    def get_level(self):
        """Return current level."""
        return self.level
    
    def get_lines_cleared(self):
        """Return total lines cleared."""
        return self.lines_cleared_total
    
    def get_next_piece(self):
        """Return the next piece for preview."""
        return self.next_piece
    
    def get_ghost_y(self):
        """Calculate the ghost piece position."""
        if not self.current_piece:
            return None
        
        ghost_y = self.current_piece["y"]
        while self.is_valid_move(self.current_piece["x"], ghost_y + 1, self.current_piece["shape"]):
            ghost_y += 1
        return ghost_y
    
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
        if len(self.key_queue) < 10:
            self.key_queue.append(key)
    
    def process_key_queue(self):
        """Process all queued key presses."""
        processed = 0
        while self.key_queue:
            key = self.key_queue.pop(0)
            if key == "Left":
                if self.is_valid_move(self.current_piece["x"] - 1, self.current_piece["y"], self.current_piece["shape"]):
                    self.current_piece["x"] -= 1
                    processed += 1
            elif key == "Right":
                if self.is_valid_move(self.current_piece["x"] + 1, self.current_piece["y"], self.current_piece["shape"]):
                    self.current_piece["x"] += 1
                    processed += 1
            elif key == "Down":
                if self.is_valid_move(self.current_piece["x"], self.current_piece["y"] + 1, self.current_piece["shape"]):
                    self.current_piece["y"] += 1
                    processed += 1
            elif key == "Up":
                if self.rotate_piece(self.current_piece):
                    processed += 1
            elif key == "HardDrop":
                self.hard_drop()
                processed += 1
        return processed
