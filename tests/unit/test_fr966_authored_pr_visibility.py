"""FR-966 witnesses: authored-PR discovery refuses unsatisfiable visibility.

`gh search prs` conjoins repeated `--visibility` flags into `is:` qualifiers.
A pull request has exactly one visibility, so any list of two or more classes
is unsatisfiable by construction and returns an empty population that the
adapter then blames on the author/owner/since triple.

GitHub offers no disjunctive escape: `is:private OR is:internal` is rejected
with HTTP 422 ("Logical operators only apply to text, not to qualifiers") and
the parenthesised form is accepted as free text and silently returns zero.
The only honest move is to refuse the cardinality at the input boundary.
"""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

import pytest

from examples.demos.corpus_census.adapters import corpus_adapters
from examples.demos.corpus_census.adapters.corpus_adapters import (
    _parse_visibility,
    gh_authored_prs_discover,
)

# References examples/ (process boundary, FR-756)
pytestmark = pytest.mark.process

SOURCE = "sheikkinen@acme:2026-01-01"


def _completed(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout)


def _explode(*argv: str) -> str:
    raise AssertionError(f"_gh must not be reached; got argv={list(argv)}")


@pytest.mark.req("REQ-YG-643")
def test_multi_value_visibility_rejected_before_any_gh_call() -> None:
    """AC-03/AC-04: reject the conjunction, and reject it before the network."""
    with (
        patch.object(corpus_adapters, "_gh", _explode),
        pytest.raises(ValueError) as excinfo,
    ):
        gh_authored_prs_discover(
            {"source": SOURCE, "visibility": '["private", "internal"]'}
        )

    message = str(excinfo.value)
    # Names the mechanism, not merely the symptom.
    assert "--visibility" in message
    assert "conjoin" in message.casefold()
    # Reproduces what the operator typed: original order, original spelling.
    assert repr(["private", "internal"]) in message
    # States the remedy.
    assert "one" in message.casefold()


@pytest.mark.req("REQ-YG-643")
def test_rejection_reports_original_order_and_spelling() -> None:
    """AC-03: the echo is the operator's input, not the canonicalised list."""
    with (
        patch.object(corpus_adapters, "_gh", _explode),
        pytest.raises(ValueError) as excinfo,
    ):
        _parse_visibility({"visibility": '["Internal", "public"]'})

    message = str(excinfo.value)
    assert repr(["Internal", "public"]) in message
    # The casefolded canonical form is not what was typed and must not be shown.
    assert repr(["internal", "public"]) not in message


@pytest.mark.req("REQ-YG-643")
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('["private"', "must be JSON list"),
        ('"private"', "must be a non-empty list"),
        ("{}", "must be a non-empty list"),
        ("[]", "must be a non-empty list"),
        ("[1]", "entry must be str"),
        ('["secret"]', "unknown visibility"),
        ('["private", "PRIVATE"]', "duplicate visibility"),
    ],
    ids=[
        "malformed-json-string",
        "non-list-json-scalar",
        "non-list-json-object",
        "empty-list",
        "non-string-entry",
        "unknown-class",
        "casefold-duplicate",
    ],
)
def test_existing_validation_classes_survive_the_new_guard(
    raw: str, expected: str
) -> None:
    """AC-05: every prior failure keeps its class and is reached first."""
    with pytest.raises(ValueError, match=expected):
        _parse_visibility({"visibility": raw})


@pytest.mark.req("REQ-YG-643")
def test_single_element_canonicalises_and_emits_exactly_one_flag() -> None:
    """AC-06: one class in, one canonical flag out, no network."""
    assert _parse_visibility({"visibility": '["PRIVATE"]'}) == ["private"]

    seen: list[list[str]] = []

    def _capture(*argv: str) -> str:
        seen.append(list(argv))
        return json.dumps([{"repository": {"nameWithOwner": "acme/api"}, "number": 7}])

    with patch.object(corpus_adapters, "_gh", _capture):
        gh_authored_prs_discover({"source": SOURCE, "visibility": '["PRIVATE"]'})

    argv = seen[0]
    assert argv.count("--visibility") == 1
    assert argv[argv.index("--visibility") + 1] == "private"


@pytest.mark.req("REQ-YG-643")
def test_accepted_population_keeps_sorted_identity_shape() -> None:
    """AC-07: the guard does not disturb the authored-PR identity contract."""
    listing = json.dumps(
        [
            {"repository": {"nameWithOwner": "acme/web"}, "number": 12},
            {"repository": {"nameWithOwner": "acme/api"}, "number": 3},
        ]
    )
    with patch.object(corpus_adapters, "_gh", lambda *argv: listing):
        refs = gh_authored_prs_discover({"source": SOURCE, "visibility": '["private"]'})

    assert refs == ["acme/api#3", "acme/web#12"]
