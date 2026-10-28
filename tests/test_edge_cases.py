"""Automated unit tests for engine edge cases, zero-delta time safety, and boundary clamping."""

import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
pygame.init()

from src.paddle import Paddle
from src.config import SCREEN_WIDTH


class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.paddle = Paddle()

    def test_zero_delta_time_safety(self):
        """Verifies that zero dt does not alter positions or trigger division errors."""
        initial_x = self.paddle.x
        self.paddle.wide_timer = 5.0
        self.paddle.update(0.0)

        self.assertEqual(self.paddle.x, initial_x, "Paddle position must not change with 0 dt.")
        self.assertEqual(self.paddle.wide_timer, 5.0, "Timers must remain unchanged with 0 dt.")

    def test_wide_paddle_expansion_boundary_clamping(self):
        """Verifies that expanding paddle width near the right edge clamps within screen bounds."""
        # Position paddle near right boundary
        self.paddle.x = SCREEN_WIDTH - self.paddle.base_width
        self.paddle.apply_wide_paddle(10.0)

        self.assertLessEqual(
            self.paddle.x + self.paddle.width,
            SCREEN_WIDTH,
            "Expanded paddle right edge must not exceed SCREEN_WIDTH."
        )

    def test_reapplying_active_powerup_resets_timer_safely(self):
        """Verifies that picking up wide paddle twice re-applies duration without distorting width."""
        self.paddle.apply_wide_paddle(10.0)
        self.assertEqual(self.paddle.width, 180.0)

        # Re-apply power-up
        self.paddle.apply_wide_paddle(10.0)
        self.assertEqual(self.paddle.width, 180.0, "Paddle width must remain 180.0 upon re-application.")
        self.assertEqual(self.paddle.wide_timer, 10.0, "Timer should reset to full duration.")


if __name__ == "__main__":
    unittest.main()