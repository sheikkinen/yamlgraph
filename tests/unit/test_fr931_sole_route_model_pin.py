"""FR-931: the judge and review sole routes carry an explicit model pin.

An unpinned copilot node inherits the CLI's ambient default — a cost and
behaviour change with no diff in the repo (diary 2026-08-25). These
witnesses make the pin a tested contract: present on both routes, equal
across them, and equal to the value this repository chose deliberately.
Changing the pin therefore requires editing this test, which requires an
FR (REQ-YG-632).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTERS = {
    "judge": REPO_ROOT / ".github/skills/judge-fr/adapters/graph.yaml",
    "review": REPO_ROOT / ".github/skills/review-pr/adapters/graph.yaml",
}
PINNED_MODEL = "gpt-5.6-sol"


def _pins() -> dict[str, str]:
    """The cli_flags.model of every copilot node in each sole route."""
    pins: dict[str, str] = {}
    for route, path in ADAPTERS.items():
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        copilot_nodes = [
            node for node in config["nodes"].values() if node.get("type") == "copilot"
        ]
        assert len(copilot_nodes) == 1, f"{route}: expected one copilot node"
        pins[route] = copilot_nodes[0].get("cli_flags", {}).get("model", "")
    return pins


@pytest.mark.req("REQ-YG-632")
def test_both_sole_routes_pin_a_model() -> None:
    """AC-01: neither route may fall through to the CLI ambient default."""
    for route, pin in _pins().items():
        assert pin, f"{route} adapter has no cli_flags.model — ambient default"


@pytest.mark.req("REQ-YG-632")
def test_sole_route_pins_agree_on_the_chosen_model() -> None:
    """AC-02: the twin routes never diverge, and never drift silently."""
    pins = _pins()
    assert pins["judge"] == pins["review"], f"routes diverged: {pins}"
    assert pins["judge"] == PINNED_MODEL, f"unexpected pin: {pins['judge']}"
