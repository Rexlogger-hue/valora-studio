"""
services/api/limiter.py

Centralized rate limiter configuration for the Valora AI API using SlowAPI.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_rate_limit_key(request: Request) -> str:
    """
    Determine the rate-limiting key for a request.

    Prefers the 'X-API-Key' header when present (ideal for API clients
    and traffic routed through proxies like ngrok), and falls back to
    the client IP address when no key is provided.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key.strip():
        return f"api_key:{api_key.strip()}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=get_rate_limit_key,
    headers_enabled=True,
)
