from guardrail import GuardrailResult


class PolicyEngine:


    def evaluate(self, tool_name: str, arguments: dict, ) -> GuardrailResult:

        if tool_name == "delete_file":
            path = arguments.get("path", "")

            if path == "sales.txt":
                return GuardrailResult(allowed=False, reason=("sales.txt is protected."), )

        return GuardrailResult(allowed=True)

PROTECTED_FILES = {
    "sales.txt",
    "config.json",
}

def protect_critical_files(
    tool_name: str,
    arguments: dict,
) -> GuardrailResult:

    if tool_name != "delete_file":
        return GuardrailResult(True)

    path = arguments.get(
        "path"
    )

    if path in PROTECTED_FILES:

        return GuardrailResult(
            allowed=False,
            reason=(
                f"{path} is protected "
                "and cannot be deleted."
            ),
        )

    return GuardrailResult(True)