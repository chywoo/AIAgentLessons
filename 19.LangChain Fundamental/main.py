from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.messages import SystemMessage, HumanMessage
from tools import *

import sys
sys.path.append("..")
from config import AgentConfig

conf = AgentConfig()

model = ChatOpenAI(
    model=conf.model,
    base_url=conf.api_base,
    api_key=conf.api_key,
)

# ----------------------------------------------------------------------
# Agent
# ----------------------------------------------------------------------

SYSTEM_PROMPT = """
You are a customer support agent for an online store.

Available tools:
- lookup_order: retrieve basic order information such as carrier and order status.
- check_shipping: retrieve the latest shipping status.
- create_ticket: create a customer support ticket.

Rules:
1. Use the minimum number of tools necessary to answer the user's request.
2. Do not create a support ticket unless the user explicitly asks for support,
   escalation, help from support staff, or the issue cannot be resolved with available information.
3. Asking for information is not a request to create or modify anything.
4. Do not call create_ticket just because an order is delayed.
5. If only the carrier is requested, lookup_order is sufficient.
6. If shipping status is requested, use check_shipping. Use lookup_order too only if additional order information is needed.
7. Never invent order data.
"""

agent = create_agent(
    model=model,
    tools=[
        lookup_order,
        check_shipping,
        create_ticket,
    ],
    system_prompt=SYSTEM_PROMPT,
)



# ----------------------------------------------------------------------
# Helper
# ----------------------------------------------------------------------

def run_test(name: str, question: str) -> None:
    print()
    print("=" * 80)
    print(name)
    print("=" * 80)
    print(f"USER: {question}")
    print()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        }
    )

    final_message = result["messages"][-1]

    print()
    print("FINAL ANSWER:")
    print(final_message.content)


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def main() -> None:
    run_test(
        "TEST 1 - Shipping status",
        "What is the shipping status of order 12345?",
    )

    run_test(
        "TEST 2 - Carrier only",
        "Which carrier is handling order 12345?",
    )

    run_test(
        "TEST 3 - Customer requests support",
        "Order 12345 has been delayed for a week and I want support.",
    )


if __name__ == "__main__":
    main()
