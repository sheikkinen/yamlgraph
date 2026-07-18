---
type: feat
scope: compile
req: REQ-YG-568
---
- **FR-718 Edge Compiler Decomposition**: edge compilation is classify-then-dispatch. `classify_edge` names every edge form as an explicit `EdgeShape` (8 members; `PLAIN` is a member, not a fall-through claim), per-shape compilers live in a dispatch table, and the condition-map assembly for router/expression edges is extracted as pure functions (`build_router_route_mapping`, `build_expression_route_mapping`). The two most complex functions in the codebase (`_process_edge` C 20, `_add_conditional_edges` C 18) are gone — nothing in the module reaches CC 10. Behavior change (Commandment 6): a condition on an untyped fan-out list now raises naming the edge instead of compiling with the condition silently dropped. (REQ-YG-568)
