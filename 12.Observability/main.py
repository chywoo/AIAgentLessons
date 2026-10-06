import sys
import json

from agent import ObservableAgent, answer_contains_score
from telemetry import tool_selection_score, get_tool_calls
sys.path.append("..")
from config import AgentConfig

def load_cases(path: str, ):
    with open(path, encoding="utf-8", ) as f:
        return json.load(f)


def main():
    cases = load_cases("eval_cases.json")
    conf = AgentConfig()
    agent = ObservableAgent(conf)
    total = 0.0

    for case in cases:
        print()
        print("=" * 60)
        print(case["id"])
        print("=" * 60)

        answer, trace = agent.run(case["input"])

        tools = [
            span.name
            for span in trace.spans
            if span.span_type == "tool"
        ]

        tool_score = tool_selection_score(case["expected_tools"], tools, )

        answer_score = (
            answer_contains_score(
                answer,
                case[
                    "expected_answer_contains"
                ],
            ))

        score = tool_score * 0.4 + answer_score * 0.6
        total += score

        print(f"Answer score: {answer_score:.2f}")
        print(f"Tool score: {tool_score:.2f}")
        print(f"Final score: {score:.2f}")

    average = total / len(cases)

    print()
    print(f"Average score: {average:.3f}")


if __name__ == "__main__":
    main()
