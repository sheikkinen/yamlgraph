"""FR-1169: Haiku 5.5 is the Anthropic default and no live graph pins Haiku 4.5.

Records (demo logs, proofs, run evidence) keep the id they ran on; only
graph and prompt YAML under ``examples/`` and ``graphs/`` are checked here.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import yamlgraph.config

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
OLD_HAIKU = "claude-haiku-4-5"
NEW_HAIKU = "claude-haiku-5-5"


@pytest.mark.req("REQ-YG-043")
def test_anthropic_default_is_haiku_5_5(monkeypatch):
    """With ANTHROPIC_MODEL unset, the Anthropic default is Haiku 5.5."""
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    try:
        config = importlib.reload(yamlgraph.config)
        assert config.DEFAULT_MODELS["anthropic"] == NEW_HAIKU
    finally:
        monkeypatch.undo()
        importlib.reload(yamlgraph.config)


@pytest.mark.req("REQ-YG-043")
def test_no_live_graph_or_prompt_pins_haiku_4_5():
    """No graph or prompt YAML under examples/ or graphs/ names Haiku 4.5."""
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for root in ("examples", "graphs")
        for path in sorted((REPO_ROOT / root).rglob("*.yaml"))
        if OLD_HAIKU in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
