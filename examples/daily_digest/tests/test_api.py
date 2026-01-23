"""Tests for the FastAPI application."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add digest dir to path for imports
DIGEST_DIR = Path(__file__).parent.parent.resolve()
if str(DIGEST_DIR) not in sys.path:
    sys.path.insert(0, str(DIGEST_DIR))


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    # Set required env vars before import
    import os

    os.environ["DIGEST_API_TOKEN"] = "test-token"

    # Clear rate limiter state by reimporting
    import importlib

    import api.app

    importlib.reload(api.app)

    from api.app import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Valid auth headers."""
    return {"Authorization": "Bearer test-token"}


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_healthy(self, client):
        """Health check should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRunEndpoint:
    """Tests for /run endpoint."""

    def test_run_requires_auth(self, client):
        """Run endpoint should require authentication."""
        response = client.post("/run", json={"topics": ["AI"]})
        # FastAPI HTTPBearer returns 403 for missing header
        assert response.status_code in (401, 403)

    def test_run_rejects_invalid_token(self, client):
        """Run endpoint should reject invalid tokens."""
        response = client.post(
            "/run",
            json={"topics": ["AI"]},
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 401

    def test_run_returns_202_accepted(self, client, auth_headers):
        """Run endpoint should return 202 Accepted immediately."""
        with patch("api.app.run_pipeline"):
            response = client.post(
                "/run",
                json={"topics": ["AI", "Python"]},
                headers=auth_headers,
            )

        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        assert "started" in response.json()["message"].lower()

    def test_run_triggers_background_task(self, client, auth_headers):
        """Run endpoint should trigger the pipeline in background."""
        with patch("api.app.run_pipeline") as mock_run:
            response = client.post(
                "/run",
                json={"topics": ["AI"]},
                headers=auth_headers,
            )
            # TestClient runs background tasks synchronously after response
            assert response.status_code == 202

        # Background task should have been called
        mock_run.assert_called_once()

    def test_run_passes_topics_to_pipeline(self, client, auth_headers):
        """Run endpoint should pass topics to the pipeline."""
        with patch("api.app.run_pipeline") as mock_run:
            response = client.post(
                "/run",
                json={"topics": ["Rust", "WebAssembly"]},
                headers=auth_headers,
            )
            assert response.status_code == 202

        # Check the topics passed to run_pipeline
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["Rust", "WebAssembly"]

    def test_run_uses_default_topics(self, client, auth_headers):
        """Run endpoint should use default topics if none provided."""
        with patch("api.app.run_pipeline") as mock_run:
            response = client.post(
                "/run",
                json={},
                headers=auth_headers,
            )
            assert response.status_code == 202

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        topics = call_args[0][0]
        assert "AI" in topics
        assert "Python" in topics
