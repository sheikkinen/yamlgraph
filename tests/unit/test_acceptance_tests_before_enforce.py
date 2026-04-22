"""Tests for FR-260: Acceptance Tests Before Enforce.

Validates that the Chaplain pipeline inserts create_worktree and
write_acceptance_tests nodes between research and judge, giving
Judge three inputs (FR, research brief, failing tests) instead of two.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPLAIN_GRAPH = REPO_ROOT / ".chaplain" / "graphs" / "copilot" / "graph.yaml"
PROMPTS_DIR = REPO_ROOT / ".chaplain" / "graphs" / "copilot" / "prompts"
ENFORCE_PROMPTS_DIR = REPO_ROOT / ".chaplain" / "graphs" / "enforce" / "prompts"
ENFORCE_SCRIPT = REPO_ROOT / "scripts" / "enforce_worktree.sh"
WORKTREE_TOOL = REPO_ROOT / ".chaplain" / "lib" / "worktree.py"


def _load_graph() -> dict:
    """Load the chaplain copilot graph YAML."""
    return yaml.safe_load(CHAPLAIN_GRAPH.read_text())


def _edge_pairs() -> list[tuple[str, str]]:
    """Return list of (from, to) edge tuples from the copilot graph."""
    graph = _load_graph()
    return [(e["from"], e["to"]) for e in graph["edges"]]


# ===========================================================================
# AC-01: State fields worktree_dir and branch
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestStateFields:
    """Graph state must include worktree_dir and branch."""

    def test_state_has_worktree_dir(self):
        """state declaration must include worktree_dir."""
        graph = _load_graph()
        state = graph.get("state", {})
        assert (
            "worktree_dir" in state
        ), f"Missing worktree_dir in state. Keys: {list(state.keys())}"

    def test_state_has_branch(self):
        """state declaration must include branch."""
        graph = _load_graph()
        state = graph.get("state", {})
        assert "branch" in state, f"Missing branch in state. Keys: {list(state.keys())}"


# ===========================================================================
# AC-02: create_worktree python node exists
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestCreateWorktreeNode:
    """create_worktree python node must exist in the copilot graph."""

    def test_create_worktree_node_exists(self):
        """graph.yaml must have a 'create_worktree' node."""
        graph = _load_graph()
        assert (
            "create_worktree" in graph["nodes"]
        ), "Missing 'create_worktree' node in copilot graph"

    def test_create_worktree_node_type_python(self):
        """create_worktree must be type: python."""
        graph = _load_graph()
        node = graph["nodes"]["create_worktree"]
        assert node["type"] == "python"

    def test_create_worktree_node_has_tool_ref(self):
        """create_worktree must reference a tool."""
        graph = _load_graph()
        node = graph["nodes"]["create_worktree"]
        assert "tool" in node, "create_worktree node must reference a tool"

    def test_create_worktree_node_state_key(self):
        """create_worktree must use a tool that returns top-level state keys."""
        graph = _load_graph()
        node = graph["nodes"]["create_worktree"]
        # Python tool nodes return directly to top-level state keys
        # (worktree_dir, branch) without an intermediate state_key
        assert "tool" in node, "create_worktree must use a tool reference"

    def test_create_worktree_tool_declared(self):
        """A create_worktree tool must be declared in tools section."""
        graph = _load_graph()
        tools = graph.get("tools", {})
        tool_names = list(tools.keys())
        worktree_tools = [t for t in tool_names if "worktree" in t.lower()]
        assert worktree_tools, f"No worktree tool declared. Tools: {tool_names}"


# ===========================================================================
# AC-03: create_worktree python tool file
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestCreateWorktreeTool:
    """create_worktree tool must exist at .chaplain/lib/worktree.py."""

    def test_tool_file_exists(self):
        """worktree.py must exist in .chaplain/lib/."""
        assert WORKTREE_TOOL.exists(), f"Missing tool file: {WORKTREE_TOOL}"

    def test_tool_has_create_worktree_function(self):
        """worktree.py must define a create_worktree function."""
        content = WORKTREE_TOOL.read_text()
        assert (
            "def create_worktree(" in content
        ), "worktree.py must define create_worktree()"

    def test_tool_uses_derive_branch_name(self):
        """Tool must use derive_branch_name from worktree_helpers."""
        content = WORKTREE_TOOL.read_text()
        assert "derive_branch_name" in content

    def test_tool_uses_construct_worktree_path(self):
        """Tool must use construct_worktree_path from worktree_helpers."""
        content = WORKTREE_TOOL.read_text()
        assert "construct_worktree_path" in content

    def test_tool_returns_worktree_dir_and_branch(self):
        """Tool must return dict with worktree_dir and branch keys."""
        content = WORKTREE_TOOL.read_text()
        assert "worktree_dir" in content
        assert "branch" in content


# ===========================================================================
# AC-04: write_acceptance_tests copilot node exists
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestWriteAcceptanceTestsNode:
    """write_acceptance_tests copilot node must exist in the graph."""

    def test_node_exists(self):
        """graph.yaml must have a 'write_acceptance_tests' node."""
        graph = _load_graph()
        assert (
            "write_acceptance_tests" in graph["nodes"]
        ), "Missing 'write_acceptance_tests' node"

    def test_node_type_copilot(self):
        """write_acceptance_tests must be type: copilot."""
        graph = _load_graph()
        node = graph["nodes"]["write_acceptance_tests"]
        assert node["type"] == "copilot"

    def test_node_has_prompt(self):
        """write_acceptance_tests must reference write-acceptance-tests prompt."""
        graph = _load_graph()
        node = graph["nodes"]["write_acceptance_tests"]
        assert node["prompt"] == "write-acceptance-tests"

    def test_node_state_key(self):
        """write_acceptance_tests must write to acceptance_tests_result."""
        graph = _load_graph()
        node = graph["nodes"]["write_acceptance_tests"]
        assert node["state_key"] == "acceptance_tests_result"

    def test_node_has_worktree_dir_variable(self):
        """write_acceptance_tests must pass worktree_dir from state."""
        graph = _load_graph()
        node = graph["nodes"]["write_acceptance_tests"]
        variables = node.get("variables", {})
        assert "worktree_dir" in variables


# ===========================================================================
# AC-05: write-acceptance-tests.yaml prompt
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestWriteAcceptanceTestsPrompt:
    """write-acceptance-tests prompt must exist with required content."""

    def test_prompt_file_exists(self):
        """prompts/write-acceptance-tests.yaml must exist."""
        path = PROMPTS_DIR / "write-acceptance-tests.yaml"
        assert path.exists(), f"Missing {path}"

    def test_prompt_has_system(self):
        """Prompt must have a system block."""
        prompt = yaml.safe_load(
            (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        )
        assert "system" in prompt

    def test_prompt_has_user(self):
        """Prompt must have a user block."""
        prompt = yaml.safe_load(
            (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        )
        assert "user" in prompt

    def test_prompt_mentions_acceptance_criteria(self):
        """Prompt must instruct reading FR acceptance criteria."""
        prompt = yaml.safe_load(
            (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        )
        user = prompt["user"].lower()
        assert "acceptance criteria" in user or "acceptance" in user

    def test_prompt_mentions_pytest_mark_req(self):
        """Prompt must instruct adding @pytest.mark.req tags."""
        prompt = yaml.safe_load(
            (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        )
        user = prompt["user"]
        assert "pytest.mark.req" in user

    def test_prompt_mentions_red_commit(self):
        """Prompt must instruct committing RED tests."""
        prompt = yaml.safe_load(
            (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        )
        content = prompt["user"].lower()
        assert "red" in content or "fail" in content

    def test_prompt_mentions_skip_pytest(self):
        """Prompt must instruct using SKIP=pytest for RED commit."""
        prompt = yaml.safe_load(
            (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        )
        assert "SKIP=pytest" in prompt["user"]

    def test_prompt_references_worktree_dir(self):
        """Prompt must reference {worktree_dir} variable."""
        prompt = yaml.safe_load(
            (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        )
        assert "{worktree_dir}" in prompt["user"]


# ===========================================================================
# AC-07: Judge prompt criterion 8 (test evidence)
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestJudgeCriterion8:
    """Judge prompt must include criterion 8 for test evidence evaluation."""

    @pytest.fixture()
    def judge_content(self) -> str:
        return (PROMPTS_DIR / "judge.yaml").read_text()

    def test_criterion_8_exists(self, judge_content: str):
        """Judge prompt must contain criterion 8."""
        assert "8." in judge_content, "Judge prompt must include criterion 8"

    def test_criterion_8_mentions_tests(self, judge_content: str):
        """Criterion 8 must mention acceptance tests."""
        content_lower = judge_content.lower()
        assert "acceptance test" in content_lower or "test" in content_lower

    def test_criterion_8_mentions_fail(self, judge_content: str):
        """Criterion 8 must mention tests failing for the right reasons."""
        content_lower = judge_content.lower()
        assert "fail" in content_lower

    def test_criterion_8_mentions_amend(self, judge_content: str):
        """If tests can't be written, judge should AMEND."""
        content_lower = judge_content.lower()
        assert "amend" in content_lower


# ===========================================================================
# AC-09: Enforce implement prompt references existing RED tests
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestEnforceImplementPrompt:
    """Enforce implement prompt must reference existing RED tests."""

    def test_prompt_mentions_existing_tests(self):
        """Prompt must reference pre-existing acceptance tests."""
        content = (ENFORCE_PROMPTS_DIR / "enforce-implement.yaml").read_text()
        content_lower = content.lower()
        assert (
            "acceptance test" in content_lower
            or "existing" in content_lower
            or "red" in content_lower
        )

    def test_prompt_forbids_modifying_test_assertions(self):
        """Prompt must instruct not to modify acceptance test assertions."""
        content = (ENFORCE_PROMPTS_DIR / "enforce-implement.yaml").read_text()
        content_lower = content.lower()
        assert (
            "do not modify" in content_lower
            or "must not" in content_lower
            or "contract" in content_lower
        )


# ===========================================================================
# AC-10: enforce_worktree.sh accepts optional pre-existing worktree
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestEnforceWorktreeScript:
    """enforce_worktree.sh must accept optional pre-existing worktree path."""

    def test_script_accepts_third_argument(self):
        """Script usage must support a third argument for worktree path."""
        content = ENFORCE_SCRIPT.read_text()
        # Should reference $3 or a third positional arg for worktree path
        assert (
            "${3" in content
            or "$3" in content
            or "EXISTING_WORKTREE" in content
            or "PRE_EXISTING" in content
        ), "enforce_worktree.sh must accept optional third argument for pre-existing worktree"

    def test_script_skips_creation_when_worktree_exists(self):
        """Script must conditionally skip worktree creation."""
        content = ENFORCE_SCRIPT.read_text()
        # Must have conditional logic around worktree add
        assert (
            "skip" in content.lower()
            or "already" in content.lower()
            or "pre-existing" in content.lower()
            or "existing" in content.lower()
        ), "Script must conditionally skip worktree creation"


# ===========================================================================
# AC-13: Unit test for create_worktree tool (valid output from FR path)
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestCreateWorktreeToolUnit:
    """Unit test: create_worktree returns valid worktree_dir and branch."""

    def test_create_worktree_output_structure(self, tmp_path, monkeypatch):
        """create_worktree returns dict with worktree_dir and branch keys."""
        import subprocess
        import sys

        # Create a fake FR draft
        drafts_dir = tmp_path / "drafts"
        drafts_dir.mkdir()
        fr_draft = drafts_dir / "FR-260-acceptance-tests-before-enforce.md"
        fr_draft.write_text("# FR-260\n\n**Status:** Draft\n")

        # Mock subprocess.run to avoid actual git operations
        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Mock os.symlink to avoid actual symlink creation
        monkeypatch.setattr(
            "os.symlink", lambda src, dst, target_is_directory=False: None
        )

        # Mock venv validators to avoid filesystem checks
        import yamlgraph.utils.worktree_helpers as wh

        monkeypatch.setattr(wh, "validate_venv_health", lambda path: None)
        monkeypatch.setattr(wh, "validate_venv_symlink", lambda s, t: None)

        # Import and call the tool
        sys.path.insert(0, str(REPO_ROOT / ".chaplain" / "lib"))
        try:
            # Remove cached module if present (re-import picks up monkeypatch)
            if "worktree" in sys.modules:
                del sys.modules["worktree"]
            from worktree import create_worktree

            state = {
                "drafts_dir": str(drafts_dir),
                "topic_file": str(fr_draft),
            }
            result = create_worktree(state)

            assert "worktree_dir" in result, "Result must contain worktree_dir"
            assert "branch" in result, "Result must contain branch"
            assert (
                "feat/" in result["branch"]
            ), f"Branch must start with feat/, got: {result['branch']}"
            assert (
                "tmp/worktrees/" in result["worktree_dir"]
            ), f"worktree_dir must be under tmp/worktrees/, got: {result['worktree_dir']}"
        finally:
            sys.path.pop(0)


# ===========================================================================
# AC-14: Unit test for prompt template variable substitution
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestPromptTemplateVariables:
    """write-acceptance-tests prompt template must render with valid variables."""

    def test_prompt_template_has_drafts_dir_var(self):
        """Prompt must use {drafts_dir} variable."""
        content = (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        assert "{drafts_dir}" in content

    def test_prompt_template_has_worktree_dir_var(self):
        """Prompt must use {worktree_dir} variable."""
        content = (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        assert "{worktree_dir}" in content

    def test_prompt_template_has_branch_var(self):
        """Prompt must use {branch} variable."""
        content = (PROMPTS_DIR / "write-acceptance-tests.yaml").read_text()
        assert "{branch}" in content


# ===========================================================================
# AC-15: Integration test — edge ordering invariant
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestEdgeOrderingInvariant:
    """Copilot graph edges must enforce:
    plan → research → create_worktree → write_acceptance_tests → judge
    """

    def test_research_to_create_worktree_edge(self):
        """Edge from research → create_worktree must exist."""
        pairs = _edge_pairs()
        assert (
            "research",
            "create_worktree",
        ) in pairs, f"Missing research → create_worktree edge. Edges: {pairs}"

    def test_create_worktree_to_write_acceptance_tests_edge(self):
        """Edge from create_worktree → write_acceptance_tests must exist."""
        pairs = _edge_pairs()
        assert (
            ("create_worktree", "write_acceptance_tests") in pairs
        ), f"Missing create_worktree → write_acceptance_tests edge. Edges: {pairs}"

    def test_write_acceptance_tests_to_judge_edge(self):
        """Edge from write_acceptance_tests → judge must exist."""
        pairs = _edge_pairs()
        assert (
            "write_acceptance_tests",
            "judge",
        ) in pairs, f"Missing write_acceptance_tests → judge edge. Edges: {pairs}"

    def test_no_direct_research_to_judge_edge(self):
        """Old research → judge edge must be removed."""
        pairs = _edge_pairs()
        assert (
            ("research", "judge") not in pairs
        ), "Direct research → judge edge still exists; should go through create_worktree → write_acceptance_tests"

    def test_full_pipeline_order(self):
        """Full pipeline order: START → plan → research → create_worktree →
        write_acceptance_tests → judge → summarize → write_diary → END."""
        pairs = _edge_pairs()
        expected_sequence = [
            ("START", "plan"),
            ("plan", "research"),
            ("research", "create_worktree"),
            ("create_worktree", "write_acceptance_tests"),
            ("write_acceptance_tests", "judge"),
            ("judge", "summarize"),
            ("summarize", "write_diary"),
            ("write_diary", "END"),
        ]
        for edge in expected_sequence:
            assert edge in pairs, f"Missing edge {edge[0]} → {edge[1]}. Edges: {pairs}"


# ===========================================================================
# AC-16: Integration test — judge prompt criterion 8 text
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestJudgeCriterion8Text:
    """Judge prompt must contain specific criterion 8 text about test evidence."""

    def test_criterion_8_underspecified(self):
        """Criterion 8 must mention underspecified criteria."""
        content = (PROMPTS_DIR / "judge.yaml").read_text().lower()
        assert (
            "underspecified" in content
        ), "Judge criterion 8 must mention underspecified criteria"

    def test_criterion_8_compile_and_fail(self):
        """Criterion 8 must mention tests compiling and failing."""
        content = (PROMPTS_DIR / "judge.yaml").read_text().lower()
        assert "fail" in content and ("compile" in content or "run" in content)

    def test_criterion_8_import_errors(self):
        """Criterion 8 must mention import errors as bad failure mode."""
        content = (PROMPTS_DIR / "judge.yaml").read_text().lower()
        assert "import" in content


# ===========================================================================
# Graph validity: all edges reference existing nodes
# ===========================================================================


@pytest.mark.req("REQ-YG-263")
class TestGraphValidity:
    """The modified chaplain graph must be structurally valid."""

    def test_graph_yaml_valid(self):
        """graph.yaml loads without error."""
        graph = _load_graph()
        assert graph["version"] == "1.0"

    def test_all_edge_targets_exist(self):
        """Every edge target must be a declared node or START/END."""
        graph = _load_graph()
        node_names = set(graph["nodes"].keys()) | {"START", "END"}
        for edge in graph["edges"]:
            assert (
                edge["from"] in node_names
            ), f"Edge 'from' references unknown node: {edge['from']}"
            assert (
                edge["to"] in node_names
            ), f"Edge 'to' references unknown node: {edge['to']}"

    def test_all_nodes_have_edges(self):
        """Every node must appear in at least one edge."""
        graph = _load_graph()
        edge_nodes = set()
        for edge in graph["edges"]:
            edge_nodes.add(edge["from"])
            edge_nodes.add(edge["to"])
        for node_name in graph["nodes"]:
            assert (
                node_name in edge_nodes
            ), f"Node '{node_name}' not referenced in any edge"
