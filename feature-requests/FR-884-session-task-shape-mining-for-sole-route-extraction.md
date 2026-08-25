# Feature Request: Chat-Session Task-Shape Mining for Sole-Route Extraction

**Priority:** HIGH
**Type:** Investigation
**Status:** Judged (APPROVED WITH REVISIONS, 2026-08-25 — R-1..R-5 folded below;
implementation authority activates only after the sanitized raw-read evidence
table (R-1/AC-02) is recorded)
**Effort:** 2 days
**Requested:** 2026-08-25

**Frozen analysis window (R-2):** 2026-06-26 through 2026-08-25 inclusive,
Europe/Helsinki local time. This one window is the denominator for raw-read
sampling, token volume, taxonomy coverage, and candidate ranking.

**Prior art:** FR-362/FR-364 (Implemented) mined process events from a
*single governed copilot run* (OTel spans → normalized event schema) to
codify stable phases into graph nodes — different surface: FR-884 mines
*interactive chat sessions* across 60–90 days for task shapes and cost;
their `scripts/extract_copilot_events.py` event schema is reusable in
Phase 1 and must be consulted before writing a new extractor. FR-363
(Implemented) provides the per-node OTel scoping those FRs consume —
infrastructure, not overlap. FR-691/FR-696 are dungeon-master narrative
FRs — noun-collision noise ("threads", "extraction"), no overlap.

## Summary

Mine the already-active session telemetry (chatSessions JSONL, chronicle DB,
hooks audit trail, model price sheets) to build an empirical taxonomy of
recurring interactive task shapes, rank them by cost × frequency ×
extractability, and produce concrete extraction candidates: predefined
subagent graphs ("sole routes") with pinned cheap models. Investigation
only — follow-up FRs implement the routes.

## Value Statement

The operator stops paying premium-model overage for routine task shapes;
the agent gets an evidence-backed answer to `is_this_a_graph` instead of a
memory-dependent one.

## Cost Evidence (2026-08 Copilot premium invoice, transcribed — source image is ephemeral)

Total gross **$5,743.68**, additional (paid overage) **$4,895.10**.
Included credits 84,858.24; additional credits 489,510.23.

| Model | Included credits | Additional credits | Gross | Additional $ |
|---|---|---|---|---|
| Claude Fable 5 | 64,143.08 | 340,041.83 | $4,041.85 | $3,400.42 |
| GPT-5.6 Sol | 1,981.44 | 58,761.42 | $607.43 | $587.61 |
| GPT-5.5 | 5,429.46 | 24,252.95 | $296.82 | $242.53 |
| Claude Opus 4.6 | 0 | 28,755.41 | $287.55 | $287.55 |
| Claude Opus 5 | 245.93 | 18,919.09 | $191.65 | $189.19 |
| Claude Sonnet 5 | 63.47 | 18,264.43 | $183.28 | $182.64 |
| Claude Opus 4.8 | 12,958.77 | 0 | $129.59 | $0.00 |
| GPT-5.4 | 0 | 298.74 | $2.99 | $2.99 |
| GPT-5.4 mini | 0 | 115.28 | $1.15 | $1.15 |
| Claude Haiku 4.5 | 0 | 74.20 | $0.74 | $0.74 |
| Claude Sonnet 4.6 | 36.08 | 10.08 | $0.46 | $0.10 |
| GPT-5.3-Codex | 0 | 14.72 | $0.15 | $0.15 |
| Auto: MAI-Code-1.1-Flash | 0 | 2.07 | $0.02 | $0.02 |

Mapping to repo pins (diary 2026-08-25 "the invoice audits the doctrine"):

- **~83% of overage** (Fable 5 + GPT-5.6 Sol, ~$3,988) flows through
  **ungoverned interactive sessions** — no model pin, no task contract.
- The three governed sole routes (author / judge / review adapters, all
  pinned `gpt-5.5`) plus chaplain steps account for **under 10%** of spend.
- The governed paths are the cheap paths. The extraction frontier is the
  chat, not the pipeline.

## Ideal Result

Every recurring interactive task shape that satisfies the prompt-contract
clauses is served by a pinned-model sole-route graph; premium interactive
capacity is reserved for genuinely novel judgement. When the agent (or the
human) wonders whether chat work should be a graph, telemetry — not
recollection — answers.

## Problem

We know *how much* interactive sessions cost, but not *what they did*.
Without a task-shape taxonomy:

1. `is_this_a_graph` is answered per-session from memory — the
   `builders_never_call` failure mode (FR-853): graphs exist unconsumed
   while equivalent work is redone interactively at premium rates.
2. Extraction candidates are chosen by anecdote (e.g. "repin
   validate-session") instead of by measured frequency × cost.
3. There is no baseline to verify a future extraction actually shifted
   spend from ungoverned to governed paths.

The telemetry to answer this **already exists**; nothing new needs
instrumenting:

| Source | What it holds |
|---|---|
| `~/Library/.../workspaceStorage/<hash>/chatSessions/*.jsonl` | Per-request timestamps, `modelId`, `promptTokens`/`outputTokens`, full turn text |
| `debug-logs/*/models.json` | Price sheet per model |
| Chronicle SQLite (`globalStorage/github.copilot-chat/session-store.db`) | Session titles, turns, files touched, FR/PR refs, FTS index — read via a committed `scripts/vscode/` script (R-2; `portrait.py` precedent), NOT the chat-only `session_store_sql` tool; if unavailable, reported as unavailable and excluded from mandatory joins |
| `.github/hooks/logs/audit.jsonl` | Per-tool-call trace with `session_id` — the action shape of each session |
| `scripts/vscode/ledger.py --by-model` | Requests/tokens/cost-range per day per model |

## Investigation Questions

1. What are the recurring task shapes in interactive sessions over the
   frozen window? (taxonomy, ≤12 shapes)
2. Which shapes are graph-extractable — i.e. satisfy the five
   prompt-contract clauses (one judgement, closed inputs, one
   validator-covered output shape, stateless, bounded)?
3. What token/cost fraction does each shape account for? (ranges only —
   `promptTokens` conflates cache reads with fresh input, billed ~10× apart)
4. Which existing graphs or sole routes were available-but-unused for
   sessions matching their task shape? (`builders_never_call` witness rate)

## Proposed Method

### Phase 0 — Raw read (gate for everything else)

Per `read_raw_output_first` and the Judge's measurement-FR gate: read
**K ≥ 10 full session transcripts end-to-end** before building any
classifier or metric. Stratified sample: the 5 highest-token sessions in
the frozen window plus 5 random. Record for each a concrete surprising
detail a generated dump could not produce. Raw reads stay in `tmp/` (see
Privacy).

**R-1 gate:** implementation authority activates only after a sanitized
raw-read evidence table is recorded in this FR or
`docs/FR-884-raw-read-log.md` — per row: session pseudonym (never the
real UUID or title), sampled stratum, date bucket, task-shape clue, one
non-identifying surprising detail, privacy classification. Zero
transcript excerpts. Manual reading here seeds the taxonomy but must not
be used to claim the AC-06 coverage threshold (R-4).

### Phase 1 — Inventory and join

Join chatSessions JSONL (tokens, model) × chronicle (title, files, refs) ×
audit.jsonl (tool-call sequence) on `session_id`. Extend `scripts/vscode/`
(stdlib-only, read-only precedent) rather than new infrastructure.

### Phase 2 — Classify

Derive the taxonomy from the Phase-0 raw reads, then classify sessions
with a **map-node graph pinned to a cheap model** (haiku-class) — dogfood,
not regex (Scripture: YAMLGraph + LLM over complex regex).

**R-4 (frozen):** LLM-assisted bulk classification MUST use a classifier
graph authored via the governed authoring route (`scripts/author.sh`),
with explicit cheap-model pin, lint, smoke record, and sanitized
fixture/sample output. Manual classification is allowed only for the
Phase-0 seed and cannot satisfy the 80% token-volume threshold.

### Phase 3 — Rank

Score each shape: `session_count × median_token_cost_range ×
extractability`, where extractability is a per-clause verdict against the
five prompt-contract clauses plus an existing-graph-overlap check
(`yamlgraph graph list` task-shape clauses).

### Phase 4 — Deliver

- Ranked candidate table in `docs/FR-884-session-task-shapes.md`
  (sanitized — shapes and counts, no transcript content).
- Top-3 candidates each get a one-paragraph proposal to
  `.chaplain/inbox/` naming: the task shape, its measured frequency/cost,
  the pinned model, and the first consumer (`would_you_use_this`).
- **R-5:** proposals are sanitized drafts only — shape label, aggregate
  counts/ranges, per-clause extractability verdict, pinned-model
  recommendation, first consumer. FR-884 must not implement, author,
  judge, or review any extracted route, and no transcript-derived
  specifics or customer-identifying facts may enter the inbox.
- If no shape clears the extractability bar, that verdict — with
  evidence — is an acceptable outcome.

## Out of Scope

- Implementing any extracted route (follow-up FRs).
- Repinning `validate-session.yaml` off Opus 4.6 (separate one-line
  proposal; different evidence base).
- New telemetry instrumentation.

## Constraints

- **Privacy (FR-874 precedent — binding, mechanized per R-3):** yamlgraph
  is a PUBLIC repo and the workspace spans customer projects; session
  transcripts contain customer-operational facts that secret-grepping
  cannot catch. Publication rules for every committed artifact:
  - repo visibility recorded in the FR before any research artifact is
    committed;
  - no transcript excerpts, exact session titles, prompt snippets,
    customer/project names, or local absolute paths;
  - aggregation buckets with `session_count < 3` collapsed into
    `rare/other`;
  - a meaning-level privacy checklist completed and recorded in this FR
    before each commit.
  Raw reads and intermediate dumps live in `tmp/` (gitignored).
- Read-only over all session stores.
- Cost figures reported as ranges (cache-read conflation).
- Classification graph must pin its model explicitly — an unpinned
  copilot node inherits the CLI's ambient default, which is the very
  failure mode under investigation.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: The FR records the exact analysis window and timezone and uses
      that same window for raw-read sampling, token-volume denominator,
      taxonomy coverage, and candidate ranking.
- [ ] AC-02: Before implementation authority activates, a sanitized raw-read
      log exists for ≥10 full sessions read end-to-end (5 highest-token in
      window + 5 random); each row records a non-identifying surprising
      detail, stratum, date bucket, and privacy classification; zero
      transcript excerpts.
- [ ] AC-03: A stdlib-only read-only script under `scripts/vscode/`
      inventories chatSessions / debug-log price sheets / audit traces and,
      if used, chronicle SQLite by session id; missing optional sources are
      reported as unavailable, never silently substituted or dropped.
- [ ] AC-04: Tests with synthetic fixtures prove the script parses session
      ids, models, prompt/output tokens, timestamps, and cost ranges without
      reading the operator's real VS Code stores.
- [ ] AC-05: Taxonomy ≤12 shapes, each with one-line inclusion criteria and
      a per-clause extractability verdict (one judgement, closed inputs, one
      validator-covered output shape, stateless, bounded).
- [ ] AC-06: ≥80% of interactive token volume in the frozen window is
      classified, or the research report records the deficit, the
      unclassified fraction, and why the taxonomy is not extraction-stable.
- [ ] AC-07: Ranked candidate table reports sanitized shape label, session
      count, token/cost range, per-clause extractability, existing
      `Task shapes:` graph overlap, and `builders_never_call` witness rate.
- [ ] AC-08: Public committed artifacts contain no transcript excerpts,
      exact session titles, customer/project names, local absolute paths, or
      singleton-identifying rows; `session_count < 3` buckets collapsed to
      `rare/other`; meaning-level privacy review recorded in the FR.
- [ ] AC-09: If LLM-assisted bulk classification is used, the classifier is
      a YAMLGraph map-style graph authored via the governed authoring route,
      pins a cheap model, lints clean, has a smoke record, and writes only
      sanitized outputs.
- [ ] AC-10: Up to three follow-up proposals filed to `.chaplain/inbox/`
      only after passing AC-08; each contains sanitized aggregate evidence,
      pinned-model recommendation, and first consumer, and implements no
      route. If none clear the bar, the report states "none extractable"
      with evidence.
- [ ] AC-11: FR updated with implementation status, decisions, deviations,
      exact commands run, and links to committed artifacts; diary
      reflection included.

## Alternatives Considered

- **Ask the human what they do all day** — recall bias; telemetry is the
  ground truth the human's memory approximates.
- **LangSmith traces** — cover graph runs only; the ungoverned surface
  under investigation is precisely what LangSmith does not see.
- **Wait for GitHub billing export** — model-level totals only; no task
  shapes, no session joins.
- **Diary sweep** — diaries record insights, not task frequency; sampling
  is biased toward surprising sessions.

## Related

- `docs/diary/diary-2026-08-25-the-invoice-audits-the-doctrine.md` — cost/pin mapping this FR operationalizes
- Scripture: `is_this_a_graph` (FR-853), `read_raw_output_first`, `builders_never_call`
- FR-874 (REJECTED) — privacy precedent for exporting workspace-derived data
- `.github/skills/{graph-authoring,judge-fr,review-pr}/adapters/` — sole-route pattern being extended
- `scripts/vscode/` (`now.py`, `ledger.py`, `portrait.py`) — read-only introspection suite to extend
- `.github/hooks/logs/audit.jsonl` — per-session tool-call traces

## Implementation Status

**2026-08-25 — Phase 0/1 (enforcement session):**

- AC-03/AC-04 done first (TDD): `scripts/vscode/session_shapes.py` —
  stdlib-only read-only inventory over chatSessions + price sheets + audit
  traces, window-filtered; synthetic-fixture tests committed RED→GREEN.
- Census: **74 sessions, ~650M prompt tokens** in the frozen window.
- **AC-02 done — authority unlocked:** all 10 sampled sessions read
  end-to-end (472-turn max). Sanitized log: `docs/FR-884-raw-read-log.md`.
  Chat-session files are op-logs (kind 0 snapshot / 1 set / 2 extend), not
  plain JSON — turn reconstruction requires replay; replay helper to be
  folded into `session_shapes.py` with fixture test.
- **Deviation (recorded):** 2 of 10 sampled sessions are forks duplicating
  long shared prefixes; token accounting and classification must dedupe by
  shared turn-prefix before the AC-06 denominator is computed. Not in the
  judged plan; surfaced only by the raw read.
- **Operator decision (R-4 route confirmed):** Phase-2 bulk classification
  runs as a yamlgraph **map** (per-session skeleton → shape verdict) +
  **reduce** (aggregate counts) with an explicit cheap mini-model pin
  (aaa-gpt-x.x-mini class) — this is what makes the full 74-session corpus
  (and larger windows) affordable, vs. the 10-session manual ceiling.
- Privacy review of committed artifacts: raw-read log carries pseudonyms,
  buckets, and paraphrased shape clues only; skeletons and any
  customer-adjacent content remain in `tmp/` (gitignored). Repo visibility
  re-verified: PUBLIC.

Next: fold replay into `session_shapes.py` (fixture-tested), author the
classifier map graph via the sole route, classify the deduped corpus, rank,
report (D-5), file proposals (D-6).
