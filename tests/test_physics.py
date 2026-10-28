"""Automated unit tests for core physics, wall reflections, and anti-tunneling collision logic."""

import os
import unittest

# Run Pygame in headless mode without opening a GUI window during test execution
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
pygame.init()

from src.ball import Ball
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT


class TestBallPhysics(unittest.TestCase):
    def setUp(self):
        self.ball = Ball()

    def test_vertical_wall_collision_reverses_horizontal_velocity(self):
        """Verifies that striking a left or right vertical wall flips horizontal velocity (vx)."""
        # Test left wall collision
        self.ball.x = self.ball.radius
        self.ball.vx = -400.0
        self.ball._resolve_wall_collisions()
        self.assertGreater(self.ball.vx, 0, "Horizontal velocity must reverse when hitting the left wall.")

        # Test right wall collision
        self.ball.x = SCREEN_WIDTH - self.ball.radius
        self.ball.vx = 400.0
        self.ball._resolve_wall_collisions()
        self.assertLess(self.ball.vx, 0, "Horizontal velocity must reverse when hitting the right wall.")

    def test_horizontal_surface_collision_reverses_vertical_velocity(self):
        """Verifies that striking the top surface flips vertical velocity (vy)."""
        self.ball.y = self.ball.radius
        self.ball.vy = -400.0
        self.ball._resolve_wall_collisions()
        self.assertGreater(self.ball.vy, 0, "Vertical velocity must reverse when hitting the top surface.")

    def test_box_collision_resolution(self):
        """Verifies directional velocity reversal upon colliding with a target rectangle."""
        target_rect = pygame.FRect(200.0, 200.0, 80.0, 24.0)

        # Approach box from below moving upward
        self.ball.x = 240.0
        self.ball.y = target_rect.bottom + 2.0
        self.ball.vx = 0.0
        self.ball.vy = -300.0

        hit = self.ball.resolve_box_collision(target_rect)
        self.assertTrue(hit, "Collision should register when ball overlaps box.")
        self.assertGreater(self.ball.vy, 0, "Vertical velocity must reverse when striking the bottom of a box.")

    def test_high_speed_substepping_anti_tunneling(self):
        """Verifies that high velocity generates sufficient sub-steps to prevent passing through bricks."""
        dt = 0.016  # 60 FPS frame time
        self.ball.vx = 2000.0
        self.ball.vy = 2000.0

        substeps = self.ball.get_substep_count(dt, max_step_distance=4.0)
        max_dist_per_step = (self.ball.speed * dt) / substeps

        self.assertGreater(substeps, 1, "High-speed movement must require multiple sub-steps.")
        self.assertLessEqual(max_dist_per_step, 4.0, "Distance per sub-step must not exceed max_step_distance.")


if __name__ == "__main__":
    unittest.main()