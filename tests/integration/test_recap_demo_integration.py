"""FR-700 Timeframe Recap Demo — Integration tests (real LLM).

FR-930 retired the live bare-repo anti-hallucination witness: the no-invented-
FR-refs clause is enforced by construction in finalize_recap (reconciliation
against the deterministic reference universe) and witnessed by unit tests in
tests/unit/test_recap_demo.py::TestReferenceReconciliation. Live end-to-end
coverage of the graph remains below (REQ-YG-534).
"""

from __future__ import annotations

import os
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


@pytest.mark.slow
class TestRecapDispositionAxis:
    """FR-702: verbatim FR status surfaces in workstream lines."""

    @pytest.mark.req("REQ-YG-534")
    def test_rejected_status_surfaces_verbatim(self, tmp_path: Path) -> None:
        """FR with **Status:** Rejected appears in its workstream (tolerant)."""
        from yamlgraph.compile.graph_loader import load_and_compile

        env = {**_GIT_ENV, "HOME": str(tmp_path)}
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, env=env)
        frdir = tmp_path / "feature-requests"
        frdir.mkdir()
        (frdir / "FR-042-widget.md").write_text(
            "# FR-042 Widget\n\n**Status:** Rejected\n\nNot worth building.\n",
            encoding="utf-8",
        )
        (tmp_path / "widget.py").write_text("# widget stub\n", encoding="utf-8")
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
        assert "Rejected" in workstreams_blob, (
            f"verbatim status missing: {workstreams_blob}"
        )


@pytest.mark.slow
class TestRecapPullRequestAxisOnOriginlessRepo:
    """FR-1027 AC-14: the axis reports its own absence, and costs no network.

    The bare fixture repository has no `origin`, so `collect_prs` ends at the
    identify step — no `gh` invocation, no second slow path (FR-922 budget).
    The recap around it must still be complete.
    """

    @pytest.mark.req("REQ-YG-669")
    def test_absent_origin_note_and_complete_recap(self, tmp_path: Path) -> None:
        from yamlgraph.compile.graph_loader import load_and_compile

        env = {**_GIT_ENV, "HOME": str(tmp_path)}
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, env=env)
        (tmp_path / "widget.py").write_text("# widget stub\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True, env=env)
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-q", "-m", "feat: FR-043 widget"],
            check=True,
            env=env,
        )
        assert (
            subprocess.run(
                ["git", "-C", str(tmp_path), "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                env=env,
            ).returncode
            != 0
        ), "fixture must have no origin"

        graph = load_and_compile(GRAPH_PATH)
        result = graph.compile().invoke(
            {"repo_path": str(tmp_path), "since": "1 day ago"}
        )

        axis = result["pr_axis"]
        assert axis["available"] is False
        assert axis["reason"] == "no origin remote"
        assert (axis["merged"], axis["closed_unmerged"], axis["open"]) == ([], [], [])

        recap = result["recap"]
        recap_dict = recap if isinstance(recap, dict) else recap.model_dump()
        assert recap_dict["workstreams"], "recap must still be complete"
        assert (
            recap_dict["pr_axis_note"]
            == "pull-request axis unavailable: no origin remote"
        )
