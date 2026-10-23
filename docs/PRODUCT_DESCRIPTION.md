# JARVIS Nexus — Product Overview & Description

## Project Title
**JARVIS Nexus: Advanced Model-Driven AI Assistant & Autonomous Task Intelligence Framework**

## Inspiration
Modern AI assistant interfaces are often stateless chat boxes disconnected from local developer workflows, persistent memory, and secure workspace files. We wanted to build an enterprise-grade, offline-first assistant framework powered by high-performance cloud intelligence (Nebius & Google Gemini) that can run seamlessly anywhere—from cloud servers to mobile Android/Termux environments.

## What It Does
JARVIS Nexus is a modular AI assistant that combines:
- A model-driven agent reasoning loop with multi-step tool execution and automated error self-healing feedback.
- Structured SQLite persistent memory with FTS5 full-text search and BM25 relevance ranking.
- Secure workspace file inspection with pre-seeded sample data and **direct device file uploads** from local computer storage.
- Persistent task and workflow automation with priority queues.
- Multi-agent persona selection (`@CodeArchitect`, `@DataScientist`, `@DevOpsEngineer`) and modular skill discovery.
- MCU cinematic capabilities: Realtime device telemetry HUD (CPU, RAM, Core Temperature), system protocols (`reset_session`, `workspace_audit`, `system_diagnostics`), and browser voice synthesis (TTS) & speech recognition.
- Advanced context management combining memories, tasks, files, and skills.
- A zero-dependency mobile-friendly Web UI built with Python's standard library `http.server`.
- Multi-provider support supporting offline mock simulation, Nebius Token Factory, and Google Gemini API.

## How We Built It
- **Language**: Python (Pure standard library + SQLite).
- **Agent Architecture**: Custom reasoning loop with tool detection, execution bounding, and error resilience.
- **Security**: Secret redaction utilities (`[REDACTED]`), configuration validation, and path sanitization.
- **Web UI**: Single-file responsive HTML/CSS/JS dashboard served via lightweight Python HTTP server.

## Challenges We Overcame
- Ensuring strict workspace isolation and path traversal defense against malicious input.
- Managing database connection lifecycles cleanly to eliminate resource leaks.
- Designing deterministic relevance scoring and prompt budgeting for context intelligence without external vector databases.

## Accomplishments We're Proud Of
- 100% offline functionality with comprehensive unit and hardening tests.
- Zero external web framework dependencies for the Web UI.
- Production-grade security hardening, secret redaction, and SQLite FTS5 search.

## What's Next
- Live token streaming via WebSockets.
- Multi-agent collaboration protocols.
- Advanced vector search embedding integrations.

## Built With
- Python 3.14
- SQLite
- Nebius Token Factory
- Google Gemini API
- HTML5 / CSS3 / JavaScript
