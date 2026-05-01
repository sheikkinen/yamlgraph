"""FR-292: Pipeline Config Path Alignment.

RED acceptance tests for:
- All yamlgraph_async graph paths resolve to existing files
- `splitting` state removed; `split` routes to `failed`
- `committing_tests` state removed; `test_demo_done` routes to `critiquing`
- `changelog_gen` uses `bash` type, not `yamlgraph_async`
- Pipeline reduced from 27 to 25 states
"""

from pathlib import Path

import pytest
import yaml

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_PATH = CHAPLAIN / "config" / "watcher-pipeline.yaml"


def load_config(path: Path) -> dict:
    """Load and return YAML config."""
    assert path.exists(), f"Config not found: {path}"
    with open(path) as f:
        return yaml.safe_load(f)


def get_transitions(config: dict) -> list[dict]:
    """Extract all transitions from config."""
    return config.get("transitions", [])


def get_action_blocks(config: dict) -> dict:
    """Extract all action blocks from config."""
    return config.get("actions", {})


# ════════════════════════════════════════════════════════════════════════
# AC-01: All yamlgraph_async graph paths resolve to existing files
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestGraphPathsResolve:
    """Every yamlgraph_async action must reference a graph file that exists on disk."""

    def test_all_graph_refs_exist_on_disk(self):
        """AC-01: Each graph: path in yamlgraph_async actions resolves to an existing file."""
        config = load_config(PIPELINE_PATH)
        actions = get_action_blocks(config)
        missing = []
        for state_name, action_list in actions.items():
            if not isinstance(action_list, list):
                continue
            for action in action_list:
                if action.get("type") != "yamlgraph_async":
                    continue
                graph_path = action.get("graph", "")
                full_path = WORKTREE / graph_path
                if not full_path.exists():
                    missing.append(f"{state_name}: {graph_path}")
        assert not missing, "Graph files not found:\n" + "\n".join(missing)

    def test_graph_paths_use_chaplain_prefix(self):
        """All yamlgraph_async graph paths must start with .chaplain/graphs/."""
        config = load_config(PIPELINE_PATH)
        actions = get_action_blocks(config)
        wrong_prefix = []
        for state_name, action_list in actions.items():
            if not isinstance(action_list, list):
                continue
            for action in action_list:
                if action.get("type") != "yamlgraph_async":
                    continue
                graph_path = action.get("graph", "")
                if not graph_path.startswith(".chaplain/graphs/"):
                    wrong_prefix.append(f"{state_name}: {graph_path}")
        assert not wrong_prefix, (
            "Graph paths missing .chaplain/graphs/ prefix:\n" + "\n".join(wrong_prefix)
        )

    def test_exactly_nine_yamlgraph_async_actions(self):
        """After removals, exactly 9 yamlgraph_async actions remain."""
        config = load_config(PIPELINE_PATH)
        actions = get_action_blocks(config)
        count = 0
        for action_list in actions.values():
            if not isinstance(action_list, list):
                continue
            for action in action_list:
                if action.get("type") == "yamlgraph_async":
                    count += 1
        assert count == 9, f"Expected 9 yamlgraph_async actions, got {count}"


# ════════════════════════════════════════════════════════════════════════
# AC-02: `splitting` state removed
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestSplittingRemoved:
    """splitting state must not exist; split event routes to failed."""

    def test_splitting_not_in_states(self):
        """AC-02: splitting is not in the states list."""
        config = load_config(PIPELINE_PATH)
        states = config.get("states", [])
        assert "splitting" not in states, "splitting state should be removed"

    def test_split_routes_to_failed(self):
        """AC-02: split event from judging goes directly to failed."""
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        split_transitions = [t for t in transitions if t.get("event") == "split"]
        assert (
            len(split_transitions) == 1
        ), f"Expected exactly 1 split transition, got {len(split_transitions)}"
        assert split_transitions[0]["from"] == "judging"
        assert split_transitions[0]["to"] == "failed"

    def test_no_split_done_event(self):
        """AC-02: split_done event should not exist."""
        config = load_config(PIPELINE_PATH)
        events = config.get("events", {})
        # events can be a dict or list depending on format
        if isinstance(events, dict | list):
            assert "split_done" not in events

    def test_no_splitting_action_block(self):
        """AC-02: No action block for splitting state."""
        config = load_config(PIPELINE_PATH)
        actions = get_action_blocks(config)
        assert "splitting" not in actions, "splitting action block should be removed"


# ════════════════════════════════════════════════════════════════════════
# AC-03: `committing_tests` state removed
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestCommittingTestsRemoved:
    """committing_tests state must not exist; testing_demo routes to critiquing."""

    def test_committing_tests_not_in_states(self):
        """AC-03: committing_tests is not in the states list."""
        config = load_config(PIPELINE_PATH)
        states = config.get("states", [])
        assert (
            "committing_tests" not in states
        ), "committing_tests state should be removed"

    def test_test_demo_done_routes_to_critiquing(self):
        """AC-03: test_demo_done event routes directly to critiquing."""
        config = load_config(PIPELINE_PATH)
        transitions = get_transitions(config)
        td_transitions = [t for t in transitions if t.get("event") == "test_demo_done"]
        assert len(td_transitions) == 1
        assert td_transitions[0]["from"] == "testing_demo"
        assert td_transitions[0]["to"] == "critiquing"

    def test_no_tests_committed_event(self):
        """AC-03: tests_committed event should not exist."""
        config = load_config(PIPELINE_PATH)
        events = config.get("events", {})
        if isinstance(events, dict | list):
            assert "tests_committed" not in events

    def test_no_committing_tests_action_block(self):
        """AC-03: No action block for committing_tests state."""
        config = load_config(PIPELINE_PATH)
        actions = get_action_blocks(config)
        assert (
            "committing_tests" not in actions
        ), "committing_tests action block should be removed"


# ════════════════════════════════════════════════════════════════════════
# AC-04: changelog_gen uses bash, not yamlgraph_async
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestChangelogGenBash:
    """changelog_gen action must use bash type."""

    def test_changelog_gen_is_bash(self):
        """AC-04: changelog_gen action uses bash type."""
        config = load_config(PIPELINE_PATH)
        actions = get_action_blocks(config)
        changelog_actions = actions.get("changelog_gen", [])
        assert (
            len(changelog_actions) >= 1
        ), "changelog_gen must have at least one action"
        assert (
            changelog_actions[0].get("type") == "bash"
        ), f"changelog_gen should be bash, got: {changelog_actions[0].get('type')}"

    def test_changelog_gen_no_graph_key(self):
        """AC-04: changelog_gen action must not have a graph: key."""
        config = load_config(PIPELINE_PATH)
        actions = get_action_blocks(config)
        changelog_actions = actions.get("changelog_gen", [])
        for action in changelog_actions:
            assert (
                "graph" not in action
            ), "changelog_gen should not reference a graph file"


# ════════════════════════════════════════════════════════════════════════
# AC-05: Pipeline reduced to 25 states
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.req("REQ-YG-162")
class TestPipelineStateCount:
    """Pipeline must have exactly 25 states after simplification."""

    def test_pipeline_has_25_states(self):
        """AC-05: Pipeline reduced from 27 to 25 states."""
        config = load_config(PIPELINE_PATH)
        states = config.get("states", [])
        assert len(states) == 25, f"Expected 25 states, got {len(states)}: {states}"
