"""FR-1120 AC-05/AC-06: census pair_executed index join and merged reducer path."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from yamlgraph.models.map_results import MapFailure

pytestmark = pytest.mark.process

LABELS = json.dumps(["tooling", "tests"])
SURFACES = json.dumps(["backend", "docs"])
ITEMS = ["acme/a#1", "acme/a#2", "acme/b#7"]


def _tools():
    from examples.demos.person_profile_census import tools

    return tools


def bundle(i: int) -> dict:
    repo, number = ITEMS[i].split("#")
    return {
        "repo": repo,
        "number": int(number),
        "url": f"https://github.com/{repo}/pull/{number}",
        "title": f"feat: thing {i}",
        "state": "merged",
        "created_at": "2026-09-01T00:00:00Z",
        "merged_at": "2026-09-02T00:00:00Z",
        "additions": 10 + i,
        "deletions": i,
        "changed_files": 1,
        "labels": [],
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
        "body_head": f"body {i}",
    }


def verdict(i: int) -> dict:
    return {
        "problem_class": "tooling",
        "change_kind": "feat",
        "surfaces": ["backend"],
        "intent": f"intent {i}",
        "evidence_span": f"thing {i}",
    }


def contents(indices=(0, 1, 2)) -> list[dict]:
    return [{"_map_index": i, "value": json.dumps(bundle(i))} for i in indices]


def findings(indices=(0, 2)) -> list[dict]:
    return [{"_map_index": i, **verdict(i)} for i in indices]


def failure(index: int) -> dict:
    return MapFailure(
        map="judge_items",
        dispatch="d1",
        index=index,
        error_type="ValueError",
        message="stub provider error",
        node="_map_judge_items_sub",
        tolerated=True,
    ).model_dump()


def pair_state(**overrides) -> dict:
    state = {
        "memo": {"result": {"todo": list(ITEMS)}},
        "executed_contents": contents(),
        "executed_findings": findings(),
        "executed_findings_failures": [failure(1)],
    }
    return {**state, **overrides}


@pytest.mark.req("REQ-YG-709")
class TestPairExecuted:
    def test_joins_by_index_and_strips_source_index(self):
        state = pair_state(
            executed_contents=list(reversed(contents())),
            executed_findings=[{**f, "source_index": 99} for f in reversed(findings())],
        )
        records = _tools().pair_executed(state)["paired"]
        assert [r["_map_index"] for r in records] == [0, 1, 2]
        assert records[0] == {
            "_map_index": 0,
            "bundle": bundle(0),
            "finding": verdict(0),
        }
        assert records[1] == {
            "_map_index": 1,
            "bundle": bundle(1),
            "error": "stub provider error",
        }
        assert records[2]["finding"] == verdict(2)
        assert all("source_index" not in r.get("finding", {}) for r in records)

    def test_empty_todo_pairs_nothing(self):
        state = pair_state(
            memo={"result": {"todo": []}},
            executed_contents=[],
            executed_findings=[],
            executed_findings_failures=[],
        )
        assert _tools().pair_executed(state) == {"paired": []}

    @pytest.mark.parametrize(
        "overrides",
        [
            {"executed_contents": contents([0, 1])},
            {"executed_contents": [*contents(), contents([1])[0]]},
            {
                "executed_contents": [
                    *contents([0, 1]),
                    {"_map_index": 3, "value": "{}"},
                ]
            },
            {
                "executed_contents": [
                    *contents([0, 1]),
                    {"_map_index": True, "value": "{}"},
                ]
            },
            {"executed_findings": findings([0])},
            {"executed_findings": findings([0, 1, 2])},
            {"executed_findings": [*findings(), {"_map_index": 5, **verdict(0)}]},
            {
                "executed_findings": [
                    {"_map_index": False, **verdict(0)},
                    *findings([2]),
                ]
            },
            {"executed_findings_failures": []},
        ],
        ids=[
            "bundle-missing",
            "bundle-duplicate",
            "bundle-out-of-range",
            "bundle-bool",
            "outcome-missing",
            "outcome-cross-channel-duplicate",
            "outcome-out-of-range",
            "outcome-bool",
            "failure-missing",
        ],
    )
    def test_malformed_attribution_emits_nothing(self, overrides):
        with pytest.raises(ValueError):
            _tools().pair_executed(pair_state(**overrides))


def _reduce(tmp_path: Path, name: str, **state) -> bytes:
    out = tmp_path / name / "ledger.md"
    _tools().reduce_pr_ledger(
        {
            "items": list(ITEMS),
            "problem_labels": LABELS,
            "surface_labels": SURFACES,
            "azure_model": "m-1",
            "output_path": str(out),
            **state,
        }
    )
    return out.with_suffix(".jsonl").read_bytes()


def _merged(records: list[dict]) -> dict:
    return {"result": {"records": records}}


@pytest.mark.req("REQ-YG-709")
class TestReduceMerged:
    def test_merged_path_is_byte_identical(self, tmp_path):
        live = _reduce(
            tmp_path,
            "live",
            contents=contents(),
            findings=findings(),
            findings_failures=[failure(1)],
        )
        records = _tools().pair_executed(pair_state())["paired"]
        memo = _reduce(tmp_path, "memo", merged=_merged(records))
        assert memo == live
        rows = [json.loads(line) for line in memo.splitlines()]
        assert [r["classification_status"] for r in rows] == [
            "judged",
            "row_failed",
            "judged",
        ]

    def test_bad_evidence_row_failed_identical(self, tmp_path):
        bad = {**verdict(0), "evidence_span": "not there"}
        live = _reduce(
            tmp_path,
            "live",
            contents=contents(),
            findings=[{"_map_index": 0, **bad}, *findings([2])],
            findings_failures=[failure(1)],
        )
        records = _tools().pair_executed(
            pair_state(executed_findings=[{"_map_index": 0, **bad}, *findings([2])])
        )["paired"]
        assert _reduce(tmp_path, "memo", merged=_merged(records)) == live

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda rs: rs[:2],
            lambda rs: [*rs, rs[0]],
            lambda rs: [*rs[:2], {**rs[2], "_map_index": 7}],
            lambda rs: [*rs[:2], {"_map_index": 2, "finding": verdict(2)}],
        ],
        ids=["missing", "duplicate", "out-of-range", "no-bundle"],
    )
    def test_malformed_merged_records_are_batch_fatal(self, tmp_path, mutate):
        records = _tools().pair_executed(pair_state())["paired"]
        with pytest.raises(ValueError):
            _reduce(tmp_path, "bad", merged=_merged(mutate(records)))
