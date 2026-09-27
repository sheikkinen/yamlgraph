"""FR-1120 AC-04: authored-PR versions adapter shares discover's search."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from examples.demos.corpus_census.adapters import corpus_adapters
from examples.demos.corpus_census.adapters.corpus_adapters import (
    gh_authored_prs_discover,
)


def gh_authored_prs_versions(state):
    return corpus_adapters.gh_authored_prs_versions(state)


pytestmark = pytest.mark.process

STATE = {"source": "sheikkinen@acme:2026-01-01", "visibility": '["private"]'}


def _entry(repo: str, number: int, updated: object = "2026-09-01T00:00:00Z"):
    entry = {"repository": {"nameWithOwner": repo}, "number": number}
    if updated is not ...:
        entry["updatedAt"] = updated
    return entry


LISTING = [
    _entry("acme/b", 7, "2026-09-03T00:00:00Z"),
    _entry("acme/a", 2, "2026-09-02T00:00:00Z"),
    _entry("acme/a", 1, "2026-09-01T00:00:00Z"),
]


def _run(fn, listing):
    seen: list[list[str]] = []

    def _capture(*argv: str) -> str:
        seen.append(list(argv))
        return json.dumps(listing)

    with patch.object(corpus_adapters, "_gh", _capture):
        return fn(dict(STATE)), seen


@pytest.mark.req("REQ-YG-709")
def test_versions_map_matches_discover_population():
    versions, seen = _run(gh_authored_prs_versions, LISTING)
    refs, _ = _run(gh_authored_prs_discover, LISTING)
    assert versions == {
        "acme/a#1": "2026-09-01T00:00:00Z",
        "acme/a#2": "2026-09-02T00:00:00Z",
        "acme/b#7": "2026-09-03T00:00:00Z",
    }
    assert list(versions) == refs
    argv = seen[0]
    assert argv[argv.index("--json") + 1] == "repository,number,updatedAt"


@pytest.mark.req("REQ-YG-709")
@pytest.mark.parametrize(
    "updated", [..., None, "", 17], ids=["missing", "null", "empty", "non-str"]
)
def test_unusable_updated_at_rejected(updated):
    listing = [*LISTING[:2], _entry("acme/a", 1, updated)]
    with pytest.raises(ValueError, match="updatedAt"):
        _run(gh_authored_prs_versions, listing)


@pytest.mark.req("REQ-YG-709")
@pytest.mark.parametrize(
    ("listing", "match"),
    [
        ([], "no PRs for"),
        ([*LISTING, _entry("acme/a", 1)], "duplicate item ref"),
        (
            [_entry("acme/r", n) for n in range(1, corpus_adapters.MAX_PRS + 2)],
            "population exceeded MAX_PRS",
        ),
    ],
    ids=["empty", "duplicate", "overflow"],
)
def test_shared_failures_keep_discover_messages(listing, match):
    for fn in (gh_authored_prs_discover, gh_authored_prs_versions):
        with pytest.raises(ValueError, match=match) as info:
            _run(fn, listing)
        assert str(info.value).startswith("gh_authored_prs_discover:")


@pytest.mark.req("REQ-YG-709")
def test_unsatisfiable_visibility_rejected_before_gh():
    def _explode(*argv: str) -> str:
        raise AssertionError("gh reached")

    state = {**STATE, "visibility": '["private","internal"]'}
    with (
        patch.object(corpus_adapters, "_gh", _explode),
        pytest.raises(ValueError, match="conjoins"),
    ):
        gh_authored_prs_versions(state)
