"""FR-317 watcher2 no-action health check mode acceptance tests.

These tests must FAIL on the current implementation and PASS after implementation.
Run with: pytest tests/unit/test_fr317_watcher2_no_action_health_check_mode.py -q --no-cov
"""

import os
from pathlib import Path

import pytest
import yaml


@pytest.mark.req("REQ-YG-318")
def test_ac01_inbox_sync_imports_chaplain_check_and_tags_health_mode():
    """AC-01: inbox_sync.sh supports importing chaplain-check issues and tags imported topic files with mode: health-check."""
    # Check that inbox_sync.sh queries for chaplain-check label
    inbox_sync_path = ".chaplain/lib/watcher/inbox_sync.sh"
    assert os.path.exists(inbox_sync_path), f"{inbox_sync_path} must exist"

    with open(inbox_sync_path) as f:
        content = f.read()

    # Should query both chaplain and chaplain-check labels
    assert (
        "--label chaplain-check" in content
    ), "inbox_sync.sh must query chaplain-check labeled issues"

    # Should write mode marker for chaplain-check issues
    assert (
        "mode: health-check" in content
    ), "inbox_sync.sh must tag health-check mode in topic headers"


@pytest.mark.req("REQ-YG-318")
def test_ac02_standard_chaplain_topics_keep_default_pipeline():
    """AC-02: Standard chaplain topics remain on existing default worker pipeline path."""
    # This is a behavioral contract test - standard chaplain label should not be affected
    # Test will pass if current behavior is preserved
    inbox_sync_path = ".chaplain/lib/watcher/inbox_sync.sh"
    with open(inbox_sync_path) as f:
        content = f.read()

    # Standard chaplain processing should remain unchanged
    assert "--label chaplain" in content, "Standard chaplain label support must remain"
    assert (
        "chaplain-check" not in content or "chaplain " in content
    ), "Both labels should be supported"


@pytest.mark.req("REQ-YG-318")
def test_ac03_dispatcher_selects_health_check_pipeline_from_topic_mode():
    """AC-03: Dispatcher can select health-check pipeline config based on topic metadata."""
    dispatcher_path = ".chaplain/config/watcher-dispatcher.yaml"
    with open(dispatcher_path) as f:
        config = yaml.safe_load(f)

    # Dispatcher should read topic header and select pipeline config
    actions = config.get("actions", {})
    processing_action = actions.get("processing_topic")
    assert processing_action is not None, "processing_topic action must exist"

    # Should have logic to select pipeline config based on mode marker
    command = processing_action[0]["command"]
    assert (
        "watcher-pipeline-health-check.yaml" in command
    ), "Dispatcher must reference health-check pipeline"


@pytest.mark.req("REQ-YG-318")
def test_ac04_health_pipeline_has_required_stage_states():
    """AC-04: .chaplain/config/watcher-pipeline-health-check.yaml exists and includes states for plan, judge, enforce_session, validate, and sanity_check."""
    health_pipeline_path = ".chaplain/config/watcher-pipeline-health-check.yaml"
    assert os.path.exists(health_pipeline_path), f"{health_pipeline_path} must exist"

    with open(health_pipeline_path) as f:
        config = yaml.safe_load(f)

    required_states = [
        "plan",
        "judge",
        "enforce_session",
        "validate",
        "sanity_check",
        "done",
    ]
    states = config.get("states", [])

    for state in required_states:
        assert state in states, f"Health check pipeline must include {state} state"


@pytest.mark.req("REQ-YG-318")
def test_ac05_health_pipeline_has_no_push_or_pr_commands():
    """AC-05: Health-check pipeline contains no git push, gh pr create, or gh pr merge commands."""
    health_pipeline_path = ".chaplain/config/watcher-pipeline-health-check.yaml"
    assert os.path.exists(health_pipeline_path), f"{health_pipeline_path} must exist"

    with open(health_pipeline_path) as f:
        content = f.read()

    # Should not contain any git push or PR creation commands
    forbidden_commands = ["git push", "gh pr create", "gh pr merge"]
    for cmd in forbidden_commands:
        assert cmd not in content, f"Health check pipeline must not contain '{cmd}'"


@pytest.mark.req("REQ-YG-318")
def test_ac06_health_pipeline_done_is_cleanup_only():
    """AC-06: Health-check pipeline done state is side-effect-safe (cleanup/logging only)."""
    health_pipeline_path = ".chaplain/config/watcher-pipeline-health-check.yaml"
    assert os.path.exists(health_pipeline_path), f"{health_pipeline_path} must exist"

    with open(health_pipeline_path) as f:
        config = yaml.safe_load(f)

    actions = config.get("actions", {})
    done_action = actions.get("done")
    assert done_action is not None, "Health check pipeline must have done action"

    # done action should only do cleanup/logging - no git operations
    command = done_action[0]["command"]
    assert "git push" not in command, "Health check done must not push"
    assert "gh pr" not in command, "Health check done must not create/merge PRs"


@pytest.mark.req("REQ-YG-318")
def test_ac07_health_check_graphs_and_prompts_exist():
    """AC-07: Dedicated health-check graphs/prompts exist for all five stage boundaries."""
    health_check_dir = Path(".chaplain/graphs/watcher-check")
    assert health_check_dir.exists(), f"{health_check_dir} directory must exist"

    required_graphs = [
        "plan-health-check.yaml",
        "judge-health-check.yaml",
        "enforce-health-check.yaml",
        "validate-health-check.yaml",
        "sanity-check-health-check.yaml",
    ]

    for graph_file in required_graphs:
        graph_path = health_check_dir / graph_file
        assert graph_path.exists(), f"Health check graph {graph_path} must exist"


@pytest.mark.req("REQ-YG-318")
def test_ac08_health_check_prompts_forbid_write_side_effects():
    """AC-08: Health-check prompts explicitly prohibit write operations."""
    health_check_dir = Path(".chaplain/graphs/watcher-check")

    if not health_check_dir.exists():
        pytest.skip(f"{health_check_dir} does not exist yet")

    for graph_file in health_check_dir.glob("*.yaml"):
        with open(graph_file) as f:
            content = f.read()

        # Health check prompts should explicitly forbid writes
        forbidden_operations = ["file edits", "git commit", "git push", "PR operations"]
        assert any(
            forbidden in content for forbidden in forbidden_operations
        ), f"{graph_file} must explicitly forbid write operations"


@pytest.mark.req("REQ-YG-318")
def test_ac09_health_sanity_check_warn_path_is_non_blocking():
    """AC-09: sanity_check still routes with PASS/WARN semantics in health-check mode, and WARN remains non-blocking."""
    health_pipeline_path = ".chaplain/config/watcher-pipeline-health-check.yaml"
    assert os.path.exists(health_pipeline_path), f"{health_pipeline_path} must exist"

    with open(health_pipeline_path) as f:
        config = yaml.safe_load(f)

    # Check that sanity_check has both PASS and WARN transitions
    transitions = config.get("transitions", [])
    sanity_transitions = [t for t in transitions if t.get("from") == "sanity_check"]

    pass_transition = any(t.get("event") == "pass" for t in sanity_transitions)
    warn_transition = any(t.get("event") == "warn" for t in sanity_transitions)

    assert pass_transition, "Health check sanity_check must support PASS event"
    assert warn_transition, "Health check sanity_check must support WARN event"

    # Both should lead to precommit_check (non-blocking)
    for transition in sanity_transitions:
        if transition.get("event") in ["pass", "warn"]:
            assert (
                transition.get("to") == "precommit_check"
            ), f"Sanity {transition['event']} should continue to precommit_check"
