"""Unit tests for JARVIS Nexus Modular Skills System (Milestone 7)."""

import unittest
from jarvis_nexus.skills.base import Skill
from jarvis_nexus.skills.registry import SkillRegistry
from jarvis_nexus.skills.builtin import register_builtin_skills
from jarvis_nexus.skill_tools import register_skill_tools
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.agent import Agent
from jarvis_nexus.models import MockModelProvider


class TestModularSkills(unittest.TestCase):
    """Test suite for Skill abstraction, SkillRegistry, built-in skills, and skill tools."""

    def setUp(self) -> None:
        self.registry = SkillRegistry()

    def test_skill_creation(self) -> None:
        skill = Skill(
            name="Test Skill",
            description="A test skill",
            version="1.1.0",
            required_tools=["calculator"],
            metadata={"domain": "test"}
        )
        self.assertEqual(skill.name, "Test Skill")
        self.assertEqual(skill.version, "1.1.0")
        self.assertIn("calculator", skill.required_tools)

    def test_skill_registration_and_duplicate_prevention(self) -> None:
        skill = Skill(name="Alpha", description="First skill")
        self.registry.register_skill(skill)
        self.assertEqual(self.registry.get_skill("Alpha"), skill)

        # Duplicate registration should raise ValueError
        with self.assertRaises(ValueError):
            self.registry.register_skill(skill)

    def test_skill_removal_and_listing(self) -> None:
        s1 = Skill(name="S1", description="Desc 1")
        s2 = Skill(name="S2", description="Desc 2")
        self.registry.register_skill(s1)
        self.registry.register_skill(s2)

        skills = self.registry.list_skills()
        self.assertEqual(len(skills), 2)

        removed = self.registry.unregister_skill("S1")
        self.assertTrue(removed)
        self.assertIsNull = self.assertIsNone(self.registry.get_skill("S1"))
        self.assertEqual(len(self.registry.list_skills()), 1)

    def test_find_matching_skills(self) -> None:
        s1 = Skill(name="Data Analyst", description="Analyze datasets", required_tools=["inspect_csv"])
        s2 = Skill(name="Writer", description="Write content")
        self.registry.register_skill(s1)
        self.registry.register_skill(s2)

        matches = self.registry.find_matching_skills("dataset")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].name, "Data Analyst")

    def test_builtin_skills_registration(self) -> None:
        register_builtin_skills(self.registry)
        skills = self.registry.list_skills()
        skill_names = {s["name"] for s in skills}

        self.assertIn("Data Analyst", skill_names)
        self.assertIn("Project Assistant", skill_names)
        self.assertIn("Research Assistant", skill_names)
        self.assertIn("Productivity Assistant", skill_names)
        self.assertIn("Cultural Intelligence Specialist", skill_names)

    def test_skill_tools_integration_and_agent(self) -> None:
        tool_reg = ToolRegistry()
        register_skill_tools(tool_reg, skill_registry=self.registry)

        agent = Agent(tool_registry=tool_reg, model_provider=MockModelProvider())

        # Test skill discovery query through agent
        resp = agent.chat("What skills do you have?")
        self.assertIn("Data Analyst", resp)
        self.assertIn("Project Assistant", resp)


if __name__ == "__main__":
    unittest.main()
