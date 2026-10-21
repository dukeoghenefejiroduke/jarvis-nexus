# JARVIS Nexus — Hackathon Submission

> **Event:** Nebius x NVIDIA Global AI Hackathon 2026

## 1. Project Title
**JARVIS Nexus: Advanced Model-Driven AI Assistant & Autonomous Task Intelligence Framework**

## 2. One-Line Tagline
An enterprise-grade, offline-capable modular AI assistant powered by NVIDIA Nemotron via Nebius Token Factory, featuring persistent memory, tool calling, file intelligence, and secure agent workflows.

## 3. Short Description
JARVIS Nexus bridges the gap between static LLM chats and autonomous local execution. Designed for robust offline operation and cloud scalability, JARVIS integrates a model-driven agent reasoning loop with SQLite persistent memory, secure workspace file inspection, task automation, modular skills, and a responsive mobile-first Web UI. It supports dual model providers: an offline mock simulator and a production Nebius Token Factory adapter configured for NVIDIA Nemotron.

## 4. Problem
Traditional AI assistants lack reliable offline continuity, struggle with secure local workspace interaction, lose context across sessions, and require heavy cloud dependencies or complex deployment stacks that are cumbersome to run on edge devices like Android/Termux.

## 5. Solution
JARVIS Nexus provides a lightweight, secure, modular AI framework that runs seamlessly offline or in the cloud. It features strict workspace isolation, bounded tool execution, deterministic memory scoring, persistent task management, and a touch-friendly dashboard accessible on any local device.

## 6. Key Features
- **Model-Driven Agent Loop & Self-Correction**: Autonomous multi-step tool execution with automated error self-healing feedback loops and iteration bounds.
- **SQLite FTS5 Structured Memory**: High-performance full-text search with BM25 relevance ranking across project, identity, and preference categories.
- **Persistent Task & Workflow Management**: Full task lifecycle tracking with priorities and statuses.
- **Secure File & Data Intelligence**: Safe workspace containment with path traversal defense, symlink protection, CSV/JSON analysis, pre-seeded sample files, and **direct device file uploads** from local computer storage.
- **Multi-Agent Personas & Skills**: Extensible skill registry and instant persona switching (`@CodeArchitect`, `@DataScientist`, `@DevOpsEngineer`).
- **MCU Cinematic Capabilities**: Realtime device telemetry HUD (CPU utilization, RAM RSS, core temperature), system protocols (`reset_session`, `workspace_audit`, `system_diagnostics`), and browser voice synthesis (TTS) & speech recognition.
- **Advanced Context Management**: Intelligent prompt assembly combining memories, tasks, files, and skills with budget controls.
- **Production Security**: Automated secret redaction (`[REDACTED]`) and configuration validation.
- **Mobile-Friendly Web UI**: Built entirely on Python's standard library (`http.server`) for fast, zero-dependency local deployment.

## 7. Technical Architecture
Built in clean Python 3.14 using standard library primitives and lightweight SQLite databases. Fully modular design separating agent reasoning, tool execution, storage, and model provider adapters (`MockModelProvider` & `NebiusProvider`).

## 8. Nebius Usage
- Configured via OpenAI-compatible API adapter (`NebiusProvider`) pointing to Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`).
- Handles chat completions, system prompts, and native tool-calling schemas.
- *Status Note:* Live API execution, Nemotron inference, and agent tool-calling workflows have been successfully verified through Nebius Token Factory.

## 9. NVIDIA Model Usage
- Configured for **NVIDIA Nemotron** (`nvidia/Nemotron-3_5-Lightning`) via Nebius Token Factory for high-speed reasoning and tool orchestration.

## 10. Agentic Capabilities
JARVIS autonomously inspects user prompts, decides when to invoke tools (calculator, memory save/recall, CSV analysis, task creation, project context aggregation), processes tool results, and delivers synthesized natural-language answers.

## 11. Security
- Strict workspace file containment.
- Path traversal & absolute path rejection.
- Secret redaction utilities scrubbing API keys and tokens.
- Bounded tool execution preventing infinite loops and flood attacks.

## 12. Offline Capabilities
Fully functional offline via `MODEL_PROVIDER=mock`, allowing developers and judges to run all 143 unit/hardening tests and the Web UI instantly without internet access, API keys, or billing.

## 13. Demo Flow
1. Start Web UI (`PYTHONPATH=. python demo_ui.py`).
2. Open `http://127.0.0.1:8000`.
3. Test chat, calculations, memory persistence, CSV inspection, task creation, and project context.
4. Click **🚀 Demo Flow** for the automated 7-step showcase.

## 14. Future Improvements
- Expand WebSocket support for real-time streaming tokens.
- Add multi-agent collaboration channels.
- Implement advanced vector search for large document corpuses.
