"""FR-1057 AC-09/AC-11: the committed live incident, after repair."""

from pathlib import Path

import pytest

from yamlgraph.executor_base import prepare_messages

# Reads a committed example prompt rather than a fixture: the claim is
# about that artifact, not about a copy of it.
pytestmark = pytest.mark.process

REQ = "REQ-YG-686"


@pytest.mark.req("REQ-YG-686")
def test_dungeon_master_plot_plan_system_message_renders() -> None:
    """The live D1 crash, condemned (AC-11).

    Before repair, `prepare_messages` raised `KeyError '\\n  "agents"'`: the
    system message is a literal JSON shape with no Jinja syntax, so it was
    rendered by `str.format` while the concatenation with the Jinja user
    message told the validator it was Jinja.
    """
    prompts_dir = (
        Path(__file__).resolve().parents[2] / "examples/dungeon_master/prompts"
    )
    messages, _, _ = prepare_messages(
        "author_plot_plan",
        {"premise": "A clan mourns a living man", "flaws": []},
        prompts_dir=prompts_dir,
    )

    system_text = messages[0].content
    assert '"agents"' in system_text
    assert "{% raw %}" not in system_text
    assert "A clan mourns a living man" in messages[-1].content
