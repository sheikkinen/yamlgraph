# Feature Request: Vision Boundary — Provider Type Lie Kills the Run

**Priority:** HIGH
**Type:** Bug
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-24), R-1…R-5 folded
**Effort:** 0.25 day
**Requested:** 2026-08-24
**First consumer / first event:** `sheikkinen/deviant-daily`'s publish
pipeline. The first event already happened — run `32688775537`
(2026-08-24 04:07), a **`workflow_dispatch` / `publish-now`** attempt,
drew slot `2026-08-24#1`, failed red at the describe step, and left
**no `skipped` row for that slot**. It will recur on the next malformed
structured output, on either trigger.

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

Run `32688775537`, 2026-08-24 04:07 UTC — a manual `publish-now`
dispatch, not the scheduled cron. It drew `2026-08-24#1` and then died:

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

The day was not lost — a later run published `2026-08-24#0` at the same
ref — but slot `#1` was left `drawn` with no terminal row, which is the
ledger state this FR is really about.

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

### S-1: two-stage capture, then repair, then validate (R-2)

**The original proposal was not mechanically possible.**
`with_structured_output(PostDescription)` validates *inside*
`structured.invoke()`, so by the time `describe_image()` receives
anything the `ValidationError` has already been raised — there is no
point at which the raw payload is in hand to repair. The repair must
move upstream of final validation.

Exact contract:

1. **Capture stage.** Request structured output against a permissive
   capture schema whose three list-typed fields (`paragraphs`, `tags`,
   `mature_classification`) accept `list[str] | str`; all other fields
   keep their strict types. The provider's payload is now in hand,
   unvalidated on exactly the axis that lies.
2. **Repair stage.** Run the narrow repair on those three fields only.
3. **Validation stage.** Validate the repaired payload against the real
   `PostDescription`. Its existing validators — tag normalization, the
   50-char title cap, mature consistency, the `mature_classification`
   enum — are unchanged and still authoritative.

```python
def _repair_list_field(field: str, value):
    """Providers sometimes serialize a list as a JSON string (run 32688775537)."""
    if not isinstance(value, str):
        return value
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as e:
        raise InvalidDescription(field=field, reason=f"schema: {field} is not valid JSON") from e
    if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
        raise InvalidDescription(field=field, reason=f"schema: {field} is not a list of strings")
    logger.info("vision: repaired %s from JSON string", field)
    return parsed
```

Repair only when `json.loads` succeeds **and** yields `list[str]`.
Anything else is not guessed at. Every repair logs the field name so
frequency is observable — if this becomes routine, the prompt or the
provider is the problem and the log is the evidence.

### S-2: a typed invalid-description value, routed through the gate (R-3, R-4)

An ad-hoc `{"__invalid__": True}` dict would be mis-diagnosed by
`PostDescription.model_validate()`. Instead a **narrow exception and a
typed result**:

```python
class InvalidDescription(Exception):
    """Schema-shaped, unrecoverable description. Never a transport error."""
    def __init__(self, field: str, reason: str): ...

class DescribeResult(BaseModel):
    valid: bool
    reason: str | None = None   # "schema: paragraphs is not valid JSON"
    field: str | None = None
    payload: dict | None = None
```

- `describe_step` catches **only** `InvalidDescription` and
  `ValidationError` — never a bare `Exception` — and returns
  `DescribeResult(valid=False, ...)`.
- `evaluate_gate()` checks for the typed value **before** attempting
  `PostDescription.model_validate()`, and returns `publish=False` with
  the supplied `schema:` reason.
- `gate_step` commits its usual `skipped` row for the same
  `(date, slot)`.

One code path classifies unusable descriptions whatever their cause, and
the gate remains the sole decider (FR-826 R-5). Graph edges are
unchanged: `gate → END` on `publish != true` already exists.

Non-goal: making `describe` never fail. Missing API key, provider or
network error, undecodable image bytes, roster failure, ledger commit
failure and publish failure all stay **red**. Only schema-shaped
failures become skips.

## Acceptance Criteria

Superseded by the judgement's revised set (2026-08-24); folded verbatim.

- [ ] AC-01: The FR is revised to state the exact witness: run `32688775537` was `workflow_dispatch` / `publish-now`, failed on `2026-08-24#1` after draw, and left no `skipped` row for that slot.
- [ ] AC-02: A condemning test reproduces the cited provider type lie: a raw describe payload with `paragraphs` as a JSON-encoded string fails before the fix and, after the fix, produces a valid `PostDescription` whose `paragraphs` is `list[str]` with the same element text.
- [ ] AC-03: The same narrow repair is covered for `tags` and `mature_classification`; repaired `mature_classification` still passes through the existing allowed-enum validation.
- [ ] AC-04: The repair helper attempts `json.loads` only for string values in the three authorized list fields, repairs only JSON arrays where every element is `str`, and leaves non-string already-valid list values to final validation unchanged.
- [ ] AC-05: Invalid JSON strings in each authorized field do not escape the describe node; they produce the typed invalid-description value with a `schema:` reason naming the field.
- [ ] AC-06: Valid JSON that is not `list[str]` is not repaired; object JSON, list-of-int JSON, and nested-list JSON each produce the same typed invalid-description path with field-specific reasons.
- [ ] AC-07: A well-formed provider response follows the same final `PostDescription` validation semantics as before; no repair log is emitted and no new mutation occurs beyond existing validators such as title trimming and tag normalization.
- [ ] AC-08: Every successful repair emits exactly one structured log line naming the repaired field; tests assert the field names and assert no log for the no-repair path.
- [ ] AC-09: `evaluate_gate()` recognizes the typed invalid-description value and returns `publish=False` with the supplied `schema:` reason without attempting normal `PostDescription` validation first.
- [ ] AC-10: `gate_step()` commits exactly one additional `skipped` ledger row for the same `(date, slot)` when it receives an invalid-description result; the row reason starts with `schema:` and names the offending field.
- [ ] AC-11: A graph/tool-level test proves a schema-shaped describe failure exits green after the skipped row is committed, following the existing `gate -> END` non-publish edge.
- [ ] AC-12: Missing API key, provider/network error, undecodable image bytes, roster failure, ledger commit failure, and publish failure each remain red; no broad exception handler converts them to skips.
- [ ] AC-13: A source-level test asserts `describe_step` contains no publish/skip decision and no ledger write; only `gate_step` records skipped rows.
- [ ] AC-14: Target-repo tests and formatter/linter commands that already exist for `sheikkinen/deviant-daily` pass; the FR records the actual test count observed, not a stale hard-coded count.
- [ ] AC-15: A live post-fix `workflow_dispatch` run completes green; the FR records the run ID and the resulting ledger transition (`published` or `skipped`). If the live run does not exercise a repair, the unit/graph tests remain the repair proof.

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
