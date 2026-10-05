import sys

sys.path.append("..")
from config import AgentConfig
import asyncio
import os

from parallel_agent import ParallelAgentSystem


async def async_main():
    conf = AgentConfig()
    print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

    agent = ParallelAgentSystem(conf)

    print("Parallel Multi-Agent System")
    print("Type 'exit' to quit.")

    while True:
        text = input("\nYou> ").strip()

        if not text:
            continue

        if text.lower() in {"exit", "quit", }:
            break

        try:
            await agent.run(text)
        except Exception as e:
            print(f"[Error] {e}")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
