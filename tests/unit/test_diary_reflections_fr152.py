"""Tests for FR-152: Missing diary reflections for FR-137 and FR-145.

Validates that diary reflection files exist with genuine metacognitive content,
not placeholder stubs. Each reflection must identify a cognitive trap and
contain a forward-looking Seed question per the Sermon's Distill obligation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

DIARY_DIR = Path(__file__).resolve().parents[2] / "docs" / "diary"

# ── FR-137 reflection ────────────────────────────────────────────────


FR137_PATH = DIARY_DIR / "2026-03-08-reflection-fr-137.md"


@pytest.mark.req("REQ-YG-144")
def test_fr137_reflection_exists():
    """AC: docs/diary/2026-03-08-reflection-fr-137.md exists."""
    assert FR137_PATH.is_file(), f"Missing reflection: {FR137_PATH}"


@pytest.mark.req("REQ-YG-144")
def test_fr137_reflection_not_stub():
    """AC: Genuine metacognitive content, not a placeholder stub."""
    content = FR137_PATH.read_text(encoding="utf-8")
    assert len(content.strip()) > 200, "Reflection is too short to be genuine"
    placeholder_markers = ["[What cognitive trap", "[What lesson", "[What question"]
    for marker in placeholder_markers:
        assert marker not in content, f"Placeholder text found: {marker}"


@pytest.mark.req("REQ-YG-144")
def test_fr137_reflection_has_cognitive_trap():
    """AC: Identifies at least one cognitive trap from the Knowledge Graph."""
    content = FR137_PATH.read_text(encoding="utf-8").lower()
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
def test_fr137_reflection_has_seed():
    """AC: Contains a forward-looking Seed question."""
    content = FR137_PATH.read_text(encoding="utf-8")
    assert "**Seed:**" in content, "Missing **Seed:** section"


@pytest.mark.req("REQ-YG-144")
def test_fr137_reflection_naming_convention():
    """AC: Follows YYYY-MM-DD-reflection-fr-NNN.md convention."""
    assert FR137_PATH.name == "2026-03-08-reflection-fr-137.md"


# ── FR-145 reflection ────────────────────────────────────────────────


FR145_PATH = DIARY_DIR / "2026-03-08-reflection-fr-145.md"


@pytest.mark.req("REQ-YG-144")
def test_fr145_reflection_exists():
    """AC: docs/diary/2026-03-08-reflection-fr-145.md exists."""
    assert FR145_PATH.is_file(), f"Missing reflection: {FR145_PATH}"


@pytest.mark.req("REQ-YG-144")
def test_fr145_reflection_not_stub():
    """AC: Genuine metacognitive content, not a placeholder stub."""
    content = FR145_PATH.read_text(encoding="utf-8")
    assert len(content.strip()) > 200, "Reflection is too short to be genuine"
    placeholder_markers = ["[What cognitive trap", "[What lesson", "[What question"]
    for marker in placeholder_markers:
        assert marker not in content, f"Placeholder text found: {marker}"


@pytest.mark.req("REQ-YG-144")
def test_fr145_reflection_has_cognitive_trap():
    """AC: Identifies at least one cognitive trap from the Knowledge Graph."""
    content = FR145_PATH.read_text(encoding="utf-8").lower()
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
def test_fr145_reflection_has_seed():
    """AC: Contains a forward-looking Seed question."""
    content = FR145_PATH.read_text(encoding="utf-8")
    assert "**Seed:**" in content, "Missing **Seed:** section"


@pytest.mark.req("REQ-YG-144")
def test_fr145_reflection_naming_convention():
    """AC: Follows YYYY-MM-DD-reflection-fr-NNN.md convention."""
    assert FR145_PATH.name == "2026-03-08-reflection-fr-145.md"
