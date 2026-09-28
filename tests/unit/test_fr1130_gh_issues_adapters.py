"""FR-1130 AC-02..AC-05: gh-issues snapshot, discover, versions, extract."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from examples.demos.corpus_census.adapters import gh_issues_adapters as gia

pytestmark = pytest.mark.process

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "fr1130" / "raw_read.json"
RECORDS = json.loads(FIXTURE.read_text(encoding="utf-8"))["records"]
NUMBERS = sorted(r["number"] for r in RECORDS)
REPO = "langchain-ai/langgraph"
SNAPSHOT = Path("tmp/gh-issues-cache/langchain-ai__langgraph.json")


def _lines(records) -> str:
    return "".join(json.dumps(r) + "\n" for r in records)


class FakeGh:
    """Records every argv; returns a canned CompletedProcess or raises."""

    def __init__(self, stdout: str = "", returncode: int = 0, exc=None):
        self.stdout, self.returncode, self.exc = stdout, returncode, exc
        self.calls: list[tuple[list[str], dict]] = []

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), kwargs))
        if self.exc is not None:
            raise self.exc
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, "boom")


@pytest.fixture
def workdir(tmp_path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _discover(source: str, fake: FakeGh) -> list[str]:
    with patch.object(gia.subprocess, "run", fake):
        return gia.gh_issues_discover({"source": source})


# --- AC-02 source grammar and selection ---------------------------------


@pytest.mark.req("REQ-YG-717")
@pytest.mark.parametrize(
    "source",
    [
        "",
        "langgraph",
        "a/b/c",
        "a b/c",
        "a/b:",
        "a/b:0",
        "a/b:-1",
        "a/b:x",
        "a/b:1.5",
        "a/b@",
        "a/b@1,1",
        "a/b@0",
        "a/b@x",
        "a/b:3@4",
    ],
)
def test_malformed_source_raises(source):
    with pytest.raises(ValueError):
        gia.parse_source(source)


@pytest.mark.req("REQ-YG-717")
@pytest.mark.parametrize(
    ("n", "expected_positions"),
    [(1, [0]), (3, [0, 5, 10]), (11, list(range(11)))],
)
def test_spread_sample_indices(workdir, n, expected_positions):
    refs = _discover(f"{REPO}:{n}", FakeGh(_lines(RECORDS)))
    assert refs == [f"{REPO}#{NUMBERS[i]}" for i in expected_positions]


@pytest.mark.req("REQ-YG-717")
def test_sample_over_population_raises_and_keeps_no_snapshot(workdir):
    with pytest.raises(ValueError, match="exceeds population"):
        _discover(f"{REPO}:12", FakeGh(_lines(RECORDS)))


@pytest.mark.req("REQ-YG-717")
def test_named_selection_and_unknown_number(workdir):
    refs = _discover(f"{REPO}@7400,6534", FakeGh(_lines(RECORDS)))
    assert refs == [f"{REPO}#6534", f"{REPO}#7400"]
    with pytest.raises(ValueError, match="not in snapshot"):
        _discover(f"{REPO}@6534,6100", FakeGh(_lines(RECORDS)))


# --- AC-03 discovery boundary --------------------------------------------


@pytest.mark.req("REQ-YG-717")
def test_discover_runs_frozen_argv_and_returns_all_refs(workdir):
    fake = FakeGh(_lines(reversed(RECORDS)))
    refs = _discover(REPO, fake)
    assert refs == [f"{REPO}#{n}" for n in NUMBERS]
    assert len(fake.calls) == 1
    argv, kwargs = fake.calls[0]
    assert argv == [
        "gh",
        "api",
        "--paginate",
        "--jq",
        gia.LIST_JQ,
        f"repos/{REPO}/issues?state=all&per_page=100",
    ]
    assert kwargs["timeout"] == 900
    assert kwargs["check"] is False


def _record(**overrides):
    record = dict(RECORDS[0])
    record.update(overrides)
    return record


ISSUE = next(r for r in RECORDS if r["kind"] == "issue")
PR = next(r for r in RECORDS if r["kind"] == "pr")

BAD_OUTPUTS = {
    "empty": "",
    "not-json": _lines(RECORDS[:2]) + "{not json\n",
    "missing-field": _lines(
        [{k: v for k, v in RECORDS[0].items() if k != "updated_at"}]
    ),
    "extra-field": _lines([_record(surprise=1)]),
    "null-title": _lines([_record(title=None)]),
    "empty-title": _lines([_record(title="")]),
    "bad-kind": _lines([_record(kind="discussion")]),
    "bad-state": _lines([_record(state="merged")]),
    "issue-with-merged": _lines([dict(ISSUE, merged=True)]),
    "pr-without-merged": _lines([dict(PR, merged=None)]),
    "negative-comments": _lines([_record(comments=-1)]),
    "long-body": _lines([_record(body_head="x" * 1501)]),
    "too-many-labels": _lines([_record(labels=[f"l{i}" for i in range(51)])]),
    "bad-timestamp": _lines([_record(updated_at="yesterday")]),
    "zero-number": _lines([_record(number=0)]),
    "duplicate": _lines([RECORDS[0], RECORDS[0]]),
}


@pytest.mark.req("REQ-YG-717")
@pytest.mark.parametrize("case", sorted(BAD_OUTPUTS))
def test_invalid_listing_raises_and_keeps_prior_snapshot(workdir, case):
    _discover(REPO, FakeGh(_lines(RECORDS)))
    before = SNAPSHOT.read_bytes()
    with pytest.raises(ValueError):
        _discover(REPO, FakeGh(BAD_OUTPUTS[case]))
    assert SNAPSHOT.read_bytes() == before


@pytest.mark.req("REQ-YG-717")
@pytest.mark.parametrize(
    "fake",
    [
        FakeGh(_lines(RECORDS), returncode=1),
        FakeGh(exc=subprocess.TimeoutExpired(["gh"], 900)),
    ],
    ids=["exit-1", "timeout"],
)
def test_command_failure_raises_and_keeps_prior_snapshot(workdir, fake):
    _discover(REPO, FakeGh(_lines(RECORDS)))
    before = SNAPSHOT.read_bytes()
    with pytest.raises((RuntimeError, subprocess.TimeoutExpired)):
        _discover(REPO, fake)
    assert SNAPSHOT.read_bytes() == before


@pytest.mark.req("REQ-YG-717")
def test_over_ceiling_population_raises(workdir, monkeypatch):
    monkeypatch.setattr(gia, "MAX_POPULATION", 5)
    with pytest.raises(ValueError, match="ceiling"):
        _discover(REPO, FakeGh(_lines(RECORDS)))
    assert not SNAPSHOT.exists()


# --- AC-04 snapshot envelope, replace-not-merge ---------------------------


@pytest.mark.req("REQ-YG-717")
def test_snapshot_envelope_is_typed_and_hashed(workdir):
    _discover(REPO, FakeGh(_lines(RECORDS)))
    snap = gia.load_snapshot(REPO)
    assert snap.schema_version == gia.SCHEMA_VERSION
    assert snap.repository == REPO
    assert snap.query == f"repos/{REPO}/issues?state=all&per_page=100"
    assert snap.count == len(RECORDS)
    assert [r.number for r in snap.items] == NUMBERS
    assert snap.sha256 == gia.items_sha256(snap.items)
    assert len(snap.retrieved_at) == 20 and snap.retrieved_at.endswith("Z")


@pytest.mark.req("REQ-YG-717")
def test_removed_item_leaves_next_snapshot(workdir):
    _discover(REPO, FakeGh(_lines(RECORDS)))
    fewer = [r for r in RECORDS if r["number"] != 7000]
    refs = _discover(REPO, FakeGh(_lines(fewer)))
    assert f"{REPO}#7000" not in refs
    assert 7000 not in [r.number for r in gia.load_snapshot(REPO).items]


# --- AC-05 versions and extract --------------------------------------------


@pytest.mark.req("REQ-YG-717")
def test_versions_match_selection(workdir):
    refs = _discover(f"{REPO}@6534,8200", FakeGh(_lines(RECORDS)))
    versions = gia.gh_issues_versions({"source": f"{REPO}@6534,8200"})
    by_number = {r["number"]: r["updated_at"] for r in RECORDS}
    assert versions == {ref: by_number[int(ref.split("#")[1])] for ref in refs}
    assert list(versions) == refs


@pytest.mark.req("REQ-YG-717")
def test_versions_without_snapshot_raises(workdir):
    with pytest.raises(FileNotFoundError):
        gia.gh_issues_versions({"source": REPO})


@pytest.mark.req("REQ-YG-717")
def test_extract_reads_snapshot_without_api_call(workdir):
    _discover(REPO, FakeGh(_lines(RECORDS)))
    forbidden = FakeGh(exc=AssertionError("extract must not call gh"))
    with patch.object(gia.subprocess, "run", forbidden):
        blob = gia.gh_issues_extract({"item": f"{REPO}#6534"})
        with pytest.raises(ValueError, match="absent"):
            gia.gh_issues_extract({"item": f"{REPO}#6100"})
    bundle = json.loads(blob)
    assert bundle == next(r for r in RECORDS if r["number"] == 6534)
    assert forbidden.calls == []
