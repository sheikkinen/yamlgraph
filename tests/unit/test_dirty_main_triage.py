"""REQ-YG-678: read-only provenance triage for a dirty main checkout (FR-1047).

Behavioral coverage for `scripts/dirty_main_triage.py` plus the safety
contract of `.github/skills/clean-dirty-main/SKILL.md`. Fixtures build real
git repositories so the classifier is exercised against actual plumbing, not
a mocked status string: the trap this FR exists to close was a misread of
real status output.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

TRIAGE = Path("scripts/dirty_main_triage.py").resolve()
SKILL = Path(".github/skills/clean-dirty-main/SKILL.md")
INSTRUCTIONS = Path(".github/copilot-instructions.md")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def run_triage(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TRIAGE), "--repo", str(repo)],
        check=False,
        capture_output=True,
        text=True,
    )


def counts(out: str) -> dict[str, int]:
    """Parse the `safe=n preserve=n unsupported=n errors=n` summary line."""
    for line in reversed(out.splitlines()):
        if line.startswith("safe="):
            return {k: int(v) for k, v in (part.split("=") for part in line.split())}
    raise AssertionError(f"no summary line in output:\n{out}")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A clone whose `origin/main` resolves, checked out on main.

    Two commits: the second adds `other.txt`. Rolling HEAD back one commit
    reproduces the partial-pull shape — HEAD behind origin/main, with
    origin's content sitting in the working tree.
    """
    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "t@example.com")
    git(seed, "config", "user.name", "t")
    (seed / "tracked.txt").write_text("original\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "seed")
    (seed / "other.txt").write_text("other\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "commit", "-qm", "add other")
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(seed), str(origin)],
        check=True,
        capture_output=True,
    )
    work = tmp_path / "work"
    subprocess.run(
        ["git", "clone", "-q", str(origin), str(work)],
        check=True,
        capture_output=True,
    )
    git(work, "config", "user.email", "t@example.com")
    git(work, "config", "user.name", "t")
    return work


# --- AC-01: clean tree ------------------------------------------------------


@pytest.mark.req("REQ-YG-678")
def test_clean_tree_exits_zero_with_all_counts_zero(repo: Path) -> None:
    result = run_triage(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert counts(result.stdout) == {
        "safe": 0,
        "preserve": 0,
        "unsupported": 0,
        "errors": 0,
    }


# --- AC-02 / AC-03: TARGET_IDENTICAL, the only safe class -------------------


@pytest.mark.req("REQ-YG-678")
def test_tracked_file_matching_origin_is_target_identical(repo: Path) -> None:
    """The partial-pull residue shape: ` M`, yet identical to origin/main."""
    (repo / "tracked.txt").write_text("local edit\n", encoding="utf-8")
    git(repo, "commit", "-qam", "local commit")
    (repo / "tracked.txt").write_text("original\n", encoding="utf-8")
    assert " M tracked.txt" in git(repo, "status", "--porcelain")
    result = run_triage(repo)
    assert "TARGET_IDENTICAL" in result.stdout
    c = counts(result.stdout)
    assert c == {"safe": 1, "preserve": 0, "unsupported": 0, "errors": 0}
    assert result.returncode == 0


@pytest.mark.req("REQ-YG-678")
def test_untracked_file_present_in_origin_is_target_identical(repo: Path) -> None:
    """The 2026-09-10 incident shape: untracked, yet already in origin/main."""
    blob = (repo / "other.txt").read_bytes()
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    (repo / "other.txt").write_bytes(blob)
    assert "?? other.txt" in git(repo, "status", "--porcelain")
    result = run_triage(repo)
    assert "TARGET_IDENTICAL" in result.stdout
    c = counts(result.stdout)
    assert c == {"safe": 1, "preserve": 0, "unsupported": 0, "errors": 0}
    assert result.returncode == 0


@pytest.mark.req("REQ-YG-678")
def test_all_safe_fixture_exits_zero(repo: Path) -> None:
    """Both shapes at once is still all-safe, the full residue snapshot."""
    blob = (repo / "other.txt").read_bytes()
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    (repo / "other.txt").write_bytes(blob)
    (repo / "tracked.txt").write_text("drifted\n", encoding="utf-8")
    git(repo, "commit", "-qam", "drift")
    (repo / "tracked.txt").write_text("original\n", encoding="utf-8")
    result = run_triage(repo)
    c = counts(result.stdout)
    assert c == {"safe": 2, "preserve": 0, "unsupported": 0, "errors": 0}
    assert result.returncode == 0


# --- AC-04 / AC-05: preserve classes ----------------------------------------


@pytest.mark.req("REQ-YG-678")
def test_bytes_from_another_commit_are_known_blob(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "sibling")
    (repo / "sibling.txt").write_text("sibling content\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "sibling work")
    sha = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "checkout", "-q", "main")
    (repo / "resurrected.txt").write_text("sibling content\n", encoding="utf-8")
    result = run_triage(repo)
    assert "KNOWN_BLOB" in result.stdout
    assert sha[:7] in result.stdout
    assert counts(result.stdout)["preserve"] == 1
    assert result.returncode != 0


@pytest.mark.req("REQ-YG-678")
def test_bytes_in_no_reachable_ref_are_unseen_blob(repo: Path) -> None:
    (repo / "novel.txt").write_text("only copy of real work\n", encoding="utf-8")
    result = run_triage(repo)
    assert "UNSEEN_BLOB" in result.stdout
    assert counts(result.stdout)["preserve"] == 1
    assert result.returncode != 0


# --- AC-06: pathological paths and binary content ---------------------------


@pytest.mark.req("REQ-YG-678")
@pytest.mark.parametrize(
    "name",
    ["with space.txt", "-leading-dash.txt", "ctrl\nnewline.txt", "b\tin.txt"],
)
def test_pathological_paths_are_classified_not_crashed(repo: Path, name: str) -> None:
    (repo / name).write_text("novel\n", encoding="utf-8")
    result = run_triage(repo)
    assert result.returncode != 0
    c = counts(result.stdout)
    assert c["preserve"] + c["unsupported"] == 1
    assert c["errors"] == 0


@pytest.mark.req("REQ-YG-678")
def test_binary_content_is_classified_without_decode_error(repo: Path) -> None:
    (repo / "blob.bin").write_bytes(bytes(range(256)) * 8)
    result = run_triage(repo)
    assert counts(result.stdout)["errors"] == 0
    assert "UNSEEN_BLOB" in result.stdout


# --- AC-07: fail closed on every unsupported state --------------------------


@pytest.mark.req("REQ-YG-678")
def test_non_main_branch_is_refused(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "feature")
    result = run_triage(repo)
    assert result.returncode != 0
    assert "REFUSED: not on main" in result.stdout + result.stderr


@pytest.mark.req("REQ-YG-678")
def test_missing_origin_main_is_refused(repo: Path) -> None:
    git(repo, "remote", "remove", "origin")
    result = run_triage(repo)
    assert result.returncode != 0
    assert "REFUSED: origin/main does not resolve" in result.stdout + result.stderr


@pytest.mark.req("REQ-YG-678")
def test_linked_worktree_is_refused(repo: Path, tmp_path: Path) -> None:
    linked = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "lane", str(linked))
    result = run_triage(linked)
    assert result.returncode != 0
    assert "REFUSED: linked worktree" in result.stdout + result.stderr


@pytest.mark.req("REQ-YG-678")
def test_staged_entry_is_unsupported(repo: Path) -> None:
    (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
    git(repo, "add", "staged.txt")
    result = run_triage(repo)
    assert "UNSUPPORTED" in result.stdout
    assert counts(result.stdout)["unsupported"] == 1
    assert counts(result.stdout)["safe"] == 0
    assert result.returncode != 0


@pytest.mark.req("REQ-YG-678")
def test_deletion_is_unsupported(repo: Path) -> None:
    (repo / "tracked.txt").unlink()
    result = run_triage(repo)
    assert counts(result.stdout)["unsupported"] == 1
    assert result.returncode != 0


@pytest.mark.req("REQ-YG-678")
def test_symlink_is_unsupported(repo: Path) -> None:
    (repo / "link.txt").symlink_to(repo / "tracked.txt")
    result = run_triage(repo)
    assert counts(result.stdout)["unsupported"] == 1
    assert counts(result.stdout)["safe"] == 0
    assert result.returncode != 0


# --- AC-08: a mixed snapshot is never partially cleaned ---------------------


@pytest.mark.req("REQ-YG-678")
def test_mixed_snapshot_exits_non_zero(repo: Path) -> None:
    """One safe path beside one preserve path must not license cleanup."""
    blob = (repo / "other.txt").read_bytes()
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    (repo / "other.txt").write_bytes(blob)
    (repo / "novel.txt").write_text("only copy\n", encoding="utf-8")
    result = run_triage(repo)
    c = counts(result.stdout)
    assert c["safe"] == 1
    assert c["preserve"] == 1
    assert result.returncode != 0


# --- AC-09: read-only, and the report pins the snapshot ---------------------


@pytest.mark.req("REQ-YG-678")
def test_classifier_mutates_nothing(repo: Path) -> None:
    (repo / "novel.txt").write_text("novel\n", encoding="utf-8")
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    index = repo / ".git" / "index"
    before = (
        git(repo, "rev-parse", "HEAD"),
        git(repo, "status", "--porcelain", "--untracked-files=all"),
        git(repo, "diff"),
        git(repo, "diff", "--cached"),
        sorted(p.name for p in repo.iterdir()),
        index.read_bytes(),
    )
    run_triage(repo)
    after = (
        git(repo, "rev-parse", "HEAD"),
        git(repo, "status", "--porcelain", "--untracked-files=all"),
        git(repo, "diff"),
        git(repo, "diff", "--cached"),
        sorted(p.name for p in repo.iterdir()),
        index.read_bytes(),
    )
    assert before == after
    # the run must actually have happened, not merely failed to start
    assert counts(run_triage(repo).stdout)["preserve"] == 2


@pytest.mark.req("REQ-YG-678")
def test_report_records_snapshot_identity(repo: Path) -> None:
    (repo / "novel.txt").write_text("novel\n", encoding="utf-8")
    head = git(repo, "rev-parse", "HEAD").strip()
    origin = git(repo, "rev-parse", "origin/main").strip()
    out = run_triage(repo).stdout
    assert head in out
    assert origin in out
    assert str(repo) in out


@pytest.mark.req("REQ-YG-678")
def test_report_escapes_paths_unambiguously(repo: Path) -> None:
    (repo / "ctrl\nnewline.txt").write_text("novel\n", encoding="utf-8")
    out = run_triage(repo).stdout
    assert "\\n" in out


# --- AC-10 / AC-11: the skill's safety contract -----------------------------


@pytest.mark.req("REQ-YG-678")
def test_skill_has_frontmatter_and_trigger() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    body = text.split("---\n", 2)
    assert "name:" in body[1]
    assert "description:" in body[1]
    assert "dirty main" in body[1]


@pytest.mark.req("REQ-YG-678")
def test_skill_runs_triage_before_any_mutation() -> None:
    text = SKILL.read_text(encoding="utf-8")
    triage_at = text.index("dirty_main_triage.py")
    for mutator in ("unlock-main", "git checkout --", "worktree.sh sync"):
        assert triage_at < text.index(mutator), mutator


@pytest.mark.req("REQ-YG-678")
def test_skill_stops_on_any_non_safe_result() -> None:
    text = SKILL.read_text(encoding="utf-8").lower()
    assert "non-zero" in text
    assert "stop" in text
    for token in ("preserve", "unsupported", "error"):
        assert token in text


@pytest.mark.req("REQ-YG-678")
def test_skill_forbids_repository_wide_discard() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "clean -fd" not in text
    assert "clean -f " not in text
    assert "checkout -- ." not in text
    assert "restore ." not in text


@pytest.mark.req("REQ-YG-678")
def test_skill_uses_explicit_pathspecs_and_restores_lock() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "-- <path>" in text
    assert "lock-main" in text


@pytest.mark.req("REQ-YG-678")
def test_skill_does_not_promise_to_transport_preserved_content() -> None:
    text = SKILL.read_text(encoding="utf-8").lower()
    assert "hand" in text and "operator" in text
    assert "move the path into a worktree" not in text


@pytest.mark.req("REQ-YG-678")
def test_skill_reruns_triage_before_cleanup() -> None:
    text = SKILL.read_text(encoding="utf-8").lower()
    assert "re-run" in text or "rerun" in text


# --- AC-12: the instruction route -------------------------------------------


@pytest.mark.req("REQ-YG-678")
def test_instructions_route_the_literal_phrase() -> None:
    text = INSTRUCTIONS.read_text(encoding="utf-8")
    assert "check dirty main" in text
    assert ".github/skills/clean-dirty-main" in text


# --- Review findings P1-P3 (PR #655): safety holes the first suite missed ----


@pytest.mark.req("REQ-YG-678")
def test_origin_symlink_target_is_never_safe(repo: Path) -> None:
    """P1: git stores a symlink's target as a blob, so bytes can match.

    A regular file whose contents equal the symlink target must not be
    licensed safe against a symlink in origin/main — the filesystem
    semantics differ even though the blobs are identical.
    """
    link = repo / "alink"
    link.symlink_to("tracked.txt")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "add symlink")
    git(repo, "push", "-q", "origin", "main")
    git(repo, "fetch", "-q", "origin")
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    (repo / "alink").write_text("tracked.txt", encoding="utf-8")
    result = run_triage(repo)
    assert "TARGET_IDENTICAL" not in result.stdout
    assert counts(result.stdout)["safe"] == 0
    assert result.returncode != 0


@pytest.mark.req("REQ-YG-678")
def test_malformed_status_record_is_never_untracked(repo: Path) -> None:
    """P2: a malformed record must not be promoted to an untracked file."""
    from importlib import util

    spec = util.spec_from_file_location("dmt", TRIAGE)
    assert spec and spec.loader
    module = util.module_from_spec(spec)
    sys.modules["dmt"] = module  # dataclasses resolve via sys.modules
    try:
        spec.loader.exec_module(module)
        entries = module.parse_status(b"X\0")
    finally:
        del sys.modules["dmt"]
    assert entries
    for code, _ in entries:
        assert code not in module.SUPPORTED_CODES


@pytest.mark.req("REQ-YG-678")
def test_known_blob_names_a_revision_that_contains_it(repo: Path) -> None:
    """P3: a deletion commit must not be reported as a blob's source."""
    git(repo, "checkout", "-q", "-b", "sibling")
    (repo / "transient.txt").write_text("transient content\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "add transient")
    added = git(repo, "rev-parse", "HEAD").strip()
    (repo / "transient.txt").unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "delete transient")
    removed = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "checkout", "-q", "main")
    (repo / "resurrected.txt").write_text("transient content\n", encoding="utf-8")
    out = run_triage(repo).stdout
    assert "KNOWN_BLOB" in out
    assert added[:7] in out, "must name the commit whose tree holds the blob"
    assert removed[:7] not in out, "must not name the deletion commit"
