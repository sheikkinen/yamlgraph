# 2026-03-25 — FR-204 FSM Router Interrupt Resume

## Context
Finalizing the `fsm-router` example so it behaves like the documented interrupt contract instead of only supporting fresh one-shot runs.

## Cognitive Process
The implementation work was mostly straightforward because the production action already demonstrated the shape of the solution. The harder part was keeping the example narrow: copy the interrupt lifecycle, but not the voicebot infrastructure surrounding it. That boundary forced the change to stay educational instead of cargo-culting production code.

## Trap Avoided
**false_duplicate** — The production `yamlgraph_async_action` looked like something to copy verbatim, but most of it solved ninchat-specific concerns rather than the example's problem. Treating the files as semantically identical would have imported event senders, UI activity helpers, and other machinery the example does not need.

## Heuristic
When promoting production behavior into an example, copy the contract, not the ecosystem. Preserve the minimal execution boundary that demonstrates the pattern, then add tests that prove the smaller version still honors the same state transitions.

## Seed
Should examples that demonstrate checkpointed interrupt flows share a tiny reusable test fixture for `thread_id` + `Command(resume=...)`, so new examples can prove the lifecycle without re-deriving the same harness?
