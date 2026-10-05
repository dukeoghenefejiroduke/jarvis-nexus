"""SQLite-backed persistent task management store for JARVIS Nexus."""

import sqlite3
import os
from typing import Any, Dict, List, Optional


VALID_STATUSES = {"pending", "in_progress", "completed", "cancelled"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}


class TaskStore:
    """Manages structured persistent tasks using SQLite with validation and search."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            os.makedirs("data", exist_ok=True)
            db_path = "data/jarvis_tasks.db"
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the tasks table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT DEFAULT '',
                        status TEXT DEFAULT 'pending',
                        priority TEXT DEFAULT 'medium',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        due_at TEXT DEFAULT NULL,
                        completed_at TIMESTAMP DEFAULT NULL
                    )
                    """
                )
                conn.commit()
        except Exception as e:
            print(f"Error initializing task database: {e}")

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: Optional[str] = "medium",
        status: Optional[str] = "pending",
        due_at: Optional[str] = None
    ) -> int:
        """Create a new task and return its task ID."""
        status = status or "pending"
        priority = priority or "medium"
        status_lower = status.lower()
        priority_lower = priority.lower()

        if status_lower not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_STATUSES}")
        if priority_lower not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{priority}'. Must be one of {VALID_PRIORITIES}")

        completed_at_val = None
        if status_lower == "completed":
            import datetime
            completed_at_val = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO tasks (title, description, status, priority, due_at, completed_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (title, description, status_lower, priority_lower, due_at, completed_at_val)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error creating task: {e}")
            return -1

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific task by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT id, title, description, status, priority, created_at, updated_at, due_at, completed_at FROM tasks WHERE id = ?",
                    (task_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error retrieving task #{task_id}: {e}")
            return None

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_at: Optional[str] = None
    ) -> bool:
        """Update an existing task."""
        existing = self.get_task(task_id)
        if not existing:
            return False

        new_title = title if title is not None else existing["title"]
        new_desc = description if description is not None else existing["description"]
        new_status = (status or existing["status"]).lower()
        new_priority = (priority or existing["priority"]).lower()
        new_due = due_at if due_at is not None else existing["due_at"]

        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_STATUSES}")
        if new_priority not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{priority}'. Must be one of {VALID_PRIORITIES}")

        completed_at_val = existing["completed_at"]
        if new_status == "completed" and existing["status"] != "completed":
            import datetime
            completed_at_val = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif new_status != "completed":
            completed_at_val = None

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE tasks
                    SET title = ?, description = ?, status = ?, priority = ?, due_at = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (new_title, new_desc, new_status, new_priority, new_due, completed_at_val, task_id)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error updating task #{task_id}: {e}")
            return False

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed."""
        return self.update_task(task_id, status="completed")

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting task #{task_id}: {e}")
            return False

    def list_tasks(self, status: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tasks, optionally filtered by status and/or priority."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                query = "SELECT id, title, description, status, priority, created_at, updated_at, due_at, completed_at FROM tasks WHERE 1=1"
                params = []

                if status:
                    query += " AND status = ?"
                    params.append(status.lower())
                if priority:
                    query += " AND priority = ?"
                    params.append(priority.lower())

                query += " ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, created_at DESC"

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error listing tasks: {e}")
            return []

    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Search tasks by title or description matching query substring."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                like_pattern = f"%{query}%"
                cursor = conn.execute(
                    """
                    SELECT id, title, description, status, priority, created_at, updated_at, due_at, completed_at
                    FROM tasks
                    WHERE title LIKE ? OR description LIKE ?
                    ORDER BY created_at DESC
                    """,
                    (like_pattern, like_pattern)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error searching tasks for '{query}': {e}")
            return []
