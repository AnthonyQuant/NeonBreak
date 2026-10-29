"""Specialized Brick entity hierarchy with dual-layer neon glowing outlines for Breakout Precision."""

from enum import Enum, auto
import pygame
from src.config import (
    COLOR_NEON_CYAN,
    COLOR_ELECTRIC_PURPLE,
    COLOR_HOT_PINK,
    COLOR_SUNSET_ORANGE,
    COLOR_SURFACE
)


class BrickType(Enum):
    STANDARD = auto()
    ARMORED = auto()      # Requires 2 hits to destroy
    EXPLOSIVE = auto()    # Destroys adjacent breakable bricks upon destruction
    MOVING = auto()       # Shifts back and forth along a horizontal path
    UNBREAKABLE = auto()  # Indestructible obstacle


class Brick:
    def __init__(
        self,
        x: float,
        y: float,
        width: float = 75.0,
        height: float = 24.0,
        brick_type: BrickType = BrickType.STANDARD,
        move_range: tuple[float, float] = (0.0, 0.0),
        move_speed: float = 90.0
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.brick_type = brick_type
        self.is_destroyed = False

        # Hit resistance initialization
        if self.brick_type == BrickType.ARMORED:
            self.max_hits = 2
        elif self.brick_type == BrickType.UNBREAKABLE:
            self.max_hits = -1  # Indestructible
        else:
            self.max_hits = 1

        self.hits_left = self.max_hits

        # Patrol properties for MOVING bricks
        self.is_moving = (self.brick_type == BrickType.MOVING)
        self.min_x, self.max_x = move_range
        self.move_speed = move_speed
        self.move_dir = 1.0  # 1.0 = move right, -1.0 = move left

    @property
    def is_unbreakable(self) -> bool:
        return self.brick_type == BrickType.UNBREAKABLE

    @property
    def rect(self) -> pygame.FRect:
        return pygame.FRect(self.x, self.y, self.width, self.height)

    def update(self, dt: float):
        """Updates position for moving bricks patrolling between min_x and max_x."""
        if self.is_moving and not self.is_destroyed:
            # Prevent movement if range is insufficient for brick width
            if self.max_x <= self.min_x or (self.max_x - self.min_x) <= self.width:
                return

            self.x += self.move_dir * self.move_speed * dt
            if self.x <= self.min_x:
                self.x = self.min_x
                self.move_dir = 1.0
            elif self.x + self.width >= self.max_x:
                self.x = self.max_x - self.width
                self.move_dir = -1.0

    def hit(self) -> bool:
        """
        Applies a hit to the brick.
        Returns True if this hit broke/destroyed the brick.
        """
        if self.is_unbreakable or self.is_destroyed:
            return False

        self.hits_left -= 1
        if self.hits_left <= 0:
            self.is_destroyed = True
            return True
        return False

    def _get_neon_palette(self) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        """Returns (fill_color, neon_border_color) based on brick type."""
        if self.brick_type == BrickType.STANDARD:
            return (COLOR_SURFACE, COLOR_NEON_CYAN)
        elif self.brick_type == BrickType.ARMORED:
            if self.hits_left == 2:
                return (COLOR_SURFACE, COLOR_ELECTRIC_PURPLE)
            return (COLOR_SURFACE, (120, 20, 180))  # Darker purple when damaged
        elif self.brick_type == BrickType.EXPLOSIVE:
            return (COLOR_SURFACE, COLOR_HOT_PINK)
        elif self.brick_type == BrickType.MOVING:
            return (COLOR_SURFACE, COLOR_SUNSET_ORANGE)
        elif self.brick_type == BrickType.UNBREAKABLE:
            return ((15, 18, 35), (80, 95, 130))
        return (COLOR_SURFACE, COLOR_NEON_CYAN)

    def draw(self, surface: pygame.Surface):
        if self.is_destroyed:
            return

        fill_color, border_color = self._get_neon_palette()
        r = self.rect

        # 1. Dark Purple Fill Surface
        pygame.draw.rect(surface, fill_color, r, border_radius=4)

        # 2. Outer Soft Neon Glow Frame
        glow_rect = r.inflate(4, 4)
        pygame.draw.rect(surface, border_color, glow_rect, width=1, border_radius=6)

        # 3. Crisp Inner Neon Outline
        pygame.draw.rect(surface, border_color, r, width=2, border_radius=4)

        # 4. Icon/Pattern Details
        if self.brick_type == BrickType.EXPLOSIVE:
            cx, cy = int(r.centerx), int(r.centery)
            pygame.draw.circle(surface, COLOR_SUNSET_ORANGE, (cx, cy), 4)
        elif self.brick_type == BrickType.UNBREAKABLE:
            pygame.draw.line(surface, border_color, (r.left + 6, r.bottom - 4), (r.right - 6, r.top + 4), 2)
            pygame.draw.line(surface, border_color, (r.left + 6, r.top + 4), (r.right - 6, r.bottom - 4), 2)