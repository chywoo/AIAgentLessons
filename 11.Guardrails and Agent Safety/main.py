import sys

sys.path.append("..")
from config import AgentConfig


from agent import HumanApprovalAgent


def main():
    conf = AgentConfig()
    print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

    agent = HumanApprovalAgent(conf)

    print("HITL System")
    print("Type 'exit' to quit.")

    while True:
        text = input("\nYou> ").strip()

        if not text:
            continue

        if text.lower() in {"exit", "quit", }:
            break

        try:
            agent.run(text)
        except Exception as e:
            print(f"[Error] {e}")


if __name__ == "__main__":
    main()
