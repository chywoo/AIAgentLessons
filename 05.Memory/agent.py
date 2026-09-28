from dataclasses import dataclass, field

from openai import OpenAI
from openai.types.chat import ChatCompletion

from config import AgentConfig

from memory import Memory, MemoryStore
from tools import TOOL_SCHEMAS
from tools import TOOLS
import json


@dataclass
class AgentState:
    goal: str
    plan: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    completed_steps: list[str] = field(default_factory=list)
    retrieved_memories: list[str] = field(default_factory=list)
    current_step: int = 0
    replan_count: int = 0


class MemoryAgent:
    def __init__(self, config: AgentConfig, max_executor_iterations: int = 10, max_replans: int = 3):
        self.config = config
        self.model = self.config.model
        self.max_executor_iterations = max_executor_iterations
        self.max_replans = max_replans

        self.client = OpenAI(api_key=config.api_key, base_url=config.api_base)
        self.memory = MemoryStore()

    def run(self, prompt: str) -> str:
        state = AgentState(prompt)

        memories = self._retrieve_memories(prompt)
        print(f"[AGENT] Retrieved memory: {memories}")
        state.retrieved_memories.append(memories)

        state.plan = self._create_plan(state.goal)

        while state.current_step < len(state.plan):
            step = state.plan[state.current_step]

            print()
            print("=" * 60)
            print(f"PLAN STEP {state.current_step + 1}/{len(state.plan)}")
            print("=" * 60)

            print(f" * Step: {step}")

            step_result = self._execute_plan_step(state, step)

            print()
            print("[Step Result]")
            print(step_result)

            state.completed_steps.append(f"{step} -> {step_result}")

            decision = self._evaluate_progress(state, step, step_result)

            print()
            print(f"[Evaluator] {decision['decision']}")
            print(f"[Reason] {decision.get('reason', '')}")

            if decision["decision"] == "finish":
                break
            elif decision["decision"] == "replan":
                if state.replan_count >= self.max_replans:
                    raise RuntimeError("Maximum number of replans reached.")

                state.replan_count += 1
                state.plan = self._replan(state, decision.get("reason", "Plan needs revision."))
                state.current_step = 0

                continue
            state.current_step += 1

        final_answer = self._generate_final_answer(state)

        print()
        print("=" * 60)
        print("FINAL ANSWER")
        print("=" * 60)

        return final_answer

    # ---------------------------------------------------------
    # Planner
    # ---------------------------------------------------------
    def _create_plan(self, goal: str) -> list[str]:
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
                    "Only make clear executable steps. "
                    "Return JSON only in this format:\n"
                    '{"steps": ["step 1", "step 2", ]} '
                    "DO NOT ANSWER TOOL CALLING. "
                ),
            },
            {
                "role": "user",
                "content": goal
            }
        ]

        response = self.__call_llm(messages, TOOL_SCHEMAS)
        message = response.choices[0].message
        content = message.content or ""

        data = self.__parse_json(content)
        steps = data.get("steps")

        if not isinstance(steps, list) or not steps:
            raise RuntimeError("Planner returned invalid steps.")

        plan = [str(step) for step in steps if str(step).strip()]

        for index, step in enumerate(plan, start=1):
            print(f"[{index}]. {step}")

        return plan

    def _execute_tool(self, too_name: str, arguments: str) -> str:
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

    def _execute_plan_step(self, state: AgentState, step: str, ) -> str:
        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "You are an execution agent. "
                    "Complete the requested plan step. "
                    "Use available tools when necessary. "
                    "Do not execute future plan steps. "
                    "When the step is complete, give a concise "
                    "summary of the result."
                ),
            },
            {
                "role": "user",
                "content":
                    self._build_state_message(state)
                    + "\n\nCurrent step:\n"
                    + step
            },
        ]

        for i in range(1, self.max_executor_iterations + 1):
            print(f"\n## Executor iteration {i}")

            response = self.__call_llm(messages, TOOL_SCHEMAS)
            message = response.choices[0].message

            # ChatCompletionMessage -> dict
            messages.append(message.to_dict())

            if not message.tool_calls:
                result = message.content or ""

                print(f"\n[Executor] step result]\n{result}")

                return result

            for call in message.tool_calls:
                tool_name = call.function.name
                tool_args = call.function.arguments

                result = self._execute_tool(tool_name, tool_args)

                print(f"\n[Executor] run the tool and result]\n{result}")
                state.facts.append(f"{tool_name}: {result}")

                tool_message = {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result)
                }

                messages.append(tool_message)

        raise RuntimeError(
            f"Executor exceeded max_steps={self.max_executor_iterations} times"
        )

    # ---------------------------------------------------------
    # Evaluator
    # ---------------------------------------------------------
    def _evaluate_progress(self, state: AgentState, step: str, step_result: str, ) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You evaluate the progress of an AI agent. "
                    "Decide whether it should continue the current "
                    "plan, create a new plan, or finish.\n\n"
                    "Return JSON only:\n"
                    "{"
                    '"decision":"continue|replan|finish",'
                    '"reason":"short explanation"'
                    "}\n\n"
                    "Use 'continue' when everything goes well. "
                    "Use 'replan' when the current plan is no longer "
                    "appropriate because of missing information, "
                    "tool failure, unexpected observations, or an "
                    "invalid assumption.\n"
                    "Use 'finish' only if the overall user goal "
                    "has already been satisfied."
                ),
            },
            {
                "role": "user",
                "content": f"""
{self._build_state_message(state)}

Just executed step:
{step}

Step result:
{step_result}
""".strip(),
            }
        ]

        response = self.__call_llm(messages)
        content = response.choices[0].message.content or ""
        decision = self.__parse_json(content)
        value = decision.get('decision')

        if value not in {'continue', 'replan', 'finish'}:
            raise RuntimeError(f"Invalid evaluator decision: {value}")

        return decision

    # ---------------------------------------------------------
    # Replanner
    # ---------------------------------------------------------
    def _replan(self, state: AgentState, reason: str) -> list[str]:
        print()
        print("=" * 60)
        print("REPLANNING")
        print("=" * 60)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a replanning agent. "
                    "Given the original goal, completed work, "
                    "observations, and the reason the previous plan "
                    "failed, create a new plan for the remaining work. "
                    "Do not repeat successfully completed steps unless "
                    "they truly need to be repeated. "
                    "Return JSON only:\n"
                    '{"steps":["step 1","step 2"]}'
                ),
            },
            {
                "role": "user",
                "content": f"""
        {self._build_state_message(state)}

        Reason for replanning:
        {reason}
        """.strip(),
            },
        ]

        response = self.__call_llm(messages)
        content = response.choices[0].message.content or ""
        data = self.__parse_json(content)
        steps = data.get("steps")

        if not isinstance(steps, list):
            raise RuntimeError("Replanner returned invalid steps.")

        new_plan = [str(step) for step in steps if str(step).strip()]
        print("[New Plan]")
        for i, step in enumerate(new_plan):
            print(f"{i}. {step}")

        return new_plan

    def _build_state_message(self, state: AgentState) -> str:
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

     * Current plan:
    {json.dumps(state.plan, indent=2)}

     * Completed steps:
    {json.dumps(state.completed_steps, indent=2)}

     * Known observations / facts:
    {json.dumps(state.facts, indent=2)}

     * Relevent long-term memories:
    {json.dumps(state.retrieved_memories, indent=2)}

     * Current step index:
    {state.current_step}

     * Replan count:
    {state.replan_count}
    """.strip()

    def _generate_final_answer(self, state: AgentState) -> str:
        facts = "".join(f"- {fact}" for fact in state.facts)
        completed = "".join(f"- {step}" for step in state.completed_steps)

        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "Your are a helpful assistant. "
                    "Produce the final answer for the user "
                    "using the results of the completed tasks and observations"
                ),
            },
            {
                "role": "user",
                "content": self._build_state_message(state),
            },
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

    def _retrieve_memories(self, query: str) -> str:
        words = [word.strip(".,?!") for word in query.split() if len(word) >= 4]

        found = {}

        for word in words:
            results = self.memory.search(
                query=word,
                limit=5,
            )

            for memory in results:
                found[memory.id] = memory

        if not found:
            return "No relevant memories."

        return "\n".join(
            f"- {memory.content}"
            for memory in found.values()
        )

    # ---------------------------------------------------------
    # Call LLM with messages or a tool schema
    # ---------------------------------------------------------
    def __call_llm(self, messages: object, tools=None) -> ChatCompletion:

        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

    # ---------------------------------------------------------
    # Parse planner JSON response
    # ---------------------------------------------------------
    def __parse_json(self, content: str) -> list[str]|dict:
        text = content.strip()

        if text.startswith("````"):
            lines = text.splitlines()

            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Planner returned invalid JSON:\n{text}"
            ) from e

