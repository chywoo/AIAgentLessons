import json
import operator
from typing import (
    Annotated,
    Literal,
)

from langgraph.graph import (
    StateGraph,
    START,
    END,
)
from openai import OpenAI
from typing_extensions import TypedDict

from tools import (
    TOOLS,
    TOOL_SCHEMAS,
)


class AgentState(TypedDict):
    messages: Annotated[
        list[dict],
        operator.add,
    ]

    step_count: int


class LangGraphAgent:

    def __init__(
            self,
            config
    ):

        self.model = config.model

        self.client = OpenAI(
            base_url=config.api_base,
            api_key=config.api_key,
        )

        self.graph = self._build_graph()

    # --------------------------------------------------
    # LLM Node
    # --------------------------------------------------

    def llm_node(
            self,
            state: AgentState,
    ) -> dict:

        print()
        print("[Node] LLM")

        response = (
            self.client
            .chat
            .completions
            .create(
                model=self.model,
                messages=state["messages"],
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                reasoning_effort="none"
            )
        )

        message = (
            response
            .choices[0]
            .message
        )

        return {
            "messages": [message.to_dict()],
            "step_count": state["step_count"] + 1,
        }

    # --------------------------------------------------
    # Tool Node
    # --------------------------------------------------

    def tool_node(self, state: AgentState, ) -> dict:
        print()
        print("[Node] TOOL")

        last_message = state["messages"][-1]

        tool_messages = []

        for tool_call in last_message.get("tool_calls", [], ):
            name = tool_call["function"]["name"]

            arguments_json = tool_call["function"]["arguments"]

            print(f"Tool: {name}")
            print(f"Arguments: {arguments_json}")

            tool = TOOLS.get(name)

            if tool is None:
                result = (f"Unknown tool: {name}")
            else:
                try:
                    arguments = json.loads(arguments_json)
                    result = str(tool(**arguments))
                except Exception as e:
                    result = (f"Tool error: {e}")

            print(f"Observation: {result}")

            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                }
            )

        return {
            "messages": tool_messages
        }

    # --------------------------------------------------
    # Conditional routing
    # --------------------------------------------------

    def route_after_llm(self, state: AgentState, ) -> Literal["tool", "__end__",]:

        last_message = state["messages"][-1]

        if last_message.get("tool_calls"):
            print("[Router] LLM → TOOL")

            return "tool"

        print("[Router] LLM → END")

        return END

    # --------------------------------------------------
    # Graph construction
    # --------------------------------------------------

    def _build_graph(self, ):

        builder = StateGraph(AgentState)

        builder.add_node("llm", self.llm_node, )
        builder.add_node("tool", self.tool_node, )
        builder.add_edge(START, "llm", )
        builder.add_conditional_edges(
            "llm",
            self.route_after_llm,
            {
                "tool": "tool",
                END: END,
            },
        )

        builder.add_edge("tool", "llm", )

        return builder.compile()

    # --------------------------------------------------
    # Execute
    # --------------------------------------------------

    def run(
            self,
            user_input: str,
    ) -> str:

        initial_state = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a tool-using "
                        "AI agent. "
                        "Use the calculator "
                        "for arithmetic."
                    ),
                },

                {
                    "role": "user",
                    "content":
                        user_input,
                },
            ],

            "step_count": 0,
        }

        final_state = (
            self.graph.invoke(
                initial_state
            )
        )

        final_message = (
            final_state[
                "messages"
            ][-1]
        )

        return (
                final_message.get(
                    "content",
                    "",
                )
                or ""
        )
