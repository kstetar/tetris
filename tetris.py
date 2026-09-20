"""Pygame entry point for the Tetris game."""

import pygame
import sys

from config import BLOCK_SIZE, COLS, INITIAL_SPEED, ROWS, SOFT_DROP_SPEED
from game_state import GameState
from renderer import Renderer
from sound import SoundManager


class TetrisGame:
    """Coordinate game state, Pygame events, rendering, and sound."""

    def __init__(self, screen):
        self.screen = screen
        self.renderer = Renderer(screen)
        self.game_state = GameState()
        self.sound = SoundManager()
        self.clock = pygame.time.Clock()
        self.running = True
        self.last_tick = pygame.time.get_ticks()
        self.drop_tick = pygame.time.get_ticks()
        self.reset_game()

    def reset_game(self, event=None):
        """Reset the game to its initial state."""
        self.game_state.reset()
        self.renderer.update_score_label(self.game_state.score)
        self.renderer.update_high_score_label(self.game_state.high_score)
        self.renderer.update_level_label(self.game_state.level)
        self.renderer.update_lines_label(self.game_state.lines_cleared_total)
        self.renderer.update_combo(0)
        self.renderer.draw_next_piece(self.game_state.get_next_piece())
        self.last_tick = pygame.time.get_ticks()
        self.drop_tick = pygame.time.get_ticks()

    def handle_key(self, key):
        """Handle one supported keyboard key."""
        if key in (pygame.K_ESCAPE, pygame.K_q):
            self.running = False
            return
        if key == pygame.K_F5:
            self.reset_game()
            return
        if key == pygame.K_p:
            self.game_state.paused = not self.game_state.paused
            return
        if self.game_state.game_over or self.game_state.paused:
            return

        # Map keys to actions
        key_actions = {
            pygame.K_LEFT: ("Left", "move"),
            pygame.K_RIGHT: ("Right", "move"),
            pygame.K_DOWN: ("Down", "drop"),
            pygame.K_UP: ("Up", "rotate"),
            pygame.K_SPACE: ("HardDrop", "hard_drop"),
        }
        
        action_info = key_actions.get(key)
        if action_info is None:
            return
        
        action_name, sound_type = action_info
        self.game_state.queue_key(action_name)
        
        if sound_type == "move":
            self.sound.play_move()
        elif sound_type == "rotate":
            self.sound.play_rotate()
        elif sound_type == "hard_drop":
            self.sound.play_hard_drop()

    def update(self):
        """Advance the game when the configured tick interval elapses."""
        now = pygame.time.get_ticks()
        
        # Handle game over or paused
        if self.game_state.game_over or self.game_state.paused:
            self.game_state.update_particles()
            return
        
        # Speed based on level and soft drop
        if self.game_state.drop_delay == SOFT_DROP_SPEED:
            current_speed = SOFT_DROP_SPEED
        else:
            # Calculate speed based on level (faster as levels progress)
            base_speed = INITIAL_SPEED
            level_multiplier = max(0.5, 1.0 - (self.game_state.level - 1) * 0.05)
            current_speed = int(base_speed * level_multiplier)
        
        # Check if it's time to move piece down
        if now - self.drop_tick >= current_speed:
            self.drop_tick = now
            
            # Check if piece can move down
            if self.game_state.is_valid_move(
                self.game_state.current_piece["x"],
                self.game_state.current_piece["y"] + 1,
                self.game_state.current_piece["shape"]
            ):
                self.game_state.current_piece["y"] += 1
                self.sound.play_drop()
            else:
                # Lock the piece
                self.game_state.merge_piece_to_board()
                lines_cleared = self.game_state.clear_lines()
                
                if lines_cleared > 0:
                    self.sound.play_line_clear()
                    # Combo check
                    if self.game_state.combo > 1:
                        self.sound.play_combo()
                    # Level up check
                    if self.game_state.level_up:
                        self.sound.play_level_up()
                        self.renderer.set_level_up_effect()
                
                # Spawn new piece
                self.game_state.current_piece = self.game_state.new_piece()
                
                # Check for game over
                if not self.game_state.is_valid_move(
                    self.game_state.current_piece["x"],
                    self.game_state.current_piece["y"],
                    self.game_state.current_piece["shape"]
                ):
                    self.game_state.game_over = True
                    self.game_state.check_high_score()
                    self.sound.play_game_over()
        
        # Process input queue
        self.game_state.process_key_queue()
        
        # Update particles
        self.game_state.update_particles()

    def draw(self):
        """Render the current game state."""
        piece = self.game_state.current_piece
        ghost_piece = None
        
        if piece:
            ghost_y = self.game_state.get_ghost_y()
            ghost_piece = {
                "shape": piece["shape"],
                "color": piece["color"],
                "x": piece["x"],
                "y": ghost_y,
            }

        # Update renderer with current game state
        self.renderer.update_score_label(self.game_state.score)
        self.renderer.update_high_score_label(self.game_state.high_score)
        self.renderer.update_level_label(self.game_state.level)
        self.renderer.update_lines_label(self.game_state.lines_cleared_total)
        self.renderer.update_combo(self.game_state.combo)
        self.renderer.update_particles(self.game_state.particles)
        self.renderer.draw_next_piece(self.game_state.get_next_piece())
        
        self.renderer.draw_board(self.game_state.board, piece, ghost_piece)
        
        # Draw level up effect
        self.renderer.draw_level_up()
        
        if self.game_state.game_over:
            self.renderer.draw_game_over(self.game_state.score)
        elif self.game_state.paused:
            self.renderer.draw_pause_indicator()
        
        pygame.display.flip()

    def run(self):
        """Run the event and rendering loop."""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)
                elif event.type == pygame.KEYUP:
                    # Reset drop speed when releasing down key
                    if event.key == pygame.K_DOWN:
                        self.game_state.drop_delay = INITIAL_SPEED
            
            # Check for held keys
            keys = pygame.key.get_pressed()
            if not self.game_state.game_over and not self.game_state.paused:
                if keys[pygame.K_DOWN]:
                    self.game_state.drop_delay = SOFT_DROP_SPEED
            
            self.update()
            self.draw()
            self.clock.tick(120)


if __name__ == "__main__":
    pygame.init()
    
    try:
        screen = pygame.display.set_mode(
            (COLS * BLOCK_SIZE + Renderer.PANEL_WIDTH, ROWS * BLOCK_SIZE)
        )
    except pygame.error as error:
        pygame.quit()
        raise SystemExit(f"Unable to create the game window: {error}") from error

    if pygame.display.get_driver() == "offscreen":
        pygame.quit()
        raise SystemExit(
            "No visible desktop display is available. "
            "Run the game from a graphical Linux desktop or set DISPLAY/WAYLAND_DISPLAY."
        )

    pygame.display.set_caption("Neon Tetris")
    game = TetrisGame(screen)
    game.run()
    pygame.quit()
