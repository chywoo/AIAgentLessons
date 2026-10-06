import json
import time
import uuid

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class Span:
    name: str
    span_type: str

    start_time: float
    end_time: float | None = None

    duration_ms: float | None = None

    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTrace:
    trace_id: str
    task: str

    start_time: float
    end_time: float | None = None

    duration_ms: float | None = None

    spans: list[Span] = field(default_factory=list)

    final_answer: str | None = None

    success: bool = True
    error: str | None = None


class Tracer:
    def __init__(self, trace_dir: str = "traces"):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    def start_trace(self, task: str) -> AgentTrace:
        return AgentTrace(
            trace_id=str(uuid.uuid4()),
            task=task,
            start_time=time.time(),
        )

    def start_span(
            self,
            trace: AgentTrace,
            name: str,
            span_type: str,
            attributes: dict | None = None,
    ) -> Span:
        span = Span(
            name=name,
            span_type=span_type,
            start_time=time.perf_counter(),
            attributes=attributes or {},
        )

        trace.spans.append(span)

        return span

    def end_span(
            self,
            span: Span,
            attributes: dict | None = None,
    ) -> None:
        span.end_time = time.perf_counter()
        span.duration_ms = (span.end_time - span.start_time) * 1000

        if attributes:
            span.attributes.update(attributes)

    def end_trace(
            self,
            trace: AgentTrace,
            final_answer: str | None = None,
            error: bool = True,
    ) -> None:
        trace.end_time = time.time()
        trace.duration_ms = (trace.end_time - trace.start_time) * 1000
        trace.final_answer = final_answer
        if error:
            trace.success = False
            trace.error = error

        self.save_trace(trace)

    def save_trace(self, trace: AgentTrace) -> None:
        path = self.trace_dir / f"{trace.trace_id}.json"

        with path.open("w") as f:
            json.dump(asdict(trace), f, ensure_ascii=False, indent=2)


def get_tool_calls(trace, ) -> list[str]:
    return [
        span.name
        for span in trace.spans
        if span.span_type == "tool"
    ]


def tool_selection_score(
        expected: list[str],
        actual: list[str],
) -> float:
    expected_set = set(expected)
    actual_set = set(actual)

    if not expected_set:
        return (1.0 if not actual_set else 0.0)

    correct = expected_set & actual_set

    return len(correct) / len(expected_set)
