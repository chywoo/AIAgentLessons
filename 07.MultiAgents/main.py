import sys
import traceback
from builtins import MemoryError

sys.path.append("..")
from config import AgentConfig
from multi_agent import ManagerAgent

conf = AgentConfig()
print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

agent = ManagerAgent(conf)

print("Planning AI Agent")
print("Type 'exit' to quit.")
print()

while True:

    user_input = input("You> ").strip()

    if not user_input:
        continue

    if user_input.lower() in {
        "exit",
        "quit",
    }:
        break

    try:
        answer = agent.run(user_input)
        print(f"Agent > {answer}")

    except Exception as e:
        print(f"[Error] {e}")
        traceback.print_exc()

    print()
