# Feature Request: FR-898 Session Accountability Report from Existing Stores

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented — enforced 2026-08-29 on `feat/fr-898` (RED→GREEN, 10 fixture witnesses). Judged APPROVED WITH REVISIONS (2026-08-29); R-1…R-5 folded below (operator decisions: intent classification OUT — deferred to a follow-up FR; verbatim prompts IN — local-only policy). Judgement: [FR-898-session-accountability-report.judgement.md](FR-898-session-accountability-report.judgement.md)
**Effort:** 0.5 day
**Requested:** 2026-08-29
**First consumer / first event:** the operator answering "what did today's sessions do and what did each cost" — at the first invocation of the report after merge, per session: prompts, per-turn summaries, models, repo, credits
**Research:** [FR-898.research.md](FR-898.research.md) (brief: `research-briefs/session-accountability-record.md`, run 2026-08-29, 5 personas, exit 0)
**Prior art:** hook hits are FR-898's own artifacts (judgement, research — self-reference, dispositioned by this FR) and FR-225-a2a-test-coverage (lexical match on "accountability" only; A2A test coverage shares no territory with session-store reporting — no overlap). Substantive prior art (ledger.py, timesheet.py, now.py, chronicle store) is dispositioned in the Research/Existing-assets sections below.

## Summary

A read-only report generator over the **existing** VS Code session stores
that emits, per session: the original user prompts, the platform's
per-turn `generatedTitle` summaries, the model(s), the repo, and usage —
especially per-turn `copilotCredits`.
No lifecycle hooks: everything the originally proposed capture hook would
have written is already persisted by the platform; the missing capability
is the *join*, which belongs at report time. Closed-enum intent
classification is deferred to a follow-up FR (R-3, operator decision
2026-08-29).

## Value Statement

The operator (who consumes a large share of a shared department inference
budget) gets per-session "what was asked, what it was for, what it cost"
from one command over data that already exists — zero latency added to any
session, zero new write paths.

## Problem

Nothing joins prompt, intent, model, repo, and cost at session scope.
Answering the operator's budget question (witnessed 2026-08-29) requires
manual archaeology across `audit.jsonl`, `chatSessions/*.jsonl`, and
`models.json`; `scripts/vscode/ledger.py` aggregates cost per day/model
but not per session, and intent is captured nowhere.

## Measured platform facts (2026-08-29, this session's own store)

The hook-vs-reporting decision was settled by reading the raw store
(`read_raw_output_first`; `does_the_platform_already_do_this`):

`~/Library/Application Support/Code/User/workspaceStorage/<hash>/chatSessions/<session_id>.jsonl`
already contains, **per request**:

- `message.text` — the verbatim original user prompt (all three of this
  session's prompts found verbatim)
- `modelId` — on the same record as credits (`copilot/claude-fable-5`);
  survives mid-session model switches
- `copilotCredits` — the per-turn figure the UI displays after each
  finished operation. *Discarded observation (R-1):* the initially
  recorded "exact per-turn" figures 69.75795 / 46.77065 were read by an
  unpatched scan and are intermediate values — superseded by
  replay-final figures (request 1 final: 378.70); see the receipt.
- **Store shape (measured 2026-08-29):** the file is an event-sourced
  patch log — line 0 is a `kind:0` snapshot; `kind:2` appends a request
  at key path `["requests"]` (optional index `i`); `kind:1` sets fields
  (`copilotCredits`, `promptTokens`, `result`, `modelState`) by path,
  **repeatedly during the turn** (credits is a running cumulative:
  118.90 → … → 378.70 final on this session's first turn). The reader
  MUST materialize by replay with last-write-wins — a naive grep-sum
  inflates credits ~5× on intermediate patches, and the dual failure
  was witnessed same-day: a *partial structural scan* (reading request
  records without applying later patches) **undercounted the session
  3.2× (560 vs 1800 credits) while producing a perfectly plausible
  ledger** (`plausible_wrong_answer`; diary
  2026-08-29-event-log-partial-read-plausible-ledger). Event-sourced
  stores have no random access: replay or provably replay-equivalent
  reads only. **Complete record grammar (censused across all 95 stores /
  ~17k records, 2026-08-29):** exactly four shapes — kind 0 snapshot,
  kind 1 set, kind 2 insert (`v` present), and kind 2 **splice-delete**
  (`k`+`i`, no `v`; 25 wild occurrences, zero in the home session — the
  single-session fixture was an incomplete grammar sample).
- **`generatedTitle` (discovered 2026-08-29):** the platform persists
  LLM-generated one-line narrative summaries per turn/tool-batch (e.g.
  "Attached .env on three occasions during prompts", "Analyzed leakage
  vectors and potential blocking strategies") — a pre-computed intent
  signal at zero report-time LLM cost. Titles arrive as later `kind:1`
  patches, only visible after replay.
- **Session header fields:** `customTitle` (set via later patch, absent
  from the snapshot), `creationDate` (ms epoch), `sessionId`;
  workspace→repo via sibling `../workspace.json` (`folder` URI).
- **Model switch encoding (verified live 2026-08-29 by switching
  mid-session):** `requests[].modelId` is the authoritative historical
  model per request; `inputState.selectedModel` is the *latest UI
  selection only* (full descriptor: pricing, reasoning effort, context
  size) — never use it for history; `modelState` is request lifecycle
  (`0` pending / `1` completed), not model identity. Monthly grouping
  must key on `requests[].modelId`.
- `timestamp` (ms), `promptTokens`/`outputTokens`
- The workspace hash maps to the repo (`stores.py` already resolves this)

Coverage caveat: 1 of 8 recent session files had no `copilotCredits`
records — token × `models.json` price range (`ledger.py` join) is the
fallback, reported as a range (cache-read conflation).

**Prior-art delta (existing cost tools, compared 2026-08-29):**
`ledger.py`'s founding premise is stale — its docstring records
"no balance/usage history is persisted locally (verified — the UI's
number is fetched live), so credits are ESTIMATED" (2026-07-16); the
platform has since started persisting `copilotCredits` per request.
`tap.py` gives exact per-session tokens but requires arming + full
VS Code restart and covers arming-onward only; `timesheet.py` is
per-session narrative without cost; none read prompts or classify
intent. `session_ledger.py` is the only per-session × authoritative-
credits × prompts × intent view — and MAP.md's ranked "third UI
anchor" next-step is satisfied for free (the anchor is now persisted
per request).

**Therefore the UserPromptSubmit/Stop hook pair is redundant**: it would
re-write data the platform already persists, pay a latency tax on every
prompt, race the store flush at `Stop`, and force intent classification
into a path where LLM calls are banned. At report time the ban lifts.

## Proposed Solution

### 1. `scripts/vscode/session_ledger.py` — the join (stdlib, read-only)

Sibling of `ledger.py`/`timesheet.py`. Per session (default: today, this
workspace; `--session <id>`, `--window Nh`, `--all-workspaces` to widen):

```
session a7be91fc  repo=yamlgraph  model=copilot/claude-fable-5
  credits: 116.53 total over 2 turns (all turns covered)
  tokens: prompt=…, output=…   cost-range fallback: n/a
  prompts:
    06:41  "plan a pair of hooks that capture the original user prompt…"
    07:19  "user session has AI credits displayed after each finished…"
```

`--csv` emits the machine-readable mode (operator decision 2026-08-29,
superseding the planned `--jsonl`): **one row per request** with session
details repeated on every row — denormalized deliberately, because the
named consumer is an Excel/pivot workflow over a concatenation of all
sessions. Columns: `session_id, session_title, created, workspace,
request, request_time, model, credits, prompt_tokens,
completion_tokens, elapsed_ms, prompt, summary, unavailable_reason`.
Missing data is an explicit empty cell with `unavailable_reason` set,
never a fabricated point (`gate_checks_shape_not_substance`). Multiple
session files on the command line concatenate under a single header.

**Malformed/truncated store policy (R-2):** an explicitly requested
session (`--session <id>` or a named path) that fails replay — invalid
JSON line, impossible patch path, missing snapshot, truncated request —
is a **hard error**. Multi-file/all-store scans continue, skip the
broken store, report it on stderr, and emit a row with
`unavailable_reason` excluded from totals. Silent omission is never
permitted.

**Prompt-privacy policy (R-4, operator decision 2026-08-29): verbatim
prompts IN.** Output is local-only: stdout or `--out`; `--out` refuses
paths inside a git repository unless `--allow-repo-output` is passed.
Generated reports are never committed.

### 2. Summaries — generatedTitle only; intent classification deferred (R-3)

The store's per-turn `generatedTitle` strings already narrate what each
request did; the report includes them by default as the `summary` field
(zero LLM cost, vendor-persisted, recovered via replay). Closed-enum
intent classification (`--classify` + `examples/demos/session-intent/`
map graph via the authoring sole route) is **deferred to a follow-up
FR** — operator decision 2026-08-29. No `intent` field is emitted under
FR-898; the report never guesses.

### 3. No hooks

The `UserPromptSubmit`/`Stop` ledger hooks are **not built**. If a future
consumer needs real-time capture (e.g. a session that must self-report
before its store flushes), that is a new FR with its own first event —
the seam is the `--csv` row schema, which a hook writer would have to match.

## Acceptance Criteria (revised per judgement)

- [x] AC-01: fixture tests materialize a `chatSessions/*.jsonl` patch
      log by replaying kind 0 snapshot, kind 1 set, kind 2 insert, and
      kind 2 splice-delete records with last-write-wins semantics;
      intermediate `copilotCredits` patches are never summed.
- [x] AC-02: fixture tests prove prompt, request timestamp, per-request
      `modelId`, final `copilotCredits`, token counts, `generatedTitle`
      summary, session title, session ID, creation date, and
      workspace/repo mapping are joined into request rows.
- [x] AC-03: a fixture with absent `copilotCredits` reports a
      token-price fallback range from `models.json` and marks the row
      with `unavailable_reason`; never a fabricated point value.
- [x] AC-04: malformed/truncated JSONL fixtures exercise the R-2
      policy: explicit-request → hard error; scan → skip with stderr
      report + `unavailable_reason` row excluded from totals; never
      silent omission.
- [x] AC-05: running against the real store reproduces the receipt
      ([FR-898.receipt.md](FR-898.receipt.md)): request 1 final credits
      378.70 (not the intermediate 69.76/46.77 an unpatched scan
      returns) and the mid-session model switch labeled per request via
      `requests[].modelId`.
- [x] AC-06: `--csv` emits exactly one header and one row per request
      across multiple session files with the column set in §1 including
      `unavailable_reason`.
- [x] AC-07: the default report includes replay-recovered per-turn
      `generatedTitle` values as `summary`; no `intent` field is
      emitted (deferred per R-3).
- [x] AC-08: read-only witnessed — stores opened read-only; output only
      to stdout or `--out` under the R-4 policy (`--out` refuses
      repo-internal paths without `--allow-repo-output`).
- [x] AC-09: session-introspection skill table gains the
      `session_ledger.py` row; `scripts/vscode/README.md` updated;
      `ledger.py` docstring's "not persisted locally" claim corrected
      and MAP.md's third-anchor entry closed (upgrading `ledger.py`
      itself is a separate follow-up, not this FR).
- [x] AC-10: changelog fragment in `changelog/unreleased/`.

## Out of scope (purge list)

- Lifecycle hooks of any kind (the redundancy is measured, not assumed).
- **Monthly aggregation and anomaly detection (R-5)** — not authorized
  under FR-898; separate FR with its own first event.
- **Closed-enum intent classification (R-3)** — deferred to a follow-up
  FR (`--classify`, `examples/demos/session-intent/` graph).
- Committing reports to git (verbatim prompts; stays local like the
  stores themselves; mechanically enforced per the R-4 policy).
- Scheduled/daemon execution — on-demand pull only; a cadence needs its
  own first consumer.
- Backfilling intent for historical sessions beyond what `--classify`
  is pointed at.
- Editing or normalizing the vendor store — reader adapts, store is
  never touched.

## Alternatives Considered

Dispositioned in [FR-898.research.md](FR-898.research.md), re-weighed
after the store measurement:

- **Hook pair writing a session-scoped ledger** (os-infra-primitivist,
  data-process-planner, yamlgraph-native-planner — the original request
  shape): REJECTED as redundant — every field it would capture is already
  persisted per request in `chatSessions/*.jsonl` (measured 2026-08-29);
  it adds per-prompt latency, a store-flush race at `Stop`, and a
  redaction obligation the read-only report doesn't have. Kept: the
  record schema and explicit-null discipline, which moved into `--csv`.
- **Subtraction — keep forensics, classify async** (subtractionist):
  ADOPTED in substance — this FR is the forensic reader made per-session
  and self-serve, with intent classified out-of-band. The dropped part:
  "operator on demand" now has a named tool instead of hand-rolled joins.
- **External precedent** (librarian): cost at the session boundary +
  async intent classification, per
  <https://www.braintrust.dev/articles/how-to-track-llm-costs-2026> —
  the boundary here is the platform's own store; we read it rather than
  duplicate it.

## Related

- `scripts/vscode/ledger.py`, `stores.py`, `timesheet.py`, `tap.py`
  (store map, workspace→repo resolution, price-range join, exact-token
  tap — reuse, don't fork; ledger.py's estimation premise is corrected
  by this FR's measurement)
- session-introspection skill (store facts; gains the new row)
- FR-743 (platform probe — the hook events remain measured and available
  for the future real-time FR, if one earns a first consumer)
- FR-425 (redaction boundary — inherited by any future hook writer, not
  needed by the read-only report)
- FR-899 (implicit-context attachment disabled — the store's
  `vscode.implicit.selection` variables are what made the .env leak
  provable request-by-request; the report surfaces them)
- `scripts/vscode/session_report.py` (prototype, 2026-08-29) and diary
  `2026-08-29-reflection-fr-898-event-log-plausible-ledger.md`

## Implementation record

**2026-08-29 (pre-judgement prototyping, operator-directed):**
`scripts/vscode/session_report.py` saved (FR-888 audited main-lane
escape) — a working replay reader rendering per-request
User / model / generatedTitles / Cost blocks with customTitle,
creationDate, sessionId, and workspace-folder heading. Validated on
this session's live store: full patch replay (kind 0/1/2 incl. `i`
index), 23 requests, mid-session model switch labeled correctly,
customTitle recovered from late patch. Same-day extensions: title
fallback chain (generatedTitle → boilerplate-only → answer first line —
some turns get no title at all, verified against the store) and `--csv`
mode (AC-03's machine-readable output, one row per request,
multi-session concatenation, verified 28 rows / 57-line two-file
concat). It covers the replay +
prompt/model/credits join and the generatedTitle narrative; it does
NOT yet cover: AC-01 fixture tests,
credits-absent token-range fallback, `--window`/`--all-workspaces`
scoping, AC-06 doc/skill/docstring updates, or the intent graph.
`session_ledger.py` should absorb or supersede the prototype at
enforcement.

**2026-08-29 (judged):** APPROVED WITH REVISIONS via the sole judge
route (gpt-5.5). R-1…R-5 folded same day: receipt named
([FR-898.receipt.md](FR-898.receipt.md)); 69.76/46.77 demoted to
discarded observation; malformed-store policy fixed (hard error on
explicit request, skip+report on scans); intent classification
deferred out (operator decision); verbatim prompts in with local-only
`--out` policy (operator decision); monthly aggregation + anomaly
section ruled OUT of FR-898 — the diary Seed graduates to a follow-up
FR, not this one.

**2026-08-29 (enforced, worktree `feat/fr-898`):** RED first —
`scripts/vscode/tests/test_session_ledger.py`, 10 witnesses on
synthetic fixtures exercising all four record shapes (snapshot / set /
insert / splice-delete), last-write-wins credits, title→answer-line
summary chain, CSV schema (14 columns incl. `unavailable_reason`),
credits-absent estimate RANGE, R-2 malformed policy (explicit → hard
error; scan → skip + stderr + reason row), `--window` scoping,
read-only stores, and the R-4 `--out` repo-path refusal. GREEN —
`scripts/vscode/session_ledger.py` absorbs the prototype (which is
deleted, not shipped) and reuses `ledger.py` price machinery
(`load_prices`, `CACHE_RATIO_BEST`, `UNKNOWN_MODEL_PRICE`; import, not
fork). AC-05 live receipt re-run with the shipped script: all stable
assertions reproduced (378.70 final credits, model switch at request
23, "Blocked by hook" title, untitled turns 17/18/21/23 summarized
from answer first line); session had grown to 34 requests / 3517.9 cr,
zero estimated rows. D-4 docs updated: session-introspection SKILL
row, scripts/vscode/README.md (cookbook + spikes table), ledger.py
stale "no local spend record" docstring corrected, MAP.md third-anchor
direction CLOSED. D-5 changelog fragment added. Deviations: none
beyond the judged fold.
