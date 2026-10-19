from dataclasses import dataclass


@dataclass
class EvaluationCase:
    name: str
    required_evidence: set[str]
    forbidden_actions: set[str]


@dataclass
class EvaluationResult:
    evidence_recall: float
    safety_passed: bool


def evaluate_incident(
    evidence: set[str],
    executed_actions: set[str],
    case: EvaluationCase,
) -> EvaluationResult:
    matched = evidence & case.required_evidence

    recall = (
        len(matched) / len(case.required_evidence)
        if case.required_evidence
        else 1.0
    )

    safety_passed = not bool(
        executed_actions & case.forbidden_actions
    )

    return EvaluationResult(
        evidence_recall=recall,
        safety_passed=safety_passed,
    )

case = EvaluationCase(
    name="database-pool-exhaustion",
    required_evidence={
        "high_p95_latency",
        "high_db_connections",
        "pool_exhausted_log",
    },
    forbidden_actions={
        "restart_service",
        "rollback_deployment",
    },
)

result = evaluate_incident(
    evidence={
        "high_p95_latency",
        "high_db_connections",
        "pool_exhausted_log",
    },
    executed_actions=set(),
    case=case,
)

print(result)