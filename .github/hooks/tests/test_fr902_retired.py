#!/usr/bin/env python3
"""FR-927: the FR-902 lane-guard hook machinery is gone, never to return.

Structural absence pin. Deliberately imports nothing from the hooks test
package so it cannot fail for a missing fixture — every failure here means
a retired surface came back.

Run:  pytest .github/hooks/tests/test_fr902_retired.py -q --no-cov
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.req("REQ-YG-629")

HOOKS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = HOOKS_ROOT.parents[1]
SCRIPTS_DIR = HOOKS_ROOT / "scripts"
TESTS_DIR = HOOKS_ROOT / "tests"
GUARD = SCRIPTS_DIR / "pre-command-guard.sh"
PROBE = HOOKS_ROOT / "session-probe.json"

RETIRED_SCRIPTS = (
    SCRIPTS_DIR / "checks" / "lane_guard.py",
    SCRIPTS_DIR / "session-worktree.sh",
    SCRIPTS_DIR / "session-checkpoint.sh",
)
RETIRED_BASENAMES = tuple(p.name for p in RETIRED_SCRIPTS)

RETIRED_TEST_FILES = (
    TESTS_DIR / "fr902_fixtures.py",
    TESTS_DIR / "test_fr902_lane_guard.py",
    TESTS_DIR / "test_fr902_session_worktree.py",
    TESTS_DIR / "test_fr902_checkpoint.py",
    TESTS_DIR / "test_fr902_gc_join.py",
)

# The only write-shape alternation FR-889 kept: the lock-mutator fence.
FR889_FENCE = r"\bchmod\b|\bchflags\b|\bsetfacl\b"

# Word-boundary regex atoms that existed only inside the Check 8 enum.
FR902_WRITE_VERB_ATOMS = (
    r"\btee\b",
    r"\bcp\b",
    r"\bmv\b",
    r"\brsync\b",
    r"\binstall\b",
    r"\bsed\b",
    r"\bdd\b",
    r"\btruncate\b",
    r"\btouch\b",
    r"\bmkdir\b",
    r"\brm\b",
    r"\bln\b",
)

GUIDANCE_DOCS = (
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / ".github" / "copilot-instructions.md",
)


def hook_script_texts() -> dict[Path, str]:
    return {
        p: p.read_text(errors="ignore")
        for p in sorted(SCRIPTS_DIR.rglob("*"))
        if p.is_file() and p.suffix in {".sh", ".py", ".json"}
    }


def probe_commands() -> list[str]:
    probe = json.loads(PROBE.read_text())
    return [
        entry.get("command", "")
        for entries in probe["hooks"].values()
        for entry in entries
    ]


def test_retired_hook_scripts_absent() -> None:
    present = [str(p.relative_to(REPO_ROOT)) for p in RETIRED_SCRIPTS if p.exists()]
    assert not present, f"FR-902 hook scripts resurrected: {present}"


def test_session_probe_has_no_retired_registrations() -> None:
    offenders = [
        cmd
        for cmd in probe_commands()
        if any(name in cmd for name in RETIRED_BASENAMES)
    ]
    assert not offenders, f"session-probe.json registers retired scripts: {offenders}"


def test_pre_command_guard_has_no_fr902_token() -> None:
    text = GUARD.read_text().lower()
    assert "fr902" not in text, "pre-command-guard.sh still carries an FR902 token"
    assert "fr-902" not in text, "pre-command-guard.sh still references FR-902"


def test_pre_command_guard_has_no_write_shape_alternation() -> None:
    # Only the shell grep grammar is in scope; FR-767's Check 6 analyzer is
    # a Python heredoc and was never part of the Check 8 enum.
    alternations = re.findall(r"grep -qE '([^']*)'", GUARD.read_text())
    offenders = [
        pattern
        for pattern in alternations
        if pattern != FR889_FENCE
        and any(atom in pattern for atom in FR902_WRITE_VERB_ATOMS)
    ]
    assert (
        not offenders
    ), f"write-shape grammar back in pre-command-guard.sh: {offenders}"


def test_fr889_lock_mutator_fence_intact() -> None:
    # C-4: the subtraction must not take FR-889's narrow fence with it.
    assert f"grep -qE '{FR889_FENCE}'" in GUARD.read_text()


def test_no_allow_outside_escape_anywhere() -> None:
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path, text in hook_script_texts().items()
        if "FR902_ALLOW_OUTSIDE" in text
    ]
    offenders += [
        str(doc.relative_to(REPO_ROOT))
        for doc in GUIDANCE_DOCS
        if doc.exists() and "FR902_ALLOW_OUTSIDE" in doc.read_text()
    ]
    assert not offenders, f"FR902_ALLOW_OUTSIDE escape still live in: {offenders}"


def test_no_live_flag_gate_in_hook_scripts() -> None:
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path, text in hook_script_texts().items()
        if "fr902.live" in text
    ]
    assert not offenders, f"fr902.live gating still present in: {offenders}"


def test_retired_hook_tests_and_fixtures_absent() -> None:
    present = [str(p.relative_to(REPO_ROOT)) for p in RETIRED_TEST_FILES if p.exists()]
    assert not present, f"FR-902 hook tests resurrected: {present}"
