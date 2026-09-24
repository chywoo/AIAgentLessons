import sys
sys.path.append("..")
from config import AgentConfig
from agent import SimpleAgent

conf = AgentConfig()
print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

agent_runner = SimpleAgent(conf)

response = agent_runner.run(
    """
    Read 'sales.txt'.

Find the 2025 annual sales.

Calculate 10% of that value.

Then tell me how many characters
are in the calculated result.
    """)

print("Agent Response:\n", response)

