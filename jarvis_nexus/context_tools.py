"""Tool registrations for Advanced Context and Memory Intelligence in JARVIS Nexus."""

from typing import Any, Dict, List, Optional
from jarvis_nexus.context import ContextManager


def register_context_tools(
    tool_registry: Any,
    context_manager: Optional[ContextManager] = None
) -> None:
    """Register context intelligence tools into the ToolRegistry."""
    cm = context_manager or ContextManager()

    def get_project_context(query: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated project context combining memory, tasks, files, and skills."""
        return cm.get_project_context(query)

    tool_registry.register(
        name="get_project_context",
        description="Retrieve aggregated project context (relevant memories, pending tasks, workspace files, and available skills).",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional search topic or query to rank context relevance."}
            },
            "required": []
        },
        func=get_project_context
    )
