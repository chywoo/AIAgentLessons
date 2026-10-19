import time
from dataclasses import dataclass
from langchain_core.messages import AIMessage, ToolMessage


@dataclass
class ExecutionMetrics:
    latency_ms: float
    model_calls: int
    too_calls: int
    input_tokens: int
    output_tokens: int


def collect_metrics(result: dict, latency_ms: float) -> ExecutionMetrics:
    messages = result["messages"]

    ai_message = [
        message for message in messages if isinstance(message, AIMessage)
    ]

    tool_message = [
        message for message in messages if isinstance(message, ToolMessage)
    ]

    return ExecutionMetrics(
        latency_ms=latency_ms,
        model_calls=result["model_calls"],
        too_calls=result["too_calls"],
        input_tokens=sum(
            (msg.usage_metadata or {}).get("input_tokens", 0) for msg in ai_message
        ),
        output_tokens=sum(
            (msg.usage_metadata or {}).get("output_tokens", 0) for msg in ai_message
        )
    )


async def measure_agent(agent, question: str):
    started = time.perf_counter()

    result = await agent.ainvoke(
        {
            "messages": [{"role": "user", "content": question}],
        }
    )

    elapsed = (time.perf_counter() - started) * 1000
    metrics = collect_metrics(result, elapsed)

    return result, metrics