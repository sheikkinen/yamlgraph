# Feature Request: Fit the local test worker count to the reference machine — measure first

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented (operator decision N = 4; not judged — see § Implementation Status)
**Requested:** 2026-09-28
**First consumer / first event:** the operator, at the first local commit
after Phase 2 merges. The `pytest` pre-commit hook runs with the chosen worker
count, and the fans should not spin up for the whole hook run.
**Research:** in-body measurement protocol (§ Phase 1) and dispositioned
alternatives table (§ Alternatives Considered). No `scripts/research.sh` run.
The deciding evidence is the Phase 1 measurement on this machine. An
alternatives survey cannot supply it.
**Prior art:**
- FR-1131 `FR-1131-test-suite-cost-concentration.md`
  (Proposed, branch `docs/fr1131-test-suite-cost`, not on main): covers the
  suite's cost, not the machine it runs on. Its Phase B item 4 clocks
  `--dist worksteal` at the unchanged `-n auto`. This FR changes only the
  worker count and leaves CI, labels, and test code to FR-1131. If both
  merge, FR-1131's Phase B clock runs at the worker count chosen here.
- [FR-293](FR-293-pytest-xdist-parallel-tests.md): introduced `-n auto`
  locally. It assumed `auto` means "fit the machine". § Problem item 2
  shows that on this machine it does not.
- [FR-073](FR-073-fast-unit-tests.md): chose to fix leaks before scaling out.
  This FR shares that stance: tune the count to measured resources, not to
  the core count.
- [FR-923](FR-923-test-suite-latency-lanes-coverage-core-slow-marks.md)
  (Proposed, superseded by FR-1131): measured suite latency and never
  measured memory or swap.
- [FR-275](FR-275-test-speed-optimization.md): the `slow` tier. Unchanged here.
- FR-945/FR-948 `lan-delegate`, FR-949 `issue-delegate`: route workloads off
  this machine when they would saturate it. That suits the full suite and
  benchmarks, but not the per-commit hook, which must run locally (§
  Alternatives A-5).

## Summary

On this iMac, `-n auto` starts 12 pytest workers on 6 physical cores and
8 GB of RAM, while swap already holds 4.6 GB. The operator reports that the
fans run at full speed during every test run, and the pre-commit hook runs
that suite on every commit. Phase 1 measures wall time, CPU, peak memory, and
swap growth at several worker counts, alone and with two runs at once.
Phase 2 applies the count that Phase 1 selects, using a decision rule frozen
in this FR before any number exists.

## Value Statement

The operator's machine stops swapping and running its fans at full speed on
every commit. The fast loop gets no slower (or faster), and the number in
the docs is measured on the machine it describes.

## Problem

Facts on the reference machine, 2026-09-28, main @ 6e11be5f:

1. **Hardware.** Intel i5-10500, `hw.physicalcpu` 6, `hw.logicalcpu` 12,
   `hw.memsize` 8 GB.
2. **`-n auto` gives the logical-core count because `psutil` is absent.**
   pytest-xdist 3.8.0 `auto_detect_cpus` (`xdist/plugin.py`) reads
   `PYTEST_XDIST_AUTO_NUM_WORKERS` first. If that is unset, it uses
   `psutil.cpu_count(logical=False)`, i.e. physical cores. Without `psutil` it
   falls back to `os.cpu_count()`, i.e. logical cores. `import psutil` in
   `.venv` raises `ModuleNotFoundError`. So `auto` is 12 here, where xdist's
   own intent would be 6. The same fallback applies on every machine that
   lacks `psutil`, including CI.
3. **Memory is already under pressure at idle.** `vm.swapusage`: 4649.75M of
   6144M used. `memory_pressure`: 46% free. Idle `vm.loadavg`: 4.99 / 5.33 /
   6.48, from other sessions and apps. No pytest was running.
4. **The hook multiplies it.** `.pre-commit-config.yaml:295` runs
   `pytest tests/unit/ -q --tb=short --no-cov -m "not slow" -n auto` on every
   commit that touches `.py`, `.yaml`, `.yml`, or `pyproject.toml`. When
   parallel agent sessions in separate worktrees commit around the same
   time, two or more 12-worker suites overlap.
5. **Contention distorts measurements.** In the FR-1134 before/after
   benchmark, summed junit time fell by 240.1 s. Only 109.3 s of that was
   removed tests. The rest was per-test slowdown under load, and it shifted
   between runs. Every timing FR on this machine (FR-1131, FR-1134) inherits
   that noise until the worker count stops oversubscribing the machine.
6. **Not yet known:** per-worker peak RSS, whether 12 workers swap, and
   whether fewer workers are slower in wall time. Phase 1 exists to answer
   these three.

Not measurable without `sudo`: fan RPM (`powermetrics` / SMC). CPU
utilisation, i.e. (user+sys) / (wall × 12), is the proxy. The operator's fan
observation per configuration is recorded as a human note.

## Ideal Result

The local test loop uses the machine to the point where adding a worker no
longer shortens wall time, and no further. It never pushes the machine into
swap, even when two sessions commit at once. The worker count is chosen by a
measured rule, not by what `os.cpu_count()` happens to return.

## Planned Operations

```yaml
probes:
  - "pgrep -f pytest before each run — non-empty means wait for quiet, never run concurrent with a foreign suite"
  - "sysctl -n vm.loadavg and vm.swapusage before and after each run — swap growth decides the memory branch"
  - "vm_stat Pageouts delta per run — non-zero pageouts under a config disqualifies it"
  - "ps -axo rss,command sampled during each run, summed over pytest processes — aggregate and max-single-worker peak RSS"
  - "/usr/bin/time -p around each run — wall and user+sys"
  - "pass/fail counts per run — a count that differs across worker counts is an xdist ordering defect, recorded and handed to its own FR"
  - "read the raw sampler output of the first run end-to-end before tabulating any aggregate"
branches:
  - "every config with no swap growth → pick by § Decision rule"
  - "no config avoids swap growth → worker count is memory-bound; record per-worker peak RSS; smallest count meeting the wall rule, plus the heaviest-module list for FR-1131 Phase C"
  - "failure counts differ by worker count → stop Phase 2, file the ordering defect, operator decides"
  - "chosen count equals xdist's physical-core intent → Phase 2 mechanism D-1 (psutil); otherwise D-2 (env var)"
  - "chosen mechanism adds a dependency → FR-761 constraints and pip-audit gates apply in the same PR"
delegations:
  - "judge.sh: 1 run on this plan, 1 run if Phase 2 mechanism changes after Phase 1"
  - "bench runs: fast-loop matrix of 5 worker counts × 2 reps, 2 concurrent-pair runs, 2 full-suite runs — 14 runs, sequential, in a detached bench worktree at a fixed SHA"
waits:
  - "judge"
  - "quiet machine before each bench run"
  - "full bench matrix"
  - "operator fan note per config"
commands:
  - git worktree add --detach tmp/bench-fr1143 <sha>
  - "/usr/bin/time -p .venv/bin/python -m pytest tests/unit/ -q --tb=short --no-cov -m \"not slow\" -n <N>"
  - sysctl -n vm.swapusage
  - vm_stat
  - memory_pressure
  - scripts/judge.sh
```

## Proposed Solution

### Phase 1 — measure (no committed config change)

Bench tree: a detached worktree at one fixed SHA, so every run tests the
same code. Before each run, no foreign pytest process may be running, and the
load average is recorded.

| Run set | Command | Configs | Reps |
|---|---|---|---|
| M-1 fast loop | hook command with `-n <N>` | N ∈ {3, 4, 6, 8, 12} | 2, order interleaved (12,4,8,3,6 then reversed) |
| M-2 concurrent pair | two M-1 commands started together | N = 12, and N = M-1 winner | 1 each |
| M-3 full suite | `pytest tests/unit/ -q --no-cov -n <N>` (all tiers) | N = 12, and N = M-1 winner | 1 each |

Per run, record: wall time, user+sys time, CPU utilisation proxy, pass/fail
counts, aggregate peak RSS of all pytest processes, peak single-worker RSS,
swap used before/after, `vm_stat` pageouts delta, lowest `memory_pressure`
free %, and the load average before the run. Raw logs go to
`logs/bench-fr1143-*.log` (local, uncommitted, same convention as FR-1131).
The results table and the sampler's command lines are committed in this FR
under § Implementation Status. No new script is committed: the protocol is
the commands above. Promote a script only if a second FR re-runs this
protocol.

### Decision rule (frozen before measurement)

1. Disqualify any N whose M-1 runs show swap growth or non-zero pageouts,
   net of the idle baseline.
2. Among the rest, take the lowest median wall time, W*.
3. Choose the **smallest** N whose median wall ≤ 1.10 × W*. Fewer workers
   means less heat and memory for the same practical wait.
4. If M-2 at the chosen N shows swap growth, step down to the next smaller N
   that passes rule 3 on the M-2 numbers.
5. If rule 1 disqualifies every N, apply rules 2–3 to all N, and record that
   the machine is memory-bound.

### Phase 2 — apply the chosen N

The mechanism is picked by a branch, so it is not an open design choice:

- **D-1 (chosen N = 6, xdist's physical-core intent):** add `psutil` to the
  `dev` extras so that `-n auto` means physical cores on every machine.
  Committed config keeps `-n auto`. This goes through FR-761 dependency
  governance in the same PR.
- **D-2 (any other N):** the hook entry keeps `-n auto`. The count is set per
  device through `PYTEST_XDIST_AUTO_NUM_WORKERS`, which xdist reads first,
  exported in the operator's shell profile. The hook's `bash -c` inherits it
  from the committing shell. `CLAUDE.md` documents the export with the
  measured N, date, and machine. No per-device number is committed to
  shared config. Probe first: a commit from a VS Code agent terminal must
  show the exported value reaching the hook. If it does not, stop and
  return to the judge.

Both: the `CLAUDE.md` testing section states the measured fast-loop wall
time with its date and machine. FR-1131 AC-03 owns the hook *name*, and this
FR does not rename it.

Re-measure once after Phase 2 (M-1 at the chosen N, 2 reps) as the witness
that the change delivered the measured number.

## Acceptance Criteria

- [ ] AC-01: § Implementation Status holds the M-1/M-2/M-3 table with every
  per-run field from § Phase 1, the bench SHA, and the idle baseline.
- [ ] AC-02: the raw sampler output of at least one run is quoted, with one
  concrete observation that the aggregate table does not show
  (`read_raw_output_first`).
- [ ] AC-03: the chosen N follows from the § Decision rule applied to the
  AC-01 table, with each rule's outcome written out.
- [ ] AC-04: pass/fail counts are identical across all M-1 runs, or the
  difference is recorded and Phase 2 is stopped by branch.
- [ ] AC-05: Phase 2 mechanism D-1 or D-2 is applied as the branch dictates.
  After the change, on this machine, `-n auto` resolves to the chosen N
  (witness: worker count printed by `pytest -n auto` in the hook run).
- [ ] AC-06: the post-change M-1 re-measure shows no swap growth and a median
  wall ≤ 1.10 × W*.
- [ ] AC-07: `CLAUDE.md` states the measured fast-loop time with its date and
  machine. `grep -n "~20s on 12 cores" CLAUDE.md` returns nothing.
- [ ] AC-08: if D-1, `psutil` passes the FR-761 constraints and `pip-audit`
  gates in the same PR.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A-1 | Hardcode `-n 6` (or any N) in the hook entry | Rejected: fits this machine and is wrong on any other, e.g. the LAN Windows host or a CI runner. |
| A-2 | Install `psutil` without measuring | Rejected as a first step: it assumes 6 is right. It becomes D-1 if Phase 1 picks 6. |
| A-3 | `nice`/`taskpolicy -b` the hook | Rejected: lowers priority but not heat or memory. Swap is the problem, not scheduling. |
| A-4 | Serialize concurrent hooks with a lock | Out of scope: M-2 measures whether it is needed. If M-2 at the chosen N still swaps, the operator decides whether to file it. |
| A-5 | Delegate the hook suite to the LAN host | Rejected: the hook must gate the local index before commit. Delegation fits full-suite and bench runs, not the per-commit gate. |
| A-6 | Cut test memory per worker | Owned by FR-1131 Phase C. This FR passes on the heaviest-module list if the machine is memory-bound. |
| A-7 | Change CI worker count | Owned by FR-1131 Phase A. CI is a different machine. |

## Implementation Status (2026-09-28)

**Operator-directed, no judge run.** Phase 1 ran on the operator's order
without a judgement. The operator stopped it partway ("computer is unstable
at 12 — no need to crash the system") and set N = 4: "let's trade some time
for stability". That decision replaces § Decision rule, rejected
alternative A-1, and mechanisms D-1/D-2. The hook entry and `CLAUDE.md` now
state `-n 4` directly. M-2 at the winner, all of M-3, and the Phase 2
re-measure did not run.

Bench: detached worktree `tmp/bench-fr1143` at main 6e11be5f. Driver:
`tmp/bench_fr1143.py` (uncommitted). It samples `ps` RSS over the pytest
process tree once per tick and `memory_pressure` / `vm.swapusage` every
fifth tick. Raw logs: `logs/bench-fr1143-*` (local).

### M-1 fast loop (hook command, `-n <N>`)

| Run | N | Wall s | CPU s | Peak tree RSS MB | Free % before → min | Load before (1-min) | Result |
|---|---|---|---|---|---|---|---|
| r1 | 12 | 175.1 | 866.0 | 2492 | 51 → 20 | 22.27 | 7481 passed |
| r1 | 4 | 135.8 | 375.4 | 2029 | 45 → 34 | 31.26 | 7481 passed |
| r1 | 8 | 103.8 | 551.4 | 2399 | 47 → 43 | 8.54 | 7481 passed |
| r1 | 3 | 147.9 | 339.8 | 1642 | 62 → 46 | 9.26 | 7481 passed |
| r1 | 6 | 106.1 | 449.1 | 1756 | 60 → 34 | 5.26 | 7481 passed |
| r2 | 6 | 96.4 | 417.8 | 2046 | 57 → 49 | 7.58 | 7481 passed |
| r2 | 3 | 154.8 | 341.3 | 1593 | 60 → 27 | 8.48 | 7481 passed |
| r2 | 8 | 117.4 | 602.9 | 2369 | 58 → 30 | 6.59 | 7481 passed |
| r2 | 4 | 123.2 | 373.2 | 1442 | 61 → 39 | 11.56 | 7481 passed |
| r2 | 12 | 196.1 | 729.1 | 2768 | 56 → 12 | 7.50 | 7481 passed |

Median wall: N=3 151 s, N=4 130 s, **N=6 101 s**, N=8 111 s,
**N=12 186 s**. The current `-n auto` (12 here) is the slowest setting
measured. It uses about twice the CPU of N=6 for less throughput, and it
has the lowest free memory. Pass/fail counts are identical across all 10
runs (AC-04).

### Idle baseline and M-2

| Run | Wall s | Swap Δ MB | Pageouts Δ | Min free % | Result |
|---|---|---|---|---|---|
| idle r1 (`sleep`, no tests) | 120.8 | +1039.8 | 5196 | 20 | — |
| idle r2 | 120.3 | +338.0 | 2801 | 46 | — |
| M-2 pair, N=12 ×2 concurrent | 580.8 | −1600.0 | 12828 | **3** | 3 failed, 7478 passed (each copy) |

- **Rule 1 had no valid metric.** With no tests running, swap still grew
  and pages still went out, driven by other apps and sessions. Swap and
  pageout deltas cannot separate pytest from background noise on this
  machine. Minimum free % was the signal that held up.
- **M-2 at 12 failed the same 3 tests in both copies.** Two are in
  `test_fr995_outsider_wrapper` (`test_input_mode_writes_placeholder_report_and_no_observation`,
  `test_pr_comment_posts_the_enriched_report_byte_for_byte`): both suites
  glob the global `TMPDIR` for `outsider-*`, which is a known isolation
  race and not fixed here. The third is
  `test_vscode_ledger::test_cli_smoke_exits_zero[args1]`: a
  `subprocess.TimeoutExpired` on `scripts/vscode/ledger.py --tap` under
  load. Each run took roughly 3× the solo time.

### Raw read (AC-02)

`bench-fr1143-m1-n12-r1.samples.log`, `free_pct` lines: the tree RSS was
2142 MB at t=32, then **fell** to 545–893 MB at t=65–131 while
`free_pct` fell to 24–33 and `nproc` rose to 33. The workers were being
compressed or paged out while their test subprocesses spawned. The peak
column cannot show that. The N=6 r2 run held 54–60% free throughout. At
every N, one process reaches 0.9–1.25 GB near the end of the run
(t≈128–146). It is visible in the `max_mb` column. Its command line was not
captured: the capture was added after M-1, and the stopped runs did not
reach that point. It is not identified.

### Decision

N = 4, set by the operator. Measured cost versus N=6: +29 s median fast
loop (130 s vs 101 s), for about 15% less CPU and 2 fewer processes
competing with the other sessions. The single machine-specific number is
committed to shared config (A-1 overruled). Other machines get 4 workers
too.

### Acceptance

- [x] AC-01 partial: M-1 and idle recorded. M-2 at the winner and M-3 not run (operator stop).
- [x] AC-02: raw read above.
- [ ] AC-03: superseded by the operator's decision.
- [x] AC-04: identical counts across M-1.
- [ ] AC-05: replaced. `-n 4` is literal in the hook entry and `CLAUDE.md`, and no `auto` resolution is involved.
- [ ] AC-06: not run.
- [x] AC-07: `CLAUDE.md` states the measured, dated M-1 N=4 range; `~20s on 12 cores` removed.
- [ ] AC-08: n/a (no dependency).

| Planned operation | Outcome | Witness |
|---|---|---|
| quiet check, loadavg/swap/vm_stat/ps sampling | ran | `logs/bench-fr1143-results.jsonl` |
| M-1 matrix, 10 runs | ran | same |
| M-2, 2 runs | 1 ran (N=12), 1 stopped | operator "stop" |
| M-3, 2 runs | did not run | operator "stop" |
| judge.sh | did not run | operator order to enforce |
| Phase 2 re-measure | did not run | operator decision |

**Unplanned operations:** 2 idle-baseline windows (needed to test rule 1);
the first M-1 launch was killed a few seconds in and relaunched, and its
logs were deleted. The commit hook failed on
`test_fr293_pytest_xdist::test_precommit_uses_parallel_flag`, which pinned
`-n auto`. Its assertion now pins `-n 4`: the contract changed by operator
decision, and no exclusion was added. The commit-hook run at `-n 4` took
140 s, with that 1 failure and 7480 passed.

## Related

- `.pre-commit-config.yaml:295` (hook entry), `CLAUDE.md` § Testing
- pytest-xdist 3.8.0 `xdist/plugin.py` `auto_detect_cpus`
- FR-1134 benchmark logs `tmp/bench-{before,after}.log` (local)
