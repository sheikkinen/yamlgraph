"""FR-995 outsider reader — typed report boundary, derived verdict, ledger.

REQ-YG-660: model text -> Pydantic report; malformed fails closed.
REQ-YG-661: derived verdict = section-3 count <= 2 and no hedge in section 1.
REQ-YG-662: ledger rows only for validated real-PR runs, attributable fields.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / ".github/skills/outsider-view/adapters/outsider_tools.py"
SPIKE_OUT = REPO / "docs/spikes/outsider-reader-2026-09-05/out"


@pytest.fixture(scope="module")
def tools():
    spec = importlib.util.spec_from_file_location("outsider_tools", MODULE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["outsider_tools"] = mod
    spec.loader.exec_module(mod)
    return mod


GOOD = """## 1. In my own words

This change adds a checker that flags unlinked claims for maintainers.

## 2. Could I decide whether to merge this from the description alone?

YES

It states what changed and where.

## 3. Words and references I could not understand

- **“CAP”** · What is a CAP?

## 4. What a merge decision would still need

- [ ] Test results.
"""


@pytest.mark.req("REQ-YG-660")
def test_parse_good_report(tools):
    r = tools.parse_report(GOOD)
    assert r.restatement.startswith("This change adds")
    assert r.model_opinion == "YES"
    assert len(r.section3) == 1 and r.section3[0].quote == "CAP"
    assert len(r.section4) == 1


@pytest.mark.req("REQ-YG-660")
@pytest.mark.parametrize(
    "mutation",
    [
        lambda t: t.replace("## 3. Words", "## 3 Words"),  # malformed heading
        lambda t: t.replace("## 4. What", "## 5. What"),  # missing section 4
        lambda t: t + "\n## 1. In my own words\n\nagain\n",  # duplicate section
        lambda t: (
            t.replace("## 2.", "## X.")
            .replace("## 3.", "## 2.")
            .replace("## X.", "## 3.")
        ),  # reordered
        lambda t: t.replace(
            "## 1. In my own words\n\nThis change adds a checker that flags unlinked claims for maintainers.",
            "## 1. In my own words\n",
        ),  # empty restatement
        lambda t: t.replace("YES\n", "MAYBE\n"),  # opinion not YES/NO
        lambda t: t.replace(
            "- **“CAP”** · What is a CAP?",
            "\n".join(f"- **“T{i}”** · Q{i}?" for i in range(9)),
        ),  # over cap §3
        lambda t: t.replace(
            "- [ ] Test results.", "\n".join(f"- [ ] item {i}" for i in range(11))
        ),  # over cap §4
    ],
)
def test_parse_fails_closed(tools, mutation):
    with pytest.raises(tools.ReportFormatError):
        tools.parse_report(mutation(GOOD))


@pytest.mark.req("REQ-YG-660")
def test_nothing_is_empty_list(tools):
    t = GOOD.replace("- **“CAP”** · What is a CAP?", "nothing").replace(
        "- [ ] Test results.", "Nothing"
    )
    r = tools.parse_report(t)
    assert r.section3 == [] and r.section4 == []


@pytest.mark.req("REQ-YG-661")
def test_derived_yes_requires_low_count_and_no_hedge(tools):
    r = tools.parse_report(GOOD)
    assert tools.derive_verdict(r) == "YES"
    two = GOOD.replace(
        "- **“CAP”** · What is a CAP?", "- **“CAP”** · a?\n- **“REQ”** · b?"
    )
    assert tools.derive_verdict(tools.parse_report(two)) == "YES"
    three = GOOD.replace(
        "- **“CAP”** · What is a CAP?",
        "- **“CAP”** · a?\n- **“REQ”** · b?\n- **“FR”** · c?",
    )
    assert tools.derive_verdict(tools.parse_report(three)) == "NO"


@pytest.mark.req("REQ-YG-661")
@pytest.mark.parametrize(
    "hedge", ["does not say", "Something Called", "NOT STATED", "cannot tell"]
)
def test_derived_no_on_hedge_case_insensitive(tools, hedge):
    t = GOOD.replace("for maintainers.", f"for maintainers; the text {hedge} who.")
    assert tools.derive_verdict(tools.parse_report(t)) == "NO"


@pytest.mark.req("REQ-YG-661")
def test_historical_reports_never_derive_yes(tools):
    reports = sorted(SPIKE_OUT.glob("*.md"))
    assert len(reports) >= 9
    for path in reports:
        text = path.read_text(encoding="utf-8")
        try:
            verdict = tools.derive_verdict(tools.parse_report(text))
        except tools.ReportFormatError:
            verdict = "REJECTED"
        assert verdict != "YES", path.name


@pytest.mark.req("REQ-YG-661")
def test_v2_reports_derive_no_not_rejected(tools):
    # v2-prompt reports (capped) must parse; verdict NO by count or hedge.
    for name in [
        "pr-591-v2-gpt-5.6-sol-20260905T052431Z.md",
        "pr-591-v5-gpt-5.6-sol-20260905T055241Z.md",
    ]:
        r = tools.parse_report((SPIKE_OUT / name).read_text(encoding="utf-8"))
        assert tools.derive_verdict(r) == "NO", name


@pytest.mark.req("REQ-YG-660")
def test_render_front_loads_derived_verdict(tools):
    r = tools.parse_report(GOOD)
    out = tools.render_report(r, "YES", model="gpt-5.6-sol", source="pr-1")
    first = [ln for ln in out.splitlines() if ln.strip()][0]
    assert first.startswith("**Derived verdict:** YES")
    assert "non-authoritative" in out and "## 2." in out


@pytest.mark.req("REQ-YG-660")
def test_rendered_report_round_trips_through_parser(tools):
    r = tools.parse_report(GOOD)
    out = tools.render_report(r, tools.derive_verdict(r), model="m", source="s")
    again = tools.parse_report(out)
    assert again.model_opinion == r.model_opinion
    assert [i.quote for i in again.section3] == [i.quote for i in r.section3]
    assert again.section4 == r.section4
    assert tools.derive_verdict(again) == tools.derive_verdict(r)


@pytest.mark.req("REQ-YG-662")
def test_ledger_row_fields_and_exclusions(tools, tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    row = tools.ledger_row(
        repo="o/r",
        pr=591,
        head_sha="a" * 40,
        input_text="# t\n\nbody",
        model="gpt-5.6-sol",
        prompt_digest="p1",
        tool_sha="deadbeef",
        verdict="NO",
        s3=4,
        s4=6,
        report_path="tmp/x.md",
    )
    for key in [
        "ts",
        "repo",
        "pr",
        "head_sha",
        "input_sha256",
        "model",
        "prompt_digest",
        "tool_sha",
        "derived_verdict",
        "s3_count",
        "s4_count",
        "report_path",
    ]:
        assert key in row, key
    tools.append_ledger(ledger, row, mode="pr")
    tools.append_ledger(ledger, row, mode="selftest")
    tools.append_ledger(ledger, row, mode="dry-run")
    lines = ledger.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["pr"] == 591


@pytest.mark.req("REQ-YG-662")
def test_distinct_pr_count(tools, tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    for pr in [1, 1, 1, 2]:
        row = tools.ledger_row(
            repo="o/r",
            pr=pr,
            head_sha="b" * 40,
            input_text="x",
            model="m",
            prompt_digest="p",
            tool_sha="s",
            verdict="NO",
            s3=1,
            s4=1,
            report_path="r",
        )
        tools.append_ledger(ledger, row, mode="pr")
    assert tools.distinct_pr_count(ledger) == 2
