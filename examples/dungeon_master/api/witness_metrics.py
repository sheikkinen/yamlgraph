"""Deterministic continuity witness metrics for FR-508 A5.

Pure utilities that parse generation logs and story artifacts to compute
objective pass/fail signals for continuity enforcement quality.
"""

from __future__ import annotations

import json
import re

_LOG_LINE_LIFECYCLE = re.compile(r"Lifecycle gate violation:")
_LOG_LINE_MEMORY = re.compile(r"Continuity memory conflict:")
_LOG_LINE_DEAD_PROSE = re.compile(r"Dead character prose violation:")
_LOG_LINE_FINAL_CUT_REVISE = re.compile(r"Final cut revise applied:")
_DEAD_ACTIVE = re.compile(
    r"(confirmed_dead character cannot be active|"
    r"missing_presumed_dead character cannot be active)"
)


def parse_generation_log_metrics(log_text: str) -> dict:
    """Extract deterministic continuity counters from generation log text."""
    lines = (log_text or "").splitlines()
    lifecycle = 0
    memory = 0
    dead_alive = 0
    dead_prose = 0
    revise_applied = 0

    for line in lines:
        if _LOG_LINE_LIFECYCLE.search(line):
            lifecycle += 1
            if _DEAD_ACTIVE.search(line):
                dead_alive += 1
        elif _LOG_LINE_MEMORY.search(line):
            memory += 1
            if _DEAD_ACTIVE.search(line):
                dead_alive += 1
        elif _LOG_LINE_DEAD_PROSE.search(line):
            dead_prose += 1
        elif _LOG_LINE_FINAL_CUT_REVISE.search(line):
            revise_applied += 1

    turn_cap_timeout = "book gate did not open within turn_cap" in (log_text or "")
    return {
        "lifecycle_gate_violation_count": lifecycle,
        "continuity_memory_conflict_count": memory,
        "dead_alive_opening_contradiction_count": dead_alive,
        "dead_character_prose_violation_count": dead_prose,
        "final_cut_revise_applied_count": revise_applied,
        "book_gate_opened": not turn_cap_timeout,
    }


def parse_story_progress_metrics(story_doc: dict) -> dict:
    """Extract chapter progression counters from story artifact dict."""
    chapters = dict(story_doc.get("chapters") or {})
    order = list(chapters.get("order") or [])
    cards = dict(chapters.get("cards") or {})

    completed = 0
    total_turns = 0
    for cid in order:
        card = dict(cards.get(cid) or {})
        text = str(card.get("text") or "").strip()
        if bool(card.get("reviewed")) and bool(text):
            completed += 1
        total_turns += len(list(card.get("turns") or []))

    return {
        "planned_chapter_count": len(order),
        "completed_chapter_count": completed,
        "total_turns_used": total_turns,
    }


def evaluate_fr508_a5(log_metrics: dict, story_metrics: dict) -> dict:
    """Evaluate FR-508 A5 pass/fail thresholds."""
    completed_equals_planned = int(
        story_metrics.get("completed_chapter_count") or 0
    ) == int(story_metrics.get("planned_chapter_count") or 0)
    checks = {
        "zero_lifecycle_gate_violations": (
            int(log_metrics.get("lifecycle_gate_violation_count") or 0) == 0
        ),
        "zero_continuity_memory_conflicts": (
            int(log_metrics.get("continuity_memory_conflict_count") or 0) == 0
        ),
        "zero_dead_alive_opening_contradictions": (
            int(log_metrics.get("dead_alive_opening_contradiction_count") or 0) == 0
        ),
        # A partial/in-progress artifact can lack timeout text while still
        # incomplete; require both gate-open signal and full completion.
        "book_gate_opened_before_turn_cap": (
            bool(log_metrics.get("book_gate_opened")) and completed_equals_planned
        ),
        "completed_equals_planned": completed_equals_planned,
    }
    return {
        "checks": checks,
        "pass": all(checks.values()),
    }


def _dead_prose_is_measurement_only(log_metrics: dict) -> bool:
    """FR-510: dead_character_prose_violation_count is a measurement target only."""
    return int(log_metrics.get("dead_character_prose_violation_count") or 0) == 0


def build_witness_summary(log_text: str, story_doc: dict) -> dict:
    """Compute full FR-508 A5 witness summary from raw artifacts."""
    log_metrics = parse_generation_log_metrics(log_text)
    story_metrics = parse_story_progress_metrics(story_doc)
    evaluation = evaluate_fr508_a5(log_metrics, story_metrics)
    return {
        "metrics": {**log_metrics, **story_metrics},
        "evaluation": evaluation,
    }


def render_markdown_table(summary: dict) -> str:
    """Render witness summary as a compact markdown table."""
    metrics = dict(summary.get("metrics") or {})
    checks = dict((summary.get("evaluation") or {}).get("checks") or {})
    lines = [
        "| Metric | Value |",
        "| --- | --- |",
        f"| lifecycle_gate_violation_count | {metrics.get('lifecycle_gate_violation_count', 0)} |",
        f"| continuity_memory_conflict_count | {metrics.get('continuity_memory_conflict_count', 0)} |",
        (
            "| dead_alive_opening_contradiction_count | "
            f"{metrics.get('dead_alive_opening_contradiction_count', 0)} |"
        ),
        (
            "| dead_character_prose_violation_count (measure) | "
            f"{metrics.get('dead_character_prose_violation_count', 0)} |"
        ),
        (
            "| final_cut_revise_applied_count (measure) | "
            f"{metrics.get('final_cut_revise_applied_count', 0)} |"
        ),
        f"| planned_chapter_count | {metrics.get('planned_chapter_count', 0)} |",
        f"| completed_chapter_count | {metrics.get('completed_chapter_count', 0)} |",
        f"| total_turns_used | {metrics.get('total_turns_used', 0)} |",
        f"| book_gate_opened | {metrics.get('book_gate_opened', False)} |",
        "",
        "| Check | Pass |",
        "| --- | --- |",
    ]
    for key, value in checks.items():
        lines.append(f"| {key} | {bool(value)} |")
    lines.append("")
    lines.append(f"Overall pass: {bool((summary.get('evaluation') or {}).get('pass'))}")
    return "\n".join(lines)


def render_json(summary: dict) -> str:
    """Render witness summary as deterministic JSON."""
    return json.dumps(summary, indent=2, sort_keys=True)
