# Chaplain Research Subjects

Composed from 40 Seeds across 28 diary entries (2026-02-17 — 2026-02-20).
Filtered: 14 Seeds already covered by existing FRs (024, 025, 041, 043, 045, 046, 050, 051, 052, 054, 055).

---

## Tier 1: Novel capabilities

- provider:host — Portable graphs that inherit the caller's LLM instead of requiring API keys. A graph node specifies `provider: host` and the orchestrating assistant's subscription model is used. Zero .env, zero cost allocation on the graph side. (Seed: diary.md, The Reverse Arrow)
- Node type macros — Generalize config-level expansion into a registry of `(node_type, config) → (expanded_nodes, expanded_edges)` functions called before compilation. Enable wizard, poll, saga as macro node types that pre-expand into existing primitives. (Seed: diary.md, The Coroutine Primitive)
- Protocol archaeology graph — Given a GitHub repo URL, extract endpoint URLs, auth flows, message formats, and error handling into a structured integration brief. Formalize the research method used for Ninchat. (Seed: diary-2026-02-18.md, Protocol Archaeology)

## Tier 2: Linter & validation

- No-silent-fallback lint rule — Flag `if not results: results = all_items` patterns in Python tool nodes as vuosikello-class bugs. Graduated to Commandment 6 but never enforced mechanically. (Seed: diary-2026-02-17.md, Vuosikello)
- Trace-shape contracts — Nodes declare expected observability events (e.g. "emits trace_start, trace_result"). Fail lint validation if a node's implementation could silently skip expected trace points. (Seed: diary-2026-02-19.md, World Digest — Observability)
- Linter config-resolution consistency — Meta-lint rule scanning resolve_* functions to ensure every `graph.get("option")` has a corresponding `defaults.get("option")` fallback. Prevents the prompts_relative bug class. (Seed: diary.md, Kill Entropy)
- Loop expression pre-validation — Validate that `loop_until` condition state paths actually resolve at expansion time, catching prefix issues before runtime. (Seed: diary.md, The state. Prefix Trap)

## Tier 3: Process & tooling

- Semantic triage for pipeline audit — Extend the audit graph with a context-aware node that classifies each flagged pattern (intentional safety net vs genuine silent failure) using surrounding code context. Reduces false positives from 72 to actionable count. (Seed: diary-2026-02-18.md, First Audit Run)
- Gotcha-to-fix audit — Scan documentation and code comments for documented edge cases and "gotcha" warnings that should be eliminated by semantic fixes instead. How many features have documented surprises that could just be fixed? (Seed: diary-2026-02-19.md, The Plan That Lied)
- Hypothesis test template — A structured prompt that converts a technical question ("does X work under Y?") into a runnable test before any source investigation begins. Circuit breaker for completionism bias. (Seed: diary-2026-02-17.md, FR-030 Completionism Bias)
- FR dependency detector — Scan FR descriptions for cross-references to other FRs and construct an execution order graph automatically. Prevents parallel opportunity illusion. (Seed: diary-2026-02-17.md, The Funnel)
- Confession registry expansion — Extend the confession pattern beyond noqa to cover hardcoded defaults, deferred migrations, and known limitations. Each invisible decision gets a CONF-ID, sin, and penance. (Seed: diary-2026-02-18.md, Confessions)
