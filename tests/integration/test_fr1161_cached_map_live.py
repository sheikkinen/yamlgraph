"""FR-1161 AC-07: cached_map writes the shared prompt cache once.

Two graphs run the same 4 items through real ``claude-haiku-5-5`` calls:
a control ``type: map`` and a ``type: cached_map``. Each variant has its own
nonce-prefixed ``cache: true`` system segment. The gate applies to the
cached_map only (FR-1161 § Live witness protocol); the control is context.
A skip is owed, never a pass.
"""

import os
import textwrap
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv

from yamlgraph.compile.graph_loader import load_and_compile

load_dotenv()
MODEL = "claude-haiku-5-5"

WORKER = textwrap.dedent(
    f'''
    from langchain_core.messages import HumanMessage

    from yamlgraph.executor_base import _build_system_message_from_segments
    from yamlgraph.utils.llm_factory import create_llm


    def ask(state):
        system = _build_system_message_from_segments(
            [{{"content": state["prefix"], "cache": True}}], {{}}, None, "anthropic"
        )
        llm = create_llm(provider="anthropic", model="{MODEL}", max_tokens=16)
        reply = llm.invoke([system, HumanMessage(content=state["item"])])
        return {{"out": {{"usage": dict(reply.usage_metadata)}}}}
    '''
)

GRAPH = """
name: fr1161_live
config:
  max_concurrency: 4
state:
  items: list
  prefix: str
  usage: list
tools:
  ask:
    type: python
    path: worker.py
    function: ask
nodes:
  fan:
    type: {kind}
    over: "{{state.items}}"
    as: item
    node:
      type: python
      tool: ask
      state_key: out
    collect: usage
edges:
  - {{from: START, to: fan}}
  - {{from: fan, to: END}}
"""


def _prefix(kind: str) -> str:
    lines = [f"[fr1161 {kind} {uuid.uuid4().hex}] You are a terse rules engine."]
    lines += [
        f"Rule {i}: When a player declares action number {i}, check the inventory, "
        f"the location graph and the faction ledger, then answer with exactly one "
        f"short sentence naming the outcome and the cost."
        for i in range(1, 51)
    ]
    return "\n".join(lines)


def _write(details: dict) -> int:
    split = (details.get("ephemeral_5m_input_tokens") or 0) + (
        details.get("ephemeral_1h_input_tokens") or 0
    )
    return max(details.get("cache_creation") or 0, split)


def _run(tmp_path: Path, kind: str) -> list[dict]:
    d = tmp_path / kind
    d.mkdir()
    (d / "worker.py").write_text(WORKER, encoding="utf-8")
    (d / "graph.yaml").write_text(GRAPH.format(kind=kind), encoding="utf-8")
    app = load_and_compile(str(d / "graph.yaml")).compile()
    items = [f"Action {n}." for n in (3, 7, 11, 19)]
    out = app.invoke({"items": items, "prefix": _prefix(kind)}, {"max_concurrency": 4})
    assert not out.get("usage_failures"), out.get("usage_failures")
    return [r["usage"] for r in sorted(out["usage"], key=lambda r: r["_map_index"])]


@pytest.mark.req("REQ-YG-728")
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set (owed)"
)
def test_cached_map_writes_shared_prefix_once_live(tmp_path):
    records = {kind: _run(tmp_path, kind) for kind in ("map", "cached_map")}
    for kind, rows in records.items():
        for i, usage in enumerate(rows):
            print(f"{kind}[{i}] usage_metadata:", usage)
        details = [u.get("input_token_details") or {} for u in rows]
        writes = sum(_write(d) for d in details)
        reads = sum(d.get("cache_read") or 0 for d in details)
        print(f"{kind} totals: writes={writes} reads={reads}")

    details = [u.get("input_token_details") or {} for u in records["cached_map"]]
    p = _write(details[0])
    assert p > 0, "warm call wrote no cache (P missing)"
    assert (details[0].get("cache_read") or 0) == 0
    writes = sum(_write(d) for d in details)
    reads = sum(d.get("cache_read") or 0 for d in details)
    assert p <= writes <= 1.5 * p
    assert reads >= 2.5 * p
