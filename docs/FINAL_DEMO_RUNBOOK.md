# JARVIS Nexus — Final Demo Runbook

This runbook outlines the exact sequence, timing, narration, and screen presentation for the 3-minute JARVIS Nexus demo.

---

## Demo Timing & Sequence (0:00 – 3:00)

### 0:00 – 0:15 | Introduction
- **Action:** Open terminal, launch Web UI with `PYTHONPATH=. python demo_ui.py`, and open browser at `http://127.0.0.1:8000`.
- **What to Say:** "Meet JARVIS Nexus: an offline-first, mobile-friendly AI agent and workspace intelligence hub powered by local mock models and ready for enterprise deployment with Nebius Token Factory and NVIDIA Nemotron."
- **What Appears on Screen:** Terminal starting FastAPI/Streamlit/gradio or custom Web UI server; browser displaying clean, responsive JARVIS chat interface.

### 0:15 – 0:35 | JARVIS Conversation
- **Action:** Type in chat: *"Hello JARVIS, who are you and what can you do?"*
- **What to Say:** "JARVIS acts as an autonomous engineering assistant with structured tool-calling, memory persistence, secure file management, and task tracking."
- **What Appears on Screen:** Instant conversational reply from JARVIS outlining its capabilities.

### 0:35 – 0:55 | Calculator / Tool Calling
- **Action:** Type in chat: *"Calculate 1428 * 79 + 543"*
- **What to Say:** "JARVIS seamlessly integrates tool execution for deterministic computation without hallucination."
- **What Appears on Screen:** Tool execution block showing arguments (`expression: 1428 * 79 + 543`) and precise result (`113355`).

### 0:55 – 1:20 | Memory Save + Recall
- **Action:** Type: *"Remember that our target release date is October 25, 2026."* Then type: *"When is our target release date?"*
- **What to Say:** "JARVIS maintains persistent SQLite memory across sessions, allowing it to retain facts, preferences, and project milestones."
- **What Appears on Screen:** Memory save confirmation, followed by instant and accurate recall of the release date.

### 1:20 – 1:45 | CSV Inspection
- **Action:** Click files tab or prompt: *"Inspect project data/sample.csv and summarize top rows."*
- **What to Say:** "Using secure sandboxed file tools, JARVIS inspects local workspace files, CSVs, and documents with rigorous security boundaries."
- **What Appears on Screen:** File contents preview and summarized analysis of the CSV dataset.

### 1:45 – 2:05 | Task Creation
- **Action:** Type: *"Create a task: Prepare hackathon slide deck and assign priority high."*
- **What to Say:** "JARVIS includes a built-in task manager to track deliverables, statuses, and priorities."
- **What Appears on Screen:** Task created success message with ID, title, and priority badge.

### 2:05 – 2:25 | Context-Aware "What Should I Work On Next?"
- **Action:** Type: *"Based on current tasks, memory, and workspace, what should I work on next?"*
- **What to Say:** "By aggregating context across files, memory, and active tasks, JARVIS provides holistic engineering recommendations."
- **What Appears on Screen:** Comprehensive context synthesis suggesting high-priority next actions.

### 2:25 – 2:40 | Skills & Workspace Overview
- **Action:** Click skills tab or show workspace dashboard.
- **What to Say:** "JARVIS supports extensible skills and sandboxed workspaces ensuring secure local operations."
- **What Appears on Screen:** List of registered skills (calculator, file reader, memory, tasks) and secure workspace folder overview.

### 2:40 – 3:00 | Architecture & Nebius / NVIDIA Explanation
- **Action:** Briefly switch to documentation (`docs/ARCHITECTURE.md`) or architecture view.
- **What to Say:** "Built with modular Python architecture, JARVIS runs entirely offline using Mock models for development, and is fully configured for Nebius Token Factory and NVIDIA Nemotron lightning-fast inference for production. Thank you!"
- **What Appears on Screen:** Architecture summary showing Model Provider abstraction (`MockModelProvider` / `NebiusProvider`), security hardening, and storage layers.

---

## Emergency Offline Demo (Failure Recovery Plan)

If any unexpected hiccup occurs during the live demonstration, follow these emergency recovery steps:

1. **If Web UI does not load or browser disconnects:**
   - *Recovery:* Terminate the terminal process (`Ctrl+C`) and restart instantly with `MODEL_PROVIDER=mock PYTHONPATH=. python demo_ui.py`.
   - *Backup Script:* Run the automated CLI demo script: `PYTHONPATH=. python demo_nebius_e2e.py` or individual demo scripts (`python demo_tasks.py`, `python demo_memory.py`, `python demo_ui.py`).

2. **If a tool call fails or returns unexpected output:**
   - *Recovery:* Refresh the web page or type a direct fallback command (`/reset` or re-send message). The mock provider has deterministic fallbacks for calculator, memory, and file tools.

3. **If terminal process stops:**
   - *Recovery:* Keep a backup terminal window pre-positioned in the `jarvis-nexus` directory with the launch command ready to press Enter.

4. **Guaranteed Offline Safety:**
   - JARVIS Nexus is designed with `MODEL_PROVIDER=mock` as default. No network connection or external API key is ever required for the demo, ensuring 100% reliability under conference Wi-Fi or offline conditions.
