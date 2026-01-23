"""Tests for Fly.io deployment configuration."""

from pathlib import Path

import pytest


class TestFlyConfig:
    """Tests for fly.toml configuration."""

    @pytest.fixture
    def fly_toml_path(self):
        """Path to fly.toml."""
        return Path(__file__).parent.parent / "fly.toml"

    @pytest.fixture
    def dockerfile_path(self):
        """Path to Dockerfile."""
        return Path(__file__).parent.parent / "Dockerfile"

    def test_fly_toml_exists(self, fly_toml_path):
        """fly.toml should exist."""
        assert fly_toml_path.exists(), f"fly.toml not found at {fly_toml_path}"

    def test_fly_toml_has_app_name(self, fly_toml_path):
        """fly.toml should have app name."""
        content = fly_toml_path.read_text()
        assert "app = " in content

    def test_fly_toml_has_http_service(self, fly_toml_path):
        """fly.toml should configure HTTP service."""
        content = fly_toml_path.read_text()
        assert "[http_service]" in content
        assert "internal_port = 8000" in content

    def test_fly_toml_has_volume(self, fly_toml_path):
        """fly.toml should mount volume for SQLite."""
        content = fly_toml_path.read_text()
        assert "[mounts]" in content or "[[mounts]]" in content

    def test_dockerfile_exists(self, dockerfile_path):
        """Dockerfile should exist."""
        assert dockerfile_path.exists(), f"Dockerfile not found at {dockerfile_path}"

    def test_dockerfile_uses_python(self, dockerfile_path):
        """Dockerfile should use Python base image."""
        content = dockerfile_path.read_text()
        assert "python:" in content.lower() or "FROM python" in content

    def test_dockerfile_installs_booking(self, dockerfile_path):
        """Dockerfile should install booking deps."""
        content = dockerfile_path.read_text()
        assert "booking" in content or "pip install" in content
