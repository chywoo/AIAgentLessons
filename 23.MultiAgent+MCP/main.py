import asyncio
import os
import sys
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

from agents import build_supervisor, final_text

sys.path.append("..")
from config import AgentConfig

conf = AgentConfig()


async def main():
    server_path = Path(__file__).with_name("mcp_server.py").resolve()

    client = MultiServerMCPClient({
        "incident": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(server_path)],
        }
    })

    mcp_tools = await client.get_tools()

    print("=== MCP Tools ===")
    for item in mcp_tools:
        print(f"- {item.name}: {item.description}")

    model = ChatOpenAI(
        model=conf.model,
        base_url=conf.api_base,
        api_key=conf.api_key,
        temperature=0,
        timeout=120,
        max_retries=2,
    )

    supervisor = build_supervisor(model, mcp_tools)

    result = await supervisor.ainvoke(
        {
            "messages": [{
                "role": "user",
                "content": (
                    "Investigate checkout-api. "
                    "Users report slow checkout requests and HTTP 503 errors. "
                    "Collect operational evidence, review relevant runbooks, "
                    "and recommend safe next steps."
                ),
            }]
        },
        config={"recursion_limit": 30},
    )

    print("\n=== FINAL REPORT ===")
    print(final_text(result))

    print("\n=== SUPERVISOR TOOL CALLS ===")
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", []):
            print(f"{call['name']}: {call['args']}")


if __name__ == "__main__":
    asyncio.run(main())
