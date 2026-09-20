# Tetris Game Improvement Tasks

## Priority 1: Core Gameplay Improvements (High Impact)

### 1. Implement Standard Tetris Scoring System
- **Impact**: High - Core game mechanic
- **Tasks**:
  - Replace `lines_cleared * 100` with standard scoring (40/100/300/1200 × level)
  - Add level system (level up every 10 lines)
  - Increase game speed as levels progress
  - Display level and lines cleared in UI

### 2. Add Next Piece Preview
- **Impact**: High - Essential Tetris feature
- **Tasks**:
  - Add canvas area for next piece preview
  - Store next piece in game state
  - Display next piece in preview area
  - Update piece rotation when current piece locks

### 3. Add Ghost Piece (Shadow)
- **Impact**: High - Improves gameplay experience
- **Tasks**:
  - Calculate where current piece will land
  - Draw semi-transparent "ghost" at landing position
  - Helps players aim drops

## Priority 2: User Experience Improvements (Medium Impact)

### 4. Add Pause Display Indicator
- **Impact**: Medium - Better UX
- **Tasks**:
  - Show "PAUSED" text when game is paused
  - Display pause status clearly on canvas

### 5. Add High Score System
- **Impact**: Medium - Adds replay value
- **Tasks**:
  - Save/load high score from file
  - Display current high score
  - Update high score when game ends

### 6. Improve Game Over Screen
- **Impact**: Medium - Better feedback
- **Tasks**:
  - Show final score on game over screen
  - Add restart button or clear instructions
  - Display high score on game over

## Priority 3: Code Quality Improvements (Lower Impact)

### 7. Refactor Code Structure
- **Impact**: Low-Medium - Better maintainability
- **Tasks**:
  - Separate game logic from rendering
  - Extract constants to config file
  - Add docstrings to methods
  - Follow PEP 8 spacing guidelines

### 8. Add Input Buffer
- **Impact**: Low - Better responsiveness
- **Tasks**:
  - Implement input queuing for rapid key presses
  - Prevent missed inputs during fast play

### 9. Add Sound Effects (Optional)
- **Impact**: Low - Polish feature
- **Tasks**:
  - Add sounds for rotation, line clear, game over
  - Use tkinter's built-in audio or simple beeps

---

## Implementation Order

1. Priority 1, Task 1: Standard Scoring System
2. Priority 1, Task 2: Next Piece Preview
3. Priority 1, Task 3: Ghost Piece
4. Priority 2, Task 1: Pause Display
5. Priority 2, Task 2: High Score
6. Priority 2, Task 3: Game Over Screen
7. Priority 3, Task 1: Code Refactoring
8. Priority 3, Task 2: Input Buffer
9. Priority 3, Task 3: Sound Effects

---

*This TODO list tracks improvements to the Tetris game.*
