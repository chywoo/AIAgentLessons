import os
import sys

sys.path.append("..")
from config import AgentConfig

from planning_graph import PlanningGraphAgent


def main():
    conf = AgentConfig()
    agent = PlanningGraphAgent(conf)

    question = """
   Read revenue.txt.

Find the 2025 revenue.

Calculate 20% of it.
    """

    answer = agent.run(
        question
    )

    print()
    print("=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)

    print(answer)


if __name__ == "__main__":
    main()
