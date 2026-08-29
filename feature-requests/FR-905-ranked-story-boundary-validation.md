# Feature Request: Validate ranked stories at the rank→format boundary

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-29
**First consumer / first event:** the `yamlgraph-daily-digest` scheduled
run, at the first cron after merge — the first run in which a malformed
ranked response is rejected loudly instead of crashing the renderer or
being laundered into a green no-op.
**Research:** in-body `## Alternatives Considered` dispositioned table
(FR-889 style — an equivalent committed record per the TEMPLATE note).
**Prior art:** child of FR-908, which the Judge returned **SPLIT**
(2026-08-29) with R-3 requiring Phase 3 to re-enter as its own FR, and R-5
requiring the no-op/invalid distinction to be explicit. FR-894
(corpus-map-reduce reconciliation reference) is the governing pattern for
reconciling model output against a frozen source, and is applied rather
than extended. Siblings FR-903 and FR-904 share no surface with this one.

## Summary

Validate each ranked story against a typed model at the first
deterministic boundary. Drop non-conforming items; raise when a non-empty
ranked response yields no conforming item. Never emit an empty bulletin as
success.

## Value Statement

A malformed model response becomes a loud, diagnosable failure instead of
either a stack trace in the renderer or a silent green run that delivers
nothing.

## Problem

`prompts/rank_stories.yaml` declares:

```yaml
schema:
  name: RankedStories
  fields:
    stories:
      type: list[Any]
```

`yamlgraph/schema_loader.py` resolves `list[Any]` to `list[Any]`, which
gives the provider **no item structure** — the emitted JSON schema
constrains the array but not its elements. The model may legitimately
return objects or strings. `nodes/formatting.py` then calls
`story.get("title", ...)` on each element.

This is not a latent bug. It is a coin flip, weighted toward working:

- **Eleven consecutive scheduled runs** (2026-08-18 → 2026-08-28) returned
  well-formed dicts and produced good bulletins.
- On **2026-08-29** the same schema, against the same
  `anthropic/claude-haiku-4-5`, returned a list of strings and crashed the
  equivalent renderer in `examples/daily_digest` with
  `jinja2.exceptions.UndefinedError: 'str object' has no attribute
  'relevance'`.

That is the shape of defect that survives review and fails on day 40. The
existing tests in `examples/daily_digest/tests/` all pass because they
feed the formatter well-formed dicts — the seam has no test in either
repository.

There is a second failure mode the current code cannot distinguish, which
the Judge raised as R-5: `format_markdown` returns `digest_markdown: ""`
for "no stories", and `run_digest.py` treats empty markdown as a no-op. So
a response that is entirely malformed and a day with no new articles are
indistinguishable — invalid model output is laundered into a green run.

## Ideal Result

Model output is reconciled at the boundary where it enters the
deterministic world. A partially bad response loses only its bad items; a
wholly bad response stops the run with a message naming what arrived; and
"nothing to report" is a distinct, explicit state that no malformed
response can impersonate.

## Proposed Solution

Normalize at the boundary where the data enters, not downstream where it
manifests.

### Typed validation in `format_markdown`

```python
class RankedStory(BaseModel):
    title: str
    url: str
    summary: str = ""
    reason: str = ""
    relevance: float | None = None
```

Each element of `stories` is validated. Non-conforming elements are
dropped with a logged reason. If the ranked response was **non-empty** but
**no** element conforms, raise — naming the count and the observed element
types.

### The status field (R-5)

`format_markdown` emits `digest_status` alongside `digest_markdown`. FR-903
establishes `no_articles` and `ready`; this FR adds the third value:

| `digest_status` | Meaning |
|---|---|
| `no_articles` | nothing was collected; the ranker was never invoked |
| `ready` | at least one story validated |
| `invalid` | the ranker returned items and none validated → raise |

Emptiness is never the signal. A no-op day and a malformed response are
different states, and only the former is green.

### Optional reconciliation

Per FR-894, each accepted story's `url` may be reconciled against the
`analyzed` set, which additionally catches invented stories. Included as
an acceptance criterion but scoped as optional — the drop/raise boundary
is the required fix.

### Explicitly not a framework change

`yamlgraph/schema_loader.py` has no nested-model support in the `fields:`
shorthand. Whether it gains one is a separate framework question. The
boundary guard is correct **regardless** of what the schema later becomes,
because a well-typed schema can still be satisfied by a well-typed lie.

## Acceptance Criteria

- [ ] **RED first, in its own commit:** `format_markdown` fed
      `["a string", "another"]` fails before the fix exists
- [ ] Non-conforming items are dropped individually; a mixed response
      renders the conforming subset
- [ ] A non-empty ranked response with zero conforming items raises,
      naming the count and the observed element types
- [ ] `digest_status == invalid` is never reported as success
- [ ] `no_articles` and `invalid` are distinguishable in the run output —
      asserted by a test, not by reading logs
- [ ] No path emits an empty bulletin as success
- [ ] Optional: accepted story URLs are reconciled against the `analyzed`
      set, with unreconciled stories dropped and logged
- [ ] No change to `yamlgraph/schema_loader.py` or to any framework
      schema behaviour

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Add nested-model support to `schema_loader.py` so `list[Any]` becomes structured | **Out of scope, worth its own FR.** A framework change judged inside a consumer FR is scope creep, and it does not remove the need for this guard: a schema constrains shape, not truth. |
| A2 | Change the schema to `list[dict]` | **Insufficient alone.** Forces objects but constrains no keys, so `story.get("title")` still yields `"Untitled"` for a well-typed but wrong response. Harmless as a complement; not the fix. |
| A3 | Coerce strings into stories (treat the string as the title) | **Rejected.** A plausible wrong answer is harder to catch than a crash. A bulletin of bare strings would ship and look almost right. |
| A4 | Guard in the template/renderer instead | **Rejected.** That is the downstream-fix trap: the guard belongs where model output enters the deterministic world, not where the symptom surfaces. One boundary, not one per renderer. |
| A5 | Drop everything and emit an empty bulletin when validation fails | **Rejected on judgement R-5.** Exactly the laundering the status field exists to prevent. |
| A6 | Do nothing — 11/11 runs were green | **Rejected.** The twelfth was not. Eleven successes of a coin flip are not evidence of a guarantee. |

**`is_this_a_graph`: no.** This is deterministic validation inside an
existing python node. No LLM orchestration, routing, or prompt artifact is
authored — `prompts/rank_stories.yaml` is deliberately left unchanged
(A1/A2).

## Out of Scope

- Delivery ordering and the email node (FR-903)
- Slot-bound collection (FR-904)
- Framework nested-schema support (A1)
- The committed-SQLite question and the JSONL ledger

## Related

- FR-908 — parent; SPLIT verdict 2026-08-29, R-3 and R-5
- FR-894 — corpus-map-reduce reconciliation; the governing pattern
- FR-903 — establishes the `digest_status` field this extends
- `examples/daily_digest/nodes/formatting.py` — the sibling renderer with
  the identical defect, and the site of the 2026-08-29 crash
