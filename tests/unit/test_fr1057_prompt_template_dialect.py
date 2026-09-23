"""FR-1057 tests: prompt template dialect is decided once, per message.

Covers the four defect classes the FR names:

- D1 validation and rendering disagreeing about the engine,
- D2 the validator being blind to text `str.format` will reject,
- D3 a literal brace being inexpressible in `str.format` mode,
- D4 simple-format fields silently dropped inside a Jinja message.
"""

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from yamlgraph.executor_base import format_prompt, prepare_messages
from yamlgraph.linter.graph_linter import lint_graph
from yamlgraph.utils.template import (
    extract_variables,
    is_jinja,
    scan_simple_fields,
    strip_jinja_raw_blocks,
    validate_variables,
)

REQ = "REQ-YG-685"


def write_prompt(tmp_path: Path, name: str, content: str) -> None:
    """Write a prompt YAML file into prompts/."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    (prompts_dir / f"{name}.yaml").write_text(content, encoding="utf-8")


def write_graph(tmp_path: Path, name: str, state: dict) -> Path:
    """Write a single-node graph referencing prompt `name`."""
    graph = {
        "version": "1.0",
        "name": f"fr1057-{name}",
        "state": state,
        "nodes": {
            "run": {"type": "llm", "prompt": name, "state_key": "result"},
        },
        "edges": [{"from": "START", "to": "run"}, {"from": "run", "to": "END"}],
    }
    graph_path = tmp_path / "graph.yaml"
    graph_path.write_text(yaml.safe_dump(graph), encoding="utf-8")
    return graph_path


def lint_codes(tmp_path: Path, prompt: str, content: str, state: dict) -> list[str]:
    """Lint a one-node graph around `content` and return the issue codes."""
    write_prompt(tmp_path, prompt, content)
    result = lint_graph(write_graph(tmp_path, prompt, state), tmp_path)
    return [issue.code for issue in result.issues]


# --- D-1: one discriminator, one field grammar -------------------------------


@pytest.mark.req("REQ-YG-685")
def test_is_jinja_discriminates_on_jinja_markers() -> None:
    """The sole dialect discriminator keys on `{{` and `{%` only."""
    assert is_jinja("Hello {{ name }}")
    assert is_jinja("{% for x in xs %}{% endfor %}")
    assert not is_jinja("Hello {name}")
    assert not is_jinja('Return {"chapters": []}')


@pytest.mark.req("REQ-YG-685")
def test_scan_simple_fields_returns_root_identifiers() -> None:
    """Attribute and index tails collapse to their root identifier (AC-04)."""
    assert scan_simple_fields("{name}").roots == {"name"}
    assert scan_simple_fields("{analysis.grade}").roots == {"analysis"}
    assert scan_simple_fields("{items[0]}").roots == {"items"}


@pytest.mark.req("REQ-YG-685")
def test_a_documentation_shape_is_a_field_like_any_other() -> None:
    """There is no "looks like prose" exemption (Correction 6).

    Two rounds of review killed the guesser that tried to tell an example
    apart from a field. An author who wants literal braces says so with
    `{% raw %}`; `strip_jinja_raw_blocks` removes the span before the scan.
    """
    assert scan_simple_fields("Shape: {pred: alive, args: []} and {topic}").roots == {
        "pred",
        "topic",
    }
    declared = "{{ x }} {% raw %}{pred: alive, args: []}{% endraw %} {topic}"
    assert scan_simple_fields(strip_jinja_raw_blocks(declared)).roots == {"topic"}


@pytest.mark.req("REQ-YG-685")
def test_a_type_specific_format_spec_is_still_a_required_variable() -> None:
    """Validation must not guess at the format-spec grammar (review P1).

    Python hands the spec to the value's own `__format__`, so
    `{when:%Y-%m-%d}` is valid for a `datetime`. A closed regex says
    otherwise, and the disagreement reappears as a `KeyError` at render —
    the failure C-3 requires to be loud and early.
    """
    template = "When: {when:%Y-%m-%d}"
    assert extract_variables(template) == {"when"}
    with pytest.raises(ValueError, match="when"):
        validate_variables(template, {}, "p")
    assert format_prompt(template, {"when": datetime(2026, 9, 23)}) == (
        "When: 2026-09-23"
    )


@pytest.mark.req("REQ-YG-685")
def test_format_spec_fields_are_required_variables() -> None:
    """A format spec or conversion never makes a field optional (review P2)."""
    for template, expected in [
        ("Score: {score:.2f}", {"score"}),
        ("Name: {name!r}", {"name"}),
        ("Padded: {label:>10}", {"label"}),
        ("Grouped: {total:,}", {"total"}),
        ("Nested: {value:{width}}", {"value", "width"}),
    ]:
        assert scan_simple_fields(template).roots == expected
        assert extract_variables(template) == expected


@pytest.mark.req("REQ-YG-685")
def test_format_spec_field_is_validated_before_render() -> None:
    """Validation must fail where the render would (review P2, C-3)."""
    with pytest.raises(ValueError, match="score"):
        validate_variables("Score: {score:.2f}", {}, "p")


@pytest.mark.req("REQ-YG-685")
def test_scan_simple_fields_reports_non_identifier_root() -> None:
    """A JSON shape parses as a field whose root is not an identifier (D2)."""
    scan = scan_simple_fields('Return {"chapters": []} for {topic}')
    assert scan.roots == {"topic"}
    assert scan.invalid_fields == ('"chapters"',)


@pytest.mark.req("REQ-YG-685")
def test_scan_simple_fields_reports_unmatched_brace() -> None:
    """An unmatched brace is reported, not raised (D2)."""
    scan = scan_simple_fields("unmatched { here")
    assert scan.brace_error is not None


@pytest.mark.req("REQ-YG-685")
def test_scan_recovers_variables_after_an_unmatched_brace() -> None:
    """A stray brace must not hide later fields from validation."""
    scan = scan_simple_fields("stray { then {topic}")
    assert "topic" in scan.roots


@pytest.mark.req("REQ-YG-685")
def test_extract_variables_uses_root_identifiers() -> None:
    """Variable extraction inherits the formatter's field grammar (AC-04)."""
    assert extract_variables("Grade: {analysis.grade}") == {"analysis"}
    assert extract_variables('Return {"chapters": []} for {topic}') == {"topic"}


# --- D-2: validation is per message ------------------------------------------


@pytest.mark.req("REQ-YG-685")
def test_variable_used_only_in_system_is_still_required(tmp_path: Path) -> None:
    """Per-message validation must not narrow the required set (AC-03)."""
    write_prompt(
        tmp_path,
        "split",
        "system: You plan for {topic}.\nuser: Go.\n",
    )
    with pytest.raises(ValueError, match="topic"):
        prepare_messages("split", {}, prompts_dir=tmp_path / "prompts")


@pytest.mark.req("REQ-YG-685")
def test_variable_used_only_in_a_segment_is_still_required(tmp_path: Path) -> None:
    """Every `system_segments[*].content` is validated (AC-03)."""
    write_prompt(
        tmp_path,
        "segmented",
        "system_segments:\n"
        "  - content: Static preamble.\n"
        "  - content: Topic is {topic}.\n"
        "user: Go.\n",
    )
    with pytest.raises(ValueError, match="topic"):
        prepare_messages("segmented", {}, prompts_dir=tmp_path / "prompts")


@pytest.mark.req("REQ-YG-685")
def test_jinja_system_does_not_bless_a_simple_format_user(tmp_path: Path) -> None:
    """D1: the concatenation used to hide the user message's real dialect."""
    write_prompt(
        tmp_path,
        "d1",
        "system: You are a planner for {{ topic }}.\n"
        'user: |\n  Return {"chapters": []}\n',
    )
    scan = scan_simple_fields('Return {"chapters": []}\n')
    assert scan.invalid_fields  # the renderer will reject this text
    with pytest.raises(ValueError, match="E013|literal|brace|format field"):
        prepare_messages("d1", {"topic": "AI"}, prompts_dir=tmp_path / "prompts")


# --- D-3 / D-2 at lint time: E013 --------------------------------------------


@pytest.mark.req("REQ-YG-685")
def test_e013_fires_for_literal_json_in_a_simple_format_message(
    tmp_path: Path,
) -> None:
    """AC-05: the D1 user message is caught before execution."""
    codes = lint_codes(
        tmp_path,
        "e013",
        'system: Plan.\nuser: |\n  Return {"chapters": []} for {topic}\n',
        {"topic": "str"},
    )
    assert "E013" in codes


@pytest.mark.req("REQ-YG-685")
def test_e013_fix_text_names_both_escapes(tmp_path: Path) -> None:
    """AC-13's remedies must reach the author through the finding."""
    write_prompt(tmp_path, "e013fix", 'user: |\n  Return {"chapters": []}\n')
    result = lint_graph(write_graph(tmp_path, "e013fix", {}), tmp_path)
    fix = next(i.fix or "" for i in result.issues if i.code == "E013")
    assert "raw" in fix


@pytest.mark.req("REQ-YG-685")
def test_e013_does_not_fire_for_well_formed_fields(tmp_path: Path) -> None:
    """AC-05: attribute and index fields are well-formed `str.format` templates.

    Well-formed, not necessarily runtime-valid: `{a.b}` is a getattr in
    `str.format`, so it still fails on a dict value. That is a separate
    defect class and E013 deliberately stays silent about it.
    """
    codes = lint_codes(
        tmp_path,
        "valid",
        "user: |\n  {topic} {analysis.grade} {items[0]}\n",
        {"topic": "str", "analysis": "dict", "items": "list"},
    )
    assert "E013" not in codes


@pytest.mark.req("REQ-YG-685")
def test_e013_does_not_fire_for_a_jinja_message(tmp_path: Path) -> None:
    """AC-06: literal braces are ordinary text once the message is Jinja."""
    codes = lint_codes(
        tmp_path,
        "jinjajson",
        'user: |\n  Return {"chapters": []} for {{ topic }}\n',
        {"topic": "str"},
    )
    assert "E013" not in codes


# --- D-4 at lint time: E014 --------------------------------------------------


@pytest.mark.req("REQ-YG-685")
def test_e014_fires_for_simple_fields_in_a_jinja_message(tmp_path: Path) -> None:
    """AC-07: Jinja never substitutes `{var}`; it passes it through."""
    write_prompt(
        tmp_path,
        "e014",
        "user: |\n"
        "  ORIGINAL: {synopsis}\n"
        "  GRADE: {analysis.grade}\n"
        "  {% for w in analysis.weaknesses %}- {{ w }}\n  {% endfor %}\n",
    )
    result = lint_graph(
        write_graph(tmp_path, "e014", {"synopsis": "str", "analysis": "dict"}),
        tmp_path,
    )
    e014 = [i for i in result.issues if i.code == "E014"]
    assert e014, "E014 must catch the silent-drop class"
    assert "synopsis" in e014[0].message
    assert "analysis" in e014[0].message


@pytest.mark.req("REQ-YG-685")
def test_e014_does_not_fire_for_literal_json_or_raw_blocks(tmp_path: Path) -> None:
    """AC-07: only identifier-rooted bare fields are silent drops.

    The raw block here holds `{state.field}` — an identifier root that would
    otherwise be reported, so this fixture fails if raw blocks are ignored.
    """
    codes = lint_codes(
        tmp_path,
        "rawblock",
        "user: |\n"
        '  Shape: {"chapters": []}\n'
        "  Use {% raw %}{state.field}{% endraw %} for state references.\n"
        "  Topic: {{ topic }}\n",
        {"topic": "str"},
    )
    assert "E014" not in codes


@pytest.mark.req("REQ-YG-685")
def test_dialect_checks_ignore_non_message_fields(tmp_path: Path) -> None:
    """AC-10: `metadata.description` is never rendered, so it is never a defect."""
    codes = lint_codes(
        tmp_path,
        "descr",
        "metadata:\n"
        '  description: |\n    Emits {"chapters": []} and {stray\n'
        "user: Topic is {{ topic }}\n",
        {"topic": "str"},
    )
    assert "E013" not in codes
    assert "E014" not in codes


@pytest.mark.req("REQ-YG-685")
def test_w024_is_retired(tmp_path: Path) -> None:
    """AC-08: the mixed-syntax warning is superseded by E014."""
    from yamlgraph.linter import checks_prompts

    assert not hasattr(checks_prompts, "check_mixed_template_syntax")
    codes = lint_codes(
        tmp_path,
        "mixed",
        "user: File {fr_path}; reviewer {{ reviewer }}\n",
        {"fr_path": "str", "reviewer": "str"},
    )
    assert "W024" not in codes
    assert "E014" in codes
