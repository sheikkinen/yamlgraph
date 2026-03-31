# Diary Reflection: FR-211 Router Route Mapping Redirect

**Date:** 2026-03-31
**FR:** FR-211
**Type:** Bugfix
**Trap:** downstream_fix — The FR-060 interrupt redirect logic lived only in the string-target path of `_process_edge`. List targets silently bypassed it, and the downstream `_add_conditional_edges` built identity mappings with no knowledge of interrupt nodes.

## Insight

**The boundary was wrong.** The route mapping is the true boundary where target names meet LangGraph's `add_conditional_edges` API. FR-060's original redirect in `_process_edge` handled the string case correctly, but the list case deferred to `_add_conditional_edges` which had no redirect awareness. The fix: bring redirect knowledge to where the mapping is built, not where the edge is parsed.

This is a textbook instance of *normalize at the boundary where external data enters* — the "external data" here being the YAML-declared target names, and the boundary being the `route_mapping` dict construction.

## Heuristic

**Mapping = boundary.** Whenever a function builds a key→value mapping that bridges two systems (here: router labels ↔ graph node names), that mapping construction is the redirect boundary. Guards applied upstream only cover some code paths; the mapping is the universal chokepoint.

## Pattern

The fix is elegant: the route mapping keys (labels) stay original so `make_router_fn` matches `_route` from state, while the values (graph node names) get redirected. This separation of concerns — label vs. target — is the same pattern as HTTP request routing (URL pattern vs. handler function).

## Seed

**Are there other edge types that build mappings without interrupt awareness?** Expression-based edges (`make_expr_router_fn`) currently don't need interrupt redirects because they use condition→target pairs where targets are already redirected strings. But if expression edges ever target lists, the same bug would recur. Should `_add_conditional_edges` apply redirect logic to expression edge targets as well, or is the current scoping correct?
