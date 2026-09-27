# Feature Request: Census re-run classifies only new or updated PRs (map memo with caller-supplied versions)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-09-27
**Depends on:** [FR-1119](FR-1119-lint-map-owned-state-fields.md) (lint knows map-owned state fields)
**First consumer / first event:** the second run of
`examples/demos/person_profile_census/graph.yaml` over the same subject
with the same rubric, labels and model. It makes zero `gh_pr_extract`
calls and zero `classify_pr` LLM calls for PRs whose GitHub `updatedAt`
is unchanged, and it writes a ledger JSONL equal to run 1's.
**Research:** in-body Alternatives table (the FR-890 equivalent-record
route), plus the FR-1116 alternatives and the FR-1065 investigation
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

GitHub supplies a change marker at discovery time. `gh search prs --json`
offers `updatedAt` (verified 2026-09-27 against `gh search prs --json`,
which lists `updatedAt` among its fields). GitHub bumps it on title and
body edits, label changes, pushes, state changes, comments and reviews.

## Ideal Result

Run 2 over an unchanged footprint makes no extract and no classify calls.
One new PR or one edited PR costs one extract and one classify. Changing
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

- For each executed index `i` in `0..len(todo)-1`, it emits
  `{_map_index: i, bundle: <parsed contents[i]>, finding: <verdict>}`, or
  `{_map_index: i, bundle, error: <MapFailure.message>}` for a judge
  failure.
- It drops the LLM-echoed `source_index` from the stored verdict. That
  index belongs to this run's `todo` positions and would be wrong on
  reuse.
- It raises on a missing, duplicate or out-of-range index.
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

- [ ] AC-01: Split with `versions` over non-file string items returns every item in `todo` on an empty store, stores the supplied strings as versions after merge, and on a second split with identical versions returns `todo == []`. It reads no item from disk.
- [ ] AC-02: A changed version for one key puts exactly that key in `todo`. Missing or extra keys, a non-dict `versions`, or a non-string or empty value raise `MapMemoInputError` and create no store. A non-string or empty `store` raises `MapMemoInputError` in both modes. All existing `test_fr1116_map_memo.py` tests pass unmodified.
- [ ] AC-03: `gh_authored_prs_versions` (with `_gh` stubbed) returns `{ref: updatedAt}` for the same population `discover` returns from the same listing. It raises on overflow, an empty listing, a duplicate ref, or unsatisfiable visibility, with the same messages as discover. `test_fr966_authored_pr_visibility.py` passes unmodified.
- [ ] AC-04: `pair_executed` emits one record per executed index with bundle plus finding or error, strips `source_index`, and raises on a missing, duplicate or out-of-range index.
- [ ] AC-05: For the same bundles and findings, `reduce_pr_ledger` given `merged` writes a ledger JSONL byte-identical to the one it writes given `contents`/`findings`/`findings_failures`. The existing census reducer tests pass unmodified.
- [ ] AC-06: A provider-free test runs the migrated graph three times with stubbed `versions`/`extract` adapters and a stubbed LLM, each with a call counter, over a 5-PR fixture that includes one judge failure. Run 1: 5 extracts and 5 classify calls. Run 2 (same versions): 0 and 0, with a byte-identical ledger JSONL and the judge failure still a `row_failed` row. Run 3 (one `updatedAt` bumped): exactly 1 and 1, for that PR. Changing `azure_model` re-runs all 5.
- [ ] AC-07: Omitting `memo_store` fails before any extract call.
- [ ] AC-08: The graph is migrated through `scripts/author.sh`. It lints with no `state:` declarations for `_map_verdict` or `executed_findings_failures` (FR-1119), and its `demo-output.log` is regenerated by the same command as before.
- [ ] AC-09: The README documents the memo, the `memo_store` variable, that the store contains per-person classifications under the same controller warning, `rm <store>` to reset, and the accepted limitation below. The corp-run and Quickstart commands gain `--tool versions=…` and `--var memo_store=…`.
- [ ] AC-10: A CAP/REQ entry covers the new behaviour and every new test carries it. `python scripts/req_coverage.py --strict` passes. The changelog fragment, FR implementation record and diary entry are present.

## Accepted limitation

For an **open** PR, GitHub may recompute `base_sha`, `additions`,
`deletions` and `changed_files` when the base branch moves, without
bumping `updatedAt`. A reused open-PR row can then carry stale size
fields. Closed and merged PRs are frozen. This is recorded in the README.
No open-PR special case is added. The alternative (always re-run open
PRs) is listed below for the judge.

## Alternatives Considered

| Option | Disposition |
|---|---|
| Memo around `judge_items` only; version = sha256 of the extracted bundle | Rejected. Every run still pays every `gh api` call, and judge must map over a todo subset of bundles, which needs a selector node plus `source_index` remapping. `updatedAt` is known at discovery, so it skips both maps. |
| Change `discover` to return `{ref: updatedAt}` | Rejected. `discover` is a slot whose list-of-refs contract is consumed by `extract` and by FR-966 tests. A second adapter leaves it untouched, and the key-set check covers the race. |
| Restructure the census into one per-PR subgraph map (extract → judge), as `meta_map` does | Rejected as larger. It re-authors the pipeline and the reducer contract. `pair_executed` gives the same per-PR record with two graph nodes. |
| Memo stores finished `PRLedgerRow`s | Rejected. The rows depend on reduce-time validation. Storing raw bundle plus finding keeps `reduce_pr_ledger` the single authority. |
| Always re-run open PRs (version = run-unique token for `state == open`) | Not adopted. It adds a policy branch for a size-field drift on a minority of rows. The judge may require it. |
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
