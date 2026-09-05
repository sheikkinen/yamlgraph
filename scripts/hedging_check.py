#!/usr/bin/env python3
"""Detect silent branching patterns and lexical FB001 token usage in Python code.

Patterns detected:
  1. `if not X: X = broader_data`  (HG001)
  2. `X = expr or backup_expr`     (HG002)
  3. Lexical FB001 token in identifiers/comments/docstrings (FB001)

Usage:
  python scripts/hedging_check.py [directory ...]   # default: yamlgraph/
  python scripts/hedging_check.py --strict          # non-zero exit on findings

FB001 can be retained only when confession-backed in docs/confessions.md via
ALLOWLIST mapping: file:line -> CONF-XXX.
"""

from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFESSIONS_PATH = REPO_ROOT / "docs" / "confessions.md"
FB001 = "FB001"
_CONF_ID_RE = re.compile(r"^CONF-\d+$")

# Allowlist: file:lineno -> CONF-XXX.
# Add entries only after adding matching docs/confessions.md entries with Code=FB001.
ALLOWLIST: dict[str, str] = {
    "scripts/extract_copilot_events_lib.py:100": "CONF-212",
    "scripts/extract_copilot_events_lib.py:104": "CONF-213",
    "scripts/extract_copilot_events_lib.py:31": "CONF-214",
    "scripts/extract_copilot_events_lib.py:33": "CONF-215",
    "scripts/req_coverage.py:403": "CONF-216",
    "scripts/req_coverage.py:408": "CONF-217",
    "scripts/req_coverage.py:450": "CONF-218",
    "yamlgraph/a2a/message.py:120": "CONF-219",
    "yamlgraph/a2a/message.py:66": "CONF-220",
    "yamlgraph/constants.py:48": "CONF-221",
    "yamlgraph/node_factory/router_race_node.py:41": "CONF-372",
    "yamlgraph/diary/importer.py:234": "CONF-222",
    "yamlgraph/compile/edge_compiler.py:229": "CONF-223",
    "yamlgraph/error_handlers.py:1": "CONF-224",
    "yamlgraph/error_handlers.py:139": "CONF-225",
    "yamlgraph/error_handlers.py:142": "CONF-226",
    "yamlgraph/error_handlers.py:144": "CONF-227",
    "yamlgraph/error_handlers.py:154": "CONF-228",
    "yamlgraph/error_handlers.py:155": "CONF-229",
    "yamlgraph/error_handlers.py:157": "CONF-230",
    "yamlgraph/error_handlers.py:161": "CONF-231",
    "yamlgraph/linter/checks_contracts.py:216": "CONF-232",
    "yamlgraph/linter/checks_contracts.py:217": "CONF-233",
    "yamlgraph/linter/checks_semantic.py:14": "CONF-234",
    "yamlgraph/linter/checks_semantic.py:232": "CONF-235",
    "yamlgraph/linter/checks_semantic.py:244": "CONF-236",
    "yamlgraph/linter/checks_semantic.py:255": "CONF-237",
    "yamlgraph/linter/graph_linter.py:128": "CONF-238",
    "yamlgraph/linter/graph_linter.py:129": "CONF-239",
    "yamlgraph/models/node_schema.py:75": "CONF-240",
    "yamlgraph/node_factory/copilot_node.py:83": "CONF-241",
    "yamlgraph/node_factory/llm_execution.py:159": "CONF-242",
    "yamlgraph/node_factory/llm_nodes.py:130": "CONF-243",
    "yamlgraph/node_factory/llm_nodes.py:131": "CONF-244",
    "yamlgraph/node_factory/llm_nodes.py:166": "CONF-245",
    "yamlgraph/node_factory/llm_nodes.py:60": "CONF-246",
    "yamlgraph/node_factory/router_race_node.py:38": "CONF-247",
    "yamlgraph/storage/serializers.py:64": "CONF-248",
    "yamlgraph/utils/conditions.py:123": "CONF-249",
    "yamlgraph/utils/fsm/action.py:29": "CONF-250",
    "yamlgraph/utils/prompts.py:1": "CONF-251",
    "yamlgraph/utils/prompts.py:159": "CONF-252",
    "yamlgraph/utils/prompts.py:71": "CONF-253",
    "yamlgraph/utils/prompts.py:87": "CONF-254",
    "yamlgraph/tools/agent.py:64": "CONF-304",
    "yamlgraph/tools/agent.py:73": "CONF-350",
    "yamlgraph/executor_base.py:381": "CONF-351",
    "yamlgraph/utils/llm_providers.py:315": "CONF-352",
    "yamlgraph/utils/llm_factory_async.py:80": "CONF-349",
}


def _has_fb_token(text: str) -> bool:
    return "fallback" in text.lower()


def _finding_key(filepath: Path, lineno: int) -> str:
    return f"{filepath}:{lineno}"


def _normalize_path(path_str: str) -> str:
    path = Path(path_str)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _parse_allowlist_key(key: str) -> tuple[str, int] | None:
    if ":" not in key:
        return None
    path_part, line_part = key.rsplit(":", 1)
    try:
        return _normalize_path(path_part), int(line_part)
    except ValueError:
        return None


def _parse_confessions(confessions_path: Path) -> dict[str, set[tuple[str, int, str]]]:
    confessions: dict[str, set[tuple[str, int, str]]] = {}
    if not confessions_path.exists():
        return confessions

    content = confessions_path.read_text(encoding="utf-8")
    current_conf: str | None = None
    current_file: str | None = None
    current_line: int | None = None
    current_code: str | None = None

    def _save_current() -> None:
        if current_conf and current_file and current_line and current_code:
            confessions.setdefault(current_conf, set()).add(
                (current_file, current_line, current_code)
            )

    for line in content.splitlines():
        conf_match = re.match(r"###\s+(CONF-\d+)", line)
        if conf_match:
            _save_current()
            current_conf = conf_match.group(1)
            current_file = None
            current_line = None
            current_code = None
            continue

        file_match = re.search(r"\*\*File\*\*:\s*\[.*?\]\(\.\./([^)#]+)#L(\d+)", line)
        if file_match and current_conf:
            current_file = file_match.group(1)
            current_line = int(file_match.group(2))
            continue

        code_match = re.search(r"\*\*Code\*\*:\s*([A-Z0-9]+)", line)
        if code_match and current_conf:
            current_code = code_match.group(1).upper()
            continue

    _save_current()
    return confessions


def _expr_has_fb_token(expr: ast.expr) -> bool:
    for node in ast.walk(expr):
        if isinstance(node, ast.Name) and _has_fb_token(node.id):
            return True
        if isinstance(node, ast.Attribute) and _has_fb_token(node.attr):
            return True
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and _has_fb_token(node.value)
        ):
            return True
    return False


def scan_file(filepath: Path) -> list[str]:
    """Return list of hedging/FB001 findings found in file."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    findings: list[str] = []
    seen_fb_lines: set[int] = set()

    def _emit_fb001(lineno: int, surface: str, token: str) -> None:
        if lineno in seen_fb_lines:
            return
        seen_fb_lines.add(lineno)
        key = _finding_key(filepath, lineno)
        if key in ALLOWLIST:
            return
        findings.append(
            f"{key}: {FB001} lexical fallback token in {surface} (`{token}`)"
        )

    # FB001 identifiers (names, args, function/class names)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and _has_fb_token(node.id):
            _emit_fb001(node.lineno, "identifier", node.id)
        elif isinstance(node, ast.arg) and _has_fb_token(node.arg):
            _emit_fb001(node.lineno, "identifier", node.arg)
        elif isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ) and _has_fb_token(node.name):
            _emit_fb001(node.lineno, "identifier", node.name)

    # FB001 docstrings
    for node in ast.walk(tree):
        if not isinstance(
            node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            continue
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            docstring = node.body[0].value.value
            if _has_fb_token(docstring):
                _emit_fb001(node.body[0].lineno, "docstring", "fallback")

    # FB001 comments
    for token_info in tokenize.generate_tokens(io.StringIO(source).readline):
        if token_info.type == tokenize.COMMENT and _has_fb_token(token_info.string):
            _emit_fb001(token_info.start[0], "comment", "fallback")

    for node in ast.walk(tree):
        # Pattern 1: if not X: X = Y
        if isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)
                and isinstance(test.operand, ast.Name)
            ):
                var_name = test.operand.id
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name) and target.id == var_name:
                                key = _finding_key(filepath, node.lineno)
                                if key not in ALLOWLIST:
                                    findings.append(
                                        f"{key}: HG001 if not {var_name}: {var_name} = ... "
                                        f"(silent fallback — Commandment 6)"
                                    )

        # Pattern 2: X = expr or backup_expr
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.BoolOp)
            and isinstance(node.value.op, ast.Or)
            and len(node.value.values) > 1
            and any(_expr_has_fb_token(v) for v in node.value.values[1:])
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    key = _finding_key(filepath, node.lineno)
                    if key not in ALLOWLIST:
                        findings.append(
                            f"{key}: HG002 {target.id} = ... or fallback ... "
                            f"(silent fallback — Commandment 6)"
                        )

    return findings


def _validate_allowlist_for_scan(scanned_files: set[str]) -> list[str]:
    confessions = _parse_confessions(CONFESSIONS_PATH)
    errors: list[str] = []

    for key, conf_id in sorted(ALLOWLIST.items()):
        parsed = _parse_allowlist_key(key)
        if not parsed:
            errors.append(
                f"{key}: malformed ALLOWLIST key (expected file:line -> CONF-XXX)"
            )
            continue

        file_path, line_no = parsed
        if file_path not in scanned_files:
            continue

        if not _CONF_ID_RE.match(conf_id):
            errors.append(f"{key}: invalid confession id `{conf_id}`")
            continue

        confession_rows = confessions.get(conf_id)
        if confession_rows is None:
            errors.append(
                f"{key}: missing confession `{conf_id}` in docs/confessions.md"
            )
            continue

        expected = (file_path, line_no, FB001)
        if expected not in confession_rows:
            errors.append(
                f"{key}: confession `{conf_id}` does not map to {file_path}:{line_no} ({FB001})"
            )

    return errors


def main() -> int:
    directories: list[str] = []
    strict = False

    for arg in sys.argv[1:]:
        if arg == "--strict":
            strict = True
        else:
            directories.append(arg)

    if len(directories) == 0:
        directories = ["yamlgraph"]

    roots = [Path(directory) for directory in directories]
    for root in roots:
        if not root.exists():
            print(f"Directory not found: {root}", file=sys.stderr)
            return 1

    all_findings: list[str] = []
    scanned_files: set[str] = set()
    for root in roots:
        for py_file in sorted(root.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue
            scanned_files.add(_normalize_path(str(py_file)))
            all_findings.extend(scan_file(py_file))

    allowlist_errors = _validate_allowlist_for_scan(scanned_files)

    if all_findings:
        print("Hedging patterns detected (Commandment 6 — no silent fallbacks):\n")
        for finding in all_findings:
            print(f"  ⚠  {finding}")
        print(
            f"\n{len(all_findings)} finding(s). Review each — add to ALLOWLIST if intentional."
        )
    else:
        print("No hedging patterns found.")

    if allowlist_errors:
        print("\nInvalid fallback confession mappings:\n")
        for err in allowlist_errors:
            print(f"  ✗ {err}")

    if strict and (all_findings or allowlist_errors):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
