#!/usr/bin/env python3
"""Weekly recap renderer (FR-821, REQ-YG-604).

Runs the recap demo graph (examples/demos/recap — unmodified, CAP-195)
against a repository and renders workstreams/orphans/hotspots into
``docs/recaps/<ISO-week>.md``.

Quiet weeks are detected deterministically BEFORE any LLM call: the
substantive commit window excludes prior recap automation commits
(subject starts with ``docs(recap): weekly recap`` and changed paths all
under ``docs/recaps/``), so the feature's own weekly merge never makes
the next week noisy.

Usage:
    python scripts/weekly_recap.py --repo-path . --since "1 week ago" \
        --output-dir docs/recaps
    python scripts/weekly_recap.py --dry-run   # print, write nothing
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = REPO_ROOT / "examples" / "demos" / "recap" / "graph.yaml"
RECAP_SUBJECT_PREFIX = "docs(recap): weekly recap"
RECAPS_DIR_PREFIX = "docs/recaps/"
GIT = shutil.which("git") or "git"

SECTIONS = ("workstreams", "orphans", "hotspots")


def iso_week(d: date) -> str:
    """ISO week label, %G-W%V (ISO year, not calendar year)."""
    return f"{d.strftime('%G')}-W{d.strftime('%V')}"


def _git(repo_path: str, *args: str) -> str:
    result = subprocess.run(  # noqa: S603
        [GIT, "-C", repo_path, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def substantive_commits(repo_path: str, since: str) -> list[str]:
    """Commits in the window minus recap-only automation commits.

    A commit is recap-only when its subject starts with
    ``docs(recap): weekly recap`` AND every changed path is under
    ``docs/recaps/``. Subject match alone is not enough — a commit that
    also touches code is substantive.
    """
    out = _git(repo_path, "log", f"--since={since}", "--pretty=format:%H|%s")
    commits = [line for line in out.splitlines() if line.strip()]
    kept: list[str] = []
    for line in commits:
        sha, subject = line.split("|", 1)
        if subject.startswith(RECAP_SUBJECT_PREFIX):
            paths = [
                p
                for p in _git(
                    repo_path, "show", "--name-only", "--pretty=format:", sha
                ).splitlines()
                if p.strip()
            ]
            if paths and all(p.startswith(RECAPS_DIR_PREFIX) for p in paths):
                continue
        kept.append(line)
    return kept


def _invoke_graph(repo_path: str, since: str) -> dict:
    from yamlgraph.compile.graph_loader import load_and_compile

    graph = load_and_compile(str(GRAPH_PATH))
    compiled = graph.compile()
    return compiled.invoke({"since": since, "repo_path": repo_path})


def run_recap_graph(repo_path: str, since: str) -> dict:
    """Invoke the recap graph (one LLM node) and return its recap state.

    Raises on any node error: a failed synthesize still yields a
    shapely partial recap (orphans bypass the model, FR-704) — publishing
    it would be a plausible wrong artifact, not a recap.
    """
    result = _invoke_graph(repo_path, since)
    errors = result.get("errors") or []
    if errors:
        raise RuntimeError(f"recap graph reported node errors: {errors}")
    return result["recap"]


def render_markdown(recap: object, week: str) -> str:
    """Render recap state into the frozen section contract.

    Normalizes at the boundary: accepts a dict or a Pydantic model.
    Empty sections render an explicit ``(none)`` — a blank section is
    indistinguishable from a render failure.
    """
    if hasattr(recap, "model_dump"):
        recap = recap.model_dump()
    if not isinstance(recap, dict):
        raise TypeError(f"recap state must be dict or model, got {type(recap)}")

    lines = [f"# Weekly Recap {week}", ""]
    for section in SECTIONS:
        lines.append(f"## {section.capitalize()}")
        lines.append("")
        items = recap.get(section) or []
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("(none)")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render weekly repo recap")
    parser.add_argument("--repo-path", default=".")
    parser.add_argument("--since", default="1 week ago")
    parser.add_argument("--output-dir", default="docs/recaps")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    window = substantive_commits(args.repo_path, args.since)
    if not window:
        print("recap: no-op — no substantive commits in window")
        return 0
    print(f"recap: {len(window)} substantive commits in window")

    recap = run_recap_graph(args.repo_path, args.since)
    week = iso_week(date.today())
    markdown = render_markdown(recap, week)

    if args.dry_run:
        print(markdown)
        return 0

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{week}.md"
    target.write_text(markdown)
    print(f"recap: wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
