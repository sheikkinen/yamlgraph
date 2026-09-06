"""Acceptance tests for FR-436 ADR-001 traceability scope contract."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.process

ARCHITECTURE_PATH = Path("ARCHITECTURE.md")
ADR001_PATH = Path("docs/adr/001-test-requirement-traceability.md")
REQ_COVERAGE_PATH = Path("scripts/req_coverage.py")
HOOKS_README_PATH = Path(".github/hooks/README.md")


def _read_lower(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


@pytest.mark.req("REQ-YG-063")
def test_ac01_architecture_adr001_defines_traceability_tiers() -> None:
    architecture = _read_lower(ARCHITECTURE_PATH)

    assert "tier 1" in architecture
    assert "tier 2" in architecture
    assert "tier 3" in architecture
    assert "tests/unit" in architecture
    assert "tests/integration" in architecture
    assert ".github/hooks/tests" in architecture


@pytest.mark.req("REQ-YG-063")
def test_ac02_reqyg063_wording_is_framework_scope_not_global() -> None:
    lines = ARCHITECTURE_PATH.read_text(encoding="utf-8").splitlines()
    req_line = next(line for line in lines if line.strip().startswith("| REQ-YG-063 |"))
    req_line_lower = req_line.lower()

    assert "tests/unit" in req_line_lower
    assert "tests/integration" in req_line_lower
    assert ".github/hooks/tests" in req_line_lower
    assert "all tests must have" not in req_line_lower


@pytest.mark.req("REQ-YG-063")
def test_ac03_adr001_doc_mirrors_tier_contract() -> None:
    adr = _read_lower(ADR001_PATH)

    assert "tier 1" in adr
    assert "tier 2" in adr
    assert "tier 3" in adr
    assert "tests/unit" in adr
    assert "tests/integration" in adr
    assert ".github/hooks/tests" in adr
    assert "infrastructure hook" in adr


@pytest.mark.req("REQ-YG-063")
def test_ac04_req_coverage_explicitly_scopes_and_excludes_hook_tests() -> None:
    req_coverage = REQ_COVERAGE_PATH.read_text(encoding="utf-8")
    req_coverage_lower = req_coverage.lower()

    assert "FRAMEWORK_TEST_DIRS" in req_coverage
    assert "EXCLUDED_TEST_DIRS" in req_coverage
    assert "tests/unit" in req_coverage
    assert "tests/integration" in req_coverage
    assert ".github/hooks/tests" in req_coverage
    assert "scope" in req_coverage_lower and "infrastructure" in req_coverage_lower


@pytest.mark.req("REQ-YG-063")
def test_ac06_hooks_readme_documents_infrastructure_scope_policy() -> None:
    hooks_readme = _read_lower(HOOKS_README_PATH)

    assert ".github/hooks/tests/" in hooks_readme
    assert "infrastructure test" in hooks_readme
    assert "outside req-yg marker coverage" in hooks_readme
    assert "tests/unit/" in hooks_readme
    assert "tests/integration/" in hooks_readme
