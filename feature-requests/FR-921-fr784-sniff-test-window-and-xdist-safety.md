# Feature Request: FR-921 Network-Sniff Tests — Full-Window Exhaustion and xdist Unsafety

**Priority:** MEDIUM (downgraded from HIGH 2026-08-30 — see "Where the cost actually lands")
**Type:** Bug
**Status:** Enforced 2026-08-30 (judged APPROVED WITH REVISIONS; R-1…R-4 folded; [judgement](FR-921-fr784-sniff-test-window-and-xdist-safety.judgement.md))
**Effort:** 0.5 days
**Requested:** 2026-08-30
**First consumer / first event:** any developer running the full local suite (`pytest tests/`) or the FR-784 module directly on a checkout where `examples/api-discovery/tools/node_modules` is installed — first event is the next such run, which pays ~82s for six `slow`-marked tests and cannot be trusted under `-n auto`.
**Research:** in-body measurement record and dispositioned alternatives table (full-suite clock run, main @ ca44832b, 2026-08-30), extended 2026-08-30 with root-cause evidence and an installation-scope correction
**Prior art:** FR-784 created the sniffer and these tests; FR-275/CAP-126 (test speed optimization) owns the `-m "not slow"` fast-loop convention — verified 2026-08-30 that this defect does **not** pollute that loop (all six tests are already slow-marked). No prior FR addresses sniffer settle latency or xdist safety.

## Summary

Five tests in `tests/unit/test_fr784_network_sniff.py` each take a uniform ~15.4s sequentially and all six sniff tests FAIL under `pytest -n auto`. The uniform duration equals the sniffer's default `--timeout 15000` window: the script exhausts its full window on every run instead of settling early. Fix the early-exit behavior at the boundary that causes it and make the tests parallel-safe.

## Value Statement

Returns ~80s to every full local suite run on a Playwright-installed checkout, removes the six failures that block full-suite `-n auto` (FR-923's prerequisite), and repairs a real FR-784 product defect: the sniffer takes `timeout` seconds even against pages that settle in milliseconds, so every downstream consumer pays the ceiling as a floor.

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

### Where the cost actually lands (correction, 2026-08-30)

The original filing claimed this defect taxes the documented fast loop. **It
does not.** All six browser witnesses already carry `@pytest.mark.slow`
(`tests/unit/test_fr784_network_sniff.py:260,279,292,312,322,331`), verified by
collection:

```
$ pytest tests/unit/test_fr784_network_sniff.py -m "not slow" --collect-only -q --no-cov
9/15 tests collected (6 deselected) in 0.15s
```

Further, the tests self-skip without Playwright:

```
$ pytest tests/unit/test_fr784_network_sniff.py -q --no-cov -rs -m "slow"
SKIPPED [6] playwright not installed: cd examples/api-discovery/tools && npm ci
6 skipped, 9 deselected in 0.13s      # in a fresh worktree
```

`.github/workflows/workflow.yml` contains no `npm ci` step, so **CI skips all
six**. The 82s is paid only on a checkout where `examples/api-discovery/tools/node_modules`
exists — today, the operator's main checkout. This narrows the blast radius and
is why Priority drops HIGH → MEDIUM. It does **not** dissolve the defect: the
underlying sniffer bug is a product defect (see below), and the six xdist
failures still block FR-923's full-suite `-n auto` goal on that checkout.

### Root cause (identified 2026-08-30)

`examples/api-discovery/tools/network-sniff.js:164-167` bounds the body reads
with a `Promise.race` against a bare `setTimeout`:

```js
await Promise.race([
  Promise.allSettled(pending),
  new Promise((resolve) => setTimeout(resolve, remaining())),
]);
```

When `allSettled` wins the race, the `setTimeout` timer is **never cleared and
never unref'd**. `main()` writes its JSON to stdout and returns, but the script
calls no `process.exit()` (`network-sniff.js:181-186`) — so Node keeps the event
loop alive until the orphaned timer fires at the deadline. The observed
`timeout + ~0.4s` uniform duration is the process waiting on a timer whose
result was already discarded. The page settles in milliseconds; only the exit
is late.

This makes the xdist hypothesis in defect 2 above suspect: under `-n auto` the
same orphaned timer plus CPU contention is the likely shared cause. Verify
after the early-exit fix rather than assuming (symptom_patch).

### Measurement environment

| Item | Value |
|---|---|
| Repo state | main @ `ca44832b` (timings); re-verified @ `6feac43c` (collection/skip evidence) |
| Python | 3.14.6 (`.venv`) |
| Node | v23.11.0 |
| Playwright | `examples/api-discovery/tools/node_modules` present on main checkout; absent in fresh worktrees and CI |
| Timing command | `pytest tests/ -q` (sequential, coverage on per `addopts`), durations from `--durations` in `logs/clock-full.log` |
| Parallel command | `pytest tests/ -q -n auto`, `logs/clock-full-xdist.log` |

**is_this_a_graph:** No. This is a deterministic Node/pytest bug fix with no
LLM stage, no fan-out, and no multi-stage pipeline — a graph would add a runtime
to a two-line timer defect.

## Ideal Result

The sniffer exits as soon as the page has settled and its captured bodies are
read, treating `--timeout` strictly as a ceiling. A trivial local fixture page
sniffs in well under a second with the default 15s ceiling; the FR-784 module
runs green under `-n auto`; and no test needs a marker, an isolation group, or a
shrunken window to hide latency that should not exist. The minimal path back is
one boundary fix in `network-sniff.js` — clear the timer that outlives its race
— condemned first by a latency witness.

## Proposed Solution

1. RED: condemn with a failing test asserting the sniff of a trivially-settling
   fixture page completes well under the window (e.g. < 5s) while still
   returning valid FR-784 JSON.
2. Fix the early-exit boundary in `examples/api-discovery/tools/network-sniff.js`:
   clear (or `unref`) the race timer so the process exits when work completes,
   keeping `--timeout` as a ceiling, not a floor. Changes to `_sniff` in the
   test module are limited to test instrumentation unless the RED test proves
   the Python helper is itself at fault.
3. Re-run `pytest tests/unit/test_fr784_network_sniff.py -n auto` ×3 on a
   Playwright-installed checkout; if failures persist, isolate with
   `@pytest.mark.xdist_group("fr784")` and record the post-fix failure evidence
   that made isolation necessary.

## Acceptance Criteria

- [x] AC-01: Failing test (RED commit) condemning full-window exhaustion on a settling page
- [x] AC-02: `pytest tests/unit/test_fr784_network_sniff.py -q --no-cov` completes in < 15s total on a Playwright-installed checkout (was ~82s)
- [x] AC-03: `pytest tests/unit/test_fr784_network_sniff.py -q --no-cov -n auto` passes with zero fr784 failures across 3 consecutive runs
- [x] AC-04: The timeout witness stays honest — the hanging fixture path still exits 0, emits valid JSON, and includes a timeout warning at `timeout_ms=4000`
- [x] AC-05: No FR-784 semantic regression — capture, telemetry demotion, redaction, auth-wall, CAPTCHA, and manifest tests pass or skip only for the existing named browser-setup reason
- [x] AC-06: Before/after wall times and the three `-n auto` runs recorded in this FR
- [x] AC-07: Changelog fragment in `changelog/unreleased/`

## Enforcement Status

**Enforced 2026-08-30** on `feat/fr921-test-latency-cluster`.

The fix is one boundary repair in `examples/api-discovery/tools/network-sniff.js`:
the `Promise.race` body-read timer is now captured and `clearTimeout`-ed after
the race resolves. Nothing about settle detection was wrong — `waitUntil:
"networkidle"` already returned in milliseconds. The process simply could not
exit, because the losing branch of the race left a live timer on the event loop
and `main()` ends without `process.exit()`.

| Measurement | Before | After |
|---|---|---|
| `pytest tests/unit/test_fr784_network_sniff.py -m slow -q --no-cov` | 82.20s (6 tests) | 13.26s (7 tests, incl. new witness) |
| Per settling-page sniff | 15.38–15.43s | 1.22–1.28s |
| `test_timeout_exits_cleanly_with_warning` (4s window, hanging fixture) | 4.43s | 4.41s — correctly unchanged; that page never settles |
| `-n auto`, 3 consecutive runs | 6 failures each | 16 passed / 14.22s, 12.29s, 12.70s |

`xdist_group("fr784")` was **not** needed: C-3's precondition (a repeated
`-n auto` failure surviving the early-exit fix) never materialised. The parallel
failures shared the orphaned-timer root cause — the FR's own hypothesis, held
loosely per symptom_patch, and now verified rather than assumed.

Evidence logs: `logs/fr784-baseline.log`, `logs/fr921-red.log`,
`logs/fr921-green.log`, `logs/fr921-xdist-{1,2,3}.log`.

### Consequence for FR-923

FR-923's baseline claims "~60s owed to FR-921" inside the 2:17 fast loop. That
is false on two counts — the witnesses are `slow`-marked (deselected from the
fast loop) and skip entirely in CI, which has no `npm ci` step. FR-923 must
re-baseline before its fast-loop acceptance criterion can be judged.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Mark the five tests `slow` and exclude from fast loop | Moot — they are already `slow`-marked; verified 2026-08-30. Never was an available lever |
| Do nothing (CI skips them anyway) | Rejected — the defect is in the shipped FR-784 sniffer, not only its tests; every consumer pays the ceiling as a floor |
| Shrink window to 2s without fixing settle detection | Rejected — symptom_patch; under xdist contention a small fixed window flakes worse |
| `xdist_group` isolation only | Insufficient alone — serializing 5×15s tests still costs 77s; acceptable as an additional measure if contention persists after the early-exit fix |
| Delete the tests | Rejected — REQ coverage for FR-784 sniffer semantics (redaction, captcha, auth-wall) would be lost |

## Related

- `tests/unit/test_fr784_network_sniff.py`
- `tests/fixtures/fr784_spa/spa_server.py`
- FR-784 (network sniff feature)
- FR-923 (suite latency umbrella — depends on this FR for the `-n auto` goal)
