import sys
sys.path.append("..")
from config import AgentConfig
import agent

conf = AgentConfig()
print(f"* API URL: {conf.api_base}\n* MODEL: {conf.model}")
response = agent.run_agent("Calculate 123 * 456 and, get current time. Answer in JSON format.", conf)

print("Agent Response:", response)

