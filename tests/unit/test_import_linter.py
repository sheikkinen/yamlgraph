"""Tests for import-linter architectural boundary enforcement (FR-218).

Verifies that the three-layer architecture (Presentation → Logic → Side Effects)
is mechanically enforced via import-linter contracts, not just documented.
"""

import configparser
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestImportLinterConfig:
    """Verify .importlinter configuration exists and declares layer contracts."""

    @pytest.mark.req("REQ-YG-218")
    def test_importlinter_config_exists(self):
        """.importlinter config file must exist at repo root."""
        config_path = REPO_ROOT / ".importlinter"
        assert config_path.exists(), (
            ".importlinter config file not found at repo root. "
            "FR-218 requires import-linter layer contracts."
        )

    @pytest.mark.req("REQ-YG-218")
    def test_importlinter_config_declares_root_package(self):
        """Config must declare yamlgraph as root_package."""
        config_path = REPO_ROOT / ".importlinter"
        config = configparser.ConfigParser()
        config.read(config_path)
        assert config.has_section(
            "importlinter"
        ), "Missing [importlinter] section in .importlinter"
        assert config.get("importlinter", "root_package") == "yamlgraph"

    @pytest.mark.req("REQ-YG-218")
    def test_importlinter_config_declares_three_layer_contract(self):
        """Config must declare a layers contract named 'three-layer'."""
        config_path = REPO_ROOT / ".importlinter"
        config = configparser.ConfigParser()
        config.read(config_path)
        section = "importlinter:contract:three-layer"
        assert config.has_section(
            section
        ), f"Missing [{section}] section in .importlinter"
        assert config.get(section, "type") == "layers"

    @pytest.mark.req("REQ-YG-218")
    def test_three_layer_contract_has_three_layers(self):
        """The layers contract must define exactly 3 layers."""
        config_path = REPO_ROOT / ".importlinter"
        config = configparser.ConfigParser()
        config.read(config_path)
        layers_raw = config.get("importlinter:contract:three-layer", "layers")
        layers = [
            line.strip() for line in layers_raw.strip().splitlines() if line.strip()
        ]
        assert (
            len(layers) == 3
        ), f"Expected 3 layers (Presentation, Logic, Side Effects), got {len(layers)}: {layers}"

    @pytest.mark.req("REQ-YG-218")
    def test_cli_is_top_layer(self):
        """Layer 1 (Presentation) must be yamlgraph.cli."""
        config_path = REPO_ROOT / ".importlinter"
        config = configparser.ConfigParser()
        config.read(config_path)
        layers_raw = config.get("importlinter:contract:three-layer", "layers")
        layers = [
            line.strip() for line in layers_raw.strip().splitlines() if line.strip()
        ]
        assert (
            layers[0] == "yamlgraph.cli"
        ), f"Layer 1 (Presentation) must be yamlgraph.cli, got: {layers[0]}"


class TestImportLinterExecution:
    """Verify lint-imports runs successfully against the codebase."""

    @pytest.mark.req("REQ-YG-218")
    def test_lint_imports_passes(self):
        """lint-imports must exit 0 on the current codebase (zero violations)."""
        lint_imports = Path(sys.executable).parent / "lint-imports"
        result = subprocess.run(
            [str(lint_imports)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"lint-imports failed with exit code {result.returncode}.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
