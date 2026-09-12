"""Pygame entry point for the Tetris game."""

import pygame

from config import BLOCK_SIZE, COLS, INITIAL_SPEED, ROWS
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
        self.reset_game()

    def reset_game(self, event=None):
        """Reset the game to its initial state."""
        self.game_state.reset()
        self.renderer.update_score_label(self.game_state.score)
        self.renderer.update_high_score_label(self.game_state.high_score)
        self.renderer.update_level_label(self.game_state.get_level())
        self.renderer.update_lines_label(self.game_state.get_lines_cleared())
        self.renderer.draw_next_piece(self.game_state.get_next_piece())
        self.last_tick = pygame.time.get_ticks()

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

        key_names = {
            pygame.K_LEFT: "Left",
            pygame.K_RIGHT: "Right",
            pygame.K_DOWN: "Down",
            pygame.K_UP: "Up",
        }
        game_key = key_names.get(key)
        if game_key is None:
            return
        self.game_state.queue_key(game_key)
        if game_key in ("Left", "Right", "Down"):
            self.sound.play_move()
        else:
            self.sound.play_rotate()

    def update(self):
        """Advance the game when the configured tick interval elapses."""
        now = pygame.time.get_ticks()
        if self.game_state.game_over or self.game_state.paused:
            return
        if now - self.last_tick < INITIAL_SPEED:
            return
        self.last_tick = now

        self.game_state.process_key_queue()
        piece = self.game_state.current_piece
        if self.game_state.is_valid_move(piece["x"], piece["y"] + 1, piece["shape"]):
            piece["y"] += 1
            self.sound.play_drop()
            return

        self.game_state.merge_piece_to_board()
        lines_cleared = self.game_state.clear_lines()
        if lines_cleared:
            self.sound.play_line_clear()
        self.game_state.current_piece = self.game_state.new_piece()
        piece = self.game_state.current_piece
        if not self.game_state.is_valid_move(piece["x"], piece["y"], piece["shape"]):
            self.game_state.game_over = True
            self.game_state.check_high_score()
            self.sound.play_game_over()

    def draw(self):
        """Render the current game state."""
        piece = self.game_state.current_piece
        ghost_piece = None
        if piece:
            ghost_y = piece["y"]
            while self.game_state.is_valid_move(piece["x"], ghost_y + 1, piece["shape"]):
                ghost_y += 1
            ghost_piece = {
                "shape": piece["shape"],
                "color": piece["color"],
                "x": piece["x"],
                "y": ghost_y,
            }

        self.renderer.update_score_label(self.game_state.score)
        self.renderer.update_high_score_label(self.game_state.high_score)
        self.renderer.update_level_label(self.game_state.get_level())
        self.renderer.update_lines_label(self.game_state.get_lines_cleared())
        self.renderer.draw_next_piece(self.game_state.get_next_piece())
        self.renderer.draw_board(self.game_state.board, piece, ghost_piece)
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

    pygame.display.set_caption("Tetris")
    game = TetrisGame(screen)
    game.run()
    pygame.quit()
