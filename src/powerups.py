"""Power-Up entity and laser projectile with Synthwave neon visual styling."""

from enum import Enum, auto
import os
import pygame
from src.config import (
    SCREEN_HEIGHT,
    COLOR_NEON_CYAN,
    COLOR_ELECTRIC_PURPLE,
    COLOR_HOT_PINK,
    COLOR_SUNSET_ORANGE,
    COLOR_SURFACE,
    FONT_BODY_PATH
)


class PowerUpType(Enum):
    WIDE_PADDLE = auto()
    SLOW_MOTION = auto()
    MULTIBALL = auto()
    LASER_PADDLE = auto()


class PowerUp:
    def __init__(self, x: float, y: float, power_type: PowerUpType, speed: float = 180.0):
        self.x = x
        self.y = y
        self.width = 34.0
        self.height = 18.0
        self.power_type = power_type
        self.speed = speed
        self.is_collected = False
        self.is_offscreen = False

        if FONT_BODY_PATH and pygame.font.get_init() and os.path.exists(FONT_BODY_PATH):
            try:
                self.font = pygame.font.Font(FONT_BODY_PATH, 14)
            except Exception:
                self.font = pygame.font.SysFont("Rajdhani", 14, bold=True)
        else:
            self.font = pygame.font.SysFont("Segoe UI", 14, bold=True)

    @property
    def rect(self) -> pygame.FRect:
        return pygame.FRect(self.x - self.width / 2.0, self.y - self.height / 2.0, self.width, self.height)

    def update(self, dt: float):
        self.y += self.speed * dt
        if self.y - self.height / 2.0 > SCREEN_HEIGHT:
            self.is_offscreen = True

    def _get_type_style(self) -> tuple[tuple[int, int, int], str]:
        if self.power_type == PowerUpType.WIDE_PADDLE:
            return (COLOR_NEON_CYAN, "W")
        elif self.power_type == PowerUpType.SLOW_MOTION:
            return (COLOR_ELECTRIC_PURPLE, "S")
        elif self.power_type == PowerUpType.MULTIBALL:
            return (COLOR_SUNSET_ORANGE, "M")
        elif self.power_type == PowerUpType.LASER_PADDLE:
            return (COLOR_HOT_PINK, "L")
        return (COLOR_NEON_CYAN, "?")

    def draw(self, surface: pygame.Surface):
        if self.is_collected or self.is_offscreen:
            return

        neon_color, label = self._get_type_style()
        r = self.rect

        # 1. Dark Purple Capsule Base
        pygame.draw.rect(surface, COLOR_SURFACE, r, border_radius=6)

        # 2. Outer Soft Glow Frame
        glow_rect = r.inflate(4, 4)
        pygame.draw.rect(surface, neon_color, glow_rect, width=1, border_radius=8)

        # 3. Crisp Inner Outline
        pygame.draw.rect(surface, neon_color, r, width=2, border_radius=6)

        # 4. Badge Text
        txt = self.font.render(label, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(txt, txt_rect)


class Laser:
    def __init__(self, x: float, y: float, speed: float = 800.0):
        self.x = x
        self.y = y
        self.width = 4.0
        self.height = 16.0
        self.speed = speed
        self.is_offscreen = False

    @property
    def rect(self) -> pygame.FRect:
        return pygame.FRect(self.x - self.width / 2.0, self.y, self.width, self.height)

    def update(self, dt: float):
        self.y -= self.speed * dt
        if self.y + self.height < 0:
            self.is_offscreen = True

    def draw(self, surface: pygame.Surface):
        if self.is_offscreen:
            return

        r = self.rect

        # 1. Outer Laser Energy Glow
        glow_rect = pygame.FRect(self.x - (self.width + 4) / 2.0, self.y - 2, self.width + 4, self.height + 4)
        g_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(g_surf, (*COLOR_HOT_PINK, 120), g_surf.get_rect(), border_radius=3)
        surface.blit(g_surf, (glow_rect.x, glow_rect.y))

        # 2. Hot Inner Core Line
        pygame.draw.rect(surface, (255, 255, 255), r, border_radius=2)