"""Global constants and configuration settings for Breakout Precision (Neon Synthwave Theme)."""

import os

# Window Configuration
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
TARGET_FPS = 60
TITLE = "NeonBreak: Break Bounce Conquer"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

# Custom Font Paths (Matched directly to assets/fonts/)
FONT_HEADING_PATH = os.path.join(FONTS_DIR, "Orbitron-Bold.ttf")
FONT_BODY_PATH = os.path.join(FONTS_DIR, "Rajdhani-SemiBold.ttf")

# Neon Synthwave Palette
COLOR_BG = (10, 15, 46)           # Deep Blue (#0A0F2E) - Main Background
COLOR_SURFACE = (20, 12, 47)      # Dark Purple (#140C2F) - Cards & Overlays
COLOR_TEXT = (255, 255, 255)      # Pure White
COLOR_TEXT_DIM = (0, 229, 255)    # Neon Cyan (#00E5FF) - Prompts & Badges

# Extended Neon Palette
COLOR_NEON_CYAN = (0, 229, 255)        # #00E5FF - Standard / Moving Bricks
COLOR_ELECTRIC_PURPLE = (176, 38, 255) # #B026FF - Armored Bricks
COLOR_HOT_PINK = (255, 45, 149)        # #FF2D95 - Explosive Bricks & Laser
COLOR_SUNSET_ORANGE = (255, 159, 28)    # #FF9F1C - Power-ups & Combo Text

# Core Game Element Colors
COLOR_PADDLE = COLOR_NEON_CYAN
COLOR_BALL = COLOR_HOT_PINK
COLOR_ACCENT = COLOR_ELECTRIC_PURPLE

# Physics Defaults
PADDLE_SPEED = 650.0  # Pixels per second
BALL_SPEED = 450.0    # Pixels per second