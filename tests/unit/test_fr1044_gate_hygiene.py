"""FR-1044 pre-commit gate hygiene — ruff pin convergence and noqa line repair.

Two gate defects witnessed on PR #652: the formatter pinned at two different
versions, and a confession ledger keyed on exact line numbers that any inserted
line invalidates.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest
import yaml

# FR-756: this module loads scripts/noqa_coverage.py as a module.
pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
CONSTRAINTS = REPO_ROOT / "constraints" / "dev-py312.txt"
NOQA_SCRIPT = REPO_ROOT / "scripts" / "noqa_coverage.py"


def _load_noqa_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("noqa_coverage", NOQA_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pre_commit_repos() -> list[dict]:
    raw = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
    return raw.get("repos", [])


def _hook_ids_in_order() -> list[str]:
    return [
        hook.get("id") for repo in _pre_commit_repos() for hook in repo.get("hooks", [])
    ]


class TestRuffVersionConvergence:
    """AC-03: one ruff version, sourced from constraints/."""

    @pytest.mark.req("REQ-YG-676")
    def test_pre_commit_rev_equals_constraints_pin(self) -> None:
        """The hook and the developer environment must format identically."""
        pinned = re.search(
            r"^ruff==(\S+)", CONSTRAINTS.read_text(encoding="utf-8"), re.MULTILINE
        )
        assert pinned, f"no ruff== pin in {CONSTRAINTS}"

        revs = [
            repo["rev"]
            for repo in _pre_commit_repos()
            if "ruff-pre-commit" in repo.get("repo", "")
        ]
        assert len(revs) == 1, f"expected exactly one ruff-pre-commit repo, got {revs}"

        # constraints carry a bare version, pre-commit tags carry a leading v
        assert revs[0].lstrip("v") == pinned.group(1), (
            f"ruff skew: pre-commit rev {revs[0]!r} vs constraints "
            f"{pinned.group(1)!r} — they format the same code differently"
        )


class TestNoqaHookOrder:
    """AC-07: --fix runs before --strict, in the ruff/ruff-format shape."""

    @pytest.mark.req("REQ-YG-677")
    def test_fix_hook_precedes_strict_hook(self) -> None:
        ids = _hook_ids_in_order()
        assert "noqa-confession-fix" in ids, "no autofix hook registered"
        assert "noqa-confession" in ids
        assert ids.index("noqa-confession-fix") < ids.index("noqa-confession")

    @pytest.mark.req("REQ-YG-677")
    def test_fix_hook_does_not_stage(self) -> None:
        """C-5: the hook may modify the ledger, never stage it."""
        entries = [
            hook.get("entry", "")
            for repo in _pre_commit_repos()
            for hook in repo.get("hooks", [])
            if hook.get("id") == "noqa-confession-fix"
        ]
        assert entries and "--fix" in entries[0]
        assert "git add" not in entries[0]


# Assembled at runtime: scripts/noqa_coverage.py scans source text, so a
# literal marker in fixture data would be counted as a real suppression here.
_MARK = "# " + "noqa"


def _suppressed(statement: str, code: str) -> str:
    return f"{statement}  {_MARK}: {code}"


def _write_fixture(
    root: Path, source: str, ledger_entries: list[tuple[str, int, str]]
) -> Path:
    """Build a miniature repo: one scanned file plus a confession ledger."""
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "sample.py").write_text(source, encoding="utf-8")

    blocks = []
    for idx, (path, line, code) in enumerate(ledger_entries, start=1):
        blocks.append(
            f"### CONF-{idx:03d}\n"
            f"- **File**: [{path}](../{path}#L{line})\n"
            f"- **Code**: {code}\n"
            f"- **Sin**: fixture\n"
            f"- **Penance**: fixture\n"
        )
    confessions = root / "docs" / "confessions.md"
    confessions.parent.mkdir(parents=True, exist_ok=True)
    confessions.write_text("\n".join(blocks), encoding="utf-8")
    return confessions


class TestNoqaLineRepair:
    """AC-05/AC-06: repair unambiguous line drift, refuse everything else."""

    @pytest.mark.req("REQ-YG-677")
    def test_fix_realigns_shifted_line_refs(self, tmp_path: Path) -> None:
        """Inserting lines above a noqa must not require manual arithmetic."""
        mod = _load_noqa_module()
        source = "\n".join(["# padding"] * 8 + [_suppressed("x = 1", "E402"), ""])
        confessions = _write_fixture(tmp_path, source, [("tests/sample.py", 3, "E402")])

        assert mod.undocumented_noqa(
            tmp_path, confessions
        ), "fixture must start drifted"

        assert mod.fix_confession_lines(tmp_path, confessions) == 1
        assert "#L9" in confessions.read_text(encoding="utf-8")
        assert mod.undocumented_noqa(tmp_path, confessions) == []

    @pytest.mark.req("REQ-YG-677")
    def test_fix_refuses_when_a_noqa_was_added(self, tmp_path: Path) -> None:
        """Ambiguous shapes stay for --strict to report (R-4)."""
        mod = _load_noqa_module()
        source = "\n".join(
            [_suppressed("a = 1", "E402"), _suppressed("b = 2", "F401"), ""]
        )
        confessions = _write_fixture(tmp_path, source, [("tests/sample.py", 1, "E402")])
        before = confessions.read_text(encoding="utf-8")

        assert mod.fix_confession_lines(tmp_path, confessions) == 0
        assert confessions.read_text(encoding="utf-8") == before
        assert mod.undocumented_noqa(tmp_path, confessions) == [
            ("tests/sample.py", 2, "F401")
        ]

    @pytest.mark.req("REQ-YG-677")
    def test_fix_refuses_when_the_code_changed(self, tmp_path: Path) -> None:
        """Same count, different code — identity is not line number alone."""
        mod = _load_noqa_module()
        source = _suppressed("a = 1", "ARG001") + "\n"
        confessions = _write_fixture(tmp_path, source, [("tests/sample.py", 4, "E402")])
        before = confessions.read_text(encoding="utf-8")

        assert mod.fix_confession_lines(tmp_path, confessions) == 0
        assert confessions.read_text(encoding="utf-8") == before

    @pytest.mark.req("REQ-YG-677")
    def test_fix_is_idempotent_when_already_aligned(self, tmp_path: Path) -> None:
        mod = _load_noqa_module()
        source = _suppressed("a = 1", "E402") + "\n"
        confessions = _write_fixture(tmp_path, source, [("tests/sample.py", 1, "E402")])

        assert mod.fix_confession_lines(tmp_path, confessions) == 0
