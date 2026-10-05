"""SQLite-backed persistent memory management for JARVIS Nexus."""

import sqlite3
import os
from typing import Any, Dict, List, Optional


class MemoryStore:
    """Manages structured persistent local memory using SQLite with categories and lifecycle timestamps."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            os.makedirs("data", exist_ok=True)
            db_path = "data/jarvis_memory.db"
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the memories table and handle schema migrations."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        category TEXT DEFAULT 'general',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor = conn.execute("PRAGMA table_info(memories)")
                columns = [row["name"] for row in cursor.fetchall()]
                if "created_at" not in columns:
                    conn.execute("ALTER TABLE memories ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                conn.commit()
        except Exception as e:
            print(f"Error initializing memory database: {e}")

    def save_memory(self, key: str, value: str, category: str = "general") -> bool:
        """Save or upsert a memory item, preventing duplicates for the same key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO memories (key, value, category, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        category = excluded.category,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (key, value, category),
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error saving memory '{key}': {e}")
            return False

    def get_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a structured memory record by key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT id, key, value, category, created_at, updated_at FROM memories WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error retrieving memory '{key}': {e}")
            return None

    def update_memory(self, key: str, value: Optional[str] = None, category: Optional[str] = None) -> bool:
        """Update an existing memory key's value and/or category."""
        try:
            existing = self.get_memory(key)
            if not existing:
                return False
            
            new_value = value if value is not None else existing["value"]
            new_category = category if category is not None else existing["category"]

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE memories
                    SET value = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE key = ?
                    """,
                    (new_value, new_category, key)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error updating memory '{key}': {e}")
            return False

    def delete_memory(self, key: str) -> bool:
        """Delete a memory item by key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting memory '{key}': {e}")
            return False

    def search_memory(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search memories by key or value matching query substring, optionally filtered by category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                like_pattern = f"%{query}%"
                if category:
                    cursor = conn.execute(
                        """
                        SELECT id, key, value, category, created_at, updated_at
                        FROM memories
                        WHERE (key LIKE ? OR value LIKE ?) AND category = ?
                        ORDER BY updated_at DESC
                        """,
                        (like_pattern, like_pattern, category),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT id, key, value, category, created_at, updated_at
                        FROM memories
                        WHERE key LIKE ? OR value LIKE ?
                        ORDER BY updated_at DESC
                        """,
                        (like_pattern, like_pattern),
                    )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error searching memory for '{query}': {e}")
            return []

    def list_memories(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all stored memories, optionally filtered by category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if category:
                    cursor = conn.execute(
                        "SELECT id, key, value, category, created_at, updated_at FROM memories WHERE category = ? ORDER BY updated_at DESC",
                        (category,)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT id, key, value, category, created_at, updated_at FROM memories ORDER BY updated_at DESC"
                    )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error listing memories: {e}")
            return []
