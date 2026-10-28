"""Paddle entity with vector movement, power-up timers, laser cannons, and Synthwave neon styling."""

import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, PADDLE_SPEED,
    COLOR_PADDLE, COLOR_NEON_CYAN, COLOR_ELECTRIC_PURPLE,
    COLOR_HOT_PINK, COLOR_SUNSET_ORANGE, COLOR_SURFACE
)
from src.powerups import Laser


class Paddle:
    def __init__(self, width: float = 120.0, height: float = 18.0):
        self.base_width = width
        self.width = width
        self.height = height

        self.x = (SCREEN_WIDTH - self.width) / 2.0
        self.y = SCREEN_HEIGHT - 60.0
        self.speed = PADDLE_SPEED

        # Active power-up timers
        self.wide_timer = 0.0
        self.laser_timer = 0.0
        self.laser_cooldown = 0.0

    @property
    def rect(self) -> pygame.FRect:
        return pygame.FRect(self.x, self.y, self.width, self.height)

    @property
    def has_laser(self) -> bool:
        return self.laser_timer > 0.0

    @property
    def is_wide(self) -> bool:
        return self.wide_timer > 0.0

    def apply_wide_paddle(self, duration: float = 10.0):
        self.wide_timer = duration
        old_center = self.x + self.width / 2.0
        self.width = 180.0
        self.x = old_center - self.width / 2.0
        self._clamp_x()

    def apply_laser_paddle(self, duration: float = 10.0):
        self.laser_timer = duration

    def shoot_lasers(self) -> list[Laser]:
        lasers = []
        if self.has_laser and self.laser_cooldown <= 0.0:
            self.laser_cooldown = 0.22  # Fire rate limiter (seconds)
            left_x = self.x + 8.0
            right_x = self.x + self.width - 8.0
            lasers.append(Laser(left_x, self.y - 12.0))
            lasers.append(Laser(right_x, self.y - 12.0))
        return lasers

    def _clamp_x(self):
        """Clamps paddle x-coordinate strictly within screen boundaries."""
        if self.x < 0:
            self.x = 0
        elif self.x + self.width > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.width

    def update(self, dt: float):
        if dt <= 0.0:
            return

        # Update power-up timers
        if self.wide_timer > 0:
            self.wide_timer -= dt
            if self.wide_timer <= 0:
                old_center = self.x + self.width / 2.0
                self.width = self.base_width
                self.x = old_center - self.width / 2.0
                self._clamp_x()

        if self.laser_timer > 0:
            self.laser_timer -= dt

        if self.laser_cooldown > 0:
            self.laser_cooldown -= dt

        keys = pygame.key.get_pressed()
        move_dir = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_dir -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_dir += 1.0

        self.x += move_dir * self.speed * dt
        self._clamp_x()

    def draw(self, surface: pygame.Surface):
        # Determine Border / Glow Color based on Active Power-ups
        if self.is_wide and self.has_laser:
            glow_color = COLOR_SUNSET_ORANGE
        elif self.is_wide:
            glow_color = COLOR_ELECTRIC_PURPLE
        elif self.has_laser:
            glow_color = COLOR_HOT_PINK
        else:
            glow_color = COLOR_NEON_CYAN

        r = self.rect

        # 1. Dark Core Fill
        pygame.draw.rect(surface, COLOR_SURFACE, r, border_radius=6)

        # 2. Outer Soft Neon Glow Frame
        glow_rect = r.inflate(6, 6)
        pygame.draw.rect(surface, glow_color, glow_rect, width=1, border_radius=8)

        # 3. Crisp Inner Neon Outline
        pygame.draw.rect(surface, glow_color, r, width=2, border_radius=6)

        # 4. Top Edge Neon Highlight Strip
        top_line_left = (int(r.left + 4), int(r.top + 2))
        top_line_right = (int(r.right - 4), int(r.top + 2))
        pygame.draw.line(surface, (255, 255, 255), top_line_left, top_line_right, 2)

        # 5. Laser Cannon Attachments
        if self.has_laser:
            cannon_w = 6.0
            cannon_h = 10.0
            left_rect = pygame.FRect(self.x + 4, self.y - cannon_h, cannon_w, cannon_h)
            right_rect = pygame.FRect(self.x + self.width - 10, self.y - cannon_h, cannon_w, cannon_h)

            pygame.draw.rect(surface, COLOR_SURFACE, left_rect, border_radius=2)
            pygame.draw.rect(surface, COLOR_SURFACE, right_rect, border_radius=2)

            pygame.draw.rect(surface, COLOR_HOT_PINK, left_rect, width=1, border_radius=2)
            pygame.draw.rect(surface, COLOR_HOT_PINK, right_rect, width=1, border_radius=2)

            # Cannon tip energy dots
            pygame.draw.circle(surface, (255, 255, 255), (int(left_rect.centerx), int(left_rect.top + 2)), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(right_rect.centerx), int(right_rect.top + 2)), 2)