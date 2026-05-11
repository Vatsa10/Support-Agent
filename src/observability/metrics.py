from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response


HTTP_REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests by method, path, status",
    ["method", "path", "status"],
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)

TOOL_RUNS = Counter(
    "tool_runs_total",
    "Tool invocations by tool and status",
    ["tool", "status"],
)

TOKEN_TOTAL = Counter(
    "tokens_total",
    "LLM tokens consumed by event_type",
    ["event_type"],
)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
