import json
import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

MAX_BODY_LOG = 2000
_REQUEST_ID_HEADER = "X-Request-ID"
_REDACTED_KEYS = frozenset({"audio_bytes"})
_SKIP_PATHS = frozenset({"/docs", "/redoc", "/openapi.json", "/favicon.ico"})


def _truncate(text: str, max_len: int = MAX_BODY_LOG) -> str:
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}... ({len(text)} chars total)"


def _redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<redacted>" if key in _REDACTED_KEYS else _redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    return value


def _format_body(body: bytes, content_type: str | None) -> str:
    if not body:
        return ""
    text = body.decode("utf-8", errors="replace")
    if content_type and "json" in content_type.lower():
        try:
            text = json.dumps(_redact_sensitive(json.loads(text)), ensure_ascii=False)
        except json.JSONDecodeError:
            pass
    return _truncate(text)


def _should_skip_logging(path: str) -> bool:
    return path in _SKIP_PATHS


def _target(path: str, query: str) -> str:
    return f"{path}?{query}" if query else path


class APILoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP API requests and responses (WebSocket traffic is not handled here)."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if _should_skip_logging(request.url.path):
            return await call_next(request)

        request_id = str(uuid.uuid4())
        start = time.perf_counter()
        method = request.method
        path = request.url.path
        query = request.url.query
        target = _target(path, query)
        client = request.client.host if request.client else "unknown"
        content_type = request.headers.get("content-type")

        body = await request.body()
        request_log = _format_body(body, content_type) or "-"

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive)
        request.state.request_id = request_id

        logging.info(
            "API request [%s] %s %s client=%s req=%s",
            request_id,
            method,
            target,
            client,
            request_log,
        )

        try:
            response = await call_next(request)
            response_body = b"".join([chunk async for chunk in response.body_iterator])
            duration_ms = (time.perf_counter() - start) * 1000
            response_log = _format_body(response_body, response.headers.get("content-type")) or "-"

            log_line = (
                f"API response [{request_id}] {method} {target} -> {response.status_code} "
                f"({duration_ms:.1f}ms) res={response_log}"
            )
            if response.status_code >= 500:
                logging.error(log_line)
            elif response.status_code >= 400:
                logging.warning(log_line)
            else:
                logging.info(log_line)

            headers = dict(response.headers)
            headers[_REQUEST_ID_HEADER] = request_id
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            log_line = (
                f"API response [{request_id}] {method} {target} failed after {duration_ms:.1f}ms"
            )
            logging.exception(log_line)
            raise
