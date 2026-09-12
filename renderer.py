"""Pygame renderer for the Tetris game."""

import pygame

from config import BLOCK_SIZE, COLS, ROWS


class Renderer:
    """Draw the board, side panel, and overlays with Pygame."""

    PANEL_WIDTH = 180
    PREVIEW_BLOCK_SIZE = 20

    def __init__(self, screen):
        self.screen = screen
        self.board_width = COLS * BLOCK_SIZE
        self.width = self.board_width + self.PANEL_WIDTH
        self.height = ROWS * BLOCK_SIZE
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 48)
        self.score = 0
        self.level = 1
        self.lines = 0
        self.high_score = 0
        self.next_piece = None

    def _draw_block(self, x, y, color, ghost=False):
        rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
        if ghost:
            pygame.draw.rect(self.screen, pygame.Color(color), rect, 2)
        else:
            pygame.draw.rect(self.screen, pygame.Color(color), rect)
            pygame.draw.rect(self.screen, pygame.Color("#202020"), rect, 1)

    def draw_next_piece(self, next_piece):
        """Store the next piece for the next frame render."""
        self.next_piece = next_piece

    def _draw_text(self, text, x, y, font=None, color="white"):
        surface = (font or self.font).render(text, True, pygame.Color(color))
        self.screen.blit(surface, (x, y))

    def draw_board(self, board, current_piece=None, ghost_piece=None):
        """Draw the complete game frame."""
        self.screen.fill(pygame.Color("#080808"))

        for row_idx, row in enumerate(board):
            for col_idx, color in enumerate(row):
                if color:
                    self._draw_block(col_idx, row_idx, color)

        if ghost_piece:
            for row_idx, row in enumerate(ghost_piece["shape"]):
                for col_idx, cell in enumerate(row):
                    if cell:
                        self._draw_block(
                            ghost_piece["x"] + col_idx,
                            ghost_piece["y"] + row_idx,
                            ghost_piece["color"],
                            ghost=True,
                        )

        if current_piece:
            for row_idx, row in enumerate(current_piece["shape"]):
                for col_idx, cell in enumerate(row):
                    if cell:
                        self._draw_block(
                            current_piece["x"] + col_idx,
                            current_piece["y"] + row_idx,
                            current_piece["color"],
                        )

        panel_x = self.board_width + 20
        self._draw_text("TETRIS", panel_x, 20, self.large_font)
        self._draw_text(f"Score: {self.score}", panel_x, 85)
        self._draw_text(f"Level: {self.level}", panel_x, 120)
        self._draw_text(f"Lines: {self.lines}", panel_x, 155)
        self._draw_text(f"Best: {self.high_score}", panel_x, 190)
        self._draw_text("Next", panel_x, 245)

        if self.next_piece:
            shape = self.next_piece["shape"]
            offset_x = panel_x + (5 - len(shape[0])) * self.PREVIEW_BLOCK_SIZE // 2
            offset_y = 285 + (5 - len(shape)) * self.PREVIEW_BLOCK_SIZE // 2
            for row_idx, row in enumerate(shape):
                for col_idx, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(
                            offset_x + col_idx * self.PREVIEW_BLOCK_SIZE,
                            offset_y + row_idx * self.PREVIEW_BLOCK_SIZE,
                            self.PREVIEW_BLOCK_SIZE,
                            self.PREVIEW_BLOCK_SIZE,
                        )
                        pygame.draw.rect(
                            self.screen,
                            pygame.Color(self.next_piece["color"]),
                            rect,
                        )
                        pygame.draw.rect(self.screen, pygame.Color("#202020"), rect, 1)

    def update_score_label(self, score):
        self.score = score

    def update_high_score_label(self, high_score):
        self.high_score = high_score

    def update_level_label(self, level):
        self.level = level

    def update_lines_label(self, lines):
        self.lines = lines

    def draw_game_over(self, score):
        """Draw the game-over overlay."""
        overlay = pygame.Surface((self.board_width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))
        self._draw_text("GAME OVER", 45, self.height // 2 - 60, self.large_font, "red")
        self._draw_text(f"Score: {score}", 105, self.height // 2, self.font)
        self._draw_text("F5 to restart", 82, self.height // 2 + 45, self.small_font, "yellow")

    def draw_pause_indicator(self):
        """Draw the pause overlay."""
        overlay = pygame.Surface((self.board_width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        self._draw_text("PAUSED", 105, self.height // 2 - 30, self.large_font)
        self._draw_text("P to resume", 112, self.height // 2 + 25, self.small_font, "yellow")
