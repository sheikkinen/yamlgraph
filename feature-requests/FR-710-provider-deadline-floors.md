# FR-710: Provider deadline floors validated at the client boundary

**Priority:** HIGH (release-targeted: v0.5.10)
**Type:** Bug (boundary normalization of a provider constraint)
**Status:** Proposed
**Effort:** 0.25 day
**Requested:** 2026-07-10
**Spawned by:** FR-709 field finding 1 — a real google request rejected the judged 5 s fixture
**Parent:** FR-708 (client request timeout — the knob this FR gives a floor)

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

1. Floor map in `llm_providers.py`, field-derived and cited:
   `_PROVIDER_TIMEOUT_FLOORS = {"google": 10.0, "vertex": 10.0}` (same
   google-genai backend enforces the deadline; both constructors affected).
2. Validation of the **effective** timeout (env, default, or caller kwarg —
   whatever `_bounded()` resolves) against the provider's floor at
   construction: below-floor raises
   `ValueError("google requires a request timeout >= 10s (provider-enforced
   deadline floor); got 5.0 via LLM_REQUEST_TIMEOUT")` — naming the floor,
   the value, and its source. Construction-time, loud, once — not a 400 per
   request.
3. Default (30 s) unaffected; providers without a known floor unchanged;
   the map is append-only as new floors are field-discovered (each entry
   must cite its field evidence — pattern-freeze rule).

## Acceptance Criteria

- [ ] RED first: google + vertex constructors with `LLM_REQUEST_TIMEOUT=5`
      currently construct silently (and would 400 at request time) —
      condemning tests assert construction raises with floor + source named
- [ ] Caller-kwarg path validated too: `timeout=5` in code raises the same
      way for google/vertex; `timeout=10` constructs
- [ ] Non-floored providers (anthropic et al.) still accept sub-10 values
- [ ] Floor map entries carry the verbatim field-evidence citation in a
      comment (FR-709 run log)
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-539")` (same client-boundary
      contract as FR-708; no new REQ); `req_coverage --strict` green
- [ ] Changelog fragment (no `req:` front-matter — REQ-YG-539 is already
      claimed by the FR-708 fragment; cross-wiring precedent FR-707)
- [ ] FR-709 witness and FR-708 matrix suites green unmodified
- [ ] **Ships in v0.5.10** with FR-708/709 — the knob and its floor arrive
      together; no released version exposes the un-floored knob

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
