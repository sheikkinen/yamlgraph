"""FR-553: deterministic turn-director prompt-mass + presence witness.

Measurement-only investigation harness (visibility, not a gate). These tests pin the
two deliverables the judgement froze:

- ``prompt_mass_summary`` recomputes ``running_scene`` offline and tiktoken-counts the
  director's actual scene mass (quantity #3 -- NOT the 12k turn-graph total, which is the
  5-call sum dominated by the intent sub-calls). tiktoken-absent degrades to ``None``
  (omission), never a char/4 proxy, never a gate (C2).
- ``presence_correlation`` answers C3: for each continuity break, was the governing
  fact's subject present in the scene at the failing turn? Absent -> a presence gap (the
  bounded/re-rank fix). Present-but-the-break-still-happened -> wording/recap, not mass.

Example tests are requirement-exempt (FR-474 J3): no ``@pytest.mark.req``, deterministic,
no live LLM, no LangSmith.
"""

from __future__ import annotations

from examples.dungeon_master.api import prompt_salience


def _two_chapter_doc() -> dict:
    """A minimal doc ``running_scene(doc, cid, n)`` can assemble for two chapters.

    Ch1 turn-1 names Hilde (a present subject); Ch2 turn-1 does NOT (an absent subject) --
    the two presence outcomes the correlation must separate.
    """
    return {
        "chapters": {
            "order": ["1", "2"],
            "cards": {
                "1": {
                    "title": "Ch1",
                    "summary": "Hilde raids the Baerenschaedel at dawn.",
                    "beats": ["Hilde raids", "Flood cuts them off"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {"beats_satisfied": [1]},
                            "recap": {"text": "Hilde struck at the shelf."},
                        }
                    ],
                },
                "2": {
                    "title": "Ch2",
                    "summary": "They survive together on the ledge.",
                    "beats": ["Share warmth", "Bond forms"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {"beats_satisfied": []},
                            "recap": {"text": "They shared the cloak."},
                        },
                        {
                            "n": 2,
                            "direction": {"beats_satisfied": [1]},
                            "recap": {"text": "Trust grew between them."},
                        },
                    ],
                },
            },
        },
        "characters": {
            "roster": ["hilde"],
            "cards": {"hilde": {"name": "Hilde", "reviewed": True}},
        },
    }


def test_prompt_mass_summary_counts_each_turn():
    """Per-turn scene token mass is recomputed for every turn of every chapter."""
    summary = prompt_mass_summary_or_skip()
    assert summary["encoding"] == "cl100k_base"
    assert summary["posture"] == "visibility-not-gate"
    chapters = {c["chapter"]: c for c in summary["by_chapter"]}
    assert set(chapters) == {"1", "2"}
    assert chapters["1"]["turn_count"] == 1
    assert chapters["2"]["turn_count"] == 2
    assert len(chapters["2"]["per_turn"]) == 2
    assert all(t["scene_tokens"] > 0 for t in chapters["2"]["per_turn"])
    assert summary["peak_scene_tokens"] == max(
        t["scene_tokens"] for c in summary["by_chapter"] for t in c["per_turn"]
    )


def prompt_mass_summary_or_skip() -> dict:
    """Compute the mass summary; the harness requires tiktoken (present in this env)."""
    summary = prompt_salience.prompt_mass_summary(_two_chapter_doc())
    assert summary is not None, "tiktoken expected in the test environment"
    return summary


def test_prompt_mass_summary_none_without_tiktoken(monkeypatch):
    """No tiktoken -> the block is omitted (None), never a char/4 proxy (C2)."""
    monkeypatch.setattr(prompt_salience, "_encoder", lambda: None)
    assert prompt_salience.prompt_mass_summary(_two_chapter_doc()) is None


def test_presence_correlation_flags_absent_subject():
    """A subject NOT in the failing-turn scene is a presence gap (-> bounded fix)."""
    doc = _two_chapter_doc()
    witness = {
        "fact_reversal": {
            "by_chapter": [
                {
                    "to_chapter": "2",
                    "gaps": [
                        {"subject": "Hilde", "prior_fact": "Hilde present and alive"}
                    ],
                }
            ]
        }
    }
    result = prompt_salience.presence_correlation(doc, witness)
    assert result["check_count"] == 1
    assert result["presence_gap_count"] == 1
    assert result["present_but_ignored_count"] == 0
    assert result["checks"][0]["subject_present_at_failing_turn"] is False


def test_presence_correlation_marks_present_subject():
    """A subject present in the failing-turn scene is present-but-ignored (-> wording)."""
    doc = _two_chapter_doc()
    witness = {
        "seam_entrance": {
            "by_chapter": [{"chapter": "1", "gaps": [{"name": "Hilde", "kind": "new"}]}]
        }
    }
    result = prompt_salience.presence_correlation(doc, witness)
    assert result["check_count"] == 1
    assert result["presence_gap_count"] == 0
    assert result["present_but_ignored_count"] == 1
    assert result["checks"][0]["subject_present_at_failing_turn"] is True


def test_format_report_is_terse_and_mentions_presence():
    """The report joins per-chapter mass and the presence verdict in one terse block."""
    doc = _two_chapter_doc()
    witness = {
        "prompt_mass": prompt_mass_summary_or_skip(),
        "presence_correlation": prompt_salience.presence_correlation(doc, {}),
    }
    report = prompt_salience.format_prompt_salience_report(witness)
    assert "presence" in report.lower()
    assert "chapter" in report.lower()


def _exit_doc(later_recap: str) -> dict:
    """A one-chapter doc where the director benches Arnulf at turn 1.

    Turn 1 declares ``cast_exits=["Arnulf"]`` (his legitimate final action and exit);
    turn 2's recap is ``later_recap`` -- the strictly-later text the witness scans.
    """
    return {
        "chapters": {
            "order": ["1"],
            "cards": {
                "1": {
                    "title": "Ch1",
                    "summary": "The salt-road confrontation.",
                    "beats": ["Arnulf falls"],
                    "turns": [
                        {
                            "n": 1,
                            "direction": {"cast_exits": ["Arnulf"]},
                            "recap": {"text": "Arnulf went down and did not rise."},
                        },
                        {
                            "n": 2,
                            "direction": {"cast_exits": []},
                            "recap": {"text": later_recap},
                        },
                    ],
                }
            },
        }
    }


def test_revived_actors_flags_exited_then_onstage():
    """C1 true-positive: an exited name acting in a strictly-later recap is a revival."""
    doc = _exit_doc("Arnulf surges up once more, weapon raised.")
    result = prompt_salience.revived_actors(doc)
    assert result["posture"] == "visibility-not-gate"
    assert result["count"] == 1
    incident = result["incidents"][0]
    assert incident["chapter"] == "1"
    assert incident["name"] == "Arnulf"
    assert incident["exit_turn"] == 1
    assert incident["revival_turn"] == 2


def test_revived_actors_ignores_possessive_only():
    """C1 true-negative: a possessive-only later mention is aftermath, NOT a revival."""
    doc = _exit_doc("Hilde stepped over Arnulf's fallen body and held the line.")
    result = prompt_salience.revived_actors(doc)
    assert result["count"] == 0
    assert result["incidents"] == []


def test_revived_actors_empty_without_exits():
    """No recorded cast_exits anywhere -> nothing to revive (empty, never a gate)."""
    doc = _two_chapter_doc()
    result = prompt_salience.revived_actors(doc)
    assert result["count"] == 0
    assert result["incidents"] == []


def test_revived_actor_appears_in_report():
    """The terse report surfaces the revived-actor count when the block is present."""
    doc = _exit_doc("Arnulf surges up once more, weapon raised.")
    witness = {"revived_actor": prompt_salience.revived_actors(doc)}
    report = prompt_salience.format_prompt_salience_report(witness)
    assert "revived" in report.lower()
    assert "Arnulf" in report
