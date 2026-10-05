"""Advanced Context and Memory Intelligence Manager for JARVIS Nexus."""

import os
import re
from typing import Any, Dict, List, Optional
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.skills.registry import SkillRegistry
from jarvis_nexus.skills.builtin import register_builtin_skills


class ContextManager:
    """Orchestrates memory, tasks, files, and skills to assemble relevant context with budgeting."""

    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        task_store: Optional[TaskStore] = None,
        file_manager: Optional[FileManager] = None,
        skill_registry: Optional[SkillRegistry] = None,
        max_history_messages: int = 10,
        max_memories: int = 5,
        max_tasks: int = 5,
        max_files: int = 5
    ) -> None:
        self.memory_store = memory_store or MemoryStore()
        self.task_store = task_store or TaskStore()
        self.file_manager = file_manager or FileManager()
        self.skill_registry = skill_registry or SkillRegistry()
        if not self.skill_registry.list_skills():
            register_builtin_skills(self.skill_registry)

        self.max_history_messages = max_history_messages
        self.max_memories = max_memories
        self.max_tasks = max_tasks
        self.max_files = max_files

    def get_relevant_memories(self, query: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve and rank relevant long-term memories using deterministic word overlap and category matching."""
        limit = limit or self.max_memories
        all_memories = self.memory_store.list_memories()
        if not all_memories:
            return []

        if not query:
            return all_memories[:limit]

        query_tokens = set(re.findall(r'\w+', query.lower()))
        scored_memories = []

        for mem in all_memories:
            score = 0
            key_lower = mem.get("key", "").lower()
            val_lower = mem.get("value", "").lower()
            cat_lower = mem.get("category", "").lower()

            # Exact key or category match bonus
            if any(t in key_lower for t in query_tokens):
                score += 3
            if any(t in cat_lower for t in query_tokens):
                score += 2

            # Word overlap in value
            val_tokens = set(re.findall(r'\w+', val_lower))
            overlap = len(query_tokens.intersection(val_tokens))
            score += overlap

            # Project/Identity bias if query asks about project or name
            if any(w in query.lower() for w in ["project", "work", "nexus", "hackathon"]) and (cat_lower == "project" or "project" in key_lower or "hackathon" in key_lower):
                score += 5
            if "name" in query.lower() and (cat_lower == "identity" or "name" in key_lower):
                score += 5

            scored_memories.append((score, mem))

        # Sort by score descending, then recency
        scored_memories.sort(key=lambda x: (x[0], x[1].get("updated_at", "")), reverse=True)
        
        # Return top N with score > 0 or all if no strict matches
        top_matches = [mem for score, mem in scored_memories if score > 0]
        if not top_matches:
            top_matches = [mem for _, mem in scored_memories]

        return top_matches[:limit]

    def get_relevant_tasks(self, status: Optional[str] = "pending", priority: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant tasks ordered by priority and status."""
        limit = limit or self.max_tasks
        tasks = self.task_store.list_tasks(status=status, priority=priority)
        # Sort by priority (high > medium > low) and recency
        priority_order = {"high": 3, "medium": 2, "low": 1}
        tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 2), t.get("created_at", "")), reverse=True)
        return tasks[:limit]

    def get_relevant_files(self, query: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """Retrieve workspace files or file search snippets relevant to query."""
        limit = limit or self.max_files
        try:
            files = self.file_manager.list_files()
            if query:
                snippets = self.file_manager.search_files(query)
                return {
                    "files": files[:limit],
                    "search_snippets": snippets[:limit]
                }
            return {"files": files[:limit], "search_snippets": []}
        except Exception:
            return {"files": [], "search_snippets": []}

    def get_project_context(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate project-related memories, pending tasks, workspace files, and available skills."""
        q = query or "project"
        memories = self.get_relevant_memories(q, limit=self.max_memories)
        tasks = self.get_relevant_tasks(status="pending", limit=self.max_tasks)
        file_info = self.get_relevant_files(q, limit=self.max_files)
        skills = self.skill_registry.list_skills()

        return {
            "query": q,
            "memories": memories,
            "pending_tasks": tasks,
            "workspace_files": file_info.get("files", []),
            "file_snippets": file_info.get("search_snippets", []),
            "available_skills": skills
        }

    def trim_history(self, messages: List[Any]) -> List[Any]:
        """Trim conversation history to respect max history messages while preserving important system/context messages."""
        if not messages or len(messages) <= self.max_history_messages:
            return messages

        # Separate system messages or initial user messages if needed, or keep last max_history_messages
        system_msgs = [m for m in messages if getattr(m, "role", "") == "system"]
        other_msgs = [m for m in messages if getattr(m, "role", "") != "system"]

        trimmed_others = other_msgs[-self.max_history_messages:]
        return system_msgs + trimmed_others

    def assemble_context_prompt(self, query: Optional[str] = None) -> str:
        """Assemble a concise structured context prompt for model injection."""
        ctx = self.get_project_context(query)
        
        mem_str = "\n".join([f"- [{m.get('category')}] {m.get('key')}: {m.get('value')}" for m in ctx["memories"]]) or "None"
        task_str = "\n".join([f"- #{t.get('id')} {t.get('title')} ({t.get('priority')} priority, {t.get('status')})" for t in ctx["pending_tasks"]]) or "None"
        file_str = "\n".join([f"- {f.get('name')} ({f.get('size_bytes')} bytes)" for f in ctx["workspace_files"]]) or "None"
        skill_str = "\n".join([f"- {s.get('name')}: {s.get('description')}" for s in ctx["available_skills"]]) or "None"

        return f"""[Context Intelligence Summary]
--- Relevant Long-Term Memories ---
{mem_str}

--- Pending Tasks ---
{task_str}

--- Workspace Files ---
{file_str}

--- Available Skills ---
{skill_str}
"""
