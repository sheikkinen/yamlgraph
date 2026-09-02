"""save_report node (FR-879 AC-10, R-5 evidence split): writes the local
full-text rejection table and the sanitized committable table."""

from __future__ import annotations

import time
from pathlib import Path

OUTPUT_BASE = Path("outputs/image_pipeline_v2")

SANITIZED_COLUMNS = [
    "ordinal",
    "prompt_sha",
    "register",
    "nll_per_char",
    "band",
    "boundary_reason",
    "verdict",
    "selected",
]


def _table(rows: list[list[str]], header: list[str]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def save_report_node(state: dict) -> dict:
    scored = state.get("scored") or []
    output_dir = OUTPUT_BASE / time.strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    sanitized_rows = [
        [i + 1] + [row.get(c, "") for c in SANITIZED_COLUMNS[1:]]
        for i, row in enumerate(scored)
    ]
    report_file = output_dir / "rejection-table.md"
    report_file.write_text(
        "# Rejection table (sanitized — no prompt text; FR-879 R-5)\n\n"
        + _table(sanitized_rows, SANITIZED_COLUMNS)
    , encoding="utf-8")

    local_rows = [
        [
            i + 1,
            row.get("verdict", ""),
            row.get("nll_per_char", ""),
            row.get("prompt", ""),
        ]
        for i, row in enumerate(scored)
    ]
    local_file = output_dir / "rejection-table-local.md"
    local_file.write_text(
        "# Rejection table (LOCAL ONLY — full prompt text, do not commit)\n\n"
        + _table(local_rows, ["ordinal", "verdict", "nll", "prompt"])
    , encoding="utf-8")

    return {
        "report_file": str(report_file),
        "local_report_file": str(local_file),
        "output_dir": str(output_dir),
    }
