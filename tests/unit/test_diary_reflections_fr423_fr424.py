"""Tests for FR-428: Missing diary reflections for FR-423 and FR-424.

Validates that diary reflection files exist with genuine metacognitive content,
not placeholder stubs. Each reflection must identify a cognitive trap and
contain a forward-looking Seed question per the Sermon's Distill obligation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

DIARY_DIR = Path(__file__).resolve().parents[2] / "docs" / "diary"
KNOWN_TRAPS = [
    "batch_fatigue",
    "partial_remediation",
    "quick_confidence",
    "downstream_fix",
    "symptom_patch",
    "intent_drift",
    "false_duplicate",
    "audit_as_ritual",
    "plausible_wrong_answer",
    "framework_costume",
    "working_system_inertia",
]
PLACEHOLDER_MARKERS = ["[What cognitive trap", "[What lesson", "[What question"]


# ── FR-423 reflection ────────────────────────────────────────────────


FR423_PATH = DIARY_DIR / "2026-05-20-reflection-fr-423.md"


@pytest.mark.req("REQ-YG-144")
def test_fr423_reflection_exists():
    """AC: docs/diary/2026-05-20-reflection-fr-423.md exists."""
    assert FR423_PATH.is_file(), f"Missing reflection: {FR423_PATH}"


@pytest.mark.req("REQ-YG-144")
def test_fr423_reflection_not_stub():
    """AC: Genuine metacognitive content, not a placeholder stub."""
    content = FR423_PATH.read_text(encoding="utf-8")
    assert len(content.strip()) > 200, "Reflection is too short to be genuine"
    for marker in PLACEHOLDER_MARKERS:
        assert marker not in content, f"Placeholder text found: {marker}"


@pytest.mark.req("REQ-YG-144")
def test_fr423_reflection_has_cognitive_trap():
    """AC: Identifies at least one cognitive trap from the Knowledge Graph."""
    content = FR423_PATH.read_text(encoding="utf-8").lower()
    found = [trap for trap in KNOWN_TRAPS if trap in content]
    assert found, f"No known cognitive trap found. Expected one of: {KNOWN_TRAPS}"


@pytest.mark.req("REQ-YG-144")
def test_fr423_reflection_has_seed():
    """AC: Contains a forward-looking Seed question."""
    content = FR423_PATH.read_text(encoding="utf-8")
    assert "**Seed:**" in content, "Missing **Seed:** section"


@pytest.mark.req("REQ-YG-144")
def test_fr423_reflection_naming_convention():
    """AC: Follows YYYY-MM-DD-reflection-fr-NNN.md convention."""
    assert FR423_PATH.name == "2026-05-20-reflection-fr-423.md"


# ── FR-424 reflection ────────────────────────────────────────────────


FR424_PATH = DIARY_DIR / "2026-05-20-reflection-fr-424.md"


@pytest.mark.req("REQ-YG-144")
def test_fr424_reflection_exists():
    """AC: docs/diary/2026-05-20-reflection-fr-424.md exists."""
    assert FR424_PATH.is_file(), f"Missing reflection: {FR424_PATH}"


@pytest.mark.req("REQ-YG-144")
def test_fr424_reflection_not_stub():
    """AC: Genuine metacognitive content, not a placeholder stub."""
    content = FR424_PATH.read_text(encoding="utf-8")
    assert len(content.strip()) > 200, "Reflection is too short to be genuine"
    for marker in PLACEHOLDER_MARKERS:
        assert marker not in content, f"Placeholder text found: {marker}"


@pytest.mark.req("REQ-YG-144")
def test_fr424_reflection_has_cognitive_trap():
    """AC: Identifies at least one cognitive trap from the Knowledge Graph."""
    content = FR424_PATH.read_text(encoding="utf-8").lower()
    found = [trap for trap in KNOWN_TRAPS if trap in content]
    assert found, f"No known cognitive trap found. Expected one of: {KNOWN_TRAPS}"


@pytest.mark.req("REQ-YG-144")
def test_fr424_reflection_has_seed():
    """AC: Contains a forward-looking Seed question."""
    content = FR424_PATH.read_text(encoding="utf-8")
    assert "**Seed:**" in content, "Missing **Seed:** section"


@pytest.mark.req("REQ-YG-144")
def test_fr424_reflection_naming_convention():
    """AC: Follows YYYY-MM-DD-reflection-fr-NNN.md convention."""
    assert FR424_PATH.name == "2026-05-20-reflection-fr-424.md"
