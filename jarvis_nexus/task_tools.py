"""Tool registrations for persistent task management in JARVIS Nexus."""

from typing import Any, Dict, List, Optional
from jarvis_nexus.tasks import TaskStore


def register_task_tools(tool_registry: Any, task_store: Optional[TaskStore] = None) -> None:
    """Register task management tools into the ToolRegistry."""
    ts = task_store or TaskStore()

    def create_task(title: str, description: str = "", priority: str = "medium", due_at: Optional[str] = None) -> Dict[str, Any]:
        """Create a new persistent task."""
        try:
            task_id = ts.create_task(title, description, priority, due_at)
            if task_id > 0:
                return {"status": "success", "task_id": task_id, "message": f"Created task #{task_id}: {title}"}
            return {"status": "error", "message": "Failed to create task."}
        except ValueError as ve:
            return {"status": "error", "message": str(ve)}

    tool_registry.register(
        name="create_task",
        description="Create a new persistent task with title, description, priority (low, medium, high, critical), and optional due date.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title of the task."},
                "description": {"type": "string", "description": "Optional description."},
                "priority": {"type": "string", "description": "Priority level ('low', 'medium', 'high', 'critical')."},
                "due_at": {"type": "string", "description": "Optional due date."}
            },
            "required": ["title"]
        },
        func=create_task
    )

    def get_task(task_id: int) -> Dict[str, Any]:
        """Retrieve a task by ID."""
        task = ts.get_task(task_id)
        if task:
            return {"status": "found", "task": task}
        return {"status": "not_found", "message": f"Task #{task_id} not found."}

    tool_registry.register(
        name="get_task",
        description="Retrieve a specific task by ID.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task."}
            },
            "required": ["task_id"]
        },
        func=get_task
    )

    def update_task(
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing task."""
        try:
            success = ts.update_task(task_id, title, description, status, priority, due_at)
            if success:
                return {"status": "success", "message": f"Successfully updated task #{task_id}."}
            return {"status": "error", "message": f"Task #{task_id} not found or update failed."}
        except ValueError as ve:
            return {"status": "error", "message": str(ve)}

    tool_registry.register(
        name="update_task",
        description="Update an existing task's title, description, status ('pending', 'in_progress', 'completed', 'cancelled'), priority, or due date.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to update."},
                "title": {"type": "string", "description": "New title (optional)."},
                "description": {"type": "string", "description": "New description (optional)."},
                "status": {"type": "string", "description": "New status (optional)."},
                "priority": {"type": "string", "description": "New priority (optional)."},
                "due_at": {"type": "string", "description": "New due date (optional)."}
            },
            "required": ["task_id"]
        },
        func=update_task
    )

    def complete_task(task_id: int) -> Dict[str, Any]:
        """Mark a task as completed."""
        success = ts.complete_task(task_id)
        if success:
            return {"status": "success", "message": f"Task #{task_id} is now completed."}
        return {"status": "error", "message": f"Task #{task_id} not found."}

    tool_registry.register(
        name="complete_task",
        description="Mark a task as completed by ID.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to complete."}
            },
            "required": ["task_id"]
        },
        func=complete_task
    )

    def delete_task(task_id: int) -> Dict[str, Any]:
        """Delete a task by ID."""
        success = ts.delete_task(task_id)
        if success:
            return {"status": "success", "message": f"Successfully deleted task #{task_id}."}
        return {"status": "error", "message": f"Task #{task_id} not found."}

    tool_registry.register(
        name="delete_task",
        description="Delete a task by ID.",
        parameters={
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to delete."}
            },
            "required": ["task_id"]
        },
        func=delete_task
    )

    def list_tasks(status: Optional[str] = None, priority: Optional[str] = None) -> Dict[str, Any]:
        """List tasks, optionally filtered by status and/or priority."""
        tasks = ts.list_tasks(status, priority)
        return {"status_filter": status, "priority_filter": priority, "tasks": tasks, "count": len(tasks)}

    tool_registry.register(
        name="list_tasks",
        description="List tasks, optionally filtered by status ('pending', 'in_progress', 'completed', 'cancelled') and/or priority.",
        parameters={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional status filter."},
                "priority": {"type": "string", "description": "Optional priority filter."}
            },
            "required": []
        },
        func=list_tasks
    )

    def search_tasks(query: str) -> Dict[str, Any]:
        """Search tasks by keyword."""
        tasks = ts.search_tasks(query)
        return {"query": query, "tasks": tasks, "count": len(tasks)}

    tool_registry.register(
        name="search_tasks",
        description="Search persistent tasks by query string in title or description.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword or phrase."}
            },
            "required": ["query"]
        },
        func=search_tasks
    )
