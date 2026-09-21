"""Game logic for Neon Tetris. No rendering."""

from __future__ import annotations

import json
import os
import random
from copy import deepcopy

from config import (
    B2B_MULTIPLIER,
    BLOCK_SIZE,
    COLS,
    COLORS,
    COMBO_BASE,
    ENTRY_DELAY_MS,
    HARD_DROP_POINTS,
    HIGHSCORE_FILE,
    INITIAL_GRAVITY_MS,
    LINE_CLEAR_MS,
    LOCK_DELAY_MS,
    MAX_HIGH_SCORES,
    MAX_LOCK_RESETS,
    MIN_GRAVITY_MS,
    PIECE_NAMES,
    QUEUE_SIZE,
    ROWS,
    SCORE_PER_LINE,
    SHAPES,
    SOFT_DROP_MS,
    SOFT_DROP_POINTS,
    TSPIN_SCORE,
)


def gravity_ms(level: int) -> int:
    """Guideline-ish curve: faster every level, never below MIN."""
    return max(MIN_GRAVITY_MS, int(INITIAL_GRAVITY_MS * (0.82 ** (level - 1))))


def _empty_board():
    return [[0 for _ in range(COLS)] for _ in range(ROWS)]


def _clone_shape(shape):
    return [row[:] for row in shape]


def _rotate_cw(shape):
    return [list(row) for row in zip(*shape[::-1])]


def _rotate_ccw(shape):
    return [list(row) for row in reversed(list(zip(*shape)))]


class GameState:
    """All Tetris rules live here."""

    def __init__(self):
        self.board = _empty_board()
        self.score = 0
        self.lines_cleared_total = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.current_piece = None
        self.held_piece = None
        self.hold_used = False
        self.queue = []
        self.bag = []
        self.high_scores = []
        self.combo = 0
        self.back_to_back = False
        self.particles = []
        self.events = []
        self.lock_timer = 0
        self.lock_resets = 0
        self.clearing_rows = []
        self.clear_timer = 0
        self.entry_timer = 0
        self.last_rotate = False
        self.last_was_tspin = False
        self.force_lock = False
        self.drop_delay = INITIAL_GRAVITY_MS
        self.soft_dropping = False
        self._grav_acc = 0
        self.stats = {"singles": 0, "doubles": 0, "triples": 0, "tetrises": 0, "tspins": 0, "pieces": 0}
        self.reset()

    def reset(self):
        self.board = _empty_board()
        self.score = 0
        self.lines_cleared_total = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.held_piece = None
        self.hold_used = False
        self.bag = []
        self.queue = [self._make_piece() for _ in range(QUEUE_SIZE)]
        self.current_piece = self._spawn_from_queue()
        self.high_scores = self.load_highscores()
        self.combo = 0
        self.back_to_back = False
        self.particles = []
        self.events = []
        self.lock_timer = 0
        self.lock_resets = 0
        self.clearing_rows = []
        self.clear_timer = 0
        self.entry_timer = 0
        self.last_rotate = False
        self.last_was_tspin = False
        self.force_lock = False
        self.drop_delay = gravity_ms(1)
        self.soft_dropping = False
        self._grav_acc = 0
        self.stats = {"singles": 0, "doubles": 0, "triples": 0, "tetrises": 0, "tspins": 0, "pieces": 0}

    # --- bag / pieces -------------------------------------------------

    def _fill_bag(self):
        indices = list(range(len(SHAPES)))
        random.shuffle(indices)
        self.bag.extend(indices)

    def _make_piece(self):
        if not self.bag:
            self._fill_bag()
        idx = self.bag.pop(0)
        shape = _clone_shape(SHAPES[idx])
        return {
            "shape": shape,
            "color": COLORS[idx],
            "type": idx,
            "name": PIECE_NAMES[idx],
            "x": COLS // 2 - len(shape[0]) // 2,
            "y": 0,
            "rotation": 0,
        }

    def _reset_piece_position(self, piece):
        piece = deepcopy(piece)
        piece["shape"] = _clone_shape(SHAPES[piece["type"]])
        piece["x"] = COLS // 2 - len(piece["shape"][0]) // 2
        piece["y"] = 0
        piece["rotation"] = 0
        return piece

    def _spawn_from_queue(self):
        piece = self._reset_piece_position(self.queue.pop(0))
        self.queue.append(self._make_piece())
        self.hold_used = False
        self.lock_timer = 0
        self.lock_resets = 0
        self.force_lock = False
        self.last_rotate = False
        self._grav_acc = 0
        self.stats["pieces"] += 1
        if not self.is_valid_move(piece["x"], piece["y"], piece["shape"]):
            # try one row up (spawn in hidden row feel)
            piece["y"] = -1
            if not self.is_valid_move(piece["x"], piece["y"], piece["shape"]):
                self.game_over = True
                self._emit("game_over")
        return piece

    def get_next_piece(self):
        return self.queue[0] if self.queue else None

    def get_queue(self):
        return list(self.queue)

    def get_held(self):
        return self.held_piece

    # --- collision ----------------------------------------------------

    def is_valid_move(self, x, y, shape):
        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if not cell:
                    continue
                nx, ny = x + col_idx, y + row_idx
                if nx < 0 or nx >= COLS or ny >= ROWS:
                    return False
                if ny >= 0 and self.board[ny][nx]:
                    return False
        return True

    def _grounded(self, piece=None):
        piece = piece or self.current_piece
        if not piece:
            return True
        return not self.is_valid_move(piece["x"], piece["y"] + 1, piece["shape"])

    # --- movement -----------------------------------------------------

    def move(self, dx, dy):
        if not self.current_piece or self.game_over or self.clearing_rows:
            return False
        x = self.current_piece["x"] + dx
        y = self.current_piece["y"] + dy
        if self.is_valid_move(x, y, self.current_piece["shape"]):
            self.current_piece["x"] = x
            self.current_piece["y"] = y
            self.last_rotate = False
            if dx:
                self._maybe_reset_lock()
            if dy > 0 and self.soft_dropping:
                self.score += SOFT_DROP_POINTS * dy
            return True
        return False

    def rotate(self, direction=1):
        if not self.current_piece or self.game_over or self.clearing_rows:
            return False
        piece = self.current_piece
        if piece["name"] == "O":
            return False
        original = piece["shape"]
        rotated = _rotate_cw(original) if direction > 0 else _rotate_ccw(original)
        kicks = [(0, 0), (1, 0), (-1, 0), (0, -1), (2, 0), (-2, 0), (1, -1), (-1, -1), (0, 1)]
        if piece["name"] == "I":
            kicks = [(0, 0), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1), (1, -1), (-1, -1)]
        for kx, ky in kicks:
            if self.is_valid_move(piece["x"] + kx, piece["y"] + ky, rotated):
                piece["x"] += kx
                piece["y"] += ky
                piece["shape"] = rotated
                piece["rotation"] = (piece["rotation"] + direction) % 4
                self.last_rotate = True
                self._maybe_reset_lock()
                return True
        return False

    def hard_drop(self):
        if not self.current_piece or self.game_over or self.clearing_rows:
            return 0
        cells = 0
        while self.is_valid_move(
            self.current_piece["x"], self.current_piece["y"] + 1, self.current_piece["shape"]
        ):
            self.current_piece["y"] += 1
            cells += 1
        self.score += cells * HARD_DROP_POINTS
        self.force_lock = True
        self.last_rotate = False
        self._emit("hard_drop", cells=cells)
        return cells

    def hold(self):
        if self.hold_used or not self.current_piece or self.game_over or self.clearing_rows:
            return False
        self.hold_used = True
        incoming = self._reset_piece_position(self.current_piece)
        if self.held_piece is None:
            self.held_piece = incoming
            self.current_piece = self._spawn_from_queue()
            self.hold_used = True  # spawn clears this; restore
        else:
            self.current_piece = self._reset_piece_position(self.held_piece)
            self.held_piece = incoming
            if not self.is_valid_move(
                self.current_piece["x"], self.current_piece["y"], self.current_piece["shape"]
            ):
                self.game_over = True
                self._emit("game_over")
        self.lock_timer = 0
        self.lock_resets = 0
        self._emit("hold")
        return True

    def _maybe_reset_lock(self):
        if self._grounded() and self.lock_resets < MAX_LOCK_RESETS:
            self.lock_timer = 0
            self.lock_resets += 1

    # --- lock / lines -------------------------------------------------

    def merge_piece_to_board(self):
        piece = self.current_piece
        if not piece:
            return
        for row_idx, row in enumerate(piece["shape"]):
            for col_idx, cell in enumerate(row):
                if not cell:
                    continue
                by = piece["y"] + row_idx
                bx = piece["x"] + col_idx
                if 0 <= by < ROWS and 0 <= bx < COLS:
                    self.board[by][bx] = piece["color"]
                elif by < 0:
                    self.game_over = True

    def _full_rows(self):
        return [i for i, row in enumerate(self.board) if all(row)]

    def _is_tspin(self):
        piece = self.current_piece
        if not piece or piece["name"] != "T" or not self.last_rotate:
            return False
        cx = piece["x"] + 1
        cy = piece["y"] + 1
        corners = [(cx - 1, cy - 1), (cx + 1, cy - 1), (cx - 1, cy + 1), (cx + 1, cy + 1)]
        filled = 0
        for x, y in corners:
            if x < 0 or x >= COLS or y >= ROWS or y < 0 or self.board[y][x]:
                filled += 1
        return filled >= 3

    def _lock_current(self):
        tspin = self._is_tspin()
        self.last_was_tspin = tspin
        self.merge_piece_to_board()
        if self.game_over:
            self._emit("lock")
            self._emit("game_over")
            return
        rows = self._full_rows()
        self._emit("lock", tspin=tspin)
        self.current_piece = None
        if rows:
            self.clearing_rows = rows
            self.clear_timer = LINE_CLEAR_MS
            self._create_particles(rows)
            n = len(rows)
            if n == 4:
                self._emit("tetris")
            elif tspin:
                self._emit("tspin", lines=n)
            else:
                self._emit("line_clear", lines=n)
        else:
            if tspin:
                self._award_clear(0, tspin=True)
                self._emit("tspin", lines=0)
            else:
                self.combo = 0
            self.entry_timer = ENTRY_DELAY_MS

    def _finish_line_clear(self):
        rows = set(self.clearing_rows)
        n = len(rows)
        new_board = [row for i, row in enumerate(self.board) if i not in rows]
        while len(new_board) < ROWS:
            new_board.insert(0, [0 for _ in range(COLS)])
        self.board = new_board
        self.clearing_rows = []
        self.clear_timer = 0
        self._award_clear(n, tspin=self.last_was_tspin)
        self.entry_timer = ENTRY_DELAY_MS
        self.current_piece = None

    def _award_clear(self, lines, tspin=False):
        old_level = self.level
        if lines:
            self.combo += 1
            self.lines_cleared_total += lines
            self.level = self.lines_cleared_total // 10 + 1
            if lines == 1:
                self.stats["singles"] += 1
            elif lines == 2:
                self.stats["doubles"] += 1
            elif lines == 3:
                self.stats["triples"] += 1
            elif lines >= 4:
                self.stats["tetrises"] += 1
        else:
            if not tspin:
                self.combo = 0
                return

        difficult = tspin or lines == 4
        if tspin:
            self.stats["tspins"] += 1
            base = TSPIN_SCORE.get(lines, 1600) * self.level
        else:
            base = SCORE_PER_LINE.get(lines, 0) * self.level

        if difficult and self.back_to_back and lines:
            base = int(base * B2B_MULTIPLIER)
            self._emit("back_to_back")
        if difficult:
            self.back_to_back = True
        elif lines:
            self.back_to_back = False

        if self.combo > 1 and lines:
            base += COMBO_BASE * (self.combo - 1) * self.level
            self._emit("combo", combo=self.combo)

        self.score += base
        if self.level > old_level:
            self._emit("level_up", level=self.level)

    def _create_particles(self, rows):
        for y in rows:
            for x in range(COLS):
                color = self.board[y][x] or (255, 255, 255)
                for _ in range(5):
                    self.particles.append(
                        {
                            "x": x * BLOCK_SIZE + BLOCK_SIZE / 2,
                            "y": y * BLOCK_SIZE + BLOCK_SIZE / 2,
                            "vx": random.uniform(-4.2, 4.2),
                            "vy": random.uniform(-7.5, -1.2),
                            "life": random.randint(22, 42),
                            "max_life": 42,
                            "color": color,
                            "size": random.uniform(2.0, 4.5),
                            "g": 0.28,
                        }
                    )
        # extra spark for tetris
        if len(rows) >= 4:
            for _ in range(80):
                self.particles.append(
                    {
                        "x": random.uniform(0, COLS * BLOCK_SIZE),
                        "y": random.uniform(min(rows) * BLOCK_SIZE, (max(rows) + 1) * BLOCK_SIZE),
                        "vx": random.uniform(-6, 6),
                        "vy": random.uniform(-9, 2),
                        "life": random.randint(28, 55),
                        "max_life": 55,
                        "color": random.choice(COLORS),
                        "size": random.uniform(1.5, 3.5),
                        "g": 0.22,
                    }
                )

    def update_particles(self):
        alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["vy"] += p.get("g", 0.2)
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive

    # --- tick ---------------------------------------------------------

    def update(self, dt_ms, soft_drop=False):
        """Advance simulation by dt milliseconds. Returns event list this frame."""
        self.events = []
        self.soft_dropping = soft_drop
        self.update_particles()
        if self.game_over or self.paused:
            return self.events

        if self.clearing_rows:
            self.clear_timer -= dt_ms
            if self.clear_timer <= 0:
                self._finish_line_clear()
            return self.events

        if self.entry_timer > 0:
            self.entry_timer -= dt_ms
            if self.entry_timer <= 0:
                self.current_piece = self._spawn_from_queue()
            return self.events

        if not self.current_piece:
            self.current_piece = self._spawn_from_queue()
            return self.events

        if self.force_lock:
            self.force_lock = False
            self._lock_current()
            return self.events

        grav = gravity_ms(self.level)
        self.drop_delay = SOFT_DROP_MS if soft_drop else grav
        
        if soft_drop:
            # Soft drop: move 1 cell per frame (not time-accumulated)
            if self.current_piece and not self._grounded() and not self.force_lock:
                self.current_piece["y"] += 1
                self.score += SOFT_DROP_POINTS
                self.last_rotate = False
                self.lock_timer = 0
        else:
            # Normal gravity: time-accumulated
            self._grav_acc = getattr(self, "_grav_acc", 0) + dt_ms
            while self._grav_acc >= grav and self.current_piece and not self.force_lock:
                self._grav_acc -= grav
                if not self._grounded():
                    self.current_piece["y"] += 1
                    self.last_rotate = False
                    self.lock_timer = 0
                else:
                    break

        if self.current_piece and self._grounded():
            self.lock_timer += dt_ms
            if self.lock_timer >= LOCK_DELAY_MS:
                self._lock_current()
        return self.events

    def get_ghost_y(self):
        if not self.current_piece:
            return None
        gy = self.current_piece["y"]
        while self.is_valid_move(self.current_piece["x"], gy + 1, self.current_piece["shape"]):
            gy += 1
        return gy

    def high_score(self):
        if not self.high_scores:
            return 0
        return self.high_scores[0]["score"]

    def qualifies_for_highscore(self):
        if self.score <= 0:
            return False
        if len(self.high_scores) < MAX_HIGH_SCORES:
            return True
        return self.score > self.high_scores[-1]["score"]

    def submit_highscore(self, initials):
        initials = (initials or "AAA")[:3].upper()
        self.high_scores.append(
            {
                "name": initials,
                "score": self.score,
                "lines": self.lines_cleared_total,
                "level": self.level,
            }
        )
        self.high_scores.sort(key=lambda e: e["score"], reverse=True)
        self.high_scores = self.high_scores[:MAX_HIGH_SCORES]
        self.save_highscores()

    def load_highscores(self):
        try:
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "high_score" in data:
                return [{"name": "---", "score": int(data["high_score"]), "lines": 0, "level": 1}]
            if isinstance(data, list):
                cleaned = []
                for row in data:
                    cleaned.append(
                        {
                            "name": str(row.get("name", "---"))[:3].upper(),
                            "score": int(row.get("score", 0)),
                            "lines": int(row.get("lines", 0)),
                            "level": int(row.get("level", 1)),
                        }
                    )
                cleaned.sort(key=lambda e: e["score"], reverse=True)
                return cleaned[:MAX_HIGH_SCORES]
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            pass
        return []

    def save_highscores(self):
        tmp = HIGHSCORE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.high_scores, f, indent=2)
        os.replace(tmp, HIGHSCORE_FILE)

    def _emit(self, name, **payload):
        event = {"name": name}
        event.update(payload)
        self.events.append(event)

    # compatibility shims used by older entry points
    def queue_key(self, key):
        mapping = {
            "Left": lambda: self.move(-1, 0),
            "Right": lambda: self.move(1, 0),
            "Down": lambda: self.move(0, 1),
            "Up": lambda: self.rotate(1),
            "HardDrop": self.hard_drop,
            "Hold": self.hold,
            "CCW": lambda: self.rotate(-1),
        }
        fn = mapping.get(key)
        if fn:
            fn()

    def process_key_queue(self):
        return 0

    def new_piece(self):
        return self._make_piece()

    def clear_lines(self):
        rows = self._full_rows()
        if not rows:
            self.combo = 0
            return 0
        self.clearing_rows = rows
        self._finish_line_clear()
        return len(rows)
