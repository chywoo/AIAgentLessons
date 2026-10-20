import asyncio
import time
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from incident.agents import collect_tool_sources, collect_usage
from incident.schemas import ActionPlan, MetricsFinding, RunbookFinding


class IncidentState(TypedDict):
    incident_id: str
    service: str
    description: str

    metrics_result: NotRequired[dict]
    runbook_result: NotRequired[dict]
    verified_sources: NotRequired[list[str]]
    action_plan: NotRequired[dict]

    status: NotRequired[str]
    approved: NotRequired[bool]
    execution_result: NotRequired[str]
    final_report: NotRequired[dict]


class IncidentWorkflow:
    def __init__(self, metrics_agent, runbook_agent):
        self.metrics_agent = metrics_agent
        self.runbook_agent = runbook_agent

    async def investigate_metrics(self, state: IncidentState) -> dict:
        started = time.perf_counter()

        try:
            result = await asyncio.wait_for(
                self.metrics_agent.ainvoke(
                    {
                        "messages": [{
                            "role": "user",
                            "content": (
                                f"Service: {state['service']}\n"
                                f"Incident: {state['description']}\n"
                                "Investigate metrics and logs."
                            ),
                        }]
                    },
                    config={"recursion_limit": 16},
                ),
                timeout=90,
            )

            finding = MetricsFinding.model_validate(result["structured_response"])
            sources, tools_used = collect_tool_sources(result["messages"])

            return {
                "metrics_result": {
                    "status": "success",
                    "finding": finding.model_dump(),
                    "verified_ids": sorted(set(finding.evidence_ids) & sources),
                    "tools_used": sorted(tools_used),
                    "usage": collect_usage(result["messages"]),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            }

        except Exception as exc:
            return {
                "metrics_result": {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "verified_ids": [],
                    "tools_used": [],
                }
            }

    async def investigate_runbooks(self, state: IncidentState) -> dict:
        started = time.perf_counter()

        try:
            result = await asyncio.wait_for(
                self.runbook_agent.ainvoke(
                    {
                        "messages": [{
                            "role": "user",
                            "content": (
                                f"Service: {state['service']}\n"
                                f"Incident: {state['description']}\n"
                                "Find relevant operational procedures."
                            ),
                        }]
                    },
                    config={"recursion_limit": 12},
                ),
                timeout=90,
            )

            finding = RunbookFinding.model_validate(result["structured_response"])
            sources, tools_used = collect_tool_sources(result["messages"])

            return {
                "runbook_result": {
                    "status": "success",
                    "finding": finding.model_dump(),
                    "verified_ids": sorted(set(finding.runbook_ids) & sources),
                    "tools_used": sorted(tools_used),
                    "usage": collect_usage(result["messages"]),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            }

        except Exception as exc:
            return {
                "runbook_result": {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "verified_ids": [],
                    "tools_used": [],
                }
            }

    def policy_gate(self, state: IncidentState) -> dict:
        metrics = state.get("metrics_result", {})
        runbook = state.get("runbook_result", {})

        metric_ids = set(metrics.get("verified_ids", []))
        runbook_ids = set(runbook.get("verified_ids", []))

        required_tools = {"query_metrics", "search_logs"}
        used_metrics_tools = set(metrics.get("tools_used", []))

        has_metric = any(
            item.startswith("METRIC-") for item in metric_ids
        )
        has_log = any(
            item.startswith("LOG-") for item in metric_ids
        )
        has_runbook = bool(runbook_ids)
        queried_required_tools = required_tools <= used_metrics_tools

        sufficient = (
                metrics.get("status") == "success"
                and runbook.get("status") == "success"
                and queried_required_tools
                and has_metric
                and has_log
                and has_runbook
        )

        verified = sorted(metric_ids | runbook_ids)

        if not sufficient:
            return {
                "verified_sources": verified,
                "status": "insufficient_evidence",
                "execution_result": "No remediation was performed.",
            }

        finding = RunbookFinding.model_validate(
            runbook["finding"]
        )

        plan = ActionPlan(
            action=finding.recommended_action,
            target_service=state["service"],
            rationale=finding.rationale,
        )

        return {
            "verified_sources": verified,
            "action_plan": plan.model_dump(),
            "status": (
                "no_action" if plan.action == "no_action"
                else "awaiting_approval"
            ),
        }

    def route_policy(self, state: IncidentState) -> str:
        if state["status"] == "awaiting_approval":
            return "approval"
        return "finalize"

    def request_approval(self, state: IncidentState) -> dict:
        plan = ActionPlan.model_validate(state["action_plan"])

        decision = interrupt({
            "incident_id": state["incident_id"],
            "service": state["service"],
            "action_plan": plan.model_dump(),
            "verified_sources": state["verified_sources"],
            "question": "Approve this simulated action?",
        })

        if not isinstance(decision, dict):
            raise ValueError("Invalid approval response")

        if type(decision.get("approved")) is not bool:
            raise ValueError("'approved' must be a boolean")

        if decision.get("incident_id") != state["incident_id"]:
            raise ValueError("Incident ID mismatch")

        if decision.get("action") != plan.action:
            raise ValueError("Approved action does not match proposal")

        return {
            "approved": decision["approved"],
            "status": ("approved" if decision["approved"] else "rejected"),
        }

    def route_approval(self, state: IncidentState) -> str:
        return "execute" if state["approved"] else "reject"

    def execute_simulated(self, state: IncidentState) -> dict:
        plan = ActionPlan.model_validate(state["action_plan"])

        if plan.target_service != state["service"]:
            raise ValueError("Action target mismatch")

        return {
            "status": "simulated",
            "execution_result": (
                f"SIMULATED: {plan.action} for {plan.target_service}. "
                "No real infrastructure was changed."
            ),
        }

    def reject(self, state: IncidentState) -> dict:
        return {
            "status": "rejected",
            "execution_result": "Action rejected. No change made.",
        }

    def finalize(self, state: IncidentState) -> dict:
        metrics = state.get("metrics_result", {})
        runbook = state.get("runbook_result", {})

        report = {
            "incident_id": state["incident_id"],
            "service": state["service"],
            "status": state["status"],
            "metrics": metrics.get("finding"),
            "runbook": runbook.get("finding"),
            "verified_sources": state.get("verified_sources", []),
            "action_plan": state.get("action_plan"),
            "approved": state.get("approved"),
            "execution_result": state.get("execution_result", "No action performed."),
            "observability": {
                "metrics_agent": {
                    "latency_ms": metrics.get("latency_ms"),
                    "usage": metrics.get("usage"),
                    "tools_used": metrics.get("tools_used"),
                },
                "runbook_agent": {
                    "latency_ms": runbook.get("latency_ms"),
                    "usage": runbook.get("usage"),
                    "tools_used": runbook.get("tools_used"),
                },
            },
        }

        return {"final_report": report}

    def build(self, checkpointer):
        builder = StateGraph(IncidentState)

        builder.add_node("metrics", self.investigate_metrics)
        builder.add_node("runbooks", self.investigate_runbooks)
        builder.add_node("policy", self.policy_gate)
        builder.add_node("approval", self.request_approval)
        builder.add_node("execute", self.execute_simulated)
        builder.add_node("reject", self.reject)
        builder.add_node("finalize", self.finalize)

        builder.add_edge(START, "metrics")
        builder.add_edge(START, "runbooks")

        builder.add_edge(
            ["metrics", "runbooks"],
            "policy",
        )

        builder.add_conditional_edges(
            "policy",
            self.route_policy,
            {
                "approval": "approval",
                "finalize": "finalize",
            },
        )

        builder.add_conditional_edges(
            "approval",
            self.route_approval,
            {
                "execute": "execute",
                "reject": "reject",
            },
        )

        builder.add_edge("execute", "finalize")
        builder.add_edge("reject", "finalize")
        builder.add_edge("finalize", END)

        return builder.compile(checkpointer=checkpointer)
