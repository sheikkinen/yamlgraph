# 2026-03-27 — FR-204 Five Whys Demo

## Context
Building a pure-YAML demo for the Five Whys root cause analysis technique: iteratively ask "why?" five times, accumulate answers in state, then synthesise a root cause summary.

## Cognitive Process
The key design question was how to accumulate structured results across loop iterations in pure YAML. The solution uses a list-type state key with Jinja2 `{{ whys | length + 1 }}` to track iteration count, and a conditional edge checking `whys | length >= 5` to exit the loop. This pattern is reusable for any fixed-count accumulation loop.

## Trap Avoided
**framework_costume** — Initially considered adding a Python counter node for iteration tracking. Realised the YAML conditional edge with Jinja2 list-length check already provides the capability without leaving the declarative layer. Adding Python would have dressed a simple config problem in framework clothing.

## Heuristic
When a loop needs a counter, check whether the accumulating state key's length already encodes the count. Prefer `len(list)` over a separate counter variable — it keeps the iteration evidence and the control signal in the same place.

## Seed
Could a `loop_count` virtual state key be auto-injected by the graph compiler for any node with `loop_limit`, eliminating the need for users to derive iteration count from list length?
