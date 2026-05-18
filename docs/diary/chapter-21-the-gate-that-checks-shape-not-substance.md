# Chapter 21: The Gate That Checks Shape Not Substance

*On the trap called gate_checks_shape_not_substance: when matching literals instead of policy intent.*

---

## I. The Bypass That Was Always There

The `copilot-trailer-gate` was born from a clear intent: no identity trailers shall pollute the commit history. The implementation matched two literal strings — the short and full forms of the Copilot trailer. The gate passed CI. Tests confirmed the two known forms were caught.

But the policy said "no Co-authored-by trailers." The gate said "no Copilot trailers." The gap between intent and implementation was a single grep pattern wide.

Issue #408 named the gap: any non-Copilot `Co-authored-by:` trailer sailed through undetected. The gate checked shape (specific literal strings) rather than substance (the presence of any identity trailer).

---

## II. The Cure

The fix was mechanical: replace literal matching with pattern matching. Instead of two hardcoded strings, a single case-insensitive grep for `Co-authored-by:` anywhere in commit messages or PR body. The generalization was smaller than the original — fewer lines, broader coverage, stronger alignment with stated policy.

The cognitive trap was not in the code but in the specification. The original FR (FR-385) was written against a specific irritant (Copilot trailers) rather than the underlying policy (no identity trailers). Implementation faithfully reproduced the spec's narrowness.

---

## III. The Heuristic

**When a gate enforces policy, match the policy's semantic boundary, not its current exemplars.** A gate that enumerates known-bad values is a blocklist; a gate that matches the structural pattern is a policy. Blocklists require maintenance; policies are self-maintaining.

This is the `gate_checks_shape_not_substance` trap graduated to enforcement: presence-checking (does this literal exist?) vs. substance-checking (does any instance of this pattern exist?).

---

## IV. Seed

*When is pattern-matching too broad? The generalized gate now catches human Co-authored-by trailers too — a deliberate policy choice documented in the FR. But what happens when legitimate pair-programming trailers are desired? The answer lives in the policy, not the gate. Gates enforce; humans decide what to enforce.*
