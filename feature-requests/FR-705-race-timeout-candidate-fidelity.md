# FR-705: Race timeout error must enumerate pending candidates (forensic fidelity)

**Status:** Proposed
**Type:** Bug (error-path fidelity)
**Effort:** 0.5 day
**Requested:** 2026-07-10
**Spawned by:** ninchat_voice NC-361 (judgement R-1) — production forensics
misled by the race error message

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

1. `_race_candidates_async` L126: `raise TimeoutError(f"race timed out …")`
   — at this point `tasks` still maps every pending task to its candidate
   dict, and `errors` holds the already-failed ones. Both are dropped.
2. Sync wrapper L284: `raise AllCandidatesFailedError([({}, exc)]) from exc`
   — wraps the bare TimeoutError as **one synthetic entry with an empty
   candidate dict**, producing `All 1` and `?/?`.

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
- The outer L284 `TimeoutError → AllCandidatesFailedError([({}, exc)])` wrap
  becomes unreachable for the race path and is removed; `on_error: skip`
  handling moves to the `AllCandidatesFailedError` branch (already present).
- No behavior change: same exception type reaches callers; only the message
  and `.errors` payload gain fidelity.

## Acceptance Criteria

- [ ] RED: two-candidate race where both hang past timeout → current error
      message asserts `All 1` / `?/?` (condemns the information loss)
- [ ] GREEN: message reads `All 2 race candidates failed` and names both
      `provider/model` pairs with `race timed out after Xs`
- [ ] Mixed case: one candidate failed fast (real exception), one pending at
      timeout → both appear, each with its own error
- [ ] `on_error: skip` still returns `{state_key: None, errors: [...]}` on
      timeout (existing contract, existing tests green)
- [ ] `errors` payload preserves candidate dicts (not `{}`) for programmatic
      consumers

## Related

- FR-271 (async race), FR-119/CAP-119 (race timeout)
- ninchat_voice NC-361 (the incident this would have clarified in one read)
- Doctrine: Commandment 6 (bear witness of thy errors — an error message that
  miscounts its own evidence is a silent fallback in forensic clothing)
