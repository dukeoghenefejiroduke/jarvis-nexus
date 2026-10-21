"""Unit tests for JARVIS Nexus model-driven Agent architecture (Milestone 4)."""

import os
import tempfile
import unittest
from jarvis_nexus.agent import Agent
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.models import MockModelProvider, ModelResponse, ToolCall
from jarvis_nexus.tools import ToolRegistry


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
        agent_1 = Agent(model_provider=self.model, memory_store=self.memory)
        agent_1.chat("Remember that my project is Nexus")

        agent_2 = Agent(model_provider=self.model, memory_store=self.memory)
        res = agent_2.chat("Search memory project")
        self.assertIn("Nexus", res)

    def test_memory_saving_and_favorite_project_recall(self) -> None:
        self.agent.chat("Remember that my favorite project is JARVIS Nexus.")
        res = self.agent.chat("What is my favorite project?")
        self.assertIn("JARVIS Nexus", res)

    def test_natural_language_high_priority_task_creation(self) -> None:
        res = self.agent.chat("Create a high-priority task to test the final JARVIS demo.")
        self.assertIn("Created task", res)
        tasks = self.agent.tool_registry.task_store.list_tasks(priority="high")
        self.assertTrue(any("test the final JARVIS demo" in t["title"] for t in tasks))

    def test_csv_average_price_analysis(self) -> None:
        workspace = os.path.join(self.temp_dir.name, "workspace_csv")
        os.makedirs(workspace, exist_ok=True)
        with open(os.path.join(workspace, "sales.csv"), "w", encoding="utf-8") as f:
            f.write("item,price\nWidget,10.00\nGadget,20.00\n")
        from jarvis_nexus.file_manager import FileManager
        from jarvis_nexus.file_tools import register_file_tools
        from jarvis_nexus.tools import ToolRegistry
        fm = FileManager(workspace_dir=workspace)
        tr = ToolRegistry(memory_store=self.memory)
        register_file_tools(tr, file_manager=fm)
        agent_csv = Agent(model_provider=self.model, memory_store=self.memory, tool_registry=tr)

        res = agent_csv.chat("Analyze sales.csv and tell me the average price.")
        self.assertIn("15.00", res)

    def test_current_work_context_empty_and_populated(self) -> None:
        from jarvis_nexus.tasks import TaskStore
        from jarvis_nexus.tools import ToolRegistry
        from jarvis_nexus.context import ContextManager
        empty_mem = MemoryStore(db_path=os.path.join(self.temp_dir.name, "empty_mem.db"))
        empty_task = TaskStore(db_path=os.path.join(self.temp_dir.name, "empty_task.db"))
        empty_ctx = ContextManager(memory_store=empty_mem, task_store=empty_task)
        empty_reg = ToolRegistry(memory_store=empty_mem, task_store=empty_task, context_manager=empty_ctx)
        agent_empty = Agent(model_provider=self.model, memory_store=empty_mem, tool_registry=empty_reg)

        res_empty = agent_empty.chat("What am I currently working on?")
        self.assertIn("couldn't find any saved memories or pending tasks", res_empty)

        agent_empty.chat("Remember that my project is Alexa+ Assistant.")
        res_pop = agent_empty.chat("What am I currently working on?")
        self.assertIn("Alexa+ Assistant", res_pop)

    def test_task_priority_persistence(self) -> None:
        self.agent.chat("Create a high-priority task to deploy hackathon submission.")
        tasks = self.agent.tool_registry.task_store.list_tasks(priority="high")
        self.assertTrue(len(tasks) > 0)
        self.assertEqual(tasks[0]["priority"], "high")

    def test_agent_introduction(self) -> None:
        res = self.agent.chat("Hello JARVIS, please introduce yourself.")
        self.assertIn("JARVIS Nexus", res)
        self.assertIn("developer workflows", res)

    def test_list_my_tasks_variations(self) -> None:
        # Create a sample task first
        self.agent.tool_registry.task_store.create_task(title="Sample Hackathon Task", priority="high")
        for query in ["List my tasks", "list tasks", "show my tasks", "what are my tasks?", "show pending tasks"]:
            res = self.agent.chat(query)
            self.assertIn("Sample Hackathon Task", res)

    def test_unrelated_request_does_not_trigger_tasks(self) -> None:
        res = self.agent.chat("What is the weather today?")
        self.assertNotIn("matching tasks", res)
        self.assertNotIn("Sample Hackathon Task", res)

    def test_file_listing_and_memory_search(self) -> None:
        from jarvis_nexus.file_manager import FileManager
        from jarvis_nexus.file_tools import register_file_tools
        workspace = os.path.join(self.temp_dir.name, "workspace_files")
        os.makedirs(workspace, exist_ok=True)
        with open(os.path.join(workspace, "test_agent_file.txt"), "w", encoding="utf-8") as f:
            f.write("content")
        fm = FileManager(workspace_dir=workspace)
        tr = ToolRegistry(memory_store=self.memory)
        register_file_tools(tr, file_manager=fm)
        agent_files = Agent(model_provider=self.model, memory_store=self.memory, tool_registry=tr)

        res_files = agent_files.chat("What files do you have?")
        self.assertIn("test_agent_file.txt", res_files)

        self.agent.chat("Remember that my secret code is 12345.")
        res_mem = self.agent.chat("Search memory secret code")
        self.assertIn("12345", res_mem)

    def test_cumulative_tool_usage_regression(self) -> None:
        """Verify per-request tool usage is not cumulative across consecutive requests."""
        # 1. "List my tasks"
        self.agent.chat("List my tasks")
        tools_1 = self.agent.get_last_tools_used()
        self.assertEqual(tools_1, ["list_tasks"])

        # 2. "Hello JARVIS, please introduce yourself."
        self.agent.chat("Hello JARVIS, please introduce yourself.")
        tools_2 = self.agent.get_last_tools_used()
        self.assertEqual(tools_2, [])
        self.assertNotIn("list_tasks", tools_2)

        # 3. "What is 27 * 14?"
        self.agent.chat("What is 27 * 14?")
        tools_3 = self.agent.get_last_tools_used()
        self.assertEqual(tools_3, ["calculator"])
        self.assertNotIn("list_tasks", tools_3)


if __name__ == "__main__":
    unittest.main()
