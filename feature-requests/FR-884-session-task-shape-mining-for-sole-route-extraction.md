# Feature Request: Chat-Session Task-Shape Mining for Sole-Route Extraction

**Priority:** HIGH
**Type:** Investigation
**Status:** Proposed
**Effort:** 2 days
**Requested:** 2026-08-25

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
| Chronicle DB (`session_store_sql`) | Session titles, turns, files touched, FR/PR refs, FTS index |
| `.github/hooks/logs/audit.jsonl` | Per-tool-call trace with `session_id` — the action shape of each session |
| `scripts/vscode/ledger.py --by-model` | Requests/tokens/cost-range per day per model |

## Investigation Questions

1. What are the recurring task shapes in interactive sessions over the
   last 60–90 days? (taxonomy, ≤12 shapes)
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
classifier or metric. Stratified sample: the 5 highest-token sessions plus
5 random. Record for each a concrete surprising detail a generated dump
could not produce. Raw reads stay in `tmp/` (see Privacy).

### Phase 1 — Inventory and join

Join chatSessions JSONL (tokens, model) × chronicle (title, files, refs) ×
audit.jsonl (tool-call sequence) on `session_id`. Extend `scripts/vscode/`
(stdlib-only, read-only precedent) rather than new infrastructure.

### Phase 2 — Classify

Derive the taxonomy from the Phase-0 raw reads, then classify sessions
with a **map-node graph pinned to a cheap model** (haiku-class) — dogfood,
not regex (Scripture: YAMLGraph + LLM over complex regex). If a classifier
graph is built, it goes through the sole authoring route
(`scripts/author.sh`) like any other graph.

### Phase 3 — Rank

Score each shape: `session_count × median_token_cost_range ×
extractability`, where extractability is a per-clause verdict against the
five prompt-contract clauses plus an existing-graph-overlap check
(`yamlgraph graph list` task-shape clauses).

### Phase 4 — Deliver

- Ranked candidate table in `research/` (sanitized — shapes and counts,
  no transcript content).
- Top-3 candidates each get a one-paragraph proposal to
  `.chaplain/inbox/` naming: the task shape, its measured frequency/cost,
  the pinned model, and the first consumer (`would_you_use_this`).
- If no shape clears the extractability bar, that verdict — with
  evidence — is an acceptable outcome.

## Out of Scope

- Implementing any extracted route (follow-up FRs).
- Repinning `validate-session.yaml` off Opus 4.6 (separate one-line
  proposal; different evidence base).
- New telemetry instrumentation.

## Constraints

- **Privacy (FR-874 precedent — binding):** yamlgraph is a PUBLIC repo and
  the workspace spans customer projects; session transcripts contain
  customer-operational facts that secret-grepping cannot catch. Committed
  artifacts carry task shapes, counts, and cost ranges ONLY — never
  transcript excerpts. Raw reads and intermediate dumps live in `tmp/`
  (gitignored) and are meaning-level reviewed before any aggregate is
  committed.
- Read-only over all session stores.
- Cost figures reported as ranges (cache-read conflation).
- Classification graph must pin its model explicitly — an unpinned
  copilot node inherits the CLI's ambient default, which is the very
  failure mode under investigation.

## Acceptance Criteria

- [ ] Raw-read log: ≥10 sessions read end-to-end, each with a cited
      surprising detail (sanitized summary in the FR or `research/`)
- [ ] Task-shape taxonomy (≤12 shapes) with one-line inclusion criteria each
- [ ] ≥80% of last-60-day interactive token volume classified into the taxonomy
- [ ] Ranked candidate table: shape, session count, token/cost range,
      per-clause extractability verdict, existing-graph overlap
- [ ] Top-3 candidates filed to `.chaplain/inbox/` (or explicit
      "none extractable" verdict with evidence)
- [ ] Zero customer-identifying content in committed artifacts (meaning-level
      review recorded in the FR)
- [ ] If a classifier graph is built: authored via sole route, lints clean,
      smoke run recorded, model pinned

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
