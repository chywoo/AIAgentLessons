from langchain.tools import tool


@tool
def query_metrics(service: str) -> dict:
    """Get recent service latency, error rate, CPU usage, and database connections."""
    if service != "checkout-api":
        return {"error": f"No metric data for service: {service}"}

    return {
        "service": service,
        "p95_latency_ms": 2400,
        "baseline_p95_latency_ms": 180,
        "error_rate_percent": 12.5,
        "cpu_percent": 42,
        "database_connections": 95,
        "database_connection_limit": 100,
    }


@tool
def search_logs(service: str, keyword: str = "") -> dict:
    """Search recent application error logs for a service."""
    if service != "checkout-api":
        return {"error": f"No logs for service: {service}"}

    logs = [
        "ERROR database connection pool exhausted",
        "WARN database connection acquisition timeout: 3000ms",
        "ERROR POST /checkout returned HTTP 503",
        "INFO recent deployment: checkout-api v2.4.1",
    ]

    if keyword:
        logs = [line for line in logs if keyword.lower() in line.lower()]

    return {"service": service, "logs": logs}


@tool
def search_runbook(topic: str) -> dict:
    """Search internal runbooks for investigation and remediation procedures."""
    runbooks = {
        "database": (
            "When the connection pool is exhausted, inspect active connections, "
            "slow queries, pool sizing, and recent deployments. "
            "Escalate to the on-call engineer before changing configuration."
        ),
        "latency": (
            "For elevated API p95 latency, compare metrics to baseline, "
            "inspect errors, and identify dependent service bottlenecks."
        ),
        "rollback": (
            "Verify the deployment is related to the incident. "
            "Obtain approval before rollback. Monitor the error rate afterward."
        ),
    }

    matches = {
        name: content
        for name, content in runbooks.items()
        if name in topic.lower() or topic.lower() in name
    }

    return {"matches": matches or runbooks}