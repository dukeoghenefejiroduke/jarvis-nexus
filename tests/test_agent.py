"""Unit tests for JARVIS Nexus model-driven Agent architecture (Milestone 4)."""

import os
import tempfile
import unittest
from jarvis_nexus.agent import Agent
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.models import MockModelProvider, ModelResponse, ToolCall, ChatMessage


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

    def test_mock_csv_filename_extraction(self) -> None:
        tools = self.agent.tool_registry.get_definitions()
        response = self.model.generate(
            [ChatMessage(role="user", content="Inspect project data file financial_data.csv and summarize top rows.")],
            system_prompt="",
            tools=tools
        )
        self.assertTrue(response.tool_calls)
        self.assertEqual(response.tool_calls[0].name, "inspect_csv")
        self.assertEqual(response.tool_calls[0].arguments.get("filename"), "financial_data.csv")

    def test_mock_identity_and_capabilities_response(self) -> None:
        response = self.agent.chat("Hello JARVIS, who are you and what can you do?")
        self.assertIn("JARVIS Nexus", response)
        self.assertIn("modular skills", response.lower())

    def test_mock_what_is_my_memory_query(self) -> None:
        self.agent.chat("Remember that my demo project is called JARVIS Nexus.")
        res = self.agent.chat("What is my demo project called?")
        self.assertIn("JARVIS Nexus", res)

    def test_mock_create_task_high_priority(self) -> None:
        tools = self.agent.tool_registry.get_definitions()
        response = self.model.generate(
            [ChatMessage(role="user", content="Create a high-priority task called Prepare the JARVIS demo.")],
            system_prompt="",
            tools=tools
        )
        self.assertTrue(response.tool_calls)
        self.assertEqual(response.tool_calls[0].name, "create_task")
        self.assertEqual(response.tool_calls[0].arguments.get("priority"), "high")
        self.assertIn("Prepare the JARVIS demo", response.tool_calls[0].arguments.get("title"))

    def test_mock_qloo_trending_trigger(self) -> None:
        tools = self.agent.tool_registry.get_definitions()
        response = self.model.generate(
            [ChatMessage(role="user", content="What are the trending movies right now?")],
            system_prompt="",
            tools=tools
        )
        self.assertTrue(response.tool_calls)
        self.assertEqual(response.tool_calls[0].name, "qloo_trending")
        self.assertEqual(response.tool_calls[0].arguments.get("category"), "movie")

    def test_mock_qloo_latest_movie_trigger(self) -> None:
        tools = self.agent.tool_registry.get_definitions()
        response = self.model.generate(
            [ChatMessage(role="user", content="Recommend the latest movie")],
            system_prompt="",
            tools=tools
        )
        self.assertTrue(response.tool_calls)
        self.assertEqual(response.tool_calls[0].name, "qloo_trending")
        self.assertEqual(response.tool_calls[0].arguments.get("category"), "movie")

    def test_mock_qloo_recommend_trigger(self) -> None:
        tools = self.agent.tool_registry.get_definitions()
        response = self.model.generate(
            [ChatMessage(role="user", content="Recommend artists similar to Burna Boy")],
            system_prompt="",
            tools=tools
        )
        self.assertTrue(response.tool_calls)
        self.assertEqual(response.tool_calls[0].name, "qloo_recommend")
        self.assertIn("Burna Boy", response.tool_calls[0].arguments.get("query"))


if __name__ == "__main__":
    unittest.main()
