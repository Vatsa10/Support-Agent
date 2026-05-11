import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from observability.logging import get_logger, request_id_var
from observability.metrics import HTTP_REQUESTS, HTTP_LATENCY

log = get_logger("http")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_var.set(rid)
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            elapsed = time.perf_counter() - start
            path = request.url.path
            HTTP_REQUESTS.labels(method=request.method, path=path, status=str(status)).inc()
            HTTP_LATENCY.labels(method=request.method, path=path).observe(elapsed)
            log.info(
                "request",
                extra={
                    "method": request.method,
                    "path": path,
                    "status": status,
                    "elapsed_s": round(elapsed, 4),
                },
            )
            request_id_var.reset(token)
