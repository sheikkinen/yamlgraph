# FR-362: Process Mining from OTel — What the Spans Actually Said

**Date:** 2026-05-10

## What happened

Ran the Minesweeper instrumentation POC end-to-end. Two Copilot phases (plan: 109s, implement: 490s), 170 OTel spans captured, extractor producing JSONL events. Then analysed the actual span contents — tool names, arguments, results, durations — to answer the original question: *is there a process that can be extracted?*

## Trap: assuming the OTel format before reading it

The initial extractor was written for OTLP `resourceSpans` JSON format (a reasonable assumption from the docs). The actual Copilot file exporter emits flat `{"type":"span", "startTime":[s,ns], ...}` records — a different schema. Result: 0 OTel events extracted from a 1.4MB file. The symptom was invisible because the extractor didn't raise — it silently yielded nothing.

**Cure:** normalize at the boundary. The boundary here is the `otel.jsonl` file format. The fix was to read one line first, check the schema, then adapt — not to assume the OTLP spec applied.

This is a textbook instance of the `downstream_fix` trap: the bug manifested as "no events extracted" but the root cause was an untested format assumption in the parser. The Scripture's "normalize at the boundary where external data enters" applies literally here — the OTel file *is* an external data source.

## The gold: `report_intent` as a free phase segmenter

The most valuable finding was not in the span counts or durations. It was in a single attribute:

```json
{"intent": "Implementing Minesweeper game"}
{"intent": "Writing YAML graph wiring"}
{"intent": "Adding requirement traceability"}
{"intent": "Running final verification"}
```

Copilot calls `report_intent` at every phase transition. The argument is a human-readable label that exactly describes the cognitive phase. This means **phase segmentation of the event log is already encoded in the OTel stream** — no ML, no heuristics, no human annotation needed.

Four `report_intent` calls divided 490 seconds into four named segments. The conformance checker can group spans by the label of the preceding `report_intent` call. This is deterministic.

## The process model that emerged

After examining the chronological span sequence and matching it against Copilot's stdout narrative and bash command outputs, a 15-step DAG emerged:

```
plan: read_fr → explore_codebase → write_plan
implement: orient → scaffold → write_tests → write_impl → run_tests
           → fix_loop↺ → wire_graph → lint_graph → trace_reqs
           → check_coverage → lint_code → final_suite
```

**7 of 15 steps are deterministic today** and could be `type: tool` or `type: python` nodes. The test-fix loop is the most interesting: it's a tight cycle (`bash pytest` → `edit` → repeat) that ran for ~280s with 6 failures resolved in sequence. This is clearly `type: copilot` — it requires adaptive editing against a real feedback signal. But the *trigger* (pytest RED) and the *gate* (pytest GREEN) are deterministic and observable from the OTel stream.

## The conformance result

Implementation followed the plan exactly: 5/5 phases in plan order, no skips. One autonomous addition (ruff lint-fix) not in the plan — Copilot added it after detecting import sort errors. This is a positive deviation: the agent improved the output beyond spec.

Session continuation worked: after `--resume`, only 2 bash re-orientation commands before writing. Far less than the 60-span exploration of the plan phase.

## Three failures, all recoverable

| Failure | Time to recover |
|---|---|
| `IndexError` in `place_mines` | 85s (6 targeted edits) |
| `grep -P` not supported on macOS | <5s (immediate retry) |
| unsorted imports (ruff) | 30s (ruff auto-fix) |

The platform trap (`grep -P`) is the most interesting: it's a boundary normalization failure where a Linux command was used on macOS. Recoverable but worth noting — it would recur in every run.

## Cognitive trap encountered during this task

**Plausible wrong answer:** the first extractor run produced 2 events (both `git_diff`). That's a valid, parseable result. If I had stopped there and moved to conformance analysis, I would have concluded "process mining yields only file change events" — which is wrong but not obviously so. The result passed shape-check (JSONL, correct schema, 2 events) but was semantically empty.

The fix required one more look: "why are there 0 OTel events from a 1.4MB file?" That question broke the plausible wrong answer.

**Heuristic extracted:** After extracting events from a new source, check the count against the raw file size. A 1.4MB file yielding 0 events is not a valid result — it is a parsing failure.

## Seed

If `report_intent` is already a free phase marker in every Copilot run, what else is already encoded? Tool argument content, result exit codes, LLM turn durations — all are in the OTel stream when content capture is enabled. The next question is: can the OTel stream alone (no stdout, no share.md) produce a complete process trace that is stable across runs? If yes, `stdout.jsonl` and `share.md` become redundant for process mining and we only need `otel.jsonl + git-diff.patch`.

**Seed:** Is `otel.jsonl` with content capture a sufficient process-mining source, or do we need the session narrative too?
