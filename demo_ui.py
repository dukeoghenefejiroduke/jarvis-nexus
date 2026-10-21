"""Polished Lightweight Web UI and Demo Experience for JARVIS Nexus (Milestone 11).

Runs completely offline using Python's standard library http.server and MockModelProvider.
Accessible at http://127.0.0.1:8000 (or configured port).
Optimized for mobile (Android/Termux) and desktop browsers.
"""

import os
import json
import time
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
from jarvis_nexus.models import get_model_provider
from jarvis_nexus.security import redact_secrets, safe_exception_message
from jarvis_nexus.protocols import ProtocolEngine
from jarvis_nexus.telemetry import TelemetryManager
from jarvis_nexus.audit import AuditManager


# Global shared instances for the Demo UI session
memory_store = MemoryStore(db_path=os.environ.get("JARVIS_MEMORY_DB"))
task_store = TaskStore(db_path=os.environ.get("JARVIS_TASK_DB"))
file_manager = FileManager(workspace_dir=os.environ.get("JARVIS_WORKSPACE"))
audit_manager = AuditManager(log_path=os.environ.get("JARVIS_AUDIT_LOG"))
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
    model_provider=get_model_provider(),
    memory_store=memory_store,
    tool_registry=tool_registry,
    context_manager=context_manager
)
protocol_engine = ProtocolEngine(memory_store, task_store, file_manager)
telemetry_manager = TelemetryManager()

# Pre-seed sample workspace files for hackathon judges
os.makedirs(file_manager.workspace_dir, exist_ok=True)
try:
    with open(os.path.join(file_manager.workspace_dir, "financial_data.csv"), "w") as f:
        f.write("quarter,revenue,expenses,profit\nQ1,150000,90000,60000\nQ2,180000,105000,75000\nQ3,210000,120000,90000\nQ4,250000,135000,115000\n")
    with open(os.path.join(file_manager.workspace_dir, "sample_project.md"), "w") as f:
        f.write("# JARVIS Nexus Project Notes\n\n- Milestone 11: Web UI & Dashboard\n- Milestone 12: Nebius + Nemotron Integration\n- Status: Ready for Hackathon Demo.\n")
    with open(os.path.join(file_manager.workspace_dir, "architecture_spec.json"), "w") as f:
        f.write(json.dumps({"system": "JARVIS Nexus", "version": "1.0.0", "engine": "NVIDIA Nemotron via Nebius Token Factory"}, indent=2))
except Exception:
    pass


UNKNOWN_COMMIT_SHA = "unknown"
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def _valid_commit_sha(value: Optional[str]) -> Optional[str]:
    """Return a stripped git SHA if it looks like one (7-64 hex chars), else None."""
    candidate = (value or "").strip()
    if 7 <= len(candidate) <= 64 and set(candidate) <= _HEX_DIGITS:
        return candidate
    return None


def get_deployment_info(env: Any = None) -> Dict[str, Any]:
    """Describe the running deployment (version and commit identity).

    Commit SHA resolution:

    * On Render (``RENDER=true`` or ``RENDER_GIT_COMMIT`` present) the SHA is read
      ONLY from Render's built-in ``RENDER_GIT_COMMIT``. There is deliberately no
      fallback to the manually configured ``APP_COMMIT_SHA``, because a manual value
      cannot independently verify the deployed revision. If the variable is missing
      or malformed the SHA is reported as ``unknown`` and
      ``deployment_identity_available`` is ``false``.
    * Outside Render (local development) ``APP_COMMIT_SHA`` is accepted as an
      optional, self-declared fallback; otherwise the SHA is ``unknown``.

    The environment is read on every call so it reflects the live process state.
    """
    env = os.environ if env is None else env
    version = (env.get("APP_VERSION") or "").strip() or "unknown"
    on_render = str(env.get("RENDER", "")).strip().lower() == "true" or "RENDER_GIT_COMMIT" in env

    if on_render:
        platform = "render"
        sha = _valid_commit_sha(env.get("RENDER_GIT_COMMIT"))
        source = "RENDER_GIT_COMMIT"
    else:
        platform = "local"
        sha = _valid_commit_sha(env.get("APP_COMMIT_SHA"))
        source = "APP_COMMIT_SHA"

    return {
        "version": version,
        "commit_sha": sha or UNKNOWN_COMMIT_SHA,
        "commit_source": source if sha else "unavailable",
        "deployment_platform": platform,
        "deployment_identity_available": sha is not None,
    }


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
        <h1>🤖 JARVIS Nexus <span style="font-size:0.8rem; color:var(--text-secondary);">MCU Edition</span></h1>
        <div id="hudTelemetry" style="font-size: 0.75rem; color: var(--success); display: flex; gap: 12px; align-items: center; background: rgba(34,197,94,0.1); padding: 6px 12px; border-radius: 8px; border: 1px solid var(--success);">
            <span>💻 CPU: <b id="hudCpu">12.5%</b></span>
            <span>🌡️ Temp: <b id="hudTemp">42.5°C</b></span>
            <span>💾 RAM: <b id="hudMem">45 MB</b></span>
            <span>⚡ Speed: <b id="hudSpeed">84.6 t/s</b></span>
        </div>
        <div class="badge">Nebius + Nemotron</div>
    </header>

    <nav>
        <button id="navChatBtn" class="active" onclick="switchTab('chat', this)">💬 Chat</button>
        <button id="navMemBtn" onclick="switchTab('memory', this)">🧠 Memory</button>
        <button id="navTasksBtn" onclick="switchTab('tasks', this)">📋 Tasks</button>
        <button id="navFilesBtn" onclick="switchTab('files', this)">📁 Workspace</button>
        <button id="navProtocolsBtn" onclick="switchTab('protocols', this)">⚡ Protocols</button>
        <button id="navSkillsBtn" onclick="switchTab('skills', this)">⚡ Skills</button>
        <button id="navContextBtn" onclick="switchTab('context', this)">🔍 Context</button>
        <button id="navDemoFlowBtn" onclick="runDemoFlow()">🚀 Demo Flow</button>
    </nav>

    <!-- CHAT TAB -->
    <div id="tab-chat" class="tab-content active card">
        <div class="chat-container">
            <div style="margin-bottom: 8px; display: flex; gap: 12px; align-items: center; justify-content: space-between;">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <label style="font-size: 0.8rem; color: var(--text-secondary);">Agent Persona:</label>
                    <select id="personaSelect" style="width: auto; padding: 4px 8px; font-size: 0.8rem;">
                        <option value="default">Default JARVIS</option>
                        <option value="codearchitect">@CodeArchitect</option>
                        <option value="datascientist">@DataScientist</option>
                        <option value="devopsengineer">@DevOpsEngineer</option>
                    </select>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <label style="font-size: 0.8rem; color: var(--text-secondary); display:flex; align-items:center; gap:4px; cursor:pointer;">
                        <input type="checkbox" id="ttsToggle" checked style="width:auto;"> 🔊 Voice Synth
                    </label>
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:0.75rem;" onclick="startVoiceInput()">🎙️ Speak</button>
                </div>
            </div>
            <div id="messages" class="messages">
                <div class="message assistant">
                    <div class="meta">JARVIS</div>
                    Hello! I am JARVIS Nexus, powered by NVIDIA Nemotron via Nebius Token Factory. How can I assist you today?
                </div>
            </div>
            <div style="display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0;">
                <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; border-radius: 6px;" onclick="setPrompt('Calculate 1428 * 79 + 543')">🔢 Calculate</button>
                <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; border-radius: 6px;" onclick="setPrompt('What is our target release date?')">📅 Release Date</button>
                <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; border-radius: 6px;" onclick="setPrompt('Based on current tasks, what should I work on next?')">💡 Next Action</button>
                <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; border-radius: 6px;" onclick="switchTab('protocols'); executeProtocol('morning_briefing'); showToast('Executing Alexa+ Morning Briefing...');">☀️ Morning Briefing</button>
            </div>
            <div class="chat-input-area">
                <input type="text" id="chatInput" placeholder="Type a message or instruction...">
                <button id="sendBtn" class="btn">Send</button>
                <button id="clearBtn" class="btn btn-secondary">Clear</button>
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
                <button id="saveMemBtn" class="btn" onclick="saveMemory()">Save Memory</button>
            </div>
        </div>
        <div class="card">
            <h2>Stored Memories</h2>
            <div style="margin-bottom: 10px; display:flex; gap:8px;">
                <input type="text" id="memSearchQuery" placeholder="Search memories..." oninput="loadMemories()">
                <button id="refreshMemBtn" class="btn btn-secondary" onclick="loadMemories()">Refresh</button>
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
                <button id="createTaskBtn" class="btn" onclick="createTask()">Create Task</button>
            </div>
        </div>
        <div class="card">
            <h2>Active Tasks</h2>
            <div style="margin-bottom: 10px;"><button id="refreshTasksBtn" class="btn btn-secondary" onclick="loadTasks()">Refresh Tasks</button></div>
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
            <h2>Upload Files from Device Storage</h2>
            <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:10px;">Select one or more documents from your device storage to add to the workspace.</p>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <input type="file" id="deviceFileInput" multiple style="background:var(--bg-color); border:1px solid var(--border); color:var(--text-primary); padding:8px; border-radius:6px;">
                <button class="btn" onclick="uploadFilesFromDevice()">Upload Selected Files</button>
            </div>
        </div>
        <div class="card">
            <h2>Create Document Manually</h2>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <input type="text" id="newDocFilename" placeholder="Document Filename (e.g. notes.md, data.csv, config.json)">
                <textarea id="newDocContent" rows="4" placeholder="Type document content here..." style="background:var(--bg-color); border:1px solid var(--border); color:var(--text-primary); padding:8px 12px; border-radius:6px; font-size:0.85rem; font-family:monospace;"></textarea>
                <button class="btn btn-secondary" onclick="uploadDocument()">Create Manual Document</button>
            </div>
        </div>
        <div class="card">
            <h2>Workspace Files</h2>
            <button id="refreshFilesBtn" class="btn btn-secondary" onclick="loadFiles()">Refresh Files</button>
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

    <!-- PROTOCOLS TAB -->
    <div id="tab-protocols" class="tab-content">
        <div class="card">
            <h2>Alexa+ Experience Simulation</h2>
            <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:12px;">Explore a simulated Alexa+-style assistant experience powered by JARVIS Nexus. The Morning Briefing summarizes live local tasks, saved memories, and workspace documents. This is an independent simulation, not a connection to an Alexa+ service.</p>
            <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:15px;">
                <button id="morningBriefingBtn" class="btn" onclick="executeProtocol('morning_briefing')">☀️ Run Alexa+ Morning Briefing</button>
                <button class="btn btn-secondary" onclick="executeProtocol('reset_session')">🧹 Reset Session</button>
                <button class="btn" onclick="executeProtocol('workspace_audit')">🎉 Workspace Audit</button>
                <button class="btn btn-secondary" onclick="executeProtocol('system_diagnostics')">🔍 System Diagnostics</button>
            </div>
            <div id="morningBriefingCard" style="display:none; margin-bottom:15px; background: rgba(59,130,246,0.08); border: 1px solid var(--accent); border-radius: 8px; padding: 12px;">
                <h3 style="color: var(--accent); font-size: 1rem; margin-bottom: 6px;">☀️ Morning Briefing Summary</h3>
                <p id="briefingMessage" style="font-size: 0.9rem; margin-bottom: 8px; font-weight: 500;"></p>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; margin-bottom: 10px; font-size: 0.85rem;">
                    <div style="background:var(--bg-color); padding:6px 10px; border-radius:6px; border:1px solid var(--border);">Pending: <b id="bPendingCount">0</b></div>
                    <div style="background:var(--bg-color); padding:6px 10px; border-radius:6px; border:1px solid var(--border);">In-Progress: <b id="bInProgressCount">0</b></div>
                    <div style="background:var(--bg-color); padding:6px 10px; border-radius:6px; border:1px solid var(--border);">Memories: <b id="bMemoryCount">0</b></div>
                    <div style="background:var(--bg-color); padding:6px 10px; border-radius:6px; border:1px solid var(--border);">Files: <b id="bFileCount">0</b></div>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-secondary);">
                    <p style="margin-bottom: 4px;"><b>Sample Pending Tasks:</b> <span id="bPendingTasksList">None</span></p>
                    <p><b>Workspace Documents:</b> <span id="bFilesList">None</span></p>
                </div>
            </div>
            <pre id="protocolResultPre">Select a protocol above to execute.</pre>
        </div>
        <div class="card">
            <h2>Multimodal Blueprint & Document Vision Inspector</h2>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <input type="text" id="visionFilename" placeholder="Enter workspace file name (e.g. architecture_spec.json or sample_project.md)">
                <button class="btn" onclick="inspectVision()">Analyze Blueprint / Schema</button>
                <pre id="visionResultPre">Result of visual/blueprint analysis will appear here.</pre>
            </div>
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
            <button id="refreshContextBtn" class="btn" onclick="loadContext()">Refresh Context</button>
            <pre id="contextPre" style="margin-top: 10px; max-height: 500px;">Click refresh to load project context.</pre>
        </div>
    </div>

    <script>
        function switchTab(tabName, btnElement) {
            try {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('nav button').forEach(el => el.classList.remove('active'));

                const tabEl = document.getElementById('tab-' + tabName);
                if (tabEl) {
                    tabEl.classList.add('active');
                }

                if (btnElement) {
                    btnElement.classList.add('active');
                } else {
                    const btns = document.querySelectorAll('nav button');
                    btns.forEach(b => {
                        if (b.getAttribute('onclick') && b.getAttribute('onclick').includes(`switchTab('${tabName}')`)) {
                            b.classList.add('active');
                        }
                    });
                }

                if (tabName === 'memory') loadMemories();
                if (tabName === 'tasks') loadTasks();
                if (tabName === 'files') loadFiles();
                if (tabName === 'skills') loadSkills();
                if (tabName === 'context') loadContext();
            } catch (err) {
                console.error('Error switching tab:', err);
            }
        }

        async function sendChat() {
            const input = document.getElementById('chatInput');
            if (!input) return;
            const msg = input.value.trim();
            if (!msg) return;

            const personaSelect = document.getElementById('personaSelect');
            const persona = personaSelect ? personaSelect.value : 'default';

            const messagesDiv = document.getElementById('messages');
            if (!messagesDiv) return;

            messagesDiv.innerHTML += `<div class="message user"><div class="meta">USER</div>${escapeHtml(msg)}</div>`;
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            const loadingId = 'loading_' + Math.random().toString(36).substring(2);
            messagesDiv.innerHTML += `<div id="${loadingId}" class="message assistant"><div class="meta">JARVIS (${escapeHtml(persona)})</div>Thinking...</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg, persona: persona})
                });
                const data = await res.json();

                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();

                let html = `<div class="message assistant"><div class="meta">JARVIS (${escapeHtml(persona)})</div>`;
                if (data.tool_activity && data.tool_activity.length > 0) {
                    data.tool_activity.forEach(act => {
                        html += `<div class="tool-activity">🔧 Using tool: <b>${escapeHtml(act.tool)}</b></div>`;
                    });
                }
                html += `${escapeHtml(data.response || 'No response')}</div>`;
                messagesDiv.innerHTML += html;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                speakText(data.response || 'No response');
                loadTelemetry();
            } catch (err) {
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();
                messagesDiv.innerHTML += `<div class="message assistant"><div class="meta">JARVIS</div>Error communicating with backend: ${escapeHtml(err.message)}</div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }

        function clearChat() {
            const messagesDiv = document.getElementById('messages');
            if (messagesDiv) {
                messagesDiv.innerHTML = `<div class="message assistant"><div class="meta">JARVIS</div>Chat history cleared.</div>`;
            }
        }

        async function loadMemories() {
            try {
                const searchInput = document.getElementById('memSearchQuery');
                const q = searchInput ? searchInput.value : '';
                const res = await fetch('/api/memories?query=' + encodeURIComponent(q));
                const data = await res.json();
                const tbody = document.getElementById('memoryTableBody');
                if (tbody) {
                    tbody.innerHTML = '';
                    (data.memories || []).forEach(m => {
                        tbody.innerHTML += `<tr>
                            <td><b>${escapeHtml(m.key)}</b></td>
                            <td><span class="badge">${escapeHtml(m.category)}</span></td>
                            <td>${escapeHtml(m.value)}</td>
                            <td><button class="btn btn-danger" style="padding:4px 8px; font-size:0.75rem;" onclick="deleteMemory('${escapeJsString(m.key)}')">Delete</button></td>
                        </tr>`;
                    });
                }
            } catch (err) {
                console.error('Error loading memories:', err);
            }
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
            try {
                const res = await fetch('/api/tasks');
                const data = await res.json();
                const tbody = document.getElementById('taskTableBody');
                if (tbody) {
                    tbody.innerHTML = '';
                    (data.tasks || []).forEach(t => {
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
            } catch (err) {
                console.error('Error loading tasks:', err);
            }
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
            try {
                const res = await fetch('/api/files');
                const data = await res.json();
                const tbody = document.getElementById('fileTableBody');
                if (tbody) {
                    tbody.innerHTML = '';
                    (data.files || []).forEach(f => {
                        tbody.innerHTML += `<tr>
                            <td><b>${escapeHtml(f.name)}</b></td>
                            <td>${f.size_bytes}</td>
                            <td>
                                <button class="btn" style="padding:4px 8px; font-size:0.75rem;" onclick="viewFile('${escapeJsString(f.name)}')">View</button>
                                ${f.extension === '.csv' ? `<button class="btn btn-secondary" style="padding:4px 8px; font-size:0.75rem;" onclick="inspectCsv('${escapeJsString(f.name)}')">Inspect CSV</button>` : ''}
                                ${f.extension === '.json' ? `<button class="btn btn-secondary" style="padding:4px 8px; font-size:0.75rem;" onclick="inspectJson('${escapeJsString(f.name)}')">Inspect JSON</button>` : ''}
                            </td>
                        </tr>`;
                    });
                }
            } catch (err) {
                console.error('Error loading files:', err);
            }
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

        async function uploadDocument() {
            const filenameInput = document.getElementById('newDocFilename');
            const contentInput = document.getElementById('newDocContent');
            if (!filenameInput || !contentInput) return;
            const filename = filenameInput.value.trim();
            const content = contentInput.value;
            if (!filename) {
                alert('Please enter a document filename (e.g. notes.md).');
                return;
            }
            try {
                const res = await fetch('/api/files/create', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filename, content})
                });
                const data = await res.json();
                if (data.status === 'success') {
                    alert('Document created successfully!');
                    filenameInput.value = '';
                    contentInput.value = '';
                    loadFiles();
                } else {
                    alert('Error: ' + (data.message || 'Failed to create document.'));
                }
            } catch (err) {
                alert('Error creating document: ' + err.message);
            }
        }

        async function uploadFilesFromDevice() {
            const fileInput = document.getElementById('deviceFileInput');
            if (!fileInput || fileInput.files.length === 0) {
                alert('Please select one or more files from your device storage first.');
                return;
            }
            let uploadedCount = 0;
            for (let i = 0; i < fileInput.files.length; i++) {
                const file = fileInput.files[i];
                await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = async function(e) {
                        const content = e.target.result;
                        const filename = file.name;
                        try {
                            const res = await fetch('/api/files/create', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({filename, content})
                            });
                            const data = await res.json();
                            if (data.status === 'success') {
                                uploadedCount++;
                            }
                        } catch (err) {
                            console.error('Error uploading file:', err);
                        }
                        resolve();
                    };
                    reader.readAsText(file);
                });
            }
            alert(`Successfully uploaded ${uploadedCount} file(s) from device storage!`);
            fileInput.value = '';
            loadFiles();
        }

        async function loadSkills() {
            try {
                const res = await fetch('/api/skills');
                const data = await res.json();
                const container = document.getElementById('skillsContainer');
                if (container) {
                    container.innerHTML = '';
                    (data.skills || []).forEach(s => {
                        container.innerHTML += `<div class="card" style="margin-bottom:8px;">
                            <h3 style="color:var(--accent); font-size:0.95rem;">${escapeHtml(s.name)}</h3>
                            <p style="font-size:0.85rem; color:var(--text-secondary); margin-top:4px;">${escapeHtml(s.description)}</p>
                        </div>`;
                    });
                }
            } catch (err) {
                console.error('Error loading skills:', err);
            }
        }

        async function loadContext() {
            try {
                const res = await fetch('/api/context');
                const data = await res.json();
                const pre = document.getElementById('contextPre');
                if (pre) {
                    pre.textContent = JSON.stringify(data, null, 2);
                }
            } catch (err) {
                console.error('Error loading context:', err);
            }
        }

        async function loadTelemetry() {
            try {
                const res = await fetch('/api/telemetry');
                const data = await res.json();
                const cEl = document.getElementById('hudCpu');
                const tEl = document.getElementById('hudTemp');
                const mEl = document.getElementById('hudMem');
                const sEl = document.getElementById('hudSpeed');
                if (cEl) cEl.textContent = data.cpu_percent + '%';
                if (tEl) tEl.textContent = data.core_temperature_c + '°C';
                if (mEl) mEl.textContent = data.memory_rss_mb + ' MB';
                if (sEl) sEl.textContent = data.tokens_per_sec + ' t/s';
            } catch (err) {
                console.error('Telemetry fetch error:', err);
            }
        }
        setInterval(loadTelemetry, 5000);

        let isExecutingProtocol = false;
        async function executeProtocol(proto) {
            if (isExecutingProtocol) return;
            isExecutingProtocol = true;

            const pre = document.getElementById('protocolResultPre');
            const btn = document.getElementById('morningBriefingBtn');
            if (btn) btn.disabled = true;
            if (pre) pre.textContent = 'Executing protocol ' + proto + '...';

            try {
                const res = await fetch('/api/protocols', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({protocol: proto})
                });
                const data = await res.json();
                if (pre) pre.textContent = JSON.stringify(data, null, 2);

                if (proto.toLowerCase().includes('briefing') && data.briefing) {
                    const card = document.getElementById('morningBriefingCard');
                    const msgEl = document.getElementById('briefingMessage');
                    const pCount = document.getElementById('bPendingCount');
                    const iCount = document.getElementById('bInProgressCount');
                    const mCount = document.getElementById('bMemoryCount');
                    const fCount = document.getElementById('bFileCount');
                    const pList = document.getElementById('bPendingTasksList');
                    const fList = document.getElementById('bFilesList');

                    if (card) card.style.display = 'block';
                    if (msgEl) msgEl.textContent = data.message || '';
                    if (data.message) speakText(data.message);
                    if (pCount) pCount.textContent = data.briefing.pending_tasks_count;
                    if (iCount) iCount.textContent = data.briefing.in_progress_tasks_count;
                    if (mCount) mCount.textContent = data.briefing.memory_count;
                    if (fCount) fCount.textContent = data.briefing.file_count;

                    if (pList) {
                        const tasks = data.briefing.pending_tasks || [];
                        pList.textContent = tasks.length > 0 ? tasks.join(', ') : 'None';
                    }
                    if (fList) {
                        const files = data.briefing.workspace_files || [];
                        fList.textContent = files.length > 0 ? files.join(', ') : 'None';
                    }
                }

                loadTasks();
                loadMemories();
                loadFiles();
                loadTelemetry();
            } catch (err) {
                if (pre) pre.textContent = 'Error executing protocol: ' + err.message;
            } finally {
                isExecutingProtocol = false;
                if (btn) btn.disabled = false;
            }
        }

        async function inspectVision() {
            const filenameInput = document.getElementById('visionFilename');
            const pre = document.getElementById('visionResultPre');
            if (!filenameInput || !pre) return;
            let filename = filenameInput.value.trim();
            if (!filename || filename === '4' || filename.toLowerCase().includes('not found') || filename.toLowerCase().startsWith('4.')) {
                filename = 'architecture_spec.json';
                filenameInput.value = filename;
            }
            pre.textContent = 'Analyzing blueprint/schema for ' + filename + '...';
            try {
                const res = await fetch('/api/files/read', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filename})
                });
                const data = await res.json();
                if (data.status === 'success') {
                    pre.textContent = `=== VISION & SCHEMA ANALYSIS ===\nFile: ${filename}\nStatus: success\nContent Preview:\n${data.content}`;
                } else {
                    pre.textContent = `=== VISION & SCHEMA ANALYSIS ===\nFile: ${filename}\nStatus: error\nMessage: ${data.message}`;
                }
            } catch (err) {
                pre.textContent = 'Error analyzing file: ' + err.message;
            }
        }

        function speakText(text) {
            const ttsToggle = document.getElementById('ttsToggle');
            if (!ttsToggle || !ttsToggle.checked) return;
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                window.speechSynthesis.speak(utterance);
            }
        }

        function startVoiceInput() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert('Speech Recognition is not supported in this browser. Please use Chrome or Edge.');
                return;
            }
            const recognition = new SpeechRecognition();
            recognition.lang = 'en-US';
            recognition.start();
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                const input = document.getElementById('chatInput');
                if (input) {
                    input.value = transcript;
                    sendChat();
                }
            };
            recognition.onerror = function(event) {
                console.error('Speech recognition error', event.error);
            };
        }

        async function runDemoFlow() {
            try {
                switchTab('chat');
                const messagesDiv = document.getElementById('messages');
                if (messagesDiv) {
                    messagesDiv.innerHTML += `<div class="message assistant" style="background:#0369a1;"><div class="meta">DEMO FLOW</div>Starting 7-Step JARVIS Demo Sequence...</div>`;
                }

                const steps = [
                    "Hello JARVIS, who are you and what can you do?",
                    "Calculate 1428 * 79 + 543",
                    "Remember that our target release date is October 25, 2026.",
                    "What is our target release date?",
                    "Inspect project data file financial_data.csv and summarize top rows.",
                    "Inspect architecture_spec.json",
                    "Create a task: Prepare slide deck and assign priority high.",
                    "List my pending tasks",
                    "What skills do you have?",
                    "Based on current tasks, memory, and workspace, what should I work on next?"
                ];

                for (let i = 0; i < steps.length; i++) {
                    await new Promise(r => setTimeout(r, 800));
                    const input = document.getElementById('chatInput');
                    if (input) {
                        input.value = steps[i];
                        await sendChat();
                    }
                }
            } catch (err) {
                console.error('Error running demo flow:', err);
            }
        }

        function escapeHtml(str) {
            if (str === null || str === undefined) return '';
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        function escapeJsString(str) {
            if (str === null || str === undefined) return '';
            return escapeHtml(String(str)
                .replace(/\\\\/g, "\\\\\\\\")
                .replace(/'/g, "\\\\'")
                .replace(/\\r/g, "\\\\r")
                .replace(/\\n/g, "\\\\n"));
        }

        function setPrompt(text) {
            const input = document.getElementById('chatInput');
            if (input) {
                input.value = text;
                input.focus();
            }
        }

        function showToast(message) {
            const toast = document.getElementById('toast');
            if (!toast) return;
            toast.textContent = message;
            toast.style.display = 'block';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        }

        // Global window bindings for cross-platform and mobile webview click reliability
        window.switchTab = switchTab;
        window.sendChat = sendChat;
        window.clearChat = clearChat;
        window.setPrompt = setPrompt;
        window.showToast = showToast;
        window.loadMemories = loadMemories;
        window.saveMemory = saveMemory;
        window.deleteMemory = deleteMemory;
        window.loadTasks = loadTasks;
        window.createTask = createTask;
        window.completeTask = completeTask;
        window.deleteTask = deleteTask;
        window.loadFiles = loadFiles;
        window.viewFile = viewFile;
        window.inspectCsv = inspectCsv;
        window.inspectJson = inspectJson;
        window.loadSkills = loadSkills;
        window.loadContext = loadContext;
        window.executeProtocol = executeProtocol;
        window.inspectVision = inspectVision;
        window.startVoiceInput = startVoiceInput;
        window.uploadFilesFromDevice = uploadFilesFromDevice;
        window.uploadDocument = uploadDocument;
        window.runDemoFlow = runDemoFlow;

        window.onerror = function(msg, url, line) {
            console.error('Browser error:', msg, 'at', url, 'line', line);
            fetch('/api/log', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({level: 'error', message: `${msg} (${url}:${line})`})
            }).catch(() => {});
        };

        document.addEventListener('DOMContentLoaded', () => {
            const sendBtn = document.getElementById('sendBtn');
            if (sendBtn) {
                sendBtn.addEventListener('click', sendChat);
            }
            const clearBtn = document.getElementById('clearBtn');
            if (clearBtn) {
                clearBtn.addEventListener('click', clearChat);
            }
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        sendChat();
                    }
                });
            }
            console.log('JARVIS Nexus UI loaded successfully.');
        });
    </script>
    <div id="toast" style="position: fixed; bottom: 20px; right: 20px; background: var(--card-bg); border: 1px solid var(--accent); color: var(--text-primary); padding: 10px 16px; border-radius: 8px; font-size: 0.85rem; display: none; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.4);"></div>
</body>
</html>
"""


class JarvisDemoHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for JARVIS Nexus Demo UI API and frontend."""

    def handle(self) -> None:
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/health":
            payload = {
                "status": "healthy",
                "service": "jarvis-nexus-nebius",
            }
            payload.update(get_deployment_info())
            self._send_json(payload)
            return

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif path == "/api/status":
            payload = {
                "status": "online",
                "service": "jarvis-nexus-nebius",
                "provider": Config.MODEL_PROVIDER,
                "memories": len(memory_store.list_memories()),
                "tasks": len(task_store.list_tasks()),
                "files": len(file_manager.list_files()),
            }
            payload.update(get_deployment_info())
            self._send_json(payload)

        elif path == "/api/telemetry":
            self._send_json(telemetry_manager.get_telemetry())

        elif path == "/api/audit/export":
            fmt = query.get("format", ["json"])[0].strip().lower()
            if fmt == "json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(audit_manager.export_json().encode("utf-8"))
            elif fmt in ["markdown", "md"]:
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(audit_manager.export_markdown().encode("utf-8"))
            else:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Invalid format '{fmt}'. Supported formats: json, markdown"}).encode("utf-8"))

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
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8"))
        except Exception as exc:
            self._send_json({"error": safe_exception_message(exc)})
            return

        if not isinstance(data, dict):
            self._send_json({"error": "JSON request body must be an object."})
            return

        try:
            self._handle_post(path, data)
        except Exception as exc:
            self._send_json({"error": safe_exception_message(exc)})

    def _handle_post(self, path: str, data: Dict[str, Any]) -> None:
        if path == "/api/chat":
            msg = data.get("message", "")
            persona = data.get("persona", "default")

            # Configure persona system prompt
            if persona == "codearchitect":
                agent.set_system_prompt("You are JARVIS Nexus @CodeArchitect, an expert software architecture and code review AI assistant powered by NVIDIA Nemotron.")
            elif persona == "datascientist":
                agent.set_system_prompt("You are JARVIS Nexus @DataScientist, an expert data analysis and CSV statistical intelligence assistant powered by NVIDIA Nemotron.")
            elif persona == "devopsengineer":
                agent.set_system_prompt("You are JARVIS Nexus @DevOpsEngineer, an expert deployment, security hardening, and task automation assistant powered by NVIDIA Nemotron.")
            else:
                agent.set_system_prompt("You are JARVIS Nexus, an advanced AI assistant built for the Nebius x NVIDIA Global AI Hackathon 2026.")

            print("\n================ CHAT SESSION START ================")
            print(f"[Persona]: {persona}")
            print(f"[User Message]: {redact_secrets(str(msg))}")
            if not msg:
                self._send_json({"response": "Please provide a message.", "tool_activity": []})
                return

            response_text = agent.chat(str(msg))
            tool_activity = [{"tool": t} for t in agent.get_last_tools_used()]

            print(f"[JARVIS Response]: {redact_secrets(str(response_text))}")
            print(f"[Tools Used]: {[t['tool'] for t in tool_activity]}")
            print("================== CHAT SESSION END ==================\n")

            telemetry_manager.record_request(len(response_text.split()) * 2)

            audit_manager.record_event("chat", str(msg), {"persona": persona, "tools_used": [t['tool'] for t in tool_activity]}, status="success")

            self._send_json({
                "response": response_text,
                "tool_activity": tool_activity
            })

        elif path == "/api/protocols":
            proto = data.get("protocol", "")
            res = protocol_engine.execute_protocol(str(proto))
            telemetry_manager.record_request(100)
            audit_manager.record_event("protocol", str(proto), {"result": res}, status="success" if res.get("status") != "error" else "error")
            self._send_json(res)

        elif path == "/api/memories":
            key = data.get("key", "")
            value = data.get("value", "")
            category = data.get("category", "general")
            success = memory_store.save_memory(str(key), str(value), str(category))
            self._send_json({"success": success})

        elif path == "/api/tasks":
            title = data.get("title", "")
            description = data.get("description", "")
            priority = data.get("priority", "medium")
            status = data.get("status", "pending")
            task_id = task_store.create_task(title=str(title), description=str(description), priority=str(priority), status=str(status))
            self._send_json({"task_id": task_id})

        elif path == "/api/tasks/complete":
            task_id = data.get("id")
            success = task_store.complete_task(int(task_id)) if task_id else False
            self._send_json({"success": success})

        elif path == "/api/files/read":
            filename = data.get("filename", "")
            res = file_manager.read_file(str(filename))
            self._send_json(res)

        elif path == "/api/files/inspect_csv":
            filename = data.get("filename", "")
            res = file_manager.inspect_csv(str(filename))
            self._send_json(res)

        elif path == "/api/files/inspect_json":
            filename = data.get("filename", "")
            res = file_manager.inspect_json(str(filename))
            self._send_json(res)

        elif path == "/api/files/create":
            filename = data.get("filename", "").strip()
            content = data.get("content", "")
            if not filename:
                self._send_json({"status": "error", "message": "Filename is required."})
                return
            try:
                success = file_manager.write_file(filename, content)
                if success:
                    self._send_json({"status": "success", "filename": filename})
                else:
                    self._send_json({"status": "error", "message": "Failed to write file."})
            except Exception as e:
                self._send_json({"status": "error", "message": safe_exception_message(e)})

        elif path == "/api/log":
            level = str(data.get("level", "info"))[:20]
            message = redact_secrets(str(data.get("message", "")))[:500]
            print(f"[BROWSER {level.upper()}] {message}")
            self._send_json({"logged": True})

        else:
            self.send_response(404)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

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
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"Not Found")

    def _send_json(self, data: Any) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        """Log HTTP requests and session activity with timestamps."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [API] {format % args}")


def run_server(port: int = 8000, background: bool = False) -> Optional[HTTPServer]:
    """Run the JARVIS Nexus Demo UI HTTP server."""
    server = HTTPServer(("0.0.0.0", port), JarvisDemoHTTPHandler)
    if background:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        server._server_thread = thread
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
