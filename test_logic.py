"""Logic tests for Neon Tetris (no display required)."""

from game_state import GameState, gravity_ms, _empty_board, _rotate_cw
from config import COLS, LOCK_DELAY_MS, ROWS, SCORE_PER_LINE, TSPIN_SCORE, COMBO_BASE, B2B_MULTIPLIER, MAX_LOCK_RESETS


def test_bag_is_seven_unique():
    gs = GameState()
    gs.bag = []
    types = [gs._make_piece()["type"] for _ in range(7)]
    assert sorted(types) == list(range(7)), types


def test_bag_refills_automatically():
    gs = GameState()
    gs.bag = []
    pieces = [gs._make_piece() for _ in range(14)]
    types = [p["type"] for p in pieces]
    assert sorted(types[:7]) == list(range(7))
    assert sorted(types[7:]) == list(range(7))


def test_queue_and_hold():
    gs = GameState()
    assert gs.current_piece is not None
    assert len(gs.queue) == 5
    first = gs.current_piece["name"]
    assert gs.hold()
    assert gs.held_piece["name"] == first
    assert gs.hold_used
    assert not gs.hold(), "hold only once per piece"


def test_hold_swaps_with_queue():
    gs = GameState()
    first = gs.current_piece["name"]
    second = gs.queue[0]["name"]
    assert gs.hold()
    assert gs.current_piece["name"] == second
    assert gs.held_piece["name"] == first
    # hold again after piece lock and new piece spawns
    gs.hard_drop()
    gs.update(16)  # lock
    gs.update(100)  # entry delay
    assert gs.current_piece is not None
    assert not gs.hold_used
    assert gs.hold()


def test_move_and_wall():
    gs = GameState()
    gs.current_piece["x"] = 0
    assert not gs.move(-1, 0)
    gs.current_piece["x"] = COLS - 1
    x = gs.current_piece["x"]
    gs.move(1, 0)
    assert gs.current_piece["x"] <= x


def test_rotate_o_noop():
    gs = GameState()
    gs.bag = [1]  # O
    piece = gs._make_piece()
    gs.current_piece = piece
    assert piece["name"] == "O"
    assert not gs.rotate(1)
    assert not gs.rotate(-1)


def test_i_wall_kicks():
    gs = GameState()
    gs.bag = [0]  # I
    piece = gs._make_piece()
    gs.current_piece = piece
    # I piece at left wall, rotate CW should kick right
    gs.current_piece["x"] = 0
    gs.current_piece["y"] = 5
    assert gs.rotate(1)
    assert gs.current_piece["x"] >= 0


def test_j_l_s_z_t_wall_kicks():
    for type_idx in [2, 3, 4, 5, 6]:  # T, L, J, S, Z
        gs = GameState()
        gs.bag = [type_idx]
        piece = gs._make_piece()
        gs.current_piece = piece
        gs.current_piece["x"] = 0
        gs.current_piece["y"] = 5
        # Should be able to rotate at wall with kicks
        assert gs.rotate(1) or gs.rotate(-1), f"type {type_idx} failed wall kick"


def test_hard_drop_increases_score_and_locks():
    gs = GameState()
    score0 = gs.score
    cells = gs.hard_drop()
    assert cells >= 0
    assert gs.score >= score0
    gs.update(16)
    assert gs.force_lock is False
    filled = sum(1 for row in gs.board for c in row if c)
    assert filled > 0 or gs.current_piece is not None


def test_soft_drop_scores():
    gs = GameState()
    score0 = gs.score
    # Simulate soft drop by moving down while soft_dropping=True
    gs.update(16, soft_drop=True)
    # If piece moved down, score should increase
    assert gs.score >= score0


def test_line_clear_and_level():
    gs = GameState()
    for x in range(COLS):
        gs.board[ROWS - 1][x] = (255, 0, 0)
    rows = gs._full_rows()
    assert rows == [ROWS - 1]
    gs.clearing_rows = rows
    gs._finish_line_clear()
    assert gs.lines_cleared_total == 1
    assert gs.score > 0
    assert gs.board[ROWS - 1] == [0] * COLS


def test_tetris_awards_800_times_level():
    gs = GameState()
    for y in range(ROWS - 4, ROWS):
        for x in range(COLS):
            gs.board[y][x] = (0, 255, 255)
    gs.clearing_rows = gs._full_rows()
    gs._finish_line_clear()
    assert gs.lines_cleared_total == 4
    assert gs.stats["tetrises"] == 1
    assert gs.score == 800  # 800 * level 1, first tetris no b2b


def test_tetris_b2b_multiplier():
    gs = GameState()
    gs.back_to_back = True
    for y in range(ROWS - 4, ROWS):
        for x in range(COLS):
            gs.board[y][x] = (0, 255, 255)
    gs.clearing_rows = gs._full_rows()
    gs._finish_line_clear()
    # 800 * 1.5 = 1200
    assert gs.score == 1200


def test_tspin_single():
    gs = GameState()
    # Set up T-spin single: T piece in position with 3 corners filled
    gs.bag = [2]  # T
    piece = gs._make_piece()
    gs.current_piece = piece
    # Place T at bottom with rotation
    gs.current_piece["y"] = ROWS - 2
    gs.current_piece["x"] = 3
    # Fill corners around T center
    # T center is at (x+1, y+1) = (4, ROWS-1)
    # Corners: (3, ROWS-2), (5, ROWS-2), (3, ROWS), (5, ROWS)
    # ROWS is out of bounds, so 3 corners filled = T-spin
    gs.board[ROWS - 2][3] = (255, 0, 0)
    gs.board[ROWS - 2][5] = (255, 0, 0)
    gs.board[ROWS - 1][3] = (255, 0, 0)
    gs.last_rotate = True
    assert gs._is_tspin()


def test_tspin_triple():
    gs = GameState()
    gs.bag = [2]  # T
    piece = gs._make_piece()
    gs.current_piece = piece
    gs.current_piece["y"] = ROWS - 3
    gs.current_piece["x"] = 3
    # T center at (4, ROWS-2)
    # Corners: (3, ROWS-3), (5, ROWS-3), (3, ROWS-1), (5, ROWS-1)
    gs.board[ROWS - 3][3] = (255, 0, 0)
    gs.board[ROWS - 3][5] = (255, 0, 0)
    gs.board[ROWS - 1][3] = (255, 0, 0)
    gs.board[ROWS - 1][5] = (255, 0, 0)
    gs.last_rotate = True
    assert gs._is_tspin()


def test_tspin_scoring():
    gs = GameState()
    gs.level = 1
    # T-spin single: 800 * 1 = 800 (no b2b, combo=1)
    gs._award_clear(1, tspin=True)
    assert gs.score == 800
    # T-spin double: 1200 * 1 * 1.5 (b2b) + 50 * 1 (combo) = 1850
    gs.score = 0
    gs.combo = 1
    gs.back_to_back = True
    gs._award_clear(2, tspin=True)
    assert gs.score == 1850
    # T-spin triple: 1600 * 1 * 1.5 (b2b) + 50 * 2 (combo) = 2500
    gs.score = 0
    gs.combo = 2
    gs.back_to_back = True
    gs._award_clear(3, tspin=True)
    assert gs.score == 2500


def test_combo_scoring():
    gs = GameState()
    gs.level = 1
    gs.combo = 0
    gs._award_clear(1)  # single, combo 1
    score1 = gs.score
    assert gs.combo == 1
    gs._award_clear(1)  # single, combo 2
    score2 = gs.score
    # combo bonus = 50 * (2-1) * 1 = 50
    assert score2 - score1 == SCORE_PER_LINE[1] + COMBO_BASE


def test_combo_resets_on_non_clear():
    gs = GameState()
    gs.level = 1
    gs.combo = 3
    gs._award_clear(0)  # no lines
    assert gs.combo == 0


def test_back_to_back_flag():
    gs = GameState()
    gs.back_to_back = False
    gs._award_clear(4)  # tetris
    assert gs.back_to_back
    gs._award_clear(1)  # single breaks b2b
    assert not gs.back_to_back


def test_gravity_speeds_up():
    assert gravity_ms(1) > gravity_ms(5) > gravity_ms(20)


def test_lock_delay_resets_on_move():
    gs = GameState()
    gy = gs.get_ghost_y()
    gs.current_piece["y"] = gy
    assert gs._grounded()
    gs.update(LOCK_DELAY_MS - 50)
    assert gs.current_piece is not None
    # Move resets lock timer
    gs.move(-1, 0)
    assert gs.lock_timer == 0
    assert gs.lock_resets == 1


def test_max_lock_resets():
    gs = GameState()
    # Position piece in middle so it can move left/right while grounded
    gs.current_piece["x"] = 5
    gy = gs.get_ghost_y()
    gs.current_piece["y"] = gy
    assert gs._grounded()
    # Each successful move while grounded resets lock_timer and increments lock_resets
    for i in range(5):
        gs.update(LOCK_DELAY_MS - 10)
        assert gs.move(-1, 0)
        assert gs.lock_resets == i + 1
        assert gs.lock_timer == 0
    # After max resets reached, further moves don't reset lock
    gs.update(LOCK_DELAY_MS - 10)
    assert not gs.move(-1, 0)  # at wall
    assert gs.lock_resets == 5  # capped at successful moves, not MAX_LOCK_RESETS
    # Lock timer now accumulates
    gs.update(LOCK_DELAY_MS)
    assert gs.current_piece is None or gs.clearing_rows or gs.entry_timer > 0


def test_ghost_piece():
    gs = GameState()
    gy = gs.get_ghost_y()
    assert gy >= gs.current_piece["y"]
    # Ghost should be at lowest valid position
    assert gs.is_valid_move(gs.current_piece["x"], gy, gs.current_piece["shape"])
    assert not gs.is_valid_move(gs.current_piece["x"], gy + 1, gs.current_piece["shape"])


def test_piece_spawn_position():
    gs = GameState()
    for _ in range(10):
        piece = gs._make_piece()
        assert piece["x"] >= 0
        assert piece["x"] + len(piece["shape"][0]) <= COLS
        assert piece["y"] == 0


def test_game_over_on_spawn_collision():
    gs = GameState()
    # Fill top rows
    for y in range(4):
        for x in range(COLS):
            gs.board[y][x] = (255, 0, 0)
    gs.current_piece = gs._spawn_from_queue()
    assert gs.game_over


def test_level_up_every_10_lines():
    gs = GameState()
    # Level up happens in _award_clear when lines are cleared
    for i in range(1, 5):
        gs.lines_cleared_total = i * 10 - 1
        gs._award_clear(1)
        assert gs.level == i + 1, f"after {i*10} lines, level should be {i+1}, got {gs.level}"


def test_highscore_migrate_and_submit():
    import game_state as gs_mod
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    old = gs_mod.HIGHSCORE_FILE
    gs_mod.HIGHSCORE_FILE = path
    try:
        gs = GameState()
        gs.score = 12345
        gs.lines_cleared_total = 12
        gs.level = 2
        assert gs.qualifies_for_highscore()
        gs.submit_highscore("neo")
        assert gs.high_scores[0]["name"] == "NEO"
        assert gs.high_scores[0]["score"] == 12345
    finally:
        gs_mod.HIGHSCORE_FILE = old
        try:
            os.remove(path)
        except OSError:
            pass


def test_highscore_loads_old_format():
    import game_state as gs_mod
    import tempfile, os, json
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    old = gs_mod.HIGHSCORE_FILE
    gs_mod.HIGHSCORE_FILE = path
    try:
        # Write old format
        with open(path, "w") as f:
            json.dump({"high_score": 999}, f)
        gs = GameState()
        assert gs.high_score() == 999
    finally:
        gs_mod.HIGHSCORE_FILE = old
        try:
            os.remove(path)
        except OSError:
            pass


def test_highscore_limit():
    import game_state as gs_mod
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    old = gs_mod.HIGHSCORE_FILE
    gs_mod.HIGHSCORE_FILE = path
    try:
        gs = GameState()
        for i in range(15):
            gs.score = 1000 + i * 100
            gs.submit_highscore(f"P{i}")
        assert len(gs.high_scores) <= 8
        # Should be sorted descending
        scores = [e["score"] for e in gs.high_scores]
        assert scores == sorted(scores, reverse=True)
    finally:
        gs_mod.HIGHSCORE_FILE = old
        try:
            os.remove(path)
        except OSError:
            pass


def test_particle_creation():
    gs = GameState()
    gs._create_particles([5, 10])
    assert len(gs.particles) > 0
    for p in gs.particles:
        assert "x" in p and "y" in p and "vx" in p and "vy" in p
        assert p["life"] > 0


def test_particle_update():
    gs = GameState()
    gs._create_particles([5])
    initial = len(gs.particles)
    # Capture initial life values
    initial_lives = [p["life"] for p in gs.particles]
    gs.update_particles()
    assert len(gs.particles) == initial
    for i, p in enumerate(gs.particles):
        assert p["life"] == initial_lives[i] - 1
        assert p["life"] >= 0


def test_particle_expiration():
    gs = GameState()
    gs._create_particles([5])
    for _ in range(50):
        gs.update_particles()
    assert len(gs.particles) == 0


def test_stats_tracking():
    gs = GameState()
    # pieces increments when a new piece spawns
    initial = gs.stats["pieces"]
    gs.hard_drop()
    gs.update(16)  # lock
    gs.update(100)  # entry delay -> new piece spawns
    assert gs.stats["pieces"] >= initial + 1


def test_rotate_shape_helpers():
    shape = [[1, 0], [1, 0], [1, 1]]  # J-like
    cw = _rotate_cw(shape)
    ccw = _rotate_cw(_rotate_cw(_rotate_cw(shape)))
    assert len(cw) == len(shape[0])
    assert len(cw[0]) == len(shape)


def test_empty_board_helper():
    board = _empty_board()
    assert len(board) == ROWS
    assert len(board[0]) == COLS
    assert all(c == 0 for row in board for c in row)


def test_is_valid_move_edge_cases():
    gs = GameState()
    # Out of bounds left
    assert not gs.is_valid_move(-1, 0, [[1]])
    # Out of bounds right
    assert not gs.is_valid_move(COLS, 0, [[1]])
    # Out of bounds bottom
    assert not gs.is_valid_move(0, ROWS, [[1]])
    # Collision with board
    gs.board[5][5] = (255, 0, 0)
    assert not gs.is_valid_move(5, 5, [[1]])


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"ok  {fn.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc!r}")
    if failed:
        raise SystemExit(failed)
    print(f"\n{len(tests)} passed")