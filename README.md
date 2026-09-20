"""Neon Tetris

A rebuilt arcade Tetris: 7-bag, hold, next queue, lock delay, DAS,
T-spins, back-to-back, neon bloom, CRT overlay, and chiptune music.

Run
---
    cd tetris-game
    .venv/bin/python tetris.py

If the venv is missing pygame:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python tetris.py

Controls
--------
    ← → / A D     move (DAS)
    ↑ / W / X     rotate CW
    Z / Ctrl      rotate CCW
    ↓ / S         soft drop
    Space         hard drop
    C / Shift     hold
    P             pause
    F5            restart
    M             toggle music
    Esc           pause / back to menu
"""
