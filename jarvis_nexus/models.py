"""Model provider abstraction and Mock model provider for model-driven agent architecture."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import re


@dataclass
class ChatMessage:
    """Structured chat message across conversation roles."""
    role: str  # 'system', 'user', 'assistant', 'tool'
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Any]] = field(default_factory=list)
    tool_call_id: Optional[str] = None


@dataclass
class ToolCall:
    """Represents a tool call requested by the model."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolDefinition:
    """Definition of a tool available for model function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class ModelResponse:
    """Structured response from a model provider."""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = field(default_factory=list)


class BaseModelProvider(ABC):
    """Abstract base class for model providers."""

    @abstractmethod
    def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: str,
        tools: Optional[List[ToolDefinition]] = None
    ) -> ModelResponse:
        """Generate a response given structured messages, system prompt, and available tools."""
        pass


class MockModelProvider(BaseModelProvider):
    """Model-driven offline mock provider simulating reasoning, task management, and tool decisions."""

    def __init__(self) -> None:
        pass

    def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: str,
        tools: Optional[List[ToolDefinition]] = None
    ) -> ModelResponse:
        """Simulate model reasoning: decide whether tool calls are needed or produce natural response."""
        if not messages:
            return ModelResponse(content="Hello! I am JARVIS Nexus (Offline Mode). How can I help you?", tool_calls=[])

        last_msg = messages[-1]

        # If the last message is a tool execution result, synthesize a natural response
        if last_msg.role == "tool":
            tool_name = last_msg.name
            tool_output_str = last_msg.content
            
            try:
                output_data = json.loads(tool_output_str)
            except Exception:
                output_data = {"result": tool_output_str}

            # Handle workflow follow-up / inspect_csv tool response
            if tool_name == "inspect_csv":
                if output_data.get("status") == "error":
                    return ModelResponse(content=f"Error inspecting CSV: {output_data.get('message')}", tool_calls=[])
                fname = output_data.get("filename", "CSV")
                rows = output_data.get("row_count", 0)
                cols = output_data.get("column_count", 0)
                cnames = output_data.get("column_names", [])
                stats = output_data.get("numeric_statistics", {})
                user_msgs = [m.content for m in messages if m.role == "user"]
                last_user_q = user_msgs[-1].lower() if user_msgs else ""

                if any(kw in last_user_q for kw in ["average", "mean", "avg"]):
                    target_col = None
                    for col in stats.keys():
                        if col.lower() in last_user_q:
                            target_col = col
                            break
                    if not target_col and "price" in stats:
                        target_col = "price"
                    elif not target_col and stats:
                        target_col = list(stats.keys())[0]

                    if target_col and target_col in stats:
                        mean_val = stats[target_col]["mean"]
                        return ModelResponse(content=f"Based on analysis of '{fname}', the average {target_col} is {mean_val:.2f} (across {stats[target_col]['count']} rows).", tool_calls=[])

                if user_msgs and "save" in user_msgs[-1].lower() and "task" in user_msgs[-1].lower():
                    return ModelResponse(
                        content=None,
                        tool_calls=[
                            ToolCall(
                                id="call_workflow_task_1",
                                name="create_task",
                                arguments={
                                    "title": f"Analyze {fname} results",
                                    "description": f"Analyzed {fname}: {rows} rows, stats: {str(stats)}",
                                    "priority": "high"
                                }
                            )
                        ]
                    )
                stats_str = ", ".join([f"{col}: mean={s['mean']:.2f}, min={s['min']}, max={s['max']}" for col, s in stats.items()])
                return ModelResponse(content=f"Inspected CSV '{fname}': {rows} rows, {cols} columns.\nColumns: {cnames}\nNumeric Statistics: {stats_str or 'None'}", tool_calls=[])

            # Handle task tool responses
            if tool_name == "create_task":
                if output_data.get("status") == "error":
                    return ModelResponse(content=output_data.get("message", "Failed to create task."), tool_calls=[])
                tid = output_data.get("task_id")
                msg = output_data.get("message", f"Created task #{tid}")
                return ModelResponse(content=msg, tool_calls=[])

            elif tool_name == "get_task":
                if output_data.get("status") == "not_found":
                    return ModelResponse(content=output_data.get("message", "Task not found."), tool_calls=[])
                t = output_data.get("task", {})
                return ModelResponse(content=f"Task #{t.get('id')}: {t.get('title')} [{t.get('status').upper()} - {t.get('priority').upper()} priority]", tool_calls=[])

            elif tool_name == "update_task" or tool_name == "complete_task":
                if output_data.get("status") == "error":
                    return ModelResponse(content=output_data.get("message", "Update failed."), tool_calls=[])
                return ModelResponse(content=output_data.get("message", "Task updated successfully."), tool_calls=[])

            elif tool_name == "delete_task":
                if output_data.get("status") == "error":
                    return ModelResponse(content=output_data.get("message", "Deletion failed."), tool_calls=[])
                return ModelResponse(content=output_data.get("message", "Task deleted successfully."), tool_calls=[])

            elif tool_name == "list_tasks":
                tasks = output_data.get("tasks", [])
                status_f = output_data.get("status_filter")
                prio_f = output_data.get("priority_filter")
                if tasks:
                    task_lines = [f"{i+1}. {t.get('title')} — {t.get('priority')} priority [{t.get('status')}]" for i, t in enumerate(tasks)]
                    prefix = f"You have {len(tasks)} matching tasks:"
                    if status_f:
                        prefix = f"You have {len(tasks)} {status_f} tasks:"
                    elif prio_f:
                        prefix = f"Here are your {prio_f}-priority tasks:"
                    return ModelResponse(content=f"{prefix}\n" + "\n".join(task_lines), tool_calls=[])
                return ModelResponse(content="You have no tasks matching the criteria.", tool_calls=[])

            elif tool_name == "search_tasks":
                tasks = output_data.get("tasks", [])
                if tasks:
                    task_lines = [f"- #{t.get('id')} {t.get('title')} ({t.get('status')})" for t in tasks]
                    return ModelResponse(content=f"Found {len(tasks)} matching task(s):\n" + "\n".join(task_lines), tool_calls=[])
                return ModelResponse(content="No matching tasks found.", tool_calls=[])

            # Handle skill discovery tool responses
            elif tool_name == "list_skills":
                skills = output_data.get("skills", [])
                if skills:
                    skill_list_str = "\n".join([f"- **{s.get('name')}**: {s.get('description')}" for s in skills])
                    return ModelResponse(content=f"I have {len(skills)} modular skills available:\n{skill_list_str}", tool_calls=[])
                return ModelResponse(content="No modular skills are currently registered.", tool_calls=[])

            elif tool_name == "get_skill_info":
                if output_data.get("status") == "error" or output_data.get("status") == "not_found":
                    return ModelResponse(content=output_data.get("message", "Skill not found."), tool_calls=[])
                sk = output_data.get("skill", {})
                return ModelResponse(content=f"Skill: {sk.get('name')} (v{sk.get('version')})\nDescription: {sk.get('description')}\nRequired Tools: {sk.get('required_tools')}", tool_calls=[])

            # Handle file intelligence tool responses
            elif tool_name == "list_files":
                files = output_data.get("files", [])
                if files:
                    file_list_str = "\n".join([f"- {f.get('name')} ({f.get('size_bytes')} bytes)" for f in files])
                    return ModelResponse(content=f"You currently have {len(files)} file(s) in your workspace:\n{file_list_str}", tool_calls=[])
                return ModelResponse(content="Your workspace directory is currently empty.", tool_calls=[])

            elif tool_name == "read_file":
                if output_data.get("status") == "error":
                    return ModelResponse(content=f"Error reading file: {output_data.get('message')}", tool_calls=[])
                fname = output_data.get("filename", "file")
                content = output_data.get("content", "")
                return ModelResponse(content=f"Contents of {fname}:\n\n{content}", tool_calls=[])

            elif tool_name == "inspect_csv":
                if output_data.get("status") == "error":
                    return ModelResponse(content=f"Error inspecting CSV: {output_data.get('message')}", tool_calls=[])
                fname = output_data.get("filename", "CSV")
                rows = output_data.get("row_count", 0)
                cols = output_data.get("column_count", 0)
                cnames = output_data.get("column_names", [])
                stats = output_data.get("numeric_statistics", {})

                user_msgs = [m.content for m in messages if m.role == "user"]
                last_user_q = user_msgs[-1].lower() if user_msgs else ""

                if any(kw in last_user_q for kw in ["average", "mean", "avg"]):
                    target_col = None
                    for col in stats.keys():
                        if col.lower() in last_user_q:
                            target_col = col
                            break
                    if not target_col and "price" in stats:
                        target_col = "price"
                    elif not target_col and stats:
                        target_col = list(stats.keys())[0]

                    if target_col and target_col in stats:
                        mean_val = stats[target_col]["mean"]
                        return ModelResponse(content=f"Based on analysis of '{fname}', the average {target_col} is {mean_val:.2f} (across {stats[target_col]['count']} rows).", tool_calls=[])

                stats_str = ", ".join([f"{col}: mean={s['mean']:.2f}, min={s['min']}, max={s['max']}" for col, s in stats.items()])
                return ModelResponse(content=f"Inspected CSV '{fname}': {rows} rows, {cols} columns.\nColumns: {cnames}\nNumeric Statistics: {stats_str or 'None'}", tool_calls=[])

            elif tool_name == "inspect_json":
                if output_data.get("status") == "error":
                    return ModelResponse(content=f"Error inspecting JSON: {output_data.get('message')}", tool_calls=[])
                fname = output_data.get("filename", "JSON")
                dtype = output_data.get("data_type", "unknown")
                keys = output_data.get("top_level_keys")
                preview = output_data.get("preview", "")
                return ModelResponse(content=f"JSON file '{fname}' structure ({dtype}):\nKeys: {keys}\nPreview:\n{preview}", tool_calls=[])

            elif tool_name == "search_files":
                query = output_data.get("query", "")
                results = output_data.get("results", [])
                if results:
                    snippets = "\n".join([f"- [{r.get('filename')}: line {r.get('line_number')}] {r.get('snippet')}" for r in results])
                    return ModelResponse(content=f"Found {len(results)} matching snippet(s) for '{query}':\n{snippets}", tool_calls=[])
                return ModelResponse(content=f"No matching snippets found for '{query}'.", tool_calls=[])

            elif tool_name == "get_project_context":
                mems = output_data.get("memories", [])
                tasks = output_data.get("pending_tasks", [])
                files = output_data.get("workspace_files", [])
                skills = output_data.get("available_skills", [])

                if not mems and not tasks:
                    return ModelResponse(content="I checked your project context, but I couldn't find any saved memories or pending tasks regarding what you are currently working on. You can tell me what you're working on, and I'll remember it!", tool_calls=[])

                mem_summary = ", ".join([f"'{m.get('key')}': {m.get('value')}" for m in mems]) or "None"
                task_summary = ", ".join([f"#{t.get('id')} {t.get('title')} ({t.get('priority')} priority)" for t in tasks]) or "None"
                file_summary = ", ".join([f"{f.get('name')}" for f in files]) or "None"

                return ModelResponse(
                    content=f"Here is what you are currently working on based on your project context:\n- Memories: {mem_summary}\n- Pending Tasks: {task_summary}\n- Workspace Files: {file_summary}",
                    tool_calls=[]
                )

            # Handle existing tool responses
            elif tool_name == "get_current_time":
                formatted_time = output_data.get("formatted", "unknown time")
                timezone = output_data.get("timezone", "")
                return ModelResponse(content=f"It is currently {formatted_time} ({timezone}).", tool_calls=[])
            
            elif tool_name == "calculator":
                expr = output_data.get("expression", "")
                res = output_data.get("result", output_data.get("error", "unknown"))
                return ModelResponse(content=f"{expr} = {res}", tool_calls=[])
            
            elif tool_name == "save_memory":
                return ModelResponse(content="Got it. I'll remember that.", tool_calls=[])
            
            elif tool_name == "get_memory":
                mem = output_data.get("memory")
                if mem:
                    return ModelResponse(content=f"Your {mem.get('key')} is {mem.get('value')}.", tool_calls=[])
                return ModelResponse(content="I couldn't find that in my memory.", tool_calls=[])
            
            elif tool_name == "search_memory":
                results = output_data.get("results", [])
                if results:
                    summary = ", ".join([f"'{r.get('key')}': {r.get('value')}" for r in results])
                    return ModelResponse(content=f"Here is what I found in memory: {summary}", tool_calls=[])
                return ModelResponse(content="I couldn't find any matching memories.", tool_calls=[])
            
            elif tool_name == "list_memories":
                mems = output_data.get("memories", [])
                if mems:
                    summary = ", ".join([f"'{m.get('key')}': {m.get('value')}" for m in mems])
                    return ModelResponse(content=f"Here are all my stored memories: {summary}", tool_calls=[])
                return ModelResponse(content="My memory store is currently empty.", tool_calls=[])
            
            else:
                return ModelResponse(content=f"Tool {tool_name} executed successfully with result: {tool_output_str}", tool_calls=[])

        # Otherwise, inspect user message and decide whether to call a tool
        user_content = last_msg.content.strip()
        user_content_lower = user_content.lower()

        if tools:
            # Introduction / greeting check
            if any(kw in user_content_lower for kw in ["introduce yourself", "who are you", "what are you", "tell me about yourself", "your name", "please introduce yourself"]):
                return ModelResponse(content="Hello! I am JARVIS Nexus, your advanced modular AI assistant engineered for reliable offline and cloud-accelerated intelligence, built for high-performance developer workflows. I can help you manage persistent memory, track tasks, inspect workspace data, and run system diagnostics.", tool_calls=[])

            # Save memory check (placed before time check so 'date' or time words in reminder sentences trigger save_memory)
            if "remember" in user_content_lower or "save memory" in user_content_lower:
                key = "user_note"
                value = user_content
                category = "general"
                if "name" in user_content_lower:
                    match = re.search(r'(?:name\s+is|=)\s+([a-zA-Z0-9_\s]+)', user_content, re.IGNORECASE)
                    if match:
                        key = "user_name"
                        value = match.group(1).strip()
                        category = "identity"
                else:
                    match = re.search(r'remember\s+(?:that\s+)?(.+?)\s+(?:is|=)\s+(.+)', user_content, re.IGNORECASE)
                    if match:
                        key = match.group(1).strip()
                        value = match.group(2).strip()
                        category = "project" if any(w in key.lower() for w in ["project", "release", "date", "goal", "target"]) else "general"
                    else:
                        match_mem = re.search(r'remember\s+(?:that\s+)?(.+)', user_content, re.IGNORECASE)
                        if match_mem:
                            key = "note"
                            value = match_mem.group(1).strip()
                for tool in tools:
                    if tool.name == "save_memory":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_save_memory_1", name="save_memory", arguments={"key": key, "value": value, "category": category})])

            # Context intelligence triggers
            if any(kw in user_content_lower for kw in ["what am i working on", "currently working on", "what should i work on next", "what do you know about this project", "current priorities", "high priority tasks", "tasks are related to my project", "my work"]):
                for tool in tools:
                    if tool.name == "get_project_context":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_proj_ctx_1", name="get_project_context", arguments={"query": user_content})])

            # Workflow trigger: analyze sales.csv and save key result as a task
            if "analyze" in user_content_lower and "sales.csv" in user_content_lower and "task" in user_content_lower:
                for tool in tools:
                    if tool.name == "inspect_csv":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_workflow_csv_1", name="inspect_csv", arguments={"filename": "sales.csv"})])

            # Task management triggers
            if any(kw in user_content_lower for kw in ["create a task", "remind me to", "add task", "create"]):
                match = re.search(r'(?:create a (?:high[- ]priority |urgent |critical |low[- ]priority )?task(?: to| for)?|remind me to|add task|create)\s+(.+)', user_content, re.IGNORECASE)
                title = match.group(1).strip() if match and match.group(1) else user_content
                if title.lower().startswith("a task to "):
                    title = title[10:]
                elif title.lower().startswith("a high-priority task to "):
                    title = title[24:]

                priority = "medium"
                if any(p in user_content_lower for p in ["high-priority", "high priority", "urgent", "critical"]):
                    priority = "high"
                elif any(p in user_content_lower for p in ["low priority", "low-priority", "low"]):
                    priority = "low"

                for tool in tools:
                    if tool.name == "create_task":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_create_task_1", name="create_task", arguments={"title": title, "priority": priority})])

            if any(kw in user_content_lower for kw in ["list my tasks", "list tasks", "show my tasks", "what are my tasks", "show pending tasks", "what tasks", "pending tasks", "do i have tasks"]):
                status_arg = "pending" if any(k in user_content_lower for k in ["pending", "what tasks", "do i have tasks"]) else None
                for tool in tools:
                    if tool.name == "list_tasks":
                        args = {"status": status_arg} if status_arg else {}
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_list_tasks_1", name="list_tasks", arguments=args)])

            if "high-priority tasks" in user_content_lower or "high priority tasks" in user_content_lower:
                for tool in tools:
                    if tool.name == "list_tasks":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_list_tasks_2", name="list_tasks", arguments={"priority": "high"})])

            if "complete" in user_content_lower and ("task" in user_content_lower or "readme" in user_content_lower or "1" in user_content_lower):
                match = re.search(r'(?:task\s*#?\s*(\d+))|(\b1\b)', user_content, re.IGNORECASE)
                tid = int(match.group(1) or match.group(2)) if match else 1
                for tool in tools:
                    if tool.name == "complete_task":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_complete_task_1", name="complete_task", arguments={"task_id": tid})])

            # Skills triggers
            if any(kw in user_content_lower for kw in ["what skills", "skills do you have", "what can you help me with", "available skills"]):
                for tool in tools:
                    if tool.name == "list_skills":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_list_skills_1", name="list_skills", arguments={})])

            # File tools triggers
            if any(kw in user_content_lower for kw in ["what files", "list files", "my files", "files do i have"]):
                for tool in tools:
                    if tool.name == "list_files":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_list_files_1", name="list_files", arguments={})])

            if "what's inside" in user_content_lower or "inspect" in user_content_lower or "contents of" in user_content_lower or "analyze" in user_content_lower or ".csv" in user_content_lower:
                match_csv = re.search(r'([\w\-\.]+\.csv)', user_content, re.IGNORECASE)
                if match_csv or "sales.csv" in user_content_lower or ".csv" in user_content_lower:
                    fname = match_csv.group(1).strip() if match_csv else ("sales.csv" if "sales.csv" in user_content_lower else "data.csv")
                    for tool in tools:
                        if tool.name == "inspect_csv":
                            return ModelResponse(content=None, tool_calls=[ToolCall(id="call_inspect_csv_1", name="inspect_csv", arguments={"filename": fname})])
                elif ".json" in user_content_lower:
                    match = re.search(r'([\w\-\.]+\.json)', user_content, re.IGNORECASE)
                    fname = match.group(1) if match else "project.json"
                    for tool in tools:
                        if tool.name == "inspect_json":
                            return ModelResponse(content=None, tool_calls=[ToolCall(id="call_inspect_json_1", name="inspect_json", arguments={"filename": fname})])

            if "search my notes" in user_content_lower or "search files" in user_content_lower or "search for" in user_content_lower or "project files" in user_content_lower:
                match = re.search(r'(?:search\s+(?:my\s+notes|project\s+files|files|for)\s+)(?:for\s+)?([a-zA-Z0-9_\-]+)', user_content, re.IGNORECASE)
                query = match.group(1).strip() if match else "SIWES"
                for tool in tools:
                    if tool.name == "search_files":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_search_files_1", name="search_files", arguments={"query": query})])

            if "understand my project" in user_content_lower or "project state" in user_content_lower or "project assistant" in user_content_lower:
                for tool in tools:
                    if tool.name == "list_files":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_list_files_2", name="list_files", arguments={})])

            if "read" in user_content_lower or "open" in user_content_lower:
                match = re.search(r'(?:read|open)\s+([a-zA-Z0-9_\-\.]+)', user_content, re.IGNORECASE)
                fname = match.group(1).strip() if match else "notes.md"
                if fname.endswith(".json"):
                    for tool in tools:
                        if tool.name == "inspect_json":
                            return ModelResponse(content=None, tool_calls=[ToolCall(id="call_inspect_json_2", name="inspect_json", arguments={"filename": fname})])
                elif fname.endswith(".csv"):
                    for tool in tools:
                        if tool.name == "inspect_csv":
                            return ModelResponse(content=None, tool_calls=[ToolCall(id="call_inspect_csv_2", name="inspect_csv", arguments={"filename": fname})])
                else:
                    for tool in tools:
                        if tool.name == "read_file":
                            return ModelResponse(content=None, tool_calls=[ToolCall(id="call_read_file_1", name="read_file", arguments={"filename": fname})])

            # Time tool check
            if any(kw in user_content_lower for kw in ["time", "clock", "date", "what time"]):
                for tool in tools:
                    if tool.name == "get_current_time":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_time_1", name="get_current_time", arguments={})])

            # Calculator check
            calc_match = re.search(r'(?:calculate|compute|what is)\s+([\d\.\+\-\*\/\(\)\s]+)', user_content_lower)
            if calc_match or (any(op in user_content for op in ['+', '-', '*', '/']) and any(ch.isdigit() for ch in user_content)):
                expr = calc_match.group(1).strip() if calc_match else user_content
                for tool in tools:
                    if tool.name == "calculator":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_calc_1", name="calculator", arguments={"expression": expr})])
                    if tool.name == "save_memory":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_mem_save_1", name="save_memory", arguments={"key": key, "value": value, "category": category})])

            # Get memory check
            if "what is my name" in user_content_lower or "who am i" in user_content_lower:
                for tool in tools:
                    if tool.name == "get_memory":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_mem_get_1", name="get_memory", arguments={"key": "user_name"})])
            
            if "get memory" in user_content_lower or "fetch memory" in user_content_lower:
                match = re.search(r'(?:get memory|fetch memory)\s+(.+)', user_content, re.IGNORECASE)
                key = match.group(1).strip() if match else "user_note"
                for tool in tools:
                    if tool.name == "get_memory":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_mem_get_1", name="get_memory", arguments={"key": key})])

            # Search memory check
            if any(kw in user_content_lower for kw in ["search memory", "recall", "what do you remember", "what is my", "what are my", "favorite", "tell me about"]):
                query_match = re.search(r'(?:search memory|recall|what do you remember about|what is my|what are my|tell me about)\s+(.+)', user_content, re.IGNORECASE)
                query = query_match.group(1).strip() if query_match and query_match.group(1) else user_content
                if query.endswith("?"):
                    query = query[:-1].strip()
                for tool in tools:
                    if tool.name == "search_memory":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_mem_search_1", name="search_memory", arguments={"query": query})])

            # List memories check
            if "list memories" in user_content_lower or "show memories" in user_content_lower:
                for tool in tools:
                    if tool.name == "list_memories":
                        return ModelResponse(content=None, tool_calls=[ToolCall(id="call_mem_list_1", name="list_memories", arguments={})])

        # Default natural conversational response
        if "name" in user_content_lower:
            return ModelResponse(content="I am JARVIS Nexus, your advanced AI assistant.", tool_calls=[])
        
        return ModelResponse(content=f"I understand: '{user_content}'. How else can I assist you?", tool_calls=[])


def get_model_provider(provider_name: Optional[str] = None) -> BaseModelProvider:
    """Factory function to instantiate model provider based on configuration or argument."""
    from jarvis_nexus.config import Config
    name = (provider_name or Config.MODEL_PROVIDER).lower()

    if name == "nebius":
        from jarvis_nexus.nebius_provider import NebiusProvider
        return NebiusProvider()
    else:
        return MockModelProvider()
