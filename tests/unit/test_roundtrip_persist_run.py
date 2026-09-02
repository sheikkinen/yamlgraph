"""FR-623 unit tests for the round-trip skeleton ``persist_run`` leaf tool.

The skeleton (FR-610..613) computes ``cast``/``briefs``/``book``/``coherence`` in
state and then discards them at process exit. ``persist_run`` is the deterministic
side-effect leaf (no LLM) that writes each stage's result to a run-stamped artifact
directory, so every run is durable and demo-able without ``--export-state``.

Judge corrections folded into these tests:
- Corr 1: ``provider``/``model`` are sourced from the environment (not graph state).
- Corr 3: ``run_id`` uses microsecond precision, so two draws of one premise within
  the same second never collide.
- The missing-key raise mirrors ``assemble_book`` (a broken upstream stage cannot
  yield a silent/empty run dir).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

EXAMPLE_DIR = Path(__file__).resolve().parents[2] / "examples" / "plot_modeller"


def _load_tools():
    if str(EXAMPLE_DIR) not in sys.path:
        sys.path.insert(0, str(EXAMPLE_DIR))
    spec = importlib.util.spec_from_file_location(
        "roundtrip_tools_fr623", EXAMPLE_DIR / "nodes" / "roundtrip_tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load_tools()
persist_run = _mod.persist_run


def _full_state() -> dict:
    return {
        "premise": "A pilot intercepts a signal that unravels a lie",
        "genre": "scifi",
        "cast": {"principals": [{"name": "Mara", "goal": "find the truth"}]},
        "briefs": {
            "chapters": [
                {
                    "chapter_id": 1,
                    "title": "Signal",
                    "scene_type": "proactive",
                    "eff_affect": [{"char": "Mara", "kind": "hope", "op": "open"}],
                }
            ]
        },
        "book": "## Signal\n\nThe console blinked.",
        "coherence": {
            "authored_dangling_rate": 1.0,
            "authored_opens": 1,
            "dangling": 1,
        },
        "chapter_count": 1,
    }


@pytest.mark.req("REQ-YG-020")
def test_persist_run_writes_all_artifacts(tmp_path, monkeypatch):
    monkeypatch.setenv("YAMLGRAPH_ROUNDTRIP_OUT", str(tmp_path))
    result = persist_run(_full_state())

    artifacts = result["artifacts"]
    run_dir = Path(artifacts["run_dir"])
    assert run_dir.is_dir()
    for name in (
        "manifest.json",
        "cast.json",
        "briefs.json",
        "book.md",
        "coherence.json",
    ):
        assert (run_dir / name).is_file(), f"missing artifact {name}"
    assert set(artifacts["files"]) >= {
        "manifest.json",
        "cast.json",
        "briefs.json",
        "book.md",
        "coherence.json",
    }


@pytest.mark.req("REQ-YG-020")
def test_briefs_written_full_no_truncation(tmp_path, monkeypatch):
    monkeypatch.setenv("YAMLGRAPH_ROUNDTRIP_OUT", str(tmp_path))
    state = _full_state()
    result = persist_run(state)
    briefs_path = Path(result["artifacts"]["run_dir"]) / "briefs.json"
    assert json.loads(briefs_path.read_text(encoding="utf-8")) == state["briefs"]


@pytest.mark.req("REQ-YG-020")
def test_manifest_sources_provider_model_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("YAMLGRAPH_ROUNDTRIP_OUT", str(tmp_path))
    monkeypatch.setenv("PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    result = persist_run(_full_state())
    manifest = json.loads(
        (Path(result["artifacts"]["run_dir"]) / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["provider"] == "anthropic"
    assert manifest["model"] == "claude-haiku-4-5"
    assert manifest["chapter_count"] == 1
    assert manifest["premise"] == _full_state()["premise"]


@pytest.mark.req("REQ-YG-020")
def test_manifest_marks_unset_provenance(tmp_path, monkeypatch):
    monkeypatch.setenv("YAMLGRAPH_ROUNDTRIP_OUT", str(tmp_path))
    monkeypatch.delenv("PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    result = persist_run(_full_state())
    manifest = json.loads(
        (Path(result["artifacts"]["run_dir"]) / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["provider"] == "(unset)"


@pytest.mark.req("REQ-YG-020")
def test_run_ids_distinct_for_same_premise(tmp_path, monkeypatch):
    monkeypatch.setenv("YAMLGRAPH_ROUNDTRIP_OUT", str(tmp_path))
    first = persist_run(_full_state())["artifacts"]["run_id"]
    second = persist_run(_full_state())["artifacts"]["run_id"]
    assert first != second, "microsecond stamp must distinguish same-premise draws"


@pytest.mark.req("REQ-YG-020")
@pytest.mark.parametrize("missing", ["cast", "briefs", "book", "coherence"])
def test_persist_run_raises_on_missing_stage(tmp_path, monkeypatch, missing):
    monkeypatch.setenv("YAMLGRAPH_ROUNDTRIP_OUT", str(tmp_path))
    state = _full_state()
    del state[missing]
    with pytest.raises(ValueError, match=missing):
        persist_run(state)
