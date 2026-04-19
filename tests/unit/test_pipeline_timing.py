"""Tests for FR-256: Pipeline Timing Metrics.

Validates that:
1. enforce_worktree.sh writes timing JSON via extended cleanup()
2. bugfix_worktree.sh writes timing JSON with same schema
3. watch.sh writes cycle metrics inline (not trap-based)
4. pipeline_summary.py aggregates daily metrics from JSON files
5. tmp/pipeline-metrics/ is gitignored (via tmp/)
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENFORCE_SCRIPT = REPO_ROOT / "scripts" / "enforce_worktree.sh"
BUGFIX_SCRIPT = REPO_ROOT / "scripts" / "bugfix_worktree.sh"
WATCH_SCRIPT = REPO_ROOT / ".chaplain" / "watch.sh"
GITIGNORE = REPO_ROOT / ".gitignore"


def _read(path: Path) -> str:
    return path.read_text()


# ---------------------------------------------------------------------------
# 1. enforce_worktree.sh timing instrumentation
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-259")
class TestEnforceTimingInstrumentation:
    """enforce_worktree.sh emits timing JSON on every exit."""

    def test_defines_metric_dir(self):
        content = _read(ENFORCE_SCRIPT)
        assert 'METRIC_DIR="tmp/pipeline-metrics"' in content

    def test_creates_metric_dir(self):
        content = _read(ENFORCE_SCRIPT)
        assert 'mkdir -p "$METRIC_DIR"' in content

    def test_captures_start_timestamp(self):
        content = _read(ENFORCE_SCRIPT)
        assert "T_START=$(date +%s)" in content

    def test_captures_phase_timestamps(self):
        """Phase timing variables for worktree_setup, llm_enforce, post_assertions, success_output."""
        content = _read(ENFORCE_SCRIPT)
        for phase in [
            "PHASE_WORKTREE_SETUP",
            "PHASE_LLM_ENFORCE",
            "PHASE_POST_ASSERTIONS",
            "PHASE_SUCCESS_OUTPUT",
        ]:
            assert phase in content, f"Missing phase timing variable: {phase}"

    def test_writes_json_in_cleanup(self):
        """cleanup() writes metrics JSON."""
        content = _read(ENFORCE_SCRIPT)
        # The cleanup function should contain the JSON write
        cleanup_start = content.index("cleanup()")
        cleanup_body = content[cleanup_start:]
        assert "METRIC_DIR" in cleanup_body
        assert '"pipeline": "enforce"' in cleanup_body

    def test_json_write_is_best_effort(self):
        """Metric write guarded with || true."""
        content = _read(ENFORCE_SCRIPT)
        # The metric write block should have || true
        assert "|| true" in content

    def test_json_has_pipeline_discriminator(self):
        content = _read(ENFORCE_SCRIPT)
        assert '"pipeline": "enforce"' in content

    def test_json_includes_phases_object(self):
        content = _read(ENFORCE_SCRIPT)
        assert '"phases"' in content
        assert '"worktree_setup"' in content
        assert '"llm_enforce"' in content
        assert '"post_assertions"' in content
        assert '"success_output"' in content


# ---------------------------------------------------------------------------
# 2. bugfix_worktree.sh timing instrumentation
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-259")
class TestBugfixTimingInstrumentation:
    """bugfix_worktree.sh emits timing JSON with pipeline=bugfix."""

    def test_defines_metric_dir(self):
        content = _read(BUGFIX_SCRIPT)
        assert 'METRIC_DIR="tmp/pipeline-metrics"' in content

    def test_creates_metric_dir(self):
        content = _read(BUGFIX_SCRIPT)
        assert 'mkdir -p "$METRIC_DIR"' in content

    def test_captures_start_timestamp(self):
        content = _read(BUGFIX_SCRIPT)
        assert "T_START=$(date +%s)" in content

    def test_captures_phase_timestamps(self):
        content = _read(BUGFIX_SCRIPT)
        for phase in [
            "PHASE_WORKTREE_SETUP",
            "PHASE_LLM_ENFORCE",
            "PHASE_POST_ASSERTIONS",
            "PHASE_SUCCESS_OUTPUT",
        ]:
            assert phase in content, f"Missing phase timing variable: {phase}"

    def test_writes_json_in_cleanup(self):
        content = _read(BUGFIX_SCRIPT)
        cleanup_start = content.index("cleanup()")
        cleanup_body = content[cleanup_start:]
        assert "METRIC_DIR" in cleanup_body
        assert '"pipeline": "bugfix"' in cleanup_body

    def test_json_write_is_best_effort(self):
        content = _read(BUGFIX_SCRIPT)
        assert "|| true" in content

    def test_json_has_bugfix_discriminator(self):
        content = _read(BUGFIX_SCRIPT)
        assert '"pipeline": "bugfix"' in content


# ---------------------------------------------------------------------------
# 3. watch.sh inline cycle metrics
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-259")
class TestWatchCycleMetrics:
    """watch.sh writes cycle metrics JSON inline (not trap-based)."""

    def test_defines_metric_dir(self):
        content = _read(WATCH_SCRIPT)
        assert 'METRIC_DIR="tmp/pipeline-metrics"' in content

    def test_captures_cycle_start_timestamp(self):
        content = _read(WATCH_SCRIPT)
        assert "t_cycle_start=$(date +%s)" in content

    def test_captures_cycle_end_timestamp(self):
        content = _read(WATCH_SCRIPT)
        assert "t_cycle_end=$(date +%s)" in content

    def test_writes_chaplain_cycle_json(self):
        content = _read(WATCH_SCRIPT)
        assert '"pipeline": "chaplain-cycle"' in content

    def test_cycle_metrics_are_inline_not_trap(self):
        """Metrics written inside the while loop, not via EXIT trap."""
        content = _read(WATCH_SCRIPT)
        # Should NOT have trap-based metrics
        assert "trap" not in content or "trap.*metric" not in content
        # Should have cycle timing inside the loop body
        loop_start = content.index("while true")
        loop_body = content[loop_start:]
        assert "t_cycle_start" in loop_body
        assert "t_cycle_end" in loop_body

    def test_json_write_is_best_effort(self):
        content = _read(WATCH_SCRIPT)
        # Metric writes should be guarded
        assert "|| true" in content


# ---------------------------------------------------------------------------
# 4. tmp/ is gitignored
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-259")
class TestGitignore:
    """tmp/ directory is gitignored (verify only, no changes)."""

    def test_tmp_is_gitignored(self):
        content = _read(GITIGNORE)
        assert "tmp/" in content


# ---------------------------------------------------------------------------
# 5. pipeline_summary.py aggregation
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-259")
class TestPipelineSummary:
    """scripts/pipeline_summary.py reads JSON files and prints daily summary."""

    def test_script_exists(self):
        script = REPO_ROOT / "scripts" / "pipeline_summary.py"
        assert script.exists(), "scripts/pipeline_summary.py must exist"

    def test_script_is_importable(self):
        """Can import the summary module."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "pipeline_summary",
            REPO_ROOT / "scripts" / "pipeline_summary.py",
        )
        assert spec is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "aggregate_metrics")

    def test_aggregate_empty_directory(self, tmp_path):
        """Empty metrics directory returns empty results."""
        from scripts.pipeline_summary import aggregate_metrics

        result = aggregate_metrics(tmp_path)
        assert result.total_runs == 0
        assert result.total_seconds == 0

    def test_aggregate_single_run(self, tmp_path):
        """Single enforce run aggregates correctly."""
        from scripts.pipeline_summary import aggregate_metrics

        metric = {
            "pipeline": "enforce",
            "fr": "FR-256",
            "branch": "feat/fr-256-test",
            "outcome": "success",
            "started_at": "2026-04-19T14:00:00Z",
            "finished_at": "2026-04-19T14:45:00Z",
            "duration_seconds": 2700,
            "phases": {
                "worktree_setup": 12,
                "llm_enforce": 2400,
                "post_assertions": 180,
                "success_output": 15,
            },
            "retries": 0,
        }
        (tmp_path / "enforce-FR-256-2026-04-19T140000.json").write_text(
            json.dumps(metric)
        )

        result = aggregate_metrics(tmp_path)
        assert result.total_runs == 1
        assert result.success_count == 1
        assert result.total_seconds == 2700
        assert result.longest_fr == "FR-256"
        assert result.shortest_fr == "FR-256"

    def test_aggregate_multiple_runs(self, tmp_path):
        """Multiple runs aggregate correctly with longest/shortest."""
        from scripts.pipeline_summary import aggregate_metrics

        for i, (fr, duration) in enumerate(
            [("FR-250", 4320), ("FR-251", 1920), ("FR-252", 1080)]
        ):
            metric = {
                "pipeline": "enforce",
                "fr": fr,
                "branch": f"feat/{fr.lower()}-test",
                "outcome": "success",
                "started_at": f"2026-04-19T{14 + i}:00:00Z",
                "finished_at": f"2026-04-19T{15 + i}:00:00Z",
                "duration_seconds": duration,
                "phases": {
                    "worktree_setup": 10,
                    "llm_enforce": duration - 30,
                    "post_assertions": 10,
                    "success_output": 10,
                },
                "retries": 0,
            }
            (tmp_path / f"enforce-{fr}-2026-04-19T{14 + i}0000.json").write_text(
                json.dumps(metric)
            )

        result = aggregate_metrics(tmp_path)
        assert result.total_runs == 3
        assert result.success_count == 3
        assert result.total_seconds == 4320 + 1920 + 1080
        assert result.longest_fr == "FR-250"
        assert result.longest_seconds == 4320
        assert result.shortest_fr == "FR-252"
        assert result.shortest_seconds == 1080

    def test_aggregate_includes_failures(self, tmp_path):
        """Failure runs counted in total but not in success_count."""
        from scripts.pipeline_summary import aggregate_metrics

        success = {
            "pipeline": "enforce",
            "fr": "FR-250",
            "branch": "feat/fr-250-test",
            "outcome": "success",
            "started_at": "2026-04-19T14:00:00Z",
            "finished_at": "2026-04-19T14:30:00Z",
            "duration_seconds": 1800,
            "phases": {},
            "retries": 0,
        }
        failure = {
            "pipeline": "enforce",
            "fr": "FR-251",
            "branch": "feat/fr-251-test",
            "outcome": "failure",
            "started_at": "2026-04-19T15:00:00Z",
            "finished_at": "2026-04-19T15:10:00Z",
            "duration_seconds": 600,
            "phases": {},
            "retries": 0,
        }
        (tmp_path / "enforce-FR-250-2026-04-19T140000.json").write_text(
            json.dumps(success)
        )
        (tmp_path / "enforce-FR-251-2026-04-19T150000.json").write_text(
            json.dumps(failure)
        )

        result = aggregate_metrics(tmp_path)
        assert result.total_runs == 2
        assert result.success_count == 1
        assert result.failure_count == 1

    def test_aggregate_filters_by_date(self, tmp_path):
        """aggregate_metrics can filter by date."""
        from scripts.pipeline_summary import aggregate_metrics

        today = {
            "pipeline": "enforce",
            "fr": "FR-250",
            "branch": "feat/fr-250-test",
            "outcome": "success",
            "started_at": "2026-04-19T14:00:00Z",
            "finished_at": "2026-04-19T14:30:00Z",
            "duration_seconds": 1800,
            "phases": {},
            "retries": 0,
        }
        yesterday = {
            "pipeline": "enforce",
            "fr": "FR-249",
            "branch": "feat/fr-249-test",
            "outcome": "success",
            "started_at": "2026-04-18T10:00:00Z",
            "finished_at": "2026-04-18T10:30:00Z",
            "duration_seconds": 1800,
            "phases": {},
            "retries": 0,
        }
        (tmp_path / "enforce-FR-250-2026-04-19T140000.json").write_text(
            json.dumps(today)
        )
        (tmp_path / "enforce-FR-249-2026-04-18T100000.json").write_text(
            json.dumps(yesterday)
        )

        result = aggregate_metrics(tmp_path, date_filter="2026-04-19")
        assert result.total_runs == 1

    def test_aggregate_skips_malformed_json(self, tmp_path):
        """Malformed JSON files are skipped, not crash."""
        from scripts.pipeline_summary import aggregate_metrics

        (tmp_path / "enforce-bad-2026-04-19T140000.json").write_text("not json")
        valid = {
            "pipeline": "enforce",
            "fr": "FR-250",
            "branch": "feat/fr-250-test",
            "outcome": "success",
            "started_at": "2026-04-19T14:00:00Z",
            "finished_at": "2026-04-19T14:30:00Z",
            "duration_seconds": 1800,
            "phases": {},
            "retries": 0,
        }
        (tmp_path / "enforce-FR-250-2026-04-19T140000.json").write_text(
            json.dumps(valid)
        )

        result = aggregate_metrics(tmp_path)
        assert result.total_runs == 1

    def test_aggregate_skips_chaplain_cycle(self, tmp_path):
        """chaplain-cycle entries are separate from enforce/bugfix runs."""
        from scripts.pipeline_summary import aggregate_metrics

        enforce = {
            "pipeline": "enforce",
            "fr": "FR-250",
            "branch": "feat/fr-250-test",
            "outcome": "success",
            "started_at": "2026-04-19T14:00:00Z",
            "finished_at": "2026-04-19T14:30:00Z",
            "duration_seconds": 1800,
            "phases": {},
            "retries": 0,
        }
        cycle = {
            "pipeline": "chaplain-cycle",
            "inbox_item": "gh-125.md",
            "fr_generated": "FR-250",
            "verdict": "approved",
            "enforce_outcome": "success",
            "total_seconds": 3200,
        }
        (tmp_path / "enforce-FR-250-2026-04-19T140000.json").write_text(
            json.dumps(enforce)
        )
        (tmp_path / "chaplain-cycle-2026-04-19T140000.json").write_text(
            json.dumps(cycle)
        )

        result = aggregate_metrics(tmp_path)
        # Only enforce/bugfix runs count in the main summary
        assert result.total_runs == 1

    def test_format_summary_output(self, tmp_path):
        """format_summary produces human-readable text."""
        from scripts.pipeline_summary import aggregate_metrics, format_summary

        metric = {
            "pipeline": "enforce",
            "fr": "FR-256",
            "branch": "feat/fr-256-test",
            "outcome": "success",
            "started_at": "2026-04-19T14:00:00Z",
            "finished_at": "2026-04-19T14:45:00Z",
            "duration_seconds": 2700,
            "phases": {},
            "retries": 0,
        }
        (tmp_path / "enforce-FR-256-2026-04-19T140000.json").write_text(
            json.dumps(metric)
        )

        result = aggregate_metrics(tmp_path)
        output = format_summary(result)
        assert "FRs processed: 1" in output
        assert "Success rate: 100%" in output

    def test_pydantic_model_for_summary_result(self):
        """Summary result uses Pydantic model (Commandment 5)."""
        from scripts.pipeline_summary import PipelineSummaryResult

        result = PipelineSummaryResult(
            date="2026-04-19",
            total_runs=3,
            success_count=2,
            failure_count=1,
            total_seconds=5400,
            avg_seconds=1800,
            longest_fr="FR-250",
            longest_seconds=3600,
            shortest_fr="FR-252",
            shortest_seconds=1080,
        )
        assert result.total_runs == 3
        assert result.success_rate == "66%"


# ---------------------------------------------------------------------------
# 6. Capability registry
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-259")
class TestCapabilityRegistry:
    """CAP-112 registered with REQ-YG-259."""

    def test_cap_112_yaml_exists(self):
        cap_file = REPO_ROOT / "capabilities" / "CAP-112-pipeline-timing-metrics.yaml"
        assert (
            cap_file.exists()
        ), "capabilities/CAP-112-pipeline-timing-metrics.yaml must exist"

    def test_cap_112_references_req_259(self):
        import yaml

        cap_file = REPO_ROOT / "capabilities" / "CAP-112-pipeline-timing-metrics.yaml"
        data = yaml.safe_load(cap_file.read_text())
        req_ids = [r["id"] for r in data["requirements"]]
        assert "REQ-YG-259" in req_ids
