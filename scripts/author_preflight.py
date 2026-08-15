"""FR-806: mechanical pre-flight for authoring briefs (sole route).

Dry-runs a task brief before scripts/author.sh spawns the copilot CLI
backend. Three checks, all static — the brief is untrusted external
input and no brief-controlled text is ever executed, and no LLM call
exists in this path:

1. Premises: workspace-relative paths the brief asserts as existing
   inputs (fixtures, servers, prerequisites) must exist. Paths named as
   outputs the run will create are not premises.
2. Commands: validation-section command executables must statically
   resolve (env-assignment prefixes, ``python -m``, ``./relative-script``).
3. Budget: 2+ live full-pipeline ``yamlgraph graph run`` smokes (or 3+
   narrower graph-run smokes) warn against the backend's 900s ceiling.

Premise violations exit 64 quoting the violated line; budget findings
are advisory.
"""

from __future__ import annotations

import argparse
import re
import shlex
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

EXIT_PREMISE = 64
CEILING_S = 900

# A workspace-relative path token: has a slash and a file extension.
_PATH_RE = re.compile(r"(?<![\w/])((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)")

# Line classifiers (case-insensitive). Output wins over input: on
# ambiguity we fail open — a false failure kills a legitimate run.
_INPUT_MARKERS = re.compile(
    r"existing|exists|fixture|prerequisite|serves?\b|against\b|\binput\b|located at",
    re.IGNORECASE,
)
_OUTPUT_MARKERS = re.compile(
    r"creat|writ|author|generat|produc|output|deliverabl|emit|\bnew\b",
    re.IGNORECASE,
)

_VALIDATION_HEADING = re.compile(r"^#+\s.*validat", re.IGNORECASE)
_HEADING = re.compile(r"^#+\s")
_ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_GRAPH_RUN = re.compile(r"yamlgraph\s+graph\s+run\s+(\S+)")


@dataclass
class PreflightResult:
    ok: bool = True
    checked: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _validation_section(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        if _VALIDATION_HEADING.match(line):
            in_section = True
            continue
        if in_section and _HEADING.match(line):
            in_section = False
        if in_section:
            out.append(line)
    return "\n".join(out)


def _fenced_commands(section: str) -> list[str]:
    commands: list[str] = []
    in_fence = False
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and stripped and not stripped.startswith("#"):
            commands.append(stripped)
    return commands


def check_premises(text: str, workdir: Path, result: PreflightResult) -> None:
    for line in text.splitlines():
        if _OUTPUT_MARKERS.search(line):
            continue  # output the run creates — not a premise
        if not _INPUT_MARKERS.search(line):
            continue  # neutral mention — fail open
        for token in _PATH_RE.findall(line):
            if (workdir / token).exists():
                result.checked.append(f"premise: {token} exists")
            else:
                result.ok = False
                result.violations.append(
                    f"premise: {token} missing — violated line: {line.strip()!r}"
                )


def _resolve_executable(command: str, workdir: Path) -> tuple[str, bool] | None:
    """Statically resolve the executable of one command line.

    Returns (executable, resolved) or None when the line cannot be
    inspected statically (substitutions are never evaluated).
    """
    if "$(" in command or "`" in command:
        head = command.split()[0] if command.split() else ""
        if "$(" in head or "`" in head:
            return None  # executable itself is dynamic — fail open
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return None
    while tokens and _ENV_ASSIGN.match(tokens[0]):
        tokens.pop(0)
    if not tokens:
        return None
    head = tokens[0]
    if head.startswith("./"):
        target = workdir / head[2:]
        return head, target.is_file()
    if "/" in head:
        return head, Path(head).is_file()
    return head, shutil.which(head) is not None


def check_commands(text: str, workdir: Path, result: PreflightResult) -> None:
    for command in _fenced_commands(_validation_section(text)):
        resolved = _resolve_executable(command, workdir)
        if resolved is None:
            continue
        head, ok = resolved
        if ok:
            result.checked.append(f"command: {head} resolves")
        else:
            result.ok = False
            result.violations.append(
                f"command: executable {head!r} does not resolve — "
                f"violated line: {command!r}"
            )


def check_budget(text: str, result: PreflightResult) -> None:
    section = _validation_section(text)
    full = narrow = 0
    for match in _GRAPH_RUN.finditer(section):
        if match.group(1).endswith("graph.yaml"):
            full += 1
        else:
            narrow += 1
    if full >= 2 or (full + narrow) >= 3:
        result.warnings.append(
            f"budget: {full} full-pipeline + {narrow} narrower live graph-run "
            f"smokes risk the backend's {CEILING_S}s ceiling — consider a "
            f"resumed validation-only brief"
        )


def run_preflight(brief_path: Path, workdir: Path) -> PreflightResult:
    text = Path(brief_path).read_text(encoding="utf-8")
    result = PreflightResult()
    check_premises(text, workdir, result)
    check_commands(text, workdir, result)
    check_budget(text, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--workdir", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    result = run_preflight(args.brief, args.workdir)
    print(f"author.sh pre-flight: {args.brief}")
    for line in result.checked:
        print(f"  \u2713 {line}")
    for line in result.warnings:
        print(f"  \u26a0 {line}")
    for line in result.violations:
        print(f"  \u2717 {line}")
    if not result.ok:
        print("pre-flight failed: fix the brief or use --no-preflight", file=sys.stderr)
        return EXIT_PREMISE
    return 0


if __name__ == "__main__":
    sys.exit(main())
