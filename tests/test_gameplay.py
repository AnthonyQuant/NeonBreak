"""Automated unit tests for gameplay lifecycle, brick durability, state transitions, and power-up expirations."""

import os
import unittest

# Run Pygame in headless mode without opening a GUI window
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
pygame.init()

from src.ball import Ball
from src.brick import Brick, BrickType
from src.game import Game
from src.states import GameState, GameMode


class TestGameplayLifecycle(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def test_armored_brick_durability_decay(self):
        """Verifies that an armored brick requires exactly two hits to be destroyed."""
        armored_brick = Brick(100.0, 100.0, brick_type=BrickType.ARMORED)
        self.assertEqual(armored_brick.hits_left, 2, "Armored brick should start with 2 hits left.")

        # First hit
        first_hit_destroyed = armored_brick.hit()
        self.assertFalse(first_hit_destroyed, "First hit should not destroy an armored brick.")
        self.assertEqual(armored_brick.hits_left, 1, "Hits remaining should decay to 1 after first hit.")
        self.assertFalse(armored_brick.is_destroyed, "Brick should remain active after first hit.")

        # Second hit
        second_hit_destroyed = armored_brick.hit()
        self.assertTrue(second_hit_destroyed, "Second hit should destroy an armored brick.")
        self.assertEqual(armored_brick.hits_left, 0, "Hits remaining should reach 0.")
        self.assertTrue(armored_brick.is_destroyed, "Brick should be marked as destroyed after second hit.")

    def test_life_loss_on_ball_out_of_bounds(self):
        """Verifies that losing all balls reduces total lives by exactly one."""
        self.game.select_mode_and_start(GameMode.CLASSIC)
        initial_lives = self.game.lives  # Should be 3
        self.assertEqual(initial_lives, 3)

        self.game.state = GameState.PLAYING
        self.game.balls[0].y = 800.0  # Move ball below lower boundary (SCREEN_HEIGHT = 700)

        self.game._update(0.016)
        self.assertEqual(self.game.lives, initial_lives - 1, "Exactly one life must be lost when ball falls below paddle.")

    def test_pause_state_freezes_gameplay_updates(self):
        """Verifies that moving objects do not update position when the game is paused."""
        self.game.state = GameState.PAUSED
        self.game.balls = []
        self.game.paddle.x = 400.0

        initial_paddle_x = self.game.paddle.x
        self.game._update(0.016)

        self.assertEqual(self.game.paddle.x, initial_paddle_x, "Paddle position must remain frozen while paused.")

    def test_slow_motion_powerup_expiration(self):
        """Verifies that the slow-motion power-up timer decays and restores standard speed upon expiration."""
        self.game.state = GameState.PLAYING
        self.game.balls = [Ball()]  # Active ball prevents reset_round() trigger
        self.game.bricks = [Brick(100.0, 100.0, brick_type=BrickType.STANDARD)]  # Active brick prevents LEVEL_CLEAR trigger
        self.game.slow_motion_timer = 0.05

        # First update step (0.05 - 0.03 = 0.02)
        self.game._update(0.03)
        self.assertAlmostEqual(self.game.slow_motion_timer, 0.02, places=2, msg="Slow motion timer should decay by dt.")

        # Second update step to fully expire timer (0.02 - 0.03 = -0.01)
        self.game._update(0.03)
        self.assertLessEqual(self.game.slow_motion_timer, 0.0, "Timer should reach 0 or below after duration expires.")

    def test_level_clear_trigger(self):
        """Verifies that destroying the final breakable brick transitions state to LEVEL_CLEAR."""
        self.game.state = GameState.PLAYING
        self.game.balls = [Ball()]  # Active ball required to prevent out-of-bounds trigger
        self.game.bricks = [Brick(100.0, 100.0, brick_type=BrickType.STANDARD)]

        self.game.bricks[0].hit()  # Destroy the only breakable brick
        self.game._update(0.016)

        self.assertEqual(self.game.state, GameState.LEVEL_CLEAR, "Game state must transition to LEVEL_CLEAR when all breakable bricks are destroyed.")

    def test_game_restart_resets_state_correctly(self):
        """Verifies that resetting the game clears score, restores lives, and resets combo streak."""
        self.game.score = 5000
        self.game.combo_streak = 4
        self.game.reset_game()

        self.assertEqual(self.game.score, 0, "Score must reset to 0.")
        self.assertEqual(self.game.combo_streak, 0, "Combo streak must reset to 0.")
        self.assertEqual(self.game.lives, 3, "Lives must reset to mode default (3 for Classic).")


if __name__ == "__main__":
    unittest.main()