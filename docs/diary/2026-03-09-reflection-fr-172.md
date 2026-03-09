# Diary: FR-172 — Configurable Loop Exit Target

**Date:** 2026-03-09
**FR:** FR-172
**Trap:** downstream_fix — The hardcoded `END` in `make_expr_router_fn` was a downstream fix for "what happens when a loop exhausts." The real contract belongs at the graph config level.

## Insight

The fix was 4 lines in `routing.py` but required threading a new parameter through 4 modules (schema → config → edge_compiler → routing). This is the cost of clean separation of concerns — but also its benefit: each layer had one clear change, and the lint rule could validate the config independently.

## Heuristic

**Configuration over hardcoding at boundaries.** When a framework behavior is hardcoded at a boundary (router returning `END`), the correct fix is a config field that flows through the compilation pipeline, not a special case at the call site. The `loop_exits` field sits next to `loop_limits` because they govern the same boundary.

## Seed

Could `loop_exits` be generalized to a `on_limit` strategy pattern? Instead of just a target node name, it could support `{action: "route", target: "node"}`, `{action: "retry_with", params: ...}`, or `{action: "escalate"}`. Is there a second use case that would justify this, or is YAGNI the right call?
