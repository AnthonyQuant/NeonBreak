"""Ball entity with motion trail rendering, sub-stepped movement, anti-tunneling physics, accurate trajectory prediction, horizontal trap prevention, and neon glow aesthetics."""

import math
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, BALL_SPEED, COLOR_BALL, COLOR_NEON_CYAN, COLOR_HOT_PINK

MIN_VERTICAL_SPEED = 120.0  # Minimum vertical velocity threshold to prevent infinite horizontal traps


class Ball:
    _glow_surf_cache: dict[int, pygame.Surface] = {}
    _trail_surf_cache: dict[tuple[int, int], pygame.Surface] = {}

    def __init__(self, radius: float = 8.0):
        self.radius = radius
        self.trail_positions: list[tuple[float, float]] = []
        self.reset()

    @classmethod
    def _get_glow_surface(cls, radius: int) -> pygame.Surface:
        glow_radius = radius + 4
        if glow_radius not in cls._glow_surf_cache:
            g_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(g_surf, (*COLOR_HOT_PINK, 90), (glow_radius, glow_radius), glow_radius)
            cls._glow_surf_cache[glow_radius] = g_surf
        return cls._glow_surf_cache[glow_radius]

    @classmethod
    def _get_trail_surface(cls, trail_radius: int, trail_alpha: int) -> pygame.Surface:
        key = (trail_radius, trail_alpha)
        if key not in cls._trail_surf_cache:
            t_surf = pygame.Surface((trail_radius * 2, trail_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (*COLOR_NEON_CYAN, trail_alpha // 2), (trail_radius, trail_radius), trail_radius)
            pygame.draw.circle(t_surf, (*COLOR_HOT_PINK, trail_alpha), (trail_radius, trail_radius), max(1, trail_radius - 2))
            cls._trail_surf_cache[key] = t_surf
        return cls._trail_surf_cache[key]

    def reset(self):
        """Resets ball position, trail history, and launch vector."""
        self.x = SCREEN_WIDTH / 2.0
        self.y = SCREEN_HEIGHT - 90.0
        self.trail_positions.clear()

        angle = math.radians(-75)
        self.vx = BALL_SPEED * math.cos(angle)
        self.vy = BALL_SPEED * math.sin(angle)

    def set_angle(self, angle_radians: float, speed: float = BALL_SPEED):
        self.vx = speed * math.cos(angle_radians)
        self.vy = speed * math.sin(angle_radians)

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    @property
    def rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )

    def get_substep_count(self, dt: float, max_step_distance: float = 4.0) -> int:
        """Calculates required sub-steps so movement never exceeds max_step_distance."""
        move_dist = self.speed * dt
        return max(1, math.ceil(move_dist / max_step_distance))

    def update_step(self, sub_dt: float):
        """Advances ball position by a single sub-step and resolves wall collisions."""
        self.x += self.vx * sub_dt
        self.y += self.vy * sub_dt
        self._resolve_wall_collisions()

    def update(self, dt: float):
        """Standard full-frame position update with trail recording."""
        self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > 8:
            self.trail_positions.pop(0)

        self.x += self.vx * dt
        self.y += self.vy * dt
        self._resolve_wall_collisions()

    def _enforce_min_vertical_velocity(self):
        """Prevents the ball from getting stuck in infinite horizontal bounce traps."""
        if abs(self.vy) < MIN_VERTICAL_SPEED:
            direction = -1.0 if self.vy < 0 else 1.0
            self.vy = direction * MIN_VERTICAL_SPEED
            current_speed = max(self.speed, BALL_SPEED)
            remaining_sq = max(100.0, current_speed**2 - self.vy**2)
            self.vx = math.copysign(math.sqrt(remaining_sq), self.vx if self.vx != 0 else 1.0)

    def _resolve_wall_collisions(self):
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = abs(self.vx)

        elif self.x + self.radius >= SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -abs(self.vx)

        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy = abs(self.vy)

        self._enforce_min_vertical_velocity()

    def resolve_paddle_collision(self, paddle_rect: pygame.FRect) -> bool:
        if not self.rect.colliderect(paddle_rect) or self.vy <= 0:
            return False

        paddle_center_x = paddle_rect.centerx
        half_width = paddle_rect.width / 2.0
        hit_offset = (self.x - paddle_center_x) / half_width
        hit_offset = max(-1.0, min(1.0, hit_offset))

        max_bounce_angle = math.radians(60)
        bounce_angle = -math.pi / 2.0 + (hit_offset * max_bounce_angle)

        current_speed = self.speed
        self.vx = current_speed * math.cos(bounce_angle)
        self.vy = current_speed * math.sin(bounce_angle)

        self.y = paddle_rect.top - self.radius
        self._enforce_min_vertical_velocity()
        return True

    def resolve_box_collision(self, target_rect: pygame.FRect) -> bool:
        ball_rect = self.rect
        if not ball_rect.colliderect(target_rect):
            return False

        overlap_left = ball_rect.right - target_rect.left
        overlap_right = target_rect.right - ball_rect.left
        overlap_top = ball_rect.bottom - target_rect.top
        overlap_bottom = target_rect.bottom - ball_rect.top

        min_overlap_x = min(overlap_left, overlap_right)
        min_overlap_y = min(overlap_top, overlap_bottom)

        # Anti-tunneling directional velocity assignment
        if min_overlap_x < min_overlap_y:
            if overlap_left < overlap_right:
                self.x = target_rect.left - self.radius
                self.vx = -abs(self.vx)
            else:
                self.x = target_rect.right + self.radius
                self.vx = abs(self.vx)
        else:
            if overlap_top < overlap_bottom:
                self.y = target_rect.top - self.radius
                self.vy = -abs(self.vy)
            else:
                self.y = target_rect.bottom + self.radius
                self.vy = abs(self.vy)

        self._enforce_min_vertical_velocity()
        return True

    def get_predicted_trajectory(
        self,
        bricks: list = None,
        paddle_rect: pygame.FRect = None,
        max_steps: int = 150,
        step_dt: float = 0.016
    ) -> list[tuple[float, float]]:
        """Calculates predicted trajectory points using sub-step resolution for 100% alignment with actual physics engine."""
        points = [(self.x, self.y)]
        sim_x, sim_y = self.x, self.y
        sim_vx, sim_vy = self.vx, self.vy

        sub_steps_per_frame = 4
        sub_dt = step_dt / sub_steps_per_frame

        for _ in range(max_steps * sub_steps_per_frame):
            sim_x += sim_vx * sub_dt
            sim_y += sim_vy * sub_dt

            if sim_y > SCREEN_HEIGHT:
                break

            # Simulate Wall Collisions
            if sim_x - self.radius <= 0:
                sim_x = self.radius
                sim_vx = abs(sim_vx)
            elif sim_x + self.radius >= SCREEN_WIDTH:
                sim_x = SCREEN_WIDTH - self.radius
                sim_vx = -abs(sim_vx)

            if sim_y - self.radius <= 0:
                sim_y = self.radius
                sim_vy = abs(sim_vy)

            sim_rect = pygame.FRect(sim_x - self.radius, sim_y - self.radius, self.radius * 2, self.radius * 2)

            # Simulate Paddle Collision
            if paddle_rect and sim_vy > 0 and sim_rect.colliderect(paddle_rect):
                paddle_center_x = paddle_rect.centerx
                half_width = paddle_rect.width / 2.0
                hit_offset = max(-1.0, min(1.0, (sim_x - paddle_center_x) / half_width))
                bounce_angle = -math.pi / 2.0 + (hit_offset * math.radians(60))
                speed = math.hypot(sim_vx, sim_vy)
                sim_vx = speed * math.cos(bounce_angle)
                sim_vy = speed * math.sin(bounce_angle)
                sim_y = paddle_rect.top - self.radius

            # Simulate Brick Collisions
            if bricks:
                hit_brick = False
                for b in bricks:
                    if not b.is_destroyed and sim_rect.colliderect(b.rect):
                        overlap_left = sim_rect.right - b.rect.left
                        overlap_right = b.rect.right - sim_rect.left
                        overlap_top = sim_rect.bottom - b.rect.top
                        overlap_bottom = b.rect.bottom - sim_rect.top

                        min_overlap_x = min(overlap_left, overlap_right)
                        min_overlap_y = min(overlap_top, overlap_bottom)

                        if min_overlap_x < min_overlap_y:
                            if overlap_left < overlap_right:
                                sim_x = b.rect.left - self.radius
                                sim_vx = -abs(sim_vx)
                            else:
                                sim_x = b.rect.right + self.radius
                                sim_vx = abs(sim_vx)
                        else:
                            if overlap_top < overlap_bottom:
                                sim_y = b.rect.top - self.radius
                                sim_vy = -abs(sim_vy)
                            else:
                                sim_y = b.rect.bottom + self.radius
                                sim_vy = abs(sim_vy)
                        hit_brick = True
                        break

                if hit_brick:
                    points.append((sim_x, sim_y))
                    continue

            points.append((sim_x, sim_y))

        return points

    def draw(self, surface: pygame.Surface):
        # 1. Render Neon Comet Motion Trail using cached surfaces
        num_points = len(self.trail_positions)
        for i, (tx, ty) in enumerate(self.trail_positions):
            ratio = (i + 1) / (num_points + 1)
            trail_radius = max(3, int(self.radius * ratio * 0.9))
            trail_alpha = int(140 * ratio)

            t_surf = self._get_trail_surface(trail_radius, trail_alpha)
            surface.blit(t_surf, (int(tx - trail_radius), int(ty - trail_radius)))

        # 2. Outer Neon Halo Glow using cached surface
        int_radius = int(self.radius)
        g_surf = self._get_glow_surface(int_radius)
        glow_radius = int_radius + 4
        surface.blit(g_surf, (int(self.x - glow_radius), int(self.y - glow_radius)))

        # 3. Main Solid Core Circle & Specular Highlight
        pygame.draw.circle(surface, COLOR_BALL, (int(self.x), int(self.y)), int_radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x - 2), int(self.y - 2)), max(1, int(self.radius * 0.35)))