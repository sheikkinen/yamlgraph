# Feature Request: FR-784 Network-Sniff Tests — Full-Window Exhaustion and xdist Unsafety

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** any developer running the documented fast loop (`pytest tests/unit/ -q --no-cov -m "not slow" -n auto`) — first event is the next fast-loop invocation, which currently pays ~77s for five tests and cannot be trusted under `-n auto`.
**Research:** in-body measurement record and dispositioned alternatives table (full-suite clock run, main @ ca44832b, 2026-08-30)
**Prior art:** FR-784 created the sniffer and these tests; FR-275/CAP-126 (test speed optimization) owns the fast-loop convention this defect pollutes. No prior FR addresses sniffer settle latency or xdist safety.

## Summary

Five tests in `tests/unit/test_fr784_network_sniff.py` each take a uniform ~15.4s sequentially and all six sniff tests FAIL under `pytest -n auto`. The uniform duration equals the sniffer's default `--timeout 15000` window: the script exhausts its full window on every run instead of settling early. Fix the early-exit behavior (or right-size the window) and make the tests parallel-safe.

## Value Statement

Restores a trustworthy sub-2-minute unit fast loop and unlocks `-n auto` for the whole suite (measured 13:46 → 7:19 full-suite potential).

## Problem

Measured on main @ ca44832b (2026-08-30):

| Test | Sequential | Under `-n auto` |
|---|---|---|
| `test_captures_data_request` | 15.51s | FAILED |
| `test_token_redaction` | 15.48s | FAILED |
| `test_telemetry_classified_behind_data` | 15.41s | FAILED |
| `test_captcha_flagged` | 15.40s | FAILED |
| `test_auth_wall_flagged_not_failed` | 15.40s | FAILED |
| `test_timeout_exits_cleanly_with_warning` | 4.49s (4s window) | FAILED |

Two distinct defects:

1. **Full-window exhaustion**: durations are uniformly `timeout + ~0.4s`. The
   sniffer never settles early even on trivial local fixture pages served by
   the in-process `ThreadingHTTPServer` (ephemeral port, so port collision is
   NOT the cause). Either the settle detection in `network-sniff.js` never
   fires, or the script waits the full window by design — in which case the
   design taxes every unit run 77s for pages that settle in milliseconds.
2. **xdist unsafety**: all six tests fail under `-n auto` with assertion
   errors (not port errors). Hypothesis to verify first: parallel node/
   playwright processes starve the fixed window under CPU contention, so
   requests that would land inside 15s land outside it. A window-exhaustion
   fix likely cures this too — verify, don't assume (symptom_patch trap).

These are the only tests separating the suite from clean `-n auto` runs:
sequential full suite has 2 unrelated failures; parallel has the same 2 plus
these 6.

## Proposed Solution

1. RED: condemn with a failing test asserting the sniff of a trivially-settling
   fixture page completes well under the window (e.g. < 5s).
2. Fix settle/early-exit in `scripts/**/network-sniff.js` (or its invocation in
   `_sniff`) at the boundary — the script should exit when the page reaches
   network-idle, keeping the window as a ceiling, not a floor.
3. Re-run `pytest tests/unit/test_fr784_network_sniff.py -n auto` ×3; if
   failures persist, isolate with `@pytest.mark.xdist_group("fr784")` and
   record why in the FR.

## Acceptance Criteria

- [ ] Failing test (RED commit) condemning full-window exhaustion on a settling page
- [ ] `pytest tests/unit/test_fr784_network_sniff.py -q --no-cov` completes in < 15s total (was ~82s)
- [ ] `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` passes with zero fr784 failures across 3 consecutive runs
- [ ] Fast-loop wall time reduced by ≥ 60s versus the 2026-08-30 baseline (2:17)
- [ ] Changelog fragment in `changelog/unreleased/`

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Mark the five tests `slow` and exclude from fast loop | Rejected — hides the defect (name_the_seam); the tests guard real FR-784 behavior and belong in the default loop once cheap |
| Shrink window to 2s without fixing settle detection | Rejected — symptom_patch; under xdist contention a small fixed window flakes worse |
| `xdist_group` isolation only | Insufficient alone — serializing 5×15s tests still costs 77s; acceptable as an additional measure if contention persists after the settle fix |
| Delete the tests | Rejected — REQ coverage for FR-784 sniffer semantics (redaction, captcha, auth-wall) would be lost |

## Related

- `tests/unit/test_fr784_network_sniff.py`
- `tests/fixtures/fr784_spa/spa_server.py`
- FR-784 (network sniff feature)
- FR-923 (suite latency umbrella — depends on this FR for the `-n auto` goal)
