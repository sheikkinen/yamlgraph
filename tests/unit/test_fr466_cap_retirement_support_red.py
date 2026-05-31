"""RED tests for FR-466: CAP retirement support.

Validates:
  - req_coverage.py excludes retired CAPs from coverage checks
  - validate_capabilities.py accepts status: retired files
  - test_capability_registry hardcoded retired set replaced by YAML status
"""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_module(name: str, script_path: Path):
    """Import a script module by file path."""
    spec = importlib.util.spec_from_file_location(name, script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_cap_file(
    cap_dir: Path, cap_num: int, name: str, req_id: str, *, status: str | None = None
) -> Path:
    """Create a minimal valid CAP YAML file."""
    lines = [
        f"id: CAP-{cap_num}",
        f"name: {name}",
    ]
    if status:
        lines.append(f"status: {status}")
    lines.extend(
        [
            "description: Test capability",
            "modules: [test]",
            "requirements:",
            f"  - id: {req_id}",
            "    description: Test requirement",
            "    modules: [test]",
            f"fr: FR-{cap_num}",
        ]
    )
    fp = cap_dir / f"CAP-{cap_num}-{name.lower().replace(' ', '-')}.yaml"
    fp.write_text("\n".join(lines) + "\n")
    return fp


@pytest.mark.req("REQ-YG-428")
class TestReqCoverageRetirementFiltering:
    """req_coverage.py must exclude retired CAPs from coverage checks."""

    def test_ac01_retired_cap_reqs_excluded_from_all_reqs(self, tmp_path: Path) -> None:
        """REQs from status: retired CAPs must not appear in ALL_REQS."""
        cap_dir = tmp_path / "capabilities"
        cap_dir.mkdir()
        _make_cap_file(cap_dir, 90, "Active", "REQ-YG-900")
        _make_cap_file(cap_dir, 91, "Retired", "REQ-YG-901", status="retired")

        mod = _load_module(
            "req_coverage",
            REPO_ROOT / "scripts" / "req_coverage.py",
        )
        with mock.patch.object(mod, "CAPABILITIES_DIR", cap_dir):
            all_reqs, capabilities = mod.load_capabilities_from_registry()

        assert "REQ-YG-900" in all_reqs
        assert "REQ-YG-901" not in all_reqs
        assert "CAP-90" in capabilities
        assert "CAP-91" not in capabilities

    def test_ac02_cap_without_status_defaults_to_active(self, tmp_path: Path) -> None:
        """CAPs without a status field are treated as active."""
        cap_dir = tmp_path / "capabilities"
        cap_dir.mkdir()
        _make_cap_file(cap_dir, 90, "No-Status", "REQ-YG-900")

        mod = _load_module(
            "req_coverage",
            REPO_ROOT / "scripts" / "req_coverage.py",
        )
        with mock.patch.object(mod, "CAPABILITIES_DIR", cap_dir):
            all_reqs, capabilities = mod.load_capabilities_from_registry()

        assert "REQ-YG-900" in all_reqs
        assert "CAP-90" in capabilities


@pytest.mark.req("REQ-YG-428")
class TestValidateCapabilitiesRetiredStatus:
    """validate_capabilities.py must accept status: retired files."""

    def test_ac03_retired_cap_passes_validation(self, tmp_path: Path) -> None:
        """A file with status: retired must pass validation even with relaxed fields."""
        cap_dir = tmp_path / "capabilities"
        cap_dir.mkdir()
        # Minimal retired CAP — no requirements, no modules list needed
        content = textwrap.dedent("""\
            id: CAP-90
            name: Retired Feature
            status: retired
            description: Was active, now retired.
            modules: []
            requirements: []
            fr: FR-90
        """)
        (cap_dir / "CAP-90-retired-feature.yaml").write_text(content)

        mod = _load_module(
            "validate_capabilities",
            REPO_ROOT / "scripts" / "validate_capabilities.py",
        )
        with mock.patch.object(mod, "CAPABILITIES_DIR", cap_dir):
            errors, _caps = mod.validate_registry()

        assert errors == [], f"Retired CAP should pass validation: {errors}"

    def test_ac04_tombstone_caps_still_blocked(self) -> None:
        """RETIRED_CAPS dict still blocks reuse of deleted CAP IDs (27, 29, 52, 58, 63)."""
        mod = _load_module(
            "validate_capabilities",
            REPO_ROOT / "scripts" / "validate_capabilities.py",
        )
        assert "CAP-27" in mod.RETIRED_CAPS
        assert "CAP-29" in mod.RETIRED_CAPS
        assert "CAP-63" in mod.RETIRED_CAPS


@pytest.mark.req("REQ-YG-428")
class TestCapabilityRegistryRetiredIdCheck:
    """test_capability_registry retired-ID test must use YAML status, not hardcoded set."""

    def test_ac05_no_hardcoded_retired_set_in_test(self) -> None:
        """test_capability_registry.py must not use a hardcoded retired ID set."""
        test_file = REPO_ROOT / "tests" / "unit" / "test_capability_registry.py"
        content = test_file.read_text()
        # The old pattern: retired = {"CAP-27", "CAP-29", ...}
        # After FR-466, this should be replaced by reading RETIRED_CAPS from the script
        assert 'retired = {"CAP-' not in content, (
            "test_capability_registry.py still uses hardcoded retired set — "
            "should read from validate_capabilities.RETIRED_CAPS"
        )
