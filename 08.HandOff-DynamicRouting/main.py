import sys

sys.path.append("..")
from config import AgentConfig

from router_agent import RouterAgent


def main():
    conf = AgentConfig()
    print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

    agent = RouterAgent(conf)

    print("Dynamic Routing Agent")
    print("Type 'exit' to quit.")

    while True:
        text = input("\nYou> ").strip()

        if not text:
            continue

        if text.lower() in {"exit", "quit", }:
            break

        try:
            result = agent.run(text)

            print()
            print("Final Answer:")
            print(result)

        except Exception as e:
            print(f"[Error] {e}")


if __name__ == "__main__":
    main()
