import json
from tools import ApprovalDecision
from openai import OpenAI

from tools import TOOLS, TOOL_SCHEMAS


class HumanApprovalAgent:
    def __init__(self, conf, max_steps: int = 10, ):
        self.model = conf.model
        self.max_steps = max_steps

        self.client = OpenAI(base_url=conf.api_base, api_key=conf.api_key, )

    # --------------------------------------------------
    # Human approval
    # --------------------------------------------------

    def request_approval(self, tool_name: str, arguments: dict, risk: str, ) -> ApprovalDecision:

        print()
        print("=" * 60)
        print("HUMAN APPROVAL REQUIRED")
        print("=" * 60)

        print(f"Tool: {tool_name}")
        print(f"Risk: {risk.upper()}")

        print("Arguments:")

        print(json.dumps(arguments, indent=2, ensure_ascii=False, ))

        answer = input("\nApprove this action? [y/N]: ").strip().lower()

        if answer in {"y", "yes", }:
            return ApprovalDecision(approved=True)

        return ApprovalDecision(approved=False, reason=("The user rejected this action."))

    # --------------------------------------------------
    # Tool execution
    # --------------------------------------------------
    def execute_tool(self, tool_name: str, arguments_json: str, ) -> str:
        tool_info = TOOLS.get(tool_name)

        if tool_info is None:
            return f"Unknown tool: {tool_name}"

        try:
            arguments = json.loads(arguments_json)
        except json.JSONDecodeError as e:
            return f"Invalid arguments: {e}"

        requires_approval = (tool_info["requires_approval"])
        risk = tool_info["risk"]

        # ----------------------------------------------
        # Approval gate
        # ----------------------------------------------

        if requires_approval:
            decision = self.request_approval(tool_name, arguments, risk, )

            if not decision.approved:
                return ("ACTION_REJECTED: " + decision.reason)

        # ----------------------------------------------
        # Execute tool
        # ----------------------------------------------

        tool = tool_info["function"]

        try:
            result = tool(**arguments)
            return str(result)
        except Exception as e:
            return (f"Tool execution error: {e}")

    # --------------------------------------------------
    # Agent loop
    # --------------------------------------------------

    def run(self, user_input: str, ) -> str:
        messages: list[dict] = [
            {
                "role": "system",
                "content": (
                    "You are a tool-using AI agent. "
                    "Use tools when useful. "
                    "Some actions require human approval. "
                    "If an action is rejected, do not attempt "
                    "to bypass the rejection. "
                    "Instead, explain the limitation or choose "
                    "a safe alternative when appropriate."
                ),
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]

        for step in range(1, self.max_steps + 1, ):
            print()
            print("=" * 60)
            print(f"Agent Step {step}")
            print("=" * 60)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                reasoning_effort="none")

            message = (response.choices[0].message)

            # ChatCompletionMessage -> dict
            messages.append(message.to_dict())

            # ------------------------------------------
            # No tool call -> final answer
            # ------------------------------------------
            if not message.tool_calls:
                answer = (message.content or "")

                print()
                print("FINAL ANSWER")
                print(answer)

                return answer

            # ------------------------------------------
            # Tool calls
            # ------------------------------------------
            for call in message.tool_calls:
                tool_name = (call.function.name)
                arguments = (call.function.arguments)
                print(f"[Agent] Requested tool: {tool_name}")

                result = self.execute_tool(tool_name, arguments, )
                print(f"[Tool Result] {result}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    }
                )

        raise RuntimeError("Agent exceeded maximum steps.")
