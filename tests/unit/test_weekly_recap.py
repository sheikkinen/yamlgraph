"""FR-821 Weekly Recap Publication — unit tests (LLM-free).

Tests the render script's frozen contract: ISO-week naming, sectioned
markdown from fixtured graph state, and the deterministic
substantive-window no-op guard (recap-only automation commits excluded).
The graph run itself is fixtured — no LLM, no network.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import weekly_recap  # noqa: E402

pytestmark = pytest.mark.process

RECAP_FIXTURE = {
    "workstreams": [
        "FR-821 weekly recap automation [Status: Approved with revisions]",
        "FR-819 digest PoC follow-through [Status: Completed]",
    ],
    "orphans": ["9f3c2ab|2026-08-14|chore: tidy tmp"],
    "hotspots": ["CLAUDE.md touched by 2 workstreams"],
}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


@pytest.fixture()
def tmp_repo(tmp_path: Path) -> Path:
    """A throwaway git repo with one substantive and one recap-only commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "code.py").write_text("x = 1\n")
    _git(repo, "add", "code.py")
    _git(repo, "commit", "-q", "-m", "feat(x): FR-000 substantive change")
    recaps = repo / "docs" / "recaps"
    recaps.mkdir(parents=True)
    (recaps / "2026-W33.md").write_text("# Weekly Recap 2026-W33\n")
    _git(repo, "add", "docs/recaps/2026-W33.md")
    _git(repo, "commit", "-q", "-m", "docs(recap): weekly recap 2026-W33")
    return repo


class TestIsoWeek:
    @pytest.mark.req("REQ-YG-604")
    def test_iso_week_uses_iso_year(self) -> None:
        """%G-W%V: Jan 1 2027 belongs to ISO week 2026-W53."""
        assert weekly_recap.iso_week(date(2026, 8, 17)) == "2026-W34"
        assert weekly_recap.iso_week(date(2027, 1, 1)) == "2026-W53"


class TestRenderMarkdown:
    @pytest.mark.req("REQ-YG-604")
    def test_sections_present_and_non_empty(self) -> None:
        md = weekly_recap.render_markdown(RECAP_FIXTURE, "2026-W34")
        assert md.startswith("# Weekly Recap 2026-W34")
        for section in ("## Workstreams", "## Orphans", "## Hotspots"):
            assert section in md
        assert "FR-821 weekly recap automation" in md
        assert "9f3c2ab|2026-08-14|chore: tidy tmp" in md
        assert "CLAUDE.md touched by 2 workstreams" in md

    @pytest.mark.req("REQ-YG-604")
    def test_pydantic_model_normalized_at_boundary(self) -> None:
        """Graph state may carry a model, not a dict (REQ-YG-535 boundary)."""
        from pydantic import BaseModel

        class Recap(BaseModel):
            workstreams: list[str]
            orphans: list[str]
            hotspots: list[str]

        md = weekly_recap.render_markdown(Recap(**RECAP_FIXTURE), "2026-W34")
        assert "## Workstreams" in md
        assert "FR-819 digest PoC follow-through" in md

    @pytest.mark.req("REQ-YG-604")
    def test_empty_lists_render_explicit_none(self) -> None:
        """Empty sections say so — a blank section is indistinguishable
        from a render failure (substance_over_presence)."""
        md = weekly_recap.render_markdown(
            {"workstreams": [], "orphans": [], "hotspots": []}, "2026-W34"
        )
        assert md.count("(none)") == 3


class TestSubstantiveWindow:
    @pytest.mark.req("REQ-YG-604")
    def test_recap_only_commit_excluded(self, tmp_repo: Path) -> None:
        commits = weekly_recap.substantive_commits(str(tmp_repo), "1 hour ago")
        subjects = [c.split("|", 1)[1] for c in commits]
        assert subjects == ["feat(x): FR-000 substantive change"]

    @pytest.mark.req("REQ-YG-604")
    def test_empty_window_is_empty(self, tmp_repo: Path) -> None:
        # 2099 not 2999: git approxidate overflows past ~2100 and
        # silently includes everything (verified git 2.50.1).
        assert weekly_recap.substantive_commits(str(tmp_repo), "2099-01-01") == []

    @pytest.mark.req("REQ-YG-604")
    def test_recap_subject_with_code_changes_is_substantive(
        self, tmp_repo: Path
    ) -> None:
        """Subject match alone must not exclude — paths must also be
        recap-only (false_duplicate: syntactic similarity != equivalence)."""
        (tmp_repo / "other.py").write_text("y = 2\n")
        _git(tmp_repo, "add", "other.py")
        _git(tmp_repo, "commit", "-q", "-m", "docs(recap): weekly recap 2026-W99")
        commits = weekly_recap.substantive_commits(str(tmp_repo), "1 hour ago")
        subjects = [c.split("|", 1)[1] for c in commits]
        assert "docs(recap): weekly recap 2026-W99" in subjects


class TestGraphErrorBoundary:
    @pytest.mark.req("REQ-YG-604")
    def test_node_failure_raises_never_renders(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failed synthesize node leaves errors in state and a partial
        recap (orphans bypass the model, FR-704) — the script must raise,
        not publish a recap with silently empty workstreams."""
        monkeypatch.setattr(
            weekly_recap,
            "_invoke_graph",
            lambda *a, **k: {
                "errors": [{"node": "synthesize", "message": "timeout"}],
                "recap": {"workstreams": [], "orphans": ["x"], "hotspots": []},
            },
        )
        with pytest.raises(RuntimeError, match="synthesize"):
            weekly_recap.run_recap_graph(".", "1 week ago")


class TestMainNoOpAndDryRun:
    @pytest.mark.req("REQ-YG-604")
    def test_quiet_week_no_op_writes_nothing(
        self,
        tmp_repo: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        """Recap-only window: exit 0, no file, graph never invoked."""

        def _boom(*a, **k):  # pragma: no cover - must not be reached
            raise AssertionError("graph invoked on quiet week")

        monkeypatch.setattr(weekly_recap, "run_recap_graph", _boom)
        monkeypatch.setattr(weekly_recap, "substantive_commits", lambda *a, **k: [])
        out_dir = tmp_path / "out"
        rc = weekly_recap.main(
            ["--repo-path", str(tmp_repo), "--output-dir", str(out_dir)]
        )
        assert rc == 0
        assert not out_dir.exists() or not list(out_dir.iterdir())
        assert "no-op" in capsys.readouterr().out

    @pytest.mark.req("REQ-YG-604")
    def test_dry_run_prints_but_never_writes(
        self,
        tmp_repo: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        monkeypatch.setattr(
            weekly_recap, "run_recap_graph", lambda *a, **k: RECAP_FIXTURE
        )
        out_dir = tmp_path / "out"
        rc = weekly_recap.main(
            [
                "--repo-path",
                str(tmp_repo),
                "--output-dir",
                str(out_dir),
                "--dry-run",
            ]
        )
        assert rc == 0
        assert not out_dir.exists() or not list(out_dir.iterdir())
        assert "## Workstreams" in capsys.readouterr().out

    @pytest.mark.req("REQ-YG-604")
    def test_writes_iso_week_file(
        self,
        tmp_repo: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            weekly_recap, "run_recap_graph", lambda *a, **k: RECAP_FIXTURE
        )
        out_dir = tmp_path / "out"
        rc = weekly_recap.main(
            ["--repo-path", str(tmp_repo), "--output-dir", str(out_dir)]
        )
        assert rc == 0
        week = weekly_recap.iso_week(date.today())
        target = out_dir / f"{week}.md"
        assert target.exists()
        assert target.read_text().startswith(f"# Weekly Recap {week}")
