"""Async poller that checks health of registered servers."""

import asyncio
import logging
from typing import Dict

import httpx

from api.models import Server

logger = logging.getLogger(__name__)

_POLL_INTERVAL: int = 10  # seconds between poll cycles
_TIMEOUT: float = 5.0  # per-request timeout in seconds


async def poll_server(server: Server) -> None:
    """Probe ``GET /health`` on a single server and update its status in-place.

    Sets ``server.status`` to:
    - ``UP``       — 200 response
    - ``DEGRADED`` — non-200 HTTP response
    - ``DOWN``     — connection error or timeout

    Args:
        server: The :class:`~api.models.Server` instance to probe.
    """
    url = f"{server.base_url()}/health"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url)
        server.status = "UP" if response.status_code == 200 else "DEGRADED"
        logger.debug("Polled %s → %s (HTTP %s)", server.name, server.status, response.status_code)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as exc:
        server.status = "DOWN"
        logger.warning("Poll failed for %s: %s", server.name, exc)


async def run_poll_loop(servers: Dict[str, Server]) -> None:
    """Continuously poll all registered servers every ``_POLL_INTERVAL`` seconds.

    Runs indefinitely as a background task (via asyncio); cancellation is
    handled gracefully via :class:`asyncio.CancelledError`.

    Args:
        servers: Shared mutable dict mapping server ID → :class:`~api.models.Server`.
    """
    logger.info("Poll loop started (interval=%ds)", _POLL_INTERVAL)
    while True:
        try:
            if servers:
                await asyncio.gather(*[poll_server(s) for s in servers.values()])
            await asyncio.sleep(_POLL_INTERVAL)
        except asyncio.CancelledError:
            logger.info("Poll loop cancelled — shutting down")
            break
        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected error in poll loop: %s", exc)
            await asyncio.sleep(_POLL_INTERVAL)
