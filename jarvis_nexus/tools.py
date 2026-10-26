"""Tool registry and secure tool implementations for JARVIS Nexus."""

import datetime
import math
import ast
import operator
from typing import Any, Callable, Dict, List, Optional
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.models import ToolDefinition
from jarvis_nexus.security import is_public_demo
from jarvis_nexus.file_tools import register_file_tools
from jarvis_nexus.skill_tools import register_skill_tools
from jarvis_nexus.task_tools import register_task_tools
from jarvis_nexus.context_tools import register_context_tools
from jarvis_nexus.qloo_tools import register_qloo_tools


class ToolRegistry:
    """Registry and execution engine for JARVIS Nexus tools."""

    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        task_store: Optional[TaskStore] = None,
        context_manager: Optional[Any] = None
    ) -> None:
        self.memory_store = memory_store or MemoryStore()
        self.task_store = task_store or TaskStore()
        self.context_manager = context_manager
        self.tools: Dict[str, Callable[..., Any]] = {}
        self.definitions: List[ToolDefinition] = []
        self._register_default_tools()

    def register(self, name: str, description: str, parameters: Dict[str, Any], func: Callable[..., Any]) -> None:
        """Register a tool function along with its schema definition."""
        self.tools[name] = func
        self.definitions.append(
            ToolDefinition(
                name=name,
                description=description,
                parameters=parameters
            )
        )

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a registered tool by name with given arguments safely."""
        if is_public_demo():
            restricted_tools = {
                "create_task", "update_task", "complete_task", "delete_task",
                "save_memory", "update_memory", "delete_memory"
            }
            if name in restricted_tools:
                return {"error": f"Tool '{name}' is disabled in Public Demo mode."}
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found."}
        try:
            func = self.tools[name]
            return func(**arguments)
        except Exception as e:
            return {"error": f"Error executing tool '{name}': {str(e)}"}

    def get_definitions(self) -> List[ToolDefinition]:
        """Return tool definitions for model function calling."""
        return self.definitions

    def _register_default_tools(self) -> None:
        """Register mandatory tools, memory tools, file intelligence, skill tools, task tools, and context tools."""
        
        # 1. get_current_time
        def get_current_time() -> Dict[str, str]:
            """Get current UTC time and formatted local time string."""
            now = datetime.datetime.now()
            return {
                "iso": now.isoformat(),
                "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": str(datetime.datetime.now().astimezone().tzinfo)
            }

        self.register(
            name="get_current_time",
            description="Get the current date and time.",
            parameters={"type": "object", "properties": {}, "required": []},
            func=get_current_time
        )

        # 2. calculator (Safe arithmetic evaluation)
        def calculator(expression: str) -> Dict[str, Any]:
            """Safely evaluate a mathematical arithmetic expression without arbitrary execution."""
            allowed_operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
            }

            def _eval_node(node: ast.AST) -> Any:
                if isinstance(node, ast.Constant):
                    if isinstance(node.value, (int, float)):
                        return node.value
                    raise ValueError(f"Unsupported constant type: {type(node.value)}")
                elif isinstance(node, ast.BinOp):
                    op_type = type(node.op)
                    if op_type in allowed_operators:
                        left = _eval_node(node.left)
                        right = _eval_node(node.right)
                        return allowed_operators[op_type](left, right)
                    raise ValueError(f"Unsupported operator: {op_type}")
                elif isinstance(node, ast.UnaryOp):
                    op_type = type(node.op)
                    if op_type in allowed_operators:
                        operand = _eval_node(node.operand)
                        return allowed_operators[op_type](operand)
                    raise ValueError(f"Unsupported unary operator: {op_type}")
                elif isinstance(node, ast.Expression):
                    return _eval_node(node.body)
                else:
                    raise ValueError(f"Unsupported expression structure: {type(node)}")

            try:
                expr_cleaned = expression.strip()
                parsed_ast = ast.parse(expr_cleaned, mode='eval')
                result = _eval_node(parsed_ast)
                return {"expression": expression, "result": result}
            except Exception as e:
                return {"expression": expression, "error": f"Invalid expression or calculation error: {str(e)}"}

        self.register(
            name="calculator",
            description="Perform safe mathematical calculations.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "The mathematical expression to evaluate, e.g. '2 + 2 * 4'"}
                },
                "required": ["expression"]
            },
            func=calculator
        )

        # 3. save_memory
        def save_memory(key: str, value: str, category: str = "general") -> Dict[str, Any]:
            """Save a structured memory item with category."""
            success = self.memory_store.save_memory(key, value, category)
            if success:
                return {"status": "success", "message": f"Successfully saved memory '{key}' under category '{category}'."}
            return {"status": "error", "message": f"Failed to save memory '{key}'."}

        self.register(
            name="save_memory",
            description="Save information to persistent local memory (categories: identity, preference, project, fact, task, general).",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Unique key for the memory."},
                    "value": {"type": "string", "description": "Information to remember."},
                    "category": {"type": "string", "description": "Category (identity, preference, project, fact, task, general)."}
                },
                "required": ["key", "value"]
            },
            func=save_memory
        )

        # 4. get_memory
        def get_memory(key: str) -> Dict[str, Any]:
            """Retrieve a specific memory by key."""
            record = self.memory_store.get_memory(key)
            if record:
                return {"status": "found", "memory": record}
            return {"status": "not_found", "message": f"Memory '{key}' not found."}

        self.register(
            name="get_memory",
            description="Retrieve a specific memory record by key.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key of the memory to retrieve."}
                },
                "required": ["key"]
            },
            func=get_memory
        )

        # 5. update_memory
        def update_memory(key: str, value: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
            """Update an existing memory."""
            success = self.memory_store.update_memory(key, value, category)
            if success:
                return {"status": "success", "message": f"Successfully updated memory '{key}'."}
            return {"status": "error", "message": f"Memory '{key}' not found or update failed."}

        self.register(
            name="update_memory",
            description="Update an existing memory key's value and/or category.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key of the memory to update."},
                    "value": {"type": "string", "description": "New value (optional)."},
                    "category": {"type": "string", "description": "New category (optional)."}
                },
                "required": ["key"]
            },
            func=update_memory
        )

        # 6. delete_memory
        def delete_memory(key: str) -> Dict[str, Any]:
            """Delete a memory by key."""
            success = self.memory_store.delete_memory(key)
            if success:
                return {"status": "success", "message": f"Successfully deleted memory '{key}'."}
            return {"status": "error", "message": f"Memory '{key}' not found."}

        self.register(
            name="delete_memory",
            description="Delete a memory item by key.",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key of the memory to delete."}
                },
                "required": ["key"]
            },
            func=delete_memory
        )

        # 7. search_memory
        def search_memory(query: str, category: Optional[str] = None) -> Dict[str, Any]:
            """Search memories by query string and optional category."""
            results = self.memory_store.search_memory(query, category)
            return {"query": query, "category": category, "results": results, "count": len(results)}

        self.register(
            name="search_memory",
            description="Search stored memories by query string and optional category.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query keyword or phrase."},
                    "category": {"type": "string", "description": "Optional category filter."}
                },
                "required": ["query"]
            },
            func=search_memory
        )

        # 8. list_memories
        def list_memories(category: Optional[str] = None) -> Dict[str, Any]:
            """List all stored memories, optionally filtered by category."""
            results = self.memory_store.list_memories(category)
            return {"category": category, "memories": results, "count": len(results)}

        self.register(
            name="list_memories",
            description="List all stored memories, optionally filtered by category.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Optional category filter."}
                },
                "required": []
            },
            func=list_memories
        )

        # 9. Register File Intelligence Tools
        register_file_tools(self)

        # 10. Register Skill Discovery Tools
        register_skill_tools(self)

        # 11. Register Task Management Tools
        register_task_tools(self, task_store=self.task_store)

        # 12. Register Context Intelligence Tools
        register_context_tools(self, context_manager=self.context_manager)

        # 13. Register Qloo Cultural Intelligence Tools
        register_qloo_tools(self)
