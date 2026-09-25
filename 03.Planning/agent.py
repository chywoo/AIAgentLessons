from dataclasses import dataclass, field

from openai.types.chat import ChatCompletion

from config import AgentConfig
from openai import OpenAI
from tools import TOOL_SCHEMAS
from tools import TOOLS
import json

@dataclass
class AgentState:
    goal: str
    plan: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    completed_steps: list[str] = field(default_factory=list)
    current_step: int = 0


class PlanningAgent:
    def __init__(self, config: AgentConfig, max_steps:int = 10):
        self.config = config
        self.model = self.config.model
        self.max_steps = max_steps
        self.client = OpenAI(api_key=config.api_key, base_url=config.api_base)

    # ---------------------------------------------------------
    # Planner
    # ---------------------------------------------------------
    def create_plan(self, goal: str) -> list[str]:
        print()
        print("=" * 60)
        print("PLANNING")
        print("=" * 60)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a planning agent. "
                    "Break the user's goal into a small number of "
                    "clear executable steps. "
                    "Do not perform the task yourself. "
                    "Return JSON only in this format:\n"
                    '{"steps": ["step 1", "step 2"]}'
                ),
            },
            {
                "role": "user",
                "content": goal
            }
        ]

        response = self.__call_llm(messages)
        message = response.choices[0].message
        content = message.content or ""

        print("[Planner raw response]")
        print(content)

        plan = self._parse_plan(content)

        print("\n[Generated Plan]")

        for index, step in enumerate(plan, start=1):
            print(f"[{index}]. {step}")

        return plan

    # ---------------------------------------------------------
    # Parse planner JSON
    # ---------------------------------------------------------
    def _parse_plan(self, content: str) -> list[str]:
        text = content.strip()

        if text.startswith("````"):
            lines = text.splitlines()

            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Planner returned invalid JSON:\n{text}"
            ) from e

        steps = data.get("steps")

        if not isinstance(steps, list):
            raise RuntimeError(
                "Planner response does not contain a valid 'steps' list."
            )

        steps = [str(step).strip() for step in steps if str(step).strip()]

        if not steps:
            raise RuntimeError("Planner returned an empty plan.")

        return steps


    def _execute_tool(self, too_name:str, arguments: str) -> str:
        tool = TOOLS.get(too_name)

        if tool is None:
            print(f"[Agent] Tool {too_name} not found")
            return f"Unkown tool: {too_name}"

        print(f"[Agent] Tool selected: {too_name}")

        try:
            args = json.loads(arguments)
            print(f"[Agent] Arguments: {arguments}")
            result = tool(**args)
            print(f"[Tool] Observation:\n{result}")
            return str(result)
        except json.decoder.JSONDecodeError as e:
            return f"Invalid tool arguments: {arguments} with {e}"
        except Exception as e:
            return f"Tool execution error: {e}"

    def run(self, prompt:str) -> str:
        state = AgentState(prompt)

        state.plan = self.create_plan(state.goal)

        for i, step in enumerate(state.plan):
            state.current_step = i

            print()
            print("=" * 60)
            print(f"PLAN STEP {i + 1}/{len(state.plan)}")
            print("=" * 60)

            print(step)

            result = self._execute_plan_step(state, step)
            state.completed_steps.append(f"{step} -> {result}")

        final_answer = self.generate_final_answer(state)

        print()
        print("=" * 60)
        print("FINAL ANSWER")
        print("=" * 60)

        print(final_answer)

        return final_answer


    def _execute_plan_step(self, state: AgentState, current_step: str, ) -> str:
        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "You are an execution agent. "
                    "Complete the requested plan step. "
                    "Use available tools when necessary. "
                    "Do not execute future plan steps."
                ),
            },
            {
                "role": "user",
                "content": self._build_state_message(state, current_step)
            },
        ]

        for i in range(1, self.max_steps + 1):
            print(f"\n  Executor iteration {i}")

            response = self.__call_llm(messages, TOOL_SCHEMAS)
            message = response.choices[0].message

            # ChatCompletionMessage -> dict
            messages.append(message.to_dict())

            if not message.tool_calls:
                result = message.content or ""

                print(f"\n[Step result]\n{result}")

                return result

            for call in message.tool_calls:
                tool_name = call.function.name
                tool_args = call.function.arguments

                result = self._execute_tool(tool_name, tool_args)

                state.facts.append(f"{tool_name}: {result}")

                tool_message = {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result)
                }

                messages.append(tool_message)

        raise RuntimeError(
            f"Executor execeeded max_steps={self.max_steps} times"
        )

    def generate_final_answer(self, state: AgentState) -> str:
        facts = "".join( f"- {fact}" for fact in state.facts)
        completed = "".join(f"- {step}" for step in state.completed_steps)

        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "Your are a helpful assistant. "
                    "Produce the final answer using the "
                    "results of the completed task."
                ),
            },
            {
                "role": "user",
                "content": f"""
Original goal:
{state.goal}

Completed steps:
{completed}

Observations:
{facts}

Provide the final answer
""".strip()
            }
        ]

        response = self.__call_llm(messages)

        return response.choices[0].message.content or ""

    def _print_messages(self, messages):
        print("\n--- Current Agent State ---")

        for i, message in enumerate(messages):
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get("content")

                print(f"[{i}] role={role}")
                print(f"    content={content}")

            else:
                print(f"[{i}] role={message.role}")

                if message.content:
                    print(f"    content={message.content}")

                if message.tool_calls:
                    for call in message.tool_calls:
                        print(
                            f"    tool_call="
                            f"{call.function.name}"
                            f"({call.function.arguments})"
                        )


    def _build_state_message(self, state: AgentState, current_step: str) -> str:
        completed = "\n".join(
            f"- {step}"
            for step in state.completed_steps
        )

        facts = "\n".join(
            f"- {fact}"
            for fact in state.facts
        )

        return f"""
* Overall Goal:
{state.goal}

* Full plan:
{json.dumps(state.plan, indent=2)}

 * Completed steps:
{completed if completed else "- None"}

 * Known observations / facts:
{facts if facts else "- None"}

 * Current step:
{current_step}

Work only on the current step.
Use tools if necessary.
When the current step has been completed,
return a concise summary of what was accomplished.

Do not continue to later plan steps.
""".strip()

    def __call_llm(self, messages: object, tools = None) -> ChatCompletion:

        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
