# The Loser That Never Got to Fail (FR-711)

**Date:** 2026-07-10
**Context:** FR-711 local instrument — connection-reuse latency witness; found a correctness bug the latency question was hiding.

## What happened

The instrument was built to measure milliseconds. Its first run returned a
correctness defect instead: the cached google-genai client **errors on half
of completed calls in fresh event loops** (`Executor shutdown has been
called` / `Timeout context manager should be used inside a task`) — while
azure and anthropic tolerate the same topology cleanly.

The sharp part: the FR-711 judgement had explicitly hedged this (F2:
"an Arm-B error is a finding, not a bug") while simultaneously citing
FR-709 as field-proof of tolerance. Both were right and wrong at once —
FR-709's google candidate was **always the cancelled loser**. It never
completed a cross-loop call, so the completion-path defect was
structurally unreachable in that witness. `assert_path_not_destination`
recursed one level deeper than we'd ever applied it: not just "assert the
path, not the endpoint" but **"know which path your fixture is physically
able to walk."** A witness that can only exercise cancellation proves
nothing about completion.

## The compounding lesson

Three witnesses in three days each masked something the next one found:
mocked losers (706/707) missed the loop-affinity class entirely; the live
witness (709) exercised only the cancel path; the latency instrument (711)
finally walked the complete path and found the bug. Each witness was
correct within its seam and blind outside it — `name_the_seam` is not
bookkeeping, it is the map of what remains unproven.

Also worth naming: the latency signal itself (Δp50 ≈ +0.5–0.6 s per
fresh-loop call on clean arms) would alone have condemned locally — but
the correctness finding outranks it and is verdict-independent: FR-712
must fix the google path regardless of what Fly says about milliseconds.

## Heuristic

When a witness passes, record not just the verdict but the paths its
fixtures could NOT reach — the complement is the residual risk list. A
"field-verified" claim must name the path that verified it; citing a test
that structurally cannot reach the claimed behavior is evidence-shaped,
not evidence.

**Seed:** should witness FRs carry a mandatory "paths not exercised"
section — a mechanical complement to acceptance criteria — so the next
investigator inherits the blind spots explicitly instead of rediscovering
them through incident?
