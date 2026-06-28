# Feature Request: Memory / Structured Note-Taking Primitive

**Priority:** HIGH
**Type:** Feature
**Status:** Judged — Authority GRANTED with corrections (2026-06-28)
**Effort:** 3 days
**Requested:** 2026-06-28

## Summary

A first-class `memory` node (and backing tool) that reads and writes durable
notes *outside* graph state, so a graph can persist knowledge across nodes and
across runs and pull it back in just-in-time — the declarative equivalent of the
agentic "NOTES.md" / file-based memory pattern.

## Value Statement

Graph authors get persistent, cross-run agent memory with minimal context
overhead: a graph can record progress, decisions, and dependencies once and
recall only the relevant slice later, instead of carrying everything in state.

## Value Proposal

- **Long-horizon coherence**: Note-taking is the technique that lets agents track
  objectives across thousands of steps after context resets. It is the natural
  companion to compaction (FR-616): compaction forgets, memory remembers.
- **Cross-run continuity**: Checkpointing resumes *one* run's state; memory lets
  *separate* runs share a knowledge base (project state, prior conclusions). No
  existing YAMLGraph primitive spans runs at the content level.
- **Context economy**: Notes live outside the window and are loaded by reference,
  directly serving the finite-attention-budget principle.
- **Proven pattern, absent in YAMLGraph**: We already rely on this exact pattern
  in our own `/memories/` tooling. The framework should expose it declaratively
  rather than forcing every graph to reinvent it in `python` nodes.

## Judgement (2026-06-28)

**Verdict: Authority GRANTED with corrections.** Sound design — the backend factory mirrors the
checkpointer pattern, notes are namespaced and Pydantic-typed, and path sanitization is called out
(OWASP boundary, good). It is the natural "remember" to compaction's "forget." The corrections
harden the one thing a shared mutable store across runs must get right: concurrency and miss
semantics.

**Correction 1 (PRIMARY — concurrent-write clobber).** `namespace: "{state.thread_id}"` does **not**
guarantee isolation: two runs sharing a thread_id (resume, retry, or parallel chaplain workers)
write the same namespace/key and clobber — the concurrent-clobber composition bug. `op: append`
must be **atomic** (file lock or append-only log), and `op: write` must define its contract
(last-writer-wins vs conflict-raise). Do not ship a cross-run mutable store without a stated
concurrency contract.

**Correction 2 (secondary — read-miss must be explicit).** `op: read` on a missing note must raise
or return an explicit sentinel — never an empty value that reads downstream like "no decisions yet."
That is the FR-598 silent-substitution lineage: a plausible-empty is harder to catch than a crash.
Define the miss contract in the AC.

**Correction 3 (secondary — memory is itself unbounded).** The monotonic-growth problem compaction
fixes for state, memory reintroduces for notes — a namespace grows without bound across runs.
Out of scope to solve here, but the FR should **acknowledge** it rather than position memory as free
of the very problem its sibling exists to fix; note compaction-of-memory as a follow-up.

**Frozen scope.** read/write/append over a file backend behind a factory; namespacing isolates;
append atomic; read-miss explicit; path/namespace sanitized (no traversal); cross-run write→recall
demo with `demo-output.log`.

## Problem

The only durable store YAMLGraph offers is the checkpointer, which persists the
*entire* state blob for *resume*, not a curated, queryable note store. There is
no declarative way for a graph to say "write this insight to memory" or "recall
notes about X" — so agentic memory is impossible without bespoke Python.

## Proposed Solution

A `memory` node with `read` / `write` / `append` modes over a pluggable backend
(file-based default, mirroring the checkpointer-factory pattern).

```yaml
nodes:
  record_decision:
    type: memory
    op: append                    # read | write | append
    namespace: "{state.thread_id}"  # scopes notes (e.g. per session/project)
    key: decisions
    value: "{state.latest_decision}"

  recall_decisions:
    type: memory
    op: read
    namespace: "{state.thread_id}"
    key: decisions
    state_key: prior_decisions    # loaded back into state just-in-time
```

- **Backend factory** mirrors `storage/` checkpointer factory: `file` default,
  extensible to SQLite/Redis later.
- **Namespaced** so memory is scoped (per thread, per project) and never leaks
  across unrelated runs.
- **Typed**: read results are validated into a Pydantic shape, not raw dicts.

## Acceptance Criteria

- [ ] `memory` node type registered with `read`/`write`/`append` ops
- [ ] File-based backend behind a factory (extensible, like checkpointers)
- [ ] Namespacing isolates notes; no cross-namespace reads
- [ ] Read results are Pydantic-validated
- [ ] Path/namespace inputs sanitized (no path traversal — OWASP boundary check)
- [ ] Demo showing a note written in run A and recalled in run B
      (`demo-output.log` included)
- [ ] Tests tagged with a new `REQ-YG-XXX`; capability file added
- [ ] `reference/graph-yaml.md` documents the node and backend config

## Alternatives Considered

- **Overload the checkpointer**: rejected — checkpoint state is whole-blob,
  resume-oriented, and not content-addressable; misuses the abstraction.
- **MCP memory tool only**: viable for agent nodes but not for plain workflow
  nodes; a graph-level primitive serves both.
- **Documentation-only (deployment pattern)**: insufficient — unlike URL prompt
  loading, this needs runtime read/write semantics inside the graph.

## Related

- `docs/2026-06-28-research.md` (gap #2)
- FR-616 (compaction) — the forgetting/remembering pair
- `yamlgraph/storage/` (checkpointer factory pattern to mirror)
