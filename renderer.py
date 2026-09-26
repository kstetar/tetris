"""Neon CRT renderer for Tetris."""

from __future__ import annotations

import math
import random

import pygame

from config import (
    ACCENT,
    ACCENT_2,
    BACKGROUND_COLOR,
    BLOCK_SIZE,
    COLS,
    COLORS,
    GRID_COLOR,
    PANEL_WIDTH,
    PIECE_NAMES,
    ROWS,
    SHAPES,
)


def _font(size, bold=False):
    names = ["consolas", "dejavusansmono", "menlo", "liberationmono", "monospace"]
    for name in names:
        matched = pygame.font.match_font(name, bold=bold)
        if matched:
            return pygame.font.Font(matched, size)
    return pygame.font.Font(None, size)


def _lighten(color, amount=40):
    return tuple(min(255, c + amount) for c in color[:3])


def _darken(color, amount=50):
    return tuple(max(0, c - amount) for c in color[:3])


class Renderer:
    PANEL_WIDTH = PANEL_WIDTH
    PREVIEW_BLOCK_SIZE = 16

    def __init__(self, screen):
        self.screen = screen
        self.board_width = COLS * BLOCK_SIZE
        self.width = self.board_width + self.PANEL_WIDTH
        self.height = ROWS * BLOCK_SIZE
        self.font = _font(22)
        self.small_font = _font(16)
        self.tiny_font = _font(14)
        self.large_font = _font(54, bold=True)
        self.huge_font = _font(72, bold=True)
        self.score = 0
        self.level = 1
        self.lines = 0
        self.high_score = 0
        self.next_piece = None
        self.queue = []
        self.held = None
        self.hold_used = False
        self.combo = 0
        self.back_to_back = False
        self.particles = []
        self.clearing_rows = []
        self.clear_timer = 0
        self.time_ms = 0
        self.shake = 0.0
        self.flash = 0.0
        self.flash_color = (255, 255, 255)
        self.banner = None
        self.banner_timer = 0
        self.floaters = []
        self.stars = [
            {
                "x": random.random() * self.width,
                "y": random.random() * self.height,
                "z": random.uniform(0.2, 1.0),
                "tw": random.random() * math.tau,
            }
            for _ in range(90)
        ]
        self._block_cache = {}
        self._ghost_cache = {}
        self._scanlines = self._make_scanlines()
        self._vignette = self._make_vignette()
        self._board_surf = pygame.Surface((self.board_width, self.height), pygame.SRCALPHA)
        self.menu_index = 0
        self.stats = {}

    def _make_scanlines(self):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, 2):
            pygame.draw.line(surf, (0, 0, 0, 38), (0, y), (self.width, y))
        return surf

    def _make_vignette(self):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx, cy = self.width / 2, self.height / 2
        max_d = math.hypot(cx, cy)
        # cheap radial darkening in bands
        for i in range(12, 0, -1):
            alpha = int(10 + (12 - i) * 7)
            r = int(max_d * i / 12)
            pygame.draw.circle(surf, (0, 0, 0, alpha), (int(cx), int(cy)), r, 18)
        return surf

    def _block_surface(self, color, ghost=False):
        key = (tuple(color[:3]), ghost)
        cache = self._ghost_cache if ghost else self._block_cache
        if key in cache:
            return cache[key]
        size = BLOCK_SIZE
        pad = 7
        surf = pygame.Surface((size + pad * 2, size + pad * 2), pygame.SRCALPHA)
        r, g, b = color[:3]
        if ghost:
            body = pygame.Rect(pad + 1, pad + 1, size - 2, size - 2)
            pygame.draw.rect(surf, (r, g, b, 35), body, border_radius=4)
            pygame.draw.rect(surf, (r, g, b, 160), body, 1, border_radius=4)
            pygame.draw.rect(surf, (255, 255, 255, 50), body.inflate(-6, -6), 1, border_radius=3)
        else:
            for i in range(pad, 0, -1):
                a = int(28 * (i / pad) ** 1.4)
                pygame.draw.rect(
                    surf,
                    (r, g, b, a),
                    pygame.Rect(pad - i, pad - i, size + i * 2, size + i * 2),
                    border_radius=5,
                )
            body = pygame.Rect(pad, pad, size, size)
            pygame.draw.rect(surf, _darken((r, g, b), 35), body, border_radius=4)
            inner = body.inflate(-3, -3)
            pygame.draw.rect(surf, (r, g, b), inner, border_radius=3)
            hi = pygame.Rect(inner.x + 2, inner.y + 2, inner.w - 8, 6)
            pygame.draw.rect(surf, (*_lighten((r, g, b), 70), 180), hi, border_radius=2)
            pygame.draw.line(
                surf,
                (*_lighten((r, g, b), 90), 140),
                (inner.x + 2, inner.y + 3),
                (inner.x + 2, inner.bottom - 4),
                2,
            )
            pygame.draw.rect(surf, (0, 0, 0, 90), body, 1, border_radius=4)
        cache[key] = surf
        return surf

    def _blit_block(self, target, x, y, color, ghost=False, offset=(0, 0), size=None, flash=False):
        if size and size != BLOCK_SIZE:
            # preview-scale without glow cache
            rect = pygame.Rect(offset[0] + x * size, offset[1] + y * size, size - 1, size - 1)
            if ghost:
                pygame.draw.rect(target, (*color[:3], 80), rect, 1, border_radius=2)
            else:
                pygame.draw.rect(target, color[:3], rect, border_radius=2)
                pygame.draw.rect(target, _lighten(color, 50), rect, 1, border_radius=2)
            return
        surf = self._block_surface(color, ghost=ghost)
        pad = 7
        px = offset[0] + x * BLOCK_SIZE - pad
        py = offset[1] + y * BLOCK_SIZE - pad
        if flash:
            glow = surf.copy()
            glow.fill((255, 255, 255, 90), special_flags=pygame.BLEND_RGBA_ADD)
            target.blit(glow, (px, py))
        else:
            target.blit(surf, (px, py))

    def _draw_shape(self, target, shape, color, origin, ghost=False, size=None, flash=False):
        ox, oy = origin
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    self._blit_block(target, c, r, color, ghost=ghost, offset=(ox, oy), size=size, flash=flash)

    # --- public state setters ----------------------------------------

    def draw_next_piece(self, next_piece):
        self.next_piece = next_piece

    def set_queue(self, queue):
        self.queue = queue

    def set_held(self, held, used=False):
        self.held = held
        self.hold_used = used

    def update_particles(self, particles):
        self.particles = particles

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
        self.show_banner(f"LEVEL {self.level}", (0, 255, 220), 90)

    def show_banner(self, text, color, frames=70):
        self.banner = (text, color)
        self.banner_timer = frames

    def add_floater(self, text, color, x=None, y=None):
        self.floaters.append(
            {
                "text": text,
                "color": color,
                "x": self.board_width / 2 if x is None else x,
                "y": self.height / 2 if y is None else y,
                "life": 50,
            }
        )

    def trigger_shake(self, amount=8):
        self.shake = max(self.shake, amount)

    def trigger_flash(self, color=(255, 255, 255), amount=0.45):
        self.flash = amount
        self.flash_color = color

    # --- frame --------------------------------------------------------

    def tick(self, dt_ms):
        self.time_ms += dt_ms
        self.shake *= 0.86
        if self.shake < 0.4:
            self.shake = 0
        self.flash *= 0.88
        if self.banner_timer > 0:
            self.banner_timer -= 1
        for f in self.floaters:
            f["y"] -= 0.7
            f["life"] -= 1
        self.floaters = [f for f in self.floaters if f["life"] > 0]
        for s in self.stars:
            s["y"] += 0.15 + s["z"] * 0.35
            if s["y"] > self.height:
                s["y"] = 0
                s["x"] = random.random() * self.width

    def _fill_background(self, target):
        target.fill(BACKGROUND_COLOR)
        t = self.time_ms / 1000.0
        # aurora wash
        wash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.circle(
            wash,
            (0, 80, 120, 28),
            (int(self.board_width * 0.4 + math.sin(t * 0.4) * 40), int(180 + math.cos(t * 0.3) * 30)),
            220,
        )
        pygame.draw.circle(
            wash,
            (90, 0, 80, 22),
            (int(self.board_width * 0.7 + math.cos(t * 0.5) * 50), int(420 + math.sin(t * 0.25) * 40)),
            260,
        )
        target.blit(wash, (0, 0))
        for s in self.stars:
            a = int(40 + 180 * s["z"] * (0.6 + 0.4 * math.sin(t * 3 + s["tw"])))
            pygame.draw.circle(target, (180, 210, 255, min(255, a)), (int(s["x"]), int(s["y"])), 1 if s["z"] < 0.6 else 2)

    def draw_board(self, board, current_piece=None, ghost_piece=None):
        sx = int((random.random() - 0.5) * 2 * self.shake) if self.shake else 0
        sy = int((random.random() - 0.5) * 2 * self.shake) if self.shake else 0

        self._fill_background(self.screen)
        board_surf = self._board_surf
        board_surf.fill((0, 0, 0, 0))

        well = pygame.Surface((self.board_width, self.height), pygame.SRCALPHA)
        well.fill((4, 6, 14, 210))
        board_surf.blit(well, (0, 0))

        pulse = 18 + int(10 * math.sin(self.time_ms / 400))
        grid = (GRID_COLOR[0], GRID_COLOR[1], GRID_COLOR[2] + pulse)
        for x in range(COLS + 1):
            pygame.draw.line(board_surf, grid, (x * BLOCK_SIZE, 0), (x * BLOCK_SIZE, self.height), 1)
        for y in range(ROWS + 1):
            pygame.draw.line(board_surf, grid, (0, y * BLOCK_SIZE), (self.board_width, y * BLOCK_SIZE), 1)

        flash_rows = set(self.clearing_rows)
        flash_on = bool(flash_rows) and ((self.time_ms // 50) % 2 == 0)
        for row_idx, row in enumerate(board):
            for col_idx, color in enumerate(row):
                if color:
                    self._blit_block(board_surf, col_idx, row_idx, color, flash=row_idx in flash_rows and flash_on)

        if ghost_piece and current_piece and ghost_piece["y"] != current_piece["y"]:
            self._draw_shape(
                board_surf,
                ghost_piece["shape"],
                ghost_piece["color"],
                (ghost_piece["x"] * BLOCK_SIZE, ghost_piece["y"] * BLOCK_SIZE),
                ghost=True,
            )

        if current_piece:
            self._draw_shape(
                board_surf,
                current_piece["shape"],
                current_piece["color"],
                (current_piece["x"] * BLOCK_SIZE, current_piece["y"] * BLOCK_SIZE),
            )

        self._draw_particles(board_surf)

        # bloom
        small = pygame.transform.smoothscale(board_surf, (self.board_width // 4, self.height // 4))
        bloom = pygame.transform.smoothscale(small, (self.board_width, self.height))
        self.screen.blit(bloom, (sx, sy), special_flags=pygame.BLEND_ADD)
        self.screen.blit(board_surf, (sx, sy))

        self._draw_panel()
        self._draw_floaters()
        self._draw_banner()

        if self.flash > 0.04:
            overlay = pygame.Surface((self.board_width, self.height), pygame.SRCALPHA)
            overlay.fill((*self.flash_color[:3], int(180 * self.flash)))
            self.screen.blit(overlay, (sx, sy))

        self.screen.blit(self._scanlines, (0, 0))
        self.screen.blit(self._vignette, (0, 0))

        # neon well border
        pygame.draw.rect(
            self.screen,
            ACCENT,
            pygame.Rect(sx, sy, self.board_width, self.height),
            2,
        )

    def _draw_particles(self, target):
        for p in self.particles:
            life = p["life"] / max(1, p["max_life"])
            size = max(1, int(p.get("size", 3) * life))
            col = p["color"][:3]
            pygame.draw.circle(target, (*col, int(220 * life)), (int(p["x"]), int(p["y"])), size)
            if size > 1:
                pygame.draw.circle(target, (255, 255, 255, int(120 * life)), (int(p["x"]), int(p["y"])), max(1, size // 2))

    def _draw_panel(self):
        px = self.board_width
        panel = pygame.Rect(px, 0, self.PANEL_WIDTH, self.height)
        pygame.draw.rect(self.screen, (8, 9, 20), panel)
        pygame.draw.line(self.screen, ACCENT, (px, 0), (px, self.height), 2)

        t = self.time_ms / 80
        title = "NEON"
        for i, ch in enumerate(title):
            hue = COLORS[(i + int(t / 8)) % len(COLORS)]
            surf = self.large_font.render(ch, True, hue)
            self.screen.blit(surf, (px + 18 + i * 34, 8))
        sub = self.tiny_font.render("T E T R I S", True, ACCENT_2)
        self.screen.blit(sub, (px + 22, 58))

        self._section_label("HOLD", px + 18, 82)
        self._preview_box(self.held, px + 18, 102, dim=self.hold_used)

        self._section_label("NEXT", px + 18, 188)
        y = 208
        for i, piece in enumerate(self.queue[:3]):
            scale = 14 if i else 16
            self._preview_box(piece, px + 18, y, height=58 if i else 70, block=scale)
            y += 62 if i else 76

        y = 430
        self._stat(px + 18, y, "SCORE", f"{self.score:,}")
        self._stat(px + 18, y + 44, "BEST", f"{self.high_score:,}")
        self._stat(px + 18, y + 88, "LEVEL", str(self.level))
        self._stat(px + 18, y + 132, "LINES", str(self.lines))

        if self.combo > 1:
            pulse = 0.7 + 0.3 * math.sin(self.time_ms / 80)
            color = (255, int(180 + 70 * pulse), 40)
            txt = self.font.render(f"COMBO x{self.combo}", True, color)
            self.screen.blit(txt, (px + 18, self.height - 36))
        if self.back_to_back:
            txt = self.tiny_font.render("BACK-TO-BACK", True, ACCENT)
            self.screen.blit(txt, (px + 18, self.height - 56))

    def _section_label(self, text, x, y):
        lab = self.tiny_font.render(text, True, (140, 160, 190))
        self.screen.blit(lab, (x, y))
        pygame.draw.line(self.screen, (40, 60, 90), (x + lab.get_width() + 8, y + 10), (x + 220, y + 10), 1)

    def _preview_box(self, piece, x, y, height=72, block=None, dim=False):
        w = self.PANEL_WIDTH - 36
        rect = pygame.Rect(x, y, w, height)
        pygame.draw.rect(self.screen, (12, 16, 28), rect, border_radius=6)
        pygame.draw.rect(self.screen, (40, 70, 110), rect, 1, border_radius=6)
        if not piece:
            return
        size = block or self.PREVIEW_BLOCK_SIZE
        shape = piece["shape"]
        rows = len(shape)
        cols = len(shape[0])
        ox = x + (w - cols * size) // 2
        oy = y + (height - rows * size) // 2
        color = piece["color"]
        if dim:
            color = tuple(c // 3 for c in color[:3])
        self._draw_shape(self.screen, shape, color, (ox, oy), size=size)

    def _stat(self, x, y, label, value):
        lab = self.tiny_font.render(label, True, (120, 140, 170))
        self.screen.blit(lab, (x, y))
        val = self.font.render(value, True, (240, 248, 255))
        self.screen.blit(val, (x, y + 14))

    def _draw_text(self, text, x, y, font=None, color="white"):
        font = font or self.font
        col = pygame.Color(color) if isinstance(color, str) else color
        shadow = font.render(text, True, (0, 0, 0))
        surf = font.render(text, True, col)
        self.screen.blit(shadow, (x + 2, y + 2))
        self.screen.blit(surf, (x, y))

    def _draw_floaters(self):
        for f in self.floaters:
            a = max(0, min(255, int(255 * f["life"] / 50)))
            surf = self.font.render(f["text"], True, f["color"])
            surf.set_alpha(a)
            rect = surf.get_rect(center=(int(f["x"]), int(f["y"])))
            self.screen.blit(surf, rect)

    def _draw_banner(self):
        if self.banner_timer <= 0 or not self.banner:
            return
        text, color = self.banner
        scale = 1.0 + 0.08 * math.sin(self.banner_timer / 4)
        alpha = 255 if self.banner_timer > 15 else int(255 * self.banner_timer / 15)
        surf = self.large_font.render(text, True, color)
        if scale != 1.0:
            w, h = surf.get_size()
            surf = pygame.transform.smoothscale(surf, (max(1, int(w * scale)), max(1, int(h * scale))))
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(self.board_width // 2, self.height // 2 - 20))
        glow = pygame.Surface((rect.w + 40, rect.h + 40), pygame.SRCALPHA)
        glow.fill((*color[:3], 30))
        self.screen.blit(glow, (rect.x - 20, rect.y - 20))
        self.screen.blit(surf, rect)

    def draw_level_up(self):
        pass  # handled via banners

    def draw_game_over(self, score, initials=None, entering=False):
        overlay = pygame.Surface((self.board_width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        title = self.large_font.render("GAME OVER", True, (255, 70, 110))
        self.screen.blit(title, title.get_rect(center=(self.board_width // 2, 160)))
        self._draw_text(f"SCORE  {score:,}", 70, 230, self.font, ACCENT)
        if entering:
            blink = (self.time_ms // 320) % 2 == 0
            name = (initials or "") + ("_" if blink else " ")
            self._draw_text("NEW HIGH SCORE", 70, 290, self.font, (255, 220, 80))
            self._draw_text(name.ljust(3), 130, 340, self.large_font, (255, 255, 255))
            self._draw_text("Type initials, Enter to save", 48, 430, self.tiny_font, (180, 190, 210))
        else:
            self._draw_text("Enter  —  menu", 90, 340, self.small_font, (220, 220, 230))
            self._draw_text("F5     —  rematch", 90, 370, self.small_font, (220, 220, 230))

    def draw_pause_indicator(self):
        overlay = pygame.Surface((self.board_width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 4, 16, 180))
        self.screen.blit(overlay, (0, 0))
        self._draw_text("PAUSED", 90, 180, self.large_font, ACCENT)
        lines = [
            "P / Esc   resume",
            "← →       move",
            "↑ / X     rotate CW",
            "Z         rotate CCW",
            "↓         soft drop",
            "Space     hard drop",
            "C / Shift hold",
            "M         music",
            "F11       fullscreen",
        ]
        for i, line in enumerate(lines):
            self._draw_text(line, 48, 270 + i * 28, self.small_font, (210, 220, 235))

    def draw_menu(self, index, high_score=0):
        self._fill_background(self.screen)
        # decorative falling ghosts
        t = self.time_ms / 1000.0
        for i, color in enumerate(COLORS):
            shape = SHAPES[i]
            x = 40 + (i * 85 + int(math.sin(t + i) * 18)) % (self.width - 80)
            y = int((t * (30 + i * 7) + i * 90) % (self.height + 80)) - 40
            self._draw_shape(self.screen, shape, color, (x, y), size=14)

        title = self.huge_font.render("NEON", True, ACCENT)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 150)))
        sub = self.large_font.render("TETRIS", True, ACCENT_2)
        self.screen.blit(sub, sub.get_rect(center=(self.width // 2, 215)))

        items = ["PLAY", "SCORES", "QUIT"]
        for i, item in enumerate(items):
            selected = i == index
            color = (255, 255, 255) if selected else (130, 150, 180)
            prefix = "▸ " if selected else "  "
            surf = self.font.render(prefix + item, True, color)
            rect = surf.get_rect(center=(self.width // 2, 320 + i * 48))
            if selected:
                pygame.draw.rect(self.screen, (0, 245, 255, 40), rect.inflate(28, 12), 1, border_radius=6)
            self.screen.blit(surf, rect)

        hs = self.tiny_font.render(f"BEST  {high_score:,}", True, (160, 180, 200))
        self.screen.blit(hs, hs.get_rect(center=(self.width // 2, self.height - 70)))
        hint = self.tiny_font.render("Enter to select   ·   M music   ·   Esc quit", True, (110, 130, 150))
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 40)))
        self.screen.blit(self._scanlines, (0, 0))
        self.screen.blit(self._vignette, (0, 0))

    def draw_scores(self, scores):
        self._fill_background(self.screen)
        title = self.large_font.render("HALL OF NEON", True, ACCENT)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 70)))
        if not scores:
            empty = self.font.render("No scores yet. Go make one.", True, (180, 190, 210))
            self.screen.blit(empty, empty.get_rect(center=(self.width // 2, 240)))
        else:
            # Fixed column positions for alignment
            col_rank = 90
            col_name = 130
            col_score = 190
            col_level = 320
            col_lines = 370
            header_color = (120, 140, 170)
            self.screen.blit(self.font.render("#", True, header_color), (col_rank, 130))
            self.screen.blit(self.font.render("NAME", True, header_color), (col_name, 130))
            self.screen.blit(self.font.render("SCORE", True, header_color), (col_score, 130))
            self.screen.blit(self.font.render("LV", True, header_color), (col_level, 130))
            self.screen.blit(self.font.render("LINES", True, header_color), (col_lines, 130))
            for i, row in enumerate(scores[:8]):
                color = COLORS[i % len(COLORS)] if i < 3 else (220, 230, 240)
                y = 165 + i * 40
                self.screen.blit(self.font.render(f"{i+1:2d}", True, color), (col_rank, y))
                self.screen.blit(self.font.render(f"{row['name']:<3}", True, color), (col_name, y))
                self.screen.blit(self.font.render(f"{row['score']:>8,}", True, color), (col_score, y))
                self.screen.blit(self.font.render(f"{row['level']:>3}", True, color), (col_level, y))
                self.screen.blit(self.font.render(f"{row['lines']:>4}", True, color), (col_lines, y))
        hint = self.tiny_font.render("Esc / Enter  back", True, (110, 130, 150))
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 40)))
        self.screen.blit(self._scanlines, (0, 0))
        self.screen.blit(self._vignette, (0, 0))
