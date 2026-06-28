"""Plot Modeller spike tests — L4 validator/evaluator + L1 evaluator.

Covers the validator (AC#2, AC#5 incl. the J1 crash regression) and the
evaluator scoring of absent/unparseable output (AC#6, J6).
FR-573: L1 evaluation — agent recall/precision, world recall, belief recall.
"""

from __future__ import annotations

from evaluate import (
    _content_words,
    _fluent_matches,
    _goal_matches,
    _jaccard,
    _norm_args,
    compare,
    score_genre,
    score_l1,
    score_l2,
    score_l3,
    summarise,
    summarise_l1,
    summarise_l2,
    summarise_l3,
    summarise_l5,
)
from nodes.tools import validate_kinds

GLOSSES = [
    {"id": "F1", "gloss": "Hagen's men abduct Pell.", "chapter": 1},
    {"id": "F2", "gloss": "Marren finds the witness gone.", "chapter": 1},
]


class TestValidateKinds:
    """AC#2 / AC#5 — validator contract."""

    def test_golden_success_writes_kinds(self):
        """Valid YAML list → kinds written, validation ok (golden)."""
        raw = (
            "- id: F1\n  kind: villainy\n  subject: Hagen\n"
            "- id: F2\n  kind: lack\n  subject: Marren\n"
        )
        out = validate_kinds({"kinds_raw": raw, "glosses": GLOSSES})
        assert out["validation"]["ok"] is True
        assert out["validation"]["flaws"] == []
        assert [item["kind"] for item in out["kinds"]] == ["villainy", "lack"]

    def test_empty_raw_does_not_crash(self):
        """J1 regression: empty kinds_raw (yaml→None) must not raise TypeError.

        The pre-fix validator did `for item in items` where items=None, crashing
        the graph on the first validation. The fix guards with isinstance(list).
        """
        out = validate_kinds({"kinds_raw": "", "glosses": GLOSSES})
        assert out["validation"]["ok"] is False
        assert "kinds" not in out  # J1: never write kinds on failure

    def test_scalar_raw_is_invalid(self):
        """Non-list YAML (a scalar) → invalid, no crash."""
        out = validate_kinds({"kinds_raw": "just a string", "glosses": GLOSSES})
        assert out["validation"]["ok"] is False
        assert "kinds" not in out

    def test_rejects_unknown_kind(self):
        """Unknown kind label → flaw, kinds absent."""
        raw = "- id: F1\n  kind: betrayal\n  subject: Hagen\n"
        out = validate_kinds({"kinds_raw": raw, "glosses": [GLOSSES[0]]})
        assert out["validation"]["ok"] is False
        assert any("betrayal" in f for f in out["validation"]["flaws"])
        assert "kinds" not in out

    def test_rejects_missing_subject(self):
        """Missing subject → flaw."""
        raw = "- id: F1\n  kind: villainy\n"
        out = validate_kinds({"kinds_raw": raw, "glosses": [GLOSSES[0]]})
        assert out["validation"]["ok"] is False
        assert any("subject" in f for f in out["validation"]["flaws"])

    def test_rejects_missing_glosses(self):
        """A gloss left unclassified → 'missing' flaw."""
        raw = "- id: F1\n  kind: villainy\n  subject: Hagen\n"
        out = validate_kinds({"kinds_raw": raw, "glosses": GLOSSES})
        assert out["validation"]["ok"] is False
        assert any("missing" in f for f in out["validation"]["flaws"])

    def test_invalid_yaml_syntax(self):
        """Unparseable YAML → caught, reported, no crash."""
        out = validate_kinds(
            {"kinds_raw": "- id: F1\n  kind: : :\n", "glosses": GLOSSES}
        )
        assert out["validation"]["ok"] is False
        assert "kinds" not in out


TRUTH = [
    {"id": "F1", "kind": "villainy", "subject": "Hagen"},
    {"id": "F2", "kind": "lack", "subject": "Marren"},
]


class TestEvaluate:
    """AC#6 / J6 — evaluator scoring of absent/unparseable predictions."""

    def test_golden_all_correct(self):
        """Perfect prediction → full marks, valid YAML true."""
        predicted = [
            {"id": "F1", "kind": "villainy", "subject": "Hagen"},
            {"id": "F2", "kind": "lack", "subject": "Marren"},
        ]
        ev = score_genre("detective", predicted, TRUTH, "anthropic", "haiku")
        assert ev["summary"]["kind_correct"] == 2
        assert ev["summary"]["kind_accuracy"] == "2/2 (1.00)"
        assert ev["summary"]["subject_correct"] == 2
        assert ev["summary"]["produced_valid_yaml"] is True
        assert ev["confusions"] == []
        assert ev["meta"]["corpus"] == "self-derived (upper-bound)"  # J2

    def test_absent_prediction_scores_all_wrong(self):
        """J6: predicted=None → every function wrong, no crash."""
        ev = score_genre("horror", None, TRUTH, "anthropic", "haiku")
        assert ev["summary"]["kind_correct"] == 0
        assert ev["summary"]["kind_accuracy"] == "0/2 (0.00)"
        assert ev["summary"]["produced_valid_yaml"] is False
        assert len(ev["confusions"]) == 2

    def test_non_list_prediction_scores_all_wrong(self):
        """J6: a scalar prediction is treated as all-wrong, never crashes."""
        ev = score_genre("scifi", "garbage", TRUTH, "anthropic", "haiku")
        assert ev["summary"]["kind_correct"] == 0
        assert ev["summary"]["produced_valid_yaml"] is False

    def test_confusion_recorded(self):
        """A misclassification is recorded as expected-vs-predicted."""
        predicted = [
            {"id": "F1", "kind": "villainy", "subject": "Hagen"},
            {"id": "F2", "kind": "pursuit", "subject": "Marren"},  # wrong kind
        ]
        per_function, confusions = compare(predicted, TRUTH)
        assert per_function[1]["kind_match"] is False
        assert confusions == [
            {"expected": "lack", "predicted": "pursuit", "function": "F2"}
        ]

    def test_subject_match_is_tolerant(self):
        """Subject comparison ignores case and surrounding whitespace."""
        predicted = [
            {"id": "F1", "kind": "villainy", "subject": "  hagen "},
            {"id": "F2", "kind": "lack", "subject": "MARREN"},
        ]
        ev = score_genre("detective", predicted, TRUTH, "anthropic", "haiku")
        assert ev["summary"]["subject_correct"] == 2

    def test_summarise_stamps_corpus_ceiling(self):
        """Aggregate summary carries the self-derived ceiling (J2)."""
        ev = score_genre("detective", None, TRUTH, "anthropic", "haiku")
        summary = summarise([ev])
        assert summary["corpus"] == "self-derived (upper-bound)"
        assert summary["total_functions"] == 2
        assert summary["kind_accuracy"] == "0/2 (0.00)"


# ---------------------------------------------------------------------------
# FR-573 — L1 evaluator tests
# ---------------------------------------------------------------------------

L1_TRUTH = {
    "agents": ["Marren", "Hagen", "Witness Pell"],
    "initial_world": [
        {"pred": "alive", "args": ["Marren"], "value": True},
        {"pred": "alive", "args": ["Hagen"], "value": True},
        {"pred": "alive", "args": ["Witness Pell"], "value": True},
        {"pred": "at", "args": ["Witness Pell", "Safe house"], "value": True},
    ],
    "initial_belief": [
        {
            "observer": "Marren",
            "fluent": {"pred": "rel", "args": ["Hagen", "Consul Drey"]},
            "held": "neutral",
        }
    ],
}


class TestScoreL1:
    """FR-573 — L1 evaluation scoring."""

    def test_golden_perfect_extraction(self):
        """Perfect extraction → full marks."""
        predicted = {
            "agents": ["Marren", "Hagen", "Witness Pell"],
            "initial_world": [
                {"pred": "alive", "args": ["Marren"], "value": True},
                {"pred": "alive", "args": ["Hagen"], "value": True},
                {"pred": "alive", "args": ["Witness Pell"], "value": True},
                {"pred": "at", "args": ["Witness Pell", "Safe house"], "value": True},
            ],
            "initial_belief": [
                {
                    "observer": "Marren",
                    "fluent": {"pred": "rel", "args": ["Hagen", "Consul Drey"]},
                    "held": "neutral",
                }
            ],
        }
        ev = score_l1("detective", predicted, L1_TRUTH, "anthropic", "haiku")
        assert ev["summary"]["agent_recall"] == "3/3 (1.00)"
        assert ev["summary"]["agent_precision"] == "3/3 (1.00)"
        assert ev["summary"]["world_recall"] == "4/4 (1.00)"
        assert ev["summary"]["belief_recall"] == "1/1 (1.00)"
        assert ev["summary"]["produced_valid_yaml"] is True

    def test_absent_prediction_scores_zero(self):
        """None prediction → all zeros, no crash."""
        ev = score_l1("horror", None, L1_TRUTH, "anthropic", "haiku")
        assert ev["summary"]["agent_recall"] == "0/3 (0.00)"
        assert ev["summary"]["produced_valid_yaml"] is False

    def test_tolerant_agent_matching(self):
        """Agent names with different casing/whitespace still match."""
        predicted = {
            "agents": ["marren", "HAGEN", " Witness Pell "],
            "initial_world": [],
            "initial_belief": [],
        }
        ev = score_l1("detective", predicted, L1_TRUTH, "anthropic", "haiku")
        assert ev["summary"]["agent_recall"] == "3/3 (1.00)"

    def test_partial_agent_name_matches(self):
        """A contains/prefix match: 'Pell' matches 'Witness Pell' (C1)."""
        predicted = {
            "agents": ["Marren", "Hagen", "Pell"],
            "initial_world": [],
            "initial_belief": [],
        }
        ev = score_l1("detective", predicted, L1_TRUTH, "anthropic", "haiku")
        # "pell" is contained in "witness pell"
        assert ev["summary"]["agent_recall"] == "3/3 (1.00)"

    def test_tolerant_world_matching(self):
        """World fluents with name variants still match (C1)."""
        predicted = {
            "agents": ["Marren", "Hagen", "Witness Pell"],
            "initial_world": [
                {"pred": "alive", "args": ["marren"], "value": True},
                {"pred": "alive", "args": ["Hagen"], "value": True},
                {"pred": "alive", "args": ["Witness Pell"], "value": True},
                {
                    "pred": "at",
                    "args": ["Witness Pell", "the Safe House"],
                    "value": True,
                },
            ],
            "initial_belief": [],
        }
        ev = score_l1("detective", predicted, L1_TRUTH, "anthropic", "haiku")
        assert ev["summary"]["world_recall"] == "4/4 (1.00)"

    def test_extra_agents_ok_for_recall(self):
        """Extra agents lower precision but don't affect recall."""
        predicted = {
            "agents": ["Marren", "Hagen", "Witness Pell", "Extra Character"],
            "initial_world": [],
            "initial_belief": [],
        }
        ev = score_l1("detective", predicted, L1_TRUTH, "anthropic", "haiku")
        assert ev["summary"]["agent_recall"] == "3/3 (1.00)"
        assert ev["summary"]["agent_precision"] == "3/4 (0.75)"

    def test_summarise_l1_aggregates(self):
        """L1 summary aggregates across genres."""
        ev1 = score_l1("detective", None, L1_TRUTH, "a", "h")
        ev2 = score_l1(
            "quest",
            {"agents": ["A", "B"], "initial_world": [], "initial_belief": []},
            {"agents": ["A", "B"], "initial_world": [], "initial_belief": []},
            "a",
            "h",
        )
        summary = summarise_l1([ev1, ev2])
        # ev1: 0/3, ev2: 2/2 → 2/5
        assert summary["agent_recall"] == "2/5 (0.40)"


# ---------------------------------------------------------------------------
# FR-574 — L2 evaluator tests
# ---------------------------------------------------------------------------

L2_TRUTH_GOALS = [
    {"pred": "alive", "args": ["Witness Pell"], "value": True},
    {"pred": "holds", "args": ["Marren", "ledger"], "value": True},
    {"pred": "rel", "args": ["Hagen", "Consul Drey"], "value": "co-conspirator"},
]


class TestScoreL2:
    """FR-574 — L2 goal evaluation scoring."""

    def test_golden_perfect(self):
        predicted = [
            {"pred": "alive", "args": ["Witness Pell"], "value": True},
            {"pred": "holds", "args": ["Marren", "ledger"], "value": True},
            {
                "pred": "rel",
                "args": ["Hagen", "Consul Drey"],
                "value": "co-conspirator",
            },
        ]
        ev = score_l2("detective", predicted, L2_TRUTH_GOALS, "a", "h")
        assert ev["summary"]["goal_recall"] == "3/3 (1.00)"
        assert ev["summary"]["goal_precision"] == "3/3 (1.00)"

    def test_absent_prediction_zero(self):
        ev = score_l2("detective", None, L2_TRUTH_GOALS, "a", "h")
        assert ev["summary"]["goal_recall"] == "0/3 (0.00)"
        assert ev["summary"]["produced_valid_yaml"] is False

    def test_order_insensitive_rel_args(self):
        """C3: rel [A, B] should match rel [B, A]."""
        predicted = [
            {
                "pred": "rel",
                "args": ["Consul Drey", "Hagen"],
                "value": "co-conspirator",
            },
        ]
        truth = [
            {
                "pred": "rel",
                "args": ["Hagen", "Consul Drey"],
                "value": "co-conspirator",
            },
        ]
        ev = score_l2("detective", predicted, truth, "a", "h")
        assert ev["summary"]["goal_recall"] == "1/1 (1.00)"

    def test_tolerant_value_comparison(self):
        """C3: value 'co-conspirator' vs 'conspirator' — contains match."""
        predicted = [
            {"pred": "rel", "args": ["Hagen", "Consul Drey"], "value": "conspirator"},
        ]
        truth = [
            {
                "pred": "rel",
                "args": ["Hagen", "Consul Drey"],
                "value": "co-conspirator",
            },
        ]
        ev = score_l2("detective", predicted, truth, "a", "h")
        assert ev["summary"]["goal_recall"] == "1/1 (1.00)"

    def test_extra_goals_lower_precision(self):
        predicted = [
            {"pred": "alive", "args": ["Witness Pell"], "value": True},
            {"pred": "alive", "args": ["Marren"], "value": True},  # extra
        ]
        truth = [
            {"pred": "alive", "args": ["Witness Pell"], "value": True},
        ]
        ev = score_l2("detective", predicted, truth, "a", "h")
        assert ev["summary"]["goal_recall"] == "1/1 (1.00)"
        assert ev["summary"]["goal_precision"] == "1/2 (0.50)"

    def test_summarise_l2_aggregates(self):
        ev1 = score_l2("d", None, L2_TRUTH_GOALS, "a", "h")
        ev2 = score_l2(
            "q",
            [{"pred": "alive", "args": ["X"], "value": True}],
            [{"pred": "alive", "args": ["X"], "value": True}],
            "a",
            "h",
        )
        summary = summarise_l2([ev1, ev2])
        # 0/3 + 1/1 = 1/4
        assert summary["goal_recall"] == "1/4 (0.25)"


class TestSummariseL5Demotion:
    """FR-595 — world_recall is demoted from the L5 gate to a diagnostic.

    FR-594 proved world_recall scores agreement with a lossy GT skeleton, not
    story capture, and the power analysis (n=5) showed the gateable axis is the
    GT-anchored simulability discrimination (stamped in l5-measure-summary.yaml).
    summarise_l5 must therefore stop emitting a GO/REVISE/KILL verdict from
    world_recall. RED before implementation.
    """

    @staticmethod
    def _evaluation(genre: str, world_recall: float) -> dict:
        # world_gt fixed at 10; hits scale to the requested recall.
        hits = round(world_recall * 10)
        return {
            "meta": {"genre": genre},
            "summary": {"world_recall": f"{hits}/10"},
            "_counts": {
                "pre_world": {"hits": hits, "gt": 10, "pred": hits},
                "eff_world": {"hits": 0, "gt": 0, "pred": 0},
                "pre_belief": {"hits": 0, "gt": 0, "pred": 0},
                "eff_belief": {"hits": 0, "gt": 0, "pred": 0},
            },
        }

    def test_verdict_is_informational_even_on_low_world_recall(self):
        # 0.49 world_recall would have been a KILL under the old gate.
        summary = summarise_l5([self._evaluation("detective", 0.40)])
        assert summary["verdict"] == "informational"

    def test_verdict_is_informational_even_on_high_world_recall(self):
        # 0.90 world_recall would have been a GO under the old gate.
        summary = summarise_l5([self._evaluation("scifi", 0.90)])
        assert summary["verdict"] == "informational"

    def test_world_recall_retained_as_diagnostic_and_redirects_gate(self):
        summary = summarise_l5([self._evaluation("horror", 0.60)])
        # world_recall is still reported — as a diagnostic, not the gate.
        assert "world_recall" in summary
        # the note must redirect the L5 gate to the regenerability discrimination.
        assert "l5-measure-summary" in summary["note"]


# ---------------------------------------------------------------------------
# FR-581 — _norm_args underscore tolerance
# ---------------------------------------------------------------------------


class TestNormArgs:
    """FR-581 failure mode 3 — underscore/space normalization."""

    def test_underscore_equals_space(self):
        """charter_letter and charter letter should normalise identically."""
        assert _norm_args(["charter_letter"]) == _norm_args(["charter letter"])

    def test_strips_articles_and_lowercases(self):
        assert _norm_args(["The Crown"]) == ["crown"]

    def test_underscore_in_multi_arg(self):
        assert _norm_args(["firmware_channel", "ARIA"]) == ["firmware channel", "aria"]


class TestL2UnderscoreMatch:
    """FR-581 — underscore tolerance propagates through L2 scoring."""

    def test_holds_underscore_vs_space_matches(self):
        predicted = [
            {"pred": "holds", "args": ["Naima", "charter letter"], "value": True},
        ]
        truth = [
            {"pred": "holds", "args": ["Naima", "charter_letter"], "value": True},
        ]
        ev = score_l2("historical", predicted, truth, "a", "h")
        assert ev["summary"]["goal_recall"] == "1/1 (1.00)"


# ---------------------------------------------------------------------------
# FR-575 — L3 evaluator tests
# ---------------------------------------------------------------------------


class TestContentWords:
    """C6 — stopword stripping for Jaccard."""

    def test_strips_stopwords(self):
        words = _content_words("the hero finds a hidden door in the castle")
        assert "the" not in words
        assert "a" not in words
        assert "in" not in words
        assert "hero" in words
        assert "hidden" in words
        assert "door" in words
        assert "castle" in words

    def test_lowercases(self):
        words = _content_words("Marren Finds The Ledger")
        assert "marren" in words
        assert "finds" in words
        assert "ledger" in words


class TestJaccard:
    """C6 — Jaccard on content words."""

    def test_identical_sets(self):
        a = {"hero", "villain", "castle"}
        assert _jaccard(a, a) == 1.0

    def test_disjoint_sets(self):
        assert _jaccard({"hero"}, {"villain"}) == 0.0

    def test_partial_overlap(self):
        # {hero, villain} ∩ {hero, castle} = {hero}, union = {hero, villain, castle}
        assert abs(_jaccard({"hero", "villain"}, {"hero", "castle"}) - 1 / 3) < 0.01

    def test_empty_sets(self):
        assert _jaccard(set(), set()) == 1.0
        assert _jaccard({"hero"}, set()) == 0.0


L3_TRUTH_GLOSSES = [
    {
        "id": "F1",
        "gloss": "Hagen's hired men abduct Witness Pell from the safe house and burn the building.",
        "chapter": 1,
    },
    {
        "id": "F2",
        "gloss": "Marren arrives at the charred ruin and discovers the witness and ledger are gone.",
        "chapter": 1,
    },
    {
        "id": "F3",
        "gloss": "Marren traces the abductors through dock manifests to the warehouse district.",
        "chapter": 2,
    },
]


class TestScoreL3:
    """FR-575 — L3 beat evaluation scoring."""

    def test_golden_exact_glosses(self):
        """Identical glosses → perfect recall and precision."""
        ev = score_l3("d", L3_TRUTH_GLOSSES, L3_TRUTH_GLOSSES, "a", "h")
        assert ev["summary"]["beat_recall"] == "3/3 (1.00)"
        assert ev["summary"]["beat_precision"] == "3/3 (1.00)"
        assert ev["summary"]["count_delta"] == 0

    def test_absent_prediction_zero(self):
        ev = score_l3("d", None, L3_TRUTH_GLOSSES, "a", "h")
        assert ev["summary"]["beat_recall"] == "0/3 (0.00)"
        assert ev["summary"]["produced_valid_yaml"] is False

    def test_paraphrased_gloss_matches(self):
        """A paraphrased gloss with shared content words should match (C6)."""
        predicted = [
            {
                "id": "F1",
                "gloss": "Hired men abduct Pell from the safe house, burning the building behind them.",
                "chapter": 1,
            },
        ]
        truth = [
            {
                "id": "F1",
                "gloss": "Hagen's hired men abduct Witness Pell from the safe house and burn the building.",
                "chapter": 1,
            },
        ]
        ev = score_l3("d", predicted, truth, "a", "h", threshold=0.25)
        assert ev["summary"]["beat_recall"] == "1/1 (1.00)"

    def test_many_to_one_matching(self):
        """C5: one coarse predicted beat covering two GT beats counts both."""
        # One predicted beat covers both F1 and F2
        predicted = [
            {
                "id": "F1",
                "gloss": "Hagen's men abduct Witness Pell and burn the safe house. "
                "Marren arrives at the charred ruin and discovers the witness "
                "and ledger are both gone.",
                "chapter": 1,
            },
        ]
        ev = score_l3("d", predicted, L3_TRUTH_GLOSSES[:2], "a", "h", threshold=0.25)
        # Both GT beats should be recalled (many-to-one)
        assert ev["summary"]["beat_recall"] == "2/2 (1.00)"

    def test_count_delta(self):
        """Count delta reports the difference in beat counts."""
        predicted = [{"id": "F1", "gloss": "A beat.", "chapter": 1}]
        ev = score_l3("d", predicted, L3_TRUTH_GLOSSES, "a", "h")
        assert ev["summary"]["count_delta"] == 2  # |1 - 3| = 2

    def test_summarise_l3_aggregates(self):
        ev1 = score_l3("d", None, L3_TRUTH_GLOSSES, "a", "h")
        ev2 = score_l3(
            "q",
            [{"id": "F1", "gloss": "hero finds crown in the temple", "chapter": 1}],
            [{"id": "F1", "gloss": "hero finds crown in the temple", "chapter": 1}],
            "a",
            "h",
        )
        summary = summarise_l3([ev1, ev2])
        # 0/3 + 1/1 = 1/4
        assert summary["beat_recall"] == "1/4 (0.25)"


class TestArgsJaccardTolerance:
    """FR-583 Part 1 — multi-word arg Jaccard tolerance at both match seams.

    AC#1: multi-word args match by token Jaccard >= 0.5, single-word args keep
    exact match, covering BOTH the ``_fluent_matches`` (L1/L5 world) and
    ``_goal_matches`` (L2) seams (J:C1). RED before implementation.
    """

    # --- _args_jaccard_match helper contract (AC#2) ---
    def test_helper_multiword_accepts_at_threshold(self):
        from evaluate import _args_jaccard_match

        # {seoul, lab} vs {seoul} -> 1/2 = 0.50, at threshold, accept
        assert _args_jaccard_match("seoul lab", "seoul") is True
        # {river, road} vs {flooded, river, road} -> 2/3 = 0.67, accept
        assert _args_jaccard_match("river road", "flooded river road") is True

    def test_helper_multiword_rejects_below_threshold(self):
        from evaluate import _args_jaccard_match

        # {firmware, update} vs {firmware, channel} -> 1/3 = 0.33, reject
        assert _args_jaccard_match("firmware update", "firmware channel") is False

    def test_helper_singleword_pair_never_loosens(self):
        from evaluate import _args_jaccard_match

        # genuine single-word synonyms are not bridged by Jaccard (AC#7)
        assert _args_jaccard_match("together", "lovers") is False

    # --- _fluent_matches seam (L1/L5 world) ---
    def test_fluent_multiword_order_swapped_matches(self):
        """Order-swapped multi-word args (neither a substring of the other) match."""
        pred = {"pred": "at", "args": ["Mara", "road river"], "value": True}
        truth = {"pred": "at", "args": ["Mara", "river road"], "value": True}
        assert _fluent_matches(pred, truth) is True

    def test_fluent_multiword_interleaved_partial_matches(self):
        """Non-contiguous superset args match when Jaccard >= 0.5."""
        pred = {"pred": "at", "args": ["Mara", "Seoul quarter lab"], "value": True}
        truth = {"pred": "at", "args": ["Mara", "Seoul lab"], "value": True}
        assert _fluent_matches(pred, truth) is True  # 2/3 = 0.67

    def test_fluent_singleword_synonym_still_rejected(self):
        """Single-word relationship synonyms remain rejected (AC#7)."""
        pred = {"pred": "rel", "args": ["Mara", "Jonas"], "value": "together"}
        truth = {"pred": "rel", "args": ["Mara", "Jonas"], "value": "lovers"}
        assert _fluent_matches(pred, truth) is False

    def test_fluent_multiword_low_overlap_rejected(self):
        """Distinct multi-word concepts (Jaccard < 0.5) stay rejected."""
        pred = {"pred": "holds", "args": ["ARIA", "firmware update"], "value": True}
        truth = {"pred": "holds", "args": ["ARIA", "firmware_channel"], "value": True}
        assert _fluent_matches(pred, truth) is False

    # --- _goal_matches seam (L2) ---
    def test_goal_multiword_order_swapped_matches(self):
        """Order-swapped multi-word goal args match via Jaccard (was rejected)."""
        pred = {"pred": "wants", "args": ["Mara", "save city"], "value": True}
        truth = {"pred": "wants", "args": ["Mara", "city save"], "value": True}
        assert _goal_matches(pred, truth) is True

    def test_goal_singleword_synonym_still_rejected(self):
        """Single-word goal synonyms remain rejected (AC#7)."""
        pred = {"pred": "wants", "args": ["Mara", "together"], "value": True}
        truth = {"pred": "wants", "args": ["Mara", "lovers"], "value": True}
        assert _goal_matches(pred, truth) is False
