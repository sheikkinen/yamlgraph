"""FR-700 Timeframe Recap Demo — Integration tests (real LLM).

Frozen acceptance criteria:
- Bare temp git repo (3 commits, no FR/changelog conventions) runs without
  error and yields no hallucinated FR references.
- A fixture commit without an FR/issue reference appears in `orphans`
  (tolerant matching — contains, never exact equality).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

GRAPH_PATH = "examples/demos/recap/graph.yaml"

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)

_GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "PATH": "/usr/bin:/bin",
}


def _make_bare_conventions_repo(path: Path) -> str:
    """Create a git repo with 3 commits and no yamlgraph conventions.

    Returns the short hash of the reference-less commit.
    """
    env = {**_GIT_ENV, "HOME": str(path)}
    subprocess.run(["git", "init", "-q", str(path)], check=True, env=env)

    def commit(msg: str, filename: str) -> str:
        (path / filename).write_text(f"content for {msg}\n")
        subprocess.run(["git", "-C", str(path), "add", "-A"], check=True, env=env)
        subprocess.run(
            ["git", "-C", str(path), "commit", "-q", "-m", msg], check=True, env=env
        )
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        ).stdout.strip()

    commit("#12 add parser", "parser.py")
    orphan_hash = commit("tweak output formatting", "formatter.py")
    commit("#13 add serializer", "serializer.py")
    return orphan_hash


@pytest.mark.slow
class TestRecapOnBareRepo:
    """Recap runs on a repo without yamlgraph conventions."""

    @pytest.mark.req("REQ-YG-531")
    def test_bare_repo_recap_no_hallucinated_conventions(self, tmp_path: Path) -> None:
        """No error; no invented FR references; orphan commit flagged."""
        from yamlgraph.graph_loader import load_and_compile

        orphan_hash = _make_bare_conventions_repo(tmp_path)

        graph = load_and_compile(GRAPH_PATH)
        app = graph.compile()
        result = app.invoke({"repo_path": str(tmp_path), "since": "1 day ago"})

        recap = result["recap"]
        recap_dict = recap if isinstance(recap, dict) else recap.model_dump()

        # No hallucinated FR references anywhere in the output.
        blob = str(recap_dict)
        assert not re.search(r"FR-\d+", blob), f"hallucinated FR refs: {blob[:500]}"

        # Orphan detection: tolerant matching — the reference-less commit's
        # hash appears somewhere in the orphans entries (contains, not equality).
        orphans_blob = " ".join(str(o) for o in recap_dict["orphans"])
        assert (
            orphan_hash in orphans_blob
        ), f"orphan {orphan_hash} not flagged; orphans: {orphans_blob}"


@pytest.mark.slow
class TestRecapDispositionAxis:
    """FR-702: verbatim FR status surfaces in workstream lines."""

    @pytest.mark.req("REQ-YG-534")
    def test_rejected_status_surfaces_verbatim(self, tmp_path: Path) -> None:
        """FR with **Status:** Rejected appears in its workstream (tolerant)."""
        from yamlgraph.graph_loader import load_and_compile

        env = {**_GIT_ENV, "HOME": str(tmp_path)}
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, env=env)
        frdir = tmp_path / "feature-requests"
        frdir.mkdir()
        (frdir / "FR-042-widget.md").write_text(
            "# FR-042 Widget\n\n**Status:** Rejected\n\nNot worth building.\n"
        )
        (tmp_path / "widget.py").write_text("# widget stub\n")
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True, env=env)
        subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "commit",
                "-q",
                "-m",
                "feat: FR-042 widget spike",
            ],
            check=True,
            env=env,
        )

        graph = load_and_compile(GRAPH_PATH)
        app = graph.compile()
        result = app.invoke({"repo_path": str(tmp_path), "since": "1 day ago"})

        recap = result["recap"]
        recap_dict = recap if isinstance(recap, dict) else recap.model_dump()
        workstreams_blob = " ".join(str(w) for w in recap_dict["workstreams"])
        assert "FR-042" in workstreams_blob
        assert (
            "Rejected" in workstreams_blob
        ), f"verbatim status missing: {workstreams_blob}"
