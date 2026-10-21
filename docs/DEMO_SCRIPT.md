# JARVIS Nexus — 3-Minute Demo Script

> **Target Duration:** 2:30 – 2:50  
> **Event:** Nebius x NVIDIA Global AI Hackathon 2026

---

## Script Timeline

| Time | Section | Action & Narrative |
| :--- | :--- | :--- |
| **0:00 – 0:15** | **Introduction** | *"Hello judges! Welcome to the demonstration of **JARVIS Nexus**, an advanced AI assistant framework built for the Nebius x NVIDIA Global AI Hackathon 2026. JARVIS Nexus brings autonomous agentic reasoning, persistent SQLite memory, secure workspace file intelligence, and multi-tool workflows to local and cloud environments."* |
| **0:15 – 0:35** | **Demo UI & Chat** | *"Here we are running the lightweight Web UI dashboard accessible at `http://127.0.0.1:8000`. Let's greet JARVIS: 'Hello JARVIS, please introduce yourself.'"* (Shows instant local response). |
| **0:35 – 0:55** | **Tool Calling** | *"Next, let's test reasoning and tool execution. Asking: 'What is 27 multiplied by 14?' Notice how JARVIS automatically detects the need for calculation, invokes the secure calculator tool, and returns the exact result: 378."* |
| **0:55 – 1:20** | **Persistent Memory** | *"JARVIS features structured persistent memory. Let's teach JARVIS a preference: 'Remember that my favorite project is JARVIS Nexus.' When we ask 'What is my favorite project?', JARVIS queries our SQLite memory store and recalls it instantly."* |
| **1:20 – 1:45** | **File Intelligence** | *"JARVIS can inspect local files securely. Asking: 'Analyze sales.csv and tell me the average price.' JARVIS reads the controlled CSV workspace, computes statistics, and summarizes the rows."* |
| **1:45 – 2:05** | **Task Automation** | *"Let's bridge analysis into productivity. Asking: 'Create a high-priority task to test the final JARVIS demo.' JARVIS creates and persists task #3 in our task database with high priority."* |
| **2:05 – 2:25** | **Project Context** | *"Asking: 'What am I currently working on?' JARVIS invokes its `ContextManager` to synthesize relevant long-term memories, pending tasks, and workspace files into a unified project summary."* |
| **2:25 – 2:45** | **Architecture & Nebius** | *"Under the hood, JARVIS is powered by a clean, modular Python architecture with dual-provider support. It is configured for **NVIDIA Nemotron** via **Nebius Token Factory**, while remaining fully operational offline via our mock provider for instant developer testing."* |
| **2:45 – 3:00** | **Conclusion** | *"Thank you! JARVIS Nexus delivers robust, secure, offline-first agent intelligence ready for production."* |

---

## Ending Variants

### Variant A: Offline / Demo-Safe Ending (Recommended for offline evaluation)
> *"Demonstrating JARVIS Nexus using our robust offline MockModelProvider, running all 143 unit and hardening tests successfully with zero external dependencies, alongside full live cloud support via Nebius Token Factory."*

### Variant B: Live Nebius Ending (To be used after verified cloud API onboarding)
> *"Powered live by NVIDIA Nemotron running on Nebius Token Factory, JARVIS Nexus successfully executed all cloud-backed reasoning and tool-calling flows in real-time."*
