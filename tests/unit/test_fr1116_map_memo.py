"""FR-1116 map memo helpers — REQ-YG-706 witnesses.

The helpers are called directly; process-boundary cases run split in a
fresh interpreter so reuse is proven through the SQLite file alone.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from yamlgraph.models.map_results import MapCompletenessError, MapFailure

pytestmark = pytest.mark.process

SHARED = Path("examples/shared")
MAP, DISPATCH = "summarize", "tok-1"


def _mm():
    import examples.shared.map_memo as mm

    return mm


@pytest.fixture
def corpus(tmp_path: Path) -> dict:
    files = []
    for i in range(5):
        p = tmp_path / f"f{i}.txt"
        p.write_text(f"file {i}\n", encoding="utf-8")
        files.append(str(p))
    sig = tmp_path / "prompt.yaml"
    sig.write_text("prompt: v1\n", encoding="utf-8")
    return {"items": files, "sig": [str(sig)], "store": str(tmp_path / "m.sqlite")}


def _split(c: dict, inputs=None) -> dict:
    return _mm().map_memo_split(
        items=c["items"], signature_files=c["sig"], store=c["store"], inputs=inputs
    )


def _fail(index: int, *, dispatch: str = DISPATCH, tolerated=False) -> MapFailure:
    return MapFailure(
        map=MAP,
        dispatch=dispatch,
        index=index,
        error_type="ClaimMismatchError",
        message=f"bad {index}",
        node="_map_summarize_sub",
        tolerated=tolerated,
    )


def _run(plan: dict, fail_keys=(), min_success=0.0, dispatch=DISPATCH) -> dict:
    """Simulate the map over `todo`, then merge."""
    results, failures = [], []
    for i, key in enumerate(plan["todo"]):
        if key in fail_keys:
            failures.append(_fail(i, dispatch=dispatch))
        else:
            results.append({"_map_index": i, "path": key, "dispatch": "business"})
    return _mm().map_memo_merge(
        plan=plan,
        results=results,
        failures=failures,
        map_name=MAP,
        map_dispatch=dispatch,
        min_success=min_success,
    )


# AC-01
@pytest.mark.req("REQ-YG-706")
def test_split_over_missing_store_creates_nothing(corpus):
    plan = _split(corpus)
    assert plan["todo"] == corpus["items"]
    assert not Path(corpus["store"]).exists()


@pytest.mark.req("REQ-YG-706")
def test_split_leaves_existing_store_byte_identical(corpus):
    _run(_split(corpus))
    before = Path(corpus["store"]).read_bytes()
    _split(corpus)
    assert Path(corpus["store"]).read_bytes() == before


# AC-02
def _split_in_subprocess(c: dict) -> dict:
    code = (
        "import json,sys\n"
        "from examples.shared.map_memo import map_memo_split\n"
        "a=json.loads(sys.argv[1])\n"
        "print(json.dumps(map_memo_split(items=a['items'],"
        "signature_files=a['sig'],store=a['store'])))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code, json.dumps(c)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout)


@pytest.mark.req("REQ-YG-706")
def test_separate_process_reuses_then_changed_file_reruns(corpus):
    _run(_split(corpus))
    plan = _split_in_subprocess(corpus)
    assert plan["todo"] == []
    assert [i["hit"] for i in plan["current"]] == ["ok"] * 5

    Path(corpus["items"][2]).write_text("changed\n", encoding="utf-8")
    plan = _split(corpus)
    assert plan["todo"] == [corpus["items"][2]]
    merged = _run(plan)
    assert [r["_map_index"] for r in merged["records"]] == [0, 1, 2, 3, 4]
    assert [r["path"] for r in merged["records"]] == corpus["items"]
    assert merged["counts"] == {
        "executed_ok": 1,
        "executed_failed": 0,
        "reused_ok": 4,
        "reused_failed": 0,
    }


# AC-03
@pytest.mark.req("REQ-YG-706")
def test_signature_file_byte_reruns_everything(corpus):
    _run(_split(corpus))
    Path(corpus["sig"][0]).write_text("prompt: v2\n", encoding="utf-8")
    assert _split(corpus)["todo"] == corpus["items"]


@pytest.mark.req("REQ-YG-706")
def test_inputs_change_reruns_everything(corpus):
    _run(_split(corpus, inputs={"rubric": "a"}))
    assert _split(corpus, inputs={"rubric": "a"})["todo"] == []
    assert _split(corpus, inputs={"rubric": "b"})["todo"] == corpus["items"]


@pytest.mark.req("REQ-YG-706")
def test_signature_stable_across_processes(corpus):
    assert _split(corpus)["signature"] == _split_in_subprocess(corpus)["signature"]


@pytest.mark.parametrize("bad", [["x"], {"n": float("nan")}, {"o": object()}])
@pytest.mark.req("REQ-YG-706")
def test_invalid_inputs_raise(corpus, bad):
    with pytest.raises(_mm().MapMemoInputError):
        _split(corpus, inputs=bad)


# AC-04
@pytest.mark.req("REQ-YG-706")
def test_failed_item_is_carried_then_rerun_on_change(corpus):
    bad = corpus["items"][1]
    _run(_split(corpus), fail_keys={bad})
    plan = _split(corpus)
    assert plan["todo"] == []
    merged = _run(plan, dispatch="tok-2")
    [failure] = [MapFailure.model_validate(f) for f in merged["failures"]]
    assert (failure.index, failure.dispatch, failure.map) == (1, "tok-2", MAP)
    assert failure.message == "bad 1"
    assert merged["counts"]["reused_failed"] == 1
    assert merged["verdict"]["failed"] == 1
    assert merged["verdict"]["dispatched"] == 5
    assert merged["verdict"]["dispatch"] == "tok-2"

    Path(bad).write_text("fixed\n", encoding="utf-8")
    assert _split(corpus)["todo"] == [bad]


# AC-05
@pytest.mark.req("REQ-YG-706")
def test_threshold_judged_after_commit_over_whole_population(corpus):
    bad = set(corpus["items"][:2])
    with pytest.raises(MapCompletenessError):
        _run(_split(corpus), fail_keys=bad, min_success=0.9)
    plan = _split(corpus)
    assert plan["todo"] == []
    with pytest.raises(MapCompletenessError) as exc:
        _run(plan, min_success=0.9)
    assert exc.value.verdict.dispatched == 5
    assert exc.value.verdict.accepted == 3


@pytest.mark.parametrize("bad", [True, -1, 1.5, -0.1, float("inf"), "0.9", None])
@pytest.mark.req("REQ-YG-706")
def test_invalid_min_success_raises_and_writes_nothing(corpus, bad):
    with pytest.raises(_mm().MapMemoInputError):
        _run(_split(corpus), min_success=bad)
    assert not Path(corpus["store"]).exists()


@pytest.mark.req("REQ-YG-706")
def test_integer_min_success_distinct_from_fraction(corpus):
    merged = _run(_split(corpus), fail_keys={corpus["items"][0]}, min_success=4)
    assert merged["verdict"]["met"] is True
    with pytest.raises(MapCompletenessError):
        _run(_split(corpus), min_success=1.0)


# AC-06
def _merge_raw(plan, results, failures):
    return _mm().map_memo_merge(
        plan=plan,
        results=results,
        failures=failures,
        map_name=MAP,
        map_dispatch=DISPATCH,
        min_success=0,
    )


@pytest.mark.parametrize(
    ("results", "failures"),
    [
        ([{"_map_index": i} for i in range(4)], []),
        ([{"_map_index": i} for i in (0, 1, 2, 3, 3)], []),
        ([{"_map_index": i} for i in range(4)] + [{"_map_index": 5}], []),
        ([{"_map_index": i} for i in range(4)] + [{"_map_index": True}], []),
        ([{"_map_index": i} for i in range(4)], [_fail(4, dispatch="other")]),
        ([{"_map_index": i} for i in range(4)] + [{"_map_index": 4, "v": {1}}], []),
    ],
    ids=["missing", "duplicate", "exceeds", "bool", "foreign-dispatch", "non-json"],
)
@pytest.mark.req("REQ-YG-706")
def test_bad_attribution_raises_and_writes_nothing(corpus, results, failures):
    with pytest.raises(_mm().MapMemoInputError):
        _merge_raw(_split(corpus), results, failures)
    assert not Path(corpus["store"]).exists()


@pytest.mark.req("REQ-YG-706")
def test_persisted_payloads_are_stable(corpus):
    _run(_split(corpus), fail_keys={corpus["items"][4]})
    with sqlite3.connect(corpus["store"]) as db:
        rows = dict(
            db.execute(
                "SELECT status, payload FROM memo WHERE key IN (?, ?)",
                (corpus["items"][0], corpus["items"][4]),
            ).fetchall()
        )
    ok, failed = json.loads(rows["ok"]), json.loads(rows["failed"])
    assert ok == {"path": corpus["items"][0], "dispatch": "business"}
    assert set(failed) == {"error_type", "message", "node", "tolerated"}


# AC-07
@pytest.mark.parametrize(
    "items",
    [[1], [""], ["DUP", "DUP"], ["missing.txt"], ["DIR"]],
    ids=["non-string", "empty", "duplicate", "missing", "directory"],
)
@pytest.mark.req("REQ-YG-706")
def test_invalid_items_raise(corpus, tmp_path, items):
    items = [str(tmp_path / "f0.txt") if i == "DUP" else i for i in items]
    items = [str(tmp_path) if i == "DIR" else i for i in items]
    with pytest.raises(_mm().MapMemoInputError):
        _mm().map_memo_split(
            items=items, signature_files=corpus["sig"], store=corpus["store"]
        )


@pytest.mark.req("REQ-YG-706")
def test_empty_signature_files_raise(corpus):
    with pytest.raises(_mm().MapMemoInputError):
        _mm().map_memo_split(
            items=corpus["items"], signature_files=[], store=corpus["store"]
        )


@pytest.mark.req("REQ-YG-706")
def test_relative_paths_resolve_against_cwd(corpus, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = _mm().map_memo_split(
        items=["f0.txt"], signature_files=["prompt.yaml"], store="m.sqlite"
    )
    assert plan["todo"] == ["f0.txt"]
    assert Path(plan["store"]).is_absolute()


# AC-08
@pytest.mark.req("REQ-YG-706")
def test_non_sqlite_store_raises(corpus):
    Path(corpus["store"]).write_text("not a database", encoding="utf-8")
    with pytest.raises(_mm().MapMemoStoreError):
        _split(corpus)


@pytest.mark.req("REQ-YG-706")
def test_wrong_schema_version_raises(corpus):
    _run(_split(corpus))
    with sqlite3.connect(corpus["store"]) as db:
        db.execute("UPDATE meta SET value = '2' WHERE name = 'schema_version'")
    with pytest.raises(_mm().MapMemoStoreError):
        _split(corpus)


@pytest.mark.req("REQ-YG-706")
def test_malformed_row_raises(corpus):
    _run(_split(corpus))
    with sqlite3.connect(corpus["store"]) as db:
        db.execute(
            "UPDATE memo SET payload = '{not json' WHERE key = ?", (corpus["items"][0],)
        )
    with pytest.raises(_mm().MapMemoStoreError):
        _split(corpus)


@pytest.mark.req("REQ-YG-706")
def test_lock_beyond_busy_timeout_raises(corpus, monkeypatch):
    _run(_split(corpus))
    monkeypatch.setattr(_mm(), "BUSY_TIMEOUT_S", 0.1)
    holder = sqlite3.connect(corpus["store"], isolation_level=None)
    holder.execute("BEGIN EXCLUSIVE")
    try:
        with pytest.raises(_mm().MapMemoStoreError):
            _split(corpus)
    finally:
        holder.execute("ROLLBACK")
        holder.close()


@pytest.mark.req("REQ-YG-706")
def test_failed_write_raises(corpus):
    plan = _split(corpus)
    Path(corpus["store"]).write_bytes(b"")
    Path(corpus["store"]).chmod(0o444)
    try:
        with pytest.raises(_mm().MapMemoStoreError):
            _run(plan)
    finally:
        Path(corpus["store"]).chmod(0o644)


# AC-08a
@pytest.mark.req("REQ-YG-706")
def test_stale_writer_never_yields_false_hit(corpus):
    target = Path(corpus["items"][0])
    plan_a = _split(corpus)
    target.write_text("version 2\n", encoding="utf-8")
    plan_b = _split(corpus)
    _run(plan_b)
    _run(plan_a)
    assert _split(corpus)["todo"] == [str(target)]


# AC-09
@pytest.mark.parametrize("name", ["map_memo_split", "map_memo_merge"])
@pytest.mark.req("REQ-YG-706")
def test_manifest_resolves_shared_module(name):
    from yamlgraph.tools.manifest import expand_tool_manifests

    manifest = (SHARED / f"{name}.tool.yaml").resolve()
    tool = expand_tool_manifests({name: {"manifest": str(manifest)}}, None)[name]
    assert tool["type"] == "python"
    assert tool["function"] == name
    assert Path(tool["path"]) == (SHARED / "map_memo.py").resolve()


def _load_via_manifest(name: str):
    """Load the function the way a graph does: FR-768 path, no sys.modules entry."""
    from yamlgraph.tools.manifest import expand_tool_manifests
    from yamlgraph.tools.python_tool import load_python_function, parse_python_tools

    manifest = (SHARED / f"{name}.tool.yaml").resolve()
    tools = expand_tool_manifests({name: {"manifest": str(manifest)}}, None)
    return load_python_function(parse_python_tools(tools)[name], tool_name=name)


# Smoke 2026-09-27: the path-loaded module could not build its Pydantic models.
@pytest.mark.req("REQ-YG-706")
def test_manifest_loaded_functions_split_and_merge(corpus):
    split = _load_via_manifest("map_memo_split")
    merge = _load_via_manifest("map_memo_merge")
    plan = split(
        items=corpus["items"], signature_files=corpus["sig"], store=corpus["store"]
    )
    results = [{"_map_index": i} for i in range(len(plan["todo"]))]
    merged = merge(
        plan=plan,
        results=results,
        failures=[],
        map_name=MAP,
        map_dispatch=DISPATCH,
    )
    assert merged["counts"]["executed_ok"] == 5


# Smoke 2026-09-27: outputs/meta_map/ did not exist on a fresh checkout.
@pytest.mark.req("REQ-YG-706")
def test_merge_creates_missing_store_directory(corpus, tmp_path):
    corpus = {**corpus, "store": str(tmp_path / "new" / "dir" / "m.sqlite")}
    _run(_split(corpus))
    assert Path(corpus["store"]).is_file()
