"""FR-702 Recap Disposition Axis — Unit tests (LLM-free).

R1: fr_statuses tool node — verbatim FR Status lines at HEAD, anchored grep,
exit-1-normalized boundary (no-convention repos succeed empty; non-git fails
loudly). R2: deterministic commit-reference partition pre-pass — mid-subject
refs (d2d2934-class) can never be flagged as orphans.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

GRAPH_PATH = "examples/demos/recap/graph.yaml"
DEMO_DIR = (
    Path(__file__).resolve().parent.parent.parent / "examples" / "demos" / "recap"
)

_GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
    "PATH": "/usr/bin:/bin",
}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        env={**_GIT_ENV, "HOME": str(repo)},
    )


def _init_repo(repo: Path) -> None:
    subprocess.run(
        ["git", "init", "-q", str(repo)],
        check=True,
        env={**_GIT_ENV, "HOME": str(repo)},
    )


class TestGraphStructureFr702:
    """Graph gains fr_statuses tool + partition pre-pass; contract holds."""

    @pytest.mark.req("REQ-YG-534")
    def test_fr_statuses_tool_declared(self) -> None:
        """fr_statuses: anchored pattern, per-file cap, exit-1 normalization."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        cmd = raw["tools"]["fr_statuses"]["command"]
        assert "git -C {repo_path} grep" in cmd
        assert "^\\*\\*Status" in cmd, f"pattern not anchored: {cmd}"
        assert "-m 1" in cmd
        assert "|| [ $? -eq 1 ]" in cmd, f"missing exit-1 normalization: {cmd}"

    @pytest.mark.req("REQ-YG-534")
    def test_partition_node_declared(self) -> None:
        """partition is a type: python pre-pass between commits and synthesis."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        node = raw["nodes"]["partition"]
        assert node["type"] == "python"
        tool = raw["tools"][node["tool"]]
        assert tool["type"] == "python"
        assert tool["function"] == "partition_commits"

    @pytest.mark.req("REQ-YG-534")
    def test_still_exactly_one_llm_node(self) -> None:
        """The pre-pass adds no judgement — synthesize remains the only LLM node."""
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        llm_nodes = [
            n for n, c in raw["nodes"].items() if c.get("type", "llm") == "llm"
        ]
        assert llm_nodes == ["synthesize"]

    @pytest.mark.req("REQ-YG-534")
    def test_prompt_consumes_partition_and_statuses(self) -> None:
        """Prompt uses unreferenced + fr_statuses; verbatim-status rule stated."""
        text = (DEMO_DIR / "prompts" / "recap.yaml").read_text()
        assert "unreferenced" in text
        assert "fr_statuses" in text
        assert "[no FR status]" in text

    @pytest.mark.req("REQ-YG-534")
    def test_graph_lint_stays_clean(self) -> None:
        """W026 stays clean: 3 schema fields, zero lint issues."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(GRAPH_PATH)
        assert result.issues == [], f"Lint issues: {result.issues}"


class TestFrStatusesBoundary:
    """Exit-code normalization at the tool boundary (F3)."""

    def _node_fn(self):
        from yamlgraph.tools.nodes import create_tool_node
        from yamlgraph.tools.shell import parse_tools

        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text())
        tools = parse_tools(raw["tools"])
        return create_tool_node(
            "get_fr_statuses", raw["nodes"]["get_fr_statuses"], tools
        )

    @pytest.mark.req("REQ-YG-534")
    def test_bare_repo_succeeds_empty(self, tmp_path: Path) -> None:
        """Repo without feature-requests/: git grep exit 1 → success, empty."""
        _init_repo(tmp_path)
        _git(tmp_path, "commit", "--allow-empty", "-q", "-m", "init")
        result = self._node_fn()({"repo_path": str(tmp_path), "since": "1 day ago"})
        assert result["fr_statuses"].strip() == ""

    @pytest.mark.req("REQ-YG-534")
    def test_non_git_fails_loudly(self, tmp_path: Path) -> None:
        """Non-git repo_path: git grep exit >=2 is NOT normalized — raises."""
        with pytest.raises(RuntimeError, match="get_fr_statuses"):
            self._node_fn()({"repo_path": str(tmp_path), "since": "1 day ago"})

    @pytest.mark.req("REQ-YG-534")
    def test_anchored_pattern_skips_prose(self, tmp_path: Path) -> None:
        """FR file with 'Status' in prose contributes only the anchored line (F2)."""
        _init_repo(tmp_path)
        frdir = tmp_path / "feature-requests"
        frdir.mkdir()
        (frdir / "FR-001-thing.md").write_text(
            "# FR-001\n\n**Status:** Rejected\n\n"
            "The Status of this work depends on Status checks in prose.\n"
        )
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "commit", "-q", "-m", "FR-001 add fr")
        out = self._node_fn()({"repo_path": str(tmp_path), "since": "1 day ago"})
        lines = [ln for ln in out["fr_statuses"].splitlines() if ln.strip()]
        assert len(lines) == 1, f"expected 1 anchored line, got: {lines}"
        assert "Rejected" in lines[0]


class TestPartitionPrePass:
    """R2: reference detection is arithmetic, not judgement."""

    @pytest.mark.req("REQ-YG-534")
    def test_mid_subject_ref_is_referenced(self) -> None:
        """d2d2934-class: ref after a colon mid-subject must not be orphanable."""
        from examples.demos.recap.nodes.partition import partition_commits

        commits = "d2d2934|2026-07-08|docs: ecosystem refresh + NC-340 persona FR"
        result = partition_commits({"commits": commits})
        assert "d2d2934" in result["referenced"]
        assert result["unreferenced"].strip() == ""

    @pytest.mark.req("REQ-YG-534")
    def test_reference_variants(self) -> None:
        """FR-, NC-, and #N refs all count; plain subjects do not."""
        from examples.demos.recap.nodes.partition import partition_commits

        commits = "\n".join(
            [
                "a1|2026-07-01|feat: FR-700 recap",
                "b2|2026-07-02|fix(x): NC-345 misroute",
                "c3|2026-07-03|#12 add parser",
                "d4|2026-07-04|chore: backlog",
            ]
        )
        result = partition_commits({"commits": commits})
        for h in ("a1", "b2", "c3"):
            assert h in result["referenced"]
        assert "d4" in result["unreferenced"]
        assert "d4" not in result["referenced"]

    @pytest.mark.req("REQ-YG-534")
    def test_lowercase_scoped_ref_is_referenced(self) -> None:
        """a9a8bdec-class: lowercase 'fr-691' in commit scope must count.

        Found by raw-output read of the first GREEN demo run: conventional
        commit scopes lowercase the ref (docs(fr-691): ...) and the frozen
        case-sensitive pattern shipped it to orphans.
        """
        from examples.demos.recap.nodes.partition import partition_commits

        commits = "a9a8bdec|2026-07-07|docs(fr-691): mark Enforced, record verdict"
        result = partition_commits({"commits": commits})
        assert "a9a8bdec" in result["referenced"]
        assert result["unreferenced"].strip() == ""

    @pytest.mark.req("REQ-YG-534")
    def test_empty_input(self) -> None:
        """Empty commit list partitions to two empty strings, no error."""
        from examples.demos.recap.nodes.partition import partition_commits

        result = partition_commits({"commits": ""})
        assert result["referenced"] == ""
        assert result["unreferenced"] == ""
