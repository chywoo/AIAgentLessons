import os
import sys

sys.path.append("..")
from config import AgentConfig

from graph_agent import (
    LangGraphAgent
)


def main():
    conf = AgentConfig()
    agent = LangGraphAgent(conf)

    question = """
Read sales.txt.
Find the 2025 annual sales.
Calculate 15% of it.
Then count the number of characters
in the calculated result.
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
