import sqlite3
from typing import Optional


class ForwardService:
    """SQLite-backed storage for message forwards and access control."""

    def __init__(self, db_path: str = "support.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def close(self) -> None:
        """Close the underlying database connection."""
        self.conn.close()

    # Context manager support -------------------------------------------------
    def __enter__(self) -> "ForwardService":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - simple
        self.close()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS forwards (
                admin_id INTEGER,
                forwarded_message_id INTEGER,
                user_chat_id INTEGER,
                PRIMARY KEY (admin_id, forwarded_message_id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS allowed_users (
                user_id INTEGER PRIMARY KEY
            )
            """
        )
        self.conn.commit()

    def record_forward(self, admin_id: int, forwarded_message_id: int, user_chat_id: int) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO forwards(admin_id, forwarded_message_id, user_chat_id) VALUES (?, ?, ?)",
            (admin_id, forwarded_message_id, user_chat_id),
        )
        self.conn.commit()

    def get_user_chat_id(self, admin_id: int, forwarded_message_id: int) -> Optional[int]:
        cur = self.conn.execute(
            "SELECT user_chat_id FROM forwards WHERE admin_id=? AND forwarded_message_id=?",
            (admin_id, forwarded_message_id),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def add_allowed_user(self, user_id: int) -> None:
        self.conn.execute("INSERT OR IGNORE INTO allowed_users(user_id) VALUES (?)", (user_id,))
        self.conn.commit()

    def remove_allowed_user(self, user_id: int) -> None:
        """Remove a user from the allowed users list."""
        self.conn.execute("DELETE FROM allowed_users WHERE user_id=?", (user_id,))
        self.conn.commit()

    def get_allowed_users(self) -> list[int]:
        """Return a list of all allowed user IDs."""
        cur = self.conn.execute("SELECT user_id FROM allowed_users")
        return [row[0] for row in cur.fetchall()]

    def is_allowed(self, user_id: int) -> bool:
        cur_total = self.conn.execute("SELECT COUNT(*) FROM allowed_users")
        total = cur_total.fetchone()[0]
        if total == 0:
            return True
        cur = self.conn.execute("SELECT 1 FROM allowed_users WHERE user_id=?", (user_id,))
        return cur.fetchone() is not None
