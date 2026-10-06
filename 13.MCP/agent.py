import json
from typing import Any

from config import AgentConfig
from mcp import Client
from mcp.types import TextContent

from openai import AsyncOpenAI


class MCPAgent:
    def __init__(self, config: AgentConfig, mcp_url: str, max_steps: int = 1000):
        self.config = config
        self.model = self.config.model
        self.max_steps = max_steps
        self.mcp_url = mcp_url
        self.client = AsyncOpenAI(api_key=config.api_key, base_url=config.api_base)

    def convert_tool(self, tool, ) -> dict:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }

    def tool_result_to_text(self, result, ) -> str:
        texts = []

        for block in result.content:
            if isinstance(block, TextContent, ):
                texts.append(block.text)

        if texts:
            return "\n".join(texts)

        if (result.structured_content is not None):
            return json.dumps(result.structured_content, ensure_ascii=False, )

        return ""

    async def run(self, user_input: str, ) -> str:
        async with Client(self.mcp_url) as mcp_client:

            # -----------------------------------
            # MCP Tool Discovery
            # -----------------------------------
            tool_result = await mcp_client.list_tools()

            chat_tools = [self.convert_tool(tool) for tool in tool_result.tools]

            print("Available MCP tools:")

            for tool in tool_result.tools:
                print(f"- {tool.name}")

            messages: list[dict] = [
                {
                    "role": "system",
                    "content": (
                        "You are a tool-using AI agent. "
                        "Use MCP tools when appropriate."
                    ),
                },
                {
                    "role": "user",
                    "content": user_input,
                },
            ]

            # -----------------------------------
            # Agent Loop
            # -----------------------------------
            for step in range(1, self.max_steps + 1, ):
                print()
                print(f"Agent Step {step}")

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=chat_tools,
                    tool_choice="auto",
                    reasoning_effort="none"
                )

                message = (response.choices[0].message)
                messages.append(message.to_dict())

                # -----------------------------
                # Finished
                # -----------------------------
                if not message.tool_calls:
                    return message.content or ""

                # -----------------------------
                # MCP tool calls
                # -----------------------------
                for call in message.tool_calls:
                    tool_name = (call.function.name)

                    arguments = json.loads(call.function.arguments)

                    print(f"MCP Tool: {tool_name}")
                    print(f"Arguments: {arguments}")

                    result = await mcp_client.call_tool(tool_name, arguments)
                    text = self.tool_result_to_text(result)

                    if result.is_error:
                        text = ("MCP_TOOL_ERROR: " + text)

                    print(f"Result: {text}")

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id":
                                call.id,
                            "content":
                                text,
                        }
                    )

        raise RuntimeError(
            "Agent exceeded maximum steps."
        )
