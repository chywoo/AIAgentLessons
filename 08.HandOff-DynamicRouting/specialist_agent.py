import json
from typing import Any
from openai import OpenAI
from tools import TOOLS, TOOL_SCHEMAS
from config import AgentConfig


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

    def execute_tool(self, name: str, arguments: str) -> str:
        if name not in self.tool_names:
            return f"Tool not allowed: {name}"

        tool = TOOLS.get(name)

        if tool is None:
            return f"Unknown tool: {name}"

        try:
            args = json.loads(arguments)
            return str(tool(**args))
        except json.JSONDecodeError as e:
            return f"Invalid arguments: {e}"
        except Exception as e:
            return f"Tool execution error: {e}"


    def run(self, messages: list[dict]) -> str:
        #
        # Add specialist identity
        #
        local_messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            *messages,
        ]

        for step in range(1, self.max_steps + 1):
            kwargs = {
                "model": self.model,
                "messages": local_messages,
            }

            if self.tool_schemas:
                kwargs["tools"] = self.tool_schemas
                kwargs["tool_choice"] = "auto"
                kwargs["reasoning_effort"] = "none"

            response = (self.client.chat.completions.create(**kwargs))
            message = (response.choices[0].message)

            local_messages.append(message.to_dict())

            if not message.tool_calls:
                return (message.content or "")

            for call in message.tool_calls:
                result = self.execute_tool(call.function.name, call.function.arguments, )

                local_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    }
                )

        raise RuntimeError(f"{self.name} exceeded max steps")
