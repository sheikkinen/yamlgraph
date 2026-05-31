"""Tests for the append-only capability registry (FR-178).

Validates:
  - Registry YAML files pass schema validation
  - req_coverage.py loads capabilities from registry
  - Aggregation script produces valid ARCHITECTURE.md content
  - Validate script catches common errors
"""

from __future__ import annotations

import importlib.util
import re
import textwrap
from pathlib import Path
from unittest import mock

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_module(name: str, script_path: Path):
    """Import a script module by file path."""
    spec = importlib.util.spec_from_file_location(name, script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.req("REQ-YG-161")
class TestCapabilityRegistry:
    """Capability registry YAML files must pass schema validation."""

    def test_registry_directory_exists(self) -> None:
        """capabilities/ directory must exist."""
        assert (REPO_ROOT / "capabilities").is_dir()

    def test_registry_has_capability_files(self) -> None:
        """Registry must contain at least 60 capability YAML files."""
        files = list((REPO_ROOT / "capabilities").glob("CAP-*.yaml"))
        assert len(files) >= 60, f"Expected >= 60 capability files, found {len(files)}"

    def test_all_files_valid_yaml(self) -> None:
        """Every capability file must be valid YAML."""
        for fp in sorted((REPO_ROOT / "capabilities").glob("CAP-*.yaml")):
            data = yaml.safe_load(fp.read_text())
            assert isinstance(data, dict), f"{fp.name}: expected mapping"

    def test_validate_capabilities_passes(self) -> None:
        """validate_capabilities.py must report zero errors on the registry."""
        mod = _load_module(
            "validate_capabilities",
            REPO_ROOT / "scripts" / "validate_capabilities.py",
        )
        errors, _caps = mod.validate_registry()
        assert errors == [], f"Validation errors: {errors}"

    def test_no_retired_ids_in_registry(self) -> None:
        """Retired capability IDs must not have YAML files."""
        mod = _load_module(
            "validate_capabilities",
            REPO_ROOT / "scripts" / "validate_capabilities.py",
        )
        retired = set(mod.RETIRED_CAPS.keys())
        for fp in (REPO_ROOT / "capabilities").glob("CAP-*.yaml"):
            cap_id_match = re.match(r"(CAP-\d+)", fp.name)
            if cap_id_match:
                assert (
                    cap_id_match.group(1) not in retired
                ), f"{fp.name} uses retired ID {cap_id_match.group(1)}"

    def test_ids_match_filenames(self) -> None:
        """Each file's id field must match its filename prefix."""
        for fp in sorted((REPO_ROOT / "capabilities").glob("CAP-*.yaml")):
            data = yaml.safe_load(fp.read_text())
            expected = re.match(r"(CAP-\d+)", fp.name).group(1)
            assert (
                str(data["id"]) == expected
            ), f"{fp.name}: id '{data['id']}' != filename '{expected}'"

    def test_no_duplicate_requirement_ids(self) -> None:
        """No two capabilities may share a requirement ID."""
        seen: dict[str, str] = {}
        for fp in sorted((REPO_ROOT / "capabilities").glob("CAP-*.yaml")):
            data = yaml.safe_load(fp.read_text())
            for req in data.get("requirements", []):
                req_id = str(req["id"])
                assert (
                    req_id not in seen
                ), f"Duplicate {req_id}: in {data['id']} and {seen[req_id]}"
                seen[req_id] = str(data["id"])


@pytest.mark.req("REQ-YG-161")
class TestReqCoverageLoadsFromRegistry:
    """req_coverage.py must load CAPABILITIES from YAML registry."""

    def test_capabilities_loaded(self) -> None:
        """CAPABILITIES dict must be non-empty and loaded from YAML files."""
        mod = _load_module(
            "req_coverage",
            REPO_ROOT / "scripts" / "req_coverage.py",
        )
        assert len(mod.CAPABILITIES) >= 60
        assert len(mod.ALL_REQS) >= 116

    def test_all_reqs_derived_from_registry(self) -> None:
        """ALL_REQS must contain exactly the requirements from YAML files."""
        mod = _load_module(
            "req_coverage",
            REPO_ROOT / "scripts" / "req_coverage.py",
        )

        # Collect directly from YAML files, excluding retired CAPs
        yaml_reqs: set[str] = set()
        for fp in (REPO_ROOT / "capabilities").glob("CAP-*.yaml"):
            data = yaml.safe_load(fp.read_text())
            if data.get("status") == "retired":
                continue
            for req in data.get("requirements", []):
                yaml_reqs.add(str(req["id"]))

        assert set(mod.ALL_REQS) == yaml_reqs


@pytest.mark.req("REQ-YG-161")
class TestValidateCapabilitiesErrors:
    """validate_capabilities.py must detect schema violations."""

    def test_catches_missing_fields(self, tmp_path: Path) -> None:
        """Missing required fields produce errors."""
        cap_dir = tmp_path / "capabilities"
        cap_dir.mkdir()
        (cap_dir / "CAP-99-test.yaml").write_text("id: CAP-99\nname: Test\n")

        mod = _load_module(
            "validate_capabilities",
            REPO_ROOT / "scripts" / "validate_capabilities.py",
        )
        with mock.patch.object(mod, "CAPABILITIES_DIR", cap_dir):
            errors, _caps = mod.validate_registry()
        assert any("Missing required fields" in e for e in errors)

    def test_catches_retired_id_reuse(self, tmp_path: Path) -> None:
        """Reusing a retired ID produces an error."""
        cap_dir = tmp_path / "capabilities"
        cap_dir.mkdir()
        content = textwrap.dedent("""\
            id: CAP-27
            name: Test
            description: Test
            modules: [test]
            requirements:
              - id: REQ-YG-999
                description: Test
                modules: [test]
            fr: legacy
        """)
        (cap_dir / "CAP-27-test.yaml").write_text(content)

        mod = _load_module(
            "validate_capabilities",
            REPO_ROOT / "scripts" / "validate_capabilities.py",
        )
        with mock.patch.object(mod, "CAPABILITIES_DIR", cap_dir):
            errors, _caps = mod.validate_registry()
        assert any("retired" in e for e in errors)

    def test_catches_duplicate_req_ids(self, tmp_path: Path) -> None:
        """Duplicate requirement IDs across files produce errors."""
        cap_dir = tmp_path / "capabilities"
        cap_dir.mkdir()

        for num, name in [(98, "first"), (99, "second")]:
            content = textwrap.dedent(f"""\
                id: CAP-{num}
                name: {name}
                description: Test capability
                modules: [test]
                requirements:
                  - id: REQ-YG-999
                    description: Duplicate req
                    modules: [test]
                fr: legacy
            """)
            (cap_dir / f"CAP-{num}-{name}.yaml").write_text(content)

        mod = _load_module(
            "validate_capabilities",
            REPO_ROOT / "scripts" / "validate_capabilities.py",
        )
        with mock.patch.object(mod, "CAPABILITIES_DIR", cap_dir):
            errors, _caps = mod.validate_registry()
        assert any("Duplicate requirement ID" in e for e in errors)

    def test_catches_id_mismatch(self, tmp_path: Path) -> None:
        """ID not matching filename produces an error."""
        cap_dir = tmp_path / "capabilities"
        cap_dir.mkdir()
        content = textwrap.dedent("""\
            id: CAP-98
            name: Mismatch
            description: Test
            modules: [test]
            requirements:
              - id: REQ-YG-998
                description: Test
                modules: [test]
            fr: legacy
        """)
        (cap_dir / "CAP-99-mismatch.yaml").write_text(content)

        mod = _load_module(
            "validate_capabilities",
            REPO_ROOT / "scripts" / "validate_capabilities.py",
        )
        with mock.patch.object(mod, "CAPABILITIES_DIR", cap_dir):
            errors, _caps = mod.validate_registry()
        assert any("ID mismatch" in e or "does not match" in e for e in errors)


@pytest.mark.req("REQ-YG-161")
class TestArchitectureGenerationMarkers:
    """ARCHITECTURE.md must have generation markers for capabilities."""

    def test_architecture_has_begin_marker(self) -> None:
        """ARCHITECTURE.md must contain BEGIN GENERATED CAPABILITIES marker."""
        text = (REPO_ROOT / "ARCHITECTURE.md").read_text()
        assert "<!-- BEGIN GENERATED CAPABILITIES -->" in text

    def test_architecture_has_end_marker(self) -> None:
        """ARCHITECTURE.md must contain END GENERATED CAPABILITIES marker."""
        text = (REPO_ROOT / "ARCHITECTURE.md").read_text()
        assert "<!-- END GENERATED CAPABILITIES -->" in text

    def test_begin_before_end(self) -> None:
        """BEGIN marker must appear before END marker."""
        text = (REPO_ROOT / "ARCHITECTURE.md").read_text()
        begin_idx = text.find("<!-- BEGIN GENERATED CAPABILITIES -->")
        end_idx = text.find("<!-- END GENERATED CAPABILITIES -->")
        assert begin_idx < end_idx

    def test_generated_content_has_summary_table(self) -> None:
        """Generated content must include a capability summary table."""
        text = (REPO_ROOT / "ARCHITECTURE.md").read_text()
        begin = text.find("<!-- BEGIN GENERATED CAPABILITIES -->")
        end = text.find("<!-- END GENERATED CAPABILITIES -->")
        generated = text[begin:end]
        assert "### Capability Summary" in generated
        assert "| # | Capability | Primary Modules | Requirements |" in generated

    def test_generated_content_has_all_capabilities(self) -> None:
        """Core capabilities from the registry must appear in the generated content."""
        text = (REPO_ROOT / "ARCHITECTURE.md").read_text()
        begin = text.find("<!-- BEGIN GENERATED CAPABILITIES -->")
        end = text.find("<!-- END GENERATED CAPABILITIES -->")
        generated = text[begin:end]

        # Spot-check core capabilities that must always be present
        for cap_num in [1, 2, 3, 4, 5, 10, 17, 19, 30, 64]:
            assert (
                f"| {cap_num} |" in generated
            ), f"CAP-{cap_num} missing from generated summary table"

    def test_generated_content_has_requirement_ids(self) -> None:
        """Generated content must reference REQ-YG-XXX IDs from registry."""
        text = (REPO_ROOT / "ARCHITECTURE.md").read_text()
        begin = text.find("<!-- BEGIN GENERATED CAPABILITIES -->")
        end = text.find("<!-- END GENERATED CAPABILITIES -->")
        generated = text[begin:end]

        # Spot-check a few key requirements
        assert "REQ-YG-001" in generated
        assert "REQ-YG-050" in generated
