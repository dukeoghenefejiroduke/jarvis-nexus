"""Built-in modular skills for JARVIS Nexus."""

from jarvis_nexus.skills.base import Skill
from jarvis_nexus.skills.registry import SkillRegistry


def register_builtin_skills(registry: SkillRegistry) -> None:
    """Register all built-in skills into the SkillRegistry."""

    # 1. Data Analyst Skill
    data_analyst = Skill(
        name="Data Analyst",
        description="Analyze CSV and JSON datasets using file inspection tools to summarize rows, columns, and numeric statistics.",
        version="1.0.0",
        required_tools=["inspect_csv", "inspect_json", "read_file"],
        metadata={"category": "analytics", "domain": "data-science"}
    )
    registry.register_skill(data_analyst)

    # 2. Project Assistant Skill
    project_assistant = Skill(
        name="Project Assistant",
        description="Manage project state by combining persistent memory search and workspace file inspection.",
        version="1.0.0",
        required_tools=["search_memory", "list_memories", "list_files", "read_file"],
        metadata={"category": "productivity", "domain": "project-management"}
    )
    registry.register_skill(project_assistant)

    # 3. Research Assistant Skill
    research_assistant = Skill(
        name="Research Assistant",
        description="Perform structured research workflows by searching workspace files, collecting snippets, and organizing findings into memory.",
        version="1.0.0",
        required_tools=["search_files", "read_file", "save_memory"],
        metadata={"category": "research", "domain": "knowledge-management"}
    )
    registry.register_skill(research_assistant)

    # 4. Productivity Assistant Skill
    productivity_assistant = Skill(
        name="Productivity Assistant",
        description="Assist with user tasks, scheduling checks, math calculations, and remembered preferences.",
        version="1.0.0",
        required_tools=["save_memory", "search_memory", "get_current_time", "calculator"],
        metadata={"category": "productivity", "domain": "task-management"}
    )
    registry.register_skill(productivity_assistant)

    # 5. Cultural Intelligence Specialist Skill
    cultural_specialist = Skill(
        name="Cultural Intelligence Specialist",
        description="Explore cross-category cultural connections, multi-interest taste profiles, explainability, trending insights, and geographic discoveries using Qloo API v2.",
        version="1.0.0",
        required_tools=["qloo_recommend", "qloo_trending", "qloo_geographic", "qloo_compare"],
        metadata={"category": "culture", "domain": "cultural-intelligence"}
    )
    registry.register_skill(cultural_specialist)
