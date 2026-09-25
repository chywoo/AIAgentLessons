import sys
sys.path.append("..")
from config import AgentConfig
from agent import ReActAgent

conf = AgentConfig()
print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

agent = ReActAgent(conf)
response = agent.run(
    """
    Read sales.txt.
Find the 2025 sales.
Calculate 10% of that value.
Then count the number of digits in the result.

    """)

print("Agent Response:\n", response)

