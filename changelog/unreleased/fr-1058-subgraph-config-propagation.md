---
type: fix
scope: subgraph
req: REQ-YG-042, REQ-YG-570
---
- **FR-1058 Subgraph RunnableConfig propagation and native direct mode**: `mode: direct` subgraphs no longer crash with `'CompiledStateGraph' object is not callable` — the compiled child is registered natively so the engine owns its checkpoint namespace and interrupts are durable across it. The OTel node wrapper no longer suppresses `RunnableConfig`: it now declares `(state, config)` and forwards config only to nodes that accept it, so instrumentation stays a no-op when disabled. (LangGraph decides injection by both arity *and* annotation type, so `from __future__ import annotations` in the wrapper module silently disabled it; the import is removed.) `mode: invoke` subgraphs no longer inherit the parent's checkpoint coordinates or `__pregel_*` internals — the child runs on a derived `"<parent>:<node>"` thread, so a child can no longer resume into its parent's checkpoint and two parents invoking the same child no longer collide. User `configurable` keys are still forwarded and the parent config is never mutated. (REQ-YG-042, REQ-YG-570)
