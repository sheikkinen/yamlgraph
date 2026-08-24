# Feature Request: Vision Boundary — Provider Type Lie Kills the Run

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.25 day
**Requested:** 2026-08-24
**First consumer / first event:** `sheikkinen/deviant-daily`'s daily
publish. The first event already happened — run `32688775537`
(2026-08-24 04:07) died at the describe step and published nothing.
It will recur on the next malformed structured output.

**Prior art:** **FR-826** froze the describe→gate contract this FR
repairs; the gate's role as sole decider is preserved, not changed.
**FR-863** is the same class one boundary over — DeviantArt's title cap
mirrored inward — and its diagnosis (`an external system's constraint
was known at its boundary but never mirrored into our model`) is the
same. **CAP-117** (race node parse-JSON content normalization) is the
existing cure for this exact shape in yamlgraph core and is the
precedent to follow. FR-862/872 are non-overlapping (dispatch surface,
ramp tooling). No REJECTED prior art occupies this territory.

## Summary

The vision model returned `paragraphs` as a JSON-encoded **string**
instead of a list. Two defects follow: the payload is not normalized at
the boundary, and the resulting failure is a **red run** instead of a
recorded `skipped` row — bypassing the gate that exists precisely to
classify bad descriptions.

## Value Statement

A model that mis-shapes one field costs a re-run at worst, not the day's
publication and an unexplained red pipeline.

## Problem

Run `32688775537`, 2026-08-24 04:07 UTC:

```
tool_call node 'describe': tool 'describe_step' failed:
1 validation error for PostDescription
paragraphs
  Input should be a valid list [type=list_type,
   input_value='["A figure stands alone ...nt. Be Art. Be Unique."', input_type=str]
```

The content was **correct**. The container was wrong: a JSON array
serialized to a string. `with_structured_output(PostDescription)` is a
request, not a guarantee — the provider's type lie
(Scripture: `schema` / `provider` boundary, FR-059).

### D-1: no normalization at the vision boundary

`describe_image()` passes the provider's object straight into Pydantic.
Nothing attempts the one obvious repair — `json.loads` on a string that
should be a list — even though yamlgraph's race node already does
exactly this for the same shape (CAP-117).

### D-2: the failure is red, not skip — and this is the worse defect

`tools/gate.py` exists to turn an unusable description into a committed
`skipped` ledger row with a reason. It never sees this one:
`describe_step` raises inside `structured.invoke`, the graph node has
`on_error: fail`, and the run dies. So:

- the ledger records nothing for the day
- the run is red, indistinguishable from a real outage
- a **shape** problem escapes the gate while a **content** problem
  (`confidence: low`) is handled gracefully

The gate is the sole publish decider by FR-826 R-5. A malformed shape
currently routes around it.

## Ideal Result

A mis-shaped but recoverable field is repaired at the boundary, logged
as repaired, and the day publishes normally. A genuinely unusable
response becomes a committed `skipped` row with a reason naming the
field — the same treatment a low-confidence description gets. The
pipeline goes red only when something is actually broken.

## Proposed Solution

### S-1: normalize at the vision boundary (D-1)

In `tools/vision.py`, before validation, attempt a **narrow, explicit**
repair on list-typed fields (`paragraphs`, `tags`,
`mature_classification`):

```python
def _repair_list_field(value):
    """Providers sometimes serialize a list as a JSON string (run 32688775537)."""
    if not isinstance(value, str):
        return value
    parsed = json.loads(value)          # raises -> no repair, caller records skip
    if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
        raise ValueError("not a list of strings")
    return parsed
```

Repair only when `json.loads` succeeds **and** yields `list[str]`.
Anything else is not guessed at. Every repair is logged with the field
name so the frequency is observable rather than silent — if this becomes
routine, the prompt or the provider is the problem and the log is the
evidence.

### S-2: route shape failures through the gate (D-2)

`describe_step` catches `ValidationError` and returns a structured
failure the gate understands, rather than raising:

```python
{"__invalid__": True, "reason": "schema: paragraphs must be a list"}
```

`gate_step` already returns `publish=False` with a `schema:` reason on
validation failure and commits a `skipped` row. Extend it to recognise
the marker, so **one code path** classifies unusable descriptions
whatever their cause. The graph edges are unchanged: `gate → END` on
`publish != true` already exists.

Non-goal: making `describe` never fail. A missing API key, a timeout, or
an unparseable image must still go red. Only *schema-shaped* failures
become skips.

## Acceptance Criteria

- [ ] AC-01: a condemning test reproduces run `32688775537` — a provider
      response with `paragraphs` as a JSON-encoded string — and fails
      before the fix (RED committed separately).
- [ ] AC-02: after the fix, that response yields a valid
      `PostDescription` with `paragraphs` as a `list[str]` whose
      elements match the original content exactly.
- [ ] AC-03: repair applies to `paragraphs`, `tags` and
      `mature_classification`; a test covers each.
- [ ] AC-04: a string that is not valid JSON is **not** repaired and
      produces a gate `skipped`, not an exception escaping the step.
- [ ] AC-05: valid JSON that is not `list[str]` (object, list of ints,
      nested list) is **not** repaired; same skip path; a test per case.
- [ ] AC-06: every repair emits one log line naming the field; a test
      asserts the log.
- [ ] AC-07: a well-formed response is byte-identical after the repair
      path — no repair, no log line (regression pin).
- [ ] AC-08: an unusable description commits exactly one `skipped`
      ledger row with a `schema:` reason naming the offending field.
- [ ] AC-09: the run exits **green** on a schema skip and **red** on a
      genuine error (missing key, network failure, undecodable image);
      a test per branch.
- [ ] AC-10: the gate remains the sole publish decider — a source scan
      asserts `describe_step` contains no publish/skip decision beyond
      producing the marker.
- [ ] AC-11: 128 existing tests stay green; `ruff` clean.
- [ ] AC-12: witnessed live — a real publish run completes green after
      the fix, run id and ledger row recorded.

## Risks

**Repair masks a degrading model.** If the provider starts mis-shaping
routinely, silent repair hides it. Mitigated by AC-06's per-repair log
line: the frequency becomes measurable, and a rise is the signal to fix
the prompt or the provider rather than widen the repair.

**Skip-instead-of-fail hides real outages.** Mitigated by AC-09: only
`ValidationError` becomes a skip. Every other exception still goes red.

**The repair grows.** Today it is `json.loads` → `list[str]`. A fourth
special case is the signal to stop patching and change the request
(`regex_fourth_exclusion`, generalized). Recorded here so the next
author sees the threshold.

**Skips are now cheaper than failures**, so a systematic problem could
accumulate as quiet skipped days. The ledger reason field makes this
countable; if skips cluster on one cause, that is its own FR.

## Alternatives Considered

- **Loosen the schema to accept `str | list[str]`.** Rejected: it moves
  the lie into our own model and every downstream consumer inherits it.
  Normalize at the boundary, not in the type.
- **Retry the LLM call on validation failure.** Rejected as the primary:
  it spends another generation on a deterministic, repairable defect.
  Reasonable as a later addition *after* repair fails.
- **Let it stay red and re-run manually.** Rejected: it costs a
  publication day and makes shape errors indistinguishable from
  outages — which is exactly what happened on 2026-08-24.
- **Fix the prompt to insist on a JSON array.** Not sufficient alone:
  the prompt already names the fields, and instruction text does not
  bind provider serialization (`two_strike_split` — mechanize at the
  boundary rather than reword).

## Related

- `sheikkinen/deviant-daily` run `32688775537` — the witness
- `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md` — same defect class, different boundary
- `feature-requests/FR-826-deviantart-daily-repo.md` — R-5 gate contract, preserved here
- CAP-117 race node JSON content normalization — the existing cure for this shape
- `docs/diary/diary-2026-08-24-twenty-gates-and-a-human-found-the-fire.md`
