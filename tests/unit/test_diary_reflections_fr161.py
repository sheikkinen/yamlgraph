"""Tests for FR-161: Missing diary reflections for FR-150 and FR-154.

Validates that diary reflection files exist with genuine metacognitive content,
not placeholder stubs. Each reflection must identify a cognitive trap and
contain a forward-looking Seed question per the Sermon's Distill obligation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

DIARY_DIR = Path(__file__).resolve().parents[2] / "docs" / "diary"

# ── FR-150 reflection ────────────────────────────────────────────────


FR150_PATH = DIARY_DIR / "2026-03-08-reflection-fr-150.md"


@pytest.mark.req("REQ-YG-144")
def test_fr150_reflection_exists():
    """AC: docs/diary/2026-03-08-reflection-fr-150.md exists."""
    assert FR150_PATH.is_file(), f"Missing reflection: {FR150_PATH}"


@pytest.mark.req("REQ-YG-144")
def test_fr150_reflection_not_stub():
    """AC: Genuine metacognitive content, not a placeholder stub."""
    content = FR150_PATH.read_text(encoding="utf-8")
    assert len(content.strip()) > 200, "Reflection is too short to be genuine"
    placeholder_markers = ["[What cognitive trap", "[What lesson", "[What question"]
    for marker in placeholder_markers:
        assert marker not in content, f"Placeholder text found: {marker}"


@pytest.mark.req("REQ-YG-144")
def test_fr150_reflection_has_cognitive_trap():
    """AC: Identifies at least one cognitive trap from the Knowledge Graph."""
    content = FR150_PATH.read_text(encoding="utf-8").lower()
    known_traps = [
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
    found = [t for t in known_traps if t in content]
    assert found, f"No known cognitive trap found. Expected one of: {known_traps}"


@pytest.mark.req("REQ-YG-144")
def test_fr150_reflection_has_seed():
    """AC: Contains a forward-looking Seed question."""
    content = FR150_PATH.read_text(encoding="utf-8")
    assert "**Seed:**" in content, "Missing **Seed:** section"


@pytest.mark.req("REQ-YG-144")
def test_fr150_reflection_naming_convention():
    """AC: Follows YYYY-MM-DD-reflection-fr-NNN.md convention."""
    assert FR150_PATH.name == "2026-03-08-reflection-fr-150.md"


# ── FR-154 reflection ────────────────────────────────────────────────


FR154_PATH = DIARY_DIR / "2026-03-08-reflection-fr-154.md"


@pytest.mark.req("REQ-YG-144")
def test_fr154_reflection_exists():
    """AC: docs/diary/2026-03-08-reflection-fr-154.md exists."""
    assert FR154_PATH.is_file(), f"Missing reflection: {FR154_PATH}"


@pytest.mark.req("REQ-YG-144")
def test_fr154_reflection_not_stub():
    """AC: Genuine metacognitive content, not a placeholder stub."""
    content = FR154_PATH.read_text(encoding="utf-8")
    assert len(content.strip()) > 200, "Reflection is too short to be genuine"
    placeholder_markers = ["[What cognitive trap", "[What lesson", "[What question"]
    for marker in placeholder_markers:
        assert marker not in content, f"Placeholder text found: {marker}"


@pytest.mark.req("REQ-YG-144")
def test_fr154_reflection_has_cognitive_trap():
    """AC: Identifies at least one cognitive trap from the Knowledge Graph."""
    content = FR154_PATH.read_text(encoding="utf-8").lower()
    known_traps = [
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
    found = [t for t in known_traps if t in content]
    assert found, f"No known cognitive trap found. Expected one of: {known_traps}"


@pytest.mark.req("REQ-YG-144")
def test_fr154_reflection_has_seed():
    """AC: Contains a forward-looking Seed question."""
    content = FR154_PATH.read_text(encoding="utf-8")
    assert "**Seed:**" in content, "Missing **Seed:** section"


@pytest.mark.req("REQ-YG-144")
def test_fr154_reflection_naming_convention():
    """AC: Follows YYYY-MM-DD-reflection-fr-NNN.md convention."""
    assert FR154_PATH.name == "2026-03-08-reflection-fr-154.md"
