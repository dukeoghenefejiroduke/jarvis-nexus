# JARVIS Nexus — Agent Lifecycle

This document defines the agent task execution lifecycle.

| Stage | JARVIS Nexus responsibility |
|---|---|
| PLAN | Analyze the requested change and identify affected components |
| CREATE | Generate or modify implementation artifacts |
| VERIFY | Run tests, syntax checks, and quality validation |
| PACKAGE | Build and prepare reproducible release artifacts |
| SECURE | Run security checks and identify vulnerabilities |
| RELEASE | Publish an approved artifact |
| CONFIGURE | Apply deployment/runtime configuration |
| MONITOR | Validate runtime health and collect operational evidence |
| GOVERN | Record decisions, failures, evidence, and final lifecycle status |

## Target Operating Mode

The target is automated execution:

Intent
→ planning
→ implementation
→ verification
→ security
→ packaging
→ release
→ configuration
→ monitoring
→ governance
