import logging
import time
import traceback
import uuid
from collections.abc import Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)

        start = time.perf_counter()

        try:
            response: Response = await call_next(request)
            duration = round((time.perf_counter() - start) * 1000, 2)

            extra = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": f"{duration} ms",
            }

            if response.status_code >= 400 and response.status_code < 500:
                logger.warning("Client error encountered", extra=extra)

            if response.status_code >= 500:
                logger.error(
                    msg=f"Internal several error encountered: {traceback.format_exc()}",
                    extra=extra,
                )

            return response

        except Exception as e:
            duration = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                f"Request failed: {e!s}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration": f"{duration} ms",
                },
            )

            raise
