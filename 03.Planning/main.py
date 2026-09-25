import sys
sys.path.append("..")
from config import AgentConfig
from agent import PlanningAgent

conf = AgentConfig()
print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

agent = PlanningAgent(conf)

print("Planning AI Agent")
print("Type 'exit' to quit.")
print()

while True:

    user_input = input(
        "You> "
    ).strip()

    if not user_input:
        continue

    if user_input.lower() in {
        "exit",
        "quit",
    }:
        break

    try:
        agent.run(user_input)

    except Exception as e:
        print(
            f"[Error] {e}"
        )

    print()