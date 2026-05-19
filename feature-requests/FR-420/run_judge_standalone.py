"""Standalone execution of the judge graph to capture raw CopilotResult.output.

Purpose: prove or disprove the preamble theory for the judge event=error failure.
The judge copilot runs for ~60s and produces real output; this script captures
the raw ``judge_result`` dict and tests what extract_event does with it.

Run:
    python feature-requests/FR-420/run_judge_standalone.py

Exits 0 if extract_event successfully maps the judge output to a verdict event.
Exits 1 if extract_event returns None (bug confirmed in current code).
Exits 2 on execution error.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
JUDGE_GRAPH = REPO_ROOT / ".chaplain/graphs/watcher-plan/step-judge-v2.yaml"
TOPIC_FILE = REPO_ROOT / ".chaplain/failed/gh-420.md"
FR_PATH = (
    REPO_ROOT
    / "tmp/worktrees/feat/watcher2-gh-420"
    / "feature-requests/FR-414-schema-as-state-loader-tool-type.md"
)

# Verbatim event_map from watcher-pipeline-v2.yaml after _normalize_event_map
EVENT_MAP: dict[str, str] = {
    "approve": "approve",
    "amend": "revise",
    "reject": "reject",
    "split": "revise",
}


async def run() -> int:
    sys.path.insert(0, str(REPO_ROOT))

    for p, label in [
        (JUDGE_GRAPH, "judge graph"),
        (TOPIC_FILE, "topic"),
        (FR_PATH, "fr"),
    ]:
        if not p.exists():
            print(f"❌ {label} not found: {p}")
            return 2

    from yamlgraph.executor_async import load_and_compile_async, run_graph_async

    print("Running judge graph against:")
    print(f"  topic: {TOPIC_FILE}")
    print(f"  fr:    {FR_PATH}")
    print()

    app = await load_and_compile_async(str(JUDGE_GRAPH), cache=None)
    result = await run_graph_async(
        app,
        initial_state={
            "topic_file": str(TOPIC_FILE),
            "fr_path": str(FR_PATH),
        },
    )

    judge_result = result.get("judge_result") if isinstance(result, dict) else None

    print("=== raw judge_result ===")
    print(json.dumps(judge_result, indent=2, default=str))
    print()

    if judge_result is None:
        print("❌ judge_result not found in graph output")
        return 2

    # Show the output field so we can see the actual format
    if isinstance(judge_result, dict) and "output" in judge_result:
        output_text = judge_result["output"]
        lines = output_text.splitlines()
        print(f"=== output ({len(lines)} lines) — first 10 ===")
        for i, line in enumerate(lines[:10]):
            print(f"  [{i:02d}] {line!r}")
        print()
        first_line = lines[0].strip().lower() if lines else ""
        print(f"First line (lowercased): {first_line!r}")
        print(f"Matches event_map: {EVENT_MAP.get(first_line)!r}")
        print()

    # Test extract_event with the actual output
    from yamlgraph.utils.fsm.helpers import extract_event

    mapped = extract_event(judge_result, EVENT_MAP)
    print(f"extract_event result: {mapped!r}")

    if mapped:
        print(f"✅ extract_event matched → {mapped}")
        return 0
    else:
        print("❌ extract_event returned None — event=error would be emitted")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
