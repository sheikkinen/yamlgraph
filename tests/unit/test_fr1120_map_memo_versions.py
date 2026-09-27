"""FR-1120 AC-01/AC-02: map memo split with caller-supplied versions."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.process

MAP, DISPATCH = "judge_items", "tok-1"
ITEMS = ["acme/a#1", "acme/a#2", "acme/b#7"]


def _mm():
    import examples.shared.map_memo as mm

    return mm


@pytest.fixture
def env(tmp_path: Path) -> dict:
    sig = tmp_path / "prompt.yaml"
    sig.write_text("prompt: v1\n", encoding="utf-8")
    return {"sig": [str(sig)], "store": str(tmp_path / "m.sqlite")}


def _versions(**overrides: str) -> dict[str, str]:
    base = dict.fromkeys(ITEMS, "2026-09-01T00:00:00Z")
    return {**base, **overrides}


def _split(env: dict, versions, items=ITEMS, store=None) -> dict:
    return _mm().map_memo_split(
        items=items,
        signature_files=env["sig"],
        store=env["store"] if store is None else store,
        versions=versions,
    )


def _merge_all(plan: dict) -> dict:
    results = [{"_map_index": i, "v": key} for i, key in enumerate(plan["todo"])]
    return _mm().map_memo_merge(plan, results, [], MAP, DISPATCH, min_success=0)


@pytest.mark.req("REQ-YG-709")
def test_versions_mode_round_trip_reads_no_item_path(env, monkeypatch):
    mm = _mm()
    real_sha = mm._file_sha

    def _guarded(raw, role):
        if role == "item":
            raise AssertionError(f"item path read: {raw}")
        return real_sha(raw, role)

    monkeypatch.setattr(mm, "_file_sha", _guarded)
    first = _split(env, _versions())
    assert first["todo"] == ITEMS
    assert [i["version"] for i in first["current"]] == [_versions()[k] for k in ITEMS]
    _merge_all(first)
    second = _split(env, _versions())
    assert second["todo"] == []
    assert set(second["hits"]) == set(ITEMS)


@pytest.mark.req("REQ-YG-709")
def test_versions_mode_never_touches_item_paths(env, tmp_path, monkeypatch):
    # An item that names an existing file must still take its supplied version.
    real = tmp_path / "acme"
    real.write_text("bytes", encoding="utf-8")
    items = [str(real)]
    plan = _split(env, {str(real): "v-1"}, items=items)
    assert plan["current"][0]["version"] == "v-1"


@pytest.mark.req("REQ-YG-709")
def test_one_changed_version_is_the_only_todo(env):
    _merge_all(_split(env, _versions()))
    plan = _split(env, _versions(**{"acme/a#2": "2026-09-02T00:00:00Z"}))
    assert plan["todo"] == ["acme/a#2"]


@pytest.mark.req("REQ-YG-709")
@pytest.mark.parametrize(
    "versions",
    [
        dict.fromkeys(ITEMS[:-1], "v"),
        {**dict.fromkeys(ITEMS, "v"), "acme/x#9": "v"},
        ["v", "v", "v"],
        {**dict.fromkeys(ITEMS, "v"), "acme/a#1": ""},
        {**dict.fromkeys(ITEMS, "v"), "acme/a#1": 5},
        {**dict.fromkeys(ITEMS, "v"), "acme/a#1": None},
    ],
    ids=["missing", "extra", "non-dict", "empty", "non-str", "none"],
)
def test_bad_versions_raise_before_store(env, versions):
    with pytest.raises(_mm().MapMemoInputError):
        _split(env, versions)
    assert not Path(env["store"]).exists()


@pytest.mark.req("REQ-YG-709")
@pytest.mark.parametrize(
    "items",
    [["acme/a#1", "acme/a#1"], ["acme/a#1", ""], ["acme/a#1", 3], []],
    ids=["duplicate", "empty", "non-str", "no-items"],
)
def test_bad_items_raise_in_versions_mode(env, items):
    versions = {i: "v" for i in items if isinstance(i, str)}
    with pytest.raises(_mm().MapMemoInputError):
        _split(env, versions, items=items)
    assert not Path(env["store"]).exists()


@pytest.mark.req("REQ-YG-709")
@pytest.mark.parametrize("store", ["", 5, None])
@pytest.mark.parametrize("mode", ["versions", "files"])
def test_bad_store_raises_in_both_modes(env, tmp_path, store, mode):
    mm = _mm()
    if mode == "versions":
        kwargs = {"items": ITEMS, "versions": _versions()}
    else:
        f = tmp_path / "f.txt"
        f.write_text("x", encoding="utf-8")
        kwargs = {"items": [str(f)]}
    with pytest.raises(mm.MapMemoInputError):
        mm.map_memo_split(signature_files=env["sig"], store=store, **kwargs)
