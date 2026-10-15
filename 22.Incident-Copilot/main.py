import os
import sys
import uuid

import config
from langchain_openai import ChatOpenAI
from langgraph.types import Command

from incident.agents import create_analysis_chain, create_research_agent
from incident.workflow import IncidentWorkflow

sys.path.append("..")
from config import AgentConfig

def main():
    conf = AgentConfig()
    print("- BASE URL: ", conf.api_base)
    print("- MODEL: ", conf.model)

    model = ChatOpenAI(
        model=conf.model,
        base_url=conf.api_base,
        api_key=conf.api_key,
        reasoning_effort=conf.reasoning_effort,
        timeout=60,
        max_retries=2,
    )

    agent = create_research_agent(model)
    analysis_chain = create_analysis_chain(model)
    graph = IncidentWorkflow(agent, analysis_chain).build()

    incident_id = f"INC-{uuid.uuid4().hex[:8]}"
    task_config = {"configurable": {"thread_id": incident_id}}

    result = graph.invoke({
        "incident_id": incident_id,
        "service": "checkout-api",
        "description": (
            "Checkout API p95 latency increased from 180ms to 2400ms, "
            "and HTTP 503 responses are increasing."
        ),
    }, config=task_config)

    if "__interrupt__" in result:
        request = result["__interrupt__"][0].value

        print("\n=== APPROVAL REQUEST ===")
        print("Incident:", request["incident_id"])
        print("Analysis:", request["analysis"])
        print("Proposed action:", request["proposed_action"])

        response = input("\nApprove simulated remediation? (yes/no): ").strip().lower()
        approved = response == "yes"

        result = graph.invoke(
            Command(resume={"approved": approved}),
            config=task_config,
        )

    print("\n=== FINAL REPORT ===")
    print(result["final_report"])


if __name__ == "__main__":
    main()