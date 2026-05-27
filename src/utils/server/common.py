from typing import TypeVar

from fastapi import Response

from .data import ApiResponse

T = TypeVar("T")


def api_response(
    status: int,
    message: str,
    response: T,
    *,
    http_response: Response | None = None,
) -> ApiResponse[T]:
    body = ApiResponse(status=status, message=message, response=response)
    if http_response is not None:
        http_response.status_code = status
    return body
