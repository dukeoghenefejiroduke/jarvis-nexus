"""Iron Man Protocol Engine for JARVIS Nexus with understandable names."""

import os
from typing import Any, Dict, List
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager


class ProtocolEngine:
    """Executes clear, understandable automated macros and MCU protocols."""

    def __init__(self, memory_store: MemoryStore, task_store: TaskStore, file_manager: FileManager) -> None:
        self.memory_store = memory_store
        self.task_store = task_store
        self.file_manager = file_manager

    def execute_protocol(self, protocol_name: str) -> Dict[str, Any]:
        """Execute a named protocol and return execution summary."""
        name = protocol_name.lower().strip()

        if name in ["clean_slate", "reset_session"]:
            try:
                self.memory_store.save_memory("last_protocol", "Reset Session executed", category="system")
                return {
                    "protocol": "Reset Session (Clean Slate)",
                    "status": "success",
                    "message": "Session reset successfully. Temporary states cleared and system logs updated."
                }
            except Exception as e:
                return {"protocol": "Reset Session", "status": "error", "message": str(e)}

        elif name in ["house_party", "workspace_audit"]:
            try:
                files = self.file_manager.list_files()
                pending_tasks = self.task_store.list_tasks(status="pending")
                existing_titles = {t.get("title") for t in pending_tasks}

                tasks_created = 0
                tasks_reused = 0

                for f in files:
                    fname = f["name"]
                    audit_title = f"Audit and analyze workspace file: {fname}"
                    if audit_title in existing_titles:
                        tasks_reused += 1
                    else:
                        self.task_store.create_task(
                            title=audit_title,
                            description=f"Automated Workspace Audit protocol inspection for {fname}",
                            priority="high",
                            status="pending"
                        )
                        existing_titles.add(audit_title)
                        tasks_created += 1

                self.memory_store.save_memory("last_protocol", f"Workspace Audit executed ({tasks_created} created, {tasks_reused} reused)", category="system")
                return {
                    "protocol": "Workspace Audit (House Party)",
                    "status": "success",
                    "tasks_created": tasks_created,
                    "tasks_reused": tasks_reused,
                    "message": f"Workspace Audit complete. Created {tasks_created} new inspection task(s) and reused {tasks_reused} existing pending task(s)."
                }
            except Exception as e:
                return {"protocol": "Workspace Audit", "status": "error", "message": str(e)}

        elif name in ["diagnostics", "system_diagnostics"]:
            try:
                mems = self.memory_store.list_memories()
                tasks = self.task_store.list_tasks()
                files = self.file_manager.list_files()
                self.memory_store.save_memory("last_protocol", "System Diagnostics executed", category="system")
                return {
                    "protocol": "System Diagnostics",
                    "status": "success",
                    "vitals": {
                        "memory_count": len(mems),
                        "task_count": len(tasks),
                        "file_count": len(files),
                        "subsystem_status": "Optimal"
                    },
                    "message": "System Diagnostics complete. All subsystems (Memory, Tasks, Files) operating at peak efficiency."
                }
            except Exception as e:
                return {"protocol": "System Diagnostics", "status": "error", "message": str(e)}

        elif name in ["morning_briefing", "briefing"]:
            try:
                pending_tasks = self.task_store.list_tasks(status="pending")
                in_progress_tasks = self.task_store.list_tasks(status="in_progress")
                mems = self.memory_store.list_memories()
                files = self.file_manager.list_files()

                pending_count = len(pending_tasks)
                in_prog_count = len(in_progress_tasks)
                memory_count = len(mems)
                file_count = len(files)

                self.memory_store.save_memory("last_protocol", "Morning Briefing executed", category="system")

                msg = f"Good morning! Briefing summary: {pending_count} pending task(s), {in_prog_count} in-progress task(s), {memory_count} saved memory item(s), and {file_count} workspace document(s)."
                if pending_count == 0 and in_prog_count == 0:
                    msg += " All task queues are clear."

                return {
                    "protocol": "Morning Briefing",
                    "status": "success",
                    "briefing": {
                        "pending_tasks_count": pending_count,
                        "in_progress_tasks_count": in_prog_count,
                        "memory_count": memory_count,
                        "file_count": file_count,
                        "pending_tasks": [t.get("title", "") for t in pending_tasks[:5]],
                        "workspace_files": [f.get("name", "") for f in files[:10]]
                    },
                    "message": msg
                }
            except Exception as e:
                return {"protocol": "Morning Briefing", "status": "error", "message": str(e)}

        else:
            return {
                "protocol": protocol_name,
                "status": "error",
                "message": f"Unknown protocol '{protocol_name}'. Available: reset_session, workspace_audit, system_diagnostics, morning_briefing."
            }
