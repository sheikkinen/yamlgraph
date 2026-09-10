"""Hook-audit session adapters for the corpus census.

Slot contract per FR-892: state-dict in; discover returns item refs,
extract returns one item's text. Item = one agent session in
`.github/hooks/logs/audit.jsonl`; the extract is a compact digest
(counts + command list) so a cheap judge can label the session's shape.

source: '<audit.jsonl path>:<since ISO date>' — the date filter keeps a
batch under the graph's map cap (the full log is ~460 sessions).
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

MAX_ITEMS = 200
MIN_EVENTS = 20
MAX_COMMANDS = 60
MAX_FILES = 30
CMD_WIDTH = 110

_VERIFY = re.compile(
    r"\b(pytest|ruff|lint-imports|mypy|yamlgraph graph (lint|run|validate)|"
    r"curl|req_coverage|pre-commit run)\b"
)
_GIT = re.compile(r"\b(git|gh)\b")
_PROSE = re.compile(r"\.(md|yaml|yml|txt)$")
# CLI child sessions (judge/outsider/author adapters) log Copilot-CLI tool names
_CLI_CMD = re.compile(r'"command":\s*"((?:[^"\\]|\\.)*)"')
_CLI_PATH = re.compile(r'(?:\*\*\* (?:Add|Update) File: |"path":\s*")([^\n"]+)')
_REPO = "/yamlgraph/"


def _require(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _events(path: Path):
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def audit_discover(state: dict[str, Any]) -> list[str]:
    """Enumerate sessions with >= MIN_EVENTS events since the date filter."""
    source = _require(state, "source")
    log, _, since = source.partition(":")
    path = Path(log)
    if not path.is_file():
        raise FileNotFoundError(f"audit_discover: not a file: {path}")
    counts: Counter[str] = Counter()
    for e in _events(path):
        sid = e.get("session_id")
        if sid and e.get("ts", "") >= since:
            counts[sid] += 1
    items = sorted(f"{path}#{sid}" for sid, n in counts.items() if n >= MIN_EVENTS)
    if not items:
        raise ValueError(
            f"audit_discover: no sessions >= {MIN_EVENTS} events since '{since}'"
        )
    if len(items) > MAX_ITEMS:
        raise ValueError(
            f"audit_discover: {len(items)} sessions exceeds {MAX_ITEMS}; move the since-date later"
        )
    return items


def audit_extract(state: dict[str, Any]) -> str:
    """One session as a digest: header counts, denials, files, commands."""
    item = _require(state, "item")
    log, _, sid = item.partition("#")
    if not sid:
        raise ValueError(f"audit_extract: item lacks '#<session_id>': {item}")
    tools: Counter[str] = Counter()
    denies: Counter[str] = Counter()
    cmds: list[str] = []
    files: list[str] = []
    first = last = None
    client = "vscode"
    for e in _events(Path(log)):
        if e.get("session_id") != sid:
            continue
        ts = e.get("ts", "")
        first = first or ts
        last = ts
        tool = e.get("tool")
        if tool:
            tools[tool] += 1
        if tool in ("Bash", "Read", "Edit", "Write", "Glob", "Grep"):
            client = "copilot-cli"
        if e.get("decision") == "deny":
            denies[e.get("reason", "?")] += 1
        detail = e.get("detail") or ""
        pre = e.get("hook") == "pre-command-guard"
        if pre and tool == "run_in_terminal":
            cmd = " ".join(detail.split())[:CMD_WIDTH]
        elif pre and tool == "Bash":
            m = _CLI_CMD.search(detail)
            cmd = (
                " ".join(m.group(1).replace("\\n", " ").split())[:CMD_WIDTH]
                if m
                else ""
            )
        else:
            cmd = ""
        if cmd and (not cmds or cmds[-1] != cmd):
            cmds.append(cmd)
        f = ""
        if e.get("hook") == "post-edit-markdown-checks":
            # post-edit hooks carry the bare path; pre-guard detail is content-first
            f = detail.split(_REPO, 1)[-1].strip() if detail else ""
        elif pre and tool in ("Edit", "Write"):
            m = _CLI_PATH.search(detail.replace("\\n", "\n"))
            f = m.group(1).split(_REPO, 1)[-1].strip() if m else ""
        if f and f not in files:
            files.append(f)
    verify = sum(1 for c in cmds if _VERIFY.search(c))
    gitops = sum(1 for c in cmds if _GIT.search(c))
    prose = sum(1 for f in files if _PROSE.search(f))
    head = [
        f"session: {sid}  client: {client}",
        f"span: {first} -> {last}",
        f"events: {sum(tools.values())}  tools: {dict(tools.most_common(8))}",
        f"denials: {dict(denies) or 'none'}",
        f"files_written: {len(files)} (prose/yaml: {prose}, code: {len(files) - prose})",
        f"terminal_commands: {len(cmds)}  verification_cmds: {verify}  git_gh_cmds: {gitops}",
        "",
        "files:",
        *[f"  {f}" for f in files[:MAX_FILES]],
        "",
        "commands (deduplicated, in order):",
        *[f"  {c}" for c in cmds[:MAX_COMMANDS]],
    ]
    if len(cmds) > MAX_COMMANDS:
        head.append(f"  ... {len(cmds) - MAX_COMMANDS} more")
    return "\n".join(head)
