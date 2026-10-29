"""Automated unit tests for SoundManager volume controls, mute states, and audio fallback safety."""

import os
import unittest

# Run Pygame in headless mode without requiring a physical audio output device
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
pygame.init()

from src.sounds import SoundManager


class TestSoundManager(unittest.TestCase):
    def setUp(self):
        self.sounds = SoundManager()

    def test_volume_clamping(self):
        """Verifies that master volume clamps strictly between 0.0 and 1.0."""
        self.sounds.set_volume(1.5)
        self.assertEqual(self.sounds.volume, 1.0, "Volume above 1.0 should clamp to 1.0.")

        self.sounds.set_volume(-0.5)
        self.assertEqual(self.sounds.volume, 0.0, "Volume below 0.0 should clamp to 0.0.")

        self.sounds.set_volume(0.65)
        self.assertAlmostEqual(self.sounds.volume, 0.65, places=2, msg="Valid volume should set directly.")

    def test_mute_toggle_behavior(self):
        """Verifies state inversion when toggling mute."""
        initial_mute_state = self.sounds.muted

        self.sounds.toggle_mute()
        self.assertEqual(self.sounds.muted, not initial_mute_state, "Toggling mute should flip boolean state.")

        self.sounds.toggle_mute()
        self.assertEqual(self.sounds.muted, initial_mute_state, "Toggling mute twice should restore original state.")

    def test_safe_execution_when_disabled_or_headless(self):
        """Ensures playing sound keys never raises unhandled exceptions when mixer is unavailable."""
        self.sounds.enabled = False

        try:
            self.sounds.play("brick")
            self.sounds.play("paddle")
            self.sounds.play("non_existent_sound_key")
        except Exception as e:
            self.fail(f"SoundManager.play() raised an unexpected exception when sound was disabled: {e}")


if __name__ == "__main__":
    unittest.main()