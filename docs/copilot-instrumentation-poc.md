# Copilot Instrumentation POC (FR-362)

This proof-of-concept captures a two-phase Copilot execution (`plan` then resumed `implement`) and converts local artifacts into normalized process-mining events.

Run: `minesweeper-001` (2026-05-10) — Minesweeper game implementation (FR-082)

## Captured Artifacts

Artifacts are written to:

`outputs/copilot-instrumentation/<run-id>/<phase>/`

Per phase (`plan`, `implement`) the run records:

- `prompt.txt`
- `command.txt`
- `stdout.jsonl`
- `stderr.log`
- `share.md`
- `otel.jsonl`
- `copilot-debug.log`
- `git-status.txt`
- `git-diff.patch`

The run root also contains `run-metadata.json` with run ID, base ref, disposable worktree path, and extracted plan session ID.

## Observed Process: minesweeper-001

### Plan phase (109s, 60 OTel spans)

Copilot announced three intent phases via `report_intent`:

| t | Intent | Dominant tools |
|---|---|---|
| +8s | Reading FR and codebase | `view ×22`, `rg ×10`, `glob ×8` |
| +23s | Exploring codebase patterns | Launched `explore` subagent (gpt-5.4-mini); `read_agent` |
| +55s | Building implementation plan | `bash ×3`, `view ×3`, then `create` |

Output: a numbered plan written to a file (1× `create` at t=106s). No files edited.

### Implement phase (490s, 110 OTel spans)

Copilot announced four intent phases:

| t | Intent | Key events |
|---|---|---|
| +10s | Implementing Minesweeper game | `bash` (ls CAP/REQ), `bash` (mkdir scaffold), `create ×3` (__init__.py files), `create` (test file, 55s LLM turn), `create` (tools/minesweeper.py) |
| +127s | — | First `pytest` run → **RED** (IndexError) |
| +145–212s | — | 6× `edit` — fix test failures, thread `rows/cols/mines` through state |
| +212s | — | `pytest` → **GREEN** (25/25 pass) |
| +242s | Writing YAML graph wiring | `create ×3` (graph.yaml, prompts/, run.py), `yamlgraph graph lint` |
| +264s | Adding requirement traceability | `bash ×6` — find next CAP/REQ numbers, `edit` ARCHITECTURE.md, `edit` scripts/req_coverage.py |
| +368s | — | `req_coverage --strict` → ✅ CAP-145 6/6 reqs, 25 tests |
| +384s | Running final verification | `ruff format --check`, `pytest` (25/25), `ruff check --fix`, `ruff format`, full suite `pytest tests/unit/ -m "not slow"` (55s) |

### Conformance: did implementation follow the plan?

Plan phases: scaffold+tests (RED) → game logic (GREEN) → graph wiring → req traceability → validate.
Observed phases: scaffold+tests (RED) → game logic (GREEN) → graph wiring → req traceability → lint+validate.

**Match: 5/5 phases observed in plan order.** No phases were skipped. One phase was not in the plan: the ruff lint-fix cycle at t=403s (Copilot added it autonomously after detecting import sort errors).

### Repeated context-gathering after `--resume`

After resuming the plan session, Copilot ran 2 bash commands at t=10s to re-check the CAP/REQ registry before writing any files. This is minimal re-orientation — significantly less than the plan phase's 60 spans. Session continuation is working.

### Failures and retries

| t | Failure | Recovery |
|---|---|---|
| t=127s | `IndexError: list index out of range` in `place_mines` | 6 targeted `edit` calls; fixed in ~85s |
| t=276s | `grep -P` flag not supported on macOS | Immediately retried without `-P` |
| t=384s | `ruff format --check` found unsorted imports | Auto-fixed with `ruff check --fix` + `ruff format` |

**3 failures, all recovered.** No restarts. No repeated full-context reads.

## Process Model

The observed workflow is a DAG with one loop:

```
plan
  ├─ read_fr          (view FR markdown)
  ├─ explore_codebase (parallel subagent + direct rg/view/glob)
  └─ write_plan       (create plan document)

implement
  ├─ orient           (bash: check CAP/REQ registry)
  ├─ scaffold         (mkdir + create __init__.py files)
  ├─ write_tests      (create test file — TDD RED)
  ├─ write_impl       (create tools/minesweeper.py)
  ├─ run_tests        (bash: pytest → RED)
  ├─ fix_loop ↺       (edit → run_tests until GREEN)
  ├─ wire_graph       (create graph.yaml, prompts, run.py)
  ├─ lint_graph       (bash: yamlgraph graph lint)
  ├─ trace_reqs       (bash: find CAP/REQ numbers, edit ARCHITECTURE.md)
  ├─ check_coverage   (bash: req_coverage --strict)
  ├─ lint_code        (bash: ruff check/format)
  └─ final_suite      (bash: pytest tests/unit/ -m "not slow")
```

### Candidate YAMLGraph node types per step

| Step | Type | Rationale |
|---|---|---|
| `read_fr` | `type: tool` or `type: python` | Deterministic file read + markdown parse |
| `explore_codebase` | `type: copilot` | Needs codebase-aware IDE context |
| `write_plan` | `type: copilot` or `type: llm` | Creative synthesis; could be templated |
| `orient` | `type: python` | Bash to find next CAP/REQ IDs is deterministic |
| `scaffold` | `type: python` | `mkdir -p` + `touch __init__.py` is deterministic |
| `write_tests` | `type: copilot` | Pattern-matching from examples; IDE context needed |
| `write_impl` | `type: copilot` | Creative; IDE context needed |
| `run_tests` | `type: tool` (shell) | Pure deterministic: `pytest` invocation |
| `fix_loop` | `type: copilot` | Adaptive editing; needs tool access |
| `wire_graph` | `type: llm` or `type: copilot` | Could be `type: llm` with template if patterns are stable |
| `lint_graph` | `type: tool` (shell) | Deterministic: `yamlgraph graph lint` |
| `trace_reqs` | `type: python` | CAP/REQ ID allocation is deterministic |
| `check_coverage` | `type: tool` (shell) | Deterministic: `req_coverage --strict` |
| `lint_code` | `type: tool` (shell) | Deterministic: `ruff check --fix && ruff format` |
| `final_suite` | `type: tool` (shell) | Deterministic: `pytest tests/unit/` |

**7 of 15 steps are deterministic enough to become `type: tool` or `type: python` today.**
The remaining 5 (`explore`, `write_tests`, `write_impl`, `fix_loop`, `wire_graph`) need `type: copilot`.
`write_plan` and `orient` sit on the boundary.

### Key finding: `report_intent` as a free phase marker

Every phase transition was preceded by a `report_intent` call. The arguments (`intent: "..."`) are structured labels that segment the event log without any ML or heuristic. This means:

- **Phase segmentation is already encoded in the OTel stream.** A conformance checker can group spans by the preceding `report_intent.arguments.intent` value.
- **Phase names are human-readable.** They can be mapped directly to workflow node names.
- **This is extractable deterministically** — no LLM needed for phase identification.

The extractor should be extended to emit `phase_marker` events from `report_intent` spans.

## Observed Event Sequence

See **Observed Process: minesweeper-001** above for the full chronological event trace.

The extractor (`scripts/extract_copilot_events.py`) emits JSONL events with:

- `case_id`
- `phase`
- `event_type`
- `timestamp`
- `summary`

Current event classes: `otel_span`, `git_diff`.

Recommended additions for the next FR:

| New event type | Source | Value |
|---|---|---|
| `phase_marker` | `report_intent` span arguments | Free phase segmentation |
| `test_run` | `bash` span with `pytest` in command + result | RED/GREEN signal |
| `lint_run` | `bash` span with `ruff`/`yamlgraph graph lint` | Conformance gate |
| `file_create` | `create` span | Scaffold boundary |
| `file_edit` | `edit` span | Fix-loop evidence |
| `failure` | `bash` result containing error/exception text | Retry trigger |

## Candidate Node Types

**7 of 15 steps are deterministic enough to become `type: tool` or `type: python` today.**

See the table in **Observed Process: minesweeper-001 → Candidate YAMLGraph node types per step**.

## Next FR

A follow-up FR should:

1. Extend the extractor to emit `phase_marker`, `test_run`, `lint_run`, `file_create`, `file_edit`, `failure` event types from OTel span attributes (tool arguments and results are already captured when `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`).
2. Add a conformance checker that groups events by `phase_marker` and compares against an expected phase sequence.
3. Prototype the 7 deterministic steps as a YAMLGraph workflow skeleton that wraps the `type: copilot` creative steps.
