"""FR-1027 Recap Pull-Request Axis — unit tests (LLM-free, network-free).

The axis is code-owned end to end: remote parsing, exact-epoch window
membership, one bounded ``gh`` invocation, stable ordering, line assembly,
and the available / unavailable / cap-reached distinction. Nothing here
touches the network — every ``gh`` and ``git`` call is a recorded fake, so
the argv itself is the assertion (R-2, R-3).

Judgement gates witnessed here: C-4 (axis never enters the prompt), C-5 (no
broad handler, no silent fallback, no fabricated empty-success), C-6 (the cap
qualifies the whole axis).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import weekly_recap  # noqa: E402

from examples.demos.recap.nodes import prs  # noqa: E402
from examples.demos.recap.nodes.partition import finalize_recap  # noqa: E402

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEMO_DIR = REPO_ROOT / "examples" / "demos" / "recap"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "fr1027_gh_pr_list.json"

# Window: 2026-09-01T00:00:00Z. Collection clock: 2026-09-07T12:00:00Z.
EPOCH = int(datetime(2026, 9, 1, tzinfo=UTC).timestamp())
NOW = int(datetime(2026, 9, 7, 12, 0, tzinfo=UTC).timestamp())

EXPECTED_MERGED = [
    "#636|2026-09-06→2026-09-07|0d|chore(research): FR-1026 retire the provenance ledger — the judge is the check, once",
    "#635|2026-09-07→2026-09-07|0d|docs(fr): FR-1023 review round sentinel — plan, research record, judgement",
    "#633|2026-09-06→2026-09-07|0d|feat(judge): FR-1022 round sentinel — third judgement is fixed text, not a model call",
]
EXPECTED_CLOSED = [
    "#627|2026-09-06→2026-09-06|0d|docs(doctrine): FR-1013 doctrine and reference sweep after Chaplain removal",
]
EXPECTED_OPEN = [
    "#641|2026-09-05→open|2d|docs(fr): FR-1027 recap pull-request axis",
    "#640|2026-06-01→open|98d|docs(plan): long-running spike kept open on purpose",
]


def fixture_rows() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class Recorder:
    """Fake ``subprocess.run`` recording argv, capturing kwargs, replying by program."""

    def __init__(self, replies: dict[str, object]) -> None:
        self.replies = replies
        self.calls: list[dict] = []

    def __call__(self, argv, **kwargs):  # noqa: ANN001, ANN003
        self.calls.append({"argv": list(argv), "kwargs": kwargs})
        program = Path(str(argv[0])).stem
        reply = self.replies.get(program)
        if isinstance(reply, Exception):
            raise reply
        if callable(reply):
            reply = reply(list(argv))
        if reply is None:
            raise AssertionError(f"no fake reply configured for {program}: {argv}")
        return subprocess.CompletedProcess(list(argv), 0, stdout=reply, stderr="")

    def programs(self) -> list[str]:
        return [Path(str(c["argv"][0])).stem for c in self.calls]

    def argv_for(self, program: str) -> list[str]:
        for call in self.calls:
            if Path(str(call["argv"][0])).stem == program:
                return call["argv"]
        raise AssertionError(f"{program} was never invoked")


def git_replies(origin: str, epoch: int = EPOCH):  # noqa: ANN201
    def reply(argv: list[str]) -> str:
        if "remote" in argv:
            if not origin:
                raise subprocess.CalledProcessError(
                    2, argv, output="", stderr="error: No such remote 'origin'\n"
                )
            return origin + "\n"
        if "rev-parse" in argv:
            return f"--max-age={epoch}\n"
        raise AssertionError(f"unexpected git argv: {argv}")

    return reply


def run_collect(
    monkeypatch, origin: str, gh_reply, now: int = NOW
) -> tuple[dict, Recorder]:  # noqa: ANN001
    rec = Recorder({"git": git_replies(origin), "gh": gh_reply})
    monkeypatch.setattr(prs.subprocess, "run", rec)
    monkeypatch.setattr(prs, "_now_epoch", lambda: now)
    result = prs.collect_prs({"repo_path": ".", "since": "1 week ago"})
    return result["pr_axis"], rec


class TestOriginParsing:
    """AC-04 / R-3: three remote families, and every rejection is silent about gh."""

    @pytest.mark.req("REQ-YG-669")
    @pytest.mark.parametrize(
        "url",
        [
            "https://github.com/sheikkinen/yamlgraph",
            "https://github.com/sheikkinen/yamlgraph.git",
            "git@github.com:sheikkinen/yamlgraph",
            "git@github.com:sheikkinen/yamlgraph.git",
            "ssh://git@github.com/sheikkinen/yamlgraph",
            "ssh://git@github.com/sheikkinen/yamlgraph.git",
        ],
    )
    def test_accepted_remote_families(self, url: str) -> None:
        slug, reason = prs.parse_origin(url)
        assert slug == "sheikkinen/yamlgraph", url
        assert reason == ""

    @pytest.mark.req("REQ-YG-669")
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://gitlab.com/o/n.git", "origin host is gitlab.com, not github.com"),
            (
                "git@bitbucket.org:o/n.git",
                "origin host is bitbucket.org, not github.com",
            ),
            ("/srv/git/mirror.git", "origin is a local path remote"),
            ("C:/src/yamlgraph", "origin is a local path remote"),
            ("file:///srv/git/mirror.git", "origin is a local path remote"),
            ("https://github.com/onlyowner", "origin URL is malformed (no owner/name)"),
            ("https://github.com/", "origin URL is malformed (no owner/name)"),
        ],
    )
    def test_rejected_remotes_carry_stable_reasons(
        self, url: str, expected: str
    ) -> None:
        slug, reason = prs.parse_origin(url)
        assert slug is None
        assert reason == expected

    @pytest.mark.req("REQ-YG-669")
    def test_absent_origin_is_unavailable_and_never_calls_gh(self, monkeypatch) -> None:  # noqa: ANN001
        """AC-14: a repository with no origin makes no gh call at all."""
        axis, rec = run_collect(monkeypatch, "", gh_reply=None)
        assert axis["available"] is False
        assert axis["reason"] == "no origin remote"
        assert "gh" not in rec.programs()
        assert (axis["merged"], axis["closed_unmerged"], axis["open"]) == ([], [], [])

    @pytest.mark.req("REQ-YG-669")
    def test_non_github_origin_never_calls_gh(self, monkeypatch) -> None:  # noqa: ANN001
        axis, rec = run_collect(
            monkeypatch, "https://gitlab.com/o/n.git", gh_reply=None
        )
        assert axis["available"] is False
        assert "gitlab.com" in axis["reason"]
        assert "gh" not in rec.programs()

    @pytest.mark.req("REQ-YG-669")
    def test_non_repository_stays_loud(self, monkeypatch) -> None:  # noqa: ANN001
        """A path that is not a git repository raises — it is not 'no origin'."""
        rec = Recorder(
            {
                "git": subprocess.CalledProcessError(
                    128, ["git"], output="", stderr="fatal: not a git repository\n"
                )
            }
        )
        monkeypatch.setattr(prs.subprocess, "run", rec)
        with pytest.raises(subprocess.CalledProcessError):
            prs.collect_prs({"repo_path": "/nowhere", "since": "1 week ago"})


class TestWindowIsExactEpoch:
    """AC-05 / R-1: the epoch decides membership; the date is only printed."""

    @pytest.mark.req("REQ-YG-669")
    def test_parse_max_age(self) -> None:
        assert prs.parse_max_age("--max-age=1788186184\n") == 1788186184

    @pytest.mark.req("REQ-YG-669")
    @pytest.mark.parametrize("bad", ["", "1788186184", "--min-age=17", "--max-age=x"])
    def test_parse_max_age_rejects_unexpected_shapes(self, bad: str) -> None:
        with pytest.raises(ValueError):
            prs.parse_max_age(bad)

    @pytest.mark.req("REQ-YG-669")
    def test_since_is_one_argv_element(self, monkeypatch) -> None:  # noqa: ANN001
        _, rec = run_collect(
            monkeypatch, "https://github.com/o/n.git", gh_reply=lambda argv: "[]"
        )
        argv = [c["argv"] for c in rec.calls if "rev-parse" in c["argv"]][0]
        assert "--since=1 week ago" in argv
        assert "1 week ago" not in argv  # never split into its own element

    @pytest.mark.req("REQ-YG-669")
    def test_midnight_truncation_cannot_move_a_row(self) -> None:
        """A row merged 09:00 with a 12:00 boundary is out, though the dates match."""
        boundary = int(datetime(2026, 9, 1, 12, 0, tzinfo=UTC).timestamp())
        rows = [
            {
                "number": 1,
                "title": "before the boundary, same calendar day",
                "state": "MERGED",
                "createdAt": "2026-08-31T09:00:00Z",
                "mergedAt": "2026-09-01T09:00:00Z",
                "closedAt": "2026-09-01T09:00:00Z",
            },
            {
                "number": 2,
                "title": "on the boundary exactly",
                "state": "MERGED",
                "createdAt": "2026-08-31T09:00:00Z",
                "mergedAt": "2026-09-01T12:00:00Z",
                "closedAt": "2026-09-01T12:00:00Z",
            },
        ]
        buckets = prs.bucket_prs(rows, boundary, NOW)
        assert [line.split("|")[0] for line in buckets["merged"]] == ["#2"]


class TestBucketingAndFormat:
    """AC-06 / AC-07: scrambled fixture in, exact ordered lines out."""

    @pytest.mark.req("REQ-YG-669")
    def test_fixture_is_scrambled(self) -> None:
        numbers = [row["number"] for row in fixture_rows()]
        assert numbers != sorted(numbers, reverse=True), (
            "fixture must not be pre-sorted"
        )

    @pytest.mark.req("REQ-YG-669")
    def test_exact_buckets_and_order(self) -> None:
        buckets = prs.bucket_prs(fixture_rows(), EPOCH, NOW)
        assert buckets["merged"] == EXPECTED_MERGED
        assert buckets["closed_unmerged"] == EXPECTED_CLOSED
        assert buckets["open"] == EXPECTED_OPEN

    @pytest.mark.req("REQ-YG-669")
    def test_before_window_rows_are_dropped(self) -> None:
        buckets = prs.bucket_prs(fixture_rows(), EPOCH, NOW)
        every = buckets["merged"] + buckets["closed_unmerged"] + buckets["open"]
        assert not [line for line in every if line.startswith(("#610|", "#500|"))]

    @pytest.mark.req("REQ-YG-669")
    def test_open_row_older_than_window_is_kept(self) -> None:
        """Staleness is the point: an open PR is never filtered by age."""
        buckets = prs.bucket_prs(fixture_rows(), EPOCH, NOW)
        assert buckets["open"][-1].startswith("#640|2026-06-01→open|98d|")

    @pytest.mark.req("REQ-YG-669")
    def test_tie_on_decision_timestamp_breaks_by_number_descending(self) -> None:
        buckets = prs.bucket_prs(fixture_rows(), EPOCH, NOW)
        assert buckets["merged"][0].startswith("#636|")
        assert buckets["merged"][1].startswith("#635|")

    @pytest.mark.req("REQ-YG-669")
    def test_title_bytes_survive_verbatim(self) -> None:
        buckets = prs.bucket_prs(fixture_rows(), EPOCH, NOW)
        titles = {row["number"]: row["title"] for row in fixture_rows()}
        for line in buckets["merged"] + buckets["closed_unmerged"] + buckets["open"]:
            number = int(line.split("|")[0].lstrip("#"))
            assert line.split("|", 3)[3] == titles[number]


class TestGhBoundary:
    """AC-08 / AC-09 / R-2: one bounded invocation, four narrow failures."""

    @pytest.mark.req("REQ-YG-669")
    def test_exactly_one_gh_invocation_with_fixed_argv(self, monkeypatch) -> None:  # noqa: ANN001
        axis, rec = run_collect(
            monkeypatch,
            "https://github.com/sheikkinen/yamlgraph.git",
            gh_reply=lambda argv: json.dumps(fixture_rows()),
        )
        assert rec.programs().count("gh") == 1
        argv = rec.argv_for("gh")
        assert argv[1:] == [
            "pr",
            "list",
            "--repo",
            "sheikkinen/yamlgraph",
            "--state",
            "all",
            "--limit",
            str(prs.PR_LIMIT),
            "--json",
            "number,title,state,createdAt,mergedAt,closedAt",
        ]
        kwargs = [
            c["kwargs"] for c in rec.calls if Path(str(c["argv"][0])).stem == "gh"
        ][0]
        assert kwargs.get("shell", False) is False
        assert kwargs.get("timeout") == prs.GH_TIMEOUT == 60
        assert axis["available"] is True

    @pytest.mark.req("REQ-YG-669")
    def test_crafted_remote_cannot_split_argv(self, monkeypatch) -> None:  # noqa: ANN001
        """A slug-shaped injection stays one argv element or is refused outright."""
        crafted = "https://github.com/o/n --limit 1 --json number"
        slug, reason = prs.parse_origin(crafted)
        assert slug is None and reason == "origin URL is malformed (no owner/name)"
        axis, rec = run_collect(monkeypatch, crafted, gh_reply=None)
        assert axis["available"] is False
        assert "gh" not in rec.programs()

    @pytest.mark.req("REQ-YG-669")
    @pytest.mark.parametrize(
        ("failure", "expected"),
        [
            (FileNotFoundError("gh"), "gh not found on PATH"),
            (
                subprocess.TimeoutExpired(["gh"], 60),
                "gh timed out after 60s",
            ),
            (
                subprocess.CalledProcessError(
                    4, ["gh"], output="", stderr="gh: Bad credentials\nmore\n"
                ),
                "gh exited 4: gh: Bad credentials",
            ),
            (
                subprocess.CalledProcessError(1, ["gh"], output="", stderr="   \n"),
                "gh exited 1 with no stderr",
            ),
        ],
    )
    def test_narrow_failures_are_unavailable_with_stable_reasons(
        self, monkeypatch, failure: Exception, expected: str
    ) -> None:  # noqa: ANN001
        axis, _ = run_collect(
            monkeypatch, "https://github.com/o/n.git", gh_reply=failure
        )
        assert axis["available"] is False
        assert axis["reason"] == expected
        assert (axis["merged"], axis["closed_unmerged"], axis["open"]) == ([], [], [])

    @pytest.mark.req("REQ-YG-669")
    def test_unparseable_json_is_unavailable(self, monkeypatch) -> None:  # noqa: ANN001
        axis, _ = run_collect(
            monkeypatch, "https://github.com/o/n.git", gh_reply=lambda argv: "not json"
        )
        assert axis["available"] is False
        assert axis["reason"] == "gh returned unparseable JSON"

    @pytest.mark.req("REQ-YG-669")
    def test_missing_required_field_names_the_field(self, monkeypatch) -> None:  # noqa: ANN001
        row = dict(fixture_rows()[1])
        del row["mergedAt"]
        axis, _ = run_collect(
            monkeypatch,
            "https://github.com/o/n.git",
            gh_reply=lambda argv: json.dumps([row]),
        )
        assert axis["available"] is False
        assert axis["reason"] == "gh row missing required field mergedAt"

    @pytest.mark.req("REQ-YG-669")
    def test_no_broad_handler_unexpected_error_propagates(self, monkeypatch) -> None:  # noqa: ANN001
        """C-5: only the four named classes are absorbed."""
        axis_error = MemoryError("out of memory mid-collection")
        rec = Recorder(
            {"git": git_replies("https://github.com/o/n.git"), "gh": axis_error}
        )
        monkeypatch.setattr(prs.subprocess, "run", rec)
        with pytest.raises(MemoryError):
            prs.collect_prs({"repo_path": ".", "since": "1 week ago"})


class TestAvailabilityAndCap:
    """AC-10 / AC-11 / C-6: empty is not unreachable, and the cap is a claim about the page."""

    @pytest.mark.req("REQ-YG-669")
    def test_zero_rows_is_available_and_empty(self, monkeypatch) -> None:  # noqa: ANN001
        axis, _ = run_collect(
            monkeypatch, "https://github.com/o/n.git", gh_reply=lambda argv: "[]"
        )
        assert axis["available"] is True
        assert axis["reason"] == ""
        assert axis["cap_reached"] is False
        assert (axis["merged"], axis["closed_unmerged"], axis["open"]) == ([], [], [])

    @pytest.mark.req("REQ-YG-669")
    def test_cap_reached_at_limit(self, monkeypatch) -> None:  # noqa: ANN001
        rows = [
            {
                "number": n,
                "title": f"row {n}",
                "state": "OPEN",
                "createdAt": "2026-09-05T00:00:00Z",
                "mergedAt": None,
                "closedAt": None,
            }
            for n in range(prs.PR_LIMIT)
        ]
        axis, _ = run_collect(
            monkeypatch,
            "https://github.com/o/n.git",
            gh_reply=lambda argv: json.dumps(rows),
        )
        assert axis["cap_reached"] is True
        assert axis["available"] is True
        assert len(axis["open"]) == prs.PR_LIMIT

    @pytest.mark.req("REQ-YG-669")
    def test_one_below_cap_is_not_cap_reached(self, monkeypatch) -> None:  # noqa: ANN001
        rows = [
            {
                "number": n,
                "title": f"row {n}",
                "state": "OPEN",
                "createdAt": "2026-09-05T00:00:00Z",
                "mergedAt": None,
                "closedAt": None,
            }
            for n in range(prs.PR_LIMIT - 1)
        ]
        axis, _ = run_collect(
            monkeypatch,
            "https://github.com/o/n.git",
            gh_reply=lambda argv: json.dumps(rows),
        )
        assert axis["cap_reached"] is False


class TestAxisNote:
    """AC-11 / AC-13 / R-4: the note is composed in code and never overstates."""

    @pytest.mark.req("REQ-YG-669")
    def test_clean_axis_has_no_note(self) -> None:
        assert (
            prs.axis_note({"available": True, "reason": "", "cap_reached": False}) == ""
        )

    @pytest.mark.req("REQ-YG-669")
    def test_unavailable_note_carries_the_reason(self) -> None:
        note = prs.axis_note(
            {"available": False, "reason": "no origin remote", "cap_reached": False}
        )
        assert note == "pull-request axis unavailable: no origin remote"

    @pytest.mark.req("REQ-YG-669")
    def test_cap_note_says_may_be_truncated_not_is(self) -> None:
        note = prs.axis_note({"available": True, "reason": "", "cap_reached": True})
        assert note == "pull-request cap of 300 reached; results may be truncated"
        assert "is truncated" not in note

    @pytest.mark.req("REQ-YG-669")
    def test_both_clauses_when_both_hold(self) -> None:
        note = prs.axis_note(
            {
                "available": False,
                "reason": "gh timed out after 60s",
                "cap_reached": True,
            }
        )
        assert "unavailable: gh timed out after 60s" in note
        assert "may be truncated" in note


class TestFinalizeAttachesAxis:
    """AC-12: the post-pass attaches the axis and disturbs nothing else."""

    BASE_STATE = {
        "commits": "abc1234|2026-09-06|feat: FR-1027 axis",
        "referenced": "abc1234|2026-09-06|feat: FR-1027 axis",
        "unreferenced": "def5678|2026-09-06|chore: tidy",
        "churn": "1\t0\tprs.py",
        "fr_changes": "feature-requests/FR-1027-recap-pull-request-axis.md",
        "fragments": "changelog/unreleased/fr-1027.md",
        "fr_statuses": "HEAD:feature-requests/FR-1027-recap-pull-request-axis.md:**Status:** Judged",
        "recap": {"workstreams": ["FR-1027 axis (commits: 1)"], "hotspots": []},
    }

    def _finalize(self, axis: dict) -> dict:
        return finalize_recap({**self.BASE_STATE, "pr_axis": axis})["recap"]

    @pytest.mark.req("REQ-YG-669")
    def test_buckets_and_note_are_attached(self) -> None:
        recap = self._finalize(
            {
                "available": True,
                "reason": "",
                "cap_reached": False,
                "merged": EXPECTED_MERGED,
                "closed_unmerged": EXPECTED_CLOSED,
                "open": EXPECTED_OPEN,
            }
        )
        assert recap["pr_merged"] == EXPECTED_MERGED
        assert recap["pr_closed_unmerged"] == EXPECTED_CLOSED
        assert recap["pr_open"] == EXPECTED_OPEN
        assert recap["pr_axis_note"] == ""

    @pytest.mark.req("REQ-YG-669")
    def test_inherited_fields_are_untouched(self) -> None:
        recap = self._finalize(
            {
                "available": False,
                "reason": "no origin remote",
                "cap_reached": False,
                "merged": [],
                "closed_unmerged": [],
                "open": [],
            }
        )
        assert recap["workstreams"] == ["FR-1027 axis (commits: 1) [Status: Judged]"]
        assert recap["orphans"] == ["def5678|2026-09-06|chore: tidy"]
        assert recap["hotspots"] == []
        assert recap["unverified_refs"] == []
        assert (
            recap["pr_axis_note"] == "pull-request axis unavailable: no origin remote"
        )

    @pytest.mark.req("REQ-YG-669")
    def test_absent_axis_state_renders_as_unavailable_not_as_empty(self) -> None:
        """A graph run without the node must not claim an observation."""
        recap = finalize_recap(dict(self.BASE_STATE))["recap"]
        assert recap["pr_merged"] == []
        assert recap["pr_axis_note"].startswith("pull-request axis unavailable:")


class TestRendererSections:
    """AC-13: exact output for available-empty, unavailable, and cap-reached."""

    BASE = {
        "workstreams": ["FR-1027 axis (commits: 1) [Status: Judged]"],
        "orphans": [],
        "hotspots": [],
    }

    @pytest.mark.req("REQ-YG-669")
    def test_existing_sections_keep_heading_and_order(self) -> None:
        out = weekly_recap.render_markdown(
            {
                **self.BASE,
                "pr_merged": [],
                "pr_closed_unmerged": [],
                "pr_open": [],
                "pr_axis_note": "",
            },
            "2026-W37",
        )
        headings = [line for line in out.splitlines() if line.startswith("## ")]
        assert headings[:3] == ["## Workstreams", "## Orphans", "## Hotspots"]
        assert headings[3:] == [
            "## Pull requests merged",
            "## Pull requests closed unmerged",
            "## Pull requests open",
        ]

    @pytest.mark.req("REQ-YG-669")
    def test_available_empty_renders_none(self) -> None:
        out = weekly_recap.render_markdown(
            {
                **self.BASE,
                "pr_merged": [],
                "pr_closed_unmerged": [],
                "pr_open": [],
                "pr_axis_note": "",
            },
            "2026-W37",
        )
        section = out.split("## Pull requests merged\n\n")[1].splitlines()[0]
        assert section == "(none)"
        assert "pull-request axis" not in out

    @pytest.mark.req("REQ-YG-669")
    def test_unavailable_renders_one_note_then_not_collected(self) -> None:
        note = "pull-request axis unavailable: no origin remote"
        out = weekly_recap.render_markdown(
            {
                **self.BASE,
                "pr_merged": [],
                "pr_closed_unmerged": [],
                "pr_open": [],
                "pr_axis_note": note,
            },
            "2026-W37",
        )
        assert out.count(note) == 1
        assert out.index(note) < out.index("## Pull requests merged")
        assert out.count("(not collected)") == 3
        assert "(none)" not in out.split("## Pull requests merged")[1]

    @pytest.mark.req("REQ-YG-669")
    def test_cap_note_survives_non_empty_buckets(self) -> None:
        """R-4: the warning cannot be suppressed by rows being present."""
        note = "pull-request cap of 300 reached; results may be truncated"
        out = weekly_recap.render_markdown(
            {
                **self.BASE,
                "pr_merged": EXPECTED_MERGED,
                "pr_closed_unmerged": [],
                "pr_open": EXPECTED_OPEN,
                "pr_axis_note": note,
            },
            "2026-W37",
        )
        assert out.count(note) == 1
        assert out.index(note) < out.index("## Pull requests merged")
        for line in EXPECTED_MERGED:
            assert f"- {line}" in out
        empty = out.split("## Pull requests closed unmerged\n\n")[1].splitlines()[0]
        assert empty == "(none)", "cap reached is not the same as not collected"


class TestGraphAndPromptShape:
    """AC-01 / AC-02 / AC-03 / C-4: the axis is invisible to the model."""

    @pytest.mark.req("REQ-YG-669")
    def test_graph_declares_the_axis_node_and_state(self) -> None:
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        assert raw["state"]["pr_axis"] == "dict"
        assert raw["nodes"]["get_prs"]["type"] == "python"
        tool = raw["tools"][raw["nodes"]["get_prs"]["tool"]]
        assert tool["type"] == "python"
        assert tool["function"] == "collect_prs"
        assert tool["module"].endswith("recap.nodes.prs")

    @pytest.mark.req("REQ-YG-669")
    def test_still_exactly_one_llm_node(self) -> None:
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        llm = [n for n, c in raw["nodes"].items() if c.get("type") == "llm"]
        assert llm == ["synthesize"]

    @pytest.mark.req("REQ-YG-669")
    def test_get_prs_is_reachable_before_finalize(self) -> None:
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        order: dict[str, str] = {e["from"]: e["to"] for e in raw["edges"]}
        node, seen = "START", []
        while node != "END":
            node = order[node]
            seen.append(node)
        assert "get_prs" in seen
        assert seen.index("get_prs") < seen.index("finalize_recap")

    @pytest.mark.req("REQ-YG-669")
    def test_prompt_carries_no_pull_request_input(self) -> None:
        text = (DEMO_DIR / "prompts" / "recap.yaml").read_text(encoding="utf-8")
        prompt = yaml.safe_load(text)
        assert set(prompt["schema"]["fields"]) == {"workstreams", "hotspots"}
        for token in ("pr_axis", "pr_merged", "pr_open", "pr_closed_unmerged", "gh "):
            assert token not in text, f"model must not see {token!r}"

    @pytest.mark.req("REQ-YG-669")
    def test_synthesize_variables_exclude_the_axis(self) -> None:
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        variables = raw["nodes"]["synthesize"]["variables"]
        assert not [k for k in variables if k.startswith("pr_")]

    @pytest.mark.req("REQ-YG-669")
    def test_shell_tools_are_still_all_portable_git(self) -> None:
        raw = yaml.safe_load((DEMO_DIR / "graph.yaml").read_text(encoding="utf-8"))
        for tool in raw["tools"].values():
            if tool.get("type") == "shell":
                assert "git -C {repo_path}" in tool["command"]
                assert "gh " not in tool["command"]


class TestWorkflowWiring:
    """AC-16 / C-3: the existing secret, scoped to the one step that needs it."""

    @pytest.mark.req("REQ-YG-669")
    def test_recap_step_receives_gh_token(self) -> None:
        wf = yaml.safe_load(
            (REPO_ROOT / ".github" / "workflows" / "weekly-recap.yml").read_text(
                encoding="utf-8"
            )
        )
        steps = wf["jobs"]["recap"]["steps"]
        recap_step = [s for s in steps if s.get("id") == "recap"][0]
        expected = "${{ secrets.RECAP_PAT }}"  # the existing secret, no new one
        assert recap_step["env"]["GH_TOKEN"] == expected

    @pytest.mark.req("REQ-YG-669")
    def test_no_new_secret_and_no_new_permission(self) -> None:
        text = (REPO_ROOT / ".github" / "workflows" / "weekly-recap.yml").read_text(
            encoding="utf-8"
        )
        wf = yaml.safe_load(text)
        assert wf["permissions"] == {"contents": "write", "pull-requests": "write"}
        secrets = set(__import__("re").findall(r"secrets\.([A-Z_]+)", text))
        assert secrets == {"RECAP_PAT", "ANTHROPIC_API_KEY"}


class TestWitness:
    """AC-15 / R-5: the real run is a named file with a mechanically checked line."""

    WITNESS = REPO_ROOT / "feature-requests" / "FR-1027.witness.md"

    @pytest.mark.req("REQ-YG-669")
    def test_witness_records_its_provenance(self) -> None:
        text = self.WITNESS.read_text(encoding="utf-8")
        for field in (
            "**Run date:**",
            "**Repository:**",
            "**since:**",
            "**Collection timestamp:**",
            "**Cap reached:**",
        ):
            assert field in text, f"witness missing {field}"

    @pytest.mark.req("REQ-YG-669")
    def test_witness_shows_the_pull_request_git_cannot_see(self) -> None:
        """#627 was closed unmerged; no commit of it reached main."""
        section = self.WITNESS.read_text(encoding="utf-8").split(
            "## Pull requests closed unmerged"
        )[1]
        lines = [
            line.lstrip("- ").strip()
            for line in section.splitlines()
            if line.startswith("- ")
        ]
        assert [line for line in lines if line.startswith("#627|")], lines


class TestSinceGrammarIsGitsOwn:
    """Enforcement deviation, recorded: git's date parser degrades silently.

    ``git rev-parse --since="not a date"`` returns the current epoch with exit
    0 — as does ``git log --since="not a date"``, which the five pre-existing
    collection tools already use. The axis inherits that behaviour rather than
    diverging from the rest of the graph; see the FR's Implementation Record.
    """

    @pytest.mark.req("REQ-YG-669")
    def test_axis_uses_the_same_parser_as_the_existing_collection(self) -> None:
        argv = prs.rev_parse_argv(".", "not a date")
        assert Path(argv[0]).stem == "git"  # resolved executable, not a shell string
        assert argv[1:] == ["-C", ".", "rev-parse", "--since=not a date"]
