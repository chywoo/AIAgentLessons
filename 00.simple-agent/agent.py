from config import AgentConfig
from openai import OpenAI
from tools import TOOL_SCHEMAS
from tools import TOOLS
import json


def run_agent(user_input: str, config: AgentConfig):
    client = OpenAI(api_key=config.api_key, base_url=config.api_base)

    messages=[{"role": "user", "content": user_input}]


    while True:
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if not msg.tool_calls: # if not tool calls,
            return msg.content

        assistant_message = {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }

                for tc in msg.tool_calls
            ]
        }

        messages.append(assistant_message)

        for call in msg.tool_calls:
            tool_name = call.function.name
            param = json.loads(call.function.arguments)
            result = TOOLS[tool_name](**param)

            messages.append( {
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result)
            })
