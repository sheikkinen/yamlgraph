"""FR-1011 — the live parts leave `.chaplain/` (Phase 1 of FR-1010).

Assertion-level witnesses (FR-1011 R-3): every test collects on the
pre-relocation tree and fails by a direct `assert` naming the missing
implementation — never by import error, FileNotFoundError, or a missing
fixture. Existence is asserted before any file is read or loaded.

Requirements witnessed (existing REQs, no new CAP — FR-1011 RED):
REQ-YG-563 (CAP-206 fr_triage), REQ-YG-564 (CAP-205 world_distill),
REQ-YG-529 (CAP-75 philosopher diary proxy), REQ-YG-125 (CAP-38 finalizer).
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# process: the witness reads hook scripts, skills and scripts/ (FR-756)
pytestmark = [
    pytest.mark.req("REQ-YG-563", "REQ-YG-564", "REQ-YG-529", "REQ-YG-125"),
    pytest.mark.process,
]

DESTINATIONS = [
    "graphs/fr_triage/graph.yaml",
    "graphs/world_distill/graph.yaml",
    "graphs/philosopher/graph.yaml",
    "graphs/philosopher/diary.py",
    "scripts/lib/finalize_lib.sh",
]
SOURCES = [
    ".chaplain/graphs/fr_triage/graph.yaml",
    ".chaplain/graphs/world_distill/graph.yaml",
    ".chaplain/graphs/philosopher/graph.yaml",
    ".chaplain/lib/diary.py",
    ".chaplain/lib/finalize_lib.sh",
]

# Frozen live-consumer list (FR-1011 § Acceptance Criteria, third bullet).
LIVE_CONSUMERS = [
    ".github/hooks/scripts/checks/triage_gate.py",
    ".github/hooks/scripts/checks/fr-checks.sh",
    ".github/hooks/scripts/pre-command-guard.sh",
    "scripts/check_authoring_proof.py",
    ".pre-commit-config.yaml",
    "scripts/vscode/now.py",
    "scripts/finalize_merge.sh",
    ".github/skills/feature-request/SKILL.md",
    ".github/skills/graph-authoring/doctrine.md",
    ".github/skills/session-introspection/SKILL.md",
    "capabilities/CAP-75-portable-chaplain.yaml",
    "capabilities/CAP-114-automated-post-merge-finalization.yaml",
    "capabilities/CAP-205-world-distill.yaml",
    "capabilities/CAP-206-fr-triage-graph.yaml",
    ".gitignore",
]
RELOCATED_TREES = ["graphs/fr_triage", "graphs/world_distill", "graphs/philosopher", "scripts/lib"]
# Path form and Path-segment form (triage_gate.py builds ".chaplain" / "graphs" / ...).
OLD_LITERALS = re.compile(
    r"\.chaplain/graphs/(fr_triage|world_distill|philosopher)"
    r"|\.chaplain/lib/(finalize_lib\.sh|diary\.py)"
    r"|\.chaplain/inbox/"
    r"|[\"']\.chaplain[\"']"
)

GUARD_SURFACES = [
    ".github/hooks/scripts/pre-command-guard.sh",
    "scripts/check_authoring_proof.py",
    ".pre-commit-config.yaml",
]


def _read(rel: str) -> str:
    p = REPO / rel
    assert p.is_file(), f"expected file missing: {rel}"
    return p.read_text(encoding="utf-8")


@pytest.mark.parametrize("rel", DESTINATIONS)
def test_destinations_exist(rel):
    assert (REPO / rel).is_file(), f"FR-1011 destination not present: {rel}"


@pytest.mark.parametrize("rel", SOURCES)
def test_sources_gone(rel):
    assert not (REPO / rel).exists(), f"FR-1011 source still present: {rel}"


@pytest.mark.parametrize("rel", LIVE_CONSUMERS)
def test_live_consumers_name_new_paths(rel):
    hits = [
        f"{rel}:{n}: {line.strip()}"
        for n, line in enumerate(_read(rel).splitlines(), 1)
        if OLD_LITERALS.search(line)
    ]
    assert not hits, "live consumer still names an old .chaplain path:\n" + "\n".join(hits)


def test_relocated_trees_name_no_old_paths():
    hits = []
    for tree in RELOCATED_TREES:
        root = REPO / tree
        assert root.is_dir(), f"relocated tree missing: {tree}"
        for p in root.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                    if OLD_LITERALS.search(line):
                        hits.append(f"{p.relative_to(REPO)}:{n}: {line.strip()}")
    assert not hits, "relocated package still names an old .chaplain path:\n" + "\n".join(hits)


def test_philosopher_diary_proxy_is_sibling():
    tools_rel = "graphs/philosopher/tools.py"
    diary_rel = "graphs/philosopher/diary.py"
    assert (REPO / tools_rel).is_file(), f"missing {tools_rel}"
    assert (REPO / diary_rel).is_file(), f"missing {diary_rel}"
    src = _read(tools_rel)
    assert 'with_name("diary.py")' in src, "write_diary proxy must load the sibling diary.py"
    assert 'parents[2] / "lib"' not in src, "old parents[2]/lib proxy path still present"
    spec = importlib.util.spec_from_file_location("fr1011_diary", REPO / diary_rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(getattr(mod, "write_diary", None)), "diary.py must expose write_diary"


def test_finalizer_sources_relocated_lib():
    src = _read("scripts/finalize_merge.sh")
    assert "scripts/lib/finalize_lib.sh" in src, "finalize_merge.sh must source scripts/lib/finalize_lib.sh"
    assert ".chaplain/lib" not in src, "finalize_merge.sh still sources .chaplain/lib"


def test_proposals_route_documented():
    skill = _read(".github/skills/feature-request/SKILL.md")
    assert "mkdir -p proposals" in skill, "feature-request skill must give the executable proposals/ command"
    assert ".chaplain/inbox" not in skill, "feature-request skill still names .chaplain/inbox"
    ignore = _read(".gitignore").splitlines()
    assert "/proposals/" in ignore, ".gitignore must ignore the root-anchored /proposals/"
    assert ".chaplain/inbox/" not in ignore, ".gitignore still lists .chaplain/inbox/"


@pytest.mark.parametrize("rel", GUARD_SURFACES)
def test_governed_surfaces_have_no_chaplain_arm(rel):
    text = _read(rel)
    assert not re.search(r"\\\.chaplain|\.chaplain", text), f"{rel} still carries a .chaplain arm or routing text"


def test_examples_philosopher_stub_removed():
    assert not (REPO / "examples" / "philosopher").exists(), "examples/philosopher/ stub must be deleted"
