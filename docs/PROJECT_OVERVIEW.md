# JARVIS Nexus — Project Overview & Architecture Guide

## 1. Project Title
**JARVIS Nexus: Advanced Model-Driven AI Assistant & Autonomous Task Intelligence Framework**

## 2. One-Line Tagline
An enterprise-grade, offline-capable modular AI assistant powered by high-performance cloud intelligence (Nebius & Google Gemini), featuring persistent memory, tool calling, file intelligence, and secure agent workflows.

## 3. Short Description
JARVIS Nexus bridges the gap between static LLM chats and autonomous local execution. Designed for robust offline operation and cloud scalability, JARVIS integrates a model-driven agent reasoning loop with SQLite persistent memory, secure workspace file inspection, task automation, modular skills, and a responsive mobile-first Web UI. It supports multi-provider cloud and offline simulation adapters.

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
Built in clean Python using standard library primitives and lightweight SQLite databases. Fully modular design separating agent reasoning, tool execution, storage, and model provider adapters (`MockModelProvider`, `NebiusProvider`, `GeminiProvider`).

## 8. Cloud Provider Integration
- Configured via OpenAI-compatible API adapters (`NebiusProvider` and `GeminiProvider`) pointing to cloud endpoints.
- Handles chat completions, system prompts, and native tool-calling schemas with automatic failover.

## 9. Agentic Capabilities
JARVIS autonomously inspects user prompts, decides when to invoke tools (calculator, memory save/recall, CSV analysis, task creation, project context aggregation), processes tool results, and delivers synthesized natural-language answers.

## 10. Security
- Strict workspace file containment.
- Path traversal & absolute path rejection.
- Secret redaction utilities scrubbing API keys and tokens.
- Bounded tool execution preventing infinite loops and flood attacks.

## 11. Offline Capabilities
Fully functional offline via `MODEL_PROVIDER=mock`, allowing developers to run all unit and hardening tests and the Web UI instantly without internet access, API keys, or billing.
