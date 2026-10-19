import uuid
import asyncio
import sys
from pathlib import Path
from urllib import request

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

from agents import build_supervisor, final_text

sys.path.append("..")
from config import AgentConfig

conf = AgentConfig()
load_dotenv()


async def run_incident(supervisor, question: str) -> dict:
    request_id = str(uuid.uuid4())

    return await asyncio.wait_for(
        supervisor.ainvoke(
            {
                "messages": [{"role": "user", "content": question}]
            },
            config={
                "recursion_limit": 30,  # Number of LangGraph execution steps.
                "run_name": "incident-invetigation",
                "tags": ["day24", "incident-copilot"],
                "metadata": {
                    "request_id": request_id,
                    "service": "check-api",
                }
            },
        ),
        timeout=180,  # timeout for async call.
    )


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
        timeout=120,
        max_retries=2,
    )

    supervisor = build_supervisor(model, mcp_tools)

    try:
        result = await run_incident(
            supervisor,
            "Investigate check-api latency and HTTP 503 errors.",
        )

        print("\n=== FINAL REPORT ===")
        print(final_text(result))

        print("\n=== SUPERVISOR TOOL CALLS ===")
        for message in result["messages"]:
            for call in getattr(message, "tool_calls", []):
                print(f"{call['name']}: {call['args']}")
    except TimeoutError:
        print("Incdent investigation exceeded the deadline.")
    except Exception as exc:
        print(f"Incdent investigation failed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
