# JARVIS Nexus

> **Nebius x NVIDIA Global AI Hackathon 2026**  
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
1. **Dual Provider Architecture**: Seamlessly switch between local offline simulation (`MockModelProvider`) and cloud intelligence (`NebiusProvider`).
2. **Robust Tool Registry**: Secure calculator, memory search/save, file readers, CSV inspectors, task managers, and project context tools.
3. **Prompt Budgeting & History Trimming**: Automatic conversation pruning preserving system prompts while respecting token budgets.
4. **Zero-Dependency Web UI**: Fast local web server (`demo_ui.py`) accessible at `http://127.0.0.1:8000`.

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
Live API execution is fully implemented and configured in code, but live API testing is currently pending payment card onboarding for Nebius account billing. All local functionality, unit tests, and demos operate fully offline.

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

4. **Run Offline Test Suite (67 tests passing)**:
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
├── tests/               # Comprehensive unit & hardening test suite (67 tests)
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
PYTHONPATH=. python -m unittest discover -s tests
```
*Current baseline: **67 passing tests, 4 skipped**.*

---

## License
MIT License. See [LICENSE](LICENSE).
