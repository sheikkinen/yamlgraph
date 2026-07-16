#!/usr/bin/env python3
"""FR-737: prior-art retrieval for newly created feature requests.

Invoked by fr-checks.sh with the FR file path. Emits a prior-art block
on stdout when the graveyard has something to say; emits nothing
otherwise (silence over alarm fatigue).

Judged pins:
- F1: rank by inverse corpus frequency — score = Σ weight/freq(noun);
  one rare noun outranks any pile of generic ones.
- FR-738 F3: weight 2 iff the noun matches the candidate's filename,
  first H1 line, or `## Summary` section text; body prose weighs 1.
  Corpus freq stays match-anywhere (frequency measures commonness;
  weight measures placement). Ties break by matched-noun count, then
  name.
- F2+A1: emit a candidate only if it matches ≥1 RARE noun, rare =
  corpus frequency ≤ 20 files (absolute; ≈3% today, tightens as the
  corpus grows). No rare filename noun → emit NOTHING.
- F3: the newly created file is never a candidate; other body-level
  citers stay (same-territory citation is signal).
- FR-738 F5: `.judgement.md` companions inherit the parent FR's
  status; orphan judgement files are excluded from candidates.
- F4: filename-only noun extraction (title/body extraction purged;
  escalate only on a real miss — two_strike_split applies).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RARE_MAX_FILES = 20  # A1: absolute count, not a corpus percentage
TOP_N = 5

STOPWORDS = {
    "fix",
    "add",
    "support",
    "node",
    "nodes",
    "graph",
    "graphs",
    "yaml",
    "demo",
    "the",
    "and",
    "for",
    "with",
    "from",
    "into",
    "new",
    "test",
    "tests",
    "update",
    "improve",
    "refactor",
    "remove",
    "enable",
    "disable",
}

_PREFIX = re.compile(r"^(fr|nc)-\d+-?", re.IGNORECASE)


def extract_nouns(filename: str) -> list[str]:
    """Filename → candidate nouns: strip FR/NC prefix, split, drop noise."""
    stem = Path(filename).stem
    stem = _PREFIX.sub("", stem)
    tokens = [t.lower() for t in stem.split("-")]
    return [t for t in tokens if len(t) > 2 and not t.isdigit() and t not in STOPWORDS]


def read_status(path: Path) -> str:
    """Status tag from the `**Status:**` line or a REJECTED- filename.

    FR-738 F5: `.judgement.md` companions inherit the parent FR's status.
    """
    if path.name.endswith(".judgement.md"):
        parent = path.with_name(path.name[: -len(".judgement.md")] + ".md")
        return read_status(parent) if parent.is_file() else "?"
    if path.name.upper().startswith("REJECTED"):
        return "REJECTED"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "?"
    match = re.search(r"^\*\*Status:\*\*\s*(\w+)", text, re.MULTILINE)
    if not match:
        return "?"
    status = match.group(1)
    return status.upper() if status.lower() == "rejected" else status


def _weighted_zone(path: Path, text: str) -> str:
    """FR-738 F3: filename + first H1 line + `## Summary` section."""
    parts = [path.name]
    for line in text.splitlines():
        if line.startswith("# "):
            parts.append(line)
            break
    summary = re.search(
        r"^## Summary\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    if summary:
        parts.append(summary.group(1))
    return "\n".join(parts)


def _is_orphan_judgement(path: Path) -> bool:
    """FR-738 F5: judgement companions without a parent FR are noise."""
    if not path.name.endswith(".judgement.md"):
        return False
    parent = path.with_name(path.name[: -len(".judgement.md")] + ".md")
    return not parent.is_file()


def build_prior_art(new_file: Path) -> str:
    nouns = extract_nouns(new_file.name)
    if not nouns:
        return ""

    corpus = [
        p
        for p in new_file.parent.glob("*.md")
        if p.resolve() != new_file.resolve()  # F3: never self
        and not _is_orphan_judgement(p)  # FR-738 F5
    ]
    if not corpus:
        return ""

    # Per-noun corpus frequency and per-file matches, one pass.
    word_res = {n: re.compile(rf"\b{re.escape(n)}\b", re.IGNORECASE) for n in nouns}
    freq: dict[str, int] = dict.fromkeys(nouns, 0)
    file_matches: dict[Path, list[str]] = {}
    file_weights: dict[Path, dict[str, int]] = {}
    for path in corpus:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matched = [
            n
            for n in nouns
            if word_res[n].search(text) or word_res[n].search(path.name)
        ]
        if matched:
            zone = _weighted_zone(path, text)
            file_matches[path] = matched
            file_weights[path] = {
                n: 2 if word_res[n].search(zone) else 1 for n in matched
            }
            for noun in matched:
                freq[noun] += 1

    rare = {n for n in nouns if 0 < freq[n] <= RARE_MAX_FILES}
    if not rare:
        return ""  # F2+A1: silence over noise

    candidates = [
        (path, matched)
        for path, matched in file_matches.items()
        if any(n in rare for n in matched)
    ]
    if not candidates:
        return ""

    def score(item: tuple[Path, list[str]]) -> float:
        path, matched = item
        weights = file_weights[path]
        return sum(weights[n] / freq[n] for n in matched)  # F1 × FR-738 F3

    candidates.sort(key=lambda item: (-score(item), -len(item[1]), item[0].name))

    lines = [f"⚠ prior art for {new_file.name} (nouns: {', '.join(nouns)}):"]
    for path, matched in candidates[:TOP_N]:
        status = read_status(path)
        lines.append(f"  {path.name}  [{status}]  matches: {', '.join(matched)}")
    lines.append(
        "Disposition required in the FR or its judgement (Scripture: Judge step)."
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        return 0
    new_file = Path(sys.argv[1])
    if not new_file.is_file():
        return 0
    output = build_prior_art(new_file)
    if output:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
