"""Tests for api/poller.py and api/main.py lifespan/WebSocket."""

import asyncio
import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("API_KEY", "test-secret-key")

from api.main import app  # noqa: E402
from api.models import Server  # noqa: E402
from api.poller import poll_server, run_poll_loop  # noqa: E402

client = TestClient(app)
HEADERS = {"X-API-Key": "test-secret-key"}


# ──────────────────────────────────────────────────────────────────────────────
# Poller — poll_server
# ──────────────────────────────────────────────────────────────────────────────

class TestPollServer:
    """Tests for the poll_server coroutine."""

    @pytest.mark.anyio
    async def test_poll_server_down_on_connection_error(self):
        """A server on an unreachable host must be marked DOWN."""
        server = Server(name="unreachable", host="192.0.2.1", port=9999)
        await poll_server(server)
        assert server.status == "DOWN"

    @pytest.mark.anyio
    async def test_poll_server_base_url(self):
        """Server.base_url() must return the correct HTTP URL."""
        server = Server(name="s1", host="10.0.0.1", port=8080)
        assert server.base_url() == "http://10.0.0.1:8080"

    @pytest.mark.anyio
    async def test_poll_server_initial_status_unknown(self):
        """A freshly created server must have UNKNOWN status."""
        server = Server(name="s2", host="10.0.0.2", port=80)
        assert server.status == "UNKNOWN"

    @pytest.mark.anyio
    async def test_run_poll_loop_cancels_cleanly(self):
        """run_poll_loop must exit gracefully when cancelled."""
        servers = {}
        task = asyncio.create_task(run_poll_loop(servers))
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert task.done()

    @pytest.mark.anyio
    async def test_run_poll_loop_with_empty_servers(self):
        """run_poll_loop with no servers must not raise."""
        servers = {}
        task = asyncio.create_task(run_poll_loop(servers))
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# WebSocket endpoint
# ──────────────────────────────────────────────────────────────────────────────

class TestWebSocket:
    """Tests for the /ws/metrics WebSocket endpoint."""

    def test_websocket_sends_json_frame(self):
        """WebSocket /ws/metrics must send a valid JSON frame."""
        import json

        with client.websocket_connect("/ws/metrics") as ws:
            data = ws.receive_text()
            parsed = json.loads(data)
            assert "cpu_percent" in parsed
            assert "memory_percent" in parsed
            assert "disk_percent" in parsed

    def test_websocket_frame_values_in_range(self):
        """WebSocket frame values must be 0–100."""
        import json

        with client.websocket_connect("/ws/metrics") as ws:
            data = ws.receive_text()
            parsed = json.loads(data)
            for key in ("cpu_percent", "memory_percent", "disk_percent"):
                assert 0 <= parsed[key] <= 100, f"{key} out of range"

    def test_websocket_sends_multiple_frames(self):
        """WebSocket must send at least 2 frames consecutively."""
        import json

        with client.websocket_connect("/ws/metrics") as ws:
            frames = [json.loads(ws.receive_text()) for _ in range(2)]
        assert len(frames) == 2
        for frame in frames:
            assert "cpu_percent" in frame


# ──────────────────────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────────────────────────────────────

class TestLifespan:
    """Tests that verify the app starts and stops cleanly via TestClient context manager."""

    def test_app_starts_and_health_ok(self):
        """App must return /health ok after lifespan startup."""
        with TestClient(app) as c:
            r = c.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}
