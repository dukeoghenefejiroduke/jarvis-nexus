"""SkillRegistry for managing and discovering modular skills in JARVIS Nexus."""

from typing import Any, Dict, List, Optional
from jarvis_nexus.skills.base import Skill


class SkillRegistry:
    """Registry for registering, discovering, and querying modular skills."""

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register_skill(self, skill: Skill) -> None:
        """Register a skill. Prevents duplicate skill registration by name."""
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered in the SkillRegistry.")
        self._skills[skill.name] = skill

    def unregister_skill(self, name: str) -> bool:
        """Unregister a skill by name."""
        if name in self._skills:
            del self._skills[name]
            return True
        return False

    def get_skill(self, name: str) -> Optional[Skill]:
        """Retrieve a registered skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> List[Dict[str, Any]]:
        """List summary information for all registered skills."""
        return [
            {
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "required_tools": s.required_tools,
                "metadata": s.metadata
            }
            for s in self._skills.values()
        ]

    def find_matching_skills(self, query: str) -> List[Skill]:
        """Find skills whose name or description matches a query keyword."""
        q_lower = query.lower()
        matches = []
        for s in self._skills.values():
            if q_lower in s.name.lower() or q_lower in s.description.lower() or any(q_lower in t.lower() for t in s.required_tools):
                matches.append(s)
        return matches
