# JARVIS Nexus — Devpost Submission Copy

> **Event:** Nebius x NVIDIA Global AI Hackathon 2026

## Project Title
**JARVIS Nexus: Advanced Model-Driven AI Assistant & Autonomous Task Intelligence Framework**

## Inspiration
Modern AI assistant interfaces are often stateless chat boxes disconnected from local developer workflows, persistent memory, and secure workspace files. We wanted to build an enterprise-grade, offline-first assistant framework powered by high-performance cloud intelligence (NVIDIA Nemotron via Nebius Token Factory) that can run seamlessly anywhere—from cloud servers to mobile Android/Termux environments.

## What It Does
JARVIS Nexus is a modular AI assistant that combines:
- A model-driven agent reasoning loop with multi-step tool execution.
- Structured SQLite persistent memory that survives across separate agent instances.
- Secure workspace file inspection (reading `.txt`, `.md`, `.csv`, `.json` with workspace containment and path traversal defense).
- Persistent task and workflow automation with priority queues.
- Modular skill discovery (`Data Analyst`, `Project Assistant`, `Research Assistant`, `Productivity Assistant`).
- Advanced context management combining memories, tasks, files, and skills.
- A zero-dependency mobile-friendly Web UI built with Python's standard library `http.server`.
- Dual-provider support supporting both an offline mock simulator and Nebius Token Factory with NVIDIA Nemotron.

## How We Built It
- **Language**: Python 3.14 (Pure standard library + SQLite).
- **Agent Architecture**: Custom reasoning loop with tool detection, execution bounding, and error resilience.
- **Security**: Secret redaction utilities (`[REDACTED]`), configuration validation, and path sanitization.
- **Web UI**: Single-file responsive HTML/CSS/JS dashboard served via lightweight Python HTTP server.

## Challenges We Ran Overcame
- Ensuring strict workspace isolation and path traversal defense against malicious input.
- Managing database connection lifecycles cleanly to eliminate resource leaks.
- Designing deterministic relevance scoring and prompt budgeting for context intelligence without external vector databases.

## Accomplishments We're Proud Of
- 100% offline functionality with 67 passing unit and hardening tests.
- Zero external web framework dependencies for the Web UI.
- Production-grade security hardening and secret redaction.

## What's Next
- Live token streaming via WebSockets.
- Multi-agent collaboration protocols.
- Advanced vector search embedding integrations.

## Built With
- Python 3.14
- SQLite
- Nebius Token Factory
- NVIDIA Nemotron
- HTML5 / CSS3 / JavaScript
