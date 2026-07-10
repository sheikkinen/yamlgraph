# FR-712: Cached google-genai client errors on completed calls in fresh event loops

**Priority:** HIGH
**Type:** Bug (correctness — silent hedge degradation)
**Status:** Proposed
**Effort:** 0.5–1 day
**Requested:** 2026-07-10
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
  would have WON its race can error instead — the FR-705 error naming makes
  it visible in logs, but the hedge silently degrades to single-provider
  ~50% of the time the gemini answer arrives first. Distinct from, and not
  fixed by, any latency verdict from FR-711.

## Direction (to be judged)

Candidates, not yet chosen — the Judge should weigh against FR-711's
eventual verdict since the fixes overlap:

1. **Exclude google-genai from `_llm_cache`** (per-call construction for
   google/vertex only): smallest change; restores correctness; forfeits
   object reuse google never benefits from cross-loop anyway. Cost: per-call
   construction (~ms, cheap per FR-711 cold-construct column).
2. **Loop-affine cache key** (cache keyed additionally by running-loop id):
   correct, bounded growth concerns (one entry per bridge loop — unbounded
   with per-call loops; requires eviction).
3. **Persistent bridge loop (FR-A from FR-711's condemn branch)**: fixes it
   structurally AND serves the latency case — but is gated on FR-711's
   deployed verdict; may be overkill if latency absolves.

Option 1 is the honest immediate fix regardless of FR-711's outcome;
option 3 may supersede it later. RED test: warm google client, N completed
calls through `_run_coro_sync_safe`, zero errors required (currently ~50%).

## Acceptance Criteria (draft, for judgement)

- [ ] RED: warm cached google client, 10 completed calls each in a fresh
      loop via the real bridge → currently errors; condemning test asserts
      zero errors (API-key-guarded, marked slow)
- [ ] GREEN: chosen fix makes it pass; azure/anthropic paths untouched
- [ ] FR-709 witness + FR-708 matrix + FR-710 floors green unmodified
- [ ] Interplay note recorded in FR-711 (whichever fix lands changes the
      Arm-B topology for google — re-run the local instrument after)
- [ ] REQ under CAP-03 or CAP-91 per fix location; changelog fix fragment;
      diary
