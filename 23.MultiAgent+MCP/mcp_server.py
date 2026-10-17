from mcp.server.fastmcp import FastMCP

mcp = FastMCP("incident-monitoring")


@mcp.tool()
def query_metrics(service: str) -> dict:
    """Get recent latency, error rate and DB connections."""
    if service != "checkout-api":
        return {"error": f"Unknown service: {service}"}

    return {
        "service": service,
        "p95_latency_ms": 2400,
        "baseline_p95_latency_ms": 100,
        "error_rate_percent": 12.5,
        "db_connections": 95,
        "db_connection_limit": 100
    }


@mcp.tool()
def search_logs(service: str) -> dict:
    """Get recent application logs for a service."""
    if service != "checkout-api":
        return {"error": f"Unknown service: {service}"}

    return {
        "logs": [
            "ERROR database connection pool exhausted",
            "WARN connection acquisition timeout: 3000ms",
            "ERROR POST /checkout returned HTTP 503",
            "INFO deployment checkout-api v2.4.1",
        ]
    }


@mcp.tool()
def search_runbook(topic: str) -> dict:
    """Find incident response procedures by topic."""
    procedures = {
        "database": (
            "Inspect active connections and slow queries. "
            "Do not modify pool settings without approval."
        ),
        "latency": (
            "Compare p95 latency against baseline and inspect logs."
        ),
        "rollback": (
            "Verify deployment correlation. "
            "Require human approval before rollback."
        ),
    }

    matches = {
        key: value
        for key, value in procedures.items()
        if key in topic.lower() or topic.lower() in key
    }

    return {"procedures": matches or procedures}


if __name__ == "__main__":
    mcp.run(transport="stdio")
