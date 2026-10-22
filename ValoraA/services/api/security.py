"""
services/api/security.py

Simple API key authentication for the Valora AI API.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from services.tts.config import settings


async def verify_api_key(x_api_key: str = Header(default=None)) -> None:
    """
    Verify the caller supplied a valid API key via the X-API-Key header.

    If VALORA_API_KEY is not configured in settings, authentication is
    skipped entirely (useful for local development).

    Args:
        x_api_key: The API key provided in the X-API-Key request header.

    Raises:
        HTTPException: 401 if the key is missing or incorrect.
    """
    if not settings.VALORA_API_KEY:
        return  # No key configured -- auth disabled (local dev mode).

    if x_api_key != settings.VALORA_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )