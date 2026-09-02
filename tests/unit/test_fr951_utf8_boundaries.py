"""FR-951 witnesses: first-party text boundaries must declare UTF-8.

These run the loaders inside a Windows subprocess whose preferred encoding is
the host ANSI code page (``PYTHONUTF8=0``). A boundary that inherits that codec
either raises on ``U+201D`` (whose third UTF-8 byte, ``0x9d``, is undefined in
cp1252) or silently decodes ``U+20AC`` as mojibake.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "fr951"
GRAPH = FIXTURES / "unicode_graph.yaml"
PROMPT = FIXTURES / "unicode_prompt.yaml"
SCHEMA = FIXTURES / "unicode_schema.yaml"

CURLY_QUOTE = "\u201d"
EURO = "\u20ac"

# Documented aliases for the Western-European Windows ANSI code page.
CP1252_ALIASES = {"cp1252", "windows1252", "1252"}

pytestmark = [
    pytest.mark.req("REQ-YG-638"),
    pytest.mark.skipif(
        sys.platform != "win32",
        reason="FR-951: the inherited-codec boundary only exists on Windows",
    ),
]

# Reports every boundary independently so one inherited codec does not mask the
# others, and emits ASCII-only JSON so the probe's own stdout codec is not a
# variable in the result.
_PROBE = r"""
import json
import locale
import sys
from pathlib import Path

import yaml

graph_path, prompt_path, schema_path = sys.argv[1:4]
report = {"encoding": locale.getencoding()}


def record(key, fn):
    try:
        report[key] = {"ok": True, "value": fn()}
    except Exception as exc:
        report[key] = {"ok": False, "error": "{}: {}".format(type(exc).__name__, exc)}


def reference(path, *keys):
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    for key in keys:
        data = data[key]
    return data


def graph():
    from yamlgraph.compile.graph_loader import load_graph_config

    return load_graph_config(graph_path).description


def prompt():
    from yamlgraph.utils.prompts import load_prompt

    content = load_prompt(
        "unicode_prompt",
        prompts_dir=Path("."),
        graph_path=Path(graph_path),
        prompts_relative=True,
    )
    return [content["system"], content["user"]]


def schema():
    from yamlgraph.schema_loader import load_schema_from_yaml

    fields = load_schema_from_yaml(schema_path).model_fields
    return [fields["quote"].description, fields["price"].description]


record("graph", graph)
record("prompt", prompt)
record("schema", schema)
record("graph_reference", lambda: reference(graph_path, "description"))
record(
    "prompt_reference",
    lambda: [reference(prompt_path, "system"), reference(prompt_path, "user")],
)
record(
    "schema_reference",
    lambda: [
        reference(schema_path, "schema", "fields", "quote", "description"),
        reference(schema_path, "schema", "fields", "price", "description"),
    ],
)
print(json.dumps(report))
"""


@pytest.fixture(scope="module")
def probe_report() -> dict:
    """Load the three fixtures in a subprocess with the host codec restored."""
    env = dict(os.environ)
    env["PYTHONUTF8"] = "0"
    env.pop("PYTHONIOENCODING", None)

    proc = subprocess.run(
        [sys.executable, "-c", _PROBE, str(GRAPH), str(PROMPT), str(SCHEMA)],
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )
    stderr = proc.stderr.decode("utf-8", "backslashreplace")
    assert proc.returncode == 0, f"boundary probe failed:\n{stderr}"

    report = json.loads(proc.stdout.decode("utf-8"))
    encoding = report["encoding"].lower().replace("-", "").replace("_", "")
    assert encoding in CP1252_ALIASES, (
        "FR-951 witness precondition unmet: locale.getencoding() reported "
        f"{report['encoding']!r}, so the inherited-codec defect cannot be "
        "reproduced on this host"
    )
    return report


def _value(report: dict, key: str):
    entry = report[key]
    assert entry["ok"], f"{key} boundary inherited the host codec: {entry.get('error')}"
    return entry["value"]


def test_graph_loader_declares_utf8(probe_report: dict) -> None:
    description = _value(probe_report, "graph")
    assert CURLY_QUOTE in description
    assert EURO in description


def test_prompt_loader_declares_utf8(probe_report: dict) -> None:
    system, user = _value(probe_report, "prompt")
    assert CURLY_QUOTE in system
    assert EURO in system
    assert EURO in user


def test_schema_loader_declares_utf8(probe_report: dict) -> None:
    quote, price = _value(probe_report, "schema")
    assert CURLY_QUOTE in quote
    assert EURO in price


@pytest.mark.parametrize(
    "loaded_key,reference_key",
    [
        ("graph", "graph_reference"),
        ("prompt", "prompt_reference"),
        ("schema", "schema_reference"),
    ],
)
def test_no_silent_corruption(
    probe_report: dict, loaded_key: str, reference_key: str
) -> None:
    """A cp1252 decode of UTF-8 usually succeeds and is usually wrong."""
    assert _value(probe_report, loaded_key) == _value(probe_report, reference_key)
