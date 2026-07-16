#!/usr/bin/env python3
"""FR-740: FR pipeline board — generated priority view + structural interrupts.

Unmarked per FR-737 F5 precedent (process infrastructure follows its
target's convention). Run: pytest scripts/tests/ -q

Pins witnessed (judgement 2026-07-16):
- AC-01 parse: both bold Status variants; canonicalization by known
  token; malformed status = parse-failure row, NEVER dropped;
  .judgement.md companions excluded (F3).
- F1 active-set scoping: terminal statuses excluded by default,
  included with all=True (723-file census: default board must not be
  a 700-row board).
- AC-02 drift lint: regenerate-and-diff; edited board fails, fresh
  board passes.
- AC-03 gates.yaml schema: open gate missing owner/ask_by/question
  fails; answered gates exempt.
- AC-04 cross-repo: absent project path = notice + skip, never error (F6).
- DAG: Parent header and gate blocks become Mermaid edges.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fr_board  # noqa: E402  # CONF-393


def make_fr(
    dir_: Path, name: str, status: str | None, fmt: str = "**Status:**"
) -> Path:
    lines = [f"# Feature Request: {name}", ""]
    if status is not None:
        lines.append(f"{fmt} {status}")
    lines += ["", "## Summary", "body"]
    p = dir_ / f"{name}.md"
    p.write_text("\n".join(lines))
    return p


def corpus(tmp_path: Path) -> Path:
    fr_dir = tmp_path / "feature-requests"
    fr_dir.mkdir()
    make_fr(fr_dir, "FR-001-active", "Proposed")
    make_fr(fr_dir, "FR-002-done", "Implemented (2026-01-01)")
    make_fr(
        fr_dir,
        "FR-003-variant",
        "Judged — APPROVED with corrections",
        fmt="**Status**:",
    )
    make_fr(fr_dir, "FR-004-weird", "Sign-off RECORDED")
    make_fr(fr_dir, "FR-005-child", "Draft")
    child = fr_dir / "FR-005-child.md"
    child.write_text(child.read_text() + "\n**Parent:** FR-001\n")
    (fr_dir / "FR-003-variant.judgement.md").write_text("# companion\n")
    return tmp_path


# ---------------------------------------------------------------- AC-01 / F1-F3


def test_parse_both_bold_variants_and_canonicalize(tmp_path):
    repo = corpus(tmp_path)
    rows = fr_board.collect_rows(repo)
    by_id = {r["id"]: r for r in rows}
    assert by_id["FR-001"]["status"] == "Proposed"
    assert by_id["FR-003"]["status"] == "Judged"  # variant format + prose tail
    assert by_id["FR-002"]["status"] == "Implemented"


def test_malformed_status_is_parse_failure_row_never_dropped(tmp_path):
    repo = corpus(tmp_path)
    rows = fr_board.collect_rows(repo)
    weird = next(r for r in rows if r["id"] == "FR-004")
    assert weird["status"] == "PARSE-FAILURE"
    assert "Sign-off RECORDED" in weird["raw"]


def test_companions_excluded(tmp_path):
    repo = corpus(tmp_path)
    names = {r["file"] for r in fr_board.collect_rows(repo)}
    assert not any(".judgement." in n for n in names)


def test_active_set_scoping(tmp_path):
    repo = corpus(tmp_path)
    rows = fr_board.collect_rows(repo)
    active_ids = {r["id"] for r in fr_board.active_rows(rows)}
    assert "FR-001" in active_ids  # Proposed
    assert "FR-003" in active_ids  # Judged
    assert "FR-004" in active_ids  # parse failures stay visible
    assert "FR-002" not in active_ids  # Implemented = terminal


# ---------------------------------------------------------------- AC-03 gates


def test_open_gate_requires_owner_askby_question():
    gates = [{"id": "P9", "fr": "FR-001", "status": "open", "owner": "sami"}]
    errors = fr_board.validate_gates(gates)
    assert errors and any("ask_by" in e for e in errors)
    assert any("question" in e for e in errors)


def test_answered_gate_exempt():
    gates = [{"id": "P5", "fr": "FR-001", "status": "answered", "answer": "YES"}]
    assert fr_board.validate_gates(gates) == []


def test_complete_open_gate_passes():
    gates = [
        {
            "id": "P9",
            "fr": "FR-001",
            "status": "open",
            "owner": "sami",
            "ask_by": "2026-07-20",
            "question": {
                "text": "Which tier?",
                "options": ["A", "B"],
                "recommendation": "A",
            },
        }
    ]
    assert fr_board.validate_gates(gates) == []


# ---------------------------------------------------------------- board + DAG


def test_board_renders_table_and_dag_with_parent_edge(tmp_path):
    repo = corpus(tmp_path)
    text = fr_board.render_board([repo])
    assert "FR-001" in text and "```mermaid" in text
    assert "FR-001 --> FR-005" in text  # Parent header edge
    assert "FR-002" not in text.split("```mermaid")[0]  # terminal not in table


# ---------------------------------------------------------------- AC-02 drift


def test_check_passes_on_fresh_board_and_fails_on_drift(tmp_path):
    repo = corpus(tmp_path)
    board = tmp_path / "fr-board.md"
    board.write_text(fr_board.render_board([repo]))
    assert fr_board.check_board([repo], board) == []
    board.write_text(board.read_text().replace("FR-001", "FR-999"))
    assert fr_board.check_board([repo], board) != []


# ---------------------------------------------------------------- AC-04 / F6


def test_missing_project_repo_is_notice_not_error(tmp_path, capsys):
    repo = corpus(tmp_path)
    ghost = tmp_path / "no-such-project"
    text = fr_board.render_board([repo, ghost])
    assert "FR-001" in text
    out = capsys.readouterr().out + text
    assert "no-such-project" in out  # named notice, somewhere visible
