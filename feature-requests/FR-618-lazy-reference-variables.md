# Feature Request: Lazy / Reference Variables (Just-in-Time Context)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — Authority GRANTED with corrections (2026-06-28)
**Effort:** 2 days
**Requested:** 2026-06-28

## Summary

Let graph variables carry a *reference* (a path, query, or id) that is resolved to
its full payload only at the node that needs it — instead of eagerly inlining
large payloads into every prompt via `variables: "{state.x}"`.

## Value Statement

Graph authors stop paying for context they don't use: a large document, dataset,
or transcript can flow through the graph as a lightweight handle and be expanded
to full text only inside the one node that actually reads it.

## Value Proposal

- **Direct context-bloat reduction**: Eager inlining puts full payloads into the
  attention budget of *every* node that touches that state key. Reference
  variables move data in only where it's consumed — the just-in-time retrieval
  principle, applied to YAMLGraph's own templating.
- **Cost + quality compound**: Fewer tokens per call is both cheaper and less
  context-rot. The saving scales with payload size and graph depth.
- **Smallest surface of the five gaps**: This is an *enhancement to existing
  variable resolution*, not a new node type — lowest-risk way to put a
  context-engineering principle into the core.
- **Composes with FR-616/617**: Memory reads and compacted summaries are exactly
  the kind of large payloads that benefit from lazy resolution.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED with corrections.** The cleanest of the feature trio — an enhancement
to existing variable resolution rather than a new node type, lowest-risk, with the security boundary
(path traversal / SSRF, http allowlist) correctly called out. The corrections address the cost of
deferring resolution: failures and non-determinism move deeper into the run.

**Correction 1 (PRIMARY — lazy moves failure from start to mid-run).** Eager inlining fails fast at
graph start; a lazy `ref` to a missing file or a 500-ing http endpoint is discovered deep in
execution, after upstream nodes are paid for. Bind: a resolution failure must raise a
`PipelineError` **at the resolving node** (never a silent empty string), AND add an optional
lint/validate-refs pass for `file` refs so statically-broken refs are caught at `graph lint` —
preserving fail-fast where the ref is knowable before run.

**Correction 2 (secondary — caching interaction).** An `http` loader makes the rendered prompt
non-deterministic and non-reproducible; a cached prompt carrying a live ref is stale. Document that
http refs either disable prompt caching for that prompt or are resolved-then-cached explicitly. The
`file` loader is deterministic only if the file is immutable during the run.

**Correction 3 (secondary — re-resolution cost).** If the same ref renders in N nodes, define
whether it loads once (memoized per run) or N times. The FR's value is token reduction; redundant
I/O on every render undercuts it. Memoize per-run-per-ref or document the per-render cost.

**Frozen scope.** `ref` + `loader` resolved at render time only; plain string variables unchanged
(no migration); `file` loader shipped behind an extensible registry; loader inputs sanitized;
resolution failure raises at the node; token-usage demo with `demo-output.log`.

## Problem

Today `variables: "{state.transcript}"` substitutes the entire value into the
rendered prompt at every node referencing it. For large payloads this inflates
input tokens linearly with graph depth, even when most nodes only need a handle.
There is no way to pass "the location of X" and defer loading X.

## Proposed Solution

A reference form for variables that resolves through a registered loader only when
rendered into a prompt.

```yaml
nodes:
  summarize:
    type: llm
    prompt: summarize_doc
    variables:
      # eager (today): inlines full text everywhere it flows
      title: "{state.title}"
      # lazy (new): resolved to full text only here, via a loader
      body:
        ref: "{state.doc_path}"
        loader: file              # file | query | http (registered loaders)
```

- A small **loader registry** (file, query, http) resolves a ref to a string at
  render time; loaders live in Layer 3 (`tools/`), honoring import boundaries.
- Non-`ref` variables behave exactly as today (no migration needed).
- Loader inputs sanitized at the boundary (path traversal / SSRF guards).

## Acceptance Criteria

- [ ] `ref` + `loader` variable form parsed and resolved at render time only
- [ ] Plain string variables unchanged (existing graphs untouched)
- [ ] At least a `file` loader shipped; loader registry is extensible
- [ ] Loader inputs sanitized (no path traversal; http loader allowlist)
- [ ] Token-usage demo showing fewer input tokens vs. eager inlining
      (`demo-output.log` included)
- [ ] Tests tagged with a new `REQ-YG-XXX`; capability file added
- [ ] `reference/expressions.md` documents the `ref`/`loader` form

## Alternatives Considered

- **Always eager (status quo)**: simplest, but pays the full token cost at every
  hop; the problem this FR exists to fix.
- **Manual `tool` node before each consumer**: works but verbose and forces the
  author to thread the loaded value through state explicitly.
- **Automatic size-based lazy loading**: rejected for v1 — implicit behavior is
  harder to reason about than an explicit `ref`.

## Related

- `docs/2026-06-28-research.md` (gap #3)
- `reference/expressions.md`, variable resolution in `node_factory/`
- FR-616, FR-617 (producers of large payloads that benefit from lazy loading)
