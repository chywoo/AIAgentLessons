import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from langchain.mcp import MCPAdapter
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from incident.agents import build_agents
from incident.rag import build_runbook_tool
from incident.workflow import IncidentWorkflow


@asynccontextmanager
async def open_incident_graph():
    load_dotenv()

    server_path = Path(__file__).with_name(
        "mcp_server.py"
    ).resolve()

    async with MCPAdapter(server_path) as adapter:
        mcp_tools = await adapter.list_tools()

        model = ChatOpenAI(
            model=os.environ["MODEL_NAME"],
            base_url=os.environ["OPENAI_BASE_URL"],
            api_key=os.getenv("OPENAI_API_KEY", "dummy"),
            temperature=0,
            timeout=60,
            max_retries=2,
        )

        runbook_tool = build_runbook_tool()

        metrics_agent, runbook_agent = build_agents(
            model=model,
            mcp_tools=mcp_tools,
            runbook_tool=runbook_tool,
        )

        async with AsyncSqliteSaver.from_conn_string(
            "incident-checkpoints.sqlite"
        ) as checkpointer:
            workflow = IncidentWorkflow(
                metrics_agent=metrics_agent,
                runbook_agent=runbook_agent,
            )

            yield workflow.build(checkpointer)