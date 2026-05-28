"""FastAPI application — DevOps Monitoring Dashboard backend."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from api.auth import verify_api_key
from api.metrics import get_system_metrics
from api.models import Server, ServerIn, ServerOut
from api.poller import run_poll_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

# In-memory server registry (shared mutable state)
servers: Dict[str, Server] = {}

_poll_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the background poll loop on startup; cancel it on shutdown."""
    global _poll_task
    _poll_task = asyncio.create_task(run_poll_loop(servers))
    logger.info("Background poll loop started")
    yield
    if _poll_task:
        _poll_task.cancel()
        try:
            await _poll_task
        except asyncio.CancelledError:
            pass
    logger.info("Background poll loop stopped")


app = FastAPI(
    title="DevOps Monitoring API",
    description="Real-time system metrics and server health monitoring.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health() -> dict:
    """Liveness probe — always returns ``{\"status\": \"ok\"}``."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@app.get("/metrics", tags=["System"])
async def metrics() -> dict:
    """Return a real-time snapshot of CPU, memory, and disk usage."""
    return get_system_metrics()


# ---------------------------------------------------------------------------
# Servers CRUD
# ---------------------------------------------------------------------------

@app.post("/servers", response_model=ServerOut, status_code=status.HTTP_201_CREATED, tags=["Servers"])
async def create_server(
    payload: ServerIn,
    _: str = Depends(verify_api_key),
) -> ServerOut:
    """Register a new server to monitor.

    Requires ``X-API-Key`` header.
    """
    server = Server(name=payload.name, host=payload.host, port=payload.port)
    servers[server.id] = server
    logger.info("Registered server %s (%s)", server.name, server.id)
    return ServerOut(
        id=server.id,
        name=server.name,
        host=server.host,
        port=server.port,
        status=server.status,
    )


@app.get("/servers", response_model=list[ServerOut], tags=["Servers"])
async def list_servers() -> list[ServerOut]:
    """List all registered servers with their current health status."""
    return [
        ServerOut(id=s.id, name=s.name, host=s.host, port=s.port, status=s.status)
        for s in servers.values()
    ]


@app.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Servers"])
async def delete_server(
    server_id: str,
    _: str = Depends(verify_api_key),
) -> None:
    """Remove a server from the registry.

    Requires ``X-API-Key`` header.

    Raises:
        HTTPException: 404 if ``server_id`` is not found.
    """
    if server_id not in servers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    del servers[server_id]
    logger.info("Deleted server %s", server_id)


@app.post("/servers/{server_id}/check", response_model=ServerOut, tags=["Servers"])
async def check_server(
    server_id: str,
    _: str = Depends(verify_api_key),
) -> ServerOut:
    """Trigger an immediate health check for a specific server.

    Requires ``X-API-Key`` header.

    Raises:
        HTTPException: 404 if ``server_id`` is not found.
    """
    from api.poller import poll_server  # local import to avoid circular

    if server_id not in servers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    server = servers[server_id]
    await poll_server(server)
    return ServerOut(id=server.id, name=server.name, host=server.host, port=server.port, status=server.status)


# ---------------------------------------------------------------------------
# WebSocket — live metrics stream
# ---------------------------------------------------------------------------

@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket) -> None:
    """Stream system metrics as JSON every second.

    Sends one JSON frame per second until the client disconnects.
    Handles :class:`~fastapi.WebSocketDisconnect` gracefully.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")
    try:
        while True:
            data = get_system_metrics()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
