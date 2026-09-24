from dataclasses import dataclass, field
import json

from config import AgentConfig
from openai import OpenAI
from tools import TOOL_SCHEMAS
from tools import TOOLS


class SimpleAgent:
    def __init__(self, config: AgentConfig, max_steps:int = 1000):
        self.config = config
        self.model = self.config.model
        self.max_steps = max_steps
        self.client = OpenAI(api_key=config.api_key, base_url=config.api_base)

    def _execute_tool(self, too_name:str, arguments: str) -> str:
        tool = TOOLS.get(too_name)

        if tool is None:
            print(f"[Agent] Tool {too_name} not found")
            return f"Unkown tool: {too_name}"

        print(f"[Agent] Tool selected: {too_name}")

        try:
            args = json.loads(arguments)
            print(f"[Agent] Arguments: {arguments}")
            result = tool(**args)
            print(f"[Tool] Observation:\n{result}")
            return str(result)
        except json.decoder.JSONDecodeError as e:
            return f"Invalid tool arguments: {arguments} with {e}"
        except Exception as e:
            return f"Tool execution error: {e}"

    def run(self, prompt:str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI agents. "
                    "Use tools whenever they are useful. "
                    "Do not perform arithmetic mentally when the "
                    "calculator tool can be used. Answer in plain text. "
                    "Don't use Markdown notation"
                ),
            },
            {
                "role": "user",
                "content": prompt
            },
        ]

        for steps in range(1, self.max_steps + 1):
            print("=" * 80)
            print(f"Agent Step {steps}")
            print("=" * 80)

            self._print_messages(messages)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
            )

            res_msg = response.choices[0].message

            if not res_msg.tool_calls:
                return res_msg.content

            messages.append(res_msg.to_dict())

            for call in res_msg.tool_calls:
                tool_name = call.function.name
                args = call.function.arguments

                result = self._execute_tool(tool_name, args)

                messages.append( {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result)
                })

        raise RuntimeError(
            f"Agent execeeded max_steps={self.max_steps} times"
        )

    def _print_messages(self, messages):
        print("\n--- Current Agent State ---")

        for i, message in enumerate(messages):
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get("content")

                print(f"[{i}] role={role}")
                print(f"    content={content}")

            else:
                print(f"[{i}] role={message.role}")

                if message.content:
                    print(f"    content={message.content}")

                if message.tool_calls:
                    for call in message.tool_calls:
                        print(
                            f"    tool_call="
                            f"{call.function.name}"
                            f"({call.function.arguments})"
                        )