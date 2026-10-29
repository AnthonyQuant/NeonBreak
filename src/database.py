"""SQLite database engine with batched stat updates, OS user-writable AppData resolution, and flexible path dependency injection."""

import os
import sys
import sqlite3
from src.config import DATA_DIR


def get_user_data_dir(app_name: str = "NeonBreak") -> str:
    """Returns an OS-appropriate, user-writable directory for application data storage."""
    if sys.platform == "win32":
        base_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base_dir, app_name)
    elif sys.platform == "darwin":
        return os.path.expanduser(f"~/Library/Application Support/{app_name}")
    else:
        base_dir = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        return os.path.join(base_dir, app_name)


class DatabaseManager:
    def __init__(self, db_filename: str = "records.db", db_path: str | None = None):
        if db_path is not None:
            self.db_path = db_path
        else:
            # Use user-writable OS AppData directory for standalone build safety
            app_data_dir = get_user_data_dir()
            self.db_path = os.path.join(app_data_dir, db_filename)

        self._shared_conn: sqlite3.Connection | None = None
        if self.db_path == ":memory:" or self.db_path.startswith("file:"):
            self._shared_conn = sqlite3.connect(self.db_path, uri=self.db_path.startswith("file:"))

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        if self.db_path != ":memory:" and not self.db_path.startswith("file:"):
            dirname = os.path.dirname(self.db_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

        conn = self._get_connection()
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
        conn = self._get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO high_scores (mode, score, level_reached) VALUES (?, ?, ?)",
                (mode, score, level_reached)
            )

    def add_bricks_destroyed(self, count: int):
        """Batch update bricks destroyed in a single transaction."""
        if count <= 0:
            return
        conn = self._get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE stats SET stat_value = stat_value + ? WHERE stat_name = 'bricks_destroyed'",
                (count,)
            )

    def get_top_scores(self, mode: str, limit: int = 5) -> list[tuple[int, int, str]]:
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT stat_value FROM stats WHERE stat_name = 'bricks_destroyed'")
        row = cursor.fetchone()
        return row[0] if row else 0