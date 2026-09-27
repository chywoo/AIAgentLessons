import sys
from builtins import MemoryError

sys.path.append("..")
from config import AgentConfig
from agent import MemoryAgent

conf = AgentConfig()
print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")

agent = MemoryAgent(conf)
# The production environment uses PostgreSQL. Remember it.
prompt="""
What DB do the production environment use?
"""
print(agent.run(prompt))
exit()
