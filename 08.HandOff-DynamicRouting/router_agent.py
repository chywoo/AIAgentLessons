import json
from typing import Any
from openai import OpenAI
from config import AgentConfig
from specialist_agent import SpecialistAgent


class RouterAgent:
    def __init__(self, config: AgentConfig):
        self.model = config.model
        self.client = OpenAI(
            base_url=config.api_base,
            api_key=config.api_key,
        )

        self.research_agent = SpecialistAgent(
            name="Research Agent",

            system_prompt=(
                "You are a research specialist. "
                "Find facts from files or long-term memory. "
                "Do not perform unnecessary coding or numeric analysis."
            ),
            model=config.model,
            client=self.client,
            tool_names=[
                "read_file",
                "list_files",
                "search_memory",
            ],
        )

        self.data_agent = SpecialistAgent(
            name="Data Agent",
            system_prompt=(
                "You are a data analysis specialist. "
                "Analyze numeric data and perform calculations. "
                "Use tools when useful."
            ),
            model=config.model,
            client=self.client,
            tool_names=[
                "read_file",
                "calculator",
            ],
        )

        self.coding_agent = SpecialistAgent(
            name="Coding Agent",
            system_prompt=(
                "You are a software engineering specialist. "
                "Help with Python, APIs, debugging, architecture, "
                "and code design. "
                "Explain code clearly."
            ),
            model=config.model,
            client=self.client,
            tool_names=[],
        )

        self.handoff_tools = [
            {
                "type": "function",
                "function": {
                    "name": "handoff_to_research",
                    "description": (
                        "Transfer control to the Research Agent "
                        "for factual research, file inspection, "
                        "or memory lookup."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "reason"
                        ],
                        "additionalProperties": False,
                    },
                },
            },

            {
                "type": "function",
                "function": {
                    "name": "handoff_to_data",
                    "description": (
                        "Transfer control to the Data Agent "
                        "for calculations or data analysis."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "reason"
                        ],
                        "additionalProperties": False,
                    },
                },
            },

            {
                "type": "function",
                "function": {
                    "name": "handoff_to_coding",
                    "description": (
                        "Transfer control to the Coding Agent "
                        "for software engineering or debugging."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "reason"
                        ],
                        "additionalProperties": False,
                    },
                },
            },
        ]

    def perform_handoff(self, handoff_name: str, messages: list[dict]) -> str:
        specialist_messages = self.build_handoff_messages(messages)

        if handoff_name == "handoff_to_research":
            return self.research_agent.run(specialist_messages)

        if handoff_name == "handoff_to_data":
            return self.data_agent.run(specialist_messages)

        if handoff_name == "handoff_to_coding":
            return self.coding_agent.run(specialist_messages)

        raise RuntimeError(f"Unknown handoff: {handoff_name}")

    def run(self, user_input: str, ) -> str:
        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "You are a routing agent. "
                    "Your job is to decide which specialist "
                    "should handle the user's request.\n\n"

                    "Research Agent:\n"
                    "- factual research\n"
                    "- file lookup\n"
                    "- memory retrieval\n\n"

                    "Data Agent:\n"
                    "- calculations\n"
                    "- numeric analysis\n"
                    "- data interpretation\n\n"

                    "Coding Agent:\n"
                    "- programming\n"
                    "- debugging\n"
                    "- APIs\n"
                    "- software architecture\n\n"

                    "Choose exactly one specialist. "
                    "Do not answer the user yourself."
                ),
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.handoff_tools,
            # Force the router to choose one.
            tool_choice="auto",
            reasoning_effort="none")

        message = response.choices[0].message
        messages.append(message.to_dict())

        if not message.tool_calls:
            raise RuntimeError("Router did not select a specialist.")

        #
        # For this example,
        # allow exactly one handoff.
        #
        handoff = message.tool_calls[0]

        print(f"[Router] Selected: {handoff.function.name}")
        print(f"[Router] Reason: {handoff.function.arguments}")

        return self.perform_handoff(handoff.function.name, messages, )

    def build_handoff_messages(self, messages: list[dict]) -> list[dict]:
        """
        When hand-off message to another agent, don't pass metadata.
        Just pass conversations.
        """
        result = []

        for message in messages:
            #
            # Skip Router system prompt
            #
            if (message.get("role") == "system"):
                continue

            #
            # Skill Router의 handoff tool-call message too.
            #
            if (message.get("role") == "assistant" and message.get("tool_calls")):
                continue

            result.append(message)

        return result
