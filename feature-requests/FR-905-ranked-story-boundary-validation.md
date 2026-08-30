# Feature Request: Validate ranked stories at the rank→format boundary

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
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

### Surface (R-1)

Implementation is limited to the external **`yamlgraph-daily-digest`**
repository:

| File | Action |
|---|---|
| `nodes/formatting.py` | typed validation, drop/raise boundary, `InvalidRankedStoriesError` |
| `tests/test_fr905_ranked_validation.py` | condemning tests |
| `run_digest.py` | only if needed to surface the failure in run output |

`examples/daily_digest/*` in **this** repository is **cited evidence
only** — the 2026-08-29 crash site. It is not an implementation target.
Fixing the sibling example is a separate judged FR, not this one.

### The status field, and what `invalid` means (R-2)

`format_markdown` emits `digest_status` alongside `digest_markdown`.
FR-903 established `no_articles` and `ready`. This FR adds `invalid`
**as a failure classification, never as a successful graph result** — a
raised node does not also return a state update, so the two cannot be the
same thing.

| Condition | Behaviour |
|---|---|
| No input articles; the ranker was never invoked | return `digest_status == no_articles` |
| At least one ranked story validates **and** rendered markdown is non-empty | return `digest_status == ready` |
| Ranker **was** invoked and: the payload is empty, **or** every item is invalid, **or** no valid survivor remains | **raise** `InvalidRankedStoriesError` |

The exception message carries `digest_status=invalid`, the ranked item
count, and the observed element types. `digest_status == invalid` may
appear only in that failure path; it is never a value a successful run
returns.

The empty-ranked-response case (R-5) is explicit above and is its own
test: an invoked ranker returning zero stories is neither a quiet day nor
a partially bad response, and leaving it unspecified would recreate the
exact empty-bulletin laundering this FR exists to kill.

Emptiness is never the signal.

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
- [ ] **Each dropped item is observable**: a `caplog` test proves the log
      record carries the item index, its observed type, and the validation
      reason — and does **not** dump the full payload (R-4)
- [ ] A non-empty ranked response with zero conforming items raises
      `InvalidRankedStoriesError`, naming the count and observed types
- [ ] An **empty** ranked response from an invoked ranker raises the same
      error — tested separately from the all-strings and mixed cases (R-5)
- [ ] `digest_status == invalid` never appears as a successful graph
      result; it exists only in the failure path
- [ ] `no_articles` and `invalid` are distinguishable in the run output —
      asserted by a test, not by reading logs
- [ ] No path emits an empty bulletin as success
- [ ] No change to `yamlgraph/schema_loader.py` or to any framework
      schema behaviour
- [ ] No change under `examples/daily_digest/` (evidence only, R-1)

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
- **URL reconciliation against the `analyzed` set (R-3).** Parked as a
  follow-up FR, not an optional criterion here. An optional gate is not a
  gate — acceptance criteria must be mechanically checkable. FR-894
  remains the precedent for a later *mandatory* reconciliation FR with
  exact input shapes and tests; this FR's required fix is the drop/raise
  boundary alone.

## Related

- FR-908 — parent; SPLIT verdict 2026-08-29, R-3 and R-5
- FR-894 — corpus-map-reduce reconciliation; the governing pattern
- FR-903 — establishes the `digest_status` field this extends
- `examples/daily_digest/nodes/formatting.py` — the sibling renderer with
  the identical defect, and the site of the 2026-08-29 crash

## Implementation Status — Enforced

**Merged:** `yamlgraph-daily-digest` PR #2, squashed to `63b6aa8`.

| | |
|---|---|
| RED | `d2ec805` — 10 witnesses, `ImportError` on the absent guard |
| GREEN | `f66639c` — 32 passed (10 new, 22 inherited from FR-903) |
| Live | 50 articles → 27 filtered → archived → delivered, exit 0 |

### What was built

`nodes/formatting.py` validates each ranked story against a typed
`RankedStory` (`title`/`url` required, `summary`/`reason`/`relevance`
optional). Non-conforming items are dropped individually and logged with
index, observed type, and a capped reason — observable via `caplog`
without dumping the payload (R-4).

`InvalidRankedStoriesError` is raised when the ranker was invoked and no
item survives, naming the item count and the observed types. Per R-2,
`invalid` is a failure classification only: a raised node returns no state
update, so `invalid` can never also be a successful result. An invoked
ranker returning an empty list raises as its own case (R-5) — previously
indistinguishable from a quiet day, which is exactly how invalid output
laundered into a green no-op.

### Decisions

- `prompts/rank_stories.yaml` is **untouched**, deliberately, and a test
  asserts `list[Any]` remains. The guard is correct regardless of what
  the schema becomes, because a well-typed schema can still be satisfied
  by a well-typed lie. Tightening the schema would have made the fix look
  done while leaving the boundary unguarded.
- URL reconciliation stayed out of scope per R-3.

### Deviations

None. Surface was confined to `yamlgraph-daily-digest` per R-1;
`examples/daily_digest/*` was used as evidence only and remains unchanged
— it still carries the identical defect, which is a candidate for a
follow-up or for retirement in favour of the standalone repo.
