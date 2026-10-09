import os
import sys

sys.path.append("..")
from config import AgentConfig
from hitl_graph import HITLAgent
from langgraph.types import Command, interrupt


def main():
    conf = AgentConfig()
    agent = HITLAgent(conf)

    config = {"configurable": {"thread_id": "day18-test-001"}}

    initial_state = {
        "messages": [
            {
                "role": "system",
                "content": ("You are a tool-using agent. "
                            "Use at most one tool call "
                            "per response. "
                            "Some actions require "
                            "human approval. "
                            "If an action is rejected, "
                            "do not attempt to bypass "
                            "the rejection."),
            },
            {
                "role": "user",
                "content": "Delete sales.txt.",
            },
        ]
    }

    # Check if interrupted
    result = (agent.graph.invoke(initial_state, config=config, ))
    interrupts = result.get(
        "__interrupt__",
        []
    )

    if interrupts:
        interrupt_info = interrupts[0]

        print()
        print("APPROVAL REQUIRED")
        print(interrupt_info.value)
        yn = input("Do you really want to continue? [y/n]")
        if yn.lower() == "y":
            # must pass the same thread_id for consistency.
            result = agent.graph.invoke(Command(resume=True), config=config)
        else:
            result = agent.graph.invoke(Command(resume=False), config=config)
    print(result)


if __name__ == "__main__":
    main()
