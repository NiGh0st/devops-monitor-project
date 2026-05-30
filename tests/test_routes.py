"""Tests for FastAPI routes in api/main.py."""

import os

from fastapi.testclient import TestClient

# Set API_KEY before importing the app so the env var is available
os.environ.setdefault("API_KEY", "test-secret-key")

from api.main import app  # noqa: E402 (must come after env setup)

client = TestClient(app)
VALID_KEY = "test-secret-key"
HEADERS = {"X-API-Key": VALID_KEY}


# ──────────────────────────────────────────────────────────────────────────────
# Health endpoint
# ──────────────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self):
        """GET /health must return {\"status\": \"ok\"} with HTTP 200."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# Metrics endpoint
# ──────────────────────────────────────────────────────────────────────────────

class TestMetrics:
    def test_metrics_status_200(self):
        """GET /metrics must return HTTP 200."""
        r = client.get("/metrics")
        assert r.status_code == 200

    def test_metrics_has_required_fields(self):
        """GET /metrics JSON must contain cpu, memory, disk fields."""
        r = client.get("/metrics")
        body = r.json()
        for field in ("cpu_percent", "memory_percent", "disk_percent"):
            assert field in body, f"Missing field: {field}"

    def test_metrics_values_in_range(self):
        """All percentage values must be between 0 and 100."""
        r = client.get("/metrics")
        body = r.json()
        for field in ("cpu_percent", "memory_percent", "disk_percent"):
            assert 0 <= body[field] <= 100, f"{field} out of range: {body[field]}"


# ──────────────────────────────────────────────────────────────────────────────
# Authentication
# ──────────────────────────────────────────────────────────────────────────────

class TestAuth:
    def test_post_servers_without_key_returns_403(self):
        """POST /servers without X-API-Key must return 403."""
        r = client.post("/servers", json={"name": "test", "host": "1.2.3.4", "port": 80})
        assert r.status_code == 403

    def test_post_servers_with_wrong_key_returns_403(self):
        """POST /servers with wrong key must return 403."""
        r = client.post(
            "/servers",
            json={"name": "test", "host": "1.2.3.4", "port": 80},
            headers={"X-API-Key": "wrong-key"},
        )
        assert r.status_code == 403

    def test_delete_server_without_key_returns_403(self):
        """DELETE /servers/{id} without key must return 403."""
        r = client.delete("/servers/nonexistent-id")
        assert r.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# Servers CRUD
# ──────────────────────────────────────────────────────────────────────────────

class TestServers:
    def test_create_server_returns_201(self):
        """POST /servers with valid key must return 201 and server data."""
        r = client.post(
            "/servers",
            json={"name": "web-01", "host": "10.0.0.1", "port": 8080},
            headers=HEADERS,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "web-01"
        assert body["host"] == "10.0.0.1"
        assert body["port"] == 8080
        assert "id" in body
        assert "status" in body

    def test_list_servers_returns_200(self):
        """GET /servers must return 200 and a list."""
        r = client.get("/servers")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_servers_contains_created_server(self):
        """GET /servers must include a server that was just created."""
        # Create a server
        create_r = client.post(
            "/servers",
            json={"name": "list-check", "host": "10.0.0.2", "port": 9090},
            headers=HEADERS,
        )
        server_id = create_r.json()["id"]

        list_r = client.get("/servers")
        ids = [s["id"] for s in list_r.json()]
        assert server_id in ids

    def test_delete_server_returns_204(self):
        """DELETE /servers/{id} must return 204 for a valid server."""
        create_r = client.post(
            "/servers",
            json={"name": "delete-me", "host": "10.0.0.3", "port": 7070},
            headers=HEADERS,
        )
        server_id = create_r.json()["id"]

        del_r = client.delete(f"/servers/{server_id}", headers=HEADERS)
        assert del_r.status_code == 204

    def test_delete_nonexistent_server_returns_404(self):
        """DELETE /servers/{id} for unknown id must return 404."""
        r = client.delete("/servers/does-not-exist", headers=HEADERS)
        assert r.status_code == 404

    def test_create_server_invalid_port_returns_422(self):
        """POST /servers with port > 65535 must return 422 (validation error)."""
        r = client.post(
            "/servers",
            json={"name": "bad", "host": "1.1.1.1", "port": 99999},
            headers=HEADERS,
        )
        assert r.status_code == 422

    def test_check_server_not_found_returns_404(self):
        """POST /servers/{id}/check for unknown id must return 404."""
        r = client.post("/servers/nonexistent-id/check", headers=HEADERS)
        assert r.status_code == 404
