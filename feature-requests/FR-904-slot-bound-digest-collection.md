# Feature Request: Slot-bound digest collection

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed — **GATED on FR-900**
**Effort:** 1 day
**Requested:** 2026-08-29
**First consumer / first event:** the `yamlgraph-daily-digest` scheduled
run, at the first cron after merge — invoked as
`yamlgraph graph run graph.yaml --tool collect=sources/hn_rss.tool.yaml`.
Second consumer, in this same FR: the second source manifest, bound to the
same graph with no graph edit.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** child of FR-902, which the Judge returned **SPLIT**
(2026-08-29) with R-2 requiring Phase 2 to re-enter as its own FR. FR-892
supplies the slot semantics, which this FR reuses **exactly** — it defines
no digest-specific slot mechanism. FR-768 supplies the manifest contract
unchanged. FR-900 is a hard gate: `--tool` is absent from every published
yamlgraph. Siblings FR-903 and FR-905 share no surface with this one.

## Summary

Convert the digest's collection stage from an inline hardcoded fetcher
into an FR-892 tool slot, and ship two source manifests that bind it —
proving that a second digest is a binding, not a fork.

## Value Statement

Standing up a digest over a different source becomes a `--tool` binding
and a topics list, while filtering, analysis, ranking, rendering, and
delivery are shared verbatim.

## Problem

`nodes/sources.py` hardcodes the Hacker News endpoint and an `RSS_FEEDS`
module constant. `graph.yaml` declares five inline
`type: python, module: nodes.*` tools, which is why `run_digest.py` must
do `sys.path.insert(0, REPO_DIR)` before importing anything.

The consequence is that a second digest — a different subject area, a
different source — can only be a fork of this repository. Every future
fix to filtering, ranking, or delivery then has to be applied N times, and
the copies drift. This is exactly the drift FR-777 documented when four
shell tools had diverged across three demos.

The operator's stated intent is reusable tools for other digests.
Documentation cannot deliver that: a pattern description does not stop the
next repo from copying `nodes/sources.py`. A slot contract does, because
the pipeline graph physically does not contain a source.

## Ideal Result

One digest pipeline, many digests. The graph declares what a collector
must provide; the caller supplies which collector at invocation. Adding a
source is writing one manifest. `graph.yaml` never changes again for a new
subject area.

## Blocking dependency

**FR-900 must be enforced first.** FR-892 `--tool` merged 2026-08-26
(`06d1dfe4`); the latest PyPI release `v0.5.22` is tagged 2026-08-17, and
`git merge-base --is-ancestor 06d1dfe4 v0.5.22` is false. The workflow
installs yamlgraph from PyPI, so the failure is an argparse error before
the graph loads — not a subtle degradation. Do not start this FR until
`pip install yamlgraph==<FR-900 version>` provides `--tool`.

## Proposed Solution

### The slot contract

```yaml
tools:
  collect:
    slot: true
    contract:
      runtimes: [python]
      args: [config]
```

```bash
yamlgraph graph run graph.yaml --tool collect=sources/hn_rss.tool.yaml
```

Slot semantics are FR-892's, unchanged: binding paths resolve relative to
the caller's CWD, the runtime allowlist is the mechanical check, and every
binding failure is a typed `ToolSlotBindingError` raised before any node
or LLM executes.

### Two bindings, because one binding proves nothing

| Manifest | Source | Note |
|---|---|---|
| `sources/hn_rss.tool.yaml` | Hacker News + RSS | current behaviour preserved; `RSS_FEEDS` moves from a module constant to manifest-supplied config |
| `sources/<second>.tool.yaml` | genuinely different (arXiv, GitHub releases, or a caller-supplied feed list) | the witness that the seam is real |

A slot with a single binding has not been shown to be a slot — it is an
inline tool with extra ceremony.

### Collateral

Manifest-ising the four existing node modules removes the
`sys.path.insert` hack, because manifest paths resolve relative to the
manifest file.

### Graph-authoring route (R-6)

`graph.yaml` is materially changed, so this is graph authoring and must go
through the governed authoring route with an authoring report.

## Acceptance Criteria

- [ ] `pip install yamlgraph==<FR-900 version>` provides `--tool`,
      verified before work starts
- [ ] `collect` is declared as a slot with an explicit `contract`
- [ ] **Two** source manifests bind it, one preserving current behaviour
- [ ] Switching between them requires **zero** edits to `graph.yaml` —
      asserted by running both bindings against an unchanged graph file
      and comparing its hash before and after
- [ ] `RSS_FEEDS` no longer exists as a module constant; feed lists arrive
      as manifest-supplied config
- [ ] A missing binding, an undeclared slot, and a runtime outside the
      allowlist each raise `ToolSlotBindingError` before any node runs
- [ ] `run_digest.py` no longer mutates `sys.path`
- [ ] The workflow pins `yamlgraph>=<FR-900 version>`
- [ ] An authoring report exists for the `graph.yaml` change
- [ ] One real scheduled run succeeds with the slot-bound graph, evidenced
      by run ID and commit SHA

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Keep collection inline; document the reuse pattern | **Rejected.** Documentation does not prevent the next repo from copying `nodes/sources.py`; a slot contract does. FR-777 recorded what drift costs when copies are permitted. |
| A2 | Make sources configurable by `--var feeds=...` instead of a slot | **Rejected.** Handles a different feed *list* but not a different *fetching strategy* — arXiv and GitHub releases are not RSS URLs. A var parameterizes one implementation; a slot replaces it. |
| A3 | Extract collection into a shared package on PyPI | **Rejected as premature.** There is one consumer repo today. The fit boundary (`examples/shared/README.md`) requires two-plus consumers before extraction, and slots deliver the reuse without a distribution decision. |
| A4 | Define a digest-specific slot mechanism | **Rejected on judgement R-2.** FR-892 semantics are reused exactly; a parallel mechanism would fork the contract. |
| A5 | Ship one binding now, a second later | **Rejected.** A single-binding slot is unfalsifiable — it demonstrates nothing that an inline tool does not. The second binding *is* the test. |
| A6 | Wait for a second digest repo to exist before slot-ifying | **Rejected.** The second repo is what this prevents; by then the fork has already happened. |

**`is_this_a_graph`: yes, and it already is one.** The change is to an
existing pipeline's tool declarations and invocation surface. The
authoring route applies.

## Out of Scope

- Delivery ordering and the email node (FR-903)
- Rank→format validation (FR-905)
- The committed-SQLite question and the JSONL ledger
- Packaging `examples/shared/` into the yamlgraph wheel (noted in FR-900)

## Related

- FR-902 — parent; SPLIT verdict 2026-08-29, R-2 and R-6
- FR-900 — hard gate; publishes `--tool`
- FR-892 — the slot semantics reused verbatim
- FR-768 — the manifest contract
- `examples/demos/corpus_census/` — the committed proof that one pipeline
  serves many corpora through slot bindings
- FR-777 — what drift costs when verbatim copies are permitted
