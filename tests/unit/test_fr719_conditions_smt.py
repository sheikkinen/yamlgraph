"""FR-719 witnesses: SMT-backed condition verification (W803–W805).

The runtime hedges condition gaps silently (`defaulting to END`,
routing.py) — a Commandment 6 violation no syntax check can see, because
gap detection over numeric thresholds needs interval reasoning. Z3
proves gap/overlap/shadowing per guard group and reports concrete
counterexample states.

AC-04 is the load-bearing witness: every counterexample the checker
emits is replayed through the REAL `evaluate_condition` — the encoding
is tested against the runtime, not against itself (Judgement F1: the
pre-judgement encoding mishandled ==/!= None-exemption).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

z3 = pytest.importorskip("z3", reason="verify extra not installed")

from yamlgraph.linter.patterns.conditions_smt import (  # noqa: E402
    check_condition_smt,
)
from yamlgraph.utils.conditions import evaluate_condition  # noqa: E402


def _graph(
    tmp_path: Path, edges_yaml: str, state_keys: list[str] | None = None
) -> Path:
    keys = state_keys or ["score"]
    nodes = "\n".join(
        f"  n{i}:\n    type: llm\n    prompt: p\n    state_key: {k}"
        for i, k in enumerate(keys)
    )
    targets = """
  publish:
    type: llm
    prompt: p
  retry:
    type: llm
    prompt: p
  critique:
    type: llm
    prompt: p
"""
    content = textwrap.dedent(
        f"""
name: fr719-fixture
nodes:
{nodes}
{targets}
edges:
  - {{from: START, to: critique}}
{edges_yaml}
"""
    )
    p = tmp_path / "graph.yaml"
    p.write_text(content)
    return p


def _issues_by_code(issues, code):
    return [i for i in issues if i.code == code]


def _replay_state(issue) -> dict:
    """Parse the counterexample model out of an issue message into a
    state dict for evaluate_condition replay."""
    import re

    state: dict = {}
    for var, val in re.findall(r"(\w[\w.]*) = ([^,;)]+)", issue.message):
        val = val.strip()
        if val == "<missing>":
            continue  # absent from state
        if val in ("True", "False"):
            state[var] = val == "True"
        else:
            try:
                state[var] = float(val)
            except ValueError:
                state[var] = val.strip("'\"")
    return state


class TestW803Gap:
    @pytest.mark.req("REQ-YG-545")
    def test_numeric_gap_yields_counterexample(self, tmp_path):
        """AC-01: the flagship reflexion gap — score in [0.5, 0.8)."""
        g = _graph(
            tmp_path,
            "  - {from: critique, to: publish, condition: 'score >= 0.8'}\n"
            "  - {from: critique, to: retry, condition: 'score < 0.5'}",
        )
        w803 = _issues_by_code(check_condition_smt(g), "W803")
        assert w803, "gap between >= 0.8 and < 0.5 must be found"
        numeric = [i for i in w803 if "<missing>" not in i.message]
        assert numeric, "a numeric counterexample must be reported"
        state = _replay_state(numeric[0])
        assert 0.5 <= state["score"] < 0.8

    @pytest.mark.req("REQ-YG-545")
    def test_none_gap_on_exhaustive_guards(self, tmp_path):
        """AC-02: syntactically exhaustive guards still leak when the
        variable is missing (on_error: skip left it unset)."""
        g = _graph(
            tmp_path,
            "  - {from: critique, to: publish, condition: 'score >= 0.5'}\n"
            "  - {from: critique, to: retry, condition: 'score < 0.5'}",
        )
        w803 = _issues_by_code(check_condition_smt(g), "W803")
        assert any(
            "<missing>" in i.message for i in w803
        ), "missing-variable fallthrough must be reported distinctly"

    @pytest.mark.req("REQ-YG-545")
    def test_null_guard_silences_missing_gap(self, tmp_path):
        """AC-02: `x == null` guard covers the missing case (==/!= are
        None-exempt in the runtime grammar — Judgement F1)."""
        g = _graph(
            tmp_path,
            "  - {from: critique, to: publish, condition: 'score >= 0.5'}\n"
            "  - {from: critique, to: retry, condition: 'score < 0.5'}\n"
            "  - {from: critique, to: retry, condition: 'score == null'}",
        )
        w803 = _issues_by_code(check_condition_smt(g), "W803")
        assert not w803, [i.message for i in w803]

    @pytest.mark.req("REQ-YG-545")
    def test_unconditional_fallback_exempts_gap(self, tmp_path):
        """F3: a group with an unconditional edge cannot gap."""
        g = _graph(
            tmp_path,
            "  - {from: critique, to: publish, condition: 'score >= 0.8'}\n"
            "  - {from: critique, to: retry}",
        )
        assert not _issues_by_code(check_condition_smt(g), "W803")


class TestW804W805:
    @pytest.mark.req("REQ-YG-545")
    def test_overlap_witnessed(self, tmp_path):
        """AC-03: >= 0.5 and >= 0.8 both true at 0.9 — order-dependent."""
        g = _graph(
            tmp_path,
            "  - {from: critique, to: retry, condition: 'score >= 0.5'}\n"
            "  - {from: critique, to: publish, condition: 'score >= 0.8'}\n"
            "  - {from: critique, to: retry, condition: 'score < 0.5'}",
        )
        w804 = _issues_by_code(check_condition_smt(g), "W804")
        assert w804, "overlap must be witnessed"

    @pytest.mark.req("REQ-YG-545")
    def test_shadowed_guard(self, tmp_path):
        """AC-03: a guard unreachable behind earlier guards."""
        g = _graph(
            tmp_path,
            "  - {from: critique, to: publish, condition: 'score >= 0.5'}\n"
            "  - {from: critique, to: retry, condition: 'score < 0.5'}\n"
            "  - {from: critique, to: retry, condition: 'score >= 0.9'}",
        )
        w805 = _issues_by_code(check_condition_smt(g), "W805")
        assert w805, "shadowed guard (>= 0.9 behind >= 0.5) must be flagged"


class TestFaithfulness:
    """AC-04: every emitted counterexample replays true on the runtime."""

    CASES = [
        # (edges, expect_code) — one per F1 encoding-table row
        (
            "  - {from: critique, to: publish, condition: 'score >= 0.8'}\n"
            "  - {from: critique, to: retry, condition: 'score < 0.5'}",
            "W803",
        ),
        (
            # != with missing var: runtime None != 0.5 is TRUE — the
            # corrected encoding row; guards ARE exhaustive incl. missing
            "  - {from: critique, to: publish, condition: 'score != 0.5'}\n"
            "  - {from: critique, to: retry, condition: 'score == 0.5'}",
            None,  # no gap: != catches missing too (None-exempt)
        ),
        (
            "  - {from: critique, to: publish, condition: 'score == 0.5'}\n"
            "  - {from: critique, to: retry, condition: 'score < 0.4'}",
            "W803",
        ),
    ]

    @pytest.mark.req("REQ-YG-545")
    @pytest.mark.parametrize(("edges", "expect"), CASES)
    def test_counterexamples_replay_true(self, tmp_path, edges, expect):
        g = _graph(tmp_path, edges)
        issues = check_condition_smt(g)
        w803 = _issues_by_code(issues, "W803")
        if expect is None:
            assert not w803, [i.message for i in w803]
            return
        assert w803
        conditions = [
            line.split("condition: ")[1].strip("'}").strip()
            for line in edges.splitlines()
        ]
        for issue in w803:
            state = _replay_state(issue)
            assert not any(evaluate_condition(c, state) for c in conditions), (
                f"checker claimed fallthrough at {state} but a guard "
                f"matched at runtime — UNFAITHFUL ENCODING (F1)"
            )


class TestSkipPaths:
    @pytest.mark.req("REQ-YG-545")
    def test_without_z3_single_notice(self, tmp_path, monkeypatch):
        """AC-05: z3 absent → one skip notice, everything else runs."""
        import builtins

        real_import = builtins.__import__

        def no_z3(name, *args, **kwargs):
            if name == "z3":
                raise ImportError("no z3")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", no_z3)
        g = _graph(
            tmp_path,
            "  - {from: critique, to: publish, condition: 'score >= 0.8'}\n"
            "  - {from: critique, to: retry, condition: 'score < 0.5'}",
        )
        issues = check_condition_smt(g)
        infos = [i for i in issues if i.severity == "info"]
        assert len(issues) == len(infos) == 1
        assert "z3" in infos[0].message.lower()

    @pytest.mark.req("REQ-YG-545")
    def test_mixed_sort_skips_group(self, tmp_path):
        """AC-06: number-vs-string on one variable → skip, no verdict."""
        g = _graph(
            tmp_path,
            "  - {from: critique, to: publish, condition: 'score >= 0.8'}\n"
            "  - {from: critique, to: retry, condition: \"score == 'high'\"}",
        )
        issues = check_condition_smt(g)
        assert not _issues_by_code(issues, "W803"), "no verdict on mixed sorts"
        assert any(
            i.severity == "info" and "mixed" in i.message.lower() for i in issues
        )

    @pytest.mark.req("REQ-YG-545")
    def test_unknown_identifier_right_side_is_string(self, tmp_path):
        """AC-09 (F2): unquoted unknown identifier → string literal;
        known state key → variable."""
        # 'high' unquoted, not a state key → literal string; guards over
        # a string sort: == 'high' / != high ... exhaustive incl. missing?
        # != is None-exempt so missing is covered by the != branch.
        g = _graph(
            tmp_path,
            "  - {from: critique, to: publish, condition: 'verdict == high'}\n"
            "  - {from: critique, to: retry, condition: 'verdict != high'}",
            state_keys=["verdict"],
        )
        issues = check_condition_smt(g)
        assert not _issues_by_code(issues, "W803"), [i.message for i in issues]

    @pytest.mark.req("REQ-YG-545")
    def test_var_vs_var_known_keys_encoded(self, tmp_path):
        """AC-09 (F2): `a > b` with both known state keys → gap analysis
        runs (a <= b or either missing falls through)."""
        g = _graph(
            tmp_path,
            "  - {from: critique, to: publish, condition: 'a > b'}",
            state_keys=["a", "b"],
        )
        w803 = _issues_by_code(check_condition_smt(g), "W803")
        assert w803, "a > b alone must gap (a <= b, or missing)"
