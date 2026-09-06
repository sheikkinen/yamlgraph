"""FR-1014 — dir-aware ``graphs/`` arm of the graph-authoring sole route (REQ-YG-423).

One truth table, three enforcement surfaces that must agree on every row:

1. ``GOVERNED`` in ``scripts/check_authoring_proof.py`` (FR-767 commit backstop);
2. ``governed_path()`` inside ``.github/hooks/scripts/pre-command-guard.sh``
   (PreToolUse guard — the Python heredoc is extracted and executed here so
   the predicate is witnessed on every platform, not only where the bash hook
   can be exec'd; the Tier-2 witness in ``.github/hooks/tests`` drives the
   whole hook);
3. the ``authoring-proof`` hook's ``files:`` selector in
   ``.pre-commit-config.yaml`` (without it a commit whose only governed
   additions are dir-style never invokes surface 1 at all).

Provenance labels (FR-1014 R-2): "exists" rows are asserted against
``git ls-files``; "FR-1011" rows are named by that judged phase FR and do not
exist yet; the synthetic flat row exercises the retained flat arm and is not
evidence of the current tree.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
PROOF_SCRIPT = REPO / "scripts" / "check_authoring_proof.py"
GUARD_SCRIPT = REPO / ".github" / "hooks" / "scripts" / "pre-command-guard.sh"
PRE_COMMIT_CONFIG = REPO / ".pre-commit-config.yaml"

# process: the witness reads enforcement scripts under scripts/ and .github/ (FR-756)
pytestmark = [pytest.mark.req("REQ-YG-423"), pytest.mark.process]

# (path, provenance, governed)
TRUTH_TABLE = [
    ("graphs/enforcement/changelog-req-check.yaml", "exists", True),
    ("graphs/enforcement/prompts/cross_check.yaml", "exists", True),
    ("graphs/fr_triage/graph.yaml", "FR-1011", True),
    ("graphs/fr_triage/prompts/triage_fr.yaml", "FR-1011", True),
    ("graphs/fr1014-flat.yaml", "synthetic", True),
    ("graphs/README.md", "negative", False),
    ("graphs/fr_triage/tools.py", "negative", False),
    ("graphs/fr_triage/nested/graph.yaml", "negative", False),
    ("graphs/fr_triage/prompts/nested/triage.yaml", "negative", False),
]
ROW_IDS = [row[0] for row in TRUTH_TABLE]


def _load_proof_module():
    spec = importlib.util.spec_from_file_location("check_authoring_proof", PROOF_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_guard_governed_path():
    """Extract ``def governed_path`` from the guard's Python heredoc and exec it."""
    text = GUARD_SCRIPT.read_text(encoding="utf-8")
    match = re.search(r"^def governed_path\(path\):\n(?:    .*\n|\n(?=    ))*", text, re.M)
    assert match, "governed_path() not found in pre-command-guard.sh"
    namespace: dict = {"re": re}
    exec(match.group(0), namespace)  # noqa: S102 — CONF-461: executes the hook's own predicate source
    return namespace["governed_path"]


def _authoring_proof_selector() -> re.Pattern[str]:
    config = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
    for repo in config["repos"]:
        for hook in repo.get("hooks", []):
            if hook.get("id") == "authoring-proof":
                return re.compile(hook["files"])
    raise AssertionError("authoring-proof hook not found in .pre-commit-config.yaml")


def _proof_governed(path: str) -> bool:
    governed = _load_proof_module().GOVERNED
    return any(pattern.match(path) for pattern in governed)


@pytest.mark.parametrize(("path", "provenance", "expected"), TRUTH_TABLE, ids=ROW_IDS)
def test_proof_governed_matches_truth_table(path, provenance, expected):
    assert _proof_governed(path) is expected, f"GOVERNED disagrees on {path} ({provenance})"


@pytest.mark.parametrize(("path", "provenance", "expected"), TRUTH_TABLE, ids=ROW_IDS)
def test_guard_governed_path_matches_truth_table(path, provenance, expected):
    governed_path = _load_guard_governed_path()
    assert governed_path(path) is expected, f"governed_path() disagrees on {path} ({provenance})"


@pytest.mark.parametrize(("path", "provenance", "expected"), TRUTH_TABLE, ids=ROW_IDS)
def test_authoring_proof_selector_matches_truth_table(path, provenance, expected):
    """A dir-style-only commit must still invoke the backstop (FR-1011 R-1)."""
    selector = _authoring_proof_selector()
    assert bool(selector.search(path)) is expected, f"files: selector disagrees on {path}"


@pytest.mark.parametrize(("path", "provenance", "expected"), TRUTH_TABLE, ids=ROW_IDS)
def test_hook_and_proof_predicates_agree(path, provenance, expected):
    """AC-02: the two mirrored predicates agree row for row."""
    assert _load_guard_governed_path()(path) is _proof_governed(path)


@pytest.mark.parametrize(
    "path", [row[0] for row in TRUTH_TABLE if row[1] == "exists"]
)
def test_exists_rows_are_tracked(path):
    """AC-03: every row labelled 'exists' is in the tree; no synthetic row is."""
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_synthetic_and_fr1011_rows_are_absent():
    tracked = subprocess.run(
        ["git", "ls-files", "graphs"], cwd=REPO, capture_output=True, text=True
    ).stdout.split()
    for path, provenance, _ in TRUTH_TABLE:
        if provenance in {"synthetic", "FR-1011"}:
            assert path not in tracked, f"{path} labelled {provenance} but is tracked"
