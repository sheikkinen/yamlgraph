# FR-705: Race timeout error must enumerate pending candidates (forensic fidelity)

**Status:** Completed
**Type:** Bug (error-path fidelity)
**Effort:** 0.5 day
**Requested:** 2026-07-10
**Judged:** 2026-07-10 — scope frozen. 5 findings resolved (see Judgement section).
**Completed:** 2026-07-10 — RED 3520ea9c, GREEN follows.
**Spawned by:** ninchat_voice NC-361 (judgement R-1) — production forensics
misled by the race error message

## Implementation (2026-07-10)

- `_race_async` raises `AllCandidatesFailedError(errors + pending-as-timeout)` at the deadline; both synthetic `[({}, exc)]` wraps deleted (race sync path + router FAIL path per F3); dead `except TimeoutError` branch removed; skip branch classifies `TIMEOUT_ERROR` when any wrapped error is a `TimeoutError` (F2).
- 4 new tests tagged REQ-YG-266 (RED 3520ea9c): pending-fleet enumeration (`All 2`, names, no `?/?`), mixed fast-failure + pending with per-candidate exceptions, mixed-skip TIMEOUT_ERROR classification, router no-double-wrap.
- Full race + router-race suites: 59/59 green; the existing REQ-YG-266 skip and `match="timed out"` tests pass **unmodified**, witnessing F2/F4.

## Problem

When a race node times out, the error reports **"All 1 race candidates
failed: - ?/?: race timed out"** regardless of how many candidates were
racing, and with no candidate identities. In the NC-361 production incident
(3 concurrent calls, 2 LLM candidates each, both left `pending`), the
message claimed one anonymous candidate — the investigators had to pull
LangSmith child runs to learn that **two** providers (Google + Azure) were
both pending, which is the decisive fact separating local starvation from
provider failure.

## Root Cause

`race_node.py` timeout path discards candidate context in two hops:

1. `_race_async` (timeout raise inside the wait loop): at this point `tasks`
   still maps every pending task to its candidate dict, and `errors` holds
   the already-failed ones. Both are dropped by the bare
   `raise TimeoutError(f"race timed out …")`.
2. Sync wrapper in `create_race_node.node_fn`:
   `raise AllCandidatesFailedError([({}, exc)]) from exc` — wraps the bare
   TimeoutError as **one synthetic entry with an empty candidate dict**,
   producing `All 1` and `?/?`.
3. **(F3, found at Judgement)** `router_race_node.py` FAIL path carries the
   identical synthetic wrap — left unfixed it would double-wrap the
   now-informative error back into `?/?` for router races.

## Proposed Solution

Raise `AllCandidatesFailedError` **at the point of timeout**, where the
context exists (L126):

```python
if not done:
    timeout_exc = TimeoutError(f"race timed out after {timeout}s")
    raise AllCandidatesFailedError(
        errors + [(c, timeout_exc) for c in tasks.values()]
    )
```

- Already-failed candidates keep their real exceptions; still-pending ones
  are reported as timed out **by name** (`provider/model`).
- The outer `TimeoutError → AllCandidatesFailedError([({}, exc)])` wrap and
  the entire `except TimeoutError` branch in `node_fn` become dead code and
  are **deleted** (Commandment 8). The skip contract's timeout
  classification moves with it (F2): the `AllCandidatesFailedError` skip
  branch tags `error_type=TIMEOUT_ERROR` when any wrapped candidate error
  is a `TimeoutError` — deadline expiry is what ended the race; individual
  entries keep their own exceptions.
- `router_race_node.py` FAIL path re-raises `AllCandidatesFailedError`
  **as-is** (F3); only a genuine bare `TimeoutError` — unreachable from the
  race path after this change — would be wrapped, and that wrap is likewise
  deleted.
- Same exception type reaches callers; the message and `.errors` payload
  gain fidelity; the message retains the `timed out` substring existing
  tests match on (F4).

## Acceptance Criteria

- [ ] RED: two-candidate race where both hang past timeout → current error
      message asserts `All 1` / `?/?` (condemns the information loss)
- [ ] GREEN: message reads `All 2 race candidates failed` and names both
      `provider/model` pairs with `race timed out after Xs`; retains the
      `timed out` substring (F4)
- [ ] Mixed case: one candidate failed fast (real exception), one pending at
      timeout → both appear, each with its own error
- [ ] `on_error: skip` on timeout still returns `{state_key: None,
      errors: [PipelineError(type=TIMEOUT_ERROR)]}` — the existing
      REQ-YG-266 skip test passes **unmodified** (F2)
- [ ] Mixed-case skip: `TIMEOUT_ERROR` classification applies when any
      wrapped error is a TimeoutError (F2)
- [ ] Router race FAIL path surfaces the enumerated candidates, not
      `?/?` — no double-wrap (F3, RED fixture on router_race_node)
- [ ] `except TimeoutError` branch in `node_fn` and router wrap deleted;
      vulture/dead-code clean (Commandment 8)
- [ ] `errors` payload preserves candidate dicts (not `{}`) for programmatic
      consumers
- [ ] New tests tagged `@pytest.mark.req("REQ-YG-266")` (existing race-timeout
      REQ; bug fix, no new REQ) — `req_coverage.py --strict` green (F5)
- [ ] `fix`-type changelog fragment in `changelog/unreleased/` + diary entry

## Judgement (2026-07-10)

Scope frozen. Findings and resolutions:

| # | Finding | Resolution |
|---|---------|------------|
| F1 | Cited function/line drift (`_race_candidates_async` L126) | Corrected to `_race_async` wait-loop raise; prose de-lined |
| F2 | "No behavior change" false: sync skip path classifies TimeoutError as `TIMEOUT_ERROR`; rerouting through the AllCandidatesFailedError branch silently loses it (existing REQ-YG-266 test would break) | Skip branch tags `TIMEOUT_ERROR` when any wrapped error is TimeoutError; existing test must pass unmodified |
| F3 | `partial_remediation`: identical synthetic wrap in router_race_node.py would double-wrap the fixed error back to `?/?` | Router FAIL path re-raises as-is; AC added |
| F4 | Existing test matches `"timed out"` on the raised error | Message retains substring; pinned as criterion |
| F5 | Traceability unpinned | Existing REQ-YG-266; no new REQ; fix-type fragment + diary |

**Out of scope (purge list):** retry semantics, per-candidate timeout budgets, LangSmith payload enrichment, changes to `_race_async` winner/cancel logic.

## Related

- FR-271 (async race), FR-119/CAP-119 (race timeout)
- ninchat_voice NC-361 (the incident this would have clarified in one read)
- Doctrine: Commandment 6 (bear witness of thy errors — an error message that
  miscounts its own evidence is a silent fallback in forensic clothing)
