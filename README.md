# JARVIS Nexus

> An enterprise-grade, offline-capable modular AI assistant framework powered by high-performance cloud intelligence (Nebius & Google Gemini).

---

## What It Does
JARVIS Nexus is an advanced model-driven AI assistant framework designed for autonomous local execution and high-performance cloud intelligence. It bridges the gap between static LLM chats and practical developer tooling by combining:
- **Model-Driven Agent Loop**: Multi-step tool execution with iteration bounding and fault isolation.
- **Persistent Structured Memory**: SQLite-backed cross-instance memory store categorized by project, identity, and preferences.
- **Persistent Task Automation**: Full task lifecycle tracking with status queues and priority ordering.
- **Secure Workspace File Intelligence**: Workspace containment with path traversal defense, symlink protection, and CSV/JSON statistical analysis.
- **Modular Skills System**: Extensible skill registry (`Data Analyst`, `Project Assistant`, `Research Assistant`, `Productivity Assistant`).
- **Advanced Context Management**: Intelligent prompt budgeting combining memories, tasks, files, and skills.
- **Production-Grade Security**: Automated secret redaction (`[REDACTED]`) and strict configuration validation.
- **Mobile-First Web UI**: Zero-dependency responsive dashboard built on Python's standard library (`http.server`).

---

## Why It Matters
Developers need AI assistants that maintain context across sessions, securely inspect local workspaces, automate workflows, and operate reliably even when cloud connectivity or billing access is unavailable. JARVIS Nexus delivers an offline-first architecture that runs instantly on any Python environment (including Android/Termux) while remaining fully ready to scale to cloud intelligence via Nebius Token Factory or Google Gemini API.

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
                ├── NebiusProvider (Cloud / OpenAI-Compatible)
                └── GeminiProvider (Google Gemini API Fallback)
```

---

## Features
1. **Multi-Provider Architecture**: Seamlessly switch between local offline simulation (`MockModelProvider`), Nebius Token Factory (`NebiusProvider`), and Google Gemini API (`GeminiProvider`).
2. **Autonomous Error Self-Correction Loop**: Agent reasons through tool calls and automatically catches and self-heals from tool exceptions using corrective feedback observations.
3. **SQLite FTS5 Full-Text Search**: Fast SQLite FTS5 full-text memory search with BM25 relevance ranking and multi-category indexing.
4. **Multi-Agent Personas**: Instantly switch agent personas (`@CodeArchitect`, `@DataScientist`, `@DevOpsEngineer`) in the Web UI.
5. **Realtime Device Telemetry HUD**: Live device resource monitoring displaying CPU utilization, RAM RSS, core temperature, and token throughput.
6. **System Protocols & Automated Macros**: Built-in automated workflows for Reset Session (`reset_session`), Workspace Audit (`workspace_audit`), and System Diagnostics (`system_diagnostics`).
7. **Voice Synthesis & Speech Recognition**: Browser-based Text-to-Speech audio feedback and microphone speech input.
8. **Direct Device File Upload**: Select and upload files directly from local computer/device storage into the workspace.
9. **Cultural Intelligence Studio (Qloo Integration)**: Cross-category cultural discovery powered by Qloo API v2 (`https://hackathon.api.qloo.com`) featuring multi-interest taste profiles, explainability, trending/geographic insights, tag exploration, and saved favorites.
10. **Zero-Dependency Web UI**: Fast responsive dashboard (`demo_ui.py`) accessible at `http://127.0.0.1:8000`.

---

## Main Differentiator: "Analyze My Project"
JARVIS Nexus turns scattered project information into **evidence-backed next actions**:
1. **Context Aggregation**: Automatically gathers available files, pending tasks, and saved memories.
2. **Evidence Separation**: Clearly distinguishes **observed facts** (file counts, task statuses) from **inferences** (recommended next steps) and **unknowns** (uninspected dependencies or external network latency).
3. **Actionable Task Creation**: Allows users to instantly approve and create high-priority tasks derived directly from evidence.

---

## Known Limitations & Honest Disclosures
- **Persistence on Cloud PaaS**: Deployed environments (e.g., Render) may use ephemeral file systems unless persistent storage disks are attached; SQLite databases and workspace files will reset on restart.
- **Model vs. Offline Fallback**: Live tool calling and reasoning depend on cloud API connectivity; when offline, JARVIS Nexus transparently falls back to `MockModelProvider` (or Gemini API fallback).
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

## Cloud Provider Integration
- **`NebiusProvider`**: OpenAI-compatible adapter for Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`).
- **`GeminiProvider`**: OpenAI-compatible adapter for Google Gemini API (`https://generativelanguage.googleapis.com/v1beta/openai/`).
- **Automatic Fallback**: If Nebius is unavailable or unconfigured, JARVIS transparently fails over to Google Gemini API (if configured), and finally to `MockModelProvider`.

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

4. **Run Test Suite (Passing Unit Tests)**:
   ```bash
   PYTHONPATH=. python -m pytest tests/
   ```

5. **Launch Web UI**:
   ```bash
   PYTHONPATH=. python demo_ui.py
   ```

---

## Cultural Intelligence Studio (Qloo Integration)
JARVIS Nexus features a robust integration with Qloo API v2 (`https://hackathon.api.qloo.com`) for cross-category cultural intelligence:
- **Configuration**: Set `QLOO_API_KEY` in your local `.env` file (which is git-ignored and never exposed to browser JavaScript or logs).
- **Multi-Interest Taste Profiles**: Combine multiple entity seeds (artists, movies, TV shows, books, brands, destinations, video games) to generate blended cross-category recommendations.
- **Explainability**: Enable `feature.explainability=true` to view transparent affinity reasoning returned by Qloo.
- **Trending & Geographic Insights**: Discover trending entities across categories and filter recommendations by geographic location.
- **Saved Favorites**: Save, view, and manage favorite discoveries persistently across restarts using SQLite (`MemoryStore`).

---

## Project Structure
```
jarvis-nexus/
├── jarvis_nexus/        # Core agent package
│   ├── agent.py         # Autonomous reasoning loop
│   ├── client.py        # Cloud client wrapper
│   ├── config.py        # Environment & validation
│   ├── context.py       # Context assembly & budgeting
│   ├── file_manager.py  # Sandboxed workspace manager
│   ├── memory.py        # SQLite persistent memory
│   ├── models.py        # Model provider factory & mock
│   ├── nebius_provider.py # Nebius Token Factory adapter
│   ├── gemini_provider.py # Google Gemini API adapter
│   ├── tasks.py         # Persistent task automation
│   ├── tools.py         # Tool registry & execution
│   └── skills/          # Modular skill registry
├── tests/               # Comprehensive unit test suite
├── docs/                # Architecture, runbooks & guides
├── demo_ui.py           # Web UI dashboard server
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## License
Distributed under the MIT License. See `LICENSE` for details.
