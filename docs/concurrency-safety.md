# Concurrency Safety Map

**FR-176 — Audit Parallelism Theatre Patterns**
**Date:** 2026-03-09
**Status:** Complete

This document classifies every concurrency pattern in YAMLGraph as safe, conditionally safe, or unsafe. Each entry documents the concurrency model, shared mutable state, safety invariant, evidence (file:line), and verdict.

> **The One Law:** Normalize at the boundary where external data enters, not downstream where it manifests.

---

## Summary

| Area | Verdict | Key Finding |
|------|---------|-------------|
| Map node fan-out | ✓ Safe | Annotated `sorted_add` reducer serializes concurrent writes |
| Checkpoint writes | ⚠️ Conditional | SQLite: file-level locking; Redis: atomic SET, last-write-wins |
| Graph cache | ⚠️ Conditional | TOCTOU race causes duplicate compilation (not corruption) |
| Inquisitor diary writes | ⚠️ Conditional | No flock; filename collision possible on concurrent runs |
| MCP server | ✓ Safe | Single-worker `ThreadPoolExecutor` serializes all invocations |
| Async executor | ✓ Safe | `asyncio.gather()` over stateless LLM calls; cache race is benign |

---

## Map Node Fan-Out

**Model:** LangGraph `Send()` dispatches parallel sub-node executions. Each item in the source list spawns an independent sub-node invocation.

**Shared State:** Sub-nodes write to `collect_key` via `Annotated[list, sorted_add]` reducer. The `sorted_add` function merges results and sorts by `_map_index` for deterministic ordering.

**Safety Invariant:** Safe because each sub-node produces an independent result tagged with `_map_index`. The `sorted_add` reducer is the single aggregation point — LangGraph guarantees reducer calls are serialized.

**Evidence:**
- Fan-out via `Send()`: `yamlgraph/map_compiler.py:275-289`
- `sorted_add` reducer: `yamlgraph/models/state_builder.py:31-50`
- Annotated type binding: `yamlgraph/models/state_builder.py:223`
- Result wrapping with `_map_index`: `yamlgraph/map_compiler.py:87-175`

**Verdict:** ✓ **SAFE** — Annotated reducer is LangGraph's native concurrency primitive. No explicit locks needed.

---

## Checkpoint Writes

**Model:** Two checkpoint backends — SQLite (local) and Redis (distributed). Both support sync and async access patterns.

**Shared State:** Checkpoint data keyed by `(thread_id, checkpoint_ns)`. Each key holds serialized graph state.

### SQLite

**Safety Invariant:** SQLite's internal WAL/journal-mode serialization prevents corruption from concurrent writes within the same process. Cross-process writes are serialized by file-level locks.

**Evidence:**
- Connection with `check_same_thread=False`: `yamlgraph/storage/checkpointer.py:44`
- Uses LangGraph's `SqliteSaver` which delegates to SQLite's built-in concurrency model

**Risk:** Safe from corruption. Concurrent writes to the same `thread_id` are serialized by SQLite, but last-write-wins semantics apply — no application-level conflict resolution.

### Redis

**Safety Invariant:** Redis `SET` is atomic at the key level. Each `(thread_id, checkpoint_ns)` maps to a single Redis key. Concurrent writes are atomic but last-write-wins.

**Evidence:**
- Async put: `yamlgraph/storage/simple_redis.py:124-153` (`await client.set(key, data)` at line 151)
- Sync put: `yamlgraph/storage/simple_redis.py:252-281` (`client.set(key, data)` at line 279)
- Key format: `yamlgraph/storage/simple_redis.py:73` (`f"{key_prefix}{thread_id}:{checkpoint_ns}"`)
- No locking: no `WATCH`/`MULTI` around checkpoint operations

**Risk:** No corruption (Redis SET is atomic), but concurrent invocations of the same `thread_id` produce unpredictable checkpoint history. This is a design constraint, not a bug — `SimpleRedisSaver` stores only the latest checkpoint (documented at file header lines 1-14).

**Verdict:** ⚠️ **CONDITIONAL** — Safe from corruption under both backends. Application layer should avoid concurrent invocations with the same `thread_id`. No follow-up FR needed — this is a documented design constraint of LangGraph's checkpoint model.

---

## Graph Cache

**Model:** Process-global dictionary storing compiled `StateGraph` objects keyed by absolute file path. No `threading.Lock` protects reads or writes.

**Shared State:** `GRAPH_CACHE: dict[str, Any] = {}` — a plain dict shared across all threads.

**Safety Invariant:** Safe because compiled graphs are immutable after construction. The TOCTOU race (check-then-insert) causes duplicate compilation work but not data corruption.

**Evidence:**
- Global dict: `yamlgraph/graph_cache.py:23`
- TOCTOU pattern in async executor: `yamlgraph/executor_async.py:265-275` (check `path in cache`, compile, insert)
- Clear function: `yamlgraph/graph_cache.py:31`

**Analysis:**
1. **Read race:** Two threads check `path in cache` simultaneously, both miss → both compile → both write. Under CPython's GIL, `dict.__setitem__` is atomic, so no dict corruption occurs.
2. **Duplicate work:** Extra compilation wastes CPU but produces identical results (same YAML → same compiled graph).
3. **Stale read:** Not possible — graphs are never mutated after insertion. `clear_cache()` is called only in tests.

**Verdict:** ⚠️ **CONDITIONAL** — Duplicate compilation is wasteful but harmless. A `threading.Lock` would eliminate waste but adds contention. Current design is acceptable for the expected concurrency level (MCP server serializes invocations via `max_workers=1`). No follow-up FR needed unless profiling reveals compilation as a bottleneck.

---

## Inquisitor Diary Writes

**Model:** Shell script (`.chaplain/inquisitor.sh`) creates diary files in `docs/diary/` with pattern `YYYY-MM-DD-inquisitor-audit-<number>.md`. File numbering is determined by the LLM generating the content, not by an atomic counter.

**Shared State:** Filesystem — `docs/diary/` directory listing used to determine last audit SHA range.

**Safety Invariant:** Safe under FR-175's sequential enforcement mode. The `.chaplain/watch.sh` daemon now processes enforcement tasks sequentially (one at a time), eliminating the concurrent-run scenario.

**Evidence:**
- Last audit lookup: `.chaplain/inquisitor.sh:34-37` (scans `docs/diary/*inquisitor-audit*`)
- File creation: `.chaplain/inquisitor.sh:78` (filename includes date and number)
- No flock: no file locking anywhere in the script
- FR-175 sequential enforcement: `.chaplain/watch.sh` runs enforcement sequentially

**Analysis:**
1. **Pre-FR-175:** Concurrent `nohup` spawning could run multiple inquisitor instances simultaneously → filename collision, SHA range overlap.
2. **Post-FR-175:** Sequential enforcement ensures only one inquisitor runs at a time → no concurrent access to diary directory.
3. **Manual invocation:** Running `inquisitor.sh` manually while `watch.sh` is active could still race. This is an operator error, not a design flaw.

**Verdict:** ⚠️ **CONDITIONAL** — Safe under normal operation (FR-175 sequential mode). Manual concurrent invocation would race but is not a supported workflow. Follow-up FR for `flock` is deferred — the sequential enforcement is the correct fix at the spawn point (The One Law: normalize at the boundary).

---

## MCP Server

**Model:** Single-worker `ThreadPoolExecutor` serializes all graph invocations. The MCP protocol handler is async, but the actual graph execution is delegated to a single thread.

**Shared State:**
- `_executor`: Module-global `ThreadPoolExecutor(max_workers=1)` — immutable after creation
- `graph_lookup`: Read-only dict populated at server startup

**Safety Invariant:** `max_workers=1` guarantees sequential execution. Only one `_invoke_graph` call runs at any time. Graph state lives in the checkpointer, not in the executor.

**Evidence:**
- Executor creation: `yamlgraph/export/mcp.py:55` (`ThreadPoolExecutor(max_workers=1)`)
- Graph invocation: `yamlgraph/export/mcp.py:277` (`loop.run_in_executor(_executor, _invoke_graph, ...)`)
- Import: `yamlgraph/export/mcp.py:26` (`from concurrent.futures import ThreadPoolExecutor`)

**Verdict:** ✓ **SAFE** — Serialized by design. Single-worker pool eliminates all concurrency concerns within graph execution.

---

## Async Executor

**Model:** Two concurrency mechanisms — `asyncio.gather()` for concurrent prompt execution, and a 4-worker `ThreadPoolExecutor` for wrapping sync LLM calls.

### Concurrent Prompt Execution

**Shared State:** None per invocation. Each prompt gets its own LLM instance (from cache) and independent state.

**Safety Invariant:** `asyncio.gather()` runs coroutines concurrently in a single thread (event loop). No data races are possible within a single event loop iteration. LLM API calls are I/O-bound and stateless.

**Evidence:**
- `asyncio.gather()`: `yamlgraph/executor_async.py:130`
- Graph cache usage: `yamlgraph/executor_async.py:265` (uses `_DEFAULT_CACHE`)

### LLM Factory Async (4-Worker Pool)

**Shared State:** LLM instances are cached and shared across threads. The cache itself is protected by `threading.Lock`.

**Safety Invariant:** LLM cache is thread-safe (locked). LLM instances are assumed stateless — they make HTTP requests without holding connection state between calls. This assumption holds for all supported providers (Anthropic, OpenAI, Mistral, Google, DeepSeek, xAI).

**Evidence:**
- 4-worker pool: `yamlgraph/utils/llm_factory_async.py:28-36`
- `run_in_executor()`: `yamlgraph/utils/llm_factory_async.py:60-61`
- Cache lock: `yamlgraph/utils/llm_factory.py:33` (`_cache_lock = threading.Lock()`)
- Lock usage: `yamlgraph/utils/llm_factory.py:275` (`with _cache_lock:`)

**Verdict:** ✓ **SAFE** — `asyncio.gather()` is single-threaded; LLM factory cache is locked; LLM instances are stateless HTTP clients.

---

## Maintenance

When adding new concurrency to YAMLGraph:

1. **Document here first.** Add an entry before writing the concurrent code.
2. **Classify shared state.** If mutable state is shared, it must be serialized.
3. **Prefer serialization at the spawn point** (The One Law) over downstream locking.
4. **Test under load.** Unit tests with `threading` or `asyncio.gather()` that exercise the concurrent path.

---

## Related

- `feature-requests/FR-175-sequential-enforcement-mode.md` — Fix for watch.sh parallelism theatre
- `feature-requests/FR-176-audit-parallelism-theatre.md` — This audit's feature request
- `docs/diary/` — Inquisitor audit entries
- `ARCHITECTURE.md` — System design and state management
