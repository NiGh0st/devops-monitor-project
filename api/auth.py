"""API key authentication dependency for FastAPI."""

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """FastAPI dependency that validates the X-API-Key header.

    Reads the expected key from the ``API_KEY`` environment variable.

    Args:
        api_key: Value from the ``X-API-Key`` request header.

    Returns:
        The validated API key string.

    Raises:
        HTTPException: 403 if the key is missing or incorrect.
    """
    expected = os.getenv("API_KEY", "")
    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return api_key
