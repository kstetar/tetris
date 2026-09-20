"""Pygame renderer for the Tetris game."""

import pygame
from config import BLOCK_SIZE, COLS, ROWS, BACKGROUND_COLOR, GRID_COLOR

class Renderer:
    """Draw the board, side panel, and overlays with Pygame."""

    PANEL_WIDTH = 200
    PREVIEW_BLOCK_SIZE = 25

    def __init__(self, screen):
        self.screen = screen
        self.board_width = COLS * BLOCK_SIZE
        self.width = self.board_width + self.PANEL_WIDTH
        self.height = ROWS * BLOCK_SIZE
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 28)
        self.large_font = pygame.font.Font(None, 64)
        self.score = 0
        self.level = 1
        self.lines = 0
        self.high_score = 0
        self.next_piece = None
        self.combo = 0
        self.lines_cleared = 0
        self.particles = []
        self.level_up_text = None
        self.level_up_timer = 0
        self.color_shift = 0

    def _draw_block(self, x, y, color, size=None, offset_x=0, offset_y=0, ghost=False, glow=True):
        if size is None:
            size = BLOCK_SIZE
        
        rect = pygame.Rect(offset_x + x * size, offset_y + y * size, size, size)
        
        if ghost:
            # Ghost piece - semi-transparent outline
            pygame.draw.rect(self.screen, (color[0], color[1], color[2], 60), rect)
            pygame.draw.rect(self.screen, (255, 255, 255, 30), rect, 1)
        else:
            # Normal block with gradient/shadow
            if glow:
                # Glow effect
                glow_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                for i in range(3):
                    alpha = max(0, 100 - i * 35)
                    glow_rect = pygame.Rect(i, i, size - i*2, size - i*2)
                    pygame.draw.rect(glow_surface, (color[0], color[1], color[2], alpha), glow_rect)
                self.screen.blit(glow_surface, rect.topleft)
            
            # Main block
            pygame.draw.rect(self.screen, color[:3], rect)
            
            # Inner highlight
            highlight = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4)
            pygame.draw.rect(self.screen, (255, 255, 255, 50), highlight, 1)
            
            # Border
            pygame.draw.rect(self.screen, (0, 0, 0, 100), rect, 1)

    def draw_next_piece(self, next_piece):
        """Store the next piece for rendering."""
        self.next_piece = next_piece

    def update_particles(self, particles):
        """Store particles for rendering."""
        self.particles = particles

    def draw_board(self, board, current_piece=None, ghost_piece=None):
        """Draw the complete game frame."""
        # Background
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw grid lines (subtle)
        for x in range(COLS + 1):
            pygame.draw.line(self.screen, GRID_COLOR, (x * BLOCK_SIZE, 0), (x * BLOCK_SIZE, self.height), 1)
        for y in range(ROWS + 1):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y * BLOCK_SIZE), (self.board_width, y * BLOCK_SIZE), 1)

        # Draw placed blocks
        for row_idx, row in enumerate(board):
            for col_idx, color in enumerate(row):
                if color:
                    self._draw_block(col_idx, row_idx, color)

        # Draw ghost piece
        if ghost_piece:
            for row_idx, row in enumerate(ghost_piece["shape"]):
                for col_idx, cell in enumerate(row):
                    if cell:
                        self._draw_block(
                            ghost_piece["x"] + col_idx,
                            ghost_piece["y"] + row_idx,
                            ghost_piece["color"],
                            ghost=True
                        )

        # Draw current piece
        if current_piece:
            for row_idx, row in enumerate(current_piece["shape"]):
                for col_idx, cell in enumerate(row):
                    if cell:
                        self._draw_block(
                            current_piece["x"] + col_idx,
                            current_piece["y"] + row_idx,
                            current_piece["color"]
                        )

        # Draw particles
        self._draw_particles()

        # Side panel background
        panel_rect = pygame.Rect(self.board_width, 0, self.PANEL_WIDTH, self.height)
        pygame.draw.rect(self.screen, (20, 20, 28), panel_rect)
        pygame.draw.line(self.screen, (40, 40, 50), (self.board_width, 0), (self.board_width, self.height), 2)

        # Draw UI elements
        self._draw_ui()

    def _draw_particles(self):
        """Draw particle effects."""
        for particle in self.particles:
            alpha = int(255 * particle["life"] / particle["max_life"])
            color = (*particle["color"][:3], alpha)
            size = int(3 * particle["life"] / particle["max_life"])
            if size > 0:
                pygame.draw.circle(self.screen, color, (int(particle["x"]), int(particle["y"])), size)

    def _draw_ui(self):
        """Draw the side panel UI."""
        panel_x = self.board_width + 20
        
        # Title with color shift effect
        title_text = "TETRIS"
        self.color_shift = (self.color_shift + 1) % 360
        colors = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (75, 0, 130), (143, 0, 255)
        ]
        
        for i, char in enumerate(title_text):
            color = colors[(i + self.color_shift // 50) % len(colors)]
            surface = self.large_font.render(char, True, color)
            self.screen.blit(surface, (panel_x + i * 35, 20))

        # Stats
        self._draw_text(f"Score: {self.score}", panel_x, 100, self.font, "white")
        self._draw_text(f"Level: {self.level}", panel_x, 145, self.font, "white")
        self._draw_text(f"Lines: {self.lines}", panel_x, 190, self.font, "white")
        self._draw_text(f"Best: {self.high_score}", panel_x, 235, self.font, "white")
        
        # Combo display
        if self.combo > 1:
            combo_color = (255, 255, 255) if self.combo % 2 == 0 else (255, 255, 0)
            combo_text = f"COMBO x{self.combo}!"
            surface = self.small_font.render(combo_text, True, combo_color)
            self.screen.blit(surface, (panel_x + 10, 280))

        # Next piece label
        self._draw_text("NEXT", panel_x, 320, self.small_font, "white")

        # Draw next piece preview
        if self.next_piece:
            shape = self.next_piece["shape"]
            offset_x = panel_x + (self.PANEL_WIDTH - 4 - len(shape[0]) * self.PREVIEW_BLOCK_SIZE) // 2
            offset_y = 350 + (5 - len(shape)) * self.PREVIEW_BLOCK_SIZE // 2
            for row_idx, row in enumerate(shape):
                for col_idx, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(
                            offset_x + col_idx * self.PREVIEW_BLOCK_SIZE,
                            offset_y + row_idx * self.PREVIEW_BLOCK_SIZE,
                            self.PREVIEW_BLOCK_SIZE,
                            self.PREVIEW_BLOCK_SIZE,
                        )
                        pygame.draw.rect(self.screen, self.next_piece["color"][:3], rect)
                        pygame.draw.rect(self.screen, (255, 255, 255, 50), rect, 1)

    def _draw_text(self, text, x, y, font=None, color="white"):
        """Draw text with shadow effect."""
        surface = (font or self.font).render(text, True, pygame.Color(color))
        # Shadow
        shadow = (font or self.font).render(text, True, pygame.Color("black"))
        self.screen.blit(shadow, (x + 2, y + 2))
        self.screen.blit(surface, (x, y))

    def update_score_label(self, score):
        self.score = score

    def update_high_score_label(self, high_score):
        self.high_score = high_score

    def update_level_label(self, level):
        self.level = level

    def update_lines_label(self, lines):
        self.lines = lines

    def update_combo(self, combo):
        self.combo = combo

    def set_level_up_effect(self):
        """Trigger level up visual effect."""
        self.level_up_text = f"LEVEL {self.level}!"
        self.level_up_timer = 60  # frames

    def draw_game_over(self, score):
        """Draw the game-over overlay with neon effects."""
        overlay = pygame.Surface((self.board_width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Game over text
        for i, char in enumerate("GAME OVER"):
            color = (255, 50 + i * 10, 50 + i * 10)
            surface = self.large_font.render(char, True, color)
            self.screen.blit(surface, (80 + i * 45, self.height // 2 - 80))

        self._draw_text(f"Final Score: {score}", 105, self.height // 2 + 20, self.font, "yellow")
        self._draw_text("F5 to restart", 95, self.height // 2 + 70, self.small_font, "white")
        self._draw_text("P to pause", 100, self.height // 2 + 100, self.small_font, "white")

    def draw_pause_indicator(self):
        """Draw the pause overlay."""
        overlay = pygame.Surface((self.board_width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        self._draw_text("PAUSED", 125, self.height // 2 - 40, self.large_font, "white")
        self._draw_text("Press P to resume", 90, self.height // 2 + 30, self.small_font, "yellow")
        
        # Controls hint
        controls = [
            "Controls:",
            "Arrow Keys: Move",
            "Up: Rotate",
            "Space: Hard Drop",
            "Down: Soft Drop",
            "P: Pause"
        ]
        for i, text in enumerate(controls):
            color = "lightgray" if "Controls" in text else "white"
            self._draw_text(text, 25, 400 + i * 25, self.small_font, color)

    def draw_level_up(self):
        """Draw level up text."""
        if self.level_up_timer > 0 and self.level_up_text:
            # Pulsing effect
            scale = 1 + abs((self.level_up_timer % 10) - 5) / 10
            alpha = int(255 * self.level_up_timer / 60)
            
            surface = self.large_font.render(self.level_up_text, True, (255, 255, 255, alpha))
            rect = surface.get_rect(center=(self.board_width // 2, self.height // 2))
            
            # Glow effect
            for i in range(3):
                glow = self.large_font.render(self.level_up_text, True, (0, 255, 255, alpha // (i + 1)))
                glow_rect = rect.copy()
                glow_rect.move_ip(i - 1, i - 1)
                self.screen.blit(glow, glow_rect)
            
            self.screen.blit(surface, rect)
            self.level_up_timer -= 1
