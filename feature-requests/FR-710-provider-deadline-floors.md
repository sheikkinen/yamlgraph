# FR-710: Provider deadline floors validated at the client boundary

**Priority:** HIGH (release-targeted: v0.5.10)
**Type:** Bug (boundary normalization of a provider constraint)
**Status:** Completed
**Effort:** 0.25 day
**Requested:** 2026-07-10
**Judged:** 2026-07-10 — scope frozen. 4 findings resolved (see Judgement section).
**Completed:** 2026-07-10 — RED fb06f57e (6 condemned), GREEN follows; ships in v0.5.10.
**Spawned by:** FR-709 field finding 1 — a real google request rejected the judged 5 s fixture
**Parent:** FR-708 (client request timeout — the knob this FR gives a floor)

## Implementation (2026-07-10)

- `_PROVIDER_TIMEOUT_FLOORS` map (google field-cited verbatim; vertex backend-inferred per F2 annotation) + provider-aware `_bounded(kwargs, timeout_param, provider)` with source resolved before `setdefault` (F1); `timeout=None`/non-numeric raises for floored providers (F3). google + vertex constructors pass their provider name; all others unchanged.
- 10 tests (6 RED → GREEN + 4 guards) under REQ-YG-539; FR-708 matrix and factory suites green unmodified; FR-709 witness unaffected (runs at the floor, 10 s).

## Summary

Google's API enforces a minimum client deadline and rejects anything below it at request time. FR-708's `LLM_REQUEST_TIMEOUT` knob has no floor awareness, so a consumer setting `LLM_REQUEST_TIMEOUT=5` (or passing `timeout=5` in code) breaks the google/vertex providers with a confusing runtime 400 on every request. Normalize the provider's constraint at **our** boundary (`the_one_law`): validate the effective timeout against a per-provider floor map at construction and raise with a floor-naming message.

## Field evidence (verbatim, FR-709 run 2, 2026-07-10)

```
google.genai.errors.APIError: 400 INVALID_ARGUMENT
'Manually set deadline 5s is too short. Minimum allowed deadline is 10s.'
```

- Surfaced by the first live-transport run of the judged `LLM_REQUEST_TIMEOUT=5` fixture — a provider-side contract that exists in no SDK docstring, discovered only by a real request (diary: "the field corrected the judge within the hour").
- Consumer impact is real and current: any FR-708 deployment tuning the knob below 10 s silently converts its google/vertex candidates into guaranteed-failing candidates — in a race, that permanently drops the gemini hedge with only per-request 400 noise as the clue.

## Proposed Solution

1. Floor map in `llm_providers.py`:
   `_PROVIDER_TIMEOUT_FLOORS = {"google": 10.0, "vertex": 10.0}` — google
   entry cites the verbatim FR-709 400; **vertex entry is annotated as
   backend-inferred** (same google-genai client enforces the deadline;
   not independently field-verified — a visible, documented exception to
   the pattern-freeze rule, one line to fix if contradicted) (F2).
2. `_bounded(kwargs, timeout_param=..., provider=None)` (F1): the SOURCE of
   the effective value is determined **before** `setdefault` (caller kwarg
   present → `timeout= kwarg`; else `LLM_REQUEST_TIMEOUT` set → env; else
   default). Below-floor — or non-numeric/None for a floored provider
   (F3: `timeout=None` would TypeError the comparison and silently defeat
   the FR-708 bound) — raises
   `ValueError("google requires a request timeout >= 10s (provider-enforced
   deadline floor); got 5.0 via LLM_REQUEST_TIMEOUT")` — floor, value, and
   source named. Construction-time, loud, once — not a 400 per request.
3. Default (30 s) unaffected; providers without a floor entry unchanged
   (the general `timeout=None` hole for non-floored providers belongs to
   FR-708's contract, out of scope here); the map is append-only, each
   entry citing its evidence or carrying the inferred annotation.

## Acceptance Criteria

- [ ] RED first: google + vertex constructors with `LLM_REQUEST_TIMEOUT=5`
      currently construct silently (and would 400 at request time) —
      condemning tests assert construction raises with floor + source named
- [ ] Caller-kwarg path validated too: `timeout=5` in code raises naming the
      kwarg as source; `timeout=10` constructs; `timeout=None` for a floored
      provider raises (F3)
- [ ] Non-floored providers (anthropic et al.) still accept sub-10 values
- [ ] Floor map: google entry cites the verbatim FR-709 400; vertex entry
      carries the backend-inferred annotation (F2)
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-539")` (same client-boundary
      contract as FR-708; no new REQ); `req_coverage --strict` green
- [ ] Changelog fragment (no `req:` front-matter — REQ-YG-539 is already
      claimed by the FR-708 fragment; cross-wiring precedent FR-707)
- [ ] FR-709 witness and FR-708 matrix suites green unmodified
- [ ] **Ships in v0.5.10** with FR-708/709 — the knob and its floor arrive
      together; no released version exposes the un-floored knob

## Judgement (2026-07-10)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | `_bounded()` knows neither provider nor value-source; the promised error message was unimplementable as written | `provider=` param + floor map lookup; source resolved BEFORE setdefault (kwarg → env → default) |
| F2 | Vertex floor is inferred, not field-verified — violates the pattern-freeze rule this FR itself invokes | Included with explicit backend-inferred annotation; visible exception, one-line fix if contradicted |
| F3 | Explicit `timeout=None` TypeErrors the floor comparison (and silently defeats the FR-708 bound) | Non-numeric/None for floored providers raises the same shaped error; the general hole stays with FR-708's contract |
| F4 | Release binding | Confirmed; enforce immediately, ships v0.5.10 |

**Out of scope (purge list):** floors for other providers (append when field-observed), retry-budget interplay (`max_retries × timeout`), the `timeout=None` hole for non-floored providers, clamping semantics of any kind.

## Alternatives Considered

1. **Document the floor in CLAUDE.md/env table only** — advisory docs for a
   breaking value (`detection_without_enforcement`). Rejected.
2. **Clamp to the floor silently** — a silent fallback wearing a safety
   costume; the consumer asked for 5 s and gets 10 s without knowing
   (Commandment 6). Rejected.
3. **Let the 400 educate** — per-request noise, and in a race the failing
   candidate is systematically dropped, which looks like a provider outage
   rather than a config error. Rejected.

## Related

- FR-709 (field finding + verbatim evidence), FR-708 (the knob), FR-227
  (same constructor boundary lineage)
- Diary 2026-07-10 "the field corrected the judge within the hour" (this FR
  is its seed executed)
- Doctrine: `the_one_law`, Commandment 6 (no silent clamping), pattern-freeze
  requires field fixtures
