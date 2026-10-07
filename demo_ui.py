"""Polished Lightweight Web UI and Demo Experience for JARVIS Nexus (Milestone 11).

Runs completely offline using Python's standard library http.server and MockModelProvider.
Accessible at http://127.0.0.1:8000 (or configured port).
Optimized for mobile (Android/Termux) and desktop browsers.
"""

import os
import json
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional

from jarvis_nexus.config import Config
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.skills.registry import SkillRegistry
from jarvis_nexus.skills.builtin import register_builtin_skills
from jarvis_nexus.context import ContextManager
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.agent import Agent
from jarvis_nexus.models import MockModelProvider
from jarvis_nexus.security import safe_exception_message


# Global shared instances for the Demo UI session
memory_store = MemoryStore()
task_store = TaskStore()
file_manager = FileManager()
skill_registry = SkillRegistry()
register_builtin_skills(skill_registry)
context_manager = ContextManager(
    memory_store=memory_store,
    task_store=task_store,
    file_manager=file_manager,
    skill_registry=skill_registry
)
tool_registry = ToolRegistry(
    memory_store=memory_store,
    task_store=task_store,
    context_manager=context_manager
)
agent = Agent(
    model_provider=MockModelProvider(),
    memory_store=memory_store,
    tool_registry=tool_registry,
    context_manager=context_manager
)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS Nexus — AI Assistant Dashboard</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --accent-hover: #0ea5e9;
            --border: #334155;
            --success: #22c55e;
            --danger: #ef4444;
            --warning: #f59e0b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-primary); line-height: 1.5; padding: 10px; }
        header { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); margin-bottom: 15px; }
        header h1 { font-size: 1.25rem; color: var(--accent); display: flex; align-items: center; gap: 8px; }
        .badge { background: rgba(56, 189, 248, 0.1); color: var(--accent); padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; border: 1px solid var(--accent); }
        
        nav { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 5px; margin-bottom: 15px; }
        nav button { background: var(--card-bg); color: var(--text-secondary); border: 1px solid var(--border); padding: 8px 16px; border-radius: 8px; cursor: pointer; white-space: nowrap; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; }
        nav button.active { background: var(--accent); color: var(--bg-color); border-color: var(--accent); font-weight: 600; }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 15px; margin-bottom: 15px; }
        .card h2 { font-size: 1rem; margin-bottom: 12px; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 8px; }

        /* Chat Layout */
        .chat-container { display: flex; flex-direction: column; height: calc(100vh - 180px); min-height: 400px; }
        .messages { flex: 1; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 12px; }
        .message { max-width: 85%; padding: 10px 14px; border-radius: 10px; font-size: 0.9rem; word-break: break-word; }
        .message.user { background: var(--accent); color: var(--bg-color); align-self: flex-end; border-bottom-right-radius: 2px; }
        .message.assistant { background: #334155; color: var(--text-primary); align-self: flex-start; border-bottom-left-radius: 2px; }
        .message .meta { font-size: 0.7rem; opacity: 0.7; margin-bottom: 4px; font-weight: 600; }
        .tool-activity { font-size: 0.75rem; color: var(--warning); background: rgba(245, 158, 11, 0.1); padding: 4px 8px; border-radius: 6px; margin: 4px 0; border-left: 2px solid var(--warning); }
        
        .chat-input-area { display: flex; gap: 8px; padding-top: 10px; border-top: 1px solid var(--border); }
        .chat-input-area input { flex: 1; background: var(--bg-color); border: 1px solid var(--border); color: var(--text-primary); padding: 10px 14px; border-radius: 8px; font-size: 0.9rem; }
        .btn { background: var(--accent); color: var(--bg-color); border: none; padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        .btn:hover { background: var(--accent-hover); }
        .btn-secondary { background: transparent; color: var(--text-secondary); border: 1px solid var(--border); }
        .btn-danger { background: var(--danger); color: white; }

        /* Tables & Lists */
        table { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 8px; }
        th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
        th { color: var(--text-secondary); font-weight: 600; }
        .form-grid { display: grid; grid-template-columns: 1fr; gap: 10px; margin-bottom: 12px; }
        @media(min-width: 600px) { .form-grid { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); } }
        input, select, textarea { width: 100%; background: var(--bg-color); border: 1px solid var(--border); color: var(--text-primary); padding: 8px 12px; border-radius: 6px; font-size: 0.85rem; }
        
        pre { background: var(--bg-color); padding: 10px; border-radius: 6px; border: 1px solid var(--border); overflow-x: auto; font-size: 0.8rem; color: var(--accent); }
        .grid-2 { display: grid; grid-template-columns: 1fr; gap: 15px; }
        @media(min-width: 768px) { .grid-2 { grid-template-columns: 1fr 1fr; } }
    </style>
</head>
<body>
    <header>
        <h1>🤖 JARVIS Nexus <span style="font-size:0.8rem; color:var(--text-secondary);">v2.0</span></h1>
        <div class="badge">Offline Mock Mode</div>
    </header>

    <nav>
        <button class="active" onclick="switchTab('chat')">💬 Chat</button>
        <button onclick="switchTab('memory')">🧠 Memory</button>
        <button onclick="switchTab('tasks')">📋 Tasks</button>
        <button onclick="switchTab('files')">📁 Workspace</button>
        <button onclick="switchTab('skills')">⚡ Skills</button>
        <button onclick="switchTab('context')">🔍 Context</button>
        <button onclick="runDemoFlow()">🚀 Demo Flow</button>
    </nav>

    <!-- CHAT TAB -->
    <div id="tab-chat" class="tab-content active card">
        <div class="chat-container">
            <div id="messages" class="messages">
                <div class="message assistant">
                    <div class="meta">JARVIS</div>
                    Hello! I am JARVIS Nexus. How can I assist you today with your project, tasks, or files?
                </div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="chatInput" placeholder="Type a message or instruction..." onkeypress="if(event.key==='Enter') sendChat()">
                <button class="btn" onclick="sendChat()">Send</button>
                <button class="btn btn-secondary" onclick="clearChat()">Clear</button>
            </div>
        </div>
    </div>

    <!-- MEMORY TAB -->
    <div id="tab-memory" class="tab-content">
        <div class="card">
            <h2>Save / Update Memory</h2>
            <div class="form-grid">
                <input type="text" id="memKey" placeholder="Key (e.g. project_name)">
                <input type="text" id="memValue" placeholder="Value (e.g. JARVIS Nexus)">
                <select id="memCategory">
                    <option value="project">project</option>
                    <option value="identity">identity</option>
                    <option value="preference">preference</option>
                    <option value="fact">fact</option>
                    <option value="task">task</option>
                    <option value="general" selected>general</option>
                </select>
                <button class="btn" onclick="saveMemory()">Save Memory</button>
            </div>
        </div>
        <div class="card">
            <h2>Stored Memories</h2>
            <div style="margin-bottom: 10px; display:flex; gap:8px;">
                <input type="text" id="memSearchQuery" placeholder="Search memories..." oninput="loadMemories()">
                <button class="btn btn-secondary" onclick="loadMemories()">Refresh</button>
            </div>
            <div style="overflow-x: auto;">
                <table>
                    <thead><tr><th>Key</th><th>Category</th><th>Value</th><th>Actions</th></tr></thead>
                    <tbody id="memoryTableBody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- TASKS TAB -->
    <div id="tab-tasks" class="tab-content">
        <div class="card">
            <h2>Create New Task</h2>
            <div class="form-grid">
                <input type="text" id="taskTitle" placeholder="Task Title">
                <input type="text" id="taskDesc" placeholder="Description (optional)">
                <select id="taskPriority">
                    <option value="low">Low</option>
                    <option value="medium" selected>Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                </select>
                <button class="btn" onclick="createTask()">Create Task</button>
            </div>
        </div>
        <div class="card">
            <h2>Active Tasks</h2>
            <div style="margin-bottom: 10px;"><button class="btn btn-secondary" onclick="loadTasks()">Refresh Tasks</button></div>
            <div style="overflow-x: auto;">
                <table>
                    <thead><tr><th>ID</th><th>Title</th><th>Priority</th><th>Status</th><th>Actions</th></tr></thead>
                    <tbody id="taskTableBody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- FILES TAB -->
    <div id="tab-files" class="tab-content">
        <div class="card">
            <h2>Workspace Files</h2>
            <button class="btn btn-secondary" onclick="loadFiles()">Refresh Files</button>
            <div style="overflow-x: auto; margin-top: 10px;">
                <table>
                    <thead><tr><th>Name</th><th>Size (Bytes)</th><th>Actions</th></tr></thead>
                    <tbody id="fileTableBody"></tbody>
                </table>
            </div>
        </div>
        <div class="card">
            <h2>File Viewer / Inspector</h2>
            <div id="fileViewerContent" style="color: var(--text-secondary);">Select a file above to view or inspect.</div>
        </div>
    </div>

    <!-- SKILLS TAB -->
    <div id="tab-skills" class="tab-content">
        <div class="card">
            <h2>Registered Modular Skills</h2>
            <div id="skillsContainer" style="display: flex; flex-direction: column; gap: 10px;"></div>
        </div>
    </div>

    <!-- CONTEXT TAB -->
    <div id="tab-context" class="tab-content">
        <div class="card">
            <h2>Project Context Intelligence Summary</h2>
            <button class="btn" onclick="loadContext()">Refresh Context</button>
            <pre id="contextPre" style="margin-top: 10px; max-height: 500px;">Click refresh to load project context.</pre>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('nav button').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tabName).classList.add('active');
            event.target.classList.add('active');

            if (tabName === 'memory') loadMemories();
            if (tabName === 'tasks') loadTasks();
            if (tabName === 'files') loadFiles();
            if (tabName === 'skills') loadSkills();
            if (tabName === 'context') loadContext();
        }

        async function sendChat() {
            const input = document.getElementById('chatInput');
            const msg = input.value.trim();
            if (!msg) return;

            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML += `<div class="message user"><div class="meta">USER</div>${escapeHtml(msg)}</div>`;
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            // Loading indicator
            const loadingId = 'loading_' + Date.now();
            messagesDiv.innerHTML += `<div id="${loadingId}" class="message assistant"><div class="meta">JARVIS</div>Thinking...</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await res.json();
                document.getElementById(loadingId).remove();

                let html = `<div class="message assistant"><div class="meta">JARVIS</div>`;
                if (data.tool_activity && data.tool_activity.length > 0) {
                    data.tool_activity.forEach(act => {
                        html += `<div class="tool-activity">🔧 Using tool: <b>${escapeHtml(act.tool)}</b></div>`;
                    });
                }
                html += `${escapeHtml(data.response)}</div>`;
                messagesDiv.innerHTML += html;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            } catch (err) {
                document.getElementById(loadingId).remove();
                messagesDiv.innerHTML += `<div class="message assistant"><div class="meta">JARVIS</div>Error communicating with backend.</div>`;
            }
        }

        function clearChat() {
            document.getElementById('messages').innerHTML = `<div class="message assistant"><div class="meta">JARVIS</div>Chat history cleared.</div>`;
        }

        async function loadMemories() {
            const q = document.getElementById('memSearchQuery').value;
            const res = await fetch('/api/memories?query=' + encodeURIComponent(q));
            const data = await res.json();
            const tbody = document.getElementById('memoryTableBody');
            tbody.innerHTML = '';
            data.memories.forEach(m => {
                tbody.innerHTML += `<tr>
                    <td><b>${escapeHtml(m.key)}</b></td>
                    <td><span class="badge">${escapeHtml(m.category)}</span></td>
                    <td>${escapeHtml(m.value)}</td>
                    <td><button class="btn btn-danger" style="padding:4px 8px; font-size:0.75rem;" onclick="deleteMemory('${escapeHtml(m.key)}')">Delete</button></td>
                </tr>`;
            });
        }

        async function saveMemory() {
            const key = document.getElementById('memKey').value;
            const value = document.getElementById('memValue').value;
            const category = document.getElementById('memCategory').value;
            if (!key || !value) return alert('Key and value required');

            await fetch('/api/memories', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key, value, category})
            });
            document.getElementById('memKey').value = '';
            document.getElementById('memValue').value = '';
            loadMemories();
        }

        async function deleteMemory(key) {
            if (!confirm('Delete memory ' + key + '?')) return;
            await fetch('/api/memories?key=' + encodeURIComponent(key), {method: 'DELETE'});
            loadMemories();
        }

        async function loadTasks() {
            const res = await fetch('/api/tasks');
            const data = await res.json();
            const tbody = document.getElementById('taskTableBody');
            tbody.innerHTML = '';
            data.tasks.forEach(t => {
                tbody.innerHTML += `<tr>
                    <td>#${t.id}</td>
                    <td><b>${escapeHtml(t.title)}</b><br><small style="color:var(--text-secondary);">${escapeHtml(t.description || '')}</small></td>
                    <td><span class="badge">${escapeHtml(t.priority)}</span></td>
                    <td>${escapeHtml(t.status)}</td>
                    <td>
                        ${t.status !== 'completed' ? `<button class="btn" style="padding:4px 8px; font-size:0.75rem;" onclick="completeTask(${t.id})">Complete</button>` : ''}
                        <button class="btn btn-danger" style="padding:4px 8px; font-size:0.75rem;" onclick="deleteTask(${t.id})">Delete</button>
                    </td>
                </tr>`;
            });
        }

        async function createTask() {
            const title = document.getElementById('taskTitle').value;
            const description = document.getElementById('taskDesc').value;
            const priority = document.getElementById('taskPriority').value;
            if (!title) return alert('Task title required');

            await fetch('/api/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title, description, priority, status: 'pending'})
            });
            document.getElementById('taskTitle').value = '';
            document.getElementById('taskDesc').value = '';
            loadTasks();
        }

        async function completeTask(id) {
            await fetch('/api/tasks/complete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id})
            });
            loadTasks();
        }

        async function deleteTask(id) {
            if (!confirm('Delete task #' + id + '?')) return;
            await fetch('/api/tasks?id=' + id, {method: 'DELETE'});
            loadTasks();
        }

        async function loadFiles() {
            const res = await fetch('/api/files');
            const data = await res.json();
            const tbody = document.getElementById('fileTableBody');
            tbody.innerHTML = '';
            data.files.forEach(f => {
                tbody.innerHTML += `<tr>
                    <td><b>${escapeHtml(f.name)}</b></td>
                    <td>${f.size_bytes}</td>
                    <td>
                        <button class="btn" style="padding:4px 8px; font-size:0.75rem;" onclick="viewFile('${escapeHtml(f.name)}')">View</button>
                        ${f.extension === '.csv' ? `<button class="btn btn-secondary" style="padding:4px 8px; font-size:0.75rem;" onclick="inspectCsv('${escapeHtml(f.name)}')">Inspect CSV</button>` : ''}
                        ${f.extension === '.json' ? `<button class="btn btn-secondary" style="padding:4px 8px; font-size:0.75rem;" onclick="inspectJson('${escapeHtml(f.name)}')">Inspect JSON</button>` : ''}
                    </td>
                </tr>`;
            });
        }

        async function viewFile(filename) {
            const res = await fetch('/api/files/read', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename})
            });
            const data = await res.json();
            const viewer = document.getElementById('fileViewerContent');
            if (data.status === 'success') {
                viewer.innerHTML = `<h3>File: ${escapeHtml(filename)}</h3><pre>${escapeHtml(data.content)}</pre>`;
            } else {
                viewer.innerHTML = `<span style="color:var(--danger);">${escapeHtml(data.message)}</span>`;
            }
        }

        async function inspectCsv(filename) {
            const res = await fetch('/api/files/inspect_csv', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename})
            });
            const data = await res.json();
            const viewer = document.getElementById('fileViewerContent');
            viewer.innerHTML = `<h3>CSV Inspection: ${escapeHtml(filename)}</h3><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
        }

        async function inspectJson(filename) {
            const res = await fetch('/api/files/inspect_json', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename})
            });
            const data = await res.json();
            const viewer = document.getElementById('fileViewerContent');
            viewer.innerHTML = `<h3>JSON Inspection: ${escapeHtml(filename)}</h3><pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
        }

        async function loadSkills() {
            const res = await fetch('/api/skills');
            const data = await res.json();
            const container = document.getElementById('skillsContainer');
            container.innerHTML = '';
            data.skills.forEach(s => {
                container.innerHTML += `<div class="card" style="margin-bottom:8px;">
                    <h3 style="color:var(--accent); font-size:0.95rem;">${escapeHtml(s.name)}</h3>
                    <p style="font-size:0.85rem; color:var(--text-secondary); margin-top:4px;">${escapeHtml(s.description)}</p>
                </div>`;
            });
        }

        async function loadContext() {
            const res = await fetch('/api/context');
            const data = await res.json();
            document.getElementById('contextPre').textContent = JSON.stringify(data, null, 2);
        }

        async function runDemoFlow() {
            switchTab('chat');
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML += `<div class="message assistant" style="background:#0369a1;"><div class="meta">DEMO FLOW</div>Starting 7-Step JARVIS Demo Sequence...</div>`;

            const steps = [
                "Hello JARVIS, please introduce yourself.",
                "What is 27 * 14?",
                "Remember that my favorite project is JARVIS Nexus.",
                "What is my favorite project?",
                "Analyze sales.csv and tell me the average price.",
                "Create a high-priority task to test the final JARVIS demo.",
                "What am I currently working on?"
            ];

            for (let i = 0; i < steps.length; i++) {
                await new Promise(r => setTimeout(r, 800));
                document.getElementById('chatInput').value = steps[i];
                await sendChat();
            }
        }

        function escapeHtml(str) {
            if (!str) return '';
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }
    </style>
</body>
</html>
"""


class JarvisDemoHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for JARVIS Nexus Demo UI API and frontend."""

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif path == "/api/status":
            self._send_json({
                "status": "online",
                "provider": Config.MODEL_PROVIDER,
                "memories": len(memory_store.list_memories()),
                "tasks": len(task_store.list_tasks()),
                "files": len(file_manager.list_files())
            })

        elif path == "/api/memories":
            q = query.get("query", [""])[0]
            mems = memory_store.search_memory(q) if q else memory_store.list_memories()
            self._send_json({"memories": mems})

        elif path == "/api/tasks":
            tasks = task_store.list_tasks()
            self._send_json({"tasks": tasks})

        elif path == "/api/files":
            files = file_manager.list_files()
            self._send_json({"files": files})

        elif path == "/api/skills":
            skills = skill_registry.list_skills()
            self._send_json({"skills": skills})

        elif path == "/api/context":
            q = query.get("query", ["project"])[0]
            ctx = context_manager.get_project_context(q)
            self._send_json(ctx)

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            data = {}

        if path == "/api/chat":
            msg = data.get("message", "")
            if not msg:
                self._send_json({"response": "Please provide a message.", "tool_activity": []})
                return

            # Clear agent history or maintain conversation
            # Let's run agent chat and track tool activity
            tool_activity = []
            
            # Intercept tool calls or check what agent did
            # To capture tool activity, we can inspect tool calls in response or history
            response_text = agent.chat(msg)
            
            # Extract recent tool activity from history if any tool was executed
            history = agent.get_history()
            for h in history:
                if h.role == "tool" and hasattr(h, "name") and h.name:
                    tool_activity.append({"tool": h.name})

            self._send_json({
                "response": response_text,
                "tool_activity": tool_activity
            })

        elif path == "/api/memories":
            key = data.get("key", "")
            value = data.get("value", "")
            category = data.get("category", "general")
            success = memory_store.save_memory(key, value, category)
            self._send_json({"success": success})

        elif path == "/api/tasks":
            title = data.get("title", "")
            description = data.get("description", "")
            priority = data.get("priority", "medium")
            status = data.get("status", "pending")
            task_id = task_store.create_task(title=title, description=description, priority=priority, status=status)
            self._send_json({"task_id": task_id})

        elif path == "/api/tasks/complete":
            task_id = data.get("id")
            success = task_store.complete_task(task_id) if task_id else False
            self._send_json({"success": success})

        elif path == "/api/files/read":
            filename = data.get("filename", "")
            res = file_manager.read_file(filename)
            self._send_json(res)

        elif path == "/api/files/inspect_csv":
            filename = data.get("filename", "")
            res = file_manager.inspect_csv(filename)
            self._send_json(res)

        elif path == "/api/files/inspect_json":
            filename = data.get("filename", "")
            res = file_manager.inspect_json(filename)
            self._send_json(res)

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_DELETE(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/api/memories":
            key = query.get("key", [""])[0]
            success = memory_store.delete_memory(key) if key else False
            self._send_json({"success": success})

        elif path == "/api/tasks":
            try:
                task_id = int(query.get("id", ["0"])[0])
                success = task_store.delete_task(task_id) if task_id else False
                self._send_json({"success": success})
            except Exception:
                self._send_json({"success": False})

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def _send_json(self, data: Any) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default HTTP server logging for clean output."""
        pass


def run_server(port: int = 8000, background: bool = False) -> Optional[HTTPServer]:
    """Run the JARVIS Nexus Demo UI HTTP server."""
    server = HTTPServer(("0.0.0.0", port), JarvisDemoHTTPHandler)
    if background:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server
    else:
        print(f"Starting JARVIS Nexus Demo UI at http://0.0.0.0:{port}")
        print("Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down demo UI server.")
            server.server_close()
        return None


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    run_server(port=port, background=False)
