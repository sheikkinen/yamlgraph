"""Deterministic tests for FR-508 continuity witness metrics helpers."""

from __future__ import annotations

from examples.dungeon_master.api import witness_metrics


def test_parse_generation_log_metrics_counts_gate_lines_and_timeout():
    log = "\n".join(
        [
            "INFO start",
            "WARNING Lifecycle gate violation: {'violations':[{'detail':'confirmed_dead character cannot be active'}]}",
            "WARNING Continuity memory conflict: {'violations':[{'detail':'x'}]}",
            "INFO Final cut revise applied: {'chapter_id':'7','attempt_count':1,'revised':True}",
            "RuntimeError: book gate did not open within turn_cap=96",
        ]
    )
    metrics = witness_metrics.parse_generation_log_metrics(log)
    assert metrics["lifecycle_gate_violation_count"] == 1
    assert metrics["continuity_memory_conflict_count"] == 1
    assert metrics["dead_alive_opening_contradiction_count"] == 1
    assert metrics["final_cut_revise_applied_count"] == 1
    assert metrics["book_gate_opened"] is False


def test_parse_story_progress_metrics_counts_completed_and_turns():
    doc = {
        "chapters": {
            "order": ["1", "2", "3"],
            "cards": {
                "1": {"reviewed": True, "text": "t1", "turns": [{"n": 1}]},
                "2": {"reviewed": True, "text": "", "turns": [{"n": 1}, {"n": 2}]},
                "3": {"reviewed": False, "text": "t3", "turns": []},
            },
        }
    }
    metrics = witness_metrics.parse_story_progress_metrics(doc)
    assert metrics["planned_chapter_count"] == 3
    assert metrics["completed_chapter_count"] == 1
    assert metrics["total_turns_used"] == 3


def test_build_witness_summary_evaluates_fr508_a5_checks():
    log = "INFO no failures"
    doc = {
        "chapters": {
            "order": ["1"],
            "cards": {"1": {"reviewed": True, "text": "ok", "turns": [{"n": 1}]}},
        }
    }
    summary = witness_metrics.build_witness_summary(log, doc)
    assert summary["evaluation"]["checks"]["zero_lifecycle_gate_violations"] is True
    assert summary["evaluation"]["checks"]["completed_equals_planned"] is True
    assert summary["evaluation"]["checks"]["book_gate_opened_before_turn_cap"] is True
    assert summary["evaluation"]["pass"] is True


def test_book_gate_check_fails_for_incomplete_story_without_timeout_line():
    log = "INFO still running"
    doc = {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {"reviewed": True, "text": "ok", "turns": [{"n": 1}]},
                "2": {"reviewed": False, "text": "", "turns": [{"n": 1}]},
            },
        }
    }
    summary = witness_metrics.build_witness_summary(log, doc)
    assert summary["evaluation"]["checks"]["completed_equals_planned"] is False
    assert summary["evaluation"]["checks"]["book_gate_opened_before_turn_cap"] is False
