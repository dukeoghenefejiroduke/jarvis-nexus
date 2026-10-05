"""Tool registrations for skill discovery and inspection in JARVIS Nexus."""

from typing import Any, Dict, List, Optional
from jarvis_nexus.skills.registry import SkillRegistry
from jarvis_nexus.skills.builtin import register_builtin_skills


def register_skill_tools(tool_registry: Any, skill_registry: Optional[SkillRegistry] = None) -> None:
    """Register skill discovery tools into the ToolRegistry."""
    sr = skill_registry or SkillRegistry()
    register_builtin_skills(sr)

    def list_skills() -> Dict[str, Any]:
        """List all available modular skills."""
        skills = sr.list_skills()
        return {"count": len(skills), "skills": skills}

    tool_registry.register(
        name="list_skills",
        description="List all available modular skills and their capabilities.",
        parameters={"type": "object", "properties": {}, "required": []},
        func=list_skills
    )

    def get_skill_info(skill_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific skill."""
        skill = sr.get_skill(skill_name)
        if skill:
            return {
                "status": "found",
                "skill": {
                    "name": skill.name,
                    "description": skill.description,
                    "version": skill.version,
                    "required_tools": skill.required_tools,
                    "metadata": skill.metadata
                }
            }
        return {"status": "not_found", "message": f"Skill '{skill_name}' not found."}

    tool_registry.register(
        name="get_skill_info",
        description="Get detailed information, version, and required tools for a specific skill.",
        parameters={
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Name of the skill to inspect."}
            },
            "required": ["skill_name"]
        },
        func=get_skill_info
    )
