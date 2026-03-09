# Feature Request: Audit Parallelism Theatre Patterns

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** ✅ Approved
**Effort:** 2 days
**Requested:** 2026-03-09

## Summary

Systematically audit all concurrency patterns in YAMLGraph, classify each as safe or theatrical (appears concurrent but races on shared state), and either document safety invariants or create targeted FRs to serialize unsafe patterns.

## Value Statement

Maintainers gain a concurrency safety map of the codebase, preventing silent data loss from race conditions that masquerade as efficient parallelism.

## Problem

FR-175 revealed "parallelism theatre" in `watch.sh` — concurrent `nohup ... &` spawning that looked efficient but produced merge conflicts on shared files. The fix was sequential enforcement.

The same anti-pattern may exist elsewhere. Candidates identified:

| Area | Concurrency Model | Shared Mutable State | Risk |
|------|-------------------|---------------------|------|
| **Map node fan-out** | LangGraph `Send()` — truly parallel | State keys via reducers | ⚠️ Drift — reducer ordering is implicit |
| **Checkpoint writes** | Async Redis `SET` / SQLite — no locking | Same `thread_id` key | ✗ Critical — last-writer-wins race |
| **Graph cache** | Global dict — no lock | `graph_cache` shared across threads | ⚠️ Drift — 4-worker ThreadPool reads/writes |
| **Inquisitor diary writes** | Sequential per call, but calls can overlap | Diary filename numbering | ⚠️ Drift — filename collision on concurrent runs |
| **MCP server** | `ThreadPoolExecutor(max_workers=1)` | Per-invocation isolated | ✓ Safe — serialized by design |
| **Async executor** | `asyncio.gather()` with 4-worker pool | LLM instances (stateless) | ✓ Safe — no shared mutable state |

Without this audit, race conditions remain latent until production load triggers them — the hardest class of bug to reproduce and diagnose.

## Proposed Solution

A structured audit producing a **concurrency safety document** and targeted follow-up FRs. No production code changes in this FR — scope is investigation and documentation only.

### Phase 1: Document each candidate's concurrency model

For each area listed above, document in `docs/concurrency-safety.md`:

```markdown
## Map Node Fan-Out

**Model:** LangGraph `Send()` dispatches parallel sub-node executions.
**Shared State:** Sub-nodes write to `collect_key` via Annotated reducers.
**Safety Invariant:** Safe IFF each sub-node writes to a unique key or uses
  append-only list reducers. Unsafe if sub-nodes read-modify-write shared keys.
**Evidence:** `yamlgraph/map_compiler.py:260-293` (fan-out), `:87-175` (aggregation).
**Verdict:** ⚠️ CONDITIONAL — safe under reducer discipline, no enforcement.
```

### Phase 2: Classify shared mutable state

For each candidate, answer:
1. Does shared mutable state exist?
2. Is access serialized (lock, single-worker, sequential loop)?
3. If not serialized, does the data structure tolerate concurrent writes (append-only, CAS, atomic)?

### Phase 3: Create targeted FRs for violations

For each unsafe pattern, create a minimal FR that serializes at the spawn point (not downstream). Examples:

- **Checkpoint thread_id locking** — Add per-`thread_id` mutex or Redis `WATCH`/`MULTI` around checkpoint put.
- **Graph cache lock** — Add `threading.Lock` to `graph_cache.py` read/write paths.
- **Inquisitor flock** — Add `flock` around diary file creation in `inquisitor.sh`.

### Phase 4: Document safe patterns

For patterns confirmed safe, document **why** they are safe so future changes don't accidentally break the invariant:

- MCP server: "Single-worker `ThreadPoolExecutor` serializes all graph invocations."
- Async executor: "LLM instances are stateless; `asyncio.gather()` is safe for I/O-bound calls."

## Acceptance Criteria

- [ ] `docs/concurrency-safety.md` exists with an entry for each of the 6 candidates
- [ ] Each entry documents: concurrency model, shared state, safety invariant, evidence (file:line), verdict
- [ ] Checkpoint write race condition is classified and a follow-up FR created if unsafe
- [ ] Graph cache concurrency is classified and a follow-up FR created if unsafe
- [ ] Map node reducer discipline is documented with an example of safe vs unsafe usage
- [ ] Inquisitor diary filename collision risk is classified and mitigated or FR'd
- [ ] Safe patterns (MCP, async executor) document why they are safe
- [ ] No production code changes in this FR (audit + documentation only)
- [ ] Tests added (test that `docs/concurrency-safety.md` exists and covers all candidates)
- [ ] Documentation updated (CHANGELOG.md, this FR status)

## Alternatives Considered

1. **Fix all races immediately in one FR.** Rejected — violates single-responsibility. Each fix has different risk profiles and should be its own FR with its own tests. The audit identifies and prioritizes; follow-up FRs fix.

2. **Skip documentation, just fix the critical ones.** Rejected — without the safety map, we lack evidence that the "safe" patterns are truly safe. Documentation prevents future regressions when someone adds concurrency to a currently-safe path.

3. **Automated concurrency analysis tooling.** Rejected for now — Python's dynamic typing makes static race detection unreliable. Manual audit with file:line evidence is more trustworthy for this codebase size.

## Judgement

**Verdict:** APPROVE — 2026-03-09

**Evaluation:**

1. **Scope clear and minimal?** YES. Investigation + documentation only, no production code changes, well-bounded to 6 candidates.
2. **Contradictions or ambiguities?** MINOR. The Problem table claims `asyncio.gather()` in async executor but the actual code uses `run_in_executor()`. This is a hypothesis table the audit itself will correct — not blocking.
3. **Acceptance criteria measurable?** YES. All 10 criteria are checkboxes with clear pass/fail conditions (file existence, entry completeness, follow-up FR creation).
4. **Implementation approach feasible?** YES. 4 phases are logical and sequential. 2-day estimate is reasonable.
5. **Aligns with architecture?** YES. Documentation-first, fixes deferred to follow-up FRs per single-responsibility.
6. **Single responsibility?** YES. One deliverable: concurrency safety map. All fixes are explicitly out of scope.

**Notes for implementer:**
- The async executor row in the Problem table says `asyncio.gather()` — actual code is `loop.run_in_executor()`. Correct during Phase 1 documentation.
- FR-156 addresses Inquisitor audit-loop repetition (duplicate range detection), which is adjacent but distinct from the filename collision concern here. Cross-reference in the concurrency doc.
- Checkpoint race (item #2) may be lower risk than initially suggested — each thread_id gets its own Redis key. The audit should verify whether concurrent invocations of the *same* thread_id are possible under normal LangGraph usage.

## Related

- `.chaplain/watch.sh` — FR-175 reference fix for parallelism theatre (sequential enforcement)
- `feature-requests/FR-175-sequential-enforcement-mode.md` — precedent FR
- `yamlgraph/map_compiler.py` — map node fan-out via `Send()`
- `yamlgraph/storage/simple_redis.py` — checkpoint writes without locking
- `yamlgraph/graph_cache.py` — global cache without lock
- `yamlgraph/utils/llm_factory_async.py` — 4-worker ThreadPool
- `yamlgraph/mcp_server.py` — single-worker executor (safe reference)
- `.chaplain/inquisitor.sh` — diary write concurrency
