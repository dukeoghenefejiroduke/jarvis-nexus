# JARVIS Nexus — Final Screenshot Plan

This document defines the screenshot plan for hackathon submission documentation, README badges, and Devpost presentation.

---

## Screenshot Specifications

### 1. Main JARVIS Chat Interface
- **Screen to Show:** Web UI main chat view (`http://127.0.0.1:8000`).
- **Action to Perform:** Send greeting and receive welcome message from JARVIS.
- **Visible Information:** Clean mobile-friendly chat UI, user bubble, JARVIS assistant bubble, active model status (`MockModelProvider` / `nebius`).
- **What NOT to Show:** No API keys, passwords, or personal account details.

### 2. Tool Execution (Calculator / Code)
- **Screen to Show:** Chat window with active tool call output.
- **Action to Perform:** Ask JARVIS to evaluate a complex math expression (`1428 * 79 + 543`).
- **Visible Information:** Tool invocation block (`calculator`), input arguments, and precise output (`113355`).
- **What NOT to Show:** Terminal debug logs or stack traces.

### 3. Memory Persistence
- **Screen to Show:** Chat window demonstrating memory save and recall.
- **Action to Perform:** Store project preference ("Release date is Oct 25") and query it back.
- **Visible Information:** Memory store confirmation (`Stored memory successfully`) and successful recall response.
- **What NOT to Show:** Local absolute file paths containing usernames (`/data/data/...`).

### 4. CSV & File Intelligence
- **Screen to Show:** Workspace file inspection and summary view.
- **Action to Perform:** Prompt JARVIS to inspect `data/sample.csv`.
- **Visible Information:** Structured table summary or key metrics extracted from the CSV file.
- **What NOT to Show:** Unrelated sensitive local files.

### 5. Task Management
- **Screen to Show:** Task tracker view or chat task creation response.
- **Action to Perform:** Create a high-priority task ("Prepare hackathon slide deck").
- **Visible Information:** Task ID, title, status (`pending`), and priority (`high`).
- **What NOT to Show:** Completed internal test tasks.

### 6. Context-Aware Synthesis ("What Next?")
- **Screen to Show:** Chat response to "What should I work on next?".
- **Action to Perform:** Query JARVIS for holistic recommendations across files, tasks, and memory.
- **Visible Information:** Synthesized recommendations prioritized by urgency and relevance.
- **What NOT to Show:** Stale or conflicting debug state.

### 7. Skills Registry
- **Screen to Show:** Skills panel or list of loaded tools/skills.
- **Action to Perform:** Inspect available built-in skills (`calculator`, `file_reader`, `memory_store`, `task_manager`).
- **Visible Information:** Skill names, descriptions, and parameter schemas.
- **What NOT to Show:** Incomplete or experimental stubs.

### 8. System Architecture Overview
- **Screen to Show:** `docs/ARCHITECTURE.md` rendered view or diagram.
- **Action to Perform:** Highlight modular layers (UI → Agent → Context → Tools → Memory → Tasks → Files → Skills → Model Provider).
- **Visible Information:** Clean architectural boxes and data flow arrows.
- **What NOT to Show:** Outdated legacy designs.

### 9. GitHub Repository & Structure
- **Screen to Show:** File tree of `jarvis-nexus` repository on GitHub or local file explorer.
- **Action to Perform:** Display project structure (`jarvis_nexus/`, `tests/`, `docs/`, `demo_ui.py`, `README.md`, `LICENSE`).
- **Visible Information:** Organized Python modules and documentation.
- **What NOT to Show:** `.env` files, `.git/` internal objects, or SQLite cache files.

### 10. Live Nebius / NVIDIA Nemotron (Conditional)
- **Screen to Show:** Configuration and test output when `MODEL_PROVIDER=nebius` is configured with a verified key.
- **Action to Perform:** Run `demo_nebius_e2e.py` (showing mock fallback or live response if verified).
- **Visible Information:** Nebius Token Factory endpoint URL and NVIDIA Nemotron model header.
- **What NOT to Show:** **NEVER show actual API keys (`sk-...` or `nebius-...`) in screenshots.** Crop or blur credential fields if config is displayed.
