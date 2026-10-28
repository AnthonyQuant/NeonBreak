"""SQLite database engine with batched stat updates."""

import os
import sqlite3
from src.config import DATA_DIR


class DatabaseManager:
    def __init__(self, db_filename: str = "records.db"):
        self.db_path = os.path.join(DATA_DIR, db_filename)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS high_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mode TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    level_reached INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    stat_name TEXT PRIMARY KEY,
                    stat_value INTEGER NOT NULL
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO stats (stat_name, stat_value) VALUES ('bricks_destroyed', 0)")
            conn.commit()

    def save_score(self, mode: str, score: int, level_reached: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO high_scores (mode, score, level_reached) VALUES (?, ?, ?)",
                (mode, score, level_reached)
            )
            conn.commit()

    def add_bricks_destroyed(self, count: int):
        """Batch update bricks destroyed in a single transaction."""
        if count <= 0:
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE stats SET stat_value = stat_value + ? WHERE stat_name = 'bricks_destroyed'",
                (count,)
            )
            conn.commit()

    def get_top_scores(self, mode: str, limit: int = 5) -> list[tuple[int, int, str]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT score, level_reached, strftime('%Y-%m-%d', timestamp) 
                FROM high_scores 
                WHERE mode = ? 
                ORDER BY score DESC 
                LIMIT ?
                """,
                (mode, limit)
            )
            return cursor.fetchall()

    def get_bricks_destroyed(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stat_value FROM stats WHERE stat_name = 'bricks_destroyed'")
            row = cursor.fetchone()
            return row[0] if row else 0