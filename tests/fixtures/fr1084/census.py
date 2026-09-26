"""FR-1084 census: every documented `yamlgraph graph run` invocation vs its graph's input schema.

Regenerate the committed evidence with:
    python tests/fixtures/fr1084/census.py
"""

from __future__ import annotations

import csv
import io
import logging
import re
import shlex
import sys
from contextlib import chdir
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = Path(__file__).resolve().parent
INVOCATIONS_PATH = FIXTURE_DIR / "invocations.tsv"
EXCLUSIONS_PATH = FIXTURE_DIR / "exclusions.tsv"

COMMAND = "yamlgraph graph run"
MECHANICAL_REASONS = (
    "missing-var-file",
    "placeholder",
    "shell-variable",
    "unresolvable-graph",
)
STOP_TOKENS = {"|", "||", "&&", ";", "&", ">", ">>", "<", "2>&1", "2>", ")", "`"}
COLUMNS = ("source", "line", "graph", "kind", "key", "status", "reason", "fr")


@dataclass(frozen=True)
class Row:
    source: str
    line: int
    graph: str
    kind: str
    key: str
    status: str
    reason: str = ""
    fr: str = ""


def scope_files() -> list[Path]:
    files = [REPO_ROOT / "README.md", REPO_ROOT / "examples/demos/demo.sh"]
    files += sorted((REPO_ROOT / "reference").rglob("*.md"))
    files += sorted((REPO_ROOT / "examples").rglob("README.md"))
    return sorted({f for f in files if f.is_file()})


def _joined_lines(text: str) -> list[tuple[int, str]]:
    """Join trailing-backslash continuations; keep the first line number."""
    joined: list[tuple[int, str]] = []
    buffer, start = "", 0
    for number, line in enumerate(text.splitlines(), start=1):
        if not buffer:
            start = number
        if line.rstrip().endswith("\\"):
            buffer += line.rstrip()[:-1] + " "
            continue
        joined.append((start, buffer + line))
        buffer = ""
    if buffer:
        joined.append((start, buffer))
    return joined


def _tokens(segment: str) -> list[str]:
    lexer = shlex.shlex(segment, posix=True, punctuation_chars="|&;<>()`")
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return segment.split()


def _is_placeholder(text: str) -> bool:
    return any(mark in text for mark in ("<", ">", "...", "…"))


def _parse_invocation(
    segment: str,
) -> tuple[str | None, list[tuple[str, str]], tuple[str, ...]]:
    graph: str | None = None
    items: list[tuple[str, str]] = []
    tools: list[str] = []
    words = _tokens(segment)
    index = 0
    while index < len(words):
        word = words[index]
        if word in STOP_TOKENS:
            break
        following = words[index + 1] if index + 1 < len(words) else ""
        if word == "--tool":
            tools.append(following)
            index += 2
            continue
        if word in ("--var", "--var-file"):
            items.append((word, following))
            index += 2
            continue
        if word.startswith(("--var=", "--var-file=")):
            flag, value = word.split("=", 1)
            items.append((flag, value))
        elif not word.startswith("-") and graph is None:
            graph = word
        index += 1
    return graph, items, tuple(tools)


def _key(value: str) -> str:
    return value.split("=", 1)[0]


@cache
def _accepted_keys(graph: str, tools: tuple[str, ...]) -> frozenset[str] | str:
    """Compiled input-schema keys, or the load/compile error text."""
    from yamlgraph.compile.graph_loader import compile_graph, load_graph_config
    from yamlgraph.tools.tool_slots import parse_tool_bindings

    logging.disable(logging.CRITICAL)
    try:
        with chdir(REPO_ROOT):
            bindings = parse_tool_bindings(list(tools))
            config = load_graph_config(graph, tool_bindings=bindings or None)
            app = compile_graph(config).compile()
        return frozenset(app.get_input_jsonschema()["properties"])
    except Exception as exc:  # census records the failure as a finding row
        text = f"{type(exc).__name__}: {exc}".replace(f"{REPO_ROOT}/", "")
        return text.splitlines()[0][:160]
    finally:
        logging.disable(logging.NOTSET)


def _var_file_keys(path: str) -> list[str] | None:
    from yamlgraph.cli.helpers import load_var_file

    target = REPO_ROOT / path
    if not target.is_file():
        return None
    return sorted(load_var_file(str(target)))


def _rows_for(source: str, line: int, segment: str) -> list[Row]:
    graph, items, tools = _parse_invocation(segment)
    graph = graph or ""
    pairs: list[tuple[str, str]] = []
    for flag, value in items:
        if flag == "--var":
            pairs.append(("--var", _key(value)))
        elif _is_placeholder(value) or "$" in value:
            pairs.append(("--var-file", value))
        else:
            keys = _var_file_keys(value)
            pairs += (
                [("--var-file", k) for k in keys]
                if keys is not None
                else [("--var-file", "-")]
            )
    missing_files = {
        value
        for flag, value in items
        if flag == "--var-file"
        and not (_is_placeholder(value) or "$" in value)
        and _var_file_keys(value) is None
    }

    rows: list[Row] = []
    for kind, key in dict.fromkeys(pairs):
        base = {
            "source": source,
            "line": line,
            "graph": graph,
            "kind": kind,
            "key": key,
        }
        if kind == "--var-file" and key == "-" and missing_files:
            rows.append(Row(**base, status="EXCLUDED", reason="missing-var-file"))
        elif _is_placeholder(graph) or _is_placeholder(key):
            rows.append(Row(**base, status="EXCLUDED", reason="placeholder"))
        elif "$" in graph or "$" in key:
            rows.append(Row(**base, status="EXCLUDED", reason="shell-variable"))
        elif not graph or not (REPO_ROOT / graph).is_file():
            rows.append(Row(**base, status="EXCLUDED", reason="unresolvable-graph"))
        else:
            accepted = _accepted_keys(graph, tools)
            if isinstance(accepted, str):
                rows.append(Row(**base, status="FINDING", reason=accepted))
            elif key in accepted:
                rows.append(Row(**base, status="PASS"))
            else:
                rows.append(Row(**base, status="FINDING", reason="unknown-key"))
    return rows


def extract() -> list[Row]:
    rows: list[Row] = []
    for path in scope_files():
        source = path.relative_to(REPO_ROOT).as_posix()
        for line, text in _joined_lines(path.read_text(encoding="utf-8")):
            for match in re.finditer(re.escape(COMMAND), text):
                rows += _rows_for(source, line, text[match.end() :])
    return rows


def load_exclusions() -> dict[tuple[str, str, str], tuple[str, str]]:
    """(source, graph, key) -> (reason, FR) for findings excluded by a filed FR."""
    reader = csv.DictReader(
        io.StringIO(EXCLUSIONS_PATH.read_text(encoding="utf-8")), delimiter="\t"
    )
    return {(r["source"], r["graph"], r["key"]): (r["reason"], r["fr"]) for r in reader}


def resolve(rows: list[Row]) -> list[Row]:
    """Findings become EXCLUDED with the manifest's reason and FR, else stay FINDING."""
    manifest = load_exclusions()
    resolved = []
    for row in rows:
        entry = manifest.get((row.source, row.graph, row.key))
        if row.status == "FINDING" and entry:
            row = replace(row, status="EXCLUDED", reason=entry[0], fr=entry[1])
        resolved.append(row)
    return resolved


def render(rows: list[Row]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(COLUMNS)
    for row in rows:
        # "-" for empty cells: a trailing tab is trailing whitespace to pre-commit.
        writer.writerow([getattr(row, column) or "-" for column in COLUMNS])
    return buffer.getvalue()


if __name__ == "__main__":
    sys.path.insert(0, str(REPO_ROOT))
    INVOCATIONS_PATH.write_text(render(resolve(extract())), encoding="utf-8")
    print(f"wrote {INVOCATIONS_PATH.relative_to(REPO_ROOT)}")
