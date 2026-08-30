# Feature Request: Slot-bound digest collection

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged
**Effort:** 1 day
**Requested:** 2026-08-29
**First consumer / first event:** the `yamlgraph-daily-digest` scheduled
run, at the first cron after merge — invoked as
`yamlgraph graph run graph.yaml --tool collect=sources/hn_rss.tool.yaml`.
Second consumer, in this same FR: the second source manifest, bound to the
same graph with no graph edit.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** child of FR-908, which the Judge returned **SPLIT**
(2026-08-29) with R-2 requiring Phase 2 to re-enter as its own FR. FR-892
supplies the slot semantics, which this FR reuses **exactly** — it defines
no digest-specific slot mechanism. FR-768 supplies the manifest contract
unchanged. FR-906 is a hard gate: `--tool` is absent from every published
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

## Blocking dependency — satisfied (R-1)

FR-906 is **enforced**: `yamlgraph 0.5.23` published 2026-08-29, verified
from a clean venv outside any checkout —
`yamlgraph graph run --help` lists `--tool TOOL_BINDINGS`. Today's
production digest run already installs it.

The workflow pin is `yamlgraph>=0.5.23`. Before FR-906 this was a hard
block, not a degradation: `--tool` did not exist in any published wheel,
so the failure was an argparse error before the graph loaded.

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

### Collector ABI, frozen (R-2)

A binding that satisfies the slot mechanically but changes the output
shape breaks filtering, content extraction, and ranking downstream. The
contract is therefore both directions:

**In** — the `collect` node supplies `config` from graph variables; a
collector takes no other required argument.

**Out** — `raw_articles` is a list of records, each carrying **at least**:

| Key | Type | Meaning |
|---|---|---|
| `title` | `str` | article title |
| `url` | `str` | canonical link; the dedupe key |
| `source` | `str` | short origin label (`"HN"`, `"RSS"`, `"arXiv"`) |
| `timestamp` | `str` | ISO-8601; `filter_recent` parses this for the 24h cutoff |

This is the shape `nodes/sources.py` already emits. Extra keys are
permitted; a missing key is a binding defect and must fail the acceptance
test, not degrade silently.

### Two bindings, because one binding proves nothing (R-4)

| Manifest | Implementation | Source |
|---|---|---|
| `sources/hn_rss.tool.yaml` | `sources/hn_rss.py` | Hacker News top stories + the current RSS feed list — behaviour preserved exactly |
| `sources/arxiv.tool.yaml` | `sources/arxiv.py` | arXiv `cs.AI` recent submissions via its Atom feed |

**arXiv is the frozen second source**, not a menu. It is genuinely
different from HN/RSS tech news (academic preprints, different cadence,
different relevance profile), and it needs **no new dependency** — the
Atom feed parses with `feedparser`, already installed for RSS.

Smoke, run from the repository root:

```bash
yamlgraph graph run graph.yaml --tool collect=sources/arxiv.tool.yaml \
  --var topics="AI,Python"
```

A slot with a single binding has not been shown to be a slot — it is an
inline tool with extra ceremony.

### Feed lists are Python, not manifest config (R-3)

The FR previously said `RSS_FEEDS` would move "from a module constant to
manifest-supplied config". **That is impossible under the current schema**
and the claim is withdrawn: `ToolManifest` permits only `name`,
`description`, and `runtime`, every model sets `extra="forbid"`, and a
python runtime permits only `type`, `function`, and exactly one of `path`
or `module` (`yamlgraph/tools/manifest.py`). A `.tool.yaml` cannot carry a
feed list.

Instead each source keeps its own constants in its own implementation
file — `sources/hn_rss.py` owns the HN endpoint and `RSS_FEEDS`,
`sources/arxiv.py` owns its query. Swapping sources swaps files, which is
the point. **No change to `yamlgraph/tools/manifest.py`.** Manifest-level
config, if ever wanted, is a separate framework FR.

### Collateral (R-5)

`run_digest.py`'s `sys.path.insert` is **out of scope**. Removing it would
require converting every remaining `module: nodes.*` tool — filtering,
content, formatting — not just collection, which is a second concern in a
FR the Judge split precisely to keep one. The hack stays; a later FR may
finish the conversion.

### Graph-authoring route (R-6)

`graph.yaml` is materially changed, so this is graph authoring and must go
through the governed authoring route with an authoring report.

## Acceptance Criteria

- [ ] `pip install "yamlgraph==0.5.23"` provides `--tool`, verified in a
      clean venv before work starts
- [ ] `collect` is declared as a slot with an explicit `contract`
- [ ] **Two** manifests bind it: `sources/hn_rss.tool.yaml` (behaviour
      preserved) and `sources/arxiv.tool.yaml`
- [ ] Switching between them requires **zero** edits to `graph.yaml` —
      asserted by running both bindings against an unchanged graph file
      and comparing its hash before and after
- [ ] **Both** collectors return `raw_articles` records carrying `title`,
      `url`, `source`, and `timestamp`; a record missing any key fails the
      test rather than degrading downstream
- [ ] `RSS_FEEDS` no longer exists in `nodes/sources.py`; it lives in
      `sources/hn_rss.py`, the implementation its manifest points at.
      **No change to `yamlgraph/tools/manifest.py`** — the manifest schema
      forbids extra keys and cannot carry config
- [ ] A missing binding, an undeclared slot, and a runtime outside the
      allowlist each raise `ToolSlotBindingError` before any node runs
- [ ] The workflow pins `yamlgraph>=0.5.23`
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
- Packaging `examples/shared/` into the yamlgraph wheel (noted in FR-906)

## Related

- FR-908 — parent; SPLIT verdict 2026-08-29, R-2 and R-6
- FR-906 — hard gate; publishes `--tool`
- FR-892 — the slot semantics reused verbatim
- FR-768 — the manifest contract
- `examples/demos/corpus_census/` — the committed proof that one pipeline
  serves many corpora through slot bindings
- FR-777 — what drift costs when verbatim copies are permitted
