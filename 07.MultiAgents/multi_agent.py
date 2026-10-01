import json
from typing import Any

from openai import OpenAI
from config import AgentConfig
from tools import TOOLS, TOOL_SCHEMAS


def select_tool_schemas(
    names: list[str],
) -> list[dict]:

    return [schema for schema in TOOL_SCHEMAS if schema["function"]["name"] in names]


class SpecialistAgent:

    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str,
        client: OpenAI,
        tool_names: list[str] | None = None,
        max_steps: int = 10,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.client = client
        self.max_steps = max_steps

        self.tool_names = tool_names or []
        self.tool_schemas = select_tool_schemas(self.tool_names)

    def execute_tool(self, tool_name: str, arguments: str) -> str:
        # Check if the tool is allowed for this agent
        if tool_name not in self.tool_names:
            return f"Tool not allowed for {self.name}: {tool_name}"

        tool = TOOLS.get(tool_name)

        if tool is None:
            return f"Unknown tool: {tool_name}"

        try:
            args = json.loads(arguments)
        except json.JSONDecodeError as e:
            return f"Invalid arguments: {e}"

        try:
            result = tool(**args)
        except Exception as e:
            return f"Tool execution error: {e}"

        return str(result)

    def run(self, task: str) -> str:
        print()
        print("-" * 60)
        print(f"{self.name} started")
        print("-" * 60)

        print(f"Task: {task}")
        messages: list[dict] = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": task,
            },
        ]

        for step in range(1, self.max_steps + 1):
            response = self.__call_llm(messages, self.tool_schemas)
            message = response.choices[0].message
            messages.append(message.to_dict())

            #
            # Agent finished
            #
            if not message.tool_calls:
                result = message.content or ""
                print(f"[{self.name}] Result:")
                print(result)

                return result

            #
            # Execute tools
            #
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                arguments = tool_call.function.arguments
                print(f"[{self.name}] " f"Tool: {name}")

                result = self.execute_tool(name, arguments)
                print(f"[{self.name}] " f"Observation: {result}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        raise RuntimeError(f"{self.name} exceeded max steps")

    # ---------------------------------------------------------
    # Call LLM with messages or a tool schema
    # ---------------------------------------------------------
    def __call_llm(self, messages, tools=None):
        params = {
            "model": self.model,
            "messages": messages,
            "reasoning_effort": "none",  # gpt-6-luna must be set to "none" for tool calling
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        return self.client.chat.completions.create(**params)


class ManagerAgent:
    def __init__(
        self,
        config: AgentConfig,
        max_steps: int = 10,
    ):

        self.model = config.model
        self.max_steps = max_steps

        self.client = OpenAI(
            base_url=config.api_base,
            api_key=config.api_key,
        )

        self.researcher = SpecialistAgent(
            name="Researcher",
            system_prompt=(
                "You are a research agent. "
                "Find factual information needed for the assigned task. "
                "Use files and memory when useful. "
                "Do not perform unnecessary numeric analysis. Return concise factual findings."
            ),
            model=config.model,
            client=self.client,
            tool_names=[
                "read_file",
                "list_files",
                "search_memory",
            ],
        )

        self.analyst = SpecialistAgent(
            name="Analyst",
            system_prompt=(
                "You are an analysis agent. "
                "Analyze the information provided and perform calculations when required. "
                "Use the calculator tool instead of doing important arithmetic mentally."
            ),
            model=config.model,
            client=self.client,
            tool_names=[
                "calculator",
            ],
        )

        self.reviewer = SpecialistAgent(
            name="Reviewer",
            system_prompt=(
                "You are a review agent. "
                "Check the supplied work for logical, factual, and numerical problems. "
                "Identify errors or missing information. "
                "Do not invent facts."
            ),
            model=config.model,
            client=self.client,
            tool_names=[],
        )

        self.manager_tools = [
            {
                "type": "function",
                "function": {
                    "name": "ask_researcher",
                    "description": (
                        "Delegate factual research or information gathering "
                        "to the Researcher agent."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {"task": {"type": "string"}},
                        "required": ["task"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "ask_analyst",
                    "description": (
                        "Delegate numerical analysis or reasoning to the Analyst agent."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {"task": {"type": "string"}},
                        "required": ["task"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "ask_reviewer",
                    "description": (
                        "Ask the Reviewer agent " "to validate or critique work."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {"task": {"type": "string"}},
                        "required": ["task"],
                        "additionalProperties": False,
                    },
                },
            },
        ]

    def execute_agent_tool(self, name: str, arguments: str) -> str:
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError as e:
            return f"Invalid arguments: {e}"

        task = args.get("task", "")

        if name == "ask_researcher":
            return self.researcher.run(task)

        if name == "ask_analyst":
            return self.analyst.run(task)

        if name == "ask_reviewer":
            return self.reviewer.run(task)

        return f"Unknown agent tool: {name}"

    def run(self, user_input: str) -> str:
        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "You are the manager of a multi-agent team.\n\n"
                    "Available specialists:\n"
                    "- Researcher: factual research\n"
                    "- Analyst: calculations and analysis\n"
                    "- Reviewer: validation and critique\n\n"
                    "Delegate work when a specialist is useful. You are responsible "
                    "for combining their results into the final answer. "
                    "Do not delegate unnecessarily."
                ),
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]

        for step in range(1, self.max_steps + 1):
            print()
            print("=" * 60)
            print(f"Manager Step {step}")
            print("=" * 60)

            response = self.__call_llm(messages, self.manager_tools)

            message = response.choices[0].message
            messages.append(message.to_dict())

            #
            # No agent calls:
            # final answer
            #
            if not message.tool_calls:
                answer = message.content or ""

                print()
                print("FINAL ANSWER")
                print("-" * 60)
                print(answer)

                return answer

            #
            # Delegate to agents
            #
            for call in message.tool_calls:
                agent_name = call.function.name

                print(
                    f"[Manager] Delegating: {agent_name} with task: {call.function.arguments}"
                )
                result = self.execute_agent_tool(
                    agent_name,
                    call.function.arguments,
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    }
                )

        raise RuntimeError("Manager exceeded max steps")

    # ---------------------------------------------------------
    # Call LLM with messages or a tool schema
    # ---------------------------------------------------------
    def __call_llm(self, messages, tools=None):
        params = {
            "model": self.model,
            "messages": messages,
            "reasoning_effort": "none",  # gpt-6-luna must be set to "none" for tool calling
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        return self.client.chat.completions.create(**params)
