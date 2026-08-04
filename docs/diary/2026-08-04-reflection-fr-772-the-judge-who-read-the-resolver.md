# The Judge Who Read the Resolver

**Date:** 2026-08-04
**Context:** FR-771 (demo executes manifest tool) blocked by its own judge;
FR-772 (tool_call inline dict args) created, judged, enforced; FR-771
unblocked and enforced — one branch, three hours, zero core patches smuggled.

## The catch

I wrote FR-771 with a plausible YAML snippet: inline `args:` with
`"{state.image}"` inside. The judge — input-closed to FR + code, blind to my
chat narrative — read `resolve_template()` and found it returns non-string
values unchanged: my inline dict would have sailed through with the literal
`"{state.image}"` string as a kwarg, and `tool_call`'s envelope would have
swallowed the downstream failure into `success: false`. Two layers of silent
wrongness stacked under a green exit code. I had even written "known risk:
verify args support first" into the FR — the risk section knew what the
solution section didn't.

The judge's C-2 ("no core patch under this FR — stop and re-judge") felt like
ceremony at filing time and was exactly right at verification time: the fix
belonged to a different authority scope. FR-772 got its own judgement, which
caught two MORE things I'd hand-waved: my AC-04 promised a guarantee the
reused resolver doesn't provide (embedded interpolation of missing paths
passes through), and my AC-06 delegated the CAP destination to "enforcer
picks" — an unmeasurable acceptance criterion. Verdict quality compounds:
each judge in this chain was stricter than my drafts, and each strictness
converted a would-be runtime surprise into a spec line.

## The resolver trap worth remembering

`resolve_node_variables({})` falls back to **whole-state passing** — the
empty dict is falsy, so "no explicit mapping" and "explicitly no args" are
the same branch. Found while writing the RED suite, not by reading docs. The
inline-args branch now short-circuits `{}` before the resolver; without that
test-first discovery, `args: {}` would have dispatched the entire graph
state as kwargs to an unsuspecting tool. Falsy-empty conflation at a
boundary — a `normalize at the boundary` violation hiding inside a utility
that three node types share.

## The arc in one line

Reflection question ("how is 769 utilizing the feature?") → gap found
(declaration ≠ invocation) → FR-770 (declaration boundary) → reflection again
→ FR-771 (invocation boundary) → judge blocks on missing core capability →
FR-772 (capability) → FR-771 lands. Each FR was small because the previous
one's *reflection* did the scoping. The W001 lint warning — waved through
twice as "expected" — was the thread the whole chain hung on: a warning you
annotate as expected twice is a finding, not noise.

## Heuristic

When an FR's own risk section says "verify X first," verify X **before
filing**, not during enforcement — the five-minute read of the resolver would
have produced FR-772 directly, skipping one judgement round-trip. The judge
caught it; the author should have. Cheaper corollary confirmed again:
`spec_kill` — every defect in this chain died in a document, none in
production.

**Seed:** the `tool_call` envelope swallows tool exceptions into
`success: false` by design (agent-loop shape). For deterministic invocation
(inline args, fixed tool), silent failure is the wrong default — should the
inline-args form grow `on_error: fail` semantics so a graph halts when a
deterministic call fails, matching every other deterministic node type?
