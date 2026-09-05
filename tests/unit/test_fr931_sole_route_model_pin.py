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
    """The cli_flags.model of the Copilot-CLI node in each sole route.

    FR-960 adds an opt-in ``backend: claude`` node to the judge route; the
    pin invariant applies to the default Copilot-CLI node (exactly one per
    route), and every other copilot node must still carry its own explicit,
    non-empty model (``test_every_copilot_node_is_pinned``).
    """
    pins: dict[str, str] = {}
    for route, path in ADAPTERS.items():
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        cli_nodes = [
            node
            for node in config["nodes"].values()
            if node.get("type") == "copilot" and (node.get("backend") or "cli") == "cli"
        ]
        assert len(cli_nodes) == 1, f"{route}: expected one Copilot-CLI copilot node"
        pins[route] = cli_nodes[0].get("cli_flags", {}).get("model", "")
    return pins


@pytest.mark.req("REQ-YG-632")
def test_every_copilot_node_is_pinned() -> None:
    """No copilot node on either route may inherit an ambient default model."""
    for route, path in ADAPTERS.items():
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        for name, node in config["nodes"].items():
            if node.get("type") == "copilot":
                assert node.get("cli_flags", {}).get("model"), (
                    f"{route}:{name} unpinned"
                )


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
