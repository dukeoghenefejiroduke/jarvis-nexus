"""Unit tests for JARVIS Nexus model-driven Agent architecture (Milestone 4)."""

import os
import tempfile
import unittest
from jarvis_nexus.agent import Agent
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.models import MockModelProvider, ModelResponse, ToolCall


class TestModelDrivenAgent(unittest.TestCase):
    """Test suite for model-driven agent architecture, tool loops, and natural responses."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_agent_m4.db")
        self.memory = MemoryStore(db_path=self.db_path)
        self.model = MockModelProvider()
        self.agent = Agent(model_provider=self.model, memory_store=self.memory)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_normal_conversation_without_tools(self) -> None:
        response = self.agent.chat("Hello JARVIS")
        self.assertIn("I understand", response)
        self.assertEqual(len(self.agent.get_history()), 2)

    def test_calculator_tool_call(self) -> None:
        response = self.agent.chat("Calculate 15 * 6")
        self.assertEqual(response, "15 * 6 = 90")

    def test_current_time_tool_call(self) -> None:
        response = self.agent.chat("What time is it?")
        self.assertTrue(response.startswith("It is currently"))

    def test_saving_and_retrieving_memory(self) -> None:
        save_res = self.agent.chat("Remember that my name is Duke")
        self.assertIn("remember", save_res.lower())

        get_res = self.agent.chat("What is my name?")
        self.assertIn("Duke", get_res)

    def test_max_iteration_protection(self) -> None:
        class InfiniteToolProvider(MockModelProvider):
            def generate(self, messages, system_prompt, tools=None):
                return ModelResponse(content=None, tool_calls=[ToolCall(id="inf_1", name="get_current_time", arguments={})])

        agent_inf = Agent(model_provider=InfiniteToolProvider(), memory_store=self.memory, max_iterations=3)
        response = agent_inf.chat("Loop test")
        self.assertIn("maximum reasoning iterations", response)

    def test_persistence_across_agent_instances(self) -> None:
        agent_1 = Agent(memory_store=self.memory)
        agent_1.chat("Remember that my project is Nexus")

        agent_2 = Agent(memory_store=self.memory)
        res = agent_2.chat("Search memory project")
        self.assertIn("Nexus", res)


if __name__ == "__main__":
    unittest.main()
