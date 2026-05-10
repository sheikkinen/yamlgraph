# Diary: FR-363 Watcher2 Sanity Check

**Date:** 2026-05-10
**FR:** FR-363 Per-node OTel exporter scoping in copilot_node.py
**Author:** watcher2 (post-validate sanity reviewer)

---

## Trap

**`implementer_note_as_authoritative`** — The FR Judgement notes said "`import os` is the only missing import". A watcher reading this before inspecting the diff would expect `import os` to appear as a new line. The diff confirms `import os` was indeed added — so the note was accurate here. However, the *existing* diary entry narrative says "os was already present", which contradicts the diff. The lesson: read the diff before reading the narrative; diffs are authoritative, prose is approximate.

---

## What Happened

Post-validate sanity review of FR-363. The implementation consists of:
- **7 production lines** in `_execute_cli` in `yamlgraph/node_factory/copilot_node.py`: env dict construction guarded by `os.environ.get("YAMLGRAPH_OTEL_DIR")`, passed as `env=node_env` to `subprocess.run`.
- **4 acceptance tests** in `tests/unit/test_fr363_per_node_otel_scoping_red.py`, all green (4 passed in 0.13s).
- **Documentation**: `CLAUDE.md` env var table updated; changelog fragment added; FR status marked Implemented.

All 4 ACs are verified at the subprocess boundary via `subprocess.run` mock assertions.

---

## Root Cause

No defects found. Scope is minimal and proportional. FR/code alignment is exact across all 4 acceptance criteria.

---

## What Worked

1. **Boundary normalization**: `node_env` is constructed inside `_execute_cli` — the process boundary — not upstream. Matches `the_one_law`.
2. **Zero-config when unset**: `node_env = None` means `subprocess.run` inherits ambient env unchanged; existing tests pass without modification.
3. **Tight AC coverage**: one test per AC, assertions check exact env key values — behavior, not implementation trivia.
4. **Proportionality**: 9 files changed; ~14 net production lines (7 implementation + `import os` + 2 log lines). No speculative scope.

---

## Seed

> Process-mining (FR-364/365) will consume the per-node `.otel.jsonl` files produced by this FR. Should the mining pipeline emit a structured summary (e.g., node-level latency, token count, exit code) back into graph state so downstream nodes can make routing decisions based on OTel evidence — turning observability data into a first-class graph input?
