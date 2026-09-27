# Feature Request: Census re-run classifies only new or updated PRs (map memo with caller-supplied versions)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented (2026-09-27)
**Effort:** 1.5 days
**Requested:** 2026-09-27
**Depends on:** [FR-1119](FR-1119-lint-map-owned-state-fields.md) (lint knows map-owned state fields)
**First consumer / first event:** the second run of
`examples/demos/person_profile_census/graph.yaml` over the same subject
with the same rubric, labels and model. It makes zero `gh_pr_extract`
calls and zero `classify_pr` LLM calls for PRs whose GitHub `updatedAt`
is unchanged, and it writes a ledger JSONL equal to run 1's.
**Research:** in-body Alternatives table (the FR-890 equivalent-record
route); the `updatedAt` evidence section below (judgement R-1); the
FR-1116 alternatives; and the FR-1065 investigation
([docs/investigations/fr1065-resumable-map.md](../docs/investigations/fr1065-resumable-map.md)).
**Prior art:**
- [FR-1116](FR-1116-map-memo-file-corpus.md): the memo this FR extends. It
  named the census as second consumer but excluded non-file items ("Dict
  items and other version modes are out of scope"). This FR is that
  excluded mode, sized to one consumer.
- [FR-1076](FR-1076-shared-map-reuse-helpers.md): superseded. It targeted
  this census with membership/publication machinery. This FR keeps
  FR-1116's split/merge and adds one argument.
- [FR-962](FR-962-person-profile-census-authored-prs.md): the census.
- [FR-966](FR-966-visibility-conjunction-unsatisfiable.md) and FR-984/985: census fixes
  whose behaviour must stay intact.

## Human decisions

- **2026-09-27, operator:** plan the census update and related map
  improvements as FRs; keep changes minimal.
- **2026-09-27, operator (judgement R-2):** *May repeated census runs
  knowingly reuse stale `base_sha`, `additions`, `deletions` and
  `changed_files` for open PRs when the base branch moves without
  advancing `updatedAt`?* Answer: **Yes.** The limitation stays and is
  documented in the README. "Unchanged" means "`updatedAt` unchanged",
  not "extracted bundle unchanged".
- **Carried from FR-1076 / FR-1116:** a stored failure is carried, not
  re-run, while its identity matches. There is no live pilot and budget
  is $0; witnesses are deterministic.

## Summary

Three small pieces:

1. `map_memo_split` takes an optional `versions: {key: str}` argument.
   When it is given, the version of each item is that string, and items
   need not be files.
2. A new census adapter, `gh_authored_prs_versions`, returns
   `{"owner/repo#N": updatedAt}` from the same `gh search prs` query that
   `discover` runs.
3. The census graph wraps both maps, `extract_items` and `judge_items`,
   in split/merge. A local `pair_executed` tool stores bundle and finding
   together per PR. `reduce_pr_ledger` reads the merged records when they
   are present.

## Value Statement

An operator who re-profiles the same person pays GitHub API and Azure LLM
cost only for PRs created or updated since the last run. The ledger stays
identical for the unchanged ones.

## Problem

Each census run spends one `gh api` call and one Azure `classify_pr` call
per authored PR, up to 500
([graph.yaml](../examples/demos/person_profile_census/graph.yaml)). A
person's closed and merged PRs rarely change, yet every re-run pays for
all of them.

FR-1116's memo cannot be used as shipped:
- Items must be readable file paths, and version is the sha256 of the
  bytes. `_hash_files` raises `MapMemoInputError` for a PR ref
  ([map_memo.py](../examples/shared/map_memo.py#L108-L130)).
- The census has two maps. The reducer needs each PR's extracted
  **bundle** as well as its **finding**: `_judged_row` checks
  `evidence_span` against the bundle's title and body, and `_row_failed`
  copies bundle fields
  ([tools.py](../examples/demos/person_profile_census/tools.py#L176-L310)).
  A memo around `judge_items` alone would lack the bundles of reused rows.

GitHub supplies a change marker at discovery time: `updatedAt`. The
evidence and its limits are in the next section.

## `updatedAt` evidence (judgement R-1)

**Field and shape.** `gh search prs --help` lists `updatedAt` among the
`--json` fields. The REST form (`gh api repos/{o}/{r}/pulls/{n}`) returns
it as `updated_at`, an ISO-8601 UTC string, for example PR #719:
`"updated_at": "2026-09-27T11:31:31Z"`.

**Documentation.** GitHub's search documentation defines the `updated:`
qualifier as "when an issue or pull request was last updated"
([docs.github.com: Searching issues and pull requests](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests#search-by-when-an-issue-or-pull-request-was-created-or-last-updated)).
It does not list the events that count as an update.

**Reproducible probe (2026-09-27).** Command:
`gh pr view <n> --json updatedAt,mergedAt,comments,reviews,commits`,
run for PRs 715–719 of this repo.

| PR | last commit | last comment | merged | updatedAt |
|---|---|---|---|---|
| 719 | 11:24:24 | — | 11:31:31 | 11:31:31 |
| 718 | 07:19:49 | — | 07:29:07 | 07:29:08 |
| 717 | 05:20:42 | 05:25:18 | 05:25:38 | 05:25:38 |
| 716 | 18:02:39 | — | 18:05:15 | 18:05:15 |
| 715 | 17:52:34 | — | 17:52:40 | 17:52:41 |

**Witnessed:** merging advances `updatedAt` (5/5). In every sample,
`updatedAt` is at or after the last commit and the last comment.

**Not witnessed:** title or body edits, label changes, comments or
reviews made *after* the merge, and pushes to an open PR. A controlled
probe for these would write to a shared GitHub PR, which this FR does
not do. The FR therefore claims no invalidation for them. The README
states the contract as "a PR is re-classified when its `updatedAt`
changes", with nothing stronger.

**Known non-advancing:** base-branch movement on an open PR can change
`base_sha` and the size fields without changing `updatedAt` (accepted by
the operator, above).

## Ideal Result

Run 2 over an unchanged footprint makes no extract and no classify calls.
One new PR, or one PR whose `updatedAt` changed, costs one extract and
one classify. Changing
the rubric, the label vocabularies, the model, the prompt or the census
code re-runs everything. The ledger JSONL for unchanged PRs is
byte-identical to run 1's. `gh-profiler.yaml` and the corpus/repo
censuses are untouched.

## Proposed Solution

### 1. `map_memo_split(..., versions=None)`, in `examples/shared/map_memo.py`

- `versions is None`: current file mode, unchanged.
- `versions` given: it must be a dict whose key set equals `set(items)`
  exactly, and every value must be a non-empty string. Otherwise split
  raises `MapMemoInputError` before any read. Items are validated as
  non-empty, unique strings and are not read from disk. The supplied
  string is stored as the row `version` verbatim.
- `store` that is not a non-empty string raises `MapMemoInputError`. This
  closes an unvalidated `Path(None)` in both modes.
- `map_memo_merge`, the schema and the manifests' outputs are unchanged.
  The split manifest documents the new argument.

### 2. `gh_authored_prs_versions(state) -> dict[str, str]`, in `examples/demos/corpus_census/adapters/corpus_adapters.py`

- It shares one private search helper with `gh_authored_prs_discover`:
  the same argv, the same `source`/`visibility` parsing (FR-966), the
  same `MAX_PRS` overflow rule and the same duplicate check. The helper
  requests `repository,number,updatedAt`.
- The versions adapter rejects a missing, null or empty `updatedAt`
  rather than storing an unusable version.
- `discover`'s return value and behaviour are unchanged
  (`tests/unit/test_fr966_authored_pr_visibility.py` stays green
  unmodified).
- There is a new manifest, `gh-authored-prs-versions.tool.yaml`.
- The adapter runs a second search, so its population can differ from
  `discover`'s (a PR created in between). Split's exact key-set check then
  raises, and the run fails closed. The operator reruns.

### 3. Census graph, authored through `scripts/author.sh`

```text
preflight → discover (items) → versions (slot, same source/visibility)
  → memo_split   tool_call: items={state.items}, versions={state.versions},
                 store={state.memo_store}, signature_files=[graph.yaml,
                 prompts/classify_pr.yaml, tools.py,
                 ../corpus_census/adapters/corpus_adapters.py],
                 inputs={rubric, problem_labels, surface_labels, azure_model}
  → extract_items   over {state.memo.result.todo}, collect executed_contents
  → judge_items     over {state.executed_contents}, collect executed_findings
                    (failures default: executed_findings_failures)
  → pair            python pair_executed → state_key paired
  → memo_merge      tool_call: plan, results={state.paired}, failures=[],
                    map_name=judge_items,
                    map_dispatch={state._map_verdict.judge_items.dispatch},
                    min_success=0
  → reduce_ledger → prepare_brief_input → synthesize → render_brief   (unchanged)
```

- `memo_store` is a required variable with no default. The store holds
  per-person classifications, so the operator chooses where it lives.
- The model is in the signature on purpose. `azure_model` is a graph
  variable, and `PRLedgerRow.model` is stamped from it, so a reused row
  must have been produced by the same model.
- The census has no `min_success` today (coverage is a ledger statistic).
  `min_success=0` keeps that behaviour.

### 4. `pair_executed(state) -> list[dict]`, in `person_profile_census/tools.py`

An index join, never a positional zip (judgement R-3):

1. It validates the extracted bundle channel (`executed_contents`) as an
   exact cover of integer indices `0..len(todo)-1`, rejecting booleans
   and missing, duplicate or out-of-range indices.
2. It validates successful findings (`executed_findings`) plus
   `executed_findings_failures` as a second exact cover of the same index
   set, including a duplicate that appears across the success and
   failure channels.
3. It parses bundles and joins them to outcomes by `_map_index`, never by
   list position.
4. It emits nothing unless both covers validate completely.

Each record is `{_map_index: i, bundle: <parsed bundle>, finding:
<verdict>}`, or `{_map_index: i, bundle, error: <MapFailure.message>}`
for a judge failure.

- It drops the LLM-echoed `source_index` from the stored verdict. That
  index belongs to this run's `todo` positions and would be wrong on
  reuse.
- A judge failure is therefore stored as an `ok` memo record that carries
  `error`. It is carried like any outcome until the PR's `updatedAt`
  changes, which is the operator's carried-failure decision. The memo's
  own `failed` status stays unused here.

### 5. `reduce_pr_ledger`

At the input boundary only: when `state["merged"]` is present, it builds
`items`, bundles and findings from `merged.result.records`, indexed by
`_map_index`, which is the current population order and equals `items`
order. Otherwise it keeps today's path, which `gh-profiler.yaml` still
uses. Row construction, rollup, canary and rendering are unchanged.

## Acceptance Criteria

Adopted verbatim from the judgement's revised criteria (AC-08 carries R-4).

- [x] AC-01: Split with `versions` over unique non-file string items returns every item in `todo` on an empty store, reads no item path, stores the supplied non-empty string versions after merge, and returns `todo == []` on a second split with identical versions.
- [x] AC-02: Changing one supplied version puts exactly that key in `todo`. Missing or extra keys, non-dict `versions`, non-string or empty version values, duplicate/empty/non-string items, and non-string or empty `store` raise `MapMemoInputError` before a store is created. File mode remains unchanged and all existing `test_fr1116_map_memo.py` tests pass unmodified.
- [x] AC-03: The committed research evidence satisfies R-1, and the FR records the operator's R-2 decision. The README states the resulting freshness contract without claiming stronger invalidation than the evidence supports.
- [x] AC-04: With `_gh` stubbed, `gh_authored_prs_versions` requests `repository,number,updatedAt` and returns `{ref: updatedAt}` for the same fixture population as discover. It rejects missing, null, or empty `updatedAt`, overflow, an empty listing, a duplicate ref, and unsatisfiable visibility; shared failures retain discover's messages. `test_fr966_authored_pr_visibility.py` passes unmodified.
- [x] AC-05: `pair_executed` performs the two exact index-cover validations in R-3, joins by index rather than list order, emits one record per todo index with parsed bundle plus finding or error, strips model-supplied `source_index`, and emits no partial result on malformed attribution.
- [x] AC-06: For identical bundles and findings, `reduce_pr_ledger` given `merged` writes JSONL byte-identical to its existing `contents`/`findings`/`findings_failures` path, including the exact `row_failed` representation. Existing reducer tests pass unmodified, and malformed merged records retain the current batch-fatal missing/duplicate/out-of-range behavior.
- [x] AC-07: A provider-free test runs the migrated graph over five PRs including one judge failure. Run 1 makes five extract and five classify calls. Run 2 with identical versions makes zero of each, writes byte-identical JSONL, and retains the judge failure as `row_failed`. Run 3 with one bumped version makes exactly one extract and one classify call for that PR and produces the same ledger as a clean full recomputation of the run-3 fixture.
- [x] AC-08: Independently changing `rubric`, `problem_labels`, `surface_labels`, or `azure_model` re-runs all five items. The graph passes exactly the four frozen signature files, and changing a signature file invalidates all five items.
- [x] AC-09: Omitting `memo_store` fails before any extract call and creates no memo store.
- [x] AC-10: After FR-1119 is enforced, the graph is migrated through `scripts/author.sh`, lints without declarations for `_map_verdict` or `executed_findings_failures`, and regenerates `demo-output.log` with the exact command recorded in the authoring/implementation record.
- [x] AC-11: The README documents the memo, required `memo_store`, controller warning, reset command, operator-selected open-PR policy, and updated Quickstart/corp invocations with the versions tool and memo store.
- [x] AC-12: A CAP/REQ entry covers the behavior; every new test carries the REQ marker; `python scripts/req_coverage.py --strict` passes; the changelog fragment, FR implementation record, and diary entry are present.

## Accepted limitation

For an **open** PR, GitHub may recompute `base_sha`, `additions`,
`deletions` and `changed_files` when the base branch moves, without
bumping `updatedAt`. A reused open-PR row can then carry stale size
fields. The operator accepted this on 2026-09-27 (Human decisions). It
is recorded in the README. No open-PR special case is added.

## Alternatives Considered

| Option | Disposition |
|---|---|
| Memo around `judge_items` only; version = sha256 of the extracted bundle | Rejected. Every run still pays every `gh api` call, and judge must map over a todo subset of bundles, which needs a selector node plus `source_index` remapping. `updatedAt` is known at discovery, so it skips both maps. |
| Change `discover` to return `{ref: updatedAt}` | Rejected. `discover` is a slot whose list-of-refs contract is consumed by `extract` and by FR-966 tests. A second adapter leaves it untouched, and the key-set check covers the race. |
| Restructure the census into one per-PR subgraph map (extract → judge), as `meta_map` does | Rejected as larger. It re-authors the pipeline and the reducer contract. `pair_executed` gives the same per-PR record with two graph nodes. |
| Memo stores finished `PRLedgerRow`s | Rejected. The rows depend on reduce-time validation. Storing raw bundle plus finding keeps `reduce_pr_ledger` the single authority. |
| Always re-run open PRs (version = run-unique token for `state == open`) | Rejected by the operator (2026-09-27, judgement R-2): the stale-size-field limitation is accepted. |
| Also migrate `gh-profiler.yaml` | Out of scope. It is not part of FR-962's enforced scope, and the reducer's unmemoized path keeps it working. |
| Framework-level map `memo:` key | Still rejected (FR-1116). This FR is the second example consumer that FR-1116 said such a key should wait for. The FR does not propose the key. |

`is_this_a_graph`: the census already is one. Split, merge, versions and
pair are deterministic I/O, so they stay Python tools.

## Not authorized

Any change under `yamlgraph/` (FR-1119 carries the only framework
change). Changes to `map_memo_merge`, the store schema, `gh_pr_extract`,
`gh-profiler.yaml`, `corpus_census`, `repo_census`, or the census prompts.
Pruning, deletion tracking, or a store-read API.

## Related

- [FR-1116](FR-1116-map-memo-file-corpus.md), [FR-1119](FR-1119-lint-map-owned-state-fields.md), [FR-1076](FR-1076-shared-map-reuse-helpers.md) (superseded), [FR-1073](FR-1073-map-result-contract.md), [FR-962](FR-962-person-profile-census-authored-prs.md), [FR-966](FR-966-visibility-conjunction-unsatisfiable.md)
- [examples/demos/person_profile_census](../examples/demos/person_profile_census/README.md), [examples/shared/map_memo.py](../examples/shared/map_memo.py)

## Implementation record (2026-09-27)

- RED `9bb8529f`: four test files (53 tests), CAP-292 / REQ-YG-709.
- GREEN `92ad255a`: `map_memo_split(..., versions=)`, manifest contract;
  `_search_authored_prs` shared by discover and the new
  `gh_authored_prs_versions` (+ `gh-authored-prs-versions.tool.yaml`);
  `memo_prepare`, `pair_executed`, `reduce_pr_ledger` merged branch;
  graph via `scripts/author.sh feature-requests/authoring-briefs/fr-1120-census-memo-brief.md`
  (report: lint 0 errors, graph witness 8 passed; live smoke blocked —
  needs Azure + gh); README memo section.
- `demo-output.log` command (AC-10):
  `{ yamlgraph graph lint <graph>; yamlgraph graph validate <graph>; } 2>&1 | tee <demo>/demo-output.log`
  for `person_profile_census` and `corpus_census`.
- Tests: FR-1120 suite plus `test_fr1116_map_memo.py`,
  `test_fr966_authored_pr_visibility.py`, `test_fr899_repo_census.py`
  unmodified: 145 passed.

### Deviations

1. **Ledger row order.** The live reducer wrote rows in findings-then-
   failures order; the merged path yields index order. Byte identity
   (AC-06) required one order, so `reduce_pr_ledger` now sorts rows by
   `source_index` on both paths. Row content is unchanged.
2. **`memo_prepare` node.** `tool_call` does not resolve templates nested
   inside dict args, so the signature inputs and the versions query are
   built as state (`memo_inputs`, `memo_query`) by a local python node,
   which also fails fast on a missing `memo_store` (AC-09).
3. **`executed_contents: []` seed.** An empty map does not write its
   collect key, so `judge_items` over an absent `executed_contents` would
   raise on a fully reused run. `memo_prepare` seeds the list; the
   framework fix is outside this FR.
4. **`versions` via `tool_call`.** Python nodes merge a returned dict into
   state; `tool_call` keeps the adapter's `{ref: updatedAt}` whole under
   `versions.result`.
5. **Judge failures stored as `error` records** inside `paired`, merged
   with `failures: []` and `min_success: 0`; the reducer's coverage floor
   stays the threshold (carried-failure decision above).
6. **Signature paths are repo-root-relative** (meta_map precedent); runs
   must start at the repo root.
7. **`corpus_census/demo-output.log` regenerated** (lint + validate of its
   unchanged graph) because demo-proof-check requires a log whenever a
   file under the demo directory changes; the graph is untouched.
8. **Graph `description:`** replaced rather than extended by the author
   run; the slot-binding sentence is lost from the description (the
   README still carries it).
9. **"Controller warning" (AC-11)** read as: CLI/env overrides and the
   smoke `sed` rewrite are not in the signature; use one `memo_store` per
   controller configuration.
10. "Existing reducer tests pass unmodified" is vacuous: no reducer test
    existed before this FR.
