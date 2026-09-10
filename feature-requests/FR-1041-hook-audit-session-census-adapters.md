# Feature Request: Hook-audit session adapters for the corpus census

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented (spike; unjudged — see Decisions)
**Effort:** 0.5 days
**Requested:** 2026-09-10
**First consumer / first event:** the metamodelling reflection arc
(docs/diary 2026-09-0x parts 11–16) asking "what shape do our agent
sessions actually have, and how many produce prose nobody verified?" —
answered by the run recorded in
`examples/demos/corpus_census/proofs/hook-audit-sessions/`.
**Research:** in-body alternatives table below (FR-889 style equivalent record).
**Prior art:** [FR-892-corpus-census-pipeline-injected-adapters.md](FR-892-corpus-census-pipeline-injected-adapters.md) — the census
graph and slot contract this FR binds to; no graph change.
[FR-895](FR-895-census-synthesize-tail.md), [FR-940](FR-940-census-judgement-normalization.md) — brief and judgement plumbing, reused as-is.
The `proofs/git-timeline/` and `proofs/pdf-library/` variants are the
proof-layout precedent; this FR differs only in that the corpus is a
private, gitignored log, so the ledger cannot be committed.

## Summary

Two FR-768 slot manifests plus one Python module that turn
`.github/hooks/logs/audit.jsonl` into census items (one item = one agent
session) with a compact digest an inexpensive judge can label by session
shape. No graph, prompt, or hook change.

## Value Statement

The operator gets a code-computed census of agent-session shapes (code
with/without tests, verified/unverified prose, git-ops, inspect-only) split
by client, instead of a narrative guess.

## Problem

The hook audit log records every tool call across all sessions but has no
per-session view; questions like "how many sessions write prose without
running any verifier" were answered by reading transcripts one at a time.
`corpus_census` already does map-reduce labelling but had no adapter for
this corpus.

## Ideal Result

`yamlgraph graph run corpus_census … --tool discover=audit-discover …`
produces a ledger whose label×client aggregate is trustworthy enough to
cite in a diary entry, with an evidence bundle that can be committed
without leaking private command lines.

## Proposed Solution

### Digest schema (extract output, plain text, in this order)

```
session: <sid>  client: vscode|copilot-cli
span: <first ts> → <last ts>
events: N  tools: {tool: count, … (top 8)}
denials: N
files_written: N (prose/yaml: P, code: C)
terminal_commands: N  verification_cmds: V  git_gh_cmds: G
files:
  <repo-relative path> …          (≤ 30)
commands (deduplicated, in order):
  <command, ≤ 110 chars> …        (≤ 60)
```

- `client` is `copilot-cli` when the session logs CLI tool names
  (`Bash`/`Edit`/`Write`/`Read`/`Grep`/`Glob`), else `vscode`.
- Commands come from `run_in_terminal` detail (VS Code) or the `"command"`
  field of `Bash` (CLI); files from `post-edit-*-checks` detail (VS Code)
  or `*** Add/Update File:` / `"path":` in `Edit`/`Write` detail (CLI).
- `verification_cmds` matches `pytest|ruff|lint-imports|mypy|yamlgraph
  graph (lint|run|validate)|curl|req_coverage|pre-commit run`.

### Discover contract

`source = '<audit.jsonl path>:<since ISO date>'`; sessions with
≥ `MIN_EVENTS` (20) events at or after the date; raises if none or more
than `MAX_ITEMS` (200) — the date filter is how a batch is kept under the
map cap.

### Public-safe evidence allowlist (`proofs/hook-audit-sessions/`)

| committed | content |
|---|---|
| `run-evidence.txt` | run log truncated before the final state dump (no digests); session ids shortened to 8-char prefix |
| `brief.md` | synthesized brief; session ids shortened to 8-char prefix |
| `summary.md` | code-computed label×client table + observations |
| **not committed** | `ledger.jsonl` / `ledger.md` — full session ids and raw command lines |

### Alternatives considered

| alternative | disposition |
|---|---|
| Per-session transcript reading | the sequential review this census replaces (`impossibly_large_sequential_task`) |
| Commit the full ledger like `proofs/git-timeline/` | rejected: rows quote private command lines and full session ids |
| Ad-hoc Python script over the log | rejected: `is_this_a_graph` — the census graph already exists (FR-853) |

## Acceptance Criteria

- [x] `audit_discover` / `audit_extract` run under the unchanged
  `corpus_census` graph (run 2: 124 items, 0 abstain, 0 failed —
  `proofs/hook-audit-sessions/run-evidence.txt`).
- [x] Copilot-CLI child sessions are digested (run 1 mislabelled 62/124 as
  `inspect-only` because CLI tool names were unparsed; fixed, `client:` tag added).
- [x] No committed artifact contains a full session id or a raw command line.
- [ ] Unit tests for the two adapters (fixture jsonl → digest) — not written;
  see Decisions.

## Decisions / Implementation status

- Committed as `chore(census)` from a spike session on operator instruction
  ("commit the adapter as proposed"); this FR was written after the code and
  has **not** been judged. Any further change to the adapters routes
  through `scripts/judge.sh` first.
- Adapter unit tests are **refused in this commit**, not deferred: the
  commit is the spike record. If the adapter is reused, the judge of that
  FR requires them.
- The brief synthesizer's percentages are over its 60-row window, not the
  corpus; `summary.md` is the citable aggregate.
