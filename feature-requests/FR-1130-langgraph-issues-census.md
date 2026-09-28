# Feature Request: LangGraph upstream issues census — solves / inherits / leaves untouched

**Priority:** MEDIUM
**Type:** Feature
**Status:** Partially enforced — pipeline shipped, census NOT run
(operator stopped the full run 2026-09-28; see Implementation Status).
Judged APPROVED WITH REVISIONS
([judgement](FR-1130-langgraph-issues-census.judgement.md), copilot backend,
2026-09-28); R-1…R-6 folded 2026-09-28
**Requested:** 2026-09-28
**First consumer / first event:** the operator choosing the next framework FRs
— the first event is reading the three disposition lists this census produces
and filing (or refusing) the candidate FRs they name.
**Research:** [FR-1130.research.md](FR-1130.research.md) (brief
`research-briefs/langgraph-issues-census.md`, run 2026-09-28, azure
`aaa-gpt-5.4-mini`, personas: os-infra-primitivist, data-process-planner,
yamlgraph-native-planner, subtractionist, librarian)
**Requirement:** REQ-YG-717 (new), capability **CAP-294 GitHub issues census**
**Prior art:** census family dispositioned in §5 (FR-892, FR-899, FR-936,
FR-939, FR-940, FR-943, FR-957, FR-962, FR-983, FR-1032, FR-1058, FR-1086,
FR-1116, FR-1120). Gate hits FR-802 (node-type usage census — counts
YAMLGraph's own node types, not upstream issues), FR-893 (diary trap census —
local diary corpus), FR-896 (cross-repo pattern census — sibling repos'
code): same census shape, different corpus; nothing reused, none changed.

## Summary

Add a gh-issues discover / versions / extract adapter trio to corpus_census,
run a full census of every `langchain-ai/langgraph` issue and pull request
(7,531 measured 2026-09-28), assign each to exactly one category of the
frozen FR-1130 taxonomy (§2), report **item counts** (never unique-pain
totals),
cross-check the categories against upstream labels and open/closed state, and
deliver three lists: pains YAMLGraph **solves**, **inherits**, and **leaves
untouched** — every row a candidate FR or an explicit disposition.

## Value Statement

The operator gets the upstream defect record, counted, instead of remembered
anecdotes when choosing which LangGraph surfaces YAMLGraph should harden next.

## Problem

YAMLGraph compiles YAML to LangGraph, so every upstream pain is — for a
YAMLGraph user — removed by the YAML layer, inherited unchanged, or outside
YAMLGraph's surface. Nobody has measured which. Roadmap choices on state,
streaming, checkpointing, subgraph config propagation (FR-1058) and interrupts
are made from the few issues someone happened to see.

Measured 2026-09-28:

| Probe | Result |
|---|---|
| `search/issues q=repo:langchain-ai/langgraph` | 7,531 total; 1,654 issues (587 open); 5,877 PRs (244 open) |
| search page 11 × 100 | HTTP 422 "Only the first 1000 search results are available" |
| `repos/…/issues?state=all&per_page=100` | cursor paging (`after=`, no `last` rel); issues + PRs together; `pull_request.merged_at` present |
| 16 sampled issue numbers | 5 returned 404 (6100, 2800, 800, 3000, 6800) — numbers are shared with Discussions |
| rate limits | core 5,000/h, search 30/min |
| `examples/demos/corpus_census/adapters/` | no gh-issues manifest (gh-org, gh-repo, gh-pr, gh-authored-prs only) |
| `corpus_census/graph.yaml` | `max_items: 200` on both maps; overflow raises (FR-939) — 7,531 cannot run through it |
| `corpus_adapters.py` | 384 lines — a new adapter family there breaches the 400-line target |

### Raw read (11 items, end-to-end)

Correction at judgement fold: the first draft said 12; the scratch record
(`tmp/fr1130/raw10.txt`, `raw10b.txt`, plus #7000 fetched alone) holds 11
readable records. The 11 become the committed fixture (R-1).

- **#6534** (issue, open, `bug,pending,external`): a second `interrupt()` after
  `Command(goto=…)` resumes the wrong node; **#8200** (external PR, closed
  unmerged, `missing-issue-link`) is its fix — "binds resume to goto target
  when another interrupt is pending". An issue and its fix PR land in the same
  category; PR/issue pairs must not be double-counted as two pains in the
  narrative (counts stay per-item).
- **#9050** (issue, open, `bug,external`): `libs/checkpoint` Redis test
  fixture hardcodes `host="localhost"` — a checkpoint-package *test* pain, not
  a runtime checkpoint pain.
- **#5000** (issue, open, `type checking,internal`): make `StateGraph` generic
  on `StateT/InputT/OutputT/ContextT`.
- **#5300** (issue, closed/completed, `question`): `create_react_agent` with
  Gemini 2.5 `include_thoughts` — prebuilt agent × provider.
- **#4500** (PR, merged, no label): custom base image for `langgraph` CLI
  docker commands — platform/CLI.
- **#3900, #1500, #2000** (PRs, merged, no label): one-word docs fixes.
- **#7400** (PR, closed unmerged): promotional "Tardygrada" pitch; **#7000**
  (PR, closed unmerged): "feat: new logos" with empty body. Not pain reports.

Surprises that shaped the plan: 6 of 11 readable items are not pain reports
(3 docs, promo, logos, CLI plumbing); most PRs carry no label; the `external` /
`missing-issue-link` labels are bot bookkeeping, not topic signals.

## Ideal Result

One committed report assigns every item of one frozen, complete upstream
snapshot to exactly one category of the frozen FR-1130 taxonomy and lists,
per category, its **item count** (issues vs PRs, open vs closed), the upstream
labels that co-occur, between `min(3, N)` and `min(5, N)` deterministically
cited items a reader can open, and an advisory disposition —
**solves** (YAMLGraph's YAML layer removes the pain; cite the mechanism),
**inherits** (YAMLGraph passes it through; a candidate FR or an explicit
"accept"), **untouched** (outside YAMLGraph's surface; explicit disposition).
Category item counts sum to the snapshot population with zero final abstained
or row-failed rows; every cited number exists upstream. Re-running next month
re-lists the whole repository but spends LLM calls only on items whose
`updated_at` changed.

## Planned Operations

```yaml
probes:
  - "read precedent FR-899, FR-962, FR-1116, FR-1120, FR-943 — decides adapter shape, reducer reuse, row-failure containment and memo wiring (done: see Problem)"
  - "grep corpus_census adapters for gh-issues — absent, so discover/versions/extract are new RED/GREEN work (done: absent)"
  - "gh api search total_count vs the 1,000 cap — 7,531 > cap, so the REST list endpoint with cursor paging is the discover boundary (done)"
  - "read 10 raw issues end-to-end before drafting categories (done: 12 read, see Raw read)"
  - "census cost: 7,531 items x per-item input tokens x cheap-map price, before any smaller alternative (done: see Proposed Solution, Cost)"
  - "corpus_census graph.yaml max_items vs population — 200 < 7,531, so the full run needs a sibling graph with a raised cap and memo wiring"
  - "measure real per-item input and output tokens on the 10-item smoke — re-costs the full run before it starts"
  - "read every smoke ledger row against its raw issue — decides whether categories stand"
branches:
  - "10-item smoke misclassifies (any row whose category a reader of the raw item rejects) → back to plan, revise category definitions, re-smoke"
  - "rate limit or transient failure on discover → paged, cached discover keyed on number + updated_at; re-run resumes from the cache with since=max(updated_at)"
  - "sibling graph and any prompt are governed graph.yaml / prompts/*.yaml → scripts/author.sh, never manual"
  - "smoke per-item tokens push the full-run estimate above 3x the first estimate → stop, record, ask the operator before the full run"
  - "full run row-failed or abstained share above 5 percent → read those rows before accepting the census; revise and re-run only the affected items via the memo"
  - "a cited issue number or label fails verification → fix the report, never the check"
delegations:
  - "research.sh: 1 run (done)"
  - "judge.sh: 1 run, 2 if revisions are disputed"
  - "author.sh: 1 run for the sibling census graph (and pain-category prompt if the generic judge_item cannot carry the closed label set)"
  - "census: smoke on 10 items through examples/demos/corpus_census/graph.yaml, then full population of 7,531 through the sibling graph with the map memo"
waits:
  - "judge"
  - "author.sh run"
  - "full census run"
commands:
  - scripts/research.sh
  - scripts/judge.sh
  - scripts/author.sh
  - yamlgraph graph lint
  - yamlgraph graph run examples/demos/corpus_census/graph.yaml
  - yamlgraph graph run examples/demos/langgraph_issues_census/graph.yaml
  - pytest tests/unit/test_fr1130_gh_issues_adapters.py
  - python scripts/req_coverage.py --strict
```

Revisions at judgement fold (2026-09-28; the block above is kept as written
before `judge.sh` so planned-vs-actual stays comparable):

```yaml
superseded:
  - "branch 'rate limit or transient failure on discover → … since=max(updated_at)' → replaced by R-2: every run re-lists the full repository; a failed listing aborts before model spend and leaves the prior snapshot intact"
  - "branch 'row-failed or abstained share above 5 percent → read' → replaced by R-1: any final abstain/row_failed row blocks the crosstab; resolve and re-run those items"
added:
  probes:
    - "read the judgement and fold R-1..R-6 (done)"
    - "status/verdict of every cited prior-art FR for §5 (done)"
    - "precedent: person_profile_census graph/tools memo glue and FR-1120 provider-free graph test"
  commands:
    - pytest tests/unit/test_fr1130_census_graph.py
    - "pytest tests/unit/ for FR-940/943/1116/1120 suites"
    - "yamlgraph graph run … --token-usage (smoke and full run)"
    - "python -m … gh_issues_report verify examples/demos/langgraph_issues_census/results"
    - "sqlite3 <memo store> DELETE for unresolved rows (only if needed)"
```

## Proposed Solution

### 1. Adapter modules (new, RED/GREEN) — R-2

Two modules under `examples/demos/corpus_census/adapters/` keep each below the
400-line target: `gh_issues_adapters.py` (snapshot, discover, versions,
extract) and `gh_issues_report.py` (memo glue, crosstab, manifest, verify).
Manifests: `gh-issues-discover.tool.yaml`, `gh-issues-versions.tool.yaml`,
`gh-issues-extract.tool.yaml`, `gh-issues-crosstab.tool.yaml`.

- **Source grammar** (parsed strictly, anything else raises):
  `<owner>/<repo>` (whole snapshot), `<owner>/<repo>:<n>` (deterministic
  spread sample), `<owner>/<repo>@<a>,<b>,…` (named numbers; every number must
  exist in the snapshot, duplicates raise). Owner/repo match
  `[A-Za-z0-9_.-]+`. Sample formula over the number-sorted population of size
  `P`: `n = 1 → [0]`; `2 ≤ n ≤ P → [i·(P−1)//(n−1) for i in 0..n−1]`
  (distinct because `n ≤ P`; `n = P` is the whole population); `n ≤ 0`,
  non-integer `n`, or `n > P` raise.
- **Snapshot (typed, replace-not-merge).** Every discover run executes one
  fixed argument vector, `["gh", "api", "--paginate", "--jq", JQ,
  "repos/<o>/<r>/issues?state=all&per_page=100"]`, via
  `subprocess.run(check=False, capture_output=True, text=True, timeout=900)`.
  Non-zero exit, timeout, a non-JSON line, a record failing the model,
  a duplicate number, an empty population, or a population above
  `MAX_POPULATION = 10_000` raises **before any model call** and leaves the
  previous snapshot byte-identical. Only after every line validates is
  `tmp/gh-issues-cache/<owner>__<repo>.json` atomically replaced (temp file +
  `os.replace`). No `since=` merging: an item absent from the listing is
  absent from the snapshot. Snapshot envelope (Pydantic `IssueSnapshot`):
  `schema_version` (int constant `SCHEMA_VERSION = 1`), `repository`,
  `query` (the endpoint string), `retrieved_at` (UTC `YYYY-MM-DDTHH:MM:SSZ`),
  `count`, `sha256` (of the canonical JSON of `items`), `items` sorted by
  number.
- **Record model** (Pydantic `IssueRecord`, `extra="forbid"`), projected by JQ:
  `number` int > 0; `kind` `issue|pr` (`pull_request` key present → `pr`);
  `merged` bool for PRs (`pull_request.merged_at != null`), `null` for
  issues; `state` `open|closed`; `state_reason` str or null; `title` non-empty
  str; `body_head` = first 1,500 chars of `body` (null → `""`); `labels`
  list of label names, at most 50 (more raises); `comments` int ≥ 0 (count
  only, no comment text is fetched); `reactions` int ≥ 0
  (`reactions.total_count`); `created_at`, `updated_at` non-empty UTC
  timestamps; `closed_at` timestamp or null. A null or missing required field
  raises. Never logs-and-returns `[]` (the `daily_digest` `fetch_hn` pattern
  swallows errors; not reused).
- **`gh_issues_discover(state) -> list[str]`** — refresh the snapshot, apply
  the source selection, return refs `<owner>/<repo>#<number>` in number order.
- **`gh_issues_versions(state) -> dict[str, str]`** — `{ref: updated_at}` for
  exactly the selected refs, read from the snapshot this run wrote; the
  FR-1120 memo key. Missing, extra, or empty versions raise.
- **`gh_issues_extract(state) -> str`** — one ref → the record's JSON bundle
  from the snapshot. No per-item API call. Raises when the ref is absent.
- **Memo glue (`gh_issues_report.py`)** — `gh_issues_memo_prepare` (require
  `memo_store`; `memo_inputs` = `rubric`, `labels`, `provider`, `model`;
  `memo_query` = `source`), `gh_issues_pair` (join executed bundles and judge
  outcomes by exact index cover, failures kept as `error` records — the
  person_profile_census `pair_executed` contract), `gh_issues_findings`
  (memo-merged records → the `items`-aligned `findings` list the unchanged
  corpus_census `reduce_ledger` consumes; `error` records become `_error`
  findings, i.e. FR-943 `row_failed` rows).
- **`gh_issues_crosstab(state) -> dict`** — reads the reduced ledger JSONL, the
  snapshot and the fixture canary. Refuses (raises, no artifact) when: any
  ledger ref is absent from the snapshot; ledger rows ≠ selected refs or any
  ref appears twice; any row is `abstain` or `row_failed`; the canary row's
  category differs from its fixture expectation; category item counts do not
  sum to the row count. Otherwise writes `crosstab.md` — category × kind ×
  open/closed **item counts**, top upstream labels per category, and
  citations: the `min(5, N)` lowest-numbered refs of the category, ascending
  (deterministic; ≥ `min(3, N)` follows) with each cited item's labels — and
  `manifest.json` (Pydantic `CensusManifest`): repository, snapshot
  `retrieved_at`/`count`/`sha256`, provider, model, run id, sha256 of every
  memo signature file and of the ledger/crosstab, row and category counts.
  Model-call count, token totals (from `yamlgraph graph run --token-usage`)
  and cost are appended to the manifest from the run log after the run.
- **Verify (`python -m` entry of `gh_issues_report.py verify <results-dir>`)**
  — for every cited ref, one `gh api repos/<o>/<r>/issues/<n>` call: the ref
  resolves and every displayed label is on the item; plus the disposition
  schema check (§4). Output recorded in the FR.

### 2. Frozen taxonomy (closed label set) — R-1

17 categories drafted from the 11 raw reads plus the upstream label list.
There is no `other` (`junk_drawer_cap`); `maintenance-non-pain` and
`spam-invalid` have concrete inclusion terms. **Precedence:** apply rules top
to bottom; the first whose inclusion matches and exclusion does not wins.

| # | Category | Includes | Excludes |
|---|---|---|---|
| 1 | `spam-invalid` | promotion, off-topic pitches, empty-body or test submissions closed unmerged, bot noise | any real defect/feature/doc content |
| 2 | `docs` | changes or requests touching only documentation, docstrings, examples prose, typos, README | code behaviour changes |
| 3 | `maintenance-non-pain` | dependency bumps, CI, release, lint/format, internal refactor, test code and test fixtures (incl. checkpoint-backend test fixtures) | defects users hit at runtime |
| 4 | `interrupt-resume-hitl` | `interrupt()`, `Command(resume/goto)` on resume, human-in-the-loop, breakpoints | checkpoint storage bugs not about resume |
| 5 | `subgraph-config-propagation` | subgraphs, nested graphs, config/context/`RunnableConfig` propagation into children, subgraph state namespaces | interrupts inside subgraphs (→ 4) |
| 6 | `checkpoint-persistence` | checkpointers (memory/sqlite/postgres/redis), store, thread history, time travel, serialization of saved state | test fixtures (→ 3) |
| 7 | `streaming` | `stream`/`astream` modes, events, token streaming, stream output shape | |
| 8 | `state-schema-reducers` | state schema, channels, reducers, `add_messages`, input/output schemas, state updates | typing-only requests (→ 17) |
| 9 | `control-flow-routing` | edges, conditional edges, `Send`, recursion limit, parallel branches, graph compile/structure | |
| 10 | `functional-api` | `@entrypoint`, `@task` | |
| 11 | `prebuilt-agents-tools` | `create_react_agent`, `ToolNode`, `tools_condition`, supervisor/swarm prebuilts, tool calling through prebuilts — wins over provider when a prebuilt is named | |
| 12 | `model-provider-integration` | a specific model/provider's message or feature handling with no prebuilt named | |
| 13 | `platform-server-cli-sdk` | `langgraph` CLI, `langgraph.json`, docker/build, LangGraph Server/Platform, SDK clients, Studio | |
| 14 | `observability-visualization` | tracing, callbacks, logging, graph drawing/mermaid | |
| 15 | `error-handling-retry` | exceptions, error messages, retry policies, `GraphRecursionError` messaging | |
| 16 | `async-concurrency-performance` | async execution, threading, concurrency, memory/CPU/latency | |
| 17 | `typing-api-ergonomics` | type hints, generics, public API shape and naming, deprecations | |

**Rubric text** (passed as `--var rubric=`) = this table + the precedence
sentence + "abstain only when the item has no title and no body". Labels are
passed as `--var labels=` (FR-940 closed-vocabulary normalization in the
unchanged `reduce_ledger`); the generic corpus_census `judge_item` prompt
carries the rubric — no new prompt.

**Fixture** `tests/fixtures/fr1130/raw_read.json`: the 11 raw-read records in
the `IssueRecord` projection with expected category + one-line rationale:

| Ref | Expected | Role |
|---|---|---|
| #6534 | `interrupt-resume-hitl` | smoke |
| #8200 | `interrupt-resume-hitl` | smoke |
| #9050 | `maintenance-non-pain` (test fixture) | smoke |
| #5000 | `typing-api-ergonomics` | smoke |
| #5300 | `prebuilt-agents-tools` (prebuilt named) | smoke |
| #4500 | `platform-server-cli-sdk` | smoke |
| #3900, #1500, #2000 | `docs` | smoke |
| #7000 | `spam-invalid` (empty-body logos PR, unmerged) | smoke |
| #7400 | `spam-invalid` (promotional pitch) | **withheld canary** |

The smoke source is `langchain-ai/langgraph@6534,8200,9050,5000,5300,4500,3900,1500,2000,7000`.
A smoke row whose category disagrees with the fixture is a finding: either
the rubric is revised in this FR (table + fixture updated **before** the paid
full run) or the fixture expectation is corrected with a recorded rationale.
The smoke never silently redefines scope.

**Final completeness.** Provisional runs may contain `abstain` / `row_failed`
rows; the accepted census contains zero of either. Resolution: read the rows;
transient `row_failed` → delete those keys from the memo store
(`sqlite3 <store> "DELETE FROM memo WHERE key IN (…)"`) and re-run, which
re-judges only them; abstentions caused by a rubric gap → revise §2 and
re-run (signature change re-spends; the 3× cost gate applies).

### 3. Sibling graph via author.sh — R-4

`examples/demos/langgraph_issues_census/graph.yaml`, authored through
`scripts/author.sh`. State/tool contract:

- **vars:** `source`, `rubric`, `labels`, `provider`, `model`, `output_path`
  (ledger), `results_dir`, `fixture_path`, `memo_store` (required).
- **nodes:** `memo_prepare` → `discover` (slot, gh-issues-discover) →
  `versions` (slot, `args: state: "{state.memo_query}"`) → `memo_split`
  (shared `map_memo_split`; `signature_files` = the sibling `graph.yaml`,
  `corpus_census/prompts/judge_item.yaml`, `corpus_census/tools.py`,
  `gh_issues_adapters.py`, `gh_issues_report.py`) → `extract_items` (map over
  `memo.result.todo`, slot extract) → `judge_items` (map, corpus_census
  `judge_item`, `provider`/`model` from state, `temperature: 0`,
  `on_error: skip`) → `pair` → `memo_merge` (shared) → `findings` →
  `reduce_ledger` (unchanged corpus_census) → `crosstab`.
- **ceilings:** `max_items: 10000` on both maps (= `MAX_POPULATION`; overflow
  raises per FR-939), `max_concurrency: 8`.
- **invalidation:** memo key = ref, version = `updated_at`; signature =
  `memo_inputs` (rubric, labels, provider, model) + signature-file hashes —
  so a taxonomy/rubric, label, provider/model, prompt, extraction
  `SCHEMA_VERSION` or census-code change re-runs every item; unchanged
  inputs make zero extract/judge calls.

The 10-row smoke runs through the unchanged corpus_census graph (10 < 200)
with the gh-issues discover/extract slots.

**Provider-free end-to-end witness** (`tests/unit/test_fr1130_census_graph.py`):
the sibling graph over the fixture with `gh` and `execute_prompt` patched
(FR-1120 test precedent) — discovery, sampling, extraction, memo split/merge,
one simulated judge failure, recovery of only that item after deleting its
memo key, reducer normalization, canary pass and canary-mismatch refusal,
crosstab, and a second unchanged run with zero judge calls and byte-identical
ledger/crosstab.

### 4. Deliverable and dispositions — R-3, R-5

`examples/demos/langgraph_issues_census/results/` (upstream data is public):
`ledger.jsonl`, `ledger.md`, `crosstab.md`, `manifest.json`,
`dispositions.md`, `verify.txt`.

All totals are **item counts**. No unique-pain total is emitted and no
heuristic issue/PR de-duplication is done. Prose that links an issue to its
fix PR cites both refs and a relationship witness quoted from the snapshot
(e.g. a `Fixes #n` span); the link never alters arithmetic.

`dispositions.md` is an **advisory report for the operator**, not a roadmap
decision: exactly three sections `## solves`, `## inherits`, `## untouched`;
exactly one row per frozen category across them; columns `category | issues
open/closed | PRs open/closed | citations | YAMLGraph evidence |
recommendation`. Recommendation is exactly one of `candidate FR: <title> —
<one-sentence objective>`, `accept`, `out of scope`, `already covered by
FR-XXX`. Rules: a `solves` row cites a repository mechanism (file path); an
`already covered` row names an existing FR file; an `inherits` row recommends
a candidate FR or `accept`; an `untouched` row recommends `out of scope`.
Filing candidate FRs, changing FR priorities/statuses, or implementing any
discovered fix is outside FR-1130.

### 5. Prior art — R-6

| FR | Status | Reused contract | Distinction / change by FR-1130 |
|---|---|---|---|
| FR-892 | Completed | corpus_census injected discover/extract slots | reused; unchanged |
| FR-899 | In Progress (enforced) | gh adapter pattern, azure census run | new gh-issues family in a new module; FR-899 adapters unchanged |
| FR-936 | SPLIT, no implementation | — | successors FR-939/FR-957; nothing reused directly |
| FR-939 | Implemented | map overflow raises | relied on for `max_items: 10000`; unchanged |
| FR-940 | ENFORCED rev 2 (first judgement REJECTED) | closed-vocabulary normalization in `reduce_ledger` | **prerequisite**; unchanged |
| FR-943 | ENFORCED rev 2 | `row_failed` containment | **prerequisite**; unchanged |
| FR-957 | Judged, not enforced | — | not relied on; retries via memo re-run instead |
| FR-962 | Approved with Revisions | person-profile census shape | precedent only; unchanged |
| FR-983 | SPLIT | — | coverage gate not relied on; crosstab refuses on any unresolved row instead |
| FR-1032 | Proposed | — | extract here is a snapshot read; not needed, untouched |
| FR-1058 | Enforced | — | a topic the census counts (`subgraph-config-propagation`); untouched |
| FR-1086 | Judged | `yamlgraph graph lint` | lint used as-is |
| FR-1116 | Implemented | shared `map_memo_split`/`map_memo_merge` | **prerequisite**; unchanged |
| FR-1120 | Implemented | caller-supplied versions memo, pair/merge contract | **prerequisite**; glue re-implemented for gh-issues, shared memo unchanged |

If enforcement finds a prerequisite's shipped contract cannot carry the
frozen graph without changing that shared surface, enforcement stops and the
FR returns to planning (judgement C-7).

### Cost

First estimate 7,531 × ~2,000 input tokens ≈ 15M input, ~150 output tokens per
item ≈ 1.1M output. Verified list prices 2026-09-28:

| Model | $/MTok in / out | Full-census estimate |
|---|---|---|
| azure `aaa-gpt-5.4-mini` (OpenAI list gpt-5.4-mini) | 0.75 / 4.50 | ≈ $16 |
| Inception `mercury-2` | 0.25 / 0.75 | ≈ $5 |
| Claude Haiku 4.5 | 1.00 / 5.00 | ≈ $21 (Anthropic key currently 401s) |

The full census is affordable; no smaller sample replaces it
(`map_reduce_the_corpus`). Default: azure `aaa-gpt-5.4-mini`. The smoke
measures real per-item tokens and re-costs before the full run.

## Acceptance Criteria

Folded from the judgement's AC-01…AC-16 (the fixture holds 11 records, not
12 — see Raw read correction).

- [ ] AC-01: §2 holds the full rubric with inclusion, exclusion and
  precedence; the committed fixture has 11 records with expected categories and
  rationales, ten named smoke rows and one withheld canary (#7400).
- [ ] AC-02: RED then GREEN commits prove strict source parsing and sample
  indices for `n=1`, an interior `n`, `n=P`, and rejection of zero, malformed,
  or over-population `n`; named `@` selection rejects unknown and duplicate
  numbers.
- [ ] AC-03: Discovery executes the one frozen argument vector, validates
  every line as `IssueRecord`, and rejects command failure, timeout, malformed
  JSON, invalid/missing fields, duplicate numbers, empty population and
  over-ceiling population, with no model call on failure.
- [ ] AC-04: A successful discovery atomically replaces the typed snapshot
  (repository, query, retrieved_at, ordered items, count, schema version,
  hash); a failed discovery leaves the prior snapshot byte-identical; an item
  missing from the next listing is missing from the next snapshot.
- [ ] AC-05: Versions returns exactly `{ref: updated_at}` for the selected
  refs and rejects missing, extra, empty or invalid versions; extraction
  returns the frozen bundle and rejects an absent ref without a per-item API
  call.
- [ ] AC-06: The sibling graph has `max_items: 10000`, `max_concurrency: 8`,
  carries every §3 memo-signature input, is authored through
  `scripts/author.sh`, and the substantive `tmp/draft-authoring-report.md`
  records lint and smoke evidence.
- [ ] AC-07: The provider-free end-to-end fixture run produces one ledger row
  per ref, passes the canary, contains a simulated judge failure, re-runs only
  that item, and reaches zero abstained and zero row-failed rows.
- [ ] AC-08: An unchanged second run makes zero extract/judge calls and emits
  byte-identical ledger/crosstab; changing rubric, labels, provider/model,
  prompt, `SCHEMA_VERSION` or a signature file invalidates the memo entries.
- [ ] AC-09: Final ledger rows == snapshot refs; each ref exactly once; each
  row one frozen category; category item counts sum to the snapshot count; no
  final `abstain` or `row_failed` row.
- [ ] AC-10: Every non-empty category cites between `min(3, N)` and
  `min(5, N)` distinct refs by the frozen lowest-number rule; each citation
  belongs to its category and snapshot; `verify.txt` proves every ref resolves
  via `gh api` and every displayed label is on its item.
- [ ] AC-11: All totals are labeled item counts; any issue/fix-PR link in
  prose cites both refs and a relationship witness and does not alter
  arithmetic; no unique-pain total.
- [ ] AC-12: `dispositions.md` has exactly one typed row per frozen category
  in exactly three sections, each row satisfying the §4 rules (checked by
  `verify`).
- [ ] AC-13: `manifest.json` records provider/model, run id, corpus and
  artifact hashes, item/model-call counts, token usage and measured cost; a
  smoke estimate above 3× the first estimate has a recorded operator approval
  before the full run.
- [ ] AC-14: §5 prior-art table present; no excluded shared/core surface is
  changed; FR-940, FR-943, FR-1116 and FR-1120 tests stay green.
- [ ] AC-15: CAP-294 / REQ-YG-717 own the graph, adapter, result-contract and
  test surfaces; every new test carries `@pytest.mark.req("REQ-YG-717")`;
  `python scripts/req_coverage.py --strict` passes.
- [ ] AC-16: Changelog fragment, implementation status/decisions/deviations,
  completed operation table with unplanned operations, authoring record,
  committed result artifacts, and diary entry with **Seed:** are present.

## Alternatives Considered

| Alternative | Probe | Disposition |
|---|---|---|
| Search API with date slices | page 11 → 422; 7,531 needs ≥ 8 slices each re-checked for the cap, 30/min search limit | Rejected: the list endpoint enumerates all items with no cap and 76 core-rate pages |
| Enumerate issue numbers 1..N | 5 of 16 numbers 404 (Discussions) | Rejected: population is not a number range |
| Per-item `gh api issues/<n>` in extract | 7,531 core calls > 5,000/h | Rejected: list pages already carry the bundle fields; extract reads the cache |
| Subtractionist: drop the census (research row 4) | full-census cost ≈ $5–$21 | Rejected: cheap relative to the roadmap decisions it informs (`map_reduce_the_corpus`) |
| FR-1032 adapter-owned extract cache (Proposed) | extract here is a local cache read; LLM re-spend is covered by the FR-1120 memo | Not needed; FR-1032 untouched |
| Stratified 500-item sample | cost difference ≈ $15 | Rejected: a sample cannot certify "counts sum to population" |
| Reuse `daily_digest` `fetch_hn` | `examples/daily_digest/nodes/sources.py` logs and returns `[]` | Rejected: silently shrinks the corpus (Commandment 6) |

## Related

- FR-892, FR-899, FR-962, FR-943, FR-1116, FR-1120, FR-939, FR-940, FR-1058
- `examples/demos/corpus_census/`, `examples/demos/person_profile_census/`
- `.github/skills/feature-request/SKILL.md` (FR-1129 Planned Operations)

## Implementation Status

| Planned operation | Outcome (ran / did not run / changed) | Witness |
|---|---|---|
| research.sh | ran, 1 run | `FR-1130.research.md` |
| judge.sh | ran, 1 run; R-1…R-6 folded | `3f669e12` |
| gh-issues adapters RED/GREEN | ran | RED `8da482da`, GREEN `7eb56140`; 45 adapter + 13 report tests |
| 10-item smoke via corpus_census | ran twice (1st failed, see unplanned) | `tmp/fr1130/smoke/run.log`; 10/10 rows match the fixture, conf 0.95–0.99; 12,978 in / 882 out / 11 calls |
| read every smoke row | ran | `tmp/fr1130/smoke/ledger.jsonl` vs `tests/fixtures/fr1130/raw_read.json` |
| re-cost from smoke | ran | ≈9M in / 0.6M out ≈ $9.5 < 3× first estimate ($16); no operator gate |
| author.sh sibling graph | changed: 2 runs | brief `2f880871`; run 1 report `tmp/fr1130/authoring-report-run1.md`; run 2 `tmp/draft-authoring-report.md`; GREEN `3fc6ad46` |
| graph provider-free test | ran | RED `8da482da`, RED2 `79733442`, GREEN `3fc6ad46`; 7 pass |
| yamlgraph graph lint | ran | clean (author report + independent re-run) |
| 2-item live smoke of sibling graph | ran | `examples/demos/langgraph_issues_census/demo-output.log`; #6534 `interrupt-resume-hitl`, canary #7400 `spam-invalid` |
| full census (7,532 items) | **did not complete** | run 1 died with its terminal inside discover (no spend); run 2 stopped by operator at 293 judged / 171 rate-limited, before `memo_merge` → nothing memoized, no ledger (`tmp/fr1130/full/run2.log`) |
| gh_issues_report verify | did not run | needs the full ledger |
| dispositions.md | did not run | needs the crosstab |
| manifest usage/cost | did not run | needs the full run |
| req_coverage --strict | ran | exit 0 (`tmp/fr1130/reqcov.log`) |
| FR-940/943/1116/1120 suites | ran | 228 passed incl. FR-1130 (`tmp/fr1130/ac14.log`) |
| memo DELETE for unresolved rows | did not run | no memo store was written |

AC status: AC-01…AC-08, AC-14, AC-15 met by the witnesses above; AC-09…AC-13
and the results/dispositions part of AC-16 are **open** — they require the
full census.

**Decisions and deviations:**

- Author run 1 routed zero-dispatch replays to END before `crosstab`, so a
  memoized `row_failed` ended the run silently. Cause: my graph test expected
  a silent replay. Test corrected (replay must raise, zero judge calls),
  committed RED as `79733442`; brief amended; author run 2 made every edge
  unconditional.
- The loader witness (`IssueRecord` unbuilt when loaded by path) was found by
  smoke #1; its RED was observed in `tmp/fr1130/red_loader.log` but not
  committed separately from GREEN.
- Run 2 disabled LangSmith tracing: every upload returned 403.
- Azure returned token-rate-limit 429s on ~37% of judge calls at
  `max_concurrency: 8`; each would have become a `row_failed` row needing
  memo re-runs. Remaining work: run the full census (lower concurrency or a
  higher-TPM deployment), resolve failed rows, verify, write dispositions.
- The memo persists only at `memo_merge`, after the whole judge map: an
  interrupted full run loses all judged items.

**Unplanned operations:** worktree recreated; Explore subagent; pricing page
fetches; prior-art gate retries (FR ×2, brief ×1); 11 `gh` fetches to build
the fixture; extra test files (`test_fr1130_gh_issues_report.py`,
`test_fr1130_census_graph.py`); failed smoke #1 and the loader witness test;
commit retries from hooks (req-coverage, ruff format ×2, ruff collapsible-if,
demo-proof ×3, end-of-file ×3, changelog ×2, examples README audit); brief
commit split from rubric/labels (demo-proof); `examples/README.md` index
row; second `author.sh` run and RED2 test edit; full run 1 killed with its
terminal; full run 2 relaunched under `nohup` with tracing off; run 2 stopped
by the operator; `llm_bounds.py` read to look for a retry override (none).
