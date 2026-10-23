# JARVIS Nexus — System Architecture & Design

## 1. System Overview

JARVIS Nexus is an advanced, modular AI assistant framework engineered for reliable local execution and high-performance cloud intelligence. It combines a model-driven agent reasoning loop with structured SQLite persistent memory, a secure workspace file manager, task and workflow automation, modular skill discovery, advanced context management, production-grade security hardening, and a responsive mobile-friendly Web UI.

---

## 2. High-Level Data Flow

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

## 3. Core Architectural Modules

### 3.1 Model Provider Abstraction (`models.py`, `nebius_provider.py`, `gemini_provider.py`)
- Defines `BaseModelProvider`, structured `ChatMessage`, `ToolCall`, and `ModelResponse`.
- **`MockModelProvider`**: Provides robust, rule-based offline simulation of chat, calculations, tool requests, memory management, CSV/JSON analysis, and project context queries without external network dependency or billing.
- **`NebiusProvider`**: OpenAI-compatible adapter pointing to Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`).
- **`GeminiProvider`**: OpenAI-compatible adapter pointing to Google Gemini API (`https://generativelanguage.googleapis.com/v1beta/openai/`).

### 3.2 Agent Core & Reasoning Loop (`agent.py`)
- Coordinates multi-step tool execution loops up to a configurable maximum iteration count (default: 10).
- Automatically manages conversation history, integrates context prompts, detects model tool requests, executes tools securely via `ToolRegistry`, feeds results back to the model, and returns natural-language responses.

### 3.3 Tool Registry & Execution Engine (`tools.py`, `task_tools.py`, `file_tools.py`, `context_tools.py`, `skill_tools.py`)
- Registers and executes tools with parameter validation.
- Implements bounded outputs, fault isolation (tool exceptions do not crash the agent), and safety guards against recursive infinite loops.

### 3.4 Persistent Structured Memory (`memory.py`)
- SQLite-backed storage (`data/jarvis_memory.db`) managing key-value memories with categories (`project`, `identity`, `preference`, `fact`, `task`, `general`).
- Supports atomic upserts, queries, searches, and cross-instance memory persistence.

### 3.5 Persistent Task System (`tasks.py`)
- SQLite-backed task store (`data/jarvis_tasks.db`) tracking tasks with statuses (`pending`, `in_progress`, `completed`, `cancelled`) and priorities (`low`, `medium`, `high`, `critical`).
- Validates state transitions and maintains persistent timestamps across agent sessions.

### 3.6 Secure Workspace File Intelligence (`file_manager.py`)
- Enforces strict workspace containment (`data/workspace`), absolute path rejection, path traversal prevention (`../`), symbolic link escape protection, and 10 MB file size limits.
- Supports reading `.txt`, `.md`, `.csv`, `.json` with structured CSV inspection (rows, columns, numeric stats) and search snippet collection.

### 3.7 Modular Skills System (`skills/`)
- Encapsulates distinct assistant capabilities (`Data Analyst`, `Project Assistant`, `Research Assistant`, `Productivity Assistant`) with dynamic discovery and deduplication via `SkillRegistry`.

### 3.8 Advanced Context Intelligence (`context.py`)
- Central orchestration layer combining conversation history, relevant long-term memories (via deterministic word overlap and category scoring), pending tasks, workspace files, and modular skills into a concise, budgeted prompt.

### 3.9 Security Hardening & Secret Redaction (`security.py`, `config.py`)
- Automatic redaction of API keys, Bearer tokens, and credentials (`[REDACTED]`) from logs and exception messages.
- Environment validation ensuring secure configuration handling without exposing secrets.

### 3.10 Demo Web UI (`demo_ui.py`)
- Lightweight HTTP server built entirely on Python's standard library (`http.server`) serving a responsive, touch-optimized dashboard for chat, memory management, task management, file inspection, skills, and project context.
