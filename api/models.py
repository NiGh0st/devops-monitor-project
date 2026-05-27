"""Data models for server registry and API schemas."""

import uuid
from dataclasses import dataclass, field

from pydantic import BaseModel, Field


@dataclass
class Server:
    """Internal representation of a monitored server.

    Attributes:
        id: Unique identifier (UUID string).
        name: Human-readable label.
        host: Hostname or IP address.
        port: TCP port number (1–65535).
        status: Current health status — ``UP``, ``DEGRADED``, or ``DOWN``.
    """

    name: str
    host: str
    port: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "UNKNOWN"

    def base_url(self) -> str:
        """Return the HTTP base URL for this server.

        Returns:
            str: e.g. ``http://192.168.1.10:8080``
        """
        return f"http://{self.host}:{self.port}"


class ServerIn(BaseModel):
    """Pydantic schema for registering a new server."""

    name: str = Field(..., min_length=1, max_length=100, description="Server label")
    host: str = Field(..., min_length=1, description="Hostname or IP")
    port: int = Field(..., ge=1, le=65535, description="TCP port")


class ServerOut(BaseModel):
    """Pydantic schema returned by the API for a server entry."""

    id: str
    name: str
    host: str
    port: int
    status: str
