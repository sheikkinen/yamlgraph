"""FR-934: merge queue workflow wiring witnesses.

The merge queue delivers required contexts via merge_group events; a
required context that never reports removes the PR from the queue by
timeout (the FR-889 §4d deadlock class, queue edition). These tests pin
the exact wiring the judgement froze: both required-context workflows
trigger on merge_group, the commitlint job itself reports on merge
groups without executing PR-payload steps, and the test matrix keeps
its context names with the full matrix running on merge groups
(judgement R-2 option 1).
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_PATH = REPO_ROOT / ".github" / "workflows" / "workflow.yml"
COMMITLINT_PATH = REPO_ROOT / ".github" / "workflows" / "commitlint.yml"


def _load(path: Path) -> dict:
    assert path.exists(), f"Workflow file missing: {path}"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _on_block(wf: dict) -> dict:
    # Unquoted `on:` parses as boolean True in YAML 1.1.
    return wf.get("on", wf.get(True, {}))


@pytest.mark.req("REQ-YG-002")
class TestMergeGroupTriggers:
    """Both required-context workflows must trigger on merge_group."""

    def test_ci_workflow_triggers_on_merge_group(self) -> None:
        assert "merge_group" in _on_block(_load(CI_PATH)), (
            "workflow.yml must trigger on merge_group or the required "
            "test (3.11)/(3.13) contexts never report on queue candidates"
        )

    def test_commitlint_workflow_triggers_on_merge_group(self) -> None:
        assert "merge_group" in _on_block(_load(COMMITLINT_PATH)), (
            "commitlint.yml must trigger on merge_group or the required "
            "commitlint context never reports on queue candidates"
        )

    def test_existing_pr_and_tag_triggers_unchanged(self) -> None:
        ci_on = _on_block(_load(CI_PATH))
        cl_on = _on_block(_load(COMMITLINT_PATH))
        assert set(ci_on["pull_request"]["types"]) == {
            "opened",
            "synchronize",
            "reopened",
        }
        assert ci_on["push"]["tags"] == ["v*.*.*"]
        assert set(cl_on["pull_request"]["types"]) == {
            "opened",
            "edited",
            "synchronize",
            "reopened",
        }
        assert cl_on["push"]["tags"] == ["v*"]


@pytest.mark.req("REQ-YG-002")
class TestCommitlintJobShape:
    """The required context is job id `commitlint`; it must report on
    merge_group without executing PR-payload steps (judgement R-3)."""

    def _job(self) -> dict:
        return _load(COMMITLINT_PATH)["jobs"]["commitlint"]

    def test_job_id_is_commitlint(self) -> None:
        assert "commitlint" in _load(COMMITLINT_PATH)["jobs"], (
            "Branch protection names the `commitlint` context; "
            "the job id must not change"
        )

    def test_job_runs_for_merge_group(self) -> None:
        condition = self._job().get("if", "")
        assert "merge_group" in condition and "pull_request" in condition, (
            "The commitlint job must run for both pull_request and "
            "merge_group events; a skipped required context never reports"
        )

    def test_pr_title_validation_is_pr_only(self) -> None:
        steps = self._job()["steps"]
        semantic = [s for s in steps if "semantic" in str(s.get("uses", "")).lower()]
        assert semantic, "PR title validation step must remain"
        for step in semantic:
            assert "pull_request" in step.get("if", ""), (
                "action-semantic-pull-request reads github.event.pull_request "
                "and must be guarded to pull_request events"
            )

    def test_merge_group_noop_step_in_same_job(self) -> None:
        steps = self._job()["steps"]
        noop = [
            s
            for s in steps
            if "merge_group" in str(s.get("if", ""))
            and "pull_request" not in str(s.get("if", ""))
        ]
        assert noop, (
            "A merge-group-only no-op step must exist in the commitlint "
            "job so the required context reaches a conclusion on queue "
            "candidates (title already validated at PR time)"
        )


@pytest.mark.req("REQ-YG-002")
class TestCiMatrixOnMergeGroup:
    """workflow.yml must keep its context names and run the full matrix
    on merge groups (judgement R-2 option 1: the queue candidate is the
    integration boundary)."""

    def test_matrix_context_names_unchanged(self) -> None:
        test_job = _load(CI_PATH)["jobs"]["test"]
        assert test_job["strategy"]["matrix"]["python-version"] == [
            "3.11",
            "3.13",
        ], "Required contexts are `test (3.11)` and `test (3.13)`"

    def test_changes_gate_short_circuits_non_pr_events(self) -> None:
        changes = _load(CI_PATH)["jobs"]["changes"]
        code_expr = changes["outputs"]["code"]
        assert "github.event_name != 'pull_request'" in code_expr, (
            "Non-PR events (merge_group, tag push) must short-circuit to "
            "code == 'true' so merge groups run the full matrix (R-2 "
            "option 1) and the release chain can never skip (FR-919 C-3)"
        )
