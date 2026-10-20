import json
import uuid

import pytest

from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from incident.schemas import MetricsFinding, RunbookFinding
from incident.workflow import IncidentWorkflow


class FakeAgent:
    def __init__(self, finding, tool_messages):
        self.finding = finding
        self.tool_messages = tool_messages

    async def ainvoke(self, input_data, config=None):
        return {
            "messages": self.tool_messages,
            "structured_response": self.finding,
        }


def tool_result(name: str, payload: dict) -> ToolMessage:
    return ToolMessage(
        name=name,
        content=json.dumps(payload),
        tool_call_id=str(uuid.uuid4()),
    )


def build_test_graph(metric_ids=None, runbook_ids=None):
    metric_ids = (
        ["METRIC-001", "LOG-001"]
        if metric_ids is None else metric_ids
    )
    runbook_ids = (
        ["RB-DB-001"]
        if runbook_ids is None else runbook_ids
    )

    metrics_agent = FakeAgent(
        finding=MetricsFinding(
            summary="High latency and HTTP errors",
            probable_cause="Database connection exhaustion",
            evidence_ids=metric_ids,
            confidence="high",
        ),
        tool_messages=[
            tool_result(
                "query_metrics",
                {"source_id": "METRIC-001"},
            ),
            tool_result(
                "search_logs",
                {"source_id": "LOG-001"},
            ),
        ],
    )

    runbook_agent = FakeAgent(
        finding=RunbookFinding(
            summary="Inspect active database connections",
            runbook_ids=runbook_ids,
            recommended_action="inspect_database_connections",
            rationale="Connection pool exhaustion evidence",
        ),
        tool_messages=[
            tool_result(
                "search_runbooks",
                {"items": [{"source_id": "RB-DB-001"}]},
            ),
        ],
    )

    return IncidentWorkflow(
        metrics_agent,
        runbook_agent,
    ).build(InMemorySaver())


def incident_input(incident_id: str) -> dict:
    return {
        "incident_id": incident_id,
        "service": "checkout-api",
        "description": "High API latency and HTTP 503 errors",
    }


@pytest.mark.asyncio
async def test_approval_required():
    graph = build_test_graph()
    incident_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": incident_id}}

    result = await graph.ainvoke(
        incident_input(incident_id),
        config=config,
    )

    assert "__interrupt__" in result
    assert result["status"] == "awaiting_approval"

    snapshot = await graph.aget_state(config)
    assert "approval" in snapshot.next


@pytest.mark.asyncio
async def test_approved_action_is_simulated():
    graph = build_test_graph()
    incident_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": incident_id}}

    await graph.ainvoke(
        incident_input(incident_id),
        config=config,
    )

    result = await graph.ainvoke(
        Command(resume={
            "approved": True,
            "incident_id": incident_id,
            "action": "inspect_database_connections",
        }),
        config=config,
    )

    assert result["status"] == "simulated"
    assert result["approved"] is True
    assert "No real infrastructure was changed" in (
        result["execution_result"]
    )


@pytest.mark.asyncio
async def test_fake_evidence_is_rejected():
    graph = build_test_graph(
        metric_ids=["METRIC-999"],
    )
    incident_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": incident_id}}

    result = await graph.ainvoke(
        incident_input(incident_id),
        config=config,
    )

    assert result["status"] == "insufficient_evidence"
    assert "__interrupt__" not in result
    assert result["approved"] if "approved" in result else True
    assert "METRIC-999" not in result["verified_sources"]
    assert result.get("approved") is not True