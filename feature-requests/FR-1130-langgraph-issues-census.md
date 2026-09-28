# Feature Request: LangGraph upstream issues census — solves / inherits / leaves untouched

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Requested:** 2026-09-28
**First consumer / first event:** the operator choosing the next framework FRs
— the first event is reading the three disposition lists this census produces
and filing (or refusing) the candidate FRs they name.
**Research:** [FR-1130.research.md](FR-1130.research.md) (brief
`research-briefs/langgraph-issues-census.md`, run 2026-09-28, azure
`aaa-gpt-5.4-mini`, personas: os-infra-primitivist, data-process-planner,
yamlgraph-native-planner, subtractionist, librarian)
**Requirement:** REQ-YG-717 (new), capability **CAP-294 GitHub issues census**

## Summary

Add a gh-issues discover / versions / extract adapter trio to corpus_census,
run a full census of every `langchain-ai/langgraph` issue and pull request
(7,531 measured 2026-09-28), classify each into one closed pain category,
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

### Raw read (12 items, end-to-end)

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

Surprises that shaped the plan: 7 of 12 readable items are not pain reports
(docs, promo, logos, CLI plumbing); most PRs carry no label; the `external` /
`missing-issue-link` labels are bot bookkeeping, not topic signals.

## Ideal Result

One committed report lists, for every pain category upstream, its item count
(issues vs PRs, open vs closed), the upstream labels that co-occur, three to
five cited items per category that a reader can open, and a disposition —
**solves** (YAMLGraph's YAML layer removes the pain; cite the mechanism),
**inherits** (YAMLGraph passes it through; a candidate FR or an explicit
"accept"), **untouched** (outside YAMLGraph's surface; explicit disposition).
Category counts sum to the discovered population; every cited number exists
upstream. Re-running next month costs LLM spend only for items whose
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

## Proposed Solution

### 1. Adapter module (new, RED/GREEN)

`examples/demos/corpus_census/adapters/gh_issues_adapters.py` with manifests
`gh-issues-discover.tool.yaml`, `gh-issues-versions.tool.yaml`,
`gh-issues-extract.tool.yaml`, `gh-issues-crosstab.tool.yaml`.

- **Source grammar:** `<owner>/<repo>` or `<owner>/<repo>:<n>` — `n` selects
  `n` items evenly spaced across the number-sorted population (deterministic
  smoke sample spanning old and new items). Malformed source raises.
- **`gh_issues_discover(state) -> list[str]`** — loads the on-disk cache
  `tmp/gh-issues-cache/<owner>__<repo>.json` (records keyed by number, each
  carrying `updated_at`), fetches
  `gh api --paginate "repos/<o>/<r>/issues?state=all&per_page=100[&since=<max updated_at>]"`
  with a `--jq` projection to one JSON object per line, merges by number
  (newer `updated_at` wins), writes the cache atomically, returns refs
  `<owner>/<repo>#<number>` sorted by number. Raises on non-zero `gh` exit,
  a malformed line, a record missing `number`/`updated_at`, or an empty
  population. Never logs-and-returns `[]` (the `daily_digest` `fetch_hn`
  pattern swallows errors; not reused).
- **`gh_issues_versions(state) -> dict[str, str]`** — `{ref: updated_at}` from
  the cache, same selection as discover; the FR-1120 memo key.
- **`gh_issues_extract(state) -> str`** — one ref → JSON bundle from the
  cache: kind (`issue`/`pr`), merged (PRs), state, state_reason, labels,
  title, body head (bounded chars), comments, reactions, created/closed dates.
  No per-item API call. Raises when the ref is absent from the cache or the
  record lacks `title`.
- **`gh_issues_crosstab(state) -> dict`** — reads the reduced ledger JSONL and
  the cache; writes a markdown crosstab: category × kind × open/closed, top
  upstream labels per category, and up to 5 cited refs per category. Raises
  if any ledger `item_ref` is absent from the cache, if any cited label is not
  on the item, or if category counts do not sum to the ledger row count
  (abstained and row-failed are counted as their own rows, never dropped).

### 2. Pain categories (closed label set)

Drafted from the 12 raw reads plus the upstream label list; every label has
non-empty inclusion terms (`junk_drawer_cap` — there is no `other`; the
model abstains instead, and abstentions are counted):

`state-schema-reducers`, `streaming`, `checkpoint-persistence`,
`interrupt-resume-hitl`, `subgraph-config-propagation`,
`control-flow-routing` (conditional edges, Send, recursion limit, parallel
branches), `prebuilt-agents-tools`, `model-provider-integration`,
`functional-api`, `typing-api-ergonomics`, `async-concurrency-performance`,
`error-handling-retry`, `observability-visualization`,
`platform-server-cli-sdk`, `docs`, `maintenance-non-pain` (dependency bumps,
CI, release, lint, internal refactor, test infrastructure), `spam-invalid`.

Passed as `--var labels=` (FR-940 closed-vocabulary normalization in
`reduce_ledger`) with the definitions in `--var rubric=`. The smoke decides
whether they stand.

### 3. Sibling graph via author.sh

`examples/demos/langgraph_issues_census/graph.yaml`: corpus_census shape with
`versions` slot, `map_memo_split`/`map_memo_merge` around extract and judge
(person_profile_census precedent), `max_items` ≥ population with
`on_overflow: error`, bounded `max_concurrency`, reuse of corpus_census
`judge_item` and `reduce_ledger`, and a final `gh_issues_crosstab` node. The
10-item smoke runs through the unchanged corpus_census graph (10 < 200).

### 4. Deliverable

`examples/demos/langgraph_issues_census/results/` (upstream data is public):
ledger JSONL, crosstab markdown, and `dispositions.md` with the three lists.
Dispositions are decided **after** the census by reading the cited rows per
category — not frozen here. Each row names either a candidate FR (title + one
sentence) or an explicit disposition (`accept`, `out of scope`, `already
covered by FR-XXX`).

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

- [ ] RED then GREEN commits for `gh_issues_adapters.py`: paging projection
  parse, cache merge keyed on number + `updated_at` with `since=` on re-run,
  evenly-spaced `:<n>` selection, versions map, extract bundle, and a raise
  per failure class (gh exit ≠ 0, malformed line, missing field, empty
  population, ref absent from cache, crosstab sum mismatch, crosstab unknown
  ref). Tests tagged `@pytest.mark.req("REQ-YG-717")`.
- [ ] `yamlgraph graph lint` clean for the sibling graph (authored via
  `scripts/author.sh`, `tmp/draft-authoring-report.md` present).
- [ ] 10-item smoke ledger committed to the FR with each row read against its
  raw item; misclassifications recorded and resolved before the full run.
- [ ] Full census ledger covers the discovered population: ledger rows ==
  discovered refs; category counts (including abstain and row-failed) sum to
  that total.
- [ ] Every cited issue number resolves via `gh api` and every cited label is
  on that item (scripted check, output recorded).
- [ ] `dispositions.md` has three lists; every row is a candidate FR or an
  explicit disposition.
- [ ] CAP-294 / REQ-YG-717, changelog fragment, diary entry with **Seed:**.
- [ ] Completion table below filled from witnesses, with Unplanned operations.

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

**Unplanned operations:** (filled at completion)
