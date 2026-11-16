#!/usr/bin/env python3
"""FR-1168: fail when a Pages-rendered docs file holds active Liquid.

GitHub Pages renders docs/ with Jekyll 3.10 + Liquid 4.0.4. Any `{{` or `{%`
outside a canonical `{% raw %}…{% endraw %}` region is either a build error
(unterminated) or silently rendered as empty text. Selection mirrors Jekyll's
reader (evidence: feature-requests/FR-1168-pages-liquid-gate.md).

Exit codes: 0 clean, 1 findings, 2 unusable input (config or encoding).
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path
from typing import NamedTuple

import yaml

DOCS_ROOT = Path(__file__).resolve().parent.parent / "docs"
MARKDOWN_EXTS = {".markdown", ".mkdown", ".mkdn", ".mkd", ".md"}
SPECIAL_LEADING = (".", "_", "#", "~")
YAML_HEADER = re.compile(rb"\A---\s*\r?\n")
FRONT_MATTER = re.compile(r"\A(---\s*\n.*?\n?)^((---|\.\.\.)\s*$\n?)", re.M | re.S)
POST_NAME = re.compile(r"^(?:.+/)*(\d{2,4}-\d{1,2}-\d{1,2})-(.*)(\.[^.]+)$")

ACTIVE = re.compile(r"\{\{|\{%")
RAW_OPEN = re.compile(r"\{%\s*raw\s*%\}")
RAW_CLOSE = re.compile(r"\{%\s*endraw\s*%\}")
RAW_CLOSE_LOOSE = re.compile(r"\{%\s*endraw(?!\w).*?%\}", re.S)
RAW_CLOSE_LTRIM = re.compile(r"\{%-\s*endraw(?!\w)")

MESSAGES = {
    "L001": "active Liquid output '{{'",
    "L002": "active Liquid tag '{%'",
    "L003": "'{% raw %}' never closed",
    "L004": "non-canonical '{% endraw %}'",
}


class GateError(Exception):
    """Input the gate cannot judge; exit 2."""


class Finding(NamedTuple):
    path: str
    line: int
    code: str


def scan_text(text: str, path: str = "", line_offset: int = 0) -> list[Finding]:
    findings: list[Finding] = []

    def emit(pos: int, code: str) -> None:
        findings.append(Finding(path, text.count("\n", 0, pos) + 1 + line_offset, code))

    pos, raw_at = 0, None
    while True:
        if raw_at is None:
            m = ACTIVE.search(text, pos)
            if not m:
                break
            opener = RAW_OPEN.match(text, m.start())
            if opener:
                raw_at, pos = m.start(), opener.end()
            else:
                emit(m.start(), "L001" if m.group() == "{{" else "L002")
                pos = m.end()
            continue
        start = text.find("{%", pos)
        if start < 0:
            break
        if close := RAW_CLOSE.match(text, start):
            raw_at, pos = None, close.end()
        elif trim := RAW_CLOSE_LTRIM.match(text, start):
            emit(start, "L004")
            pos = trim.end()
        elif loose := RAW_CLOSE_LOOSE.match(text, start):
            emit(start, "L004")
            raw_at, pos = None, loose.end()
        else:
            pos = start + 2
    if raw_at is not None:
        emit(raw_at, "L003")
    return findings


def load_excludes(root: Path) -> list[str]:
    config = root / "_config.yml"
    try:
        data = yaml.safe_load(config.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise GateError(f"{config}: _config.yml missing") from e
    except (yaml.YAMLError, UnicodeDecodeError) as e:
        raise GateError(f"{config}: _config.yml malformed: {e}") from e
    if not isinstance(data, dict):
        raise GateError(f"{config}: _config.yml is not a mapping")
    excludes = data.get("exclude", [])
    if not isinstance(excludes, list):
        raise GateError(f"{config}: _config.yml 'exclude' is not a list")
    if not all(isinstance(e, str) for e in excludes):
        raise GateError(f"{config}: _config.yml 'exclude' has a non-string member")
    return excludes


def _rendered(rel: str, excludes: list[str]) -> bool:
    parts = rel.split("/")
    for i, part in enumerate(parts):
        if part.startswith(SPECIAL_LEADING):
            is_post = (
                part == "_posts" and i < len(parts) - 1 and POST_NAME.match(parts[-1])
            )
            if not is_post:
                return False
    prefixes = ["/".join(parts[: i + 1]) for i in range(len(parts))]
    return not any(fnmatch.fnmatchcase(p, pat) for p in prefixes for pat in excludes)


def select_files(root: Path, excludes: list[str]) -> list[Path]:
    selected = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if not _rendered(rel, excludes):
            continue
        if path.suffix.lower() in MARKDOWN_EXTS:
            selected.append(path)
        else:
            with path.open("rb") as fh:
                if YAML_HEADER.match(fh.read(64)):
                    selected.append(path)
    return selected


def scan_file(path: Path, root: Path) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise GateError(f"{rel}: not valid UTF-8: {e}") from e
    offset = 0
    if fm := FRONT_MATTER.match(text):
        offset = fm.group(0).count("\n")
        text = text[fm.end() :]
    return scan_text(text, rel, offset)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DOCS_ROOT)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        files = select_files(root, load_excludes(root))
        wanted = {p.resolve() for p in args.paths}
        if wanted and (root / "_config.yml") not in wanted:
            files = [f for f in files if f.resolve() in wanted]
        findings = [f for path in files for f in scan_file(path, root)]
    except GateError as e:
        print(f"check_docs_liquid: {e}", file=sys.stderr)
        return 2
    for f in findings:
        print(
            f"{root.name}/{f.path}:{f.line}: {f.code} {MESSAGES[f.code]}"
            " — wrap in {% raw %}…{% endraw %}"
        )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
