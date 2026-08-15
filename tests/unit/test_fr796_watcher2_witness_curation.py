"""Regression tests for FR-796 watcher2 witness curation (REQ-YG-206)."""

from pathlib import Path

import pytest

from yamlgraph.discovery import DEFAULT_GRAPH_PATTERNS, discover_graphs

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DEMOS = REPO_ROOT / "examples" / "demos"
CHAPLAIN_DEMOS = REPO_ROOT / ".chaplain" / "demos"

DELETED_WITNESSES = {
    "script-retirement",
    "security-cve-ignore",
    "watcher2-red-verification",
}
RELOCATED_WITNESSES = {
    "watcher2-changelog-gen",
    "watcher2-ci-remediation",
    "watcher2-deduplication-gate",
    "watcher2-hook-preflight-gate",
    "watcher2-merged-branch-collision-guard",
    "watcher2-post-merge-inbox-consumption",
    "watcher2-remediation",
}
RETIRED_DISCOVERY_NAMES = {
    "Security CVE Ignore Demo",
    "TimestampBugDemo",
    "Watcher2 Remediation Demo",
    "Watcher2DeduplicationGateDemo",
    "Watcher2HookPreflightGateDemo",
    "Watcher2MergedBranchCollisionGuardDemo",
    "Watcher2PostMergeInboxConsumptionDemo",
    "watcher2-changelog-gen-demo",
    "watcher2-ci-remediation-demo",
}


@pytest.mark.req("REQ-YG-206")
def test_witnesses_are_removed_from_examples_garden() -> None:
    """Deleted and relocated witnesses no longer occupy examples/demos."""
    retired = DELETED_WITNESSES | RELOCATED_WITNESSES
    assert not {name for name in retired if (EXAMPLES_DEMOS / name).exists()}


@pytest.mark.req("REQ-YG-206")
def test_relocated_witnesses_live_under_chaplain() -> None:
    """All seven retained watcher2 witnesses live beside Chaplain runtime."""
    assert not {
        name for name in RELOCATED_WITNESSES if not (CHAPLAIN_DEMOS / name).is_dir()
    }


@pytest.mark.req("REQ-YG-206")
def test_retired_witnesses_are_absent_from_default_discovery() -> None:
    """Garden curation removes infrastructure witnesses from MCP discovery."""
    patterns = [str(REPO_ROOT / pattern) for pattern in DEFAULT_GRAPH_PATTERNS]
    discovered_names = {graph["name"] for graph in discover_graphs(patterns)}
    assert discovered_names.isdisjoint(RETIRED_DISCOVERY_NAMES)
