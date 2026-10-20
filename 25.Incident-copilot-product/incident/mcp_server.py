import json

from fastmcp import FastMCP

mcp = FastMCP("incident-observability")


@mcp.tool()
def query_metrics(service: str) -> str:
    """Read recent service metrics. Return authoritative source IDs."""
    if service != "checkout-api":
        return json.dumps({
            "error": "service_not_found",
            "service": service,
        })

    return json.dumps({
        "source_id": "METRIC-001",
        "service": service,
        "window": "mock-incident-window",
        "p95_latency_ms": 2400,
        "baseline_p95_latency_ms": 180,
        "error_rate_percent": 12.5,
        "db_connections": 95,
        "db_connection_limit": 100,
    })


@mcp.tool()
def search_logs(service: str) -> str:
    """Read service logs with their evidence source IDs."""
    if service != "checkout-api":
        return json.dumps({
            "error": "service_not_found",
            "service": service,
        })

    return json.dumps({
        "source_id": "LOG-001",
        "service": service,
        "entries": [
            "ERROR database connection pool exhausted",
            "WARN connection acquisition timeout: 3000ms",
            "ERROR POST /checkout HTTP 503",
            "INFO recent deployment checkout-api v2.4.1",
        ],
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")
