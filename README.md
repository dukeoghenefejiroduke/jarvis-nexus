# JARVIS Nexus

> An enterprise-grade, offline-capable modular AI assistant framework powered by NVIDIA Nemotron via Nebius Token Factory.

---

## What It Does
JARVIS Nexus is an advanced model-driven AI assistant framework designed for autonomous local execution and high-performance cloud intelligence. It bridges the gap between static LLM chats and practical developer tooling by combining:
- **Model-Driven Agent Loop**: Multi-step tool execution with iteration bounding and fault isolation.
- **Persistent Structured Memory**: SQLite-backed cross-instance memory store categorized by project, identity, and preferences.
- **Persistent Task Automation**: Full task lifecycle tracking with status queues and priority ordering.
- **Secure File & Data Intelligence**: Workspace containment with path traversal defense, symlink protection, and CSV/JSON statistical analysis.
- **Modular Skills System**: Extensible skill registry (`Data Analyst`, `Project Assistant`, `Research Assistant`, `Productivity Assistant`).
- **Advanced Context Management**: Intelligent prompt budgeting combining memories, tasks, files, and skills.
- **Production-Grade Security**: Automated secret redaction (`[REDACTED]`) and strict configuration validation.
- **Mobile-First Web UI**: Zero-dependency responsive dashboard built on Python's standard library (`http.server`).

---

## Why It Matters
Developers need AI assistants that maintain context across sessions, securely inspect local workspaces, automate workflows, and operate reliably even when cloud connectivity or billing access is unavailable. JARVIS Nexus delivers an offline-first architecture that runs instantly on any Python environment (including Android/Termux) while remaining fully ready to scale to cloud intelligence via Nebius Token Factory.

---

## Architecture

```
[User / Web UI Dashboard]
           │
           ▼
     [Agent Core]  <───>  [ContextManager]
           │
           ├──► [MemoryStore] (SQLite)
           ├──► [TaskStore]   (SQLite)
           ├──► [FileManager] (Workspace Isolation)
           └──► [ToolRegistry]
                      │
                      ▼
               [Model Provider]
                ├── MockModelProvider (Offline / Testing)
                └── NebiusProvider (Cloud / OpenAI-Compatible)
                      │
                      ▼
        [Nebius Token Factory API] ──► [NVIDIA Nemotron]
```

---

## Features
1. **Dual Provider Architecture**: Seamlessly switch between local offline simulation (`MockModelProvider`) and cloud intelligence (`NebiusProvider`) powered by NVIDIA Nemotron via Nebius Token Factory.
2. **Autonomous Error Self-Correction Loop**: Agent reasons through tool calls and automatically catches and self-heals from tool exceptions using corrective feedback observations.
3. **SQLite FTS5 Full-Text Search**: Fast SQLite FTS5 full-text memory search with BM25 relevance ranking and multi-category indexing.
4. **Multi-Agent Personas**: Instantly switch agent personas (`@CodeArchitect`, `@DataScientist`, `@DevOpsEngineer`) in the Web UI.
5. **Realtime Device Telemetry HUD**: Live device resource monitoring displaying CPU utilization, RAM RSS, core temperature, and token throughput.
6. **System Protocols & Automated Macros**: Built-in automated workflows for Reset Session (`reset_session`), Workspace Audit (`workspace_audit`), and System Diagnostics (`system_diagnostics`).
7. **Voice Synthesis & Speech Recognition**: Browser-based Text-to-Speech audio feedback and microphone speech input.
8. **Direct Device File Upload**: Select and upload files directly from local computer/device storage into the workspace.
9. **Zero-Dependency Web UI**: Fast responsive dashboard (`demo_ui.py`) accessible at `http://127.0.0.1:8000`.

---

## Main Differentiator: "Analyze My Project"
JARVIS Nexus turns scattered project information into **evidence-backed next actions**:
1. **Context Aggregation**: Automatically gathers available files, pending tasks, and saved memories.
2. **Evidence Separation**: Clearly distinguishes **observed facts** (file counts, task statuses) from **inferences** (recommended next steps) and **unknowns** (uninspected dependencies or external network latency).
3. **Actionable Task Creation**: Allows users to instantly approve and create high-priority tasks derived directly from evidence.

---

## Known Limitations & Honest Disclosures
- **Persistence on Cloud PaaS**: Deployed environments (e.g., Render) may use ephemeral file systems unless persistent storage disks are attached; SQLite databases and workspace files will reset on restart.
- **Model vs. Offline Fallback**: Live tool calling and reasoning depend on Nebius Token Factory connectivity and NVIDIA Nemotron API availability; when offline, JARVIS Nexus transparently falls back to `MockModelProvider`.
- **Speech Recognition**: Browser-based TTS and speech recognition capabilities depend on browser support (Web Speech API).

---

## Security
- **Secret Redaction**: Sanitizes API keys, Bearer tokens, and credentials from all exception traces and logs (`[REDACTED]`).
- **Workspace Containment**: Strict path sanitization (`_sanitize_path`) blocking path traversal (`../`) and absolute paths outside `data/workspace`.
- **Symlink Protection**: Resolves real paths to prevent symlink escaping.
- **File Size Limits**: Enforces 10 MB maximum file limits to prevent denial-of-service.
- **Bounded Execution**: Maximum iteration guards on agent loops.

---

## Offline Mode
JARVIS Nexus operates 100% offline out-of-the-box using the default `MODEL_PROVIDER=mock`. No API keys, internet connection, or billing setup are required for local execution, testing, or running the Web UI.

---

## Demo UI
Launch the interactive web dashboard:
```bash
PYTHONPATH=. python demo_ui.py
```
Open in your browser at: **`http://127.0.0.1:8000`**

---

## Nebius + NVIDIA Integration

### Implemented:
- **`NebiusProvider`**: OpenAI-compatible adapter for Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`).
- **NVIDIA Nemotron Configuration**: Configured for `nvidia/Nemotron-3_5-Lightning`.
- **Verification Script**: `demo_nebius_e2e.py` for comprehensive live verification.

### Status Note:
Live API execution, Nemotron inference, and agent tool-calling workflows have been successfully verified through Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`). Full offline fallback (`MockModelProvider`) is also available for zero-config testing and local development.

---

## Hackathon Relevance
- **Nebius Token Factory**: Utilizes OpenAI-compatible cloud endpoints for high-speed LLM inference.
- **NVIDIA Open-Source Model**: Configured for cutting-edge NVIDIA Nemotron models.
- **Agentic Engineering**: Autonomous tool invocation, multi-step planning, and memory persistence.
- **Edge Readiness**: Lightweight Python implementation optimized for resource-constrained environments (Termux/Android).

---

## Quick Start

1. **Clone & Setup Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```

4. **Run Test Suite (143 passing unit tests)**:
   ```bash
   PYTHONPATH=. python -m unittest discover -s tests
   ```

5. **Launch Web UI**:
   ```bash
   PYTHONPATH=. python demo_ui.py
   ```

---

## Project Structure

```
jarvis-nexus/
├── jarvis_nexus/        # Core Python package (agent, models, memory, tasks, files, context, security)
├── tests/               # Comprehensive unit & hardening test suite (143 tests)
├── docs/                # Architecture, hackathon submission, demo scripts, Devpost copy
├── demo_ui.py           # Polished Web UI & dashboard server
├── demo_context.py      # Context intelligence demo script
├── demo_tasks.py        # Task automation demo script
├── demo_skills.py       # Modular skills demo script
├── demo_files.py        # File intelligence demo script
├── demo_memory.py       # Persistent memory demo script
├── demo_nebius_e2e.py   # Live Nebius verification script
├── requirements.txt     # Python dependencies
├── LICENSE              # MIT License
└── README.md            # Documentation
```

---

## Testing
Run the complete test suite:
```bash
python3 -m pytest tests/
```
*Current baseline: **143 passing unit tests**.*

---

## License
MIT License. See [LICENSE](LICENSE).
