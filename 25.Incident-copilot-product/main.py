import argparse
import asyncio
import json
import uuid

from langgraph.types import Command

from incident.schemas import IncidentInput
from incident.service import open_incident_graph


def show_result(result: dict) -> None:
    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n=== APPROVAL REQUIRED ===")
        print(json.dumps(payload, indent=2))
        print("\nResume with the incident ID above.")
        return

    print("\n=== FINAL REPORT ===")
    print(json.dumps(
        result["final_report"],
        indent=2,
        ensure_ascii=False,
    ))


async def run(args):
    async with open_incident_graph() as graph:
        if args.command == "start":
            incident_id = f"INC-{uuid.uuid4().hex[:10]}"

            incident = IncidentInput(
                incident_id=incident_id,
                service=args.service,
                description=args.description,
            )

            config = {
                "configurable": {
                    "thread_id": incident_id
                }
            }

            print("Incident ID:", incident_id)

            result = await graph.ainvoke(
                incident.model_dump(),
                config=config,
            )

        else:
            config = {
                "configurable": {
                    "thread_id": args.incident_id
                }
            }

            snapshot = await graph.aget_state(config)

            if "approval" not in snapshot.next:
                raise ValueError(
                    "Incident is not waiting for approval."
                )

            plan = snapshot.values["action_plan"]

            result = await graph.ainvoke(
                Command(resume={
                    "approved": args.decision == "approve",
                    "incident_id": args.incident_id,
                    "action": plan["action"],
                }),
                config=config,
            )

        show_result(result)


def parse_args():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    start = commands.add_parser("start")
    start.add_argument("--service", required=True)
    start.add_argument("--description", required=True)

    resume = commands.add_parser("resume")
    resume.add_argument("--incident-id", required=True)
    resume.add_argument(
        "--decision",
        choices=["approve", "reject"],
        required=True,
    )

    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))