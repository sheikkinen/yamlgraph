# Problem brief: a rate-limited map fan-out drops 39% of a census and the brief reports the survivors as the whole

**Prior art:** FR-962
(`feature-requests/FR-962-person-profile-census-authored-prs.md`,
Implemented, PR #562) introduced the person-profile census whose
`judge_items` map node and code reducer are the surfaces here; its
"completeness" gate checks that every index has a finding, and its
rollup prints `classification coverage` but does not act on it. FR-943
(`feature-requests/FR-943-census-row-failure-containment.md`) introduced
per-row failure containment (`on_error: skip` producing a `row_failed`
marker instead of aborting the map) — the mechanism that converts a
retry-exhausted row into a silently missing classification, and whose
intent (one bad row must not kill the batch) must be preserved. FR-939
(`feature-requests/FR-939-map-overflow-detection.md`) and FR-027 own
population bounds (`max_items`, overflow at 501) — a cap on *how many*
items, not on *how many at once*; out of bounds. FR-069 owns the map
per-item `timeout` in `yamlgraph/compile/map_compiler.py` and the
one-shot `ThreadPoolExecutor(max_workers=1)` wrapper for it; unrelated
to fan-out width. FR-895 owns the bounded synthesize input
(`BRIEF_TOP_N = 30`) and the fabricated-URL citation boundary in
`render_brief`; its top-N truncation is disclosed nowhere either, but
is by-design and out of scope here. `recursion_limit` plumbing
(`yamlgraph/cli/graph_run_helpers.py:140-143`, `GraphConfig.recursion_limit`)
is the precedent for a graph-level `RunnableConfig` knob reachable
from both `graph.yaml` and the CLI. A REJECTED-FR sweep for
`max_concurrency`, `throttle`, `semaphore`, `rate limit` and `429`
found no prior proposal; FR-104 (parallel chapter workers) mentions
rate limits in passing and was not about the map node.

## Problem statement

On 2026-09-04 the corp person-profile census ran against 259 private
PRs (`source=sheikkinen@<owner>:2025-01-01`, `visibility=["private"]`,
Azure deployment resolving to `gpt-5.4-mini` in `swedencentral`). The
run exited 0 and wrote both artifacts. Measured from `logs/tt-profile.log`
(2864 lines, 09:16:07 → 09:18:51):

| observation | value |
|---|---|
| PRs discovered | 259 |
| `_map_judge_items_sub` completed successfully | 159 |
| `_map_judge_items_sub` failed, skipping | **100** |
| rows with a parsed `change_kind` in the ledger | 147 |
| ledger rollup line `classification coverage` | **56.8%** |
| HTTP 429 responses | 1249 |
| `openai._base_client: Retrying request` lines | 1149 |
| distinct raw 429 body | `Your requests to gpt-5.4-mini for <deployment> in swedencentral have exceeded rate limit.` |

Two independent defects compose:

**1. Fan-out width is not a graph-authoring knob.** `judge_items` is a
`type: map` over 259 items with `max_items: 500` and no concurrency
setting; `graph.yaml` has no field for one and the CLI has no flag.
LangGraph *does* have the primitive: `RunnableConfig["max_concurrency"]`
is honoured by both the sync `BackgroundExecutor` and the async
`AsyncBackgroundExecutor` (`langgraph/pregel/_executor.py:135`, v1.2.9)
via a semaphore around `Send` tasks. Probe on this machine, 40 `Send`
tasks each sleeping 50 ms: default config → peak 12 parallel workers;
`{"max_concurrency": 4}` → peak 4, all 40 results returned. So the
observed flood was 12-wide (the default thread pool), not 259-wide,
and the platform already offers the throttle — yamlgraph never passes
it. Each row then gets yamlgraph's `LLM_MAX_RETRIES=3` with
1 s / 2 s / 4 s backoff (`yamlgraph/config.py:84-86`,
`executor.py:161-176`), and inside each attempt the OpenAI client's own
two retries honouring `Retry-After` — twelve rows retrying in lockstep
against a per-minute quota exhaust nine HTTP attempts in ~7 s and are
dropped by FR-943 containment.

**2. Coverage is computed, printed, and then ignored.**
`_mechanical_rollup` computes `classification_coverage = judged / total`
(`examples/demos/person_profile_census/tools.py:344`) and
`reduce_pr_ledger` prints it into the ledger head (`tools.py:481`).
Nothing gates on it: the reducer's completeness check
(`tools.py:454-457`) verifies that every index has *a* finding —
`row_failed` counts — and the canary gate checks one row. Downstream,
`prepare_brief_input` selects only `judged` rows (`tools.py:551-553`),
`synthesize` receives `rubric` + `rows` and nothing about the
population (`graph.yaml:137-144`), and `render_brief` writes the LLM's
text with a citation scan but no header. The resulting
`tmp/tt-profile.brief.md` (102 lines) contains the words "Themes",
"Surface concentration", "Cadence" and no mention of coverage, skips,
rate limits or 429 (grep: 0 hits outside quoted PR titles). Its
`change_kind` skew (`docs 76 / feat 35 / fix 23`) is over the 147
survivors, and which rows survived is whatever the rate limiter
admitted — not a sample the reader can reason about.

The ledger is honest and the brief is not; the brief is the artifact a
human reads. This is the `plausible_wrong_answer` shape: every
structural check passes, the text is fluent, and the population claim
is false by 43%.

## Classification

enforcement/latency-critical — deterministic config plumbing
(`graph.yaml` / CLI → `RunnableConfig`) and an LLM-free numeric gate in
a code reducer; no model judgement in either path.

## Constraints

- FR-943 row containment stays: one failed row must still produce a
  `row_failed` marker, never abort the map. The gate belongs at the
  reducer, on the aggregate, not per row.
- Commandment 6: when a filter yields a partial population, raise or
  disclose — never substitute the survivors for the whole. A threshold
  breach must be loud (non-zero exit, no brief written), and a
  below-1.0 coverage that passes must still be stamped on the brief by
  code, not requested from the model.
- The throttle must be the platform's `max_concurrency`, not a
  yamlgraph-side semaphore or sleep (`does_the_platform_already_do_this`;
  Commandment 8, no parallel implementations).
- `graph.yaml` and CLI must both be able to set it, following the
  `recursion_limit` precedent (`GraphConfig` field + `--flag` override);
  default behaviour when unset is unchanged (no throttle), so existing
  graphs and their committed demo logs are unaffected.
- Corpus map-reduce contract (`reference/patterns/corpus-map-reduce.md`)
  and the FR-892 tool-slot contract for the census adapters are
  inherited; the census `graph.yaml` may gain a field, not a new node.
- Any behaviour claimed must be witnessed without a live LLM or a live
  Azure endpoint; the 40-task `Send` probe above is the shape of the
  concurrency witness.
- Zero corp identifiers in anything committed (FR-962 invariant 7):
  deployment names, owner, endpoint host stay out of tests and docs.

## Witnessed incidents

- 2026-09-04 09:16–09:18, this repository, `logs/tt-profile.log`: the
  table above. Exit code 0; `tmp/tt-profile.md` line 8 reads
  `- classification coverage: 56.8%`; `tmp/tt-profile.brief.md` has no
  coverage statement. First raw 429 at 09:16:43 on
  `_map_judge_items_sub` attempt 1/3; 100 rows exhausted attempt 3/3
  and were skipped.
- 2026-09-04, same session: `grep -rn max_concurrency yamlgraph/`
  returns nothing; `reference/graph-yaml.md` mentions "concurrency"
  once, in the FR-069 thread-leakage note. The primitive is unexposed.
- 2026-09-04, same session: LangGraph `max_concurrency` probe — 40
  `Send` tasks, default → 12 peak workers; `max_concurrency=4` → 4 peak,
  40/40 results. The platform primitive works for sync `invoke`.
- 2026-09-02, PR #562: FR-962 merged with `classification coverage` in
  the rollup (item 2 of its ideal result) and a "completeness" gate
  (item 5 wording "enforces completeness + hidden-canary before
  rendering"); completeness was implemented as index presence, which
  `row_failed` satisfies. `gate_checks_shape_not_substance`.
