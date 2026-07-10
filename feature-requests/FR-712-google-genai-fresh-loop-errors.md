# FR-712: Cached google-genai client errors on completed calls in fresh event loops

**Priority:** HIGH
**Type:** Bug (correctness — silent hedge degradation)
**Status:** Judged
**Effort:** 0.5 day
**Requested:** 2026-07-10
**Judged:** 2026-07-10 — scope frozen. 7 findings resolved; fix pinned to option 1 (see Judgement section).
**Spawned by:** FR-711 local instrument, Finding A (10/20 Arm-B errors)
**Related:** FR-709 (whose cancellation masked this), FR-707 (bridge), `_llm_cache` (llm_factory)

## Problem (field evidence, verbatim from the FR-711 artifact)

With a warm `_llm_cache` entry, `ChatGoogleGenerativeAI.ainvoke` **errors on
~50% of completed calls** when each call runs in a fresh event loop — the
production topology of every race turn (`_run_coro_sync_safe`):

```
RuntimeError: Executor shutdown has been called
RuntimeError: Timeout context manager should be used inside a task
```

(10 of 20 calls, `docs/analysis/fr711-conn-witness-2026-07-10.txt`; aiohttp
internals in google-genai bind to the first loop that runs them.)

- azure and anthropic clients tolerate fresh loops cleanly (0 errors) —
  google-genai is the outlier.
- **Why every prior witness missed it:** FR-709's google candidate was
  always the cancelled loser — it never COMPLETED cross-loop; cancellation
  masked the completion-path defect. The FR-711 judgement's F2
  ("field-verified tolerant by FR-709") was wrong for exactly this reason —
  `assert_path_not_destination` at the fixture level: the path exercised
  was cancel, never complete.
- **Production implication (ninchat_voice fleet):** a gemini candidate that
  would have WON its race can error instead — **predicted from the witness,
  not yet observed in production logs** (F5: 2026-07-10 grep of ninchat
  logs found zero occurrences; FR-705's naming means real occurrences
  would appear as `Race candidate google/… failed:` lines — consumer
  should grep after next deploy). Distinct from, and not fixed by, any
  latency verdict from FR-711.

## Solution (frozen — F1)

**Uncache google/vertex**: `_UNCACHED_PROVIDERS = frozenset({"google",
"vertex"})` in `llm_factory` — these providers construct fresh per call so
the aiohttp session is born in (and dies with) the loop that uses it. The
working shape is proven by the witness itself: Arm A (client used in its
birth topology) was clean; Arm B (cross-loop reuse) errored.

- Vertex inclusion is **same-class-inferred** (identical wrapper class and
  session internals — stronger than FR-710's backend inference) —
  annotated in code (F4).
- Cost accepted (F6): per-call construction is ms-scale; the
  `_VERTEX_CONSTRUCT_LOCK` + env masking re-entry per call is negligible
  at fleet sizes.
- Option 2 (loop-keyed cache) REJECTED: one entry per bridge loop with a
  fresh loop per call = unbounded growth, the week's own disease.
- Option 3 (persistent bridge loop, FR-711's FR-A) stays gated on the
  deployed verdict and may supersede this fix later — interplay recorded,
  not a reason to ship broken hedges meanwhile.

## Acceptance Criteria

- [ ] RED (integration, API-key-guarded, slow): warm google client, 10
      completed calls each in a fresh loop via the real bridge → currently
      errors ~50%; condemning test asserts ZERO errors (false-pass odds
      ≈ 0.1% at observed rate, F2)
- [ ] Unit gate (LLM-free, F3): `create_llm("google")` twice → distinct
      objects; `create_llm("anthropic")` twice → same object; cache-clear
      fixture isolates the process-global cache
- [ ] Vertex annotated as same-class-inferred in code (F4)
- [ ] FR-709 witness + FR-708 matrix + FR-710 floors + FR-711 script green
      unmodified
- [ ] FR-711 interplay note: re-run the local instrument post-fix (google
      Arm B should now be clean AND carry the honest Δ for the latency
      question)
- [ ] New REQ under CAP-03, id verified free against origin at enforce
      (F7); `req_coverage --strict` green; fix-type changelog fragment
      (may carry the new req — single claimant); diary entry

## Judgement (2026-07-10)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | Three fix options open | Pinned: uncache google/vertex; loop-keyed cache rejected (unbounded per-loop growth); persistent loop stays FR-711-gated |
| F2 | GREEN proof strength | Zero errors over N≥10 completed calls (≈0.1% false-pass at observed 50%) |
| F3 | No mechanical unit gate | Cache-identity test: distinct per call for google/vertex, cached for others |
| F4 | Vertex not directly witnessed | Same-class-inferred (identical wrapper + session internals); in-code annotation |
| F5 | "Silently degrading ~50%" stated as fact | Softened to predicted; production grep found zero occurrences; consumer greps post-deploy |
| F6 | Per-call construction cost | Accepted: ms-scale; lock re-entry negligible |
| F7 | Traceability | New REQ under CAP-03 at enforce |

**Out of scope (purge list):** persistent bridge loop (FR-711 verdict
territory), cache eviction policies, other providers' cache behavior,
aiohttp session lifecycle patches upstream.
