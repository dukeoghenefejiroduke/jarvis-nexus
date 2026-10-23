"""Model-driven Agent architecture for JARVIS Nexus."""

import json
from typing import Any, Dict, List, Optional
from jarvis_nexus.models import BaseModelProvider, get_model_provider, ModelResponse, ChatMessage
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tools import ToolRegistry


DEFAULT_TOOL_INSTRUCTIONS = (
    " You have access to executable tools for calculations, persistent memory, file inspection, "
    "CSV and JSON analysis, task management, skill discovery, and project context. "
    "IMPORTANT TOOL RULES: When a request requires a calculation, call the calculator tool. "
    "When asked to inspect a CSV file, call inspect_csv. When asked to inspect a JSON file, "
    "call inspect_json. When asked to create a task, call create_task. When asked to list tasks, "
    "call list_tasks. When asked what skills are available, call list_skills. "
    "Use the exact tool names provided in the available tool definitions; never invent tool names "
    "or claim a tool is unavailable without trying the supplied tool. Use tool results as the source "
    "of truth. For requests about remembered information, use memory tools rather than guessing. "
    "After tools return results, explain the findings clearly and accurately. When presenting CSV or "
    "dataset inspection results, ALWAYS format them as clean, structured Markdown tables (tabular form) "
    "for metrics, column statistics, and sample rows rather than bullet points or prose paragraphs. "
    "Never claim an action succeeded unless the tool result confirms success."
)


def get_persona_prompt(persona: str) -> str:
    """Return comprehensive system prompt including identity and tool rules for given persona."""
    base = "You are JARVIS Nexus, an advanced modular AI assistant."
    p_lower = (persona or "default").lower()
    if "codearchitect" in p_lower:
        base = "You are JARVIS Nexus @CodeArchitect, an expert software architecture and code review AI assistant."
    elif "datascientist" in p_lower:
        base = "You are JARVIS Nexus @DataScientist, an expert data analysis and CSV statistical intelligence assistant."
    elif "devopsengineer" in p_lower:
        base = "You are JARVIS Nexus @DevOpsEngineer, an expert deployment, security hardening, and task automation assistant."
    return base + DEFAULT_TOOL_INSTRUCTIONS


class Agent:
    """Model-driven JARVIS Nexus AI Agent coordinating conversation, memory, and tools."""

    def __init__(
        self,
        model_provider: Optional[BaseModelProvider] = None,
        memory_store: Optional[MemoryStore] = None,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
        context_manager: Optional[Any] = None
    ) -> None:
        self.model_provider = model_provider or get_model_provider()
        self.memory_store = memory_store or MemoryStore()
        self.tool_registry = tool_registry or ToolRegistry(memory_store=self.memory_store, context_manager=context_manager)
        
        self.system_prompt = system_prompt or get_persona_prompt("default")
        self.messages: List[ChatMessage] = []
        self.last_tools_used: List[str] = []
        self.max_iterations = max_iterations

    def set_system_prompt(self, prompt: str) -> None:
        """Update the system prompt."""
        self.system_prompt = prompt

    def get_last_tools_used(self) -> List[str]:
        """Return list of tool names executed during the most recent chat request."""
        return self.last_tools_used

    def add_message(self, role: str, content: str, tool_calls: Optional[List[Any]] = None, tool_call_id: Optional[str] = None) -> None:
        """Add a structured chat message to conversation history."""
        self.messages.append(
            ChatMessage(
                role=role,
                content=content,
                tool_calls=tool_calls or [],
                tool_call_id=tool_call_id
            )
        )

    def get_history(self) -> List[ChatMessage]:
        """Return conversation history."""
        return self.messages

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages = []

    def chat(self, user_message: str) -> str:
        """Process a user message through model-driven tool execution loop and return final response."""
        self.add_message("user", user_message)
        self.last_tools_used = []
        
        tool_defs = self.tool_registry.get_definitions()
        iteration = 0

        try:
            while iteration < self.max_iterations:
                iteration += 1
                
                # Trim history if context_manager is available
                active_messages = self.messages
                if self.tool_registry.context_manager and hasattr(self.tool_registry.context_manager, "trim_history"):
                    active_messages = self.tool_registry.context_manager.trim_history(self.messages)

                # Generate response from model provider
                response: ModelResponse = self.model_provider.generate(
                    messages=active_messages,
                    system_prompt=self.system_prompt,
                    tools=tool_defs
                )

                # If model returned tool calls
                if response.tool_calls:
                    # Append assistant message with tool calls
                    self.add_message("assistant", content="", tool_calls=response.tool_calls)

                    for tool_call in response.tool_calls:
                        tool_name = tool_call.name
                        tool_args = tool_call.arguments
                        tool_id = tool_call.id

                        # Record tool execution for this request
                        self.last_tools_used.append(tool_name)

                        # Execute tool
                        try:
                            tool_result = self.tool_registry.execute(tool_name, tool_args)
                        except Exception as tool_err:
                            tool_result = {"error": str(tool_err), "correction_hint": "Please adjust arguments and retry with valid parameters."}
                        
                        # Append tool result message
                        self.add_message(
                            role="tool",
                            content=json.dumps(tool_result),
                            tool_call_id=tool_id
                        )
                        self.messages[-1].name = tool_name

                    # Continue loop to let model process tool results and produce final response
                    continue

                # If model returned final content
                final_content = response.content or "I have completed your request."
                self.add_message("assistant", content=final_content)
                return final_content

            # Exceeded max iterations fallback
            fallback_msg = "I reached the maximum reasoning iterations while processing your request."
            self.add_message("assistant", content=fallback_msg)
            return fallback_msg

        except Exception as e:
            error_msg = f"An error occurred while processing your request: {str(e)}"
            self.add_message("assistant", content=error_msg)
            return error_msg
