"""save_report node (FR-881 AC-07, R-4/R-5): writes the sanitized
committable generation table (no prompt text) and the local full-text
table, under outputs/image_pipeline_v3 — never the v2 tree."""

from __future__ import annotations

import time
from pathlib import Path

OUTPUT_BASE = Path("outputs/image_pipeline_v3")

SANITIZED_COLUMNS = [
    "ordinal",
    "prompt_sha",
    "attempts_for_candidate",
    "verdict_counts",
    "selected",
]


def _table(rows: list[list], header: list[str]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def save_report_node(state: dict) -> dict:
    scored = state.get("scored") or []
    summary = state.get("gen_summary") or {}
    output_dir = OUTPUT_BASE / time.strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    provenance = {
        k: scored[0].get(k, "") if scored else ""
        for k in ("ckpt_sha", "corpus_sha", "git_sha")
    }
    sanitized_rows = [[row.get(c, "") for c in SANITIZED_COLUMNS] for row in scored]
    report_file = output_dir / "generation-table.md"
    report_file.write_text(
        "# Generation table (sanitized — no prompt text; FR-881 R-5)\n\n"
        f"Total attempts: {summary.get('attempts', '?')}; aggregate verdicts: "
        f"`{summary.get('verdict_counts', {})}`; provenance: `{provenance}`\n\n"
        + _table(sanitized_rows, SANITIZED_COLUMNS)
    )

    local_rows = [
        [row.get("ordinal", ""), row.get("selected", ""), row.get("prompt", "")]
        for row in scored
    ]
    local_file = output_dir / "generation-table-local.md"
    local_file.write_text(
        "# Generation table (LOCAL ONLY — full prompt text, do not commit)\n\n"
        + _table(local_rows, ["ordinal", "selected", "prompt"])
    )

    return {
        "report_file": str(report_file),
        "local_report_file": str(local_file),
        "output_dir": str(output_dir),
    }
