"""Neon Tetris — pygame entry point."""

from __future__ import annotations

import sys

import pygame

from config import (
    ARR_MS,
    BLOCK_SIZE,
    COLS,
    DAS_DELAY_MS,
    PANEL_WIDTH,
    ROWS,
)
from game_state import GameState
from renderer import Renderer
from sound import SoundManager

MENU, PLAYING, SCORES = "menu", "playing", "scores"


class TetrisGame:
    def __init__(self, screen):
        self.screen = screen
        self.renderer = Renderer(screen)
        self.game_state = GameState()
        self.sound = SoundManager()
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = MENU
        self.menu_index = 0
        self.das_dir = 0
        self.das_timer = 0
        self.arr_timer = 0
        self.initials = ""
        self.entering_score = False
        self.sound.start_music()

    def reset_game(self, event=None):
        self.game_state.reset()
        self.entering_score = False
        self.initials = ""
        self.das_dir = 0
        self._sync_hud()
        self.renderer.banner = None
        self.renderer.floaters.clear()
        self.sound.start_music()

    def start_play(self):
        self.reset_game()
        self.scene = PLAYING
        self.sound.play_select()

    def _sync_hud(self):
        gs = self.game_state
        r = self.renderer
        r.update_score_label(gs.score)
        r.update_high_score_label(gs.high_score())
        r.update_level_label(gs.level)
        r.update_lines_label(gs.lines_cleared_total)
        r.update_combo(gs.combo)
        r.back_to_back = gs.back_to_back
        r.update_particles(gs.particles)
        r.set_queue(gs.get_queue())
        r.set_held(gs.get_held(), gs.hold_used)
        r.clearing_rows = list(gs.clearing_rows)
        r.stats = gs.stats

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type != pygame.KEYDOWN:
            if event.type == pygame.KEYUP and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                self.das_dir = 0
            return

        key = event.key
        if key == pygame.K_m:
            on = self.sound.toggle_music()
            self.renderer.add_floater("MUSIC ON" if on else "MUSIC OFF", (180, 220, 255), y=80)
            return

        if self.scene == MENU:
            self._menu_key(key)
            return
        if self.scene == SCORES:
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_q):
                self.scene = MENU
                self.sound.play_select()
            return
        self._play_key(key, event)

    def _menu_key(self, key):
        if key in (pygame.K_ESCAPE, pygame.K_q):
            self.running = False
            return
        if key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % 3
            self.sound.play_move()
        elif key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % 3
            self.sound.play_move()
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.menu_index == 0:
                self.start_play()
            elif self.menu_index == 1:
                self.scene = SCORES
                self.sound.play_select()
            else:
                self.running = False

    def _play_key(self, key, event):
        gs = self.game_state

        if self.entering_score:
            if key == pygame.K_BACKSPACE:
                self.initials = self.initials[:-1]
            elif key == pygame.K_RETURN and len(self.initials) >= 1:
                gs.submit_highscore(self.initials.ljust(3, "A"))
                self.entering_score = False
                self.sound.play_select()
            elif event.unicode and event.unicode.isalnum() and len(self.initials) < 3:
                self.initials += event.unicode.upper()
                self.sound.play_move()
            return

        if key == pygame.K_F5:
            self.reset_game()
            return
        if key in (pygame.K_p,):
            if not gs.game_over:
                gs.paused = not gs.paused
            return
        if key == pygame.K_ESCAPE:
            if gs.paused or gs.game_over:
                self.scene = MENU
                self.sound.start_music()
            else:
                gs.paused = True
            return
        if gs.game_over and key == pygame.K_RETURN:
            self.scene = MENU
            return
        if gs.game_over or gs.paused:
            return

        if key in (pygame.K_LEFT, pygame.K_a):
            if gs.move(-1, 0):
                self.sound.play_move()
            self.das_dir = -1
            self.das_timer = 0
            self.arr_timer = 0
        elif key in (pygame.K_RIGHT, pygame.K_d):
            if gs.move(1, 0):
                self.sound.play_move()
            self.das_dir = 1
            self.das_timer = 0
            self.arr_timer = 0
        elif key in (pygame.K_UP, pygame.K_x, pygame.K_w):
            if gs.rotate(1):
                self.sound.play_rotate()
        elif key in (pygame.K_z, pygame.K_LCTRL, pygame.K_RCTRL):
            if gs.rotate(-1):
                self.sound.play_rotate()
        elif key == pygame.K_SPACE:
            gs.hard_drop()
            self.sound.play_hard_drop()
        elif key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
            if gs.hold():
                self.sound.play_hold()

    def _handle_das(self, dt):
        gs = self.game_state
        if gs.game_over or gs.paused or self.scene != PLAYING or not self.das_dir:
            return
        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        if self.das_dir < 0 and not left:
            self.das_dir = 0
            return
        if self.das_dir > 0 and not right:
            self.das_dir = 0
            return
        self.das_timer += dt
        if self.das_timer < DAS_DELAY_MS:
            return
        self.arr_timer += dt
        while self.arr_timer >= ARR_MS:
            self.arr_timer -= ARR_MS
            if gs.move(self.das_dir, 0):
                self.sound.play_move()
            else:
                break

    def _dispatch_events(self, events):
        r = self.renderer
        s = self.sound
        for ev in events:
            name = ev["name"]
            if name == "lock":
                s.play_lock()
            elif name == "hard_drop":
                r.trigger_shake(5 + min(8, ev.get("cells", 0) // 3))
            elif name == "line_clear":
                s.play_line_clear()
                n = ev.get("lines", 1)
                r.trigger_flash((180, 255, 255), 0.25)
                r.add_floater(["", "SINGLE", "DOUBLE", "TRIPLE"][n] if n < 4 else "TETRIS", (180, 255, 255))
            elif name == "tetris":
                s.play_tetris()
                r.trigger_shake(14)
                r.trigger_flash((0, 255, 255), 0.55)
                r.show_banner("TETRIS", (0, 255, 255), 80)
            elif name == "tspin":
                s.play_tspin()
                r.trigger_shake(10)
                r.trigger_flash((210, 80, 255), 0.4)
                r.show_banner("T-SPIN", (210, 80, 255), 80)
            elif name == "combo":
                s.play_combo()
                r.add_floater(f"x{ev.get('combo', 2)}", (255, 200, 60), y=280)
            elif name == "back_to_back":
                s.play_back_to_back()
                r.show_banner("BACK-TO-BACK", (255, 210, 80), 55)
            elif name == "level_up":
                s.play_level_up()
                r.set_level_up_effect()
                r.trigger_flash((0, 255, 180), 0.35)
            elif name == "game_over":
                s.play_game_over()
                r.trigger_shake(16)
                if self.game_state.qualifies_for_highscore():
                    self.entering_score = True
                    self.initials = ""
            elif name == "hold":
                pass

    def update(self, dt):
        self.renderer.tick(dt)
        if self.scene != PLAYING:
            return
        gs = self.game_state
        if gs.game_over or gs.paused:
            gs.update_particles()
            return
        self._handle_das(dt)
        keys = pygame.key.get_pressed()
        soft = keys[pygame.K_DOWN] or keys[pygame.K_s]
        events = gs.update(dt, soft_drop=soft)
        self._dispatch_events(events)

    def draw(self):
        if self.scene == MENU:
            self.renderer.draw_menu(self.menu_index, self.game_state.high_score())
            pygame.display.flip()
            return
        if self.scene == SCORES:
            self.renderer.draw_scores(self.game_state.high_scores)
            pygame.display.flip()
            return

        gs = self.game_state
        piece = gs.current_piece
        ghost = None
        if piece:
            ghost = {
                "shape": piece["shape"],
                "color": piece["color"],
                "x": piece["x"],
                "y": gs.get_ghost_y(),
            }
        self._sync_hud()
        self.renderer.draw_board(gs.board, piece, ghost)
        if gs.game_over:
            self.renderer.draw_game_over(gs.score, self.initials, self.entering_score)
        elif gs.paused:
            self.renderer.draw_pause_indicator()
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(120)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()


def main():
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    try:
        screen = pygame.display.set_mode((COLS * BLOCK_SIZE + PANEL_WIDTH, ROWS * BLOCK_SIZE))
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
    try:
        pygame.mouse.set_visible(False)
    except pygame.error:
        pass
    TetrisGame(screen).run()
    pygame.quit()


if __name__ == "__main__":
    main()
    sys.exit(0)
