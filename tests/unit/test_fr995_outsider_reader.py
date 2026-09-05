"""FR-995 outsider reader — typed report boundary, derived verdict, observation.

REQ-YG-660: model text -> Pydantic report; malformed fails closed.
REQ-YG-661: derived verdict = section-3 count <= 2 and no hedge in section 1.
REQ-YG-662 (FR-1004): every rendered report carries one typed observation
marker (eleven fields, full digests, UTC `Z` timestamp, no `source:`); the
committed ledger and its helpers are gone; only a *posted* comment counts.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

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

MARKER_KEYS = (
    "ts",
    "repo",
    "pr",
    "head",
    "input",
    "model",
    "prompt",
    "tool",
    "verdict",
    "s3",
    "s4",
)


def _obs(tools, **over):
    base = {
        "ts": "2026-09-05T12:11:22Z",
        "repo": "sheikkinen/yamlgraph",
        "pr": 596,
        "head_sha": "1edb9e82" + "0" * 32,
        "input_sha256": "acb34bfc" + "1" * 56,
        "model": "gpt-5.6-sol",
        "prompt_digest": "3f9c2a1b0d4e5f67",
        "tool_sha": "2e67a32a",
        "derived_verdict": "NO",
        "s3": 4,
        "s4": 6,
    }
    base.update(over)
    return tools.Observation(**base)


def _marker_line(text: str) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    assert lines[0].startswith("**Derived verdict:**")
    return lines[1]


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
        lambda t: t.replace(
            "YES\n\nIt states what changed and where.", "YES\n"
        ),  # opinion without reason
        lambda t: t.replace(
            "- **“CAP”** · What is a CAP?", "- **“CAP”**"
        ),  # item without question
        lambda t: t.replace("- [ ] Test results.", "- [ ] "),  # empty §4 item
        lambda t: t.replace(
            "## 3. Words and references I could not understand",
            "## 3. Words and references I could not understand (extra)",
        ),  # heading is not a complete line
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
    # The nine spike reports that predate the positive fixture (AC-07): none derives YES.
    reports = sorted(
        p
        for p in SPIKE_OUT.glob("*.md")
        if not p.name.startswith(("positive-", "selftest-"))
    )
    assert len(reports) >= 9
    for path in reports:
        text = path.read_text(encoding="utf-8")
        try:
            verdict = tools.derive_verdict(tools.parse_report(text))
        except tools.ReportFormatError:
            verdict = "REJECTED"
        assert verdict != "YES", path.name


@pytest.mark.req("REQ-YG-661")
def test_positive_fixture_reports(tools):
    # Same input, two runs: attempt 4 derived NO (5 items), the selftest run derived YES (0 items).
    no_report = SPIKE_OUT / "positive-attempt4-gpt-5.6-sol-20260905T062422Z.md"
    yes_report = SPIKE_OUT / "positive-selftest-gpt-5.6-sol-20260905T062639Z.md"
    assert (
        tools.derive_verdict(tools.parse_report(no_report.read_text(encoding="utf-8")))
        == "NO"
    )
    assert (
        tools.derive_verdict(tools.parse_report(yes_report.read_text(encoding="utf-8")))
        == "YES"
    )


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
    out = tools.render_report(r, _obs(tools, derived_verdict="YES", s3=1, s4=1))
    first = [ln for ln in out.splitlines() if ln.strip()][0]
    assert first.startswith("**Derived verdict:** YES")
    assert "non-authoritative" in out and "## 2." in out


@pytest.mark.req("REQ-YG-660")
def test_rendered_report_round_trips_through_parser(tools):
    r = tools.parse_report(GOOD)
    out = tools.render_report(r, _obs(tools, derived_verdict=tools.derive_verdict(r)))
    again = tools.parse_report(out)
    assert again.model_opinion == r.model_opinion
    assert [i.quote for i in again.section3] == [i.quote for i in r.section3]
    assert again.section4 == r.section4
    assert tools.derive_verdict(again) == tools.derive_verdict(r)


# ----------------------------------------------------------- FR-1004 marker


@pytest.mark.req("REQ-YG-662")
def test_observation_marker_fields_complete_and_unique(tools):
    obs = _obs(tools)
    out = tools.render_report(tools.parse_report(GOOD), obs)
    marker = _marker_line(out)
    assert marker.startswith("<!-- outsider reader | ") and marker.endswith(" -->")
    for key in MARKER_KEYS:
        assert marker.count(f"| {key}: ") == 1, key
    assert "source:" not in out
    assert "/var/folders" not in out and "/tmp/" not in out and "mktemp" not in out
    assert f"| head: {obs.head_sha} |" in marker and len(obs.head_sha) == 40
    assert f"| input: {obs.input_sha256} |" in marker and len(obs.input_sha256) == 64
    assert "| ts: 2026-09-05T12:11:22Z |" in marker
    assert "| repo: sheikkinen/yamlgraph | pr: 596 |" in marker
    assert "| verdict: NO | s3: 4 | s4: 6 -->" in marker
    # exactly one marker in the whole report
    assert out.count("<!-- outsider reader |") == 1


@pytest.mark.req("REQ-YG-662")
def test_observation_round_trips_through_marker(tools):
    obs = _obs(tools)
    out = tools.render_report(tools.parse_report(GOOD), obs)
    assert tools.parse_observation(out) == obs


@pytest.mark.req("REQ-YG-662")
def test_non_pr_reports_use_placeholders(tools):
    obs = _obs(tools, repo="-", pr="-", head_sha="-")
    out = tools.render_report(tools.parse_report(GOOD), obs)
    marker = _marker_line(out)
    assert "| repo: - | pr: - | head: - |" in marker
    again = tools.parse_observation(out)
    assert again == obs and again.pr == "-" and again.head_sha == "-"


@pytest.mark.req("REQ-YG-662")
@pytest.mark.parametrize(
    "bad",
    [
        {"head_sha": "1edb9e82" + "0" * 31},  # 39 hex
        {"head_sha": "g" * 40},  # not hex
        {"input_sha256": "ab" * 31},  # 62 hex
        {"input_sha256": "-"},  # the input digest is never a placeholder
        {"ts": "2026-09-05T12:11:22+00:00"},  # not the Z shape
        {"ts": "2026-09-05 12:11:22Z"},
        {"derived_verdict": "MAYBE"},
        {"s3": -1},
        {"pr": "abc"},
    ],
)
def test_observation_rejects_malformed_fields(tools, bad):
    with pytest.raises(ValidationError):
        _obs(tools, **bad)


@pytest.mark.req("REQ-YG-662")
def test_parse_observation_fails_closed_without_marker(tools):
    with pytest.raises(tools.ReportFormatError):
        tools.parse_observation(GOOD)
    out = tools.render_report(tools.parse_report(GOOD), _obs(tools))
    doubled = out.replace("## 1.", _marker_line(out) + "\n## 1.", 1)
    with pytest.raises(tools.ReportFormatError):
        tools.parse_observation(doubled)


OLD_MARKER_COMMENT = (
    "**Derived verdict:** NO  (rule: ...)\n"
    "<!-- outsider reader | source: /var/folders/x/outsider-abc/input.md"
    " | model: gpt-5.6-sol | 2026-09-05T12:57:34.123456+00:00 -->\n"
    "\n## 1. In my own words\n\nold report\n"
)


@pytest.mark.req("REQ-YG-662")
def test_is_observation_comment_accepts_only_complete_markers(tools):
    """Review #602 P2: the count keys on complete markers, never on prose."""
    new_report = tools.render_report(tools.parse_report(GOOD), _obs(tools))
    assert tools.is_observation_comment(new_report)
    assert tools.is_observation_comment(OLD_MARKER_COMMENT)
    assert not tools.is_observation_comment("The outsider reader said this PR is fine.")
    assert not tools.is_observation_comment("<!-- outsider reader | ts: 2026 -->")
    truncated = new_report.replace(" | s4: 6 -->", " -->")
    assert not tools.is_observation_comment(truncated)
    assert not tools.is_observation_comment(
        "<!-- outsider reader | source: x | model: m -->"
    )  # old marker without its timestamp is not complete


@pytest.mark.req("REQ-YG-662")
def test_distinct_observed_prs_dedups_and_ignores_prose(tools):
    new_report = tools.render_report(tools.parse_report(GOOD), _obs(tools))
    comments = [
        (596, new_report),
        (596, OLD_MARKER_COMMENT),
        (602, new_report),
        (603, "I ran the outsider reader locally; looks good."),
        (604, "<!-- outsider reader | ts: broken -->"),
    ]
    assert tools.distinct_observed_prs(comments) == {596, 602}


@pytest.mark.req("REQ-YG-662")
def test_parse_observation_rejects_duplicate_keys(tools):
    out = tools.render_report(tools.parse_report(GOOD), _obs(tools))
    marker = _marker_line(out)
    doubled_ts = marker.replace("| repo: ", "| ts: 2030-01-01T00:00:00Z | repo: ", 1)
    with pytest.raises(tools.ReportFormatError):
        tools.parse_observation(out.replace(marker, doubled_ts))


@pytest.mark.req("REQ-YG-662")
def test_observation_survives_crlf_comment_bodies(tools):
    """A report written on Windows (or echoed back by GitHub) carries CRLF;
    the marker must still parse and still count (review #602 live reducer)."""
    obs = _obs(tools)
    out = tools.render_report(tools.parse_report(GOOD), obs)
    crlf = out.replace(chr(10), chr(13) + chr(10))
    assert tools.parse_observation(crlf) == obs
    assert tools.is_observation_comment(crlf)
    assert tools.is_observation_comment(
        OLD_MARKER_COMMENT.replace(chr(10), chr(13) + chr(10))
    )


@pytest.mark.req("REQ-YG-662")
def test_ledger_helpers_are_gone(tools):
    for name in ("ledger_row", "append_ledger", "distinct_pr_count"):
        assert not hasattr(tools, name), name
    source = MODULE.read_text(encoding="utf-8")
    assert "ledger" not in source.casefold()


@pytest.mark.req("REQ-YG-662")
def test_finalize_report_builds_observation_from_state(tools, tmp_path):
    src = tmp_path / "input.md"
    src.write_bytes(b"# T\n\nB body\n")
    report = tmp_path / "out" / "report.md"
    result = tools.finalize_report(
        {
            "outsider_result": {"output": GOOD},
            "input_path": str(src),
            "report_path": str(report),
            "model": "gpt-5.6-sol",
            "repo": "o/r",
            "pr": "4242",
            "head_sha": "a" * 40,
            "prompt_digest": "p" * 16,
            "tool_sha": "deadbeef",
        }
    )
    assert result["derived_verdict"] == "YES"
    text = report.read_text(encoding="utf-8")
    obs = tools.parse_observation(text)
    assert obs.repo == "o/r" and obs.pr == 4242 and obs.head_sha == "a" * 40
    assert obs.input_sha256 == hashlib.sha256(src.read_bytes()).hexdigest()
    assert obs.model == "gpt-5.6-sol"
    assert obs.prompt_digest == "p" * 16 and obs.tool_sha == "deadbeef"
    assert obs.derived_verdict == "YES" and obs.s3 == 1 and obs.s4 == 1
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", obs.ts)
    assert "source:" not in text and str(src) not in text


@pytest.mark.req("REQ-YG-662")
def test_finalize_report_placeholders_for_non_pr_state(tools, tmp_path):
    src = tmp_path / "input.md"
    src.write_text("# t\n\nbody", encoding="utf-8")
    report = tmp_path / "report.md"
    tools.finalize_report(
        {
            "outsider_result": {"output": GOOD},
            "input_path": str(src),
            "report_path": str(report),
            "model": "gpt-5.6-sol",
            "repo": "-",
            "pr": "-",
            "head_sha": "-",
            "prompt_digest": "p" * 16,
            "tool_sha": "deadbeef",
        }
    )
    obs = tools.parse_observation(report.read_text(encoding="utf-8"))
    assert (obs.repo, obs.pr, obs.head_sha) == ("-", "-", "-")
