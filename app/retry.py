"""Retry wrapper for httpx API calls with exponential backoff."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import cast

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUSES: frozenset[int] = frozenset({429, 500, 502, 503, 504})
RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    httpx.ReadError,
    httpx.WriteError,
)
MAX_RETRIES = 3
_BACKOFF_SECONDS: list[float] = [1.0, 2.0, 4.0]
_RATE_LIMIT_STATUS = 429
_SERVER_ERROR_THRESHOLD = 500


def _retry_after_seconds(response: httpx.Response) -> float:
    header = cast("str", response.headers.get("Retry-After", ""))
    if not header:
        return 0.0
    return float(header)


async def retry_request(
    request: Callable[[], Awaitable[httpx.Response]],
    max_retries: int = MAX_RETRIES,
) -> httpx.Response:
    last_exception: BaseException | None = None
    delay: float = 0.0

    for attempt in range(max_retries + 1):
        if attempt > 0:
            await asyncio.sleep(delay)
        try:
            response = await request()
            is_failure = (
                response.status_code >= _SERVER_ERROR_THRESHOLD
                or response.status_code == _RATE_LIMIT_STATUS
            )
            if not is_failure:
                return response
            if attempt == max_retries:
                return response
            delay = _retry_after_seconds(response)
            if delay == 0.0:
                delay = _BACKOFF_SECONDS[attempt]
            logger.warning(
                "Retrying after HTTP %d from %s (attempt %d/%d)",
                response.status_code,
                response.url,
                attempt + 1,
                max_retries,
            )
        except RETRYABLE_EXCEPTIONS as exc:
            if attempt == max_retries:
                raise
            last_exception = exc
            delay = _BACKOFF_SECONDS[attempt]
            logger.warning(
                "Retrying after %s (attempt %d/%d): %s",
                type(exc).__name__,
                attempt + 1,
                max_retries,
                exc,
            )
    if last_exception is not None:
        raise last_exception
    msg = f"Request failed after {max_retries} retries"
    raise RuntimeError(msg)
