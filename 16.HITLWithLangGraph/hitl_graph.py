import json
import sys
import operator

from typing import (Annotated, Any, )

sys.path.append("..")
from config import AgentConfig
from typing import Any, Literal
from openai import OpenAI
from typing_extensions import TypedDict
from tools import (TOOLS, TOOL_SCHEMAS, )

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command, interrupt

import sqlite3

class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add,]


class HITLAgent:
    def __init__(self, config: AgentConfig):
        self.model = config.model
        self.client = OpenAI(base_url=config.api_base, api_key=config.api_key, )
        #self.connection = sqlite3.connect("agent_checkpoints.db", check_same_thread=False)
        #self.checkpointer = SqliteSaver(self.connection)
        self.checkpointer = InMemorySaver()
        self.graph = (self._build_graph())

    def llm_node(self, state: AgentState, ) -> dict:
        print()
        print("[NODE] LLM")

        response = self.client.chat.completions.create(model=self.model, messages=state["messages"], tools=TOOL_SCHEMAS,
                                                       tool_choice="auto", reasoning_effort="none", )

        message = response.choices[0].message

        return {"messages": [message.to_dict()]}

    def route_after_llm(self, state: AgentState, ) -> str:

        last_message = (state["messages"][-1])
        tool_calls = (last_message.get("tool_calls", [], ))

        if not tool_calls:
            print("[ROUTER] → END")
            return "end"

        #
        # Day 18에서는 이해를 쉽게 하기 위해
        # 한 번에 하나의 tool call만 허용한다.
        #
        tool_call = tool_calls[0]
        tool_name = (tool_call["function"]["name"])
        tool_info = TOOLS.get(tool_name)

        if tool_info is None:
            return "safe_tool"

        if tool_info["requires_approval"]:
            print("[ROUTER] → APPROVAL")
            return "approval"

        print("[ROUTER] → SAFE TOOL")

        return "safe_tool"

    def safe_tool_node(self, state: AgentState, ) -> dict:
        print()
        print("[NODE] SAFE TOOL")

        last_message = state["messages"][-1]
        tool_call = last_message["tool_calls"][0]
        tool_name = tool_call["function"]["name"]

        arguments = json.loads(tool_call["function"]["arguments"])

        tool_info = TOOLS.get(tool_name)

        if tool_info is None:
            result = f"Unknown tool: {tool_name}"
        else:
            try:
                result = str(tool_info["function"](**arguments))
            except Exception as e:
                result = f"Tool error: {e}"

        print(f"[RESULT] {result}")

        return {"messages": [{"role": "tool", "tool_call_id": tool_call["id"], "content": result, }]}

    def approval_node(self, state: AgentState, ) -> Command:
        print()
        print("[NODE] APPROVAL")

        last_message = (state["messages"][-1])
        tool_call = (last_message["tool_calls"][0])
        tool_name = (tool_call["function"]["name"])
        arguments = json.loads(tool_call["function"]["arguments"])
        tool_info = (TOOLS[tool_name])

        #
        # HERE THE GRAPH PAUSES.
        #

        decision = interrupt(
            {
                "question": "Approve this action?",
                "tool": tool_name,
                "arguments": arguments,
                "risk": tool_info["risk"],
            }
        )

        if decision:
            return Command(goto="execute_approved")

        return Command(goto="reject_action")

    def execute_approved_node(self, state: AgentState, ) -> dict:

        print()
        print("[NODE] EXECUTE APPROVED")

        last_message = (state["messages"][-1])
        tool_call = (last_message["tool_calls"][0])
        tool_name = (tool_call["function"]["name"])
        arguments = json.loads(tool_call["function"]["arguments"])

        try:
            result = str(TOOLS[tool_name]["function"](**arguments))
        except Exception as e:
            result = (f"Tool error: {e}")

        return {"messages": [{"role": "tool", "tool_call_id": tool_call["id"], "content": result, }]}

    def reject_action_node(self, state: AgentState, ) -> dict:

        print()
        print("[NODE] ACTION REJECTED")

        last_message = (state["messages"][-1])
        tool_call = (last_message["tool_calls"][0])

        return {
            "messages": [
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": "ACTION_REJECTED: The human did not approve this action.",
                }
            ]
        }

    def _build_graph(self, ):

        builder = StateGraph(AgentState)

        builder.add_node("llm", self.llm_node, )
        builder.add_node("safe_tool", self.safe_tool_node, )
        builder.add_node("approval", self.approval_node, )
        builder.add_node("execute_approved", self.execute_approved_node, )
        builder.add_node("reject_action", self.reject_action_node, )

        builder.add_edge(START, "llm", )
        builder.add_conditional_edges(
            "llm",
            self.route_after_llm,
            {
                "safe_tool": "safe_tool",
                "approval": "approval",
                "end": END,
            },
        )
        builder.add_edge("safe_tool", "llm", )

        #
        # approval node 자체가
        # Command(goto=...)로 routing한다.
        #
        builder.add_edge("execute_approved", "llm", )
        builder.add_edge("reject_action", "llm", )

        return builder.compile(checkpointer=self.checkpointer)
