from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path("./data").resolve()


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""


def validate_user_input(user_input: str, ) -> GuardrailResult:
    if not user_input.strip():
        return GuardrailResult(allowed=False, reason="Empty input.", )

    if len(user_input) > 20_000:
        return GuardrailResult(allowed=False, reason="Input is too long.", )

    return GuardrailResult(
        allowed=True
    )


def validate_output(
        answer: str,
) -> GuardrailResult:
    if not answer.strip():
        return GuardrailResult(
            allowed=False,
            reason="Empty final answer.",
        )

    if len(answer) > 50_000:
        return GuardrailResult(
            allowed=False,
            reason="Output too large.",
        )

    return GuardrailResult(
        allowed=True
    )


def validate_analysis_output(
        text: str,
) -> GuardrailResult:
    try:
        data = json.loads(text)

    except json.JSONDecodeError:
        return GuardrailResult(
            allowed=False,
            reason="Output is not valid JSON.",
        )

    if "summary" not in data:
        return GuardrailResult(
            allowed=False,
            reason="Missing summary field.",
        )

    if "confidence" not in data:
        return GuardrailResult(
            allowed=False,
            reason="Missing confidence field.",
        )

    return GuardrailResult(
        allowed=True
    )


def validate_file_path(path: str, ) -> GuardrailResult:
    target = (DATA_DIR / path).resolve()

    if (target != DATA_DIR and DATA_DIR not in target.parents):
        return GuardrailResult(
            allowed=False,
            reason=(
                "Access outside the data "
                "directory is not allowed."
            ),
        )

    return GuardrailResult(
        allowed=True
    )


def validate_write_file(
        arguments: dict,
) -> GuardrailResult:
    path = arguments.get(
        "path"
    )

    content = arguments.get(
        "content"
    )

    if not isinstance(path, str):
        return GuardrailResult(
            allowed=False,
            reason="path must be a string",
        )

    if not isinstance(content, str):
        return GuardrailResult(
            allowed=False,
            reason="content must be a string",
        )

    path_result = (
        validate_file_path(path)
    )

    if not path_result.allowed:
        return path_result

    if len(content) > 100_000:
        return GuardrailResult(
            allowed=False,
            reason="File content is too large.",
        )

    return GuardrailResult(
        allowed=True
    )


@dataclass
class ExecutionBudget:
    max_steps: int = 10
    max_tool_calls: int = 20
    max_replans: int = 3


@dataclass
class RuntimeState:
    step_count: int = 0
    tool_call_count: int = 0


def check_budget(
        state: RuntimeState,
        budget: ExecutionBudget,
) -> GuardrailResult:
    if (
            state.step_count
            >= budget.max_steps
    ):
        return GuardrailResult(
            allowed=False,
            reason="Maximum step count reached.",
        )

    if (
            state.tool_call_count
            >= budget.max_tool_calls
    ):
        return GuardrailResult(
            allowed=False,
            reason="Maximum tool-call budget reached.",
        )

    return GuardrailResult(
        allowed=True
    )


@dataclass
class CostBudget:
    max_cost_usd: float = 1.0
    current_cost_usd: float = 0.0
