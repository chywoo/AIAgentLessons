from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver

from incident.agents import research_incident
from incident.schemas import IncidentState


class IncidentWorkflow:
    def __init__(self, agent, analysis_chain):
        self.agent = agent
        self.analysis_chain = analysis_chain

    def investigate(self, state: IncidentState) -> dict:
        research, tools_used = research_incident(
            self.agent,
            state["service"],
            state["description"],
        )

        investigation = [
            (
                "system",
                "Convert the incident research into a structured incident analysis. " \
                "Use only evidence in the research. Do not invent facts. " \
                "Recommend a conservative action requiring human approval."
            ),
            (
                "human",
                f"Service: {state['service']}\n" \
                f"Incident: {state['description']}\n" \
                f"Research:\n{research}\n" \
                f"Tools used: {tools_used}"
            ),
        ]
        analysis = self.analysis_chain.invoke(investigation)

        return {
            "analysis": analysis.model_dump(),
            "proposed_action": analysis.recommended_action,
        }

    def request_approval(self, state: IncidentState) -> dict:
        decision = interrupt({
            "incident_id": state["incident_id"],
            "service": state["service"],
            "analysis": state["analysis"],
            "proposed_action": state["proposed_action"],
            "question": "Approve the proposed remediation?",
        })

        # Approval must be an explicit boolean, not a truthy string.
        if not isinstance(decision, dict) or type(decision.get("approved")) is not bool:
            raise ValueError("Approval response must contain a boolean 'approved'")

        return {"approved": decision["approved"]}

    def route_approval(self, state: IncidentState) -> str:
        return "remediate" if state["approved"] else "rejected"

    def remediate(self, state: IncidentState) -> dict:
        # Training-only simulation. No infrastructure changes.
        return {
            "execution_result": (
                "SIMULATED ONLY: Approved remediation was recorded. "
                "No real infrastructure changes were made."
            )
        }

    def rejected(self, state: IncidentState) -> dict:
        return {
            "execution_result": (
                "Remediation rejected. No action was performed."
            )
        }

    def report(self, state: IncidentState) -> dict:
        analysis = state["analysis"]
        report = (
            f"Incident: {state['incident_id']}\n"
            f"Service: {state['service']}\n"
            f"Summary: {analysis['summary']}\n"
            f"Probable cause: {analysis['probable_cause']}\n"
            f"Confidence: {analysis['confidence']}\n"
            f"Evidence: {analysis['evidence']}\n"
            f"Proposed action: {state['proposed_action']}\n"
            f"Approved: {state['approved']}\n"
            f"Result: {state['execution_result']}"
        )

        return {"final_report": report}

    def build(self, checkpointer=None):
        builder = StateGraph(IncidentState)

        builder.add_node("investigate", self.investigate)
        builder.add_node("approval", self.request_approval)
        builder.add_node("remediate", self.remediate)
        builder.add_node("rejected", self.rejected)
        builder.add_node("report", self.report)

        builder.add_edge(START, "investigate")
        builder.add_edge("investigate", "approval")

        builder.add_conditional_edges(
            "approval",
            self.route_approval,
            {"remediate": "remediate", "rejected": "rejected"},
        )

        builder.add_edge("remediate", "report")
        builder.add_edge("rejected", "report")
        builder.add_edge("report", END)

        return builder.compile(checkpointer=checkpointer or InMemorySaver())