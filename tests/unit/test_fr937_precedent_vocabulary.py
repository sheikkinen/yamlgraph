"""FR-937: the prompts and the validators must mean the same thing.

FR-896 sanctioned ``brief-echo`` as a demotion; FR-938 retired it in the
reducer and replaced it with a bounded ``none-retrieved`` claim. The
replacement never reached the prompts, so the only instruction a persona
holds when it has no precedent is the one that kills the run, and the
accepted escape is unreachable from the prompt.

The same contract is also implemented twice — once in the reducer, once in
the artifact preflight — with opposite precedence, so a cell citing real
identifiers is accepted by one and rejected by the other.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTE = REPO_ROOT / "examples" / "demos" / "research-route"
PROMPTS = ROUTE / "prompts"
# Both librarian prompts are URL-only: `librarian` searches, `librarian_structure`
# shapes what it found. Neither gets an internal honest-miss escape.
LIBRARIAN_PROMPTS = sorted(PROMPTS.glob("librarian*.yaml"))
INTERNAL_PROMPTS = sorted(set(PROMPTS.glob("*.yaml")) - set(LIBRARIAN_PROMPTS))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rt = _load("research_tools_fr937", ROUTE / "nodes" / "research_tools.py")
pf = _load("research_preflight_fr937", REPO_ROOT / "scripts" / "research_preflight.py")


# --- AC-01: the prompts name the accepted marker, not the fatal one --------


@pytest.mark.req("REQ-YG-623")
def test_no_prompt_instructs_the_retired_marker():
    offenders = [
        p.name
        for p in PROMPTS.glob("*.yaml")
        if rt.ECHO_MARKER in p.read_text(encoding="utf-8")
    ]
    assert not offenders, f"prompts still instruct {rt.ECHO_MARKER!r}, which the reducer rejects: {offenders}"


@pytest.mark.req("REQ-YG-623")
def test_internal_personas_are_taught_the_accepted_marker():
    silent = [
        p.name
        for p in INTERNAL_PROMPTS
        if rt.NONE_RETRIEVED not in p.read_text(encoding="utf-8")
    ]
    assert not silent, f"internal personas are never told they may claim {rt.NONE_RETRIEVED!r}: {silent}"


@pytest.mark.req("REQ-YG-623")
@pytest.mark.parametrize("prompt", LIBRARIAN_PROMPTS, ids=lambda p: p.name)
def test_librarian_keeps_its_url_only_contract(prompt):
    """The librarian cites a real URL from tool results; it has no honest miss."""
    text = prompt.read_text(encoding="utf-8")
    assert (
        rt.NONE_RETRIEVED not in text
    ), "librarian must not be offered an internal honest-miss escape"
    assert "URL" in text or "url" in text, "librarian must still require a URL"


# --- AC-02: anti-drift — edit either half alone and this fails -------------


@pytest.mark.req("REQ-YG-623")
def test_marker_tokens_agree_across_both_validators():
    assert rt.ECHO_MARKER == pf.ECHO_MARKER
    assert rt.NONE_RETRIEVED == pf.NONE_RETRIEVED


@pytest.mark.req("REQ-YG-623")
def test_prompt_marker_is_the_code_constant_verbatim():
    """Not extraction: the exact token, so renaming either side breaks this."""
    for prompt in INTERNAL_PROMPTS:
        text = prompt.read_text(encoding="utf-8")
        assert rt.NONE_RETRIEVED in text, prompt.name


# --- AC-03/AC-04/AC-05: one truth table, two validators -------------------

# Verbatim cells from feature-requests/FR-937-evidence.md.
W3_CELL = (
    "FR-896 (precedent traceability), FR-932 (none-retrieved bounded claim), "
    "CAP-248 (research sole route)."
)
W6_CELL = (
    "FR-890 research-route graph; CAP-248 research sole route (closed-input "
    "alternatives); brief-echo: planning phase must gain input closure "
    "comparable to judge/review/author routes."
)

# (label, cell, prior_art_empty, accepted)
TRUTH_TABLE = [
    ("w3-committed-ids-mentioning-none-retrieved", W3_CELL, False, True),
    ("w6-committed-ids-followed-by-echo-marker", W6_CELL, False, True),
    ("bare-none-retrieved-with-empty-retrieval", "none-retrieved", True, True),
    ("bare-none-retrieved-with-hits", "none-retrieved", False, False),
    ("echo-marker-claim", "brief-echo: the brief says so", False, False),
    ("prose-only", "this seems like a good idea generally", False, False),
]


def _reducer_accepts(cell: str, prior_art_empty: bool) -> bool:
    try:
        rt._classify_precedent(cell, REPO_ROOT, prior_art_empty)
    except ValueError:
        return False
    return True


def _preflight_accepts(cell: str, prior_art_empty: bool) -> bool:
    return not pf._check_precedent(cell, prior_art_empty)


@pytest.mark.req("REQ-YG-623")
@pytest.mark.parametrize(("label", "cell", "empty", "accepted"), TRUTH_TABLE)
def test_reducer_matches_the_truth_table(label, cell, empty, accepted):
    assert _reducer_accepts(cell, empty) is accepted, label


@pytest.mark.req("REQ-YG-623")
@pytest.mark.parametrize(("label", "cell", "empty", "accepted"), TRUTH_TABLE)
def test_preflight_matches_the_truth_table(label, cell, empty, accepted):
    assert _preflight_accepts(cell, empty) is accepted, label


@pytest.mark.req("REQ-YG-623")
@pytest.mark.parametrize(("label", "cell", "empty", "_accepted"), TRUTH_TABLE)
def test_both_validators_agree(label, cell, empty, _accepted):
    assert _reducer_accepts(cell, empty) == _preflight_accepts(cell, empty), label


@pytest.mark.req("REQ-YG-623")
def test_reducer_alone_enforces_filesystem_existence():
    """Intended asymmetry: a shape check is not proof the identifier exists."""
    fabricated = "FR-99999 (a number nothing has ever claimed)"
    assert _preflight_accepts(fabricated, False) is True
    assert _reducer_accepts(fabricated, False) is False


# --- AC-09: a classification is claimed, not mentioned --------------------


def _classification_violations(body: str) -> list[str]:
    brief = "\n".join(
        [
            "## Problem statement",
            "Something is wrong and it recurs.",
            "",
            "## Classification",
            body,
            "",
            "## Constraints",
            "- must not change the schema",
            "",
            "## Witnessed incidents",
            "- 2026-08-31: it happened.",
            "",
        ]
    )
    return [v for v in pf.check_brief(brief) if "classification" in v.lower()]


@pytest.mark.req("REQ-YG-623")
def test_classification_claim_survives_prose_that_disclaims_another_class():
    body = "judgement/analysis/generation — nothing here needs measurement."
    assert not _classification_violations(body)


@pytest.mark.req("REQ-YG-623")
def test_two_classes_in_the_claim_position_still_fail():
    body = "judgement/analysis/generation measurement"
    assert _classification_violations(body)


@pytest.mark.req("REQ-YG-623")
def test_no_class_still_fails():
    assert _classification_violations("undecided for now")


# --- AC-10: the wrapper reports the fault it was given --------------------


@pytest.mark.req("REQ-YG-623")
@pytest.mark.slow
def test_wrapper_reports_the_missing_heading_it_was_given(tmp_path):
    brief = tmp_path / "missing-heading-brief.md"
    brief.write_text(
        "## Problem statement\nSomething recurs.\n\n"
        "## Classification\nenforcement/latency-critical\n\n"
        "## Constraints\n- none\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [str(REPO_ROOT / "scripts" / "research.sh"), str(brief)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 64, combined
    assert "missing or empty required heading" in combined, combined
    assert "remove solution-shaped sections" not in combined, combined
