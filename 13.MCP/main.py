import sys
import asyncio
import os

from agent import MCPAgent

sys.path.append("..")
from config import AgentConfig


async def main():
    conf = AgentConfig()
    print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

    agent = MCPAgent(conf, mcp_url="http://localhost:8000/mcp")

    answer = await agent.run(
        """
        Read sales.txt.
        Find the 2025 annual sales.
        Calculate 15 percent of that value.
        """
    )

    print()
    print("Final Answer:")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
