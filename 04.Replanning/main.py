import sys
sys.path.append("..")
from config import AgentConfig
from agent import ReplanningAgent

conf = AgentConfig()
print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

agent = ReplanningAgent(conf)

prompt="""
Read sales2.txt file.

Find the 2025 annual sales.

Calculate 15% of it.

Then count the number of digits in the calculated value.
"""
print(agent.run(prompt))
exit()
