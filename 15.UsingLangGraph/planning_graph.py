import json
import sys

sys.path.append("..")
from config import AgentConfig
from typing import Any, Literal
from openai import OpenAI
from langgraph.graph import (StateGraph, START, END, )
from typing_extensions import TypedDict
from tools import (TOOLS, TOOL_SCHEMAS, )


class AgentState(TypedDict):
    goal: str
    plan: list[str]
    current_step: int
    completed_steps: list[str]
    facts: list[str]
    step_result: str
    decision: str
    decision_reason: str
    replan_count: int
    final_answer: str


class PlanningGraphAgent:
    def __init__(self, config: AgentConfig, max_executor_iterations: int = 8, max_replans: int = 3, ):
        self.model = config.model
        self.max_executor_iterations = (max_executor_iterations)
        self.max_replans = max_replans
        self.client = OpenAI(base_url=config.api_base, api_key=config.api_key, )
        self.graph = (self._build_graph())

    def parse_json(self, content: str, ) -> dict:
        text = content.strip()

        # Some OpenAI-compatible models
        # wrap JSON in Markdown fences.
        if text.startswith("```"):
            lines = text.splitlines()
            lines = lines[1:]

            if (lines and lines[-1].strip() == "```"):
                lines = lines[:-1]

            text = "\n".join(lines).strip()

            if text.startswith("json"):
                text = text[4:].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError("Model returned invalid JSON:\n" + text) from e

    # =========================================================
    # Planner Node
    # =========================================================

    def planner_node(self, state: AgentState, ) -> dict:

        print()
        print("=" * 60)
        print("[NODE] PLANNER")
        print("=" * 60)

        messages = [{"role": "system", "content": ("You are a planning agent. "
                                                   "Break the user's goal into a small number "
                                                   "of clear executable steps.\n\n"
                                                   "Do not execute the task.\n"
                                                   "Do not include unnecessary steps.\n\n"
                                                   "Return JSON only:\n"
                                                   '{"steps":["step 1","step 2"]}'), },
                    {"role": "user", "content": state["goal"], }, ]

        response = (self.client.chat.completions.create(model=self.model, messages=messages, reasoning_effort="none"))
        content = (response.choices[0].message.content or "")
        data = self.parse_json(content)
        steps = data.get("steps")

        if not isinstance(steps, list, ):
            raise RuntimeError("Planner did not return "
                               "a valid steps list.")

        plan = [str(step).strip() for step in steps if str(step).strip()]

        if not plan:
            raise RuntimeError("Planner returned an empty plan.")

        print("[PLAN]")

        for index, step in enumerate(plan, start=1, ):
            print(f"{index}. {step}")

        return {"plan": plan, "current_step": 0, "completed_steps": [], "facts": [], "step_result": "", "decision": "",
                "decision_reason": "", "replan_count": 0, "final_answer": "", }

    # =========================================================
    # Executor Node
    # =========================================================

    def executor_node(self, state: AgentState, ) -> dict:

        print()
        print("=" * 60)
        print("[NODE] EXECUTOR")
        print("=" * 60)

        current_index = (state["current_step"])
        current_step = (state["plan"][current_index])

        print(f"Step {current_index + 1}: {current_step}")

        facts_text = "\n".join(f"- {fact}" for fact in state["facts"])

        completed_text = "\n".join(f"- {step}" for step in state["completed_steps"])

        messages: list[dict] = [
            {
                "role": "system",
                "content": ("You are an execution agent.\n"
                            "Complete ONLY the current plan step.\n"
                            "Use tools when necessary.\n"
                            "Do not execute future steps.\n"
                            "When the current step is complete, "
                            "return a concise summary."),
            },
            {
                "role": "user",
                "content": f"""
Overall goal:
{state["goal"]}

Current plan:
{json.dumps(state["plan"], indent=2)}

Completed steps:
{completed_text if completed_text else "- None"}

Known facts:
{facts_text if facts_text else "- None"}

Current step:
{current_step}
""".strip(),
            },
        ]

        new_facts = []

        for iteration in range(1, self.max_executor_iterations + 1, ):
            print(f"Executor iteration {iteration}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                reasoning_effort="none"
            )

            message = (response.choices[0].message)
            messages.append(message.to_dict())

            # -----------------------------------------
            # No tool call:
            # current plan step is complete.
            # -----------------------------------------

            if not message.tool_calls:
                result = (message.content or "")
                print("[STEP RESULT]")
                print(result)

                return {
                    "step_result": result,
                    "facts": state["facts"] + new_facts,
                }

            # -----------------------------------------
            # Tool calls
            # -----------------------------------------
            for call in message.tool_calls:
                tool_name = call.function.name
                arguments_json = call.function.arguments

                print(f"[TOOL] {tool_name}")
                print(f"[ARGS] {arguments_json}")

                tool = TOOLS.get(tool_name)

                if tool is None:
                    result = (f"Unknown tool: {tool_name}")
                else:
                    try:
                        arguments = (json.loads(arguments_json))
                        result = str(tool(**arguments))
                    except Exception as e:
                        result = (f"Tool execution error: {e}")

                print(f"[OBSERVATION]\n"
                      "====== CONTENT ======\n"
                      f"{result}\n"
                      "======== END ========\n")

                new_facts.append(f"{tool_name}: {result}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result, })

        raise RuntimeError("Executor exceeded maximum iterations.")

    # =========================================================
    # Evaluator Node
    # =========================================================
    def evaluator_node(self, state: AgentState, ) -> dict:
        print()
        print("=" * 60)
        print("[NODE] EVALUATOR")
        print("=" * 60)

        current_step = state["plan"][state["current_step"]]

        messages = [
            {
                "role": "system",
                "content": (
                    "You evaluate an AI agent's progress.\n\n"
                    "Choose exactly one decision:\n"
                    "- continue\n"
                    "- replan\n"
                    "- finish\n\n"

                    "continue:\n"
                    "The step succeeded and the existing plan is still valid.\n\n"

                    "replan:\n"
                    "A tool failed, an assumption was wrong, required information is missing, or the "
                    "remaining plan is no longer appropriate.\n\n"

                    "finish:\n"
                    "The overall user goal is already satisfied.\n\n"

                    "Return JSON only:\n"
                    "{"
                    '"decision":"continue|replan|finish",'
                    '"reason":"short reason"'
                    "}"),
            },
            {
                "role": "user",
                "content": f"""
Goal:
{state["goal"]}

Plan:
{json.dumps(state["plan"], indent=2)}

Current step:
{current_step}

Step result:
{state["step_result"]}

Known facts:
{json.dumps(state["facts"], indent=2)}

Completed steps:
{json.dumps(state["completed_steps"], indent=2)}
""".strip(), }, ]

        response = (self.client.chat.completions.create(model=self.model, messages=messages, ))
        content = (response.choices[0].message.content or "")
        data = self.parse_json(content)
        decision = data.get("decision")
        reason = data.get("reason", "", )
        if decision not in {"continue", "replan", "finish", }:
            raise RuntimeError(f"Invalid evaluator "
                               f"decision: {decision}")

        print(f"[DECISION] {decision}")
        print(f"[REASON] {reason}")
        return {
            "decision": decision,
            "decision_reason": reason,
        }

    # =========================================================
    # Advance Node
    # =========================================================

    def advance_node(self, state: AgentState, ) -> dict:
        print()
        print("[NODE] ADVANCE")

        current_step_text = state["plan"][state["current_step"]]
        completed = state["completed_steps"] + [f"{current_step_text} -> {state['step_result']}"]

        return {
            "completed_steps": completed,
            "current_step": state["current_step"] + 1,
            "step_result": "",
            "decision": "",
            "decision_reason": "",
        }

    # =========================================================
    # Replanner Node
    # =========================================================
    def replanner_node(self, state: AgentState, ) -> dict:
        print()
        print("=" * 60)
        print("[NODE] REPLANNER")
        print("=" * 60)

        if (state["replan_count"] >= self.max_replans):
            raise RuntimeError("Maximum replan count exceeded.")

        messages = [
            {
                "role": "system",
                "content": "You are a replanning agent.\n"
                           "Create a new plan ONLY for the remaining work.\n\n"
                           "Do not repeat work that already succeeded unless necessary.\n\n"
                           "Take tool failures and new facts into account.\n\n"
                           "Return JSON only:\n"
                           '{"steps":["step 1","step 2"]}',
            },
            {
                "role": "user",
                "content": f"""
Original goal:
{state["goal"]}

Previous plan:
{json.dumps(state["plan"], indent=2)}

Completed steps:
{json.dumps(state["completed_steps"], indent=2)}

Known facts:
{json.dumps(state["facts"], indent=2)}

Last step result:
{state["step_result"]}

Reason for replanning:
{state["decision_reason"]}
""".strip(),
            },
        ]

        response = (self.client.chat.completions.create(model=self.model, messages=messages, reasoning_effort="none"))
        content = response.choices[0].message.content or ""
        data = self.parse_json(content)
        steps = data.get("steps")

        if not isinstance(steps, list, ):
            raise RuntimeError("Replanner returned "
                               "invalid plan.")

        new_plan = [str(step).strip() for step in steps if str(step).strip()]

        if not new_plan:
            raise RuntimeError("Replanner returned "
                               "an empty plan.")

        print("[NEW PLAN]")

        for index, step in enumerate(new_plan, start=1, ):
            print(f"{index}. {step}")

        return {
            "plan": new_plan,
            "current_step": 0,
            "replan_count": state["replan_count"] + 1,
            "step_result": "",
            "decision": "",
            "decision_reason": "",
        }

    # =========================================================
    # Finalizer Node
    # =========================================================
    def finalizer_node(self, state: AgentState, ) -> dict:
        print()
        print("=" * 60)
        print("[NODE] FINALIZER")
        print("=" * 60)

        messages = [
            {
                "role": "system",
                "content": ("Produce a clear final answer "
                            "for the user using the completed "
                            "work and known facts. "
                            "Do not invent missing facts."),
            },
            {
                "role": "user",
                "content": f"""
Original goal:
{state["goal"]}

Completed steps:
{json.dumps(state["completed_steps"], indent=2)}

Known facts:
{json.dumps(state["facts"], indent=2)}

Latest step result:
{state["step_result"]}
""".strip(),
            },
        ]

        response = (self.client.chat.completions.create(model=self.model, messages=messages, reasoning_effort="none"))
        answer = (response.choices[0].message.content or "")

        print("[FINAL ANSWER]")
        print(answer)

        return {"final_answer": answer}

    # =========================================================
    # Routing Functions
    # =========================================================

    def route_after_evaluation(self, state: AgentState, ) -> Literal["continue", "replan", "finish",]:
        return state["decision"]

    def route_after_advance(self, state: AgentState, ) -> Literal["execute", "finish",]:
        if (state["current_step"] >= len(state["plan"])):
            return "finish"

        return "execute"

    # =========================================================
    # Build Graph
    # =========================================================

    def _build_graph(self, ):

        builder = StateGraph(AgentState)

        # Nodes
        builder.add_node("planner", self.planner_node, )
        builder.add_node("executor", self.executor_node, )
        builder.add_node("evaluator", self.evaluator_node, )
        builder.add_node("advance", self.advance_node, )
        builder.add_node("replanner", self.replanner_node, )
        builder.add_node("finalizer", self.finalizer_node, )

        # START
        builder.add_edge(START, "planner", )

        # Normal execution
        builder.add_edge("planner", "executor", )
        builder.add_edge("executor", "evaluator", )

        # Evaluator branching
        builder.add_conditional_edges(
            "evaluator",
            self.route_after_evaluation,
            {
                "continue": "advance",
                "replan": "replanner",
                "finish": "finalizer",
            },
        )

        # After normal step completion
        builder.add_conditional_edges(
            "advance",
            self.route_after_advance,
            {
                "execute": "executor",
                "finish": "finalizer",
            },
        )

        # Replan -> execute new plan
        builder.add_edge("replanner", "executor", )

        # End
        builder.add_edge("finalizer", END, )

        return builder.compile()

    # =========================================================
    # Run
    # =========================================================

    def run(self, user_input: str, ) -> str:

        initial_state: AgentState = {
            "goal": user_input,
            "plan": [],
            "current_step": 0,
            "completed_steps": [],
            "facts": [],
            "step_result": "",
            "decision": "",
            "decision_reason": "",
            "replan_count": 0,
            "final_answer": "",
        }

        final_state = (self.graph.invoke(initial_state))

        return final_state["final_answer"]
