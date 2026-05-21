#!/usr/bin/env python3
"""FR-443 acceptance tests for Copilot hooks documentation in instructions."""

from __future__ import annotations

from pathlib import Path

import pytest

INSTRUCTIONS = Path(__file__).resolve().parents[2] / "copilot-instructions.md"
SECTION_HEADER = "### Copilot Hooks (.github/hooks/)"


def _lines() -> list[str]:
    return INSTRUCTIONS.read_text().splitlines()


def _find_index(lines: list[str], value: str) -> int:
    try:
        return lines.index(value)
    except ValueError as exc:
        raise AssertionError(f"missing line: {value}") from exc


def _subsection_body(lines: list[str], section_index: int) -> list[str]:
    for idx in range(section_index + 1, len(lines)):
        if lines[idx].startswith("### "):
            return lines[section_index + 1 : idx]
    return lines[section_index + 1 :]


@pytest.mark.req("REQ-YG-063")
def test_ac01_hooks_subsection_exists_under_conventions():
    lines = _lines()
    conventions_idx = _find_index(lines, "### Conventions")
    hooks_idx = _find_index(lines, SECTION_HEADER)
    assert hooks_idx > conventions_idx


@pytest.mark.req("REQ-YG-063")
def test_ac02_hooks_subsection_contains_required_operational_tokens():
    lines = _lines()
    hooks_idx = _find_index(lines, SECTION_HEADER)
    body = "\n".join(_subsection_body(lines, hooks_idx))

    required_tokens = [
        "pre-command-guard.sh",
        "python-checks.sh",
        "yaml-checks.sh",
        "markdown-checks.sh",
        "fr-checks.sh",
        "reasoning-pattern-check.sh",
        ".github/hooks/cmd lockdown",
        "audit.jsonl",
        ".github/hooks/README.md",
    ]
    for token in required_tokens:
        assert token in body


@pytest.mark.req("REQ-YG-063")
def test_ac03_hooks_subsection_is_concise():
    lines = _lines()
    hooks_idx = _find_index(lines, SECTION_HEADER)
    body = _subsection_body(lines, hooks_idx)
    non_empty_lines = [line for line in body if line.strip()]
    assert len(non_empty_lines) <= 15
