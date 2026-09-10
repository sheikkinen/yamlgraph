# An async example must demonstrate overlapping lifetimes

**Date:** 2026-09-10
**Prior art:** [FR-1038](../../feature-requests/FR-1038-interruptible-search-fsm-integration.md),
[shared hook contract](../../feature-requests/FR-369-fsm-snapshot-hooks-phase2-subclassing.md).

A sequential application can use an asynchronous action without exercising the
reason its ownership contract is difficult. The router example supplies useful
wiring, but its integration-named tests inspect configuration rather than execute
the composed system. Names are inventory; execution paths are evidence.

The proposed interruptible search example adds one realistic event: a newer query
supersedes unfinished work. Explicit barriers make late completion inevitable in
tests instead of hoping network timing produces it. The engine, compiled graph,
action and event transport remain real. The provider is unnecessary for this
ordering claim, but these tests cannot claim provider latency or throughput.

Two specification traps emerged. Query text is not identity because identical
queries can be submitted twice. A send-time ownership check is also not a
receive-time guarantee because an accepted datagram can outlive its authority.
The contract must name both the shared commit boundary and the consumer's result
acceptance boundary without expanding into a new transport framework.

**Heuristic:** choose the smallest application whose normal user interaction
forces the disputed interleaving. Keep the runtime path real, control the schedule,
and wait for obsolete work to finish before asserting that it caused no effects.

**Seed:** Can the same scripted interaction demonstrate the ownership invariant
to a human and condemn its regression automatically without two implementations?
