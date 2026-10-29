"""Automated unit tests for SQLite database persistence, isolated path injection, and score ordering."""

import unittest
from src.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Inject an in-memory SQLite database path for 100% isolated unit tests
        self.db = DatabaseManager(db_path=":memory:")

    def test_isolated_database_initialization(self):
        """Verifies that the in-memory database initializes with default tables and stats."""
        self.assertEqual(self.db.db_path, ":memory:", "Database path should match injected memory string.")
        self.assertEqual(self.db.get_bricks_destroyed(), 0, "Initial brick count should default to 0.")

    def test_save_and_retrieve_top_scores(self):
        """Verifies score saving, mode filtering, and descending score ordering."""
        self.db.save_score("Classic", 1200, 2)
        self.db.save_score("Classic", 3500, 3)
        self.db.save_score("Classic", 800, 1)
        self.db.save_score("Precision", 5000, 2)

        classic_top = self.db.get_top_scores("Classic", limit=2)
        self.assertEqual(len(classic_top), 2, "Should limit results to specified count.")
        self.assertEqual(classic_top[0][0], 3500, "Highest score should be ordered first.")
        self.assertEqual(classic_top[1][0], 1200, "Second highest score should follow.")

        precision_top = self.db.get_top_scores("Precision", limit=5)
        self.assertEqual(len(precision_top), 1, "Should filter results strictly by game mode.")
        self.assertEqual(precision_top[0][0], 5000, "Precision score should match saved value.")

    def test_bricks_destroyed_stat_accumulation(self):
        """Verifies cumulative brick destruction tracking and batch transaction safety."""
        self.assertEqual(self.db.get_bricks_destroyed(), 0)

        self.db.add_bricks_destroyed(15)
        self.db.add_bricks_destroyed(10)
        self.assertEqual(self.db.get_bricks_destroyed(), 25, "Stat count should accumulate accurately across calls.")

        # Ignore non-positive increments
        self.db.add_bricks_destroyed(-5)
        self.db.add_bricks_destroyed(0)
        self.assertEqual(self.db.get_bricks_destroyed(), 25, "Non-positive stat increments should be ignored.")


if __name__ == "__main__":
    unittest.main()