"""Optimized particle emitter with surface reuse, neon glow styling, and floating score pop-up notifications."""

import math
import random
import pygame
from src.config import COLOR_TEXT_DIM, FONT_BODY_PATH


class Particle:
    _cache_surface: pygame.Surface | None = None

    def __init__(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        vx: float = 0.0,
        vy: float = 0.0,
        radius: float = 3.5,
        lifetime: float = 0.4
    ):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.is_dead = False

    def update(self, dt: float):
        if dt <= 0.0:
            return

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_dead = True
            return

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 180.0 * dt  # Gentle downward gravity for neon sparks

    def draw(self, surface: pygame.Surface):
        if self.is_dead:
            return

        alpha_ratio = max(0.0, self.lifetime / self.max_lifetime)
        current_radius = max(1, int(self.radius * alpha_ratio))
        diameter = current_radius * 2

        required_size = max(32, diameter)
        if Particle._cache_surface is None or Particle._cache_surface.get_width() < required_size:
            Particle._cache_surface = pygame.Surface((required_size, required_size), pygame.SRCALPHA)

        p_surf = Particle._cache_surface
        p_surf.fill((0, 0, 0, 0))

        color_with_alpha = (*self.color[:3], int(255 * alpha_ratio))
        pygame.draw.circle(p_surf, color_with_alpha, (current_radius, current_radius), current_radius)
        surface.blit(p_surf, (int(self.x - current_radius), int(self.y - current_radius)), area=pygame.Rect(0, 0, diameter, diameter))


class FloatingText:
    """Animated text pop-up that rises upward and fades out using pre-rendered surfaces and cached fonts."""

    _font_cache: dict[int, pygame.font.Font] = {}

    @classmethod
    def _get_font(cls, font_size: int) -> pygame.font.Font:
        if font_size not in cls._font_cache:
            if FONT_BODY_PATH and pygame.font.get_init():
                try:
                    cls._font_cache[font_size] = pygame.font.Font(FONT_BODY_PATH, font_size)
                except Exception:
                    cls._font_cache[font_size] = pygame.font.SysFont("Rajdhani", font_size, bold=True)
            else:
                cls._font_cache[font_size] = pygame.font.SysFont("Segoe UI", font_size, bold=True)
        return cls._font_cache[font_size]

    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        color: tuple[int, int, int] = COLOR_TEXT_DIM,
        font_size: int = 16,
        lifetime: float = 0.65
    ):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.vy = -45.0  # Drift upward
        self.is_dead = False

        font = self._get_font(font_size)
        self.base_surf = font.render(self.text, True, self.color)

    def update(self, dt: float):
        if dt <= 0.0:
            return

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_dead = True
            return

        self.y += self.vy * dt

    def draw(self, surface: pygame.Surface):
        if self.is_dead:
            return

        alpha_ratio = max(0.0, self.lifetime / self.max_lifetime)
        alpha = int(255 * alpha_ratio)

        self.base_surf.set_alpha(alpha)
        rect = self.base_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.base_surf, rect)


class ParticleManager:
    def __init__(self):
        self.particles: list[Particle] = []
        self.floating_texts: list[FloatingText] = []

    def spawn_burst(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        count: int = 12,
        speed_min: float = 60.0,
        speed_max: float = 220.0
    ):
        for _ in range(count):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(speed_min, speed_max)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            radius = random.uniform(2.5, 4.0)
            lifetime = random.uniform(0.25, 0.45)
            self.particles.append(Particle(x, y, color, vx, vy, radius, lifetime))

    def spawn_floating_text(
        self,
        x: float,
        y: float,
        text: str,
        color: tuple[int, int, int] = COLOR_TEXT_DIM,
        font_size: int = 16
    ):
        self.floating_texts.append(FloatingText(x, y, text, color, font_size))

    def update(self, dt: float):
        if dt <= 0.0:
            return

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.is_dead]

        for ft in self.floating_texts:
            ft.update(dt)
        self.floating_texts = [ft for ft in self.floating_texts if not ft.is_dead]

    def draw(self, surface: pygame.Surface):
        for p in self.particles:
            p.draw(surface)

        for ft in self.floating_texts:
            ft.draw(surface)