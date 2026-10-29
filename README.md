# NeonBreak — Synthwave Arcade Breakout Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Pygame-CE](https://img.shields.io/badge/Pygame--CE-2.5.8-green?style=for-the-badge&logo=python)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)

A high-performance, retro synthwave Breakout engine built in Python with custom sub-stepped physics, procedural audio, state persistence, dynamic level loading, and headless automated testing.

---

## 📋 Table of Contents
- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Technical Architecture](#-technical-architecture)
- [Collision Physics & Anti-Tunneling Math](#-collision-physics--anti-tunneling-math)
- [Directory Structure](#-directory-structure)
- [Installation & Local Setup](#-installation--local-setup)
- [Automated Testing Suite](#-automated-testing-suite)
- [Building Standalone Executable (.exe)](#-building-standalone-executable-exe)
- [Controls Reference](#-controls-reference)

---

## 🚀 Project Overview

**NeonBreak** is designed as a software engineering portfolio piece demonstrating robust game logic, mathematical physics resolution, strict state management, local database persistence, and comprehensive unit testing. 

Unlike basic tutorial clones, **NeonBreak** uses sub-stepped trajectory physics to prevent high-speed tunneling, external JSON level layout configuration, procedural waveform sound generation, and a headless unit test pipeline suitable for CI/CD integration.

---

## ✨ Key Features

- **Sub-Stepped Physics Engine**: Calculates dynamic movement sub-steps per frame to resolve fast-moving ball collisions accurately without phase-through bugs.
- **Dynamic Level Parsing**: Reads level grid schemas from structured `data/levels.json` files, supporting standard, armored, explosive, moving, and unbreakable bricks.
- **Power-Up Lifecycle System**: Features Wide Paddle, Slow Motion, Multiball split vectors, and Laser Cannons with strict duration timers and clean reset mechanics.
- **Retro Synthwave Aesthetics**: Glow outlines, particle spark emitters, screen shake camera effects, floating score pop-ups, and custom typography using Orbitron and Rajdhani TTF fonts.
- **Dual Game Modes**:
  - **Classic Mode**: 3 lives, score multiplier (1.0x), and interactive trajectory guide preview.
  - **Precision Mode**: 1 life, enhanced score multiplier (1.5x), and hidden trajectory guide for high-risk play.
- **SQLite Data Persistence**: Tracks top 5 local leaderboard records per mode and cumulative lifetime brick destruction statistics in user-writable application data directories.
- **Procedural Sound Engine**: In-memory WAV waveform synthesizer for dynamic SFX and integrated background music streaming.
- **Automated Test Pipeline**: Headless `unittest` suite testing physics reflections, gameplay lifecycles, and edge-case boundary conditions.

---

## 🛠️ Technical Architecture

The project is structured to separate core engine logic from game state management, assets, and data persistence:

- **Core Engine (`src/`)**: Entity classes (`ball.py`, `paddle.py`, `brick.py`, `powerups.py`), visual effects (`particles.py`), audio (`sounds.py`), and the main state machine (`game.py`).
- **Data Layer (`data/`)**: Contains SQLite local storage (`records.db`) and JSON layout maps (`levels.json`).
- **Tests (`tests/`)**: Continuous integration ready unit tests decoupled from the Pygame GUI.

---

## 📐 Collision Physics & Anti-Tunneling Math

### 1. Sub-Step Distance Calculation
To guarantee that a ball moving at speed `v` never tunnels through a thin target box, frame displacement `s = v * dt` is partitioned into `N` equal sub-steps where `N` is defined by:

`N = max(1, ceil((v * dt) / d_max))`

Where `d_max = 4.0` pixels. Each sub-step updates position by `dt_sub = dt / N` and re-evaluates collision bounds.

### 2. Continuous Paddle Bounce Angle Deflection
Paddle collision response converts the horizontal hit location into a specular bounce angle bounded between -60 degrees and +60 degrees relative to the paddle normal:

`offset = clamp((x_ball - x_paddle_center) / (0.5 * w_paddle), -1.0, 1.0)`  
`theta_bounce = -pi/2 + (offset * pi/3)`  

`v_x = speed * cos(theta_bounce)`  
`v_y = speed * sin(theta_bounce)`  

---

## 📂 Directory Structure

```text
NeonBreak/
├── assets/                  # Binary visual & typography assets
│   └── fonts/               # Custom Orbitron & Rajdhani TTF fonts
├── data/                    # JSON schematics & default game data
│   └── levels.json          # Level grid definitions
├── src/                     # Core engine package
│   ├── ball.py              # Sub-stepped physics & trajectory prediction
│   ├── brick.py             # Brick hierarchy & durability logic
│   ├── config.py            # Global constants, paths, & palette definitions
│   ├── database.py          # SQLite manager for scores & lifetime stats
│   ├── game.py              # Central game loop & state coordinator
│   ├── paddle.py            # Paddle movement, power-up timers, & laser firing
│   ├── particles.py         # Particle emitters & floating score text
│   ├── powerups.py          # Power-up capsules & laser entity physics
│   ├── sounds.py            # Procedural synth & audio manager
│   └── states.py            # Enums for GameState and GameMode
├── tests/                   # Headless automated unit test suite
│   ├── test_audio.py        # Audio fallback & volume control tests
│   ├── test_database.py     # SQLite persistence & isolation tests
│   ├── test_gameplay.py     # Gameplay lifecycle & durability tests
│   └── test_physics.py      # Wall reflections & sub-step distance bounds
├── main.py                  # Application entry point
├── main.spec                # PyInstaller build specification
├── LICENSE                  # MIT License
├── README.md                # Project documentation
├── requirements.txt         # Runtime dependencies
└── requirements-dev.txt     # Development & build dependencies
```

---

## ⚙️ Installation & Local Setup

### Prerequisites
- Python 3.10 or higher
- Git

### Quickstart Commands

```bash
# 1. Clone repository
git clone https://github.com/AnthonyQuant/NeonBreak.git
cd NeonBreak

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 3. Install runtime dependencies
pip install -r requirements.txt

# 4. Run the game
python main.py
```

---

## 🧪 Automated Testing Suite

The engine includes headless unit tests built using `unittest`. The test harness forces Pygame into dummy video mode (`SDL_VIDEODRIVER=dummy`) so tests execute rapidly without spawning GUI windows.

Run the complete test suite:

```bash
python -m unittest discover tests
```

### Test Coverage Breakdown
- `tests/test_physics.py`: Validates horizontal/vertical wall reflection vectors, box penetration resolution, and sub-stepping distance calculations.
- `tests/test_gameplay.py`: Verifies armored brick health degradation, single-life decrement logic, pause freeze isolation, power-up timer expirations, and level completion triggers.
- `tests/test_database.py`: Confirms isolated in-memory SQLite database saving, top-N sorting, mode filtering, and cumulative brick stat updates.
- `tests/test_audio.py`: Asserts safe volume adjustments, mute toggling, and headless fallback handling when `pygame.mixer` is uninitialized.

---

## 📦 Building Standalone Executable (.exe)

You can package NeonBreak into a standalone Windows binary that runs on computers without Python installed using PyInstaller:

```bash
# Install development/build dependencies
pip install -r requirements-dev.txt

# Generate standalone directory build using spec file
pyinstaller --noconfirm main.spec
```

The output executable will be compiled inside `dist/main/main.exe`.

---

## 🎮 Controls Reference

| Action | Control Key |
|---|---|
| **Paddle Movement** | Left / Right Arrows or `A` / `D` |
| **Launch Ball / Confirm** | `SPACE` |
| **Fire Laser Cannon** | `SPACE` / `UP` / `W` (When Laser Active) |
| **Toggle Trajectory Guide** | `T` (Classic Mode Only) |
| **Pause / Resume Game** | `P` or `ESC` |
| **Return to Main Menu** | `ENTER` |
| **Adjust Sound Volume** | Left / Right / Up / Down (In Settings) |
| **Toggle Sound Mute** | `M` (In Settings) |